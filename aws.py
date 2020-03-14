import boto3
import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
phone_number = '16127502017'  # change it to your phone number
default_lease_minutes = 180

def terminate_instance(instance):
    message = "terminating:" + instance.id +" "+ instance.state['Name'] +"  "
    instance.terminate()
    return message

def get_lease(instance):
    tags_dict = {t['Key']: t['Value'] for t in instance.tags}
    try:
        lease_minutes = tags_dict['lease_minutes']
    except KeyError:
        lease_minutes = default_lease_minutes

def get_expired_instances(ec2):
    expired_instances = []
    instances = ec2.instances.all()
    for instance in instances:
        lease_minutes = get_lease(instance)
        killtime = datetime.timedelta(minutes=lease_minutes)
        tz = instance.launch_time.tzinfo
        datetime_now = datetime.datetime.now(tz)
        if datetime_now - instance.launch_time > killtime:
            expired_instances.append(instance)
    return expired_instances

def lambda_handler(event, context):
    logger.info('Received event: ' + json.dumps(event))
    result = ""
    regions = ['us-east-1','us-east-2']
    for region in regions:
        ec2 = boto3.resource('ec2', region_name=region)
        expired_instances = get_expired_instances(ec2)
        for instance in expired_instances:
            result += terminate_instance(instance)

    if result is not "":
        sns.publish(PhoneNumber=phone_number, Message="lablease Deleted instances:" + result)
        logger.info('SMS has been sent to ' + phone_number)

    return result
