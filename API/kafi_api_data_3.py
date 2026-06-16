import requests
import websocket
import json
import time
import threading

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ CƠ BẢN
# ==============================================================================

# Token VIP từ phiên đăng nhập của bạn
JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJ4NWMiOlsiTUlJQzZqQ0NBZEtnQXdJQkFnSUdBWThBRjRoUU1BMEdDU3FHU0liM0RRRUJDd1VBTURZeE5EQXlCZ05WQkFNTUswNXlPRUp1ZUhSeWJYazJSRm95VmtOYU5UVnBjbVF5WkU5S2Rta3pRbGxSV0RaUVdHaFBNVVpEUmtFd0hoY05NalF3TkRJeE1EazFPREV6V2hjTk1qVXdNakUxTURrMU9ERXpXakEyTVRRd01nWURWUVFEREN0T2NqaENibmgwY20xNU5rUmFNbFpEV2pVMWFYSmtNbVJQU25acE0wSlpVVmcyVUZob1R6RkdRMFpCTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFxNnRFVE9pRE1Cd3VTTFA3QlB6M1ZyL2VBVm96SDVSbXNhRUtMRW9tVXpPRDBKS3lVV2xPRTlBRnAxczhyUlAvTmFpRzVHYStGcGdvWkY1d3FzeXc1a21iYlJKa1MzenFPWk5mSmdad1dXbzRneExhdzE1UXJGVDJ5ZDZZREx2SzJ5WGo0VGNUSXVtQ09pUEFOMFpBWk4xNDBYMjMzWDRyM082MW1aeVVEMW0xR1FDQnU5b3drY2ZiOW9RMVpqZitYeE5tS3B4ZVBES2xrRFJDM0ZSUkdMWmV6RXM3SHBYdllJcExBS0Z5YW4xREtlc2JwY2lFeUhGci9hdkJqKzJBNGRwVFFqZ3BmcjRZc2cwYkE5dkhwT2E5V0FKWisvSTJFVGdqYmF0eHR0bFZISUZZWDZPYW5FemMvY3FIQVhFSFlNQ0pxNEViQTVjWHk3UDllUGVrK3dJREFRQUJNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUF2SXRic0RtTUhWckRKVFl6OEdwQk0vbno5bklZUE5UYW5MNjdISjU5R1NMVzF2VkhmTHdLTWp1Ylh0VzdMQktZaVlGSHpNK1RHamd2aW1mVFdzU3phSXRJRTNjVHl5VXRHMy9Pc2J0T1M0Vm1reGsyMzJWajBZbGFDeVVyeTJQU3B1UWVBMi93eGc5Nyt2UTVOQUVYbmpoSDZSM1FsT2JNZXc1SXdOZGpsekZlMjJmNUdKaHNxUi94RVNmSVE4MURvaEZmT2JhRmswZ3ZHQ2ZaeEEva0xySUF1MHc3VVpZTGdWTzgvUDlLR0NHWDc4RTZGZm96REZlbDFLU205eC9IQThnTm0xS0NQSlhGaE1oZGJoWE5SZWhUQW5jektudlpqcC9lS2UvQkNUaFdSWHl0ZUpicVI1WHZjRzk4eEZDYTZyYjFxVEUxb21FbkZJMVR4SU1HZyJdLCJhbGciOiJSUzI1NiJ9.eyJkZXZpY2VJbmZvIjp7ImRldmljZUlkIjoiMmU1NmI3MDItNTQ3ZC00NTYwLWFmNzAtNTQzMWRlODNiMGMyIiwiZGV2aWNlTmFtZSI6InVua25vd24iLCJkZXZpY2VNb2RlbCI6InVua25vd24iLCJkZXZpY2VPc1ZlcnNpb24iOiJ1bmtub3duIiwiZGV2aWNlT3MiOiJ1bmtub3duIn0sImV4cCI6MTc4MTUyNDU4NywiaXNzIjoicmhqQVR2UDZyMmdGOVU2Nmk3dmc5Q2V5Y3FzaU16anQiLCJsb2dpblVVSUQiOiJUT0tFTl9MT0dJTl80Mzc2MV8yMDI2MDYxNTEwNTYyN18yMDI2MDYxNTE4NTYyN185ZDY2OGY1My1lNGYwLTRmOGEtOWEyZS1kM2EwYzViM2Q2YWEiLCJpYXQiOjE3ODE0OTU3ODcsImNsaWVudElkIjoiNTY5NzYiLCJjaWQiOiJkMTU2ZWNhNS1jNTNkLTQ3M2ItOTBjZC00M2NlMWVlNmNmZmYiLCJpc3Jlc2V0IjoiTiIsInNnSWRzIjpbMSwzLDEyLDgsMTQsOSwxMSw1LDM1LDI4LDMwLDUyLDU1LDgwLDgzLDg0LDEwNiwxMDksMTE5XSwidWQiOnsiZXgiOnsiY29yZVVzZXJJZCI6IjAwMDEwMTg5MjEiLCJsZXZlbCI6IkNVU1RPTUVSIiwic3ViTnVtYmVycyI6W3siYWNjb3VudHR5cGVuYW1lIjoiQ0FTSCAtIE4xIDAuMTUlIDEyJSIsImlzb3duZXIiOiJZIiwidmFsZGF0ZSI6IjA3LzEwLzIwMjQiLCJzdWJUeXBlIjoiRVFVSVRZIiwic2hvcnRhY2N0bm8iOiIwMSIsIm1ydHlwZSI6Ik4iLCJhdXRvYWR2IjoiWSIsImFjY291bnR0eXBlYnJpZWZuYW1lIjoiRmVlIDAuMTUlIE1hcmdpbiAxMiUiLCJhY2NvdW50dHlwZSI6IjAwMTEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidmFhY2N0bm9saXN0IjoiS0FGNjQ5MjgyMSIsImF1dGh0eXBlIjoiMSIsImF1dGhjb2RlIjoiQURXSU5QVVQvQ0FTSFRSQU5TL0NBU0hUUkFOU0VORERBVEUvQ09ORF9PUkRFUi9DT05GSVJNT1JERVIvREVQT1NJVC9FWFRFTkQvR1JPVVBfT1JERVIvSVNTVUVJTlBVVC9PUkRJTlBVVC9SRVNFVFBBU1MvU1RPQ0tUUkFOUy9UQUtFSU4iLCJtb2JpbGVzbXMiOiIwOTQ4NjQ5MjgyIiwiYWNjb3VudG5oIjoiMDAwMTAyMzU1NyIsIm9wZW5kYXRlIjoiMjAyNC0xMC0wN1QwMDowMDowMFoiLCJ2aWEiOiJBIiwic3ViTnVtYmVyIjoiMDAwMTAyMzU1NyIsImFjY291bnRuYW1lIjoiTmd1eeG7hW4gQW5oIFF1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MH0seyJhY2NvdW50dHlwZW5hbWUiOiJNQVJHSU4gLSBOMSAwLjE1JSAxMiUiLCJpc293bmVyIjoiWSIsInZhbGRhdGUiOiIwNy8xMC8yMDI0Iiwic3ViVHlwZSI6IkVRVUlUWSIsInNob3J0YWNjdG5vIjoiMDYiLCJtcnR5cGUiOiJUIiwiYXV0b2FkdiI6IlkiLCJhY2NvdW50dHlwZWJyaWVmbmFtZSI6IkZlZSAwLjE1JSBNYXJnaW4gMTIlIiwiYWNvdW50dHlwZSI6IjAwMTIiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6ZmFsc2UsInZhYWNjdG5vbGlzdCI6IktBRjY0OTI4MjYiLCJhdXRodHlwZSI6IjEiLCJhdXRoY29kZSI6IkFEV0lOUFVUL0NBU0hUUkFOUy9DQVNIVFJBTlNFTkREQVRFL0NPTkRfT1JERVIvQ09ORklSTU9SREVSL0RFUE9TSVQvRVhURU5EL0dST1VQX09SREVSL0lTU1VCSU5QVVQvT1JESU5QVVQvUkVTRVRQQVNTL1NUT0NLVFJBTlMvVEFLRUlOIiwibW9iaWxlc21zIjoiMDk0ODY0OTI4MiIsImFjY291bnRubyI6IjAwMDEwMjM1NTgiLCJvcGVuZGF0ZSI6IjIwMjQtMTAtMDdUMDA6MDA6MDBaIiwidmlhIjoiQSIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTgiLCJhY2NvdW50bmFtZSI6Ik5ndXnhu4VuIEFuaBR1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MTAwMDAwMDAwMH0seyJyZWFjdG5vIjoiMDAwMTAwMDAwMTAwMDEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidDBpbWxpbWl0IjoiMCIsInZhYWNjdG5vIjoiS0FGNjQ5MjgyOCIsInN1YlR5cGUiOiJERVJJVkFUSVZFUyIsInN0YXR1cyI6IkEiLCJkdGFTdGF0dXMiOiJBIiwiZG1BY2N0bm8iOiIwNDlDNjQ5MjgyIiwiYWZ0eXBlIjoiMDAwMyIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTciLCJjZENvbnRlbnQiOiIwMDAxMDIzNTU3IiwiY2Z0eXBlIjoiMDAwMSIsImF2bGNhc2hvbmhhbmQiOiIwIn1dfSwiaSI6NDM3NjEsInUiOiIwNDlDNjQ5MjgyIiwicklkcyI6WzFdfSwia2NVc2VySWQiOiIyMzEyNDkyZi05YWJlLTQ3M2YtYTZhMy1mZTc4ZWMwNWZmMzUiLCJmbGV4QWNjb3VudE51bWJlciI6IjA0OUM2NDkyODIiLCJjdXN0b21Vc2VybmFtZSI6IjA0OWM2NDkyODIifQ.baf5Zww3juu9xcMW_w3QODnYUn5mBJZOFU9aUUdKO2Q1gFtWtUTdSzOd0Pb0V95xWaDWtAZo6z6rViNvLPaeut1x8XF7twjE3l3KaCbJh5MNf4J5yGkSyHV55hrFPXZjJ5ppZqLXZZZYMqBLUVv8eLi_gAjFUwmWuy3ALfAWVNLBBRkFRmcYhfxt92KcE2WHttsOFInJ0JRSQTXhejXQQE5-y40TQUf22XWOHezx1hnw5jYqBq6GQTRwlO_rPtANaVlYL3VkDOTY_VH7WJwMws_t4HSNvgzutClGQ-Db3s4757OiN4Y-4qIHsoOWyrHfGx7qIL9UCpPP1lwidRQpng"

