import logging
import os
from random import randint
from time import strptime
from typing import Union, Tuple

import boto3


class AwsResources:
    def __init__(self, args):
        self.volume_name = args.volume_name
        self.availability_zone = args.availability_zone
        self.encrypted = args.encrypted
        self.iops = args.iops
        self.size = args.size
        self.volume_type = args.volume_type
        self.region_name = args.region_name
        self.volume = None

        # Random key name to allow concurrent executions
        self.key_name = f'EBS-Cargo-{randint(100000, 1000000)}'

        if self.volume_type == 'io1' and self.iops is None:
            raise Exception('You need to specify IOPS if you are using a io1 volume')

        if (self.volume_type == 'gp2' and not 1 <= self.size < 16384) or (
                self.volume_type == 'io1' and not 4 <= self.size < 16384) or (
                self.volume_type == 'st1' and not 500 <= self.size < 16384) or (
                self.volume_type == 'sc1' and not 500 <= self.size < 16384) or (
                self.volume_type == 'standard' and not 1 <= self.size < 1024):
            raise Exception(
                'The volume size has the following constraints: 1-16384 for gp2 , 4-16384 for '
                'io1 , 500-16384 for st1 , 500-16384 for sc1 , and 1-1024 for standard ')

        try:
            if self.region_name is not None:
                self.ec2_client = boto3.client('ec2', region_name=self.region_name)
                self.ec2_resource = boto3.resource('ec2', region_name=self.region_name)
            else:
                self.ec2_client = boto3.client('ec2')
                self.ec2_resource = boto3.resource('ec2')

            logging.debug(boto3.client('sts').get_caller_identity())
        except Exception as e:
            logging.error('Impossible logging in:')
            logging.error(e)
            logging.error(
                'Please read https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration '
                'for a proper configuration of the credentials.')  # TODO: write a guide on our wiki

            raise Exception('Critical error, aborting.')

    def create_ebs(self) -> Union[str, int]:
        tag_specifications = [{
            'ResourceType': 'volume',
            'Tags': [{
                'Key': 'Name',
                'Value': self.volume_name
            }]
        }]

        # botocore complains if iops is none:
        # Invalid type for parameter Iops, value: None, type: <class 'NoneType'>,
        # valid types: <class 'int'>
        try:
            if self.iops is not None:
                response = self.ec2_client.create_volume(
                    AvailabilityZone=self.availability_zone,
                    Encrypted=self.encrypted,
                    Iops=self.iops,
                    Size=self.size,
                    VolumeType=self.volume_type,
                    TagSpecifications=tag_specifications
                )
            else:
                response = self.ec2_client.create_volume(
                    AvailabilityZone=self.availability_zone,
                    Encrypted=self.encrypted,
                    Size=self.size,
                    VolumeType=self.volume_type,
                    TagSpecifications=tag_specifications
                )
        except Exception as e:
            logging.error('Impossible creating the EBS volume:')
            logging.error(e)
            return -1

        return response["VolumeId"]

    def find_ami(self) -> str:
        # We use Amazon Linux 2, because it has an important functionality:
        # when you attach an EBS, Amazon Linux creates a symbolic link for the name you
        # specified to the renamed device.
        # In this way we always know where we can reach the attached EBS
        images = self.ec2_resource.images.filter(
            Filters=[
                {
                    'Name': 'architecture',
                    'Values': ['x86_64']
                },
                {
                    'Name': 'name',
                    'Values': ['amzn2-ami-hvm-2.0*']
                },
            ],
            Owners=['amazon']
        )

        sorted_list = sorted(images, reverse=True,
                             key=lambda i: strptime(i.creation_date, '%Y-%m-%dT%H:%M:%S.%fZ'))

        return [image for image in sorted_list][0].id

    def create_key_pair(self):
        response = self.ec2_client.create_key_pair(KeyName=self.key_name)
        with open(f'/tmp/{self.key_name}.pem', 'w') as key_file:
            key_file.write(response['KeyMaterial'])

        os.chmod(f'/tmp/{self.key_name}.pem', 0o400)

    def delete_key_pair(self):
        self.ec2_client.delete_key_pair(KeyName=self.key_name)
        os.remove(f'/tmp/{self.key_name}.pem')

    def create_instance(self) -> Union[str, int]:
        try:
            image_id = self.find_ami()
        except Exception as e:
            logging.error('Impossible finding a valid AMI')
            logging.error(e)

            return -1

        logging.info(f'Selected AMI with id {image_id}')

        try:
            self.create_key_pair()
        except Exception as e:
            logging.error('Impossible creating a new key pair')
            logging.error(e)

            return -1

        try:
            instances = self.ec2_resource.create_instances(
                ImageId=image_id,
                InstanceType='t2.micro',
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{
                        'Key': 'Name',
                        'Value': 'Managed by EBS-Cargo'
                    }]
                }],
                MinCount=1,
                MaxCount=1,
                KeyName=self.key_name,
                Placement={
                    'AvailabilityZone': self.availability_zone
                }
            )
        except Exception as e:
            logging.error('Impossible creating a custom instance')
            logging.error(e)

            return -1

        return instances[0].id

    def attach_ebs_to_instance(self, volume_id, instance_id):
        instance = self.ec2_resource.Instance(instance_id)

        logging.info('Waiting until the instance is running')
        instance.wait_until_running()
        logging.info('The instance is running')

        self.volume = self.ec2_resource.Volume(volume_id)

        try:
            logging.info('Attaching volume to the instance')

            result = self.volume.attach_to_instance(
                Device='/dev/sdk',
                InstanceId=instance_id
            )

            logging.debug(result)

            logging.info('Waiting for the volume to be ready')
            waiter = self.ec2_client.get_waiter('volume_in_use')
            waiter.wait(VolumeIds=[self.volume.id])

        except Exception as e:
            logging.error('Impossible attaching the EBS volume to the instance:')
            logging.error(e)
            return -1

    def detach_ebs_from_instance(self, volume_id: str):
        self.ec2_client.detach_volume(
            VolumeId=volume_id
        )

    def delete_instance(self, instance_id: str):
        self.ec2_client.terminate_instances(
            InstanceIds=[instance_id]
        )

        logging.info('Waiting until the instance is terminated')
        instance = self.ec2_resource.Instance(instance_id)
        instance.wait_until_terminated()
        logging.info('The instance is terminated')

    def retrieve_instance_hostname(self, instance_id: str) -> str:
        return self.ec2_resource.Instance(instance_id).public_dns_name
