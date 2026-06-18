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

import time
from collections import defaultdict

import time
import math
from collections import defaultdict

import time
import math
from collections import defaultdict

# ==============================================================================
# 2. LAYER 2: MARKET STATE & QUANT LIQUIDITY LIFE-CYCLE ENGINE
# ==============================================================================

ACTIVE_ZONE_SPREAD_MULTIPLIER = 10 
CLUSTER_PRICE_GAP_PCT = 0.002 # Các mức giá cách nhau <= 0.2% sẽ được gộp thành 1 Cluster

class MarketState:
    def __init__(self):
        self.last_price = 0.0
        self.best_bid = 0.0
        self.best_ask = 0.0
        
        # Thêm biến theo dõi EMA của Notional (Bắt đầu bằng None để khởi tạo chuẩn xác)
        self.trade_notional_ema = None
        
        self.price_memory = defaultdict(lambda: {"total_vol": 0, "total_cvd": 0})
        self.active_sessions = {}
        self.current_book = {"bids": {}, "asks": {}}
        self.prev_book = {"bids": {}, "asks": {}}
        self.wobi = 0.0
        self.book_deltas = {"bids": {}, "asks": {}}
        self.traded_vol_at_bid = defaultdict(int)
        self.traded_vol_at_ask = defaultdict(int)
        self.active_walls = {}

    def process_trade(self, price, volume):
        notional = volume * price
        
        # Cập nhật EMA của quy mô lệnh (Tự học theo thời gian thực)
        if self.trade_notional_ema is None:
            self.trade_notional_ema = notional
        else:
            self.trade_notional_ema = 0.99 * self.trade_notional_ema + 0.01 * notional
            
        # Tính toán mức độ đột biến của lệnh (Trade Z-Score)
        trade_z = notional / self.trade_notional_ema if self.trade_notional_ema > 0 else 0

        # Xác định phe chủ động... (Giữ nguyên logic cũ)
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

        # Cập nhật Memory... (Giữ nguyên logic cũ)
        self.price_memory[price]["total_vol"] += volume
        self.price_memory[price]["total_cvd"] += (aggressor * volume)

        # Khởi tạo/Cập nhật Active Session...
        current_queue = self.current_book["bids"].get(price, 0) if aggressor == -1 else self.current_book["asks"].get(price, 0)
        if current_queue == 0: current_queue = 1 
            
        if price not in self.active_sessions:
            self.active_sessions[price] = {
                "state": "ACTIVE",
                "side": "BID" if aggressor == -1 else "ASK",
                "start_time": time.time(),
                "cvd": 0,
                "absorbed_volume": 0,
                "replenished_volume": 0,
                "removed_volume": 0,
                "initial_queue": current_queue,
                "max_queue_seen": current_queue,
                "attack_volume": 0,
                "ticks_survived": 0
            }
            
        session = self.active_sessions[price]
        session["cvd"] += (aggressor * volume)
        session["absorbed_volume"] += volume
        session["max_queue_seen"] = max(session["max_queue_seen"], current_queue)
        
        # ==========================================
        # LOGIC NHẬN DIỆN TẤN CÔNG HOÀN TOÀN MỚI
        # ==========================================
        impact_ratio = volume / session["max_queue_seen"]
        
        # Điều kiện: Lệnh phải ăn >= 15% Max Queue VÀ Lớn gấp 2 lần lệnh bình thường
        is_significant_attack = (impact_ratio > 0.15) and (trade_z > 2.0)
        
        if is_significant_attack:
            session["state"] = "UNDER_ATTACK"
            session["attack_volume"] += volume
            session["ticks_survived"] += 1

        self.last_price = price
        return {
            "type": "TRADE", 
            "price": price, 
            "volume": volume, 
            "aggressor": aggressor,
            "trade_z": trade_z  # Có thể log ra để debug xem lệnh bự gấp mấy lần bình thường
        }


