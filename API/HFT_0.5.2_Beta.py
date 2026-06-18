import requests
import websocket
import json
import time
import threading
import sqlite3
import os
import math
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
        # Bảng 1: Lịch Sử Khớp Lệnh Cơ Bản
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, symbol TEXT, price REAL, volume INTEGER, price_change INTEGER, total_volume INTEGER)''')
        
        # Bảng 2: Sổ Lệnh 10 Cấp Độ L2 Thô
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp DATETIME, symbol TEXT, 
            b_p1 REAL, b_v1 INTEGER, b_p2 REAL, b_v2 INTEGER, b_p3 REAL, b_v3 INTEGER, b_p4 REAL, b_v4 INTEGER, b_p5 REAL, b_v5 INTEGER,
            b_p6 REAL, b_v6 INTEGER, b_p7 REAL, b_v7 INTEGER, b_p8 REAL, b_v8 INTEGER, b_p9 REAL, b_v9 INTEGER, b_p10 REAL, b_v10 INTEGER,
            a_p1 REAL, a_v1 INTEGER, a_p2 REAL, a_v2 INTEGER, a_p3 REAL, a_v3 INTEGER, a_p4 REAL, a_v4 INTEGER, a_p5 REAL, a_v5 INTEGER,
            a_p6 REAL, a_v6 INTEGER, a_p7 REAL, a_v7 INTEGER, a_p8 REAL, a_v8 INTEGER, a_p9 REAL, a_v9 INTEGER, a_p10 REAL, a_v10 INTEGER
        )''')
        
        # Bảng 3: Chỉ số Quant Cụm phòng thủ (HFT Metrics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cluster_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, price_start REAL, price_end REAL,
                side TEXT, absorbed_notional REAL, replenished_notional REAL, attack_notional REAL,
                duration REAL, refill_ratio REAL, cluster_score REAL
            )
        ''')
        
        # Bảng 4: Tick-level Microstructure Data (Ghi lại từng cú Impact & Regime của cá mập)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, price REAL, notional REAL,
                impact_ratio REAL, regime_ratio REAL, is_attack INTEGER
            )
        ''')

        # Bảng 5: OUTCOME LOG - Lưu trữ giá tương lai để backtest
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outcome_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                timestamp DATETIME, 
                event_type TEXT, 
                side TEXT, 
                signal_price REAL, 
                price_1m REAL, 
                price_5m REAL, 
                price_15m REAL
            )
        ''')
        
        conn.commit()
        print("[INFO] SQLite Database initialized: 5 tables ready for full-scale HFT tracking & Outcome analytics.")

# ==============================================================================
# 2. LAYER 2: MARKET STATE & QUANT LIQUIDITY LIFE-CYCLE ENGINE
# ==============================================================================
CLUSTER_PRICE_GAP_PCT = 0.002 
COOLDOWN_DURATION = 10.0
SESSION_TIMEOUT = 60.0       

class MarketState:
    def __init__(self):
        self.last_price = 0.0
        self.best_bid = 0.0
        self.best_ask = 0.0
        
        self.ema_fast = None
        self.ema_slow = None
        
        self.active_sessions = {}
        self.current_book = {"bids": {}, "asks": {}}
        self.prev_book = {"bids": {}, "asks": {}}
        self.traded_vol_at_bid = defaultdict(int)
        self.traded_vol_at_ask = defaultdict(int)

    def process_trade(self, price, volume):
        notional = volume * price
        now = time.time()
        
        if self.ema_fast is None or self.ema_slow is None:
            self.ema_fast = notional
            self.ema_slow = notional
        else:
            self.ema_fast = 0.10 * notional + 0.90 * self.ema_fast
            self.ema_slow = 0.01 * notional + 0.99 * self.ema_slow
            
        regime_ratio = self.ema_fast / self.ema_slow if self.ema_slow > 0 else 1.0

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

        if price in self.active_sessions:
            if now - self.active_sessions[price]["last_update"] > SESSION_TIMEOUT:
                del self.active_sessions[price]

        current_queue = self.current_book["bids"].get(price, 0) if aggressor == -1 else self.current_book["asks"].get(price, 0)
        current_queue_notional = current_queue * price
        if current_queue_notional == 0: current_queue_notional = 1.0
            
        if price not in self.active_sessions:
            self.active_sessions[price] = {
                "state": "ACTIVE",
                "side": "BID" if aggressor == -1 else "ASK",
                "start_time": now,
                "last_update": now,
                "broken_time": None,
                "cvd_notional": 0.0,
                "absorbed_notional": 0.0,
                "replenished_notional": 0.0,
                "max_queue_notional_seen": current_queue_notional,
                "attack_notional": 0.0,
                "ticks_survived": 0
            }
            
        session = self.active_sessions[price]
        session["last_update"] = now 
        
        if session["state"] == "COOLDOWN":
            if now - session["broken_time"] > COOLDOWN_DURATION:
                del self.active_sessions[price]
            return {"type": "TRADE_IGNORED", "aggressor": aggressor}

        session["cvd_notional"] += (aggressor * notional)
        session["absorbed_notional"] += notional
        session["max_queue_notional_seen"] = max(session["max_queue_notional_seen"], current_queue_notional)
        
        impact_ratio = notional / session["max_queue_notional_seen"]
        
        is_attack = 0
        if impact_ratio > 0.15 and regime_ratio > 1.5:
            is_attack = 1
            session["state"] = "UNDER_ATTACK"
            session["attack_notional"] += notional
            session["ticks_survived"] += 1

        with db_lock:
            cursor.execute('''
                INSERT INTO trade_metrics (timestamp, price, notional, impact_ratio, regime_ratio, is_attack)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (now, price, notional, impact_ratio, regime_ratio, is_attack))
            conn.commit()

        self.last_price = price
        return {"type": "TRADE", "price": price, "volume": volume, "aggressor": aggressor, "regime_ratio": regime_ratio}

    def process_book(self, bid_prices, bid_vols, ask_prices, ask_vols):
        if bid_prices: self.best_bid = bid_prices[0]
        if ask_prices: self.best_ask = ask_prices[0]
        now = time.time()

        self.prev_book = self.current_book.copy()
        self.current_book = {
            "bids": dict(zip(bid_prices, bid_vols)),
            "asks": dict(zip(ask_prices, ask_vols))
        }

        for p in list(self.active_sessions.keys()):
            session = self.active_sessions[p]
            
            if now - session["last_update"] > SESSION_TIMEOUT:
                del self.active_sessions[p]
                continue
                
            if session["state"] == "COOLDOWN":
                if now - session["broken_time"] > COOLDOWN_DURATION:
                    del self.active_sessions[p]
                continue

            if session["side"] == "BID":
                actual_vol = self.current_book["bids"].get(p, 0)
                old_vol = self.prev_book["bids"].get(p, 0)
                matched_vol = self.traded_vol_at_bid.get(p, 0)
            else:
                actual_vol = self.current_book["asks"].get(p, 0)
                old_vol = self.prev_book["asks"].get(p, 0)
                matched_vol = self.traded_vol_at_ask.get(p, 0)

            expected_vol = max(0, old_vol - matched_vol)
            actual_notional = actual_vol * p
            expected_notional = expected_vol * p
            matched_notional = matched_vol * p
            
            if actual_vol != old_vol:
                session["last_update"] = now 
            
            if actual_notional > expected_notional:
                replenished_money = actual_notional - expected_notional
                session["replenished_notional"] += replenished_money
                session["state"] = "REPLENISHED"
            
            if actual_notional > 0:
                session["max_queue_notional_seen"] = max(session["max_queue_notional_seen"], actual_notional)

            net_liquidity_loss = session["absorbed_notional"] - session["replenished_notional"]
            if net_liquidity_loss > (0.8 * session["max_queue_notional_seen"]):
                session["state"] = "COOLDOWN"
                session["broken_time"] = now
            elif matched_notional > 0 and session["state"] != "REPLENISHED":
                session["state"] = "ABSORBED"

        return {"type": "BOOK_UPDATE"}

