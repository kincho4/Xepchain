import requests

def broadcast(signed_tx: str):
    url = "https://api.mainnet-beta.solana.com"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [
            signed_tx,
            {"encoding": "base58"}
        ]
    }
    
    response = requests.post(url, json=payload)
    return response.json()