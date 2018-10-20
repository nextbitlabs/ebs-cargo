import logging

import paramiko as paramiko


class Ssh:
    def __init__(self, hostname: str, key: str):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(hostname, username='ubuntu', key_filename=key)

    def exec_command(self, command: str):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)

        for line in stdout.readlines():
            logging.info(line)

        for line in stderr.readlines():
            logging.error(line)

    def format_volume(self, filesystem: str):
        logging.info('Formatting EBS volume')
        self.exec_command(f'sudo mkfs -t {filesystem} /dev/sdk')

    def mount_volume(self):
        logging.info('Mounting EBS')
        self.exec_command('sudo mkdir /ebs-cargo-data')
        self.exec_command('sudo mount /dev/sdk /ebs-cargo-data')

    def create_directory(self, dst: str):
        logging.info('Creating directory')
        self.exec_command(f'sudo mkdir -p /ebs-cargo-data/{dst}')