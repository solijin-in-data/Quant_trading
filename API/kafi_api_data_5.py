import requests
import websocket
import json
import time
import threading
import sqlite3
from datetime import datetime

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ VÀ DATABASE
# ==============================================================================

JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJ4NWMiOlsiTUlJQzZqQ0NBZEtnQXdJQkFnSUdBWThBRjRoUU1BMEdDU3FHU0liM0RRRUJDd1VBTURZeE5EQXlCZ05WQkFNTUswNXlPRUp1ZUhSeWJYazJSRm95VmtOYU5UVnBjbVF5WkU5S2Rta3pRbGxSV0RaUVdHaFBNVVpEUmtFd0hoY05NalF3TkRJeE1EazFPREV6V2hjTk1qVXdNakUxTURrMU9ERXpXakEyTVRRd01nWURWUVFEREN0T2NqaENibmgwY20xNU5rUmFNbFpEV2pVMWFYSmtNbVJQU25acE0wSlpVVmcyVUZob1R6RkdRMFpCTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFxNnRFVE9pRE1Cd3VTTFA3QlB6M1ZyL2VBVm96SDVSbXNhRUtMRW9tVXpPRDBKS3lVV2xPRTlBRnAxczhyUlAvTmFpRzVHYStGcGdvWkY1d3FzeXc1a21iYlJKa1MzenFPWk5mSmdad1dXbzRneExhdzE1UXJGVDJ5ZDZZREx2SzJ5WGo0VGNUSXVtQ09pUEFOMFpBWk4xNDBYMjMzWDRyM082MW1aeVVEMW0xR1FDQnU5b3drY2ZiOW9RMVpqZitYeE5tS3B4ZVBES2xrRFJDM0ZSUkdMWmV6RXM3SHBYdllJcExBS0Z5YW4xREtlc2JwY2lFeUhGci9hdkJqKzJBNGRwVFFqZ3BmcjRZc2cwYkE5dkhwT2E5V0FKWisvSTJFVGdqYmF0eHR0bFZISUZZWDZPYW5FemMvY3FIQVhFSFlNQ0pxNEViQTVjWHk3UDllUGVrK3dJREFRQUJNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUF2SXRic0RtTUhWckRKVFl6OEdwQk0vbno5bklZUE5UYW5MNjdISjU5R1NMVzF2VkhmTHdLTWp1Ylh0VzdMQktZaVlGSHpNK1RHamd2aW1mVFdzU3phSXRJRTNjVHl5VXRHMy9Pc2J0T1M0Vm1reGsyMzJWajBZbGFDeVVyeTJQU3B1UWVBMi93eGc5Nyt2UTVOQUVYbmpoSDZSM1FsT2JNZXc1SXdOZGpsekZlMjJmNUdKaHNxUi94RVNmSVE4MURvaEZmT2JhRmswZ3ZHQ2ZaeEEva0xySUF1MHc3VVpZTGdWTzgvUDlLR0NHWDc4RTZGZm96REZlbDFLU205eC9IQThnTm0xS0NQSlhGaE1oZGJoWE5SZWhUQW5jektudlpqcC9lS2UvQkNUaFdSWHl0ZUpicVI1WHZjRzk4eEZDYTZyYjFxVEUxb21FbkZJMVR4SU1HZyJdLCJhbGciOiJSUzI1NiJ9.eyJkZXZpY2VJbmZvIjp7ImRldmljZUlkIjoiMmU1NmI3MDItNTQ3ZC00NTYwLWFmNzAtNTQzMWRlODNiMGMyIiwiZGV2aWNlTmFtZSI6InVua25vd24iLCJkZXZpY2VNb2RlbCI6InVua25vd24iLCJkZXZpY2VPc1ZlcnNpb24iOiJ1bmtub3duIiwiZGV2aWNlT3MiOiJ1bmtub3duIn0sImV4cCI6MTc4MTUyNDU4NywiaXNzIjoicmhqQVR2UDZyMmdGOVU2Nmk3dmc5Q2V5Y3FzaU16anQiLCJsb2dpblVVSUQiOiJUT0tFTl9MT0dJTl80Mzc2MV8yMDI2MDYxNTEwNTYyN18yMDI2MDYxNTE4NTYyN185ZDY2OGY1My1lNGYwLTRmOGEtOWEyZS1kM2EwYzViM2Q2YWEiLCJpYXQiOjE3ODE0OTU3ODcsImNsaWVudElkIjoiNTY5NzYiLCJjaWQiOiJkMTU2ZWNhNS1jNTNkLTQ3M2ItOTBjZC00M2NlMWVlNmNmZmYiLCJpc3Jlc2V0IjoiTiIsInNnSWRzIjpbMSwzLDEyLDgsMTQsOSwxMSw1LDM1LDI4LDMwLDUyLDU1LDgwLDgzLDg0LDEwNiwxMDksMTE5XSwidWQiOnsiZXgiOnsiY29yZVVzZXJJZCI6IjAwMDEwMTg5MjEiLCJsZXZlbCI6IkNVU1RPTUVSIiwic3ViTnVtYmVycyI6W3siYWNjb3VudHR5cGVuYW1lIjoiQ0FTSCAtIE4xIDAuMTUlIDEyJSIsImlzb3duZXIiOiJZIiwidmFsZGF0ZSI6IjA3LzEwLzIwMjQiLCJzdWJUeXBlIjoiRVFVSVRZIiwic2hvcnRhY2N0bm8iOiIwMSIsIm1ydHlwZSI6Ik4iLCJhdXRvYWR2IjoiWSIsImFjY291bnR0eXBlYnJpZWZuYW1lIjoiRmVlIDAuMTUlIE1hcmdpbiAxMiUiLCJhY2NvdW50dHlwZSI6IjAwMTEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidmFhY2N0bm9saXN0IjoiS0FGNjQ5MjgyMSIsImF1dGh0eXBlIjoiMSIsImF1dGhjb2RlIjoiQURXSU5QVVQvQ0FTSFRSQU5TL0NBU0hUUkFOU0VORERBVEUvQ09ORF9PUkRFUi9DT05GSVJNT1JERVIvREVQT1NJVC9FWFRFTkQvR1JPVVBfT1JERVIvSVNTVUVJTlBVVC9PUkRJTlBVVC9SRVNFVFBBU1MvU1RPQ0tUUkFOUy9UQUtFSU4iLCJtb2JpbGVzbXMiOiIwOTQ4NjQ5MjgyIiwiYWNjb3VudG5vIjoiMDAwMTAyMzU1NyIsIm9wZW5kYXRlIjoiMjAyNC0xMC0wN1QwMDowMDowMFoiLCJ2aWEiOiJBIiwic3ViTnVtYmVyIjoiMDAwMTAyMzU1NyIsImFjY291bnRuYW1lIjoiTmd1eeG7hW4gQW5oIFF1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MH0seyJhY2NvdW50dHlwZW5hbWUiOiJNQVJHSU4gLSBOMSAwLjE1JSAxMiUiLCJpc293bmVyIjoiWSIsInZhbGRhdGUiOiIwNy8xMC8yMDI0Iiwic3ViVHlwZSI6IkVRVUlUWSIsInNob3J0YWNjdG5vIjoiMDYiLCJtcnR5cGUiOiJUIiwiYXV0b2FkdiI6IlkiLCJhY2NvdW50dHlwZWJyaWVmbmFtZSI6IkZlZSAwLjE1JSBNYXJnaW4gMTIlIiwiYWNvdW50dHlwZSI6IjAwMTIiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6ZmFsc2UsInZhYWNjdG5vbGlzdCI6IktBRjY0OTI4MjYiLCJhdXRodHlwZSI6IjEiLCJhdXRoY29kZSI6IkFEV0lOUFVUL0NBU0hUUkFOUy9DQVNIVFJBTlNFTkREQVRFL0NPTkRfT1JERVIvQ09ORklSTU9SREVSL0RFUE9TSVQvRVhURU5EL0dST1VQX09SREVSL0lTU1VCSU5QVVQvT1JESU5QVVQvUkVTRVRQQVNTL1NUT0NLVFJBTlMvVEFLRUlOIiwibW9iaWxlc21zIjoiMDk0ODY0OTI4MiIsImFjY291bnRubyI6IjAwMDEwMjM1NTgiLCJvcGVuZGF0ZSI6IjIwMjQtMTAtMDdUMDA6MDA6MDBaIiwidmlhIjoiQSIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTgiLCJhY2NvdW50bmFtZSI6Ik5ndXnhu4VuIEFuaBR1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MTAwMDAwMDAwMH0seyJyZWFjdG5vIjoiMDAwMTAwMDAwMTAwMDEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidDBpbWxpbWl0IjoiMCIsInZhYWNjdG5vIjoiS0FGNjQ5MjgyOCIsInN1YlR5cGUiOiJERVJJVkFUSVZFUyIsInN0YXR1cyI6IkEiLCJkdGFTdGF0dXMiOiJBIiwiZG1BY2N0bm8iOiIwNDlDNjQ5MjgyIiwiYWZ0eXBlIjoiMDAwMyIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTciLCJjZENvbnRlbnQiOiIwMDAxMDIzNTU3IiwiY2Z0eXBlIjoiMDAwMSIsImF2bGNhc2hvbmhhbmQiOiIwIn1dfSwiaSI6NDM3NjEsInUiOiIwNDlDNjQ5MjgyIiwicklkcyI6WzFdfSwia2NVc2VySWQiOiIyMzEyNDkyZi05YWJlLTQ3M2YtYTZhMy1mZTc4ZWMwNWZmMzUiLCJmbGV4QWNjb3VudE51bWJlciI6IjA0OUM2NDkyODIiLCJjdXN0b21Vc2VybmFtZSI6IjA0OWM2NDkyODIifQ.baf5Zww3juu9xcMW_w3QODnYUn5mBJZOFU9aUUdKO2Q1gFtWtUTdSzOd0Pb0V95xWaDWtAZo6z6rViNvLPaeut1x8XF7twjE3l3KaCbJh5MNf4J5yGkSyHV55hrFPXZjJ5ppZqLXZZZYMqBLUVv8eLi_gAjFUwmWuy3ALfAWVNLBBRkFRmcYhfxt92KcE2WHttsOFInJ0JRSQTXhejXQQE5-y40TQUf22XWOHezx1hnw5jYqBq6GQTRwlO_rPtANaVlYL3VkDOTY_VH7WJwMws_t4HSNvgzutClGQ-Db3s4757OiN4Y-4qIHsoOWyrHfGx7qIL9UCpPP1lwidRQpng"
SYMBOL_TO_WATCH = "CTD"

