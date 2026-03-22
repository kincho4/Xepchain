import sqlite3
#wallets.db
conn = sqlite3.connect("wallets.db")
cursor = conn.cursor()

for table in ["BCH", "BTC", "EVM", "LTC", "SOL"]:
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (time TEXT, address TEXT, private_key TEXT)")

conn.commit()
conn.close()

#orders.db
conn2 = sqlite3.connect("orders.db")
cursor2 = conn2.cursor()

cursor2.execute(f"CREATE TABLE IF NOT EXISTS admin (time TEXT, order_id TEXT, LTC TEXT, BTC TEXT, BCH TEXT, EVM TEXT, SOL TEXT)")
cursor2.execute(f"CREATE TABLE IF NOT EXISTS client (time TEXT, order_id TEXT, LTC TEXT, BTC TEXT, BCH TEXT, EVM TEXT, SOL TEXT)")

conn2.commit()
conn2.close()
