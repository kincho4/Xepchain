import sqlite3

conn = sqlite3.connect("wallets.db")
cursor = conn.cursor()

for table in ["BCH", "BTC", "EVM", "LTC", "SOL", "XRP"]:
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (time TEXT, address TEXT, private_key TEXT)")

conn.commit()
conn.close()