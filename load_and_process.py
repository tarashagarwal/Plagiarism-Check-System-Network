import boto3
from copydetect import CopyDetector
import os

aws_access_key_id='ASIAYVSO3UBVF2W3BIG7'
aws_secret_access_key='P83usLZN5l9u7twEKAWbvPcVLxy8/cq2ttuyFL61'
aws_session_token='FwoGZXIvYXdzEKH//////////wEaDK8k2C4Nzw3aakz0qiLAAUsRGX7Rk1ksz8UWuEKfzvXR9l+/O9c29Ptkh/2K77sx3tor8p1O/ujTK3Zbw3m8cmL1CQ9gFRCqaoZ9jCw/G/8y9Mm7IXgpxCl6PzP/K7urX84zX6H0PqxLGzEVFtXFjBVJAUSK9ChRWzv1mr5XmFoVn4WMbhMOTafYxAJKc22tmfH/+3X3Hy1/2Z6tmz7IGG8vi1c5K8Ix06Sop3f00+V66tgewkWblIAtjccYjbECj4k0zbiHA1UklWpcXfqrtCixtcuhBjItD8o6yfgmtnaB/xEcTkyQQN/dT3AXh15MOYOK+VJKDHxI8vZBvkKSsVjVa2P9'

def append_to_file(message):
    with open("/tmp/output.logs", 'a') as f:
        f.write(message + '\n')
    print(message)

# Set up SQS client
sqs = boto3.client('sqs', region_name='us-east-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,aws_session_token=aws_session_token)

queue_name = 'pcsn-sqs-queue'
response = sqs.get_queue_url(QueueName=queue_name)
queue_url =  response['QueueUrl']

# Set up S3 client
s3 = boto3.client('s3', region_name='us-east-1',aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,aws_session_token=aws_session_token)

source_bucket_name = 'pdsn-raw-documents'
destination_bucket_name = 'pdsn-processed-documents'

# Set up SNS client
sns = boto3.client('sns', region_name='us-east-1',aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,aws_session_token=aws_session_token)

topic_name = 'document-processed'

response = sns.list_topics()
topics = response['Topics']
for topic in topics:
    if topic['TopicArn'].split(':')[-1] == topic_name:
        topic_arn =  topic['TopicArn']
        break

# Receive messages from SQS queue
while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )

    # Check if there are any messages in the response
    if 'Messages' in response:
        for message in response['Messages']:

            append_to_file("Processing Message for filename:" + message['Body'])

            receipt_handle = message['ReceiptHandle']

            # Get the filename from the message body
            filename = message['Body']

            # Download the file from S3
            s3.download_file(source_bucket_name, filename, '/tmp/' + filename)

            detector = CopyDetector(test_dirs=["/tmp/"], extensions=["txt"], display_t=0.5)
            detector.run()
            detector.generate_html_report()

            append_to_file("Uploading Report to S3")

            append_to_file("Clearing Files Up")

            # Upload the file to the destination bucket
            s3.upload_file('report.html', destination_bucket_name, filename + "_report.html")

            s3.delete_object(Bucket=source_bucket_name, Key=filename)

            file_path = "report.html"

            os.remove(file_path)

            # Send an SNS message
            append_to_file("Publishing file to Topic:" + topic_arn)

            sns.publish(
                TopicArn=topic_arn,
                Message='File ' + filename + ' has been processed from ' + source_bucket_name + ' and report puublished to ' + destination_bucket_name
            )

            append_to_file("Cleaning Up Queues")

            # Delete the message from the queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
    else:
        append_to_file('No messages in the queue')



