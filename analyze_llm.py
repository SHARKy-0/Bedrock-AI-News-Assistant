# agent2_llm.py
import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
region = os.getenv("AWS_REGION", "ap-southeast-2")


client = boto3.client(
    'bedrock-runtime',
    region_name=os.getenv("AWS_REGION"),
)



def analyze_news(news_json):
    print(news_json)
    prompt = f"Below is a list of news articles. Please analyze their market impact and provide investment recommendations.:\n{news_json}"
    
    response = client.invoke_model(
        modelId='amazon.titan-text-express-v1',
        body=json.dumps({"inputText": prompt}),
        contentType='application/json'
    )
    
    result = response['body'].read().decode()
    return result

def analyze_in_chunks(news_list, chunk_size=300):
    results = []
    for news in news_list:
        paragraphs = news.split("。")  
        for i in range(0, len(paragraphs), chunk_size):
            chunk = "。".join(paragraphs[i:i+chunk_size])  
            prompt = f"Analyze the following news and provide market impact and investment recommendations:\n{chunk}"
            result = analyze_news(prompt)
            results.append(result)
    return results
