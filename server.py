from flask import Flask, request, jsonify
import uuid
import sqlite3
from datetime import datetime
import main

app = Flask(__name__)


"""
'currency':'USDC/BTC/ETH/...' <--- this is the value of what the order should be created to recieve on creation
'amount':'67.76' 
'wallets':{'LTC':'...', 'EVM':'...', ...}
'webhook':'https://sigmaportal.com/listener'
"""
import re

def validate(address, type):
    patterns = {
        "BTC": r"^(1|3)[a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$",
        "LTC": r"^(L|M)[a-km-zA-HJ-NP-Z1-9]{26,33}$|^ltc1[a-z0-9]{39,59}$",
        "BCH": r"^(bitcoincash:)?(q|p)[a-z0-9]{41}$|^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$",
        "EVM":  r"^0x[a-fA-F0-9]{40}$",  # ETH, BNB, MATIC, any EVM chain
        "SOL":  r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",
        }

    pattern = patterns.get(type.upper())
    if pattern is None:
        raise ValueError(f"Unsupported address type: {type}")
    return bool(re.match(pattern, address))

@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.get_json("orders.db")
    currency = data.get("currency")
    amount = data["amount"]
    wallets = data["wallets"]
    primary = next(iter(data["wallets"]))
    webhook = data.get("webhook")
    order_id = str(uuid.uuid4())

    coins = ", ".join(wallets.keys())
    placeholders = ", ".join("?" * len(wallets))

    if not all(validate(value, key) for key, value in wallets.items()):
        return 406

    try:
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO admin (time, order_id, main, {coins}, webhook) VALUES (?, ?, ?, ?, {placeholders})", (datetime.now().strftime("%H:%M %d/%m/%Y"), order_id, primary, *wallets.values(), webhook))
        cursor.execute(f"INSERT INTO client (time, order_id) VALUES (?, ?)", (datetime.now().strftime("%H:%M %d/%m/%Y"), order_id))
        conn.commit()
        conn.close()
    except Exception as e:
        return 400

    return jsonify({"order_id": order_id}), 200

"""
'order-id':'67926405-abab-4553-9de1-2a835b368eb5'
'type':'EVM'
"""
@app.route('/get-address', methods=['POST'])
def get_address():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()

    data = request.get_json()
    order_id = data["order-id"]
    type = data["type"]

    cursor.execute(f"SELECT {type} FROM client WHERE order_id = ?", (order_id,))
    wallet = cursor.fetchone()
    print(wallet)

    if wallet != (None,):
        return jsonify({type:wallet}), 200
    else:
        address = main.WalletGen(type).address
        cursor.execute(f"UPDATE client SET time = ?, {type} = ? WHERE order_id = ?", (datetime.now().strftime("%H:%M %d/%m/%Y"), address, order_id))
        conn.commit()
        conn.close()
        return jsonify({type:address}), 201

"""
'order-id':'67926405-abab-4553-9de1-2a835b368eb5'
"""
@app.route('/get-link', methods=['POST'])
def get_link():
    data = request.get_json()
    order_id = data["order-id"]

    return jsonify({}), 200

"""
'order-id':'67926405-abab-4553-9de1-2a835b368eb5'
"""
@app.route('/order-status', methods=['POST'])
def order_status():
    data = request.get_json()
    order_id = data.get("order-id")
    if not order_id:
        return jsonify({"error": "order-id required"}), 400

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    cursor.execute("SELECT * FROM admin WHERE order_id = ?", (order_id,))
    admin = cursor.fetchone()
    if not admin:
        conn.close()
        return jsonify({"error": "order not found"}), 404


    cursor.execute("SELECT * FROM client WHERE order_id = ?", (order_id,))
    client = cursor.fetchone()


    cursor.execute("SELECT time, from_cc, to_cc, txid, via, via_info FROM payouts WHERE order_id = ?", (order_id,))
    payouts = [dict(row) for row in cursor.fetchall()]
    conn.close()

    coin_types = ["LTC", "BTC", "BCH", "EVM", "SOL"]
    merchant_wallets = {c: admin[c] for c in coin_types if admin[c]}

    addresses = {}
    if client:
        addresses = {c: client[c] for c in coin_types if client[c]}

    if payouts:
        status = "completed"
    elif addresses:
        status = "awaiting_payment"
    else:
        status = "pending"

    return jsonify({
        "order_id": order_id,
        "status": status,
        "created": admin["time"],
        "main": admin["main"],
        "merchant_wallets": merchant_wallets,
        "addresses": addresses,
        "webhook": admin["webhook"],
        "payouts": payouts
    }), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6767, debug=False)