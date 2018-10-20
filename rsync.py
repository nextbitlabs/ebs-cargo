import logging
import subprocess


def perform_rsync(src: str, hostname: str, key_file: str, dst: str = ''):
    command = f'rsync -rave --progress "ssh -i {key_file}" {src} ubuntu@{hostname}:/dev/sdk/{dst}'

    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        logging.info(stdout_line)

    popen.stdout.close()

    return_code = popen.wait()

    if return_code:
        raise subprocess.CalledProcessError(return_code, command)