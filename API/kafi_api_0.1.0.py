import requests
import websocket
import json
import time
import threading

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS
# ==============================================================================

# WARNING: Remember to log out from the Kafi portal to invalidate this token after testing!
JWT_TOKEN = ""

# Target symbol for market data
SYMBOL_TO_WATCH = "CTD"

# FiinTrade market data endpoints
NEGOTIATE_URL = "https://wl-realtime.fiintrade.vn/RealtimeHub/negotiate?negotiateVersion=1"
WS_BASE_URL = "wss://wl-realtime.fiintrade.vn/RealtimeHub"

# Request headers fro authentication and routing
custom_headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin: https://banggia.kafi.vn",
    "Accept-Language: vi-VN,vi;q=0.9",
    f"Authorization: Bearer {JWT_TOKEN}"
]

# ==============================================================================
# 2. CORE FUNCTIONS
# ==============================================================================

def get_fresh_connection_id():
    """Fetches a new Connection ID from the SignalR negotiation endpoint."""
    print("[INFO] Negotiating connection ID with the server...")
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://banggia.kafi.vn"
    }
    
    response = requests.post(NEGOTIATE_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        conn_id = data.get("connectionId") or data.get("connectionToken")
        print(f"[SUCCESS] Connection ID acquired: {conn_id}")
        return conn_id
    else:
        print(f"[ERROR] Negotiation failed (Status: {response.status_code}): {response.text}")
        return None

def subscribe_to_stock(ws, symbol):
    """Sends payloads commands to subscribe to Snapshot, Tick, and Ticker data."""
    time.sleep(1) # Brief pause to ensure the server readiness
    
    try:
        # REQUEST 1: END-OF-DAY SNAPSHOT DATA
        payload_snapshot = {
            "arguments": [symbol, "Tick", True],
            "invocationId": "41",
            "target": "SubscribePullMethod",
            "type": 1
        }
        ws.send(json.dumps(payload_snapshot) + chr(30))
        print(f"[INFO] Snapshot data requested for symbol: {symbol}")

        # REQUEST 2: REAL-TIME TICK DATA (MATCHES TRADES)
        payload_tick = {
            "arguments": [f"Realtime.Tick.{symbol}"],
            "invocationId": "45",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_tick) + chr(30))
        print(f"[INFO] Subcribed to real-time tick stream for: {symbol}")

        # REQUEST 3: REAL-TIME TICKER DATA (BID/ASK ORDER BOOK)
        payload_ticker = {
            "arguments": [f"Realtime.Ticker.{symbol}"],
            "invocationId": "46",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_ticker) + chr(30))
        print(f"[INFO] Subcribed to order book (Ticker) stream for: {symbol}")
        print("[INFO] Awaiting data from server...\n" + "-"*50)
        
    except Exception as e:
        print(f"[ERROR] SUbscription exception occurred: {e}")

# ==============================================================================
# 3. WEBSOCKET EVENT HANDLERS
# ==============================================================================

def on_message(ws, message):
    try:
        # Split SignalR messages by the record separator character chr(30)
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': 
                # Ignore server ping hearbeat
                continue
            
            # Successful Handshake response 
            if msg == '{}':
                print("[INFO] Handshake successful. Preparing to subscribe to stock data...")
                # Spawn a daemon thread to subscribe to streams
                threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL_TO_WATCH)).start()
                return

            # Process incoming data streams
            data = json.loads(msg)
            
            # HANDLE SNAPSHOT DATA
            if data.get("type") == 3 and data.get("invocationId") == "41":
                result = data.get("result")
                if result and isinstance(result, list):
                    # Data structure mapping: result[5]=Symbol, result[12]=Price, result[0]=Volume
                    print(f"\n[DATA] SNAPSHOT | Symbol: {result[5]} | Price: {result[12]} | Total Vol: {result[0]}")
            
            # HANDLE PUSHED MARKET DATA (ReceiveMessage)
            if data.get("type") == 1 and data.get("target") == "ReceiveMessage":
                args = data.get("arguments", [])
                if args:
                    channel = args[0].get("chanel")
                    
                    # Process Realtime Tick (Matched Trades)
                    if channel in [f"Realtime.Tick.{SYMBOL_TO_WATCH}", "Realtime.Tick"]:
                        code = args[0].get("code")
                        parts = args[0]["data"][0].split("|")
                        if len(parts) > 10:
                            price = parts[10]
                            vol = parts[15]
                            print(f"[DATA] TICK | Symbol: {code:4} | Price: {price} | Volume: {vol}")
                            
                    # Process Realtime Ticker (Bid/Ask Updates)
                    elif channel in [f"Realtime.Ticker.{SYMBOL_TO_WATCH}", "Realtime.Ticker"]:
                        code = args[0].get("code")
                        parts = args[0]["data"][0].split("|")
                        print(f"[DATA] TICKER | Symbol: {code:4} | Update String: {parts[0][:15]}...")
                 
    except Exception as e: 
        # Silently pass parsing errors for non-JSON payloads, or log them in debug mode
        pass

def on_error(ws, error): 
    print(f"[ERROR] WebSocket connection error: {error}")

def on_close(ws, close_status_code, close_msg): 
    print(f"[WARNING] Connection closed. (Status Code: {close_status_code})")

def on_open(ws):
    print("[INFO] WebSocket connected. Initiating SignalR handshake protocol...")
    ws.send('{"protocol":"json","version":1}' + chr(30))

# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    # STEP 1: Negotiate connection parameters
    fresh_id = get_fresh_connection_id()
    
    if fresh_id:
        # STEP 2: Construct the WebSocket URL with the token
        final_ws_url = f"{WS_BASE_URL}?id={fresh_id}"
        print(f"[INFO] Opening WebSocket gateway to: {final_ws_url}")
        
        websocket.enableTrace(False) # Set to True for low-level debugging
        
        # STEP 3: Initialize and run the WebSocket client
        ws = websocket.WebSocketApp(
            final_ws_url, 
            header=custom_headers, 
            on_open=on_open, 
            on_message=on_message, 
            on_error=on_error, 
            on_close=on_close
        )
        
        ws.keep_running = True
        ws.run_forever()