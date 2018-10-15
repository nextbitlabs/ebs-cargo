import boto3
import argparse
import logging

from AwsResources import AwsResources

parser = argparse.ArgumentParser(description='Load data on an AWS EBS volume')
parser.add_argument('--existing-volume', help='specifies an already existing EBS volume by its '
                                              'Volume ID')
parser.add_argument('--existing-instance', help='specifies an already existing EC2 instance to use '
                                                'to load data. If none is specified, a new one '
                                                'will be create and destroyed at the end of the '
                                                'process')
parser.add_argument('--volume-name', help='specifies a name for the volume')
parser.add_argument('--availability-zone', help='the Availability Zone in which to create the '
                                                'volume (default: %(default)s)',
                    default='eu-central-1a')
parser.add_argument('--encrypted', help='specifies whether the volume should be encrypted',
                    action='store_true')
parser.add_argument('--iops', help='the number of I/O operations per second (IOPS) to provision '
                                   'for the volume. This parameter is valid only for Provisioned '
                                   'IOPS SSD (io1) volumes. (default: %(default)s)', type=int)
parser.add_argument('--size', help='The size of the volume, in GiBs. (default: %(default)s)',
                    type=int, default=1024)
parser.add_argument('--volume-type', help='The volume type. This can be gp2 for General Purpose '
                                          'SSD, io1 for Provisioned IOPS SSD, st1 for Throughput '
                                          'Optimized HDD, sc1 for Cold HDD, or standard for '
                                          'Magnetic volumes. (default: %(default)s)',
                    choices=['gp2', 'io1', 'st1', 'sc1' 'standard'], default='gp2')
parser.add_argument('--region-name', help='If specified, overrides the default region zone '
                                          'specified in the credentials file')
parser.add_argument('--verbose', action='store_true', help='More verbose logging')
parser.add_argument('--debug', action='store_true', help='Log everything for debugging purpose')

args = parser.parse_args()

logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO if args.verbose else logging.WARNING)

aws = AwsResources(args)

logging.info(boto3.client('sts').get_caller_identity())

volume_id = args.existing_volume

if volume_id is None:
    result = aws.create_ebs()

    if result == -1:
        raise Exception('Critical error, aborting.')

    logging.warning(f'EBS volume created successfully with ID {result["VolumeId"]}')

    volume_id = result["VolumeId"]

instance_id = args.existing_instance
delete_instance_at_end = instance_id is None

if instance_id is None:
    result = aws.create_instance()

    if result == -1:
        raise Exception('Critical error, aborting.')

    logging.warning(f'EBS volume created successfully with ID {result["VolumeId"]}')

    instance_id = result["VolumeId"]

aws.attach_ebs_to_instance(volume_id, instance_id)