SYMBOL_TO_WATCH = "CTD"

NEGOTIATE_URL = "https://wl-realtime.fiintrade.vn/RealtimeHub/negotiate?negotiateVersion=1"
WS_BASE_URL = "wss://wl-realtime.fiintrade.vn/RealtimeHub"

custom_headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin: https://banggia.kafi.vn",
    "Accept-Language: vi-VN,vi;q=0.9",
    f"Authorization: Bearer {JWT_TOKEN}"
]

# ==============================================================================
# 2. XIN QUYỀN VÀ ĐĂNG KÝ CÁC KÊNH
# ==============================================================================

def get_fresh_connection_id():
    print("🎫 Đang mang Thẻ VIP đến hệ thống FiinTrade xin vé (Connection ID)...")
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://banggia.kafi.vn"
    }
    try:
        response = requests.post(NEGOTIATE_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            conn_id = data.get("connectionId") or data.get("connectionToken")
            print(f"✅ Đã nhận vé: {conn_id}")
            return conn_id
    except Exception as e:
        print(f"❌ Lỗi mạng: {e}")
    return None

def subscribe_to_stock(ws, symbol):
    time.sleep(1) 
    try:
        # 1. Đăng ký kênh Khớp Lệnh (Tick)
        payload_tick = {
            "arguments": [f"Realtime.Tick.{symbol}"],
            "invocationId": "45",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_tick) + chr(30))
        
        # 2. Giăng lưới các tên miền có thể chứa Sổ lệnh
        potential_channels = ["Quote", "BidAsk", "Depth", "MarketDepth", "OrderBook"]
        for idx, channel in enumerate(potential_channels):
            payload_quote = {
                "arguments": [f"Realtime.{channel}.{symbol}"],
                "invocationId": str(50 + idx),
                "target": "JoinGroup",
                "type": 1
            }
            ws.send(json.dumps(payload_quote) + chr(30))

        print(f"🎯 Đã đăng ký luồng Tick và giăng lưới Sổ Lệnh (Quote/BidAsk) cho {symbol}!")
        print("="*60)
    except Exception as e:
        print(f"❌ Lỗi Subscribe: {e}")

