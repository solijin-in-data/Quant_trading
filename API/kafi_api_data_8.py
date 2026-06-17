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

JWT_TOKEN = ""
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
        # CẬP NHẬT: Thay đổi 'aggressor' thành 'price_change' để đồng bộ với DB cũ
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, price REAL, volume INTEGER, price_change INTEGER, total_volume INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, b_p1 REAL, b_v1 INTEGER, b_p2 REAL, b_v2 INTEGER, b_p3 REAL, b_v3 INTEGER, a_p1 REAL, a_v1 INTEGER, a_p2 REAL, a_v2 INTEGER, a_p3 REAL, a_v3 INTEGER)''')
        conn.commit()
        print("💽 Database SQLite đã khởi tạo và đồng bộ cột (market_data.db)")


# ==============================================================================
# 2. TẦNG 2: MARKET STATE (Bộ Nhớ Ngắn Hạn & Dữ Liệu Thô)
# ==============================================================================
class MarketState:
    def __init__(self):
        self.last_price = 0.0
        self.best_bid = 0.0
        self.best_ask = 0.0
        
        self.price_levels = defaultdict(lambda: {
            "cvd": 0, 
            "volume": 0, 
            "ticks_survived": 0
        })
        
        self.current_book = {"bids": {}, "asks": {}}
        self.prev_book = {"bids": {}, "asks": {}}
        self.wobi = 0.0
        self.book_deltas = {"bids": {}, "asks": {}}
        
        self.traded_vol_at_bid = defaultdict(int)
        self.traded_vol_at_ask = defaultdict(int)
        self.active_walls = {}

    def process_trade(self, price, volume):
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

        level = self.price_levels[price]
        level["cvd"] += (aggressor * volume)
        level["volume"] += volume
        level["ticks_survived"] += 1

        self.last_price = price
        return {"type": "TRADE", "price": price, "volume": volume, "aggressor": aggressor}

    def process_book(self, bid_prices, bid_vols, ask_prices, ask_vols):
        if bid_prices: self.best_bid = bid_prices[0]
        if ask_prices: self.best_ask = ask_prices[0]

        self.prev_book = self.current_book.copy()
        self.current_book = {
            "bids": dict(zip(bid_prices, bid_vols)),
            "asks": dict(zip(ask_prices, ask_vols))
        }
        
        weights = [1.0, 0.8, 0.6]
        w_bid = sum(v * w for v, w in zip(bid_vols, weights))
        w_ask = sum(v * w for v, w in zip(ask_vols, weights))
        total_w = w_bid + w_ask
        self.wobi = (w_bid - w_ask) / total_w if total_w > 0 else 0.0

        self.book_deltas = {"bids": {}, "asks": {}}
        if self.prev_book["bids"]:
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

            if actual_vol > 50000:
                if p not in self.state.active_walls:
                    self.state.active_walls[p] = {"side": "ASK", "birth_time": now}
                    events.append({"event": "WALL_CREATED", "price": p, "side": "ASK", "delta": actual_vol - old_vol})
            else:
                if p in self.state.active_walls:
                    del self.state.active_walls[p]
                    events.append({"event": "WALL_REMOVED", "price": p, "side": "ASK", "delta": actual_vol - old_vol})

        self.state.traded_vol_at_bid.clear()
        self.state.traded_vol_at_ask.clear()
        
        return events

class SignalInterpreter:
    @staticmethod
    def interpret(events):
        alerts = []
        for e in events:
            if e["event"] == "REPLENISHMENT":
                alerts.append(f"\033[92m💦 [HIDDEN LIQUIDITY] {e['side']} tại {e['price']:,.0f}: Bị ăn {e['matched']} nhưng lại được nhồi thêm {e['amount']} cổ!\033[0m")
            elif e["event"] == "BID_ABSORPTION":
                alerts.append(f"\033[1;95m🛡️ [PASSIVE BUYER] Mức giá {e['price']:,.0f} trụ vững qua {e['ticks']} nhịp xả! (CVD: {e['cvd']})\033[0m")
            elif e["event"] == "ASK_ABSORPTION":
                alerts.append(f"\033[1;96m🛡️ [PASSIVE SELLER] Mức giá {e['price']:,.0f} chặn đà kéo qua {e['ticks']} nhịp! (CVD: {e['cvd']})\033[0m")
            elif e["event"] == "PERSISTENT_WALL":
                alerts.append(f"\033[93m🧱 [SOLID WALL] Tường tại {e['price']:,.0f} đã trụ được {e['age']:.1f} giây. Ý chí phòng thủ cao!\033[0m")
            elif e["event"] == "WALL_CREATED":
                alerts.append(f"\033[93m🧱 [WALL ADDED] {e['side']} kê thêm {e.get('delta', 0):,.0f} cổ tại {e['price']:,.0f}\033[0m")
            elif e["event"] == "WALL_REMOVED":
                alerts.append(f"\033[91m🚨 [WALL PULLED] {e['side']} tường tại {e['price']:,.0f} đã bị rút! (Có dấu hiệu Spoofing)\033[0m")
        return alerts

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

                        trade_data = global_state.process_trade(match_price, match_vol)
                        events = global_event_engine.evaluate_trade_events(trade_data)
                        alerts = global_interpreter.interpret(events)
                        
                        aggressor = trade_data["aggressor"]
                        c = "\033[92m" if aggressor == 1 else "\033[91m" if aggressor == -1 else "\033[93m"
                        side_str = "BUY " if aggressor == 1 else "SELL" if aggressor == -1 else "FLAT"
                        print(f"{c}🔥 [TRADE] {side_str:>4} | Giá: {match_price:,.0f} | Vol: {match_vol:>5}\033[0m")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")

                        # CẬP NHẬT: Lưu trữ biến `aggressor` vào thẳng cột `price_change`
                        with db_lock:
                            cursor.execute("INSERT INTO trades (timestamp, symbol, price, volume, price_change, total_volume) VALUES (?, ?, ?, ?, ?, ?)", (now, code, match_price, match_vol, aggressor, total_vol))
                            conn.commit()

                    # --- XỬ LÝ SỔ LỆNH ---
                    elif "BidAsk" in str(channel_name) and len(parts) >= 66:
                        bp = [float(parts[3]), float(parts[5]), float(parts[7])]
                        bv = [int(parts[4]), int(parts[6]), int(parts[8])]
                        ap = [float(parts[33]), float(parts[35]), float(parts[37])]
                        av = [int(parts[34]), int(parts[36]), int(parts[38])]

                        global_state.process_book(bp, bv, ap, av)
                        events = global_event_engine.evaluate_book_events()
                        alerts = global_interpreter.interpret(events)
                        
                        print(f"📊 [BOOK] MUA 1: {bp[0]:,.0f} ({bv[0]:>5}) | BÁN 1: {ap[0]:,.0f} ({av[0]:>5}) | wOBI: {global_state.wobi:+.2f}")
                        
                        for alert in alerts:
                            print(f"   ➤ {alert}")
                        print("-" * 65)

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