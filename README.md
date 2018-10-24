**WARNING: this software is in pre-alpha. The happy flow works, but not all the flags combinations have been tested.**

**BE CAREFUL USING IT WITH ALREADY EXISTING EBS VOLUMES, DATA CAN BE LOST IF YOU SPECIFY AS TARGET AN ALREADY EXISTING DIRECTORY**

Please test it and report issues, patches are more than welcome.

# ebs-cargo

A small utility to simplify loading GBs of data in an EBS volume on AWS.

When you want to load data on a new EBS volume, lots of operations have to be done: logging in AWS, creating a volume, creating an instance, attaching the volume, formatting it, mounting it, downloading instance keys, using them to sync data, detaching the EBS and so on.

Wouldn't be easier just having to launch a command indicating which local directory you want to upload?

Thanks to EBS-Cargo you can do that!

## Setup

After cloning the repo (we are working on other ways to distribuite the program), you need to configure your AWS credentials.

You can read the [full guide on the AWS website](https://boto3.amazonaws.com/v2/documentation/api/latest/guide/quickstart.html#configuration) or simply create a file in `~/.aws/credentials` and insert:

```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

You also need to install some requirements:

```
pip install -r requirements.txt --user
```

## Usage

The simplest usage is launching the main.py indicating which directory you want to sync:

```
python3 main.py ~/clone-this
```

Sane defaults are set for all the options.

You can see all the available options using:

```
python3 main.py --help
```

Creating a new 100 GBs EBS in us-east-1 and call it *nextbit*, with detailed logs:

```
python3 main.py --verbose --size 100 --volume-name nextbit --region us-east-1 ~/clone-this 
```