NEGOTIATE_URL = "https://wl-realtime.fiintrade.vn/RealtimeHub/negotiate?negotiateVersion=1"
WS_BASE_URL = "wss://wl-realtime.fiintrade.vn/RealtimeHub"
custom_headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin: https://banggia.kafi.vn",
    f"Authorization: Bearer {JWT_TOKEN}"
]

db_lock = threading.Lock()
conn = sqlite3.connect("market_data.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    with db_lock:
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, price REAL, volume INTEGER, price_change REAL, total_volume INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, b_p1 REAL, b_v1 INTEGER, b_p2 REAL, b_v2 INTEGER, b_p3 REAL, b_v3 INTEGER, a_p1 REAL, a_v1 INTEGER, a_p2 REAL, a_v2 INTEGER, a_p3 REAL, a_v3 INTEGER)''')
        conn.commit()
        print("💽 Database SQLite đã khởi tạo (market_data.db)")

# ==============================================================================
# 2. STATE ENGINE & SIGNAL ENGINE (CORE QUANT LOGIC)
# ==============================================================================

class MarketState:
    def __init__(self):
        self.price = 0.0
        self.cvd = 0  # Global Cumulative Volume Delta
        
        # --- ABSORPTION TRACKING ---
        self.local_price = 0.0
        self.local_cvd = 0     # CVD tích lũy tại mức giá hiện tại
        self.local_volume = 0  # Tổng volume khớp tại mức giá hiện tại
        
        self.bid_volume = 0
        self.ask_volume = 0
        self.obi = 0.0

    def process_trade(self, price, volume, change):
        # 1. Tính toán hướng mua/bán (Aggressor)
        direction = 1 if change > 0 else (-1 if change < 0 else 0)
        self.cvd += direction * volume

        # 2. Xử lý Logic Absorption (Local Tracker)
        if price == self.local_price:
            self.local_cvd += direction * volume
            self.local_volume += volume
        else:
            # Nếu giá thay đổi (level bị phá vỡ), reset lại Tracker cho mức giá mới
            self.local_price = price
            self.local_cvd = direction * volume
            self.local_volume = volume
            
        self.price = price

    def process_book(self, bid_prices, bid_vols, ask_prices, ask_vols):
        self.bid_volume = sum(bid_vols)
        self.ask_volume = sum(ask_vols)
        
        total_depth = self.bid_volume + self.ask_volume
        if total_depth > 0:
            self.obi = (self.bid_volume - self.ask_volume) / total_depth

class SignalEngine:
    def __init__(self, state: MarketState):
        self.state = state

    def check_signals(self):
        signals = []
        
        # 1. Tín hiệu OBI
        if self.state.obi > 0.6:
            signals.append("\033[92m🟢 [OBI] PHE MUA ĐANG ĐÈ LỆNH ÁP ĐẢO!\033[0m")
        elif self.state.obi < -0.6:
            signals.append("\033[91m🔴 [OBI] PHE BÁN ĐANG CHẶN DÀY ĐẶC!\033[0m")

        # 2. Tín hiệu Wall (Tường chặn)
        if self.state.bid_volume > 50000:
            signals.append("\033[93m🧱 [BUY WALL] TƯỜNG MUA XUẤT HIỆN DƯỚI GIÁ!\033[0m")

        # 3. ABSORPTION SIGNAL: Hấp thụ lực Bán (Hidden Buyer)
        # Giả định ngưỡng kích hoạt: CVD âm > 5000 cổ phiếu tại MỘT mức giá (tùy biến theo mã)
        cvd_threshold = -5000 
        
        if self.state.local_cvd <= cvd_threshold:
            # Tính Absorption Score (Thang điểm 10 dựa trên độ lớn của khối lượng hấp thụ)
            # Ví dụ: Cứ 1000 cổ bán ra được hấp thụ = 1 điểm. Max = 10.
            score = min(10.0, abs(self.state.local_cvd) / 1000.0)
            
            absorption_alert = f"""
\033[1;95m⚠️ EVENT DETECTED: Heavy Selling Absorption\033[0m
\033[95m  ├─ CVD Change:       {self.state.local_cvd}\033[0m
\033[95m  ├─ Price Change:     0 (Giá giữ vững tại {self.state.local_price:,.0f})\033[0m
\033[95m  ├─ Absorption Score: {score:.1f} / 10\033[0m
\033[95m  └─ Conclusion:       Potential Passive Buyer Detected\033[0m"""
            signals.append(absorption_alert)

        return signals

# Khởi tạo Engine
global_state = MarketState()
global_engine = SignalEngine(global_state)

# ==============================================================================
# 3. WEBSOCKET & DATA PROCESSING
# ==============================================================================

def get_fresh_connection_id():
    try:
        response = requests.post(NEGOTIATE_URL, headers={"Authorization": f"Bearer {JWT_TOKEN}"}, timeout=10)
        if response.status_code == 200:
            return response.json().get("connectionId") or response.json().get("connectionToken")
    except Exception: pass
    return None

def subscribe_to_stock(ws, symbol):
    time.sleep(1)
    try:
        ws.send(json.dumps({"arguments": [f"Realtime.Tick.{symbol}"], "invocationId": "1", "target": "JoinGroup", "type": 1}) + chr(30))
        ws.send(json.dumps({"arguments": [f"Realtime.BidAsk.{symbol}"], "invocationId": "2", "target": "JoinGroup", "type": 1}) + chr(30))
        print(f"🎯 Đã kết nối Engine & Database cho {symbol}!\n{'='*65}")
    except Exception: pass

def on_message(ws, message):
    try:
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': continue 
            if msg == '{}':
                threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL_TO_WATCH)).start()
                continue

            data = json.loads(msg)
            if data.get("type") == 1 and data.get("target") == "ReceiveMessage":
                args = data.get("arguments", [])
                if args and isinstance(args, list):
                    item = args[0]
                    channel_name = item.get("chanel") or item.get("channel") or ""
                    code = item.get("code", "").strip()
                    raw_data_list = item.get("data", [])
                    
                    if not raw_data_list or code != SYMBOL_TO_WATCH: continue
                    parts = raw_data_list[0].split("|")
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # --- LƯU TRỮ VÀ XỬ LÝ KHỚP LỆNH ---
                    if "Tick" in str(channel_name) and len(parts) >= 18:
                        match_price = float(parts[13])
                        change = float(parts[15])
                        match_vol = int(parts[17])
                        total_vol = int(parts[0])

                        # Cập nhật State Engine
                        global_state.process_trade(match_price, match_vol, change)
                        
                        # In ra màn hình
                        c = "\033[92m" if change > 0 else "\033[91m" if change < 0 else "\033[93m"
                        print(f"{c}🔥 [TRADE] Giá: {match_price:,.0f} | Vol: {match_vol:>5} | CVD: {global_state.cvd:>6}\033[0m")
                        
                        # Ghi Data vào SQLite
                        with db_lock:
                            cursor.execute("INSERT INTO trades (timestamp, symbol, price, volume, price_change, total_volume) VALUES (?, ?, ?, ?, ?, ?)", (now, code, match_price, match_vol, change, total_vol))
                            conn.commit()

                    # --- LƯU TRỮ VÀ XỬ LÝ SỔ LỆNH ---
                    elif "BidAsk" in str(channel_name) and len(parts) >= 66:
                        bp = [float(parts[3]), float(parts[5]), float(parts[7])]
                        bv = [int(parts[4]), int(parts[6]), int(parts[8])]
                        ap = [float(parts[33]), float(parts[35]), float(parts[37])]
                        av = [int(parts[34]), int(parts[36]), int(parts[38])]

                        # Cập nhật State Engine
                        global_state.process_book(bp, bv, ap, av)
                        
                        # Quét Signal Engine từ State mới nhất
                        signals = global_engine.check_signals()
                        
                        # In Sổ Lệnh & Tín hiệu
                        print(f"📊 [BOOK] MUA 1: {bp[0]:,.0f} ({bv[0]:>5}) | BÁN 1: {ap[0]:,.0f} ({av[0]:>5}) | OBI: {global_state.obi:+.2f}")
                        for sig in signals:
                            print(f"\033[96m   ➤ SIGNAL TRUTH: {sig}\033[0m")
                        print("-" * 65)

                        # Ghi Data vào SQLite
                        with db_lock:
                            cursor.execute("INSERT INTO order_book (timestamp, symbol, b_p1, b_v1, b_p2, b_v2, b_p3, b_v3, a_p1, a_v1, a_p2, a_v2, a_p3, a_v3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (now, code, bp[0], bv[0], bp[1], bv[1], bp[2], bv[2], ap[0], av[0], ap[1], av[1], ap[2], av[2]))
                            conn.commit()
    except Exception: pass

def on_error(ws, error): pass
def on_close(ws, code, msg): pass
def on_open(ws): ws.send('{"protocol":"json","version":1}' + chr(30))

if __name__ == "__main__":
    init_db()
    fresh_id = get_fresh_connection_id()
    if fresh_id:
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(f"{WS_BASE_URL}?id={fresh_id}", header=custom_headers, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever(ping_interval=15, ping_timeout=10)