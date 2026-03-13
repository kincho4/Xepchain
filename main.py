from bip_utils import *
import requests
import os
from dotenv import load_dotenv
import gnupg
from datetime import datetime, timedelta
import sqlite3
import time
from decimal import Decimal
import base58
import base64

# Ethereum
from web3 import Web3

# Solana
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction as SolTransaction
from solders.message import Message
from solders.hash import Hash

# XRP
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import autofill_and_sign
from xrpl.clients import JsonRpcClient

# UTXO
from bitcoinlib.keys import Key
from bitcoinlib.transactions import Transaction

load_dotenv()

cg_map = {
    "BTC": "bitcoin",
    "LTC": "litecoin",
    "ETH": "ethereum",
    "POL": "polygon-ecosystem-token",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "BCH": "bitcoin-cash",
    "USDC": "usd",
    "USDT": "usd",
    "USD": "usd",
    "EUR": "eur",
    "GBP": "gbp"
}

blockchair_map = {
    "BTC": "bitcoin",
    "LTC": "litecoin",
    "ETH": "ethereum",
    "BNB": "binance-smart-chain",
    "SOL": "solana",
    "XRP": "ripple",
    "BCH": "bitcoin-cash",
}

coin_decimals = {
    "BTC": 100000000,
    "LTC": 100000000,
    "BCH": 100000000,
    "EVM": 10**18,
    "SOL": 10**9,
    "XRP": 1000000,
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 1000000, #usdc
    "0xdac17f958d2ee523a2206206994597c13d831ec7": 1000000, #usdt
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": 10**18 #dai
}

coin_confirmations = {
    "BTC": 6,
    "LTC": 12,
    "BCH": 15,
    "ETH": 12,
    "BNB": 25,
    "SOL": 1,
    "XRP": 1,
}

BROADCAST_PATHS = {
    "BTC": "/bitcoin/broadcast",
    "LTC": "/litecoin/broadcast",
    "BCH": "/bcash/broadcast",
    "ETH": "/ethereum/broadcast",
    "SOL": "/solana/broadcast",
    "XRP": "/xrp/broadcast",
}

UTXO_CHAINS = {
    "BTC": {"network": "bitcoin", "tatum": "bitcoin"},
    "LTC": {"network": "litecoin", "tatum": "litecoin"},
    "BCH": {"network": "bitcoin_cash", "tatum": "bcash"},
}

