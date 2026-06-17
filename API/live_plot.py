import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def get_latest_data():
    conn = sqlite3.connect("market_data.db")
    # Lấy dòng mới nhất
    df = pd.read_sql_query("SELECT * FROM order_book ORDER BY id DESC LIMIT 1", conn)
    conn.close()
    return df

def animate(i):
    df = get_latest_data()
    if df.empty: return

    # Trích xuất Bid/Ask
    bids = [(df[f'b_p{i}'].values[0], df[f'b_v{i}'].values[0]) for i in range(1, 11)]
    asks = [(df[f'a_p{i}'].values[0], df[f'a_v{i}'].values[0]) for i in range(1, 11)]
    
    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0])

    bid_prices = [b[0] for b in bids]
    bid_volumes = [b[1] for b in bids]
    ask_prices = [a[0] for a in asks]
    ask_volumes = [a[1] for a in asks]

    # Làm mới đồ thị
    plt.cla()
    plt.fill_between(bid_prices, bid_volumes, color='green', alpha=0.4, label='Mua (Bids)')
    plt.fill_between(ask_prices, ask_volumes, color='red', alpha=0.4, label='Bán (Asks)')
    plt.title(f"Real-time Order Book Depth: {df['symbol'].values[0]}")
    plt.xlabel("Giá")
    plt.ylabel("Khối lượng")
    plt.legend(loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)

# Thiết lập cửa sổ vẽ
fig = plt.figure(figsize=(10, 6))
ani = FuncAnimation(fig, animate, interval=1000) # Cập nhật mỗi 1000ms (1 giây)
plt.show()