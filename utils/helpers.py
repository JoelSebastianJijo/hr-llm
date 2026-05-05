import requests

response = requests.get("https://httpbin.org/get")
print("GET Response:")
print(response.json())

data = {
    "name": "Sheza",
    "role": "intern"
}
response = requests.post("https://httpbin.org/post", json=data)
print("\nPOST Response:")
print(response.json())