import logging

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
                self.client = boto3.client('ec2', region_name=args.region_name)
            else:
                self.client = boto3.client('ec2')
        except Exception as e:
            logging.error('Impossible logging in:')
            logging.error(e)
            logging.error(
                'Please read https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration '
                'for a proper configuration of the credentials.')  # TODO: write a guide on our wiki

            raise Exception('Critical error, aborting.')

    def create_ebs(self):
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
                response = self.client.create_volume(
                    AvailabilityZone=self.availability_zone,
                    Encrypted=self.encrypted,
                    Iops=self.iops,
                    Size=self.size,
                    VolumeType=self.volume_type,
                    TagSpecifications=tag_specifications
                )
            else:
                response = self.client.create_volume(
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

        return response

    def create_instance(self):
        ec2 = boto3.resource('ec2', region_name=self.region_name)
        image_iterator = ec2.images.filter(
            Filters=[
                {
                    'Name': 'name',
                    'Values': ['ubuntu']
                }
            ]
        )

        print(list(image_iterator))

        # image_id = [image for image in image_iterator]
        # print(image_id)

        # instance = client.create_instances(
        #     BlockDeviceMappings=[{
        #
        #     }]
        # )

    def attach_ebs_to_instance(self, volume_id, instance_id):
        self.volume = self.client.Volume(volume_id)

        try:
            return self.volume.attach_to_instance(
                Device='/dev/sdk',
                InstanceId=instance_id
            )
        except Exception as e:
            logging.error('Impossible attaching the EBS volume to the instance:')
            logging.error(e)
            return -1