# ==============================================================================
# 3. LAYER 3: QUANT EVENT ENGINE (WITH LIQUIDITY CLUSTERS)
# ==============================================================================
class EventEngine:
    def __init__(self, state: MarketState):
        self.state = state

    def _get_liquidity_clusters(self, side):
        # Thuật toán gom cụm các mức giá phòng thủ liền kề
        sessions = [(p, s) for p, s in self.state.active_sessions.items() if s["side"] == side]
        if not sessions:
            return []
            
        sessions.sort(key=lambda x: x[0], reverse=(side == "BID"))
        clusters = []
        current_cluster = [sessions[0]]
        
        for i in range(1, len(sessions)):
            prev_price = current_cluster[-1][0]
            curr_price = sessions[i][0]
            
            # Gộp nếu khoảng cách <= 0.2% thị giá
            if abs(prev_price - curr_price) / prev_price <= CLUSTER_PRICE_GAP_PCT:
                current_cluster.append(sessions[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sessions[i]]
                
        if current_cluster:
            clusters.append(current_cluster)
            
        return clusters

    def evaluate_book_events(self):
        events = []
        now = time.time()
        
        # 1. QUÉT CLUSTERS: Phát hiện Cụm Phòng Tuyến Tổ Chức (Institutional Zone)
        for side in ["BID", "ASK"]:
            clusters = self._get_liquidity_clusters(side)
            
            for cluster in clusters:
                if len(cluster) == 0: continue
                
                prices = [item[0] for item in cluster]
                cluster_cvd = sum([item[1]["cvd"] for item in cluster])
                cluster_absorbed = sum([item[1]["absorbed_volume"] for item in cluster])
                cluster_replenished = sum([item[1]["replenished_volume"] for item in cluster])
                cluster_attack = sum([item[1]["attack_volume"] for item in cluster])
                
                # Tính Score chung cho cả Cụm bằng công thức Logarit giảm xóc
                refill_ratio = cluster_replenished / max(cluster_absorbed, 1)
                capped_refill_ratio = min(refill_ratio, 1.0)
                cluster_score = math.log(1 + cluster_attack) * capped_refill_ratio
                
                # Lọc tín hiệu Cluster mạnh (Score đủ lớn & nhiều lệnh đập)
                if cluster_score > 5.0 and cluster_replenished > 0:
                    events.append({
                        "event": "QUANT_CLUSTER_DEFENSE",
                        "side": side,
                        "price_start": min(prices),
                        "price_end": max(prices),
                        "absorbed_vol": cluster_absorbed,
                        "refilled_vol": cluster_replenished,
                        "score": cluster_score
                    })
        
        # 2. XỬ LÝ SỰ KIỆN SINGLE LEVEL (Thất thủ & Replenish Đơn Lẻ)
        for p, session in list(self.state.active_sessions.items()):
            if session["state"] == "BROKEN":
                refill_ratio = session["replenished_volume"] / max(session["absorbed_volume"], 1)
                events.append({
                    "event": "QUANT_SESSION_BROKEN",
                    "price": p,
                    "side": session["side"],
                    "absorbed_vol": session["absorbed_volume"],
                    "refill_ratio": refill_ratio
                })
                del self.state.active_sessions[p]

        # Xử lý Tường Cơ bản (Giữ nguyên logic cũ cho walls)
        # ... (Có thể giữ lại đoạn logic tính tường cũ nếu muốn)
        
        return events


class SignalInterpreter:
    @staticmethod
    def interpret(events):
        alerts = []
        for e in events:
            if e["event"] == "QUANT_CLUSTER_DEFENSE":
                zone_str = f"{e['price_start']:,.0f}" if e['price_start'] == e['price_end'] else f"{e['price_start']:,.0f} - {e['price_end']:,.0f}"
                alerts.append(
                    f"\033[1;44;97m [INSTITUTIONAL DEFENSE ZONE] {e['side']} Vùng {zone_str}: \n"
                    f"   >> Đã Hấp thụ: {e['absorbed_vol']:,.0f} cổ | Tiếp tế thêm: {e['refilled_vol']:,.0f} cổ\n"
                    f"   >> Tín hiệu sức mạnh (Score): {e['score']:.2f}! \033[0m"
                )
            elif e["event"] == "QUANT_SESSION_BROKEN":
                alerts.append(
                    f"\033[1;41;97m [DEFENSE BROKEN] Phòng tuyến {e['side']} tại {e['price']:,.0f} THẤT THỦ! "
                    f"(Net Loss vượt 80% Max Queue) \033[0m"
                )
        return alerts

# Khởi tạo
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