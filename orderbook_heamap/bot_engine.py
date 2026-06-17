import requests
import websocket
import json
import time
import threading
import sqlite3
from datetime import datetime

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ (Token của bạn đã được cập nhật ở đây)
# ==============================================================================
JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsIng1YyI6WyJNSUlDNmpDQ0FkS2dBd0lCQWdJR0FZOEFGNGhRTUEwR0NTcUdTSWIzRFFFQkN3VUFNRFl4TkRBeUJnTlZCQU1NSzA1eU9FSnVlSFJ5YlhrMlJGb3lWa05hTlRWcGNtUXlaRTlLZG1relFsbFJXRFpRV0doUE1VWkRSkFdG...[đoạn giữa cắt bớt cho gọn]...t-nq0JOMRg_0itGcyVNqsVg" 
SYMBOL = "CTD"

NEGOTIATE_URL = "https://wl-realtime.fiintrade.vn/RealtimeHub/negotiate?negotiateVersion=1"
WS_BASE_URL = "wss://wl-realtime.fiintrade.vn/RealtimeHub"

# Khởi tạo Database SQLite
conn = sqlite3.connect("market_data.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL")  # Bật ghi nhanh để không nghẽn dữ liệu
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, price REAL, volume INTEGER, aggressor INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, b_p1 REAL, b_v1 INTEGER, a_p1 REAL, a_v1 INTEGER)''')
conn.commit()

class State:
    def __init__(self):
        self.best_bid = 0.0
        self.best_ask = 0.0

global_state = State()

# ==============================================================================
# 2. HÀM PHỤ TRỢ SIGNALR (NEGOTIATE & SUBSCRIBE)
# ==============================================================================
def get_connection_id():
    """Gọi API đàm phán để lấy Connection ID hợp lệ từ FiinTrade"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://banggia.kafi.vn",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    try:
        response = requests.post(NEGOTIATE_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            # Trả về connectionId (hoặc connectionToken tùy phiên bản)
            return res_json.get("connectionId") or res_json.get("connectionToken")
    except Exception as e:
        print(f"❌ Lỗi đàm phán lấy Connection ID: {e}")
    return None

def subscribe_to_stock(ws, symbol):
    """Gửi lệnh đăng ký luồng dữ liệu Tick và BidAsk sau khi bắt tay thành công"""
    time.sleep(1)  # Chờ 1 giây cho kết nối ổn định
    try:
        # Đăng ký kênh Khớp lệnh (Tick)
        ws.send(json.dumps({"arguments": [f"Realtime.Tick.{symbol}"], "invocationId": "1", "target": "JoinGroup", "type": 1}) + chr(30))
        # Đăng ký kênh Sổ lệnh (BidAsk)
        ws.send(json.dumps({"arguments": [f"Realtime.BidAsk.{symbol}"], "invocationId": "2", "target": "JoinGroup", "type": 1}) + chr(30))
        print(f"🎯 Đã gửi lệnh Đăng ký theo dõi mã: {symbol}")
    except Exception as e:
        print(f"❌ Lỗi đăng ký Group: {e}")

# ==============================================================================
# 3. XỬ LÝ DỮ LIỆU WEBSOCKET REALTIME
# ==============================================================================
def on_message(ws, message):
    # Cắt thông điệp theo ký tự phân tách đặc biệt của SignalR (0x1E / chr(30))
    raw_messages = message.split(chr(30))
    
    for msg in raw_messages:
        if not msg or msg == '{"type":6}':  # Bỏ qua tin nhắn ping giữ mạng
            continue 
            
        if msg == '{}':  # Khi nhận được phản hồi trống đầu tiên -> Bắt đầu đăng ký mã
            threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL)).start()
            continue

        try:
            data = json.loads(msg)
            if data.get("type") == 1 and data.get("target") == "ReceiveMessage":
                item = data["arguments"][0]
                channel_name = item.get("chanel") or item.get("channel") or ""
                parts = item["data"][0].split("|")
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # A. XỬ LÝ LỆNH KHỚP REALTIME (TICK)
                if "Tick" in str(channel_name) and len(parts) >= 18:
                    price, vol = float(parts[13]), int(parts[17])
                    
                    # Thuật toán tính toán Aggressor (Lee-Ready)
                    if price >= global_state.best_ask and global_state.best_ask > 0:
                        aggressor = 1   # Chủ động Mua
                    elif price <= global_state.best_bid and global_state.best_bid > 0:
                        aggressor = -1  # Chủ động Bán
                    else:
                        aggressor = 0   # Không rõ xu hướng
                        
                    cursor.execute("INSERT INTO trades (timestamp, price, volume, aggressor) VALUES (?, ?, ?, ?)", (now, price, vol, aggressor))
                    conn.commit()
                    print(f"🔥 [TICK] Giá: {price:,.0f} | Vol: {vol} | Side: {aggressor}")
                
                # B. XỬ LÝ SỔ LỆNH REALTIME (BIDASK)
                elif "BidAsk" in str(channel_name) and len(parts) >= 35:
                    global_state.best_bid = float(parts[3])
                    global_state.best_ask = float(parts[33])
                    
                    cursor.execute("INSERT INTO order_book (timestamp, b_p1, b_v1, a_p1, a_v1) VALUES (?, ?, ?, ?, ?)", 
                                   (now, global_state.best_bid, int(parts[4]), global_state.best_ask, int(parts[34])))
                    conn.commit()
                    print(f"📊 [BOOK] Thăng cấp Best Bid: {global_state.best_bid:,.0f} | Best Ask: {global_state.best_ask:,.0f}")
                    
        except Exception as e:
            pass

def on_open(ws):
    print("🔌 Kết nối thành công cơ sở mạng! Đang thực hiện Handshake...")
    # Bước bắt tay bắt buộc của SignalR để chọn Protocol định dạng JSON
    ws.send('{"protocol":"json","version":1}' + chr(30))

if __name__ == "__main__":
    print("🚀 Đang khởi động Engine dữ liệu...")
    connection_id = get_connection_id()
    
    if connection_id:
        print(f"🔑 Lấy ID thành công: {connection_id[:10]}...")
        # Tạo link chuẩn hóa chứa ID hợp lệ
        full_ws_url = f"{WS_BASE_URL}?id={connection_id}"
        
        ws = websocket.WebSocketApp(
            full_ws_url,
            header=[f"Authorization: Bearer {JWT_TOKEN}"],
            on_open=on_open,
            on_message=on_message
        )
        ws.run_forever(ping_interval=15, ping_timeout=10)
    else:
        print("❌ Thất bại! Token hết hạn hoặc URL đàm phán (Negotiate) lỗi.")