import logging
import subprocess


def perform_rsync(src: str, dst: str, user: str, hostname: str, key_file: str):
    command = f'rsync -rae "ssh -o StrictHostKeyChecking=no -i {key_file}" {src} ' \
              f'{user}@{hostname}:/ebs-cargo-data/{dst} --progress --keep-dirlinks'

    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        logging.info(stdout_line)

    popen.stdout.close()

    return_code = popen.wait()

    if return_code:
        raise subprocess.CalledProcessError(return_code, command)