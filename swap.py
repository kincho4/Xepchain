import hmac
import json
import hashlib
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
API_SECRET = os.getenv("FIXEDFLOAT_API_SECRET")
API_KEY = os.getenv("FIXEDFLOAT_API_KEY")
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

ref = ""

def sign(data):
    return hmac.new(
      key=API_SECRET.encode(),
      msg=data.encode(),
      digestmod=hashlib.sha256
    ).hexdigest()
  
  
def request(method, params={}):
    url = 'https://ff.io/api/v2/' + method
    data = json.dumps(params)
    headers = {
      'X-API-KEY': API_KEY,
      'X-API-SIGN': sign(data)
    }
    r = requests.post(url, data=data, headers=headers)
    return r.json()

def rate(curfrom, curto, amount):
    req = request("price", {"type":"float", "fromCcy":curfrom, "toCcy":curto, "direction":"from", "amount":amount, "refcode":ref})
    data = {
        "min":req["data"]["from"]["min"],
        "max":req["data"]["from"]["max"],
        "rate":req["data"]["from"]["rate"],
        "amount":req["data"]["to"]["amount"]
    }
    return data if req["code"] == 0 else f"FAILED: {req["msg"]}"
#{'min': 0.19318, 'max': 1564.13046, 'rate': 0.025893, 'amount': 0.129463}

def create(curfrom, curto, amount, addressto):
    req = request("create", {"type":"float", "fromCcy":curfrom, "toCcy":curto, "direction":"from", "amount":amount, "toAddress":addressto, "refcode":ref})
    data = {
        "order_token":req["data"]["token"],
        "order_id":req["data"]["id"],
        "deposit":req["data"]["from"]["address"],
        "deposit_amount":req["data"]["from"]["amount"]
    }
    return data if req["code"] == 0 else f"FAILED: {req["msg"]}"
#{'order_token': 'Hi2byfp1o3mrS139fVazzYLK9hR4rEaOskIPim9t', 'order_id': '42Q8YB', 'deposit': '0xa4627eeb93bb283f4e96c176aa830452c97a0afb', 'deposit_amount': '1.00000000'}

def poll(id, token, order_id):
    req = request("order", {"id":id, "token":token})
    last = req["data"]["status"]
    while req["data"]["status"] != last:
        req = request("order", {"id":id, "token":token})
        time.sleep(15)
    if req["data"]["status"] == "EMERGENCY":
            resp = requests.post(WEBHOOK, json={"content":f"EMERGENCY:\nORDER-ID: {order_id}"}, timeout=10)
            if resp.status_code != 204:
                print(f"Discord webhook error: {resp.status_code} {resp.text}")

    return req["data"]["status"]