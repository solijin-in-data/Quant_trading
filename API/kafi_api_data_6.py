import requests
import websocket
import json
import time
import threading
import sqlite3
from datetime import datetime
from collections import defaultdict

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
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, price REAL, volume INTEGER, aggressor INTEGER, total_volume INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, b_p1 REAL, b_v1 INTEGER, b_p2 REAL, b_v2 INTEGER, b_p3 REAL, b_v3 INTEGER, a_p1 REAL, a_v1 INTEGER, a_p2 REAL, a_v2 INTEGER, a_p3 REAL, a_v3 INTEGER)''')
        conn.commit()
        print("💽 Database SQLite đã khởi tạo (market_data.db)")


# ==============================================================================
# 2. TẦNG 2: MARKET STATE (Bộ Nhớ Ngắn Hạn & Dữ Liệu Thô)
# ==============================================================================
class MarketState:
    def __init__(self):
        # 1. Biến trạng thái giá & Tick Test
        self.last_price = 0.0
        self.tick_direction = 0  # 1 (Up/Buyer), -1 (Down/Seller), 0 (Flat)
        
        # 2. Theo dõi Volume/CVD theo TỪNG MỨC GIÁ
        self.price_levels = defaultdict(lambda: {"cvd": 0, "volume": 0})
        
        # 3. Theo dõi Sổ lệnh (Current vs Previous)
        self.current_book = {"bids": {}, "asks": {}}
        self.prev_book = {"bids": {}, "asks": {}}
        self.wobi = 0.0
        self.book_deltas = {"bids": {}, "asks": {}}

    def process_trade(self, price, volume):
        """Xử lý Khớp Lệnh: Tìm Aggressor bằng Tick Test"""
        if self.last_price > 0:
            if price > self.last_price:
                self.tick_direction = 1
            elif price < self.last_price:
                self.tick_direction = -1
        
        aggressor = self.tick_direction
        
        # Cập nhật Profile tại mức giá này
        level = self.price_levels[price]
        level["cvd"] += (aggressor * volume)
        level["volume"] += volume
        
        self.last_price = price
        return {"type": "TRADE", "price": price, "volume": volume, "aggressor": aggressor}

    def process_book(self, bid_prices, bid_vols, ask_prices, ask_vols):
        """Xử lý Sổ Lệnh: Tính Weighted OBI & Book Deltas"""
        self.prev_book = self.current_book.copy()
        self.current_book = {
            "bids": dict(zip(bid_prices, bid_vols)),
            "asks": dict(zip(ask_prices, ask_vols))
        }
        
        # Tính Weighted OBI
        weights = [1.0, 0.8, 0.6]
        w_bid = sum(v * w for v, w in zip(bid_vols, weights))
        w_ask = sum(v * w for v, w in zip(ask_vols, weights))
        
        total_w = w_bid + w_ask
        self.wobi = (w_bid - w_ask) / total_w if total_w > 0 else 0.0

        # Tính Book Delta
        self.book_deltas = {"bids": {}, "asks": {}}
        if self.prev_book["bids"]:  # Chỉ tính khi đã có lịch sử
            for p in self.current_book["bids"]:
                old_vol = self.prev_book["bids"].get(p, 0)
                self.book_deltas["bids"][p] = self.current_book["bids"][p] - old_vol
            for p in self.current_book["asks"]:
                old_vol = self.prev_book["asks"].get(p, 0)
                self.book_deltas["asks"][p] = self.current_book["asks"][p] - old_vol
                
        return {"type": "BOOK_UPDATE"}


# ==============================================================================
# 3. TẦNG 3: EVENT ENGINE & SIGNAL INTERPRETER
# ==============================================================================
class EventEngine:
    def __init__(self, state: MarketState):
        self.state = state

    def evaluate_trade_events(self, trade_data):
        events = []
        price = trade_data["price"]
        level_data = self.state.price_levels[price]
        
        # Công thức Absorption: Vì xét trong price_level (delta_price = 0)
        abs_cvd = abs(level_data["cvd"])
        
        # Ngưỡng hấp thụ phụ thuộc vào từng mã (vd: > 20,000 cổ phiếu)
        if abs_cvd > 20000:
            event_type = "BID_ABSORPTION" if level_data["cvd"] < 0 else "ASK_ABSORPTION"
            events.append({
                "event": event_type,
                "price": price,
                "cvd": level_data["cvd"],
                "score": abs_cvd
            })
        return events

    def evaluate_book_events(self):
        events = []
        # Quét Book Delta để tìm Wall Added / Removed
        for price, delta in self.state.book_deltas["bids"].items():
            if delta > 50000:
                events.append({"event": "WALL_CREATED", "side": "BID", "price": price, "delta": delta})
            elif delta < -50000:
                events.append({"event": "WALL_REMOVED", "side": "BID", "price": price, "delta": delta})
                
        for price, delta in self.state.book_deltas["asks"].items():
            if delta > 50000:
                events.append({"event": "WALL_CREATED", "side": "ASK", "price": price, "delta": delta})
            elif delta < -50000:
                events.append({"event": "WALL_REMOVED", "side": "ASK", "price": price, "delta": delta})
                
        return events

class SignalInterpreter:
    @staticmethod
    def interpret(events):
        alerts = []
        for e in events:
            if e["event"] == "BID_ABSORPTION":
                alerts.append(f"\033[1;95m⚠️ [PASSIVE BUYER DETECTED] Giá {e['price']:,.0f} đang hấp thụ xả! Local CVD: {e['cvd']}\033[0m")
            elif e["event"] == "ASK_ABSORPTION":
                alerts.append(f"\033[1;96m⚠️ [PASSIVE SELLER DETECTED] Giá {e['price']:,.0f} đang chặn kéo! Local CVD: {e['cvd']}\033[0m")
            elif e["event"] == "WALL_CREATED":
                alerts.append(f"\033[93m🧱 [WALL ADDED] {e['side']} kê thêm {e['delta']:,.0f} cổ tại {e['price']:,.0f}\033[0m")
            elif e["event"] == "WALL_REMOVED":
                alerts.append(f"\033[91m🚨 [WALL PULLED] {e['side']} rút {-e['delta']:,.0f} cổ tại {e['price']:,.0f} (Spoofing?)\033[0m")
        return alerts


# Khởi tạo Hệ thống
global_state = MarketState()
global_event_engine = EventEngine(global_state)
global_interpreter = SignalInterpreter()


# ==============================================================================
# 4. WEBSOCKET & DATA PROCESSING
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
        print(f"🎯 Đã khởi động HFT Engine cho {symbol}!\n{'='*65}")
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

                    # --- XỬ LÝ KHỚP LỆNH ---
                    if "Tick" in str(channel_name) and len(parts) >= 18:
                        match_price = float(parts[13])
                        match_vol = int(parts[17])
                        total_vol = int(parts[0])

                        # Core Engine Processing
                        trade_data = global_state.process_trade(match_price, match_vol)
                        events = global_event_engine.evaluate_trade_events(trade_data)
                        alerts = global_interpreter.interpret(events)
                        
                        # In Trade Info
                        aggressor = trade_data["aggressor"]
                        c = "\033[92m" if aggressor == 1 else "\033[91m" if aggressor == -1 else "\033[93m"
                        side_str = "BUY " if aggressor == 1 else "SELL" if aggressor == -1 else "FLAT"
                        print(f"{c}🔥 [TRADE] {side_str:>4} | Giá: {match_price:,.0f} | Vol: {match_vol:>5}\033[0m")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")

                        # Ghi Data vào SQLite
                        with db_lock:
                            cursor.execute("INSERT INTO trades (timestamp, symbol, price, volume, aggressor, total_volume) VALUES (?, ?, ?, ?, ?, ?)", (now, code, match_price, match_vol, aggressor, total_vol))
                            conn.commit()

                    # --- XỬ LÝ SỔ LỆNH ---
                    elif "BidAsk" in str(channel_name) and len(parts) >= 66:
                        bp = [float(parts[3]), float(parts[5]), float(parts[7])]
                        bv = [int(parts[4]), int(parts[6]), int(parts[8])]
                        ap = [float(parts[33]), float(parts[35]), float(parts[37])]
                        av = [int(parts[34]), int(parts[36]), int(parts[38])]

                        # Core Engine Processing
                        global_state.process_book(bp, bv, ap, av)
                        events = global_event_engine.evaluate_book_events()
                        alerts = global_interpreter.interpret(events)
                        
                        # In Book Info
                        print(f"📊 [BOOK] MUA 1: {bp[0]:,.0f} ({bv[0]:>5}) | BÁN 1: {ap[0]:,.0f} ({av[0]:>5}) | wOBI: {global_state.wobi:+.2f}")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")
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