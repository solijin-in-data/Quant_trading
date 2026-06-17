import sqlite3
import pandas as pd

conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(trades)")
columns = [info[1] for info in cursor.fetchall()]
print(f"Các cột hiện có trong bảng trades: {columns}")
conn.close()