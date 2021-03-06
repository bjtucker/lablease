import boto3
import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client("sns")
phone_number = "16127502017"  # change it to your phone number
default_lease_minutes = 180


def terminate_instance(instance):

    logger.info("Terminating instance: " + instance.id)
    message = "terminating:" + instance.id + " " + instance.state["Name"] + "  "
    instance.terminate()
    return message


def get_lease(instance):

    logger.info("Checking lease for instance: " + instance.id)
    tags_dict = {t["Key"]: t["Value"] for t in instance.tags}
    try:
        lease_minutes = int(tags_dict["lease_minutes"])
    except (KeyError, ValueError) as e:
        lease_minutes = default_lease_minutes
    logger.info("Lease: " + str(datetime.timedelta(minutes=lease_minutes)))
    return lease_minutes

def get_expired_instances(ec2):
    expired_instances = []
    instances = ec2.instances.all()
    for instance in instances:
        lease_minutes = get_lease(instance)
        killtime = datetime.timedelta(minutes=lease_minutes)
        tz = instance.launch_time.tzinfo
        datetime_now = datetime.datetime.now(tz)
        time_running = datetime_now - instance.launch_time
        logger.info("Time running: " + str(time_running))
        time_remaining = killtime - time_running
        logger.info("Time remaining: " + str(time_remaining))


        if time_remaining < datetime.timedelta(minutes=0):
            expired_instances.append(instance)
    return expired_instances


def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event))
    result = ""
    regions = ["us-east-1", "us-east-2"]
    for region in regions:
        logger.info("Scanning region: " + region)
        ec2 = boto3.resource("ec2", region_name=region)
        expired_instances = get_expired_instances(ec2)
        for instance in expired_instances:
            result += terminate_instance(instance)

    if result is not "":
        sns.publish(
            PhoneNumber=phone_number, Message="lablease Deleted instances:" + result
        )
        logger.info("SMS has been sent to " + phone_number)

    return result
