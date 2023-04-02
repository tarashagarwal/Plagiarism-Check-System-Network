import boto3

aws_access_key_id='ASIAYVSO3UBVDPFCUSUW'
aws_secret_access_key='ZSVnPB6ORddih+phuGkn5DkLr0YYSrbkXUJfO2e+'
aws_session_token='FwoGZXIvYXdzEPr//////////wEaDNtod3ucb8eIB4hOOCLAAahyWS2p4tmqQ4ZxQ9rUjSI2F0DFVOZFh/hpDiUUW0KpcbenpXzYH08OMgI6IGdLvGVUopT8qXeKV4reRi+A5t2JLGFkZEW1ZXP3kuVrBeumNYxuU5MYPIBt4vgAD7XkG88RZxohrgVL8jEryLnN76vO8VN6sF3tjNyi8j/rlmpI0eHCQTACSmfvz609LxiLq1B+a6Zqn1VN89E9gtHQFyphC2y1Qhiadr22sooQKOnOGJ1MPgqhZkVk1K0AREM4cijx16ahBjItbahxK9wmXWKRBWX/9qu2YpUhjNHeoufoVIvO9bhaQDod2/Hqspc59li1LVEK'

def append_to_file(message):
    with open("/tmp/output.logs", 'a') as f:
        f.write(message + '\n')

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

            # Upload the file to the destination bucket
            s3.upload_file('/tmp/' + filename, destination_bucket_name, filename)

            s3.delete_object(Bucket=source_bucket_name, Key=filename)

            # Send an SNS message
            append_to_file("Publishing file to Topic:" + topic_arn)

            sns.publish(
                TopicArn=topic_arn,
                Message='File ' + filename + ' has been transferred from ' + source_bucket_name + ' to ' + destination_bucket_name
            )

            # Delete the message from the queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
    else:
        append_to_file('No messages in the queue')



