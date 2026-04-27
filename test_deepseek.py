# -*- coding: utf-8 -*-
import boto3
import json
import os

client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

body = json.dumps({
    'messages': [{'role': 'user', 'content': 'Say hi'}],
    'inferenceConfig': {'max_new_tokens': 100, 'temperature': 0.7}
})

resp = client.invoke_model(modelId='deepseek.v3.2', body=body)
response_body = json.loads(resp['body'].read())

with open('deepseek_response.json', 'w', encoding='utf-8') as f:
    json.dump(response_body, f, indent=2, ensure_ascii=False)

print("Response saved to deepseek_response.json")
print("Keys:", list(response_body.keys()))
