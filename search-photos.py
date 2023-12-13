
import logging
import base64
import json
import boto3
import os
import time
import requests
import math
import dateutil.parser
import datetime
import requests


ES_URL = "https://search-photos-lstzdko5g6jwk4pyb2kwunzz6y.us-west-2.es.amazonaws.com/photos/_doc"
ES_USER = 'masteruser'
ES_PASS = '#EasyPass01'

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

headers = {"Content-Type": "application/json"}
host = ES_URL
region = 'us-west-2'
lex = boto3.client('lexv2-runtime', region_name=region)


def lambda_handler(event, context):

    print("EVENT --- {}".format(json.dumps(event)))
    q1 = event['queryStringParameters']['q']

    print("q1:", q1)
    labels = get_labels(q1)
    print("labels", labels)
    if len(labels) == 0:
        return
    else:
        img_paths = get_photo_path(labels)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'imagePaths': img_paths,
            'userQuery': q1,
            'labels': labels,
        }),
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        "isBase64Encoded": False
    }


def get_labels(query):
    response = lex.recognize_text(
        botId='P8YO6XWJEF',
        botAliasId='TSTALIASID',
        localeId="en_US",
        text=query,
        sessionId="amhijetomachichichi"
    )
    print("lex-response : {}".format(json.dumps(response)))

    labels = []
    if 'slots' not in response['interpretations'][0]['intent']:
        print("No photo collection for query {}".format(query))
    else:
        print("slot: ", response['interpretations'][0]['intent'])
        slot_val = response['interpretations'][0]['intent']['slots']
        for key, value in slot_val.items():
            if value != None:
                labels.append(value['value']['resolvedValues'][0])
    return labels


def get_photo_path(labels):
    img_paths = []
    unique_labels = set(labels)
    labels = tuple(unique_labels)
    print("inside get photo path ", labels)
    for i in labels:
        path = host + '/_search?q=labels:'+i
        print(path)
        response = requests.get(path, headers=headers,
                                auth=(ES_USER, ES_PASS))
                                
        print("response from ES", response)
        dict1 = json.loads(response.text)
        hits_count = dict1['hits']['total']['value']
        print("DICT : ", dict1)
        
        for k in range(0, hits_count):
            img_obj = dict1["hits"]["hits"]
            img_bucket = dict1["hits"]["hits"][k]["_source"]["bucket"]
            print("img_bucket", img_bucket)
            img_name = dict1["hits"]["hits"][k]["_source"]["objectKey"]
            print("img_name", img_name)
            img_link = 'https://s3.amazonaws.com/' + \
                str(img_bucket) + '/' + str(img_name)
            print(img_link)
            img_paths.append(img_link)
            
    print("img paths : ", img_paths)
    return img_paths