# ==============================================================================
# 3. LAYER 3: QUANT EVENT ENGINE & ALERT MANAGER
# ==============================================================================
ALERT_COOLDOWN = 30.0        
FAKE_BREAKOUT_WINDOW = 3.0   

class EventEngine:
    def __init__(self, state: MarketState):
        self.state = state
        self.cluster_alert_memory = {} 

    def _get_liquidity_clusters(self, side):
        active_items = [(p, s) for p, s in self.state.active_sessions.items() if s["side"] == side and s["state"] != "COOLDOWN"]
        if not active_items: return []
            
        active_items.sort(key=lambda x: x[0], reverse=(side == "BID"))
        clusters = []
        current_cluster = [active_items[0]]
        
        for i in range(1, len(active_items)):
            prev_price = current_cluster[-1][0]
            curr_price = active_items[i][0]
            
            if abs(prev_price - curr_price) / prev_price <= CLUSTER_PRICE_GAP_PCT:
                current_cluster.append(active_items[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [active_items[i]]
        if current_cluster: clusters.append(current_cluster)
        return clusters

    def evaluate_book_events(self):
        events = []
        now = time.time()
        
        for side in ["BID", "ASK"]:
            clusters = self._get_liquidity_clusters(side)
            
            for cluster in clusters:
                if len(cluster) == 0: continue
                
                prices = [item[0] for item in cluster]
                p_start, p_end = min(prices), max(prices)
                
                cluster_absorbed_money = sum([item[1]["absorbed_notional"] for item in cluster])
                cluster_replenished_money = sum([item[1]["replenished_notional"] for item in cluster])
                cluster_attack_money = sum([item[1]["attack_notional"] for item in cluster])
                
                earliest_start = min([item[1]["start_time"] for item in cluster])
                duration_seconds = max(1.0, now - earliest_start)
                
                refill_ratio = cluster_replenished_money / max(cluster_absorbed_money, 1.0)
                capped_refill = min(refill_ratio, 1.0)
                
                cluster_score = (math.log(1 + cluster_attack_money) * capped_refill) / math.log(2 + duration_seconds)
                
                with db_lock:
                    cursor.execute('''
                        INSERT INTO cluster_metrics (timestamp, price_start, price_end, side, absorbed_notional, replenished_notional, attack_notional, duration, refill_ratio, cluster_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (now, p_start, p_end, side, cluster_absorbed_money, cluster_replenished_money, cluster_attack_money, duration_seconds, refill_ratio, cluster_score))
                    conn.commit()
                
                if cluster_score > 1.2 and cluster_replenished_money >= 500_000_000:
                    cluster_key = (p_start, p_end, side)
                    last_alert = self.cluster_alert_memory.get(cluster_key, 0)
                    
                    if now - last_alert > ALERT_COOLDOWN:
                        events.append({
                            "event": "QUANT_CLUSTER_DEFENSE",
                            "side": side,
                            "price_start": p_start,
                            "price_end": p_end,
                            "absorbed_notional": cluster_absorbed_money,
                            "replenished_notional": cluster_replenished_money,
                            "duration": duration_seconds,
                            "score": cluster_score
                        })
                        self.cluster_alert_memory[cluster_key] = now

        cooldown_sessions = [p for p, s in self.state.active_sessions.items() if s["state"] == "COOLDOWN"]
        if len(cooldown_sessions) >= 2:
            cooldown_sessions.sort()
            for i in range(len(cooldown_sessions) - 1):
                p1, p2 = cooldown_sessions[i], cooldown_sessions[i+1]
                if (p2 - p1) / p1 <= CLUSTER_PRICE_GAP_PCT:
                    s1, s2 = self.state.active_sessions[p1], self.state.active_sessions[p2]
                    if s1["broken_time"] and s2["broken_time"] and abs(s1["broken_time"] - s2["broken_time"]) <= 5.0:
                        events.append({
                            "event": "QUANT_CLUSTER_CASCADE_BREAKOUT",
                            "side": s1["side"],
                            "price_start": p1,
                            "price_end": p2,
                            "total_damage": s1["absorbed_notional"] + s2["absorbed_notional"]
                        })
                        del self.state.active_sessions[p1]
                        del self.state.active_sessions[p2]
                        break

        for p, session in list(self.state.active_sessions.items()):
            if session["state"] == "COOLDOWN" and session["broken_time"]:
                if now - session["broken_time"] <= FAKE_BREAKOUT_WINDOW:
                    actual_vol = self.state.current_book["bids"].get(p, 0) if session["side"] == "BID" else self.state.current_book["asks"].get(p, 0)
                    if actual_vol * p > (0.5 * session["max_queue_notional_seen"]):
                        events.append({
                            "event": "QUANT_FAKE_BREAKOUT_DETECTED",
                            "side": session["side"],
                            "price": p,
                            "trap_value": actual_vol * p
                        })
                        session["state"] = "REPLENISHED"
                        session["broken_time"] = None

        return events

class SignalInterpreter:
    @staticmethod
    def interpret(events):
        alerts = []
        for e in events:
            if e["event"] == "QUANT_CLUSTER_DEFENSE":
                zone_str = f"{e['price_start']:,.0f}" if e['price_start'] == e['price_end'] else f"{e['price_start']:,.0f} - {e['price_end']:,.0f}"
                alerts.append(
                    f"\033[1;44;97m [INSTITUTIONAL DEFENSE ZONE] Phe {e['side']} Vùng {zone_str}: \n"
                    f"   >> Hấp thụ: {e['absorbed_notional']/1e6:,.1f} tr | Tiếp tế thêm: {e['replenished_notional']/1e6:,.1f} tr\n"
                    f"   >> Thời gian giằng co: {e['duration']:.1f}s | Velocity Score: {e['score']:.2f}! \033[0m"
                )
            elif e["event"] == "QUANT_CLUSTER_CASCADE_BREAKOUT":
                alerts.append(
                    f"\033[1;41;97m [⚡ CASCADE BREAKOUT ⚡] SỤP ĐỔ DÂY CHUYỀN! Cụm {e['side']} vùng {e['price_start']:,.0f} - {e['price_end']:,.0f} đã VỠ! \n"
                    f"   >> Tổng thiệt hại: {e['total_damage']/1e6:,.1f} triệu VNĐ. \033[0m"
                )
            elif e["event"] == "QUANT_FAKE_BREAKOUT_DETECTED":
                alerts.append(
                    f"\033[1;45;97m [⚠️ BEAR/BULL TRAP DETECTED] BẪY! Mức {e['price']:,.0f} vừa thủng nhưng lập tức kê lại {e['trap_value']/1e6:,.1f} triệu VNĐ! \033[0m"
                )
        return alerts

# ==============================================================================
# 4. BACKGROUND OUTCOME TRACKER (ASYNC DAEMON)
# ==============================================================================
class OutcomeTracker:
    def __init__(self, state: MarketState):
        self.state = state
        self.pending_signals = []
        self.lock = threading.Lock()
        
        # Start daemon thread
        threading.Thread(target=self._background_watcher, daemon=True).start()

    def register_signal(self, event_type, side, signal_price):
        now = time.time()
        with self.lock:
            self.pending_signals.append({
                "event_type": event_type,
                "side": side,
                "signal_time": now,
                "signal_price": signal_price,
                "p_1m": None, 
                "p_5m": None, 
                "p_15m": None
            })

    def _background_watcher(self):
        while True:
            time.sleep(1.0)
            now = time.time()
            current_price = self.state.last_price
            
            if current_price == 0: 
                continue

            with self.lock:
                for sig in self.pending_signals[:]:
                    elapsed = now - sig["signal_time"]

                    if elapsed >= 60 and sig["p_1m"] is None:
                        sig["p_1m"] = current_price
                        
                    if elapsed >= 300 and sig["p_5m"] is None:
                        sig["p_5m"] = current_price
                        
                    if elapsed >= 900 and sig["p_15m"] is None:
                        sig["p_15m"] = current_price
                        
                        dt_string = datetime.fromtimestamp(sig["signal_time"]).strftime('%Y-%m-%d %H:%M:%S')
                        
                        with db_lock:
                            cursor.execute('''
                                INSERT INTO outcome_log (timestamp, event_type, side, signal_price, price_1m, price_5m, price_15m)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (dt_string, sig["event_type"], sig["side"], sig["signal_price"], sig["p_1m"], sig["p_5m"], sig["p_15m"]))
                            conn.commit()
                            
                        self.pending_signals.remove(sig)

# Khởi tạo Đối Tượng Toàn Cục
global_state = MarketState()
global_event_engine = EventEngine(global_state)
global_interpreter = SignalInterpreter()
global_outcome_tracker = OutcomeTracker(global_state)


# ==============================================================================
# 5. WEBSOCKET & DATA PROCESSING ENGINE
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
        print(f"[INFO] HFT Microstructure Engine fully armed for {symbol}!\n{'='*65}")
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

                    # --- TICK PROCESSING ---
                    if "Tick" in str(channel_name) and len(parts) >= 18:
                        match_price = float(parts[13])
                        match_vol = int(parts[17])
                        total_vol = int(parts[0])

                        trade_data = global_state.process_trade(match_price, match_vol)
                        events = global_event_engine.evaluate_book_events()
                        alerts = global_interpreter.interpret(events)
                        
                        # Gửi Event cho Outcome Tracker ngầm
                        for e in events:
                            sig_price = e.get("price") or ((e.get("price_start", 0) + e.get("price_end", 0)) / 2)
                            global_outcome_tracker.register_signal(e["event"], e.get("side", "UNKNOWN"), sig_price)
                        
                        aggressor = trade_data["aggressor"]
                        c = "\033[92m" if aggressor == 1 else "\033[91m" if aggressor == -1 else "\033[93m"
                        side_str = "BUY " if aggressor == 1 else "SELL" if aggressor == -1 else "FLAT"
                        print(f"{c}[TRADE] {side_str:>4} | Price: {match_price:,.0f} | Vol: {match_vol:>5} | Regime: {trade_data.get('regime_ratio',1.0):.2f}\033[0m")
                        
                        for alert in alerts: print(f"   ➤ {alert}")

                        with db_lock:
                            cursor.execute("INSERT INTO trades (timestamp, symbol, price, volume, price_change, total_volume) VALUES (?, ?, ?, ?, ?, ?)", (now, code, match_price, match_vol, aggressor, total_vol))
                            conn.commit()

                    # --- LEVEL 2 BOOK PROCESSING ---
                    elif "BidAsk" in str(channel_name) and len(parts) >= 60:
                        bp = [float(parts[i]) for i in range(3, 23, 2)]
                        bv = [int(parts[i]) for i in range(4, 24, 2)]
                        ap = [float(parts[i]) for i in range(33, 53, 2)]
                        av = [int(parts[i]) for i in range(34, 54, 2)]

                        global_state.process_book(bp[:3], bv[:3], ap[:3], av[:3])
                        events = global_event_engine.evaluate_book_events()
                        alerts = global_interpreter.interpret(events)
                        
                        # Gửi Event cho Outcome Tracker ngầm
                        for e in events:
                            sig_price = e.get("price") or ((e.get("price_start", 0) + e.get("price_end", 0)) / 2)
                            global_outcome_tracker.register_signal(e["event"], e.get("side", "UNKNOWN"), sig_price)
                        
                        print(f"[BOOK] BID 1: {bp[0]:,.0f} ({bv[0]:>5}) | ASK 1: {ap[0]:,.0f} ({av[0]:>5})")
                        for alert in alerts: print(f"   ➤ {alert}")
                        print("-" * 65)

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
# 6. AUTO-RECONNECT ENGINE
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
            ws.run_forever(ping_interval=15, ping_timeout=10)
        
        print("[WARNING] Link severed. Auto-recovering in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    start_trading_bot()