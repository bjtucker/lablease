import boto3
import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
phone_number = '16127502017'  # change it to your phone number

def terminate_instance(instance):
    message = "terminating:" + instance.id +" "+ instance.state['Name'] +"  "
    instance.terminate()
    return message

def lambda_handler(event, context):
    logger.info('Received event: ' + json.dumps(event))
    killtime = datetime.timedelta(minutes=180)
    result = ""
    ec2 = boto3.resource('ec2', region_name='us-east-1')
#   volumes = ec2.volumes.all()
#   volume_ids = [v.id for v in volumes]
    instances = ec2.instances.all()
    for instance in instances:
        tz = instance.launch_time.tzinfo
        datetime_now = datetime.datetime.now(tz)

        if datetime_now - instance.launch_time > killtime:
            result += terminate_instance(instance)

    if result is not "":
        sns.publish(PhoneNumber=phone_number, Message="lablease Deleted instances:" + result)
        logger.info('SMS has been sent to ' + phone_number)

    return result