# ==============================================================================
# 3. HÀM XỬ LÝ MESSAGE - IN KHỚP LỆNH CHUẨN & THEO DÕI SỔ LỆNH
# ==============================================================================

def on_message(ws, message):
    try:
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': 
                continue 
            
            if msg == '{}':
                print("🎉 HANDSHAKE THÀNH CÔNG!")
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
                    
                    if not raw_data_list or code != SYMBOL_TO_WATCH:
                        continue
                        
                    raw_string = raw_data_list[0]
                    parts = raw_string.split("|")
                    
                    # --- XỬ LÝ LUỒNG KHỚP LỆNH (Tick) ---
                    if "Tick" in str(channel_name):
                        if len(parts) >= 18:
                            total_vol = parts[0]
                            match_price = parts[13]
                            change = parts[15]
                            match_vol = parts[17]
                            print(f"🔥 [KHỚP LỆNH] Giá: {match_price} ({change}đ) | Vol khớp: {match_vol:>5} | Tổng Vol: {total_vol}")
                    
                    # --- BẮT QUẢ TANG LUỒNG SỔ LỆNH (Quote/BidAsk/Depth...) ---
                    elif any(c in str(channel_name) for c in ["Quote", "BidAsk", "Depth", "OrderBook", "MarketDepth"]):
                        print(f"\n✅ [BẮT ĐƯỢC SỔ LỆNH] Kênh chính xác là: {channel_name}")
                        print(f"Chuỗi thô để phân tích Index: {raw_string}")
                        print("-" * 60)

    except Exception as e: 
        pass

def on_error(ws, error): pass
def on_close(ws, close_status_code, close_msg): pass

def on_open(ws):
    print("🚀 Kết nối thành công! Gửi thư thiết lập giao thức...")
    ws.send('{"protocol":"json","version":1}' + chr(30))

# ==============================================================================
# 4. CHẠY CHƯƠNG TRÌNH
# ==============================================================================

def start_trading_bot():
    fresh_id = get_fresh_connection_id()
    if fresh_id:
        final_ws_url = f"{WS_BASE_URL}?id={fresh_id}"
        print(f"🔗 Mở cổng WebSocket tới: {final_ws_url}")
        
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

if __name__ == "__main__":
    start_trading_bot()