ERC20_TOKENS = {
    "USDT": {"address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
    "USDC": {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6},
    "DAI": {"address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "decimals":18}
}

def get_price(crypto, pair="USDC"):
    def clean_mean(vals):
        v = vals[:]
        while len(v) > 1:
            m = sum(v)/len(v)
            worst = max(v, key=lambda x: abs(x-m))
            if abs(worst-m)/m > 0.01:
                v.remove(worst)
            else:
                break
        if not v:
            return round(sum(vals)/len(vals), 2)
        return round(sum(v)/len(v), 2)

    prices = []
    try:    
        ## DATA SOURCE 1
        cc={"fsyms": crypto, "tsyms": pair}
        cc_req = requests.get(
        "https://min-api.cryptocompare.com/data/pricemultifull",
        params=cc,
        headers={"accept": "application/json"}
        ).json()
        prices.append(round(float(cc_req["RAW"][crypto][pair]["PRICE"]), 2))
    except Exception as e:
        print(e)
    
    try:
        ## DATA SOURCE 2
        coingecko = {
        "ids": cg_map[crypto],
        "vs_currencies": cg_map[pair]
        }
        cg_req = requests.get("https://api.coingecko.com/api/v3/simple/price", params=coingecko, headers={"x-cg-pro-api-key": os.getenv("COINGECKO_API_KEY")}).json()
        prices.append(round(float(cg_req[cg_map[crypto]][cg_map[pair]]), 2))
    except Exception as e:
        print(e)
    
    try:
        ## DATA SOURCE 3
        binance = {"symbol": f"{crypto}{pair}"}
        binance_req = requests.get("https://api.binance.com/api/v3/ticker/price", params=binance).json()
        prices.append(round(float(binance_req["price"]), 2))
    except Exception as e:
        print(e)

    return clean_mean(prices)

class WalletGen:
    def __init__(self):
        self.mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
        self.seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()

    def _encrypt(self, msg):
        gpg = gnupg.GPG()
        with open("public.asc", "r") as f:
            result = gpg.import_keys(f.read())
        encrypted = gpg.encrypt(msg, recipients=[result.fingerprints[0]], always_trust=True)
        return str(encrypted)
    
    def _save(self, address, private_key, type):
        conn = sqlite3.connect("wallets.db")
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {type} VALUES (?, ?, ?)", (f"{datetime.now().strftime("%M:%H %d/%m/%Y")}", address, self._encrypt(private_key)))
        conn.commit()
        conn.close()

    def _generate_wallet(self, coin_type):
        bip_obj = Bip44.FromSeed(self.seed_bytes, coin_type)
        account = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

        return {
            "address": account.PublicKey().ToAddress(),
            "private_key": account.PrivateKey().Raw().ToHex(),
            "expiry": datetime.now() + timedelta(hours=1)
        }
    
    def generate_BTC(self): # p2pkh
        key_pair = self._generate_wallet(Bip44Coins.BITCOIN)
        self._save(key_pair["address"], key_pair["private_key"], "BTC")
        return key_pair
    
    def generate_LTC(self):
        key_pair = self._generate_wallet(Bip44Coins.LITECOIN)
        self._save(key_pair["address"], key_pair["private_key"], "LTC")
        return key_pair
    
    def generate_EVM(self):
        key_pair = self._generate_wallet(Bip44Coins.ETHEREUM)
        self._save(key_pair["address"], key_pair["private_key"], "EVM")
        return key_pair
    
    def generate_XRP(self):
        key_pair = self._generate_wallet(Bip44Coins.RIPPLE) 
        self._save(key_pair["address"], key_pair["private_key"], "XRP")
        return key_pair
    
    def generate_BCH(self):
        key_pair = self._generate_wallet(Bip44Coins.BITCOIN_CASH)
        self._save(key_pair["address"], key_pair["private_key"], "BCH")
        return key_pair
    
    def generate_SOL(self):
        key_pair = self._generate_wallet(Bip44Coins.SOLANA)

        full_keypair = bytes.fromhex(key_pair["private_key"]) + base58.b58decode(key_pair["address"])
        key_pair["private_key"] = base58.b58encode(full_keypair).decode()

        self._save(key_pair["address"], key_pair["private_key"], "SOL")
        return key_pair

class WalletScan:
    def __init__(self, address, type, expiry):
        self.address = address.lower() if type in ["ETH"] else address
        self.type = type
        self.expiry = expiry
        self.isEVM = self.type in ["ETH"]
        self.confirmations = coin_confirmations[self.type]
    
    def _convert(self, balance, decimals=""):
        return float(Decimal(balance) / ((coin_decimals["EVM" if self.isEVM else self.type]) if decimals =="" else decimals))
    
    def scan(self):
        while datetime.now() < self.expiry:
            try:
                time.sleep(10)
                if self.isEVM:
                    result = self._check_evm()
                elif self.type == "SOL":
                    result = self._check_sol()
                elif self.type == "XRP":
                    result = self._check_xrp()
                else:
                    result = self._check_utxo()
                if result:
                    return result
                print(",")
            except Exception as e:
                print(e)
                time.sleep(3)
        return {"detected": False}

    def _check_utxo(self):
        url = f"https://api.blockchair.com/{blockchair_map[self.type]}/dashboards/address/{self.address}?key={os.getenv("BLOCKCHAIR_API_KEY")}"
        data = requests.get(url).json()
        addr = data["data"][self.address]
        if addr["address"]["balance"] > 0:
            return {
                "detected": True,
                "balance": self._convert(addr["address"]["balance"]),
                "tx_hash": addr["transactions"][0],
                "confirmed": (addr.get("utxo", [{}])[0].get("block_id", -1) != -1) and (data["context"]["state"] - addr.get("utxo", [{}])[0].get("block_id", -1) + 1) >= self.confirmations
            }

    def _check_evm(self):
        url = f"https://api.blockchair.com/{blockchair_map[self.type]}/dashboards/address/{self.address}?key={os.getenv('BLOCKCHAIR_API_KEY')}&transactions_instead_of_calls=true&erc_20=true"
        data = requests.get(url).json()
        addr = data["data"][self.address]

        if int(addr["address"]["balance"]) > 0:
            return {
                "detected": True,
                "balance": self._convert(addr["address"]["balance"]),
                "tx_hash": addr["transactions"][0] if addr.get("transactions") else None,
                "confirmed": True
            }

        for token in addr.get("layer_2", {}).get("erc_20", []):
            if token["balance"] != "0":
                return {
                    "detected": True,
                    "balance": self._convert(token["balance"], coin_decimals[token["token_address"]]),
                    "token": token["token_address"],#
                    "confirmed": True
                }
            
    def _check_sol(self):
        resp = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [self.address]
        })

        if resp.status_code != 200 or not resp.text:
            return None

        data = resp.json()
        balance = data.get("result", {}).get("value", 0)

        if balance > 0:
            return {
                "detected": True,
                "balance": balance / 10**9,
                "confirmed": True
            }
        
    def _check_xrp(self):
        resp = requests.post("https://s1.ripple.com:51234/", json={
            "method": "account_info",
            "params": [{
                "account": self.address,
                "ledger_index": "validated"
            }]
        })

        if resp.status_code != 200 or not resp.text:
            return None

        data = resp.json()
        result = data.get("result", {})

        if result.get("status") == "success":
            balance = int(result["account_data"]["Balance"])
            if balance > 0:
                return {
                    "detected": True,
                    "balance": balance / 1_000_000,
                    "confirmed": True
                }

class WalletSend:
    def __init__(self, private_key, type, address, amount: float|Decimal|int, testnet=False):
        self.private = private_key
        self.type = type
        self.address = address
        self.amount = amount
        self.testnet = testnet

    def broadcast(self, data):
        url = f"https://api.tatum.io/v3/{BROADCAST_PATHS[self.type().lower()]}"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": os.getenv("TATUM_API_KEY")
        }
        return requests.post(url, headers=headers, json={"txData": data}).json()
    
    def _signUTXO(self):
        pass

    def _signEVM(self):
        pass
    
    def _signXRP(self):
        pass

    def _signSOL(self):
        pass

#w = WalletGen()
#
#v = w.generate_EVM()
#print(v)
#
#s = WalletScan(v["address"], "ETH", v["expiry"])
#s.scan()