import json
import urllib.parse
import boto3
import requests 
from datetime import datetime
# from botocore.vendored import requests
from botocore.exceptions import ClientError
# import urllib3
# from requests_aws4auth import AWS4Auth
# from elasticsearch import Elasticsearch

print('Loading function')

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

# Update these variables with your AWS region, Amazon ES endpoint, and index name
REGION = 'us-west-2'
ES_ENDPOINT = 'https://search-photos-lstzdko5g6jwk4pyb2kwunzz6y.us-west-2.es.amazonaws.com'
INDEX_NAME = 'photos'
ES_USER = 'masteruser'
ES_PASS = '#EasyPass01'
ES_URL = ES_ENDPOINT
# es = Elasticsearch()
# awsauth = AWS4Auth('AKIAWNZY5YQYWZ33WA27', 'CDObKUxh+VUEKwX/StmaEY6sbs+9mXY0dvvRjF28', REGION, 'es')
# http = urllib3.PoolManager()
headers = {
    'Content-Type': 'application/json',
}

def lambda_handler(event, context):
    print("event : ", event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    try:
        # Get the object from S3
        response = s3.get_object(Bucket=bucket, Key=key) 
        image_content = response['Body'].read()

        # Call Rekognition to detect labels
        rekognition_response = rekognition.detect_labels(
            Image={
                'Bytes': image_content
            }
        )

        # Process labels found in the image
        labels_detected = []
        if 'Labels' in rekognition_response and len(rekognition_response['Labels']) > 0:
            labels_detected = [label['Name'] for label in rekognition_response['Labels']]
            print('Labels detected:', labels_detected)

        # Create a JSON object for Elasticsearch
        es_data = {
            'objectKey': key,
            'bucket': bucket,
            'createdTimestamp': response['LastModified'].isoformat(),  # ISO8601 format
            'labels': labels_detected
        }

        # AWS authentication
        # awsauth = AWS4Auth('', 'YOUR_SECRET_KEY', REGION, 'es')
        # headers = {"Content-Type": "application/json"}
        # response = requests.put(ES_URL, headers=headers, data=es_data, auth=(ES_USER, ES_PASS))

        # Store JSON object in Amazon ES
        url = f"{ES_ENDPOINT}/{INDEX_NAME}/_doc"
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, headers=headers, data=json.dumps(es_data), auth=(ES_USER,ES_PASS))
        print("r : ", r, " and content of r : ", r.content)
        # response = http.request('POST',url,body=json.dumps(es_data),header=headers)
        

        return {
            'statusCode': 200,
            'body': json.dumps({'LabelsDetected': labels_detected})
        }
    except Exception as e:
        print('Error processing labels or storing in Amazon ES:', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'Error': 'Error processing labels or storing in Amazon ES.'})
        }


