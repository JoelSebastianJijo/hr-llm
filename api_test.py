import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("API_KEY")

print(f"Using API key: {api_key}")

url = "https://jsonplaceholder.typicode.com/posts/1"

response = requests.get(url)

print(json.dumps(response.json(), indent=4))