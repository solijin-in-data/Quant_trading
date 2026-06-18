import requests
import websocket
import json
import time
import threading
import sqlite3
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# ==============================================================================
# 1. CONFIGURATION & DATABASE INITIALIZATION
# ==============================================================================

load_dotenv()  # Load environment variables from .env file

JWT_TOKEN = os.getenv("KAFI_JWT_TOKEN")  # Ensure you set this in your .env file
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
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, price REAL, volume INTEGER, price_change INTEGER, total_volume INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp DATETIME, symbol TEXT, 
            b_p1 REAL, b_v1 INTEGER, b_p2 REAL, b_v2 INTEGER, b_p3 REAL, b_v3 INTEGER, b_p4 REAL, b_v4 INTEGER, b_p5 REAL, b_v5 INTEGER,
            b_p6 REAL, b_v6 INTEGER, b_p7 REAL, b_v7 INTEGER, b_p8 REAL, b_v8 INTEGER, b_p9 REAL, b_v9 INTEGER, b_p10 REAL, b_v10 INTEGER,
            a_p1 REAL, a_v1 INTEGER, a_p2 REAL, a_v2 INTEGER, a_p3 REAL, a_v3 INTEGER, a_p4 REAL, a_v4 INTEGER, a_p5 REAL, a_v5 INTEGER,
            a_p6 REAL, a_v6 INTEGER, a_p7 REAL, a_v7 INTEGER, a_p8 REAL, a_v8 INTEGER, a_p9 REAL, a_v9 INTEGER, a_p10 REAL, a_v10 INTEGER
        )''')
        conn.commit()
        print("[INFO] SQLite Database initialized: Ready to record 10-level L2 Book.")

# ==============================================================================
# 2. LAYER 2: MARKET STATE & GARBAGE COLLECTION
# ==============================================================================

# ==============================================================================
# 2. LAYER 2: MARKET STATE & GARBAGE COLLECTION
# ==============================================================================
class MarketState:
    def __init__(self):
        self.last_price = 0.0
        self.best_bid = 0.0
        self.best_ask = 0.0
        
        # TẦNG 1: MEMORY - Lưu trữ Profile/Volume Surface cả ngày
        self.price_memory = defaultdict(lambda: {"total_vol": 0, "total_cvd": 0})
        
        # TẦNG 2: ACTIVE SESSIONS - Quản lý trận chiến (Hấp thụ) hiện tại
        self.active_sessions = {}
        
        # Các thông số thiết lập bộ lọc (Tùy chỉnh cho CTD)
        self.ACTIVE_ZONE = 5        # Vùng sống sót: 5 bước giá
        self.VOLUME_THRESHOLD = 1000 # Bỏ qua các lệnh đấm < 1000 cổ để tránh nhiễu
        
        self.current_book = {"bids": {}, "asks": {}}
        self.prev_book = {"bids": {}, "asks": {}}
        self.wobi = 0.0
        self.book_deltas = {"bids": {}, "asks": {}}
        
        self.traded_vol_at_bid = defaultdict(int)
        self.traded_vol_at_ask = defaultdict(int)
        self.active_walls = {}

    def process_trade(self, price, volume):
        # 1. Tính toán phe chủ động
        aggressor = 0
        if self.best_ask > 0 and self.best_bid > 0:
            if price >= self.best_ask:
                aggressor = 1   
                self.traded_vol_at_ask[price] += volume
            elif price <= self.best_bid:
                aggressor = -1  
                self.traded_vol_at_bid[price] += volume
            else:
                aggressor = 1 if price > self.last_price else (-1 if price < self.last_price else 0)
        else:
            aggressor = 1 if price > self.last_price else (-1 if price < self.last_price else 0)

        # 2. LƯU TẦNG 1 (Luôn cộng dồn để vẽ Volume Profile)
        self.price_memory[price]["total_vol"] += volume
        self.price_memory[price]["total_cvd"] += (aggressor * volume)

        # 3. QUẢN LÝ TẦNG 2 (Khởi tạo/Cập nhật Session Hấp Thụ)
        if price not in self.active_sessions:
            self.active_sessions[price] = {
                "start_time": time.time(),
                "cvd": 0,
                "absorbed_volume": 0,
                "ticks_survived": 0,
                "status": "ACTIVE"
            }
            
        session = self.active_sessions[price]
        session["cvd"] += (aggressor * volume)
        session["absorbed_volume"] += volume
        
        # CHỈ tính là 1 nhịp tấn công thực sự nếu volume đủ lớn (Institutional Flow)
        if volume >= self.VOLUME_THRESHOLD:
            session["ticks_survived"] += 1

# ==============================================================================
# 3. LAYER 3: EVENT ENGINE & SIGNAL INTERPRETER
# ==============================================================================
class EventEngine:
    def __init__(self, state: MarketState):
        self.state = state

    def evaluate_trade_events(self, trade_data):
        events = []
        price = trade_data["price"]
        level = self.state.price_levels[price]
        
        if abs(level["cvd"]) > 20000 and level["ticks_survived"] >= 5:
            event_type = "BID_ABSORPTION" if level["cvd"] < 0 else "ASK_ABSORPTION"
            events.append({
                "event": event_type,
                "price": price,
                "cvd": level["cvd"],
                "ticks": level["ticks_survived"]
            })
        return events

    def evaluate_book_events(self):
        events = []
        now = time.time()
        
        # Process Bids
        for p, actual_vol in self.state.current_book["bids"].items():
            old_vol = self.state.prev_book["bids"].get(p, 0)
            matched_vol = self.state.traded_vol_at_bid.get(p, 0)
            
            expected_vol = old_vol - matched_vol
            replenished_amount = actual_vol - expected_vol
            
            if matched_vol > 0 and replenished_amount > 5000:
                events.append({
                    "event": "REPLENISHMENT", "side": "BID", "price": p,
                    "amount": replenished_amount, "matched": matched_vol
                })
            
            # RACE CONDITION FIX: Delete matched volume to prevent double-counting
            if p in self.state.traded_vol_at_bid:
                del self.state.traded_vol_at_bid[p]

            if actual_vol > 50000:
                if p not in self.state.active_walls:
                    self.state.active_walls[p] = {"side": "BID", "birth_time": now}
                    events.append({"event": "WALL_CREATED", "price": p, "side": "BID", "delta": actual_vol - old_vol})
                else:
                    wall_age = now - self.state.active_walls[p]["birth_time"]
                    if wall_age > 30 and wall_age < 35: 
                        events.append({"event": "PERSISTENT_WALL", "price": p, "age": wall_age})
            else:
                if p in self.state.active_walls:
                    del self.state.active_walls[p]
                    events.append({"event": "WALL_REMOVED", "price": p, "side": "BID", "delta": actual_vol - old_vol})

        # Process Asks
        for p, actual_vol in self.state.current_book["asks"].items():
            old_vol = self.state.prev_book["asks"].get(p, 0)
            matched_vol = self.state.traded_vol_at_ask.get(p, 0)
            
            expected_vol = old_vol - matched_vol
            replenished_amount = actual_vol - expected_vol
            
            if matched_vol > 0 and replenished_amount > 5000:
                events.append({
                    "event": "REPLENISHMENT", "side": "ASK", "price": p,
                    "amount": replenished_amount, "matched": matched_vol
                })
                
            # RACE CONDITION FIX: Delete matched volume to prevent double-counting
            if p in self.state.traded_vol_at_ask:
                del self.state.traded_vol_at_ask[p]

            if actual_vol > 50000:
                if p not in self.state.active_walls:
                    self.state.active_walls[p] = {"side": "ASK", "birth_time": now}
                    events.append({"event": "WALL_CREATED", "price": p, "side": "ASK", "delta": actual_vol - old_vol})
            else:
                if p in self.state.active_walls:
                    del self.state.active_walls[p]
                    events.append({"event": "WALL_REMOVED", "price": p, "side": "ASK", "delta": actual_vol - old_vol})
        
        return events

class SignalInterpreter:
    @staticmethod
    def interpret(events):
        alerts = []
        for e in events:
            if e["event"] == "REPLENISHMENT":
                alerts.append(f"\033[92m [HIDDEN LIQUIDITY] {e['side']} at {e['price']:,.0f}: Absorbed {e['matched']} but replenished {e['amount']} shares!\033[0m")
            elif e["event"] == "BID_ABSORPTION":
                alerts.append(f"\033[1;95m [PASSIVE BUYER] Level {e['price']:,.0f} absorbed {e['ticks']} aggressive hits! (CVD: {e['cvd']})\033[0m")
            elif e["event"] == "ASK_ABSORPTION":
                alerts.append(f"\033[1;96m [PASSIVE SELLER] Level {e['price']:,.0f} blocked {e['ticks']} upward thrusts! (CVD: {e['cvd']})\033[0m")
            elif e["event"] == "PERSISTENT_WALL":
                alerts.append(f"\033[93m [SOLID WALL] Wall at {e['price']:,.0f} held for {e['age']:.1f}s. High defense intent!\033[0m")
            elif e["event"] == "WALL_CREATED":
                alerts.append(f"\033[93m [WALL ADDED] {e['side']} stacked {e.get('delta', 0):,.0f} shares at {e['price']:,.0f}\033[0m")
            elif e["event"] == "WALL_REMOVED":
                alerts.append(f"\033[91m [WALL PULLED] {e['side']} wall at {e['price']:,.0f} removed! (Potential Spoofing)\033[0m")
        return alerts

global_state = MarketState()
global_event_engine = EventEngine(global_state)
global_interpreter = SignalInterpreter()

# ==============================================================================
# 4. WEBSOCKET & DATA PROCESSING ENGINE
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
        print(f"[INFO] HFT Engine fully armed for {symbol}!\n{'='*65}")
    except Exception: pass

def on_message(ws, message):
    try:
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': continue 
            if msg == '{}':
                threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL_TO_WATCH), daemon=True).start()
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

                    # --- TICK PROCESSING (MATCHED TRADES) ---
                    if "Tick" in str(channel_name) and len(parts) >= 18:
                        match_price = float(parts[13])
                        match_vol = int(parts[17])
                        total_vol = int(parts[0])

                        trade_data = global_state.process_trade(match_price, match_vol)
                        events = global_event_engine.evaluate_trade_events(trade_data)
                        alerts = global_interpreter.interpret(events)
                        
                        aggressor = trade_data["aggressor"]
                        c = "\033[92m" if aggressor == 1 else "\033[91m" if aggressor == -1 else "\033[93m"
                        side_str = "BUY " if aggressor == 1 else "SELL" if aggressor == -1 else "FLAT"
                        print(f"{c}[TRADE] {side_str:>4} | Price: {match_price:,.0f} | Vol: {match_vol:>5}\033[0m")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")

                        with db_lock:
                            cursor.execute("INSERT INTO trades (timestamp, symbol, price, volume, price_change, total_volume) VALUES (?, ?, ?, ?, ?, ?)", (now, code, match_price, match_vol, aggressor, total_vol))
                            conn.commit()

                    # --- LEVEL 2 BOOK PROCESSING (10 LEVELS) ---
                    elif "BidAsk" in str(channel_name) and len(parts) >= 60:
                        bp = [float(parts[i]) for i in range(3, 23, 2)]
                        bv = [int(parts[i]) for i in range(4, 24, 2)]
                        ap = [float(parts[i]) for i in range(33, 53, 2)]
                        av = [int(parts[i]) for i in range(34, 54, 2)]

                        # Push top 3 levels to core analysis
                        global_state.process_book(bp[:3], bv[:3], ap[:3], av[:3])
                        events = global_event_engine.evaluate_book_events()
                        alerts = global_interpreter.interpret(events)
                        
                        print(f"[BOOK] BID 1: {bp[0]:,.0f} ({bv[0]:>5}) | ASK 1: {ap[0]:,.0f} ({av[0]:>5}) | wOBI: {global_state.wobi:+.2f}")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")
                        print("-" * 65)

                        # Write all 10 levels to SQLite
                        with db_lock:
                            params = [now, code]
                            for i in range(10): params.extend([bp[i], bv[i]])
                            for i in range(10): params.extend([ap[i], av[i]])
                            
                            placeholders = ', '.join(['?'] * 42)
                            cursor.execute(f"""
                                INSERT INTO order_book (
                                    timestamp, symbol, 
                                    b_p1, b_v1, b_p2, b_v2, b_p3, b_v3, b_p4, b_v4, b_p5, b_v5, b_p6, b_v6, b_p7, b_v7, b_p8, b_v8, b_p9, b_v9, b_p10, b_v10,
                                    a_p1, a_v1, a_p2, a_v2, a_p3, a_v3, a_p4, a_v4, a_p5, a_v5, a_p6, a_v6, a_p7, a_v7, a_p8, a_v8, a_p9, a_v9, a_p10, a_v10
                                ) VALUES ({placeholders})
                            """, tuple(params))
                            conn.commit()
    except Exception: pass

def on_error(ws, error): print(f"[ERROR] Connection error: {error}")
def on_close(ws, code, msg): print(f"[WARNING] Connection closed. Code: {code}")
def on_open(ws): ws.send('{"protocol":"json","version":1}' + chr(30))

# ==============================================================================
# 5. AUTO-RECONNECT ENGINE
# ==============================================================================
def start_trading_bot():
    init_db()
    while True:
        fresh_id = get_fresh_connection_id()
        if fresh_id:
            final_ws_url = f"{WS_BASE_URL}?id={fresh_id}"
            print(f"[INFO] Connecting to socket gateway...")
            websocket.enableTrace(False)
            ws = websocket.WebSocketApp(
                final_ws_url, 
                header=custom_headers, 
                on_open=on_open, 
                on_message=on_message, 
                on_error=on_error, 
                on_close=on_close
            )
            # 15-second ping keeps the socket alive
            ws.run_forever(ping_interval=15, ping_timeout=10)
        
        print("[WARNING] Link severed. Auto-recovering in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    start_trading_bot()