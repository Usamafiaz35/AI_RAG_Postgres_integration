import requests

url = "http://127.0.0.1:8000/query"
payload = {"query": "What was the revenue last month?"}
resp = requests.post(url, json=payload)
print(resp.json())
