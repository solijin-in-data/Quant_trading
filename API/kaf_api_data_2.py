import requests
import websocket
import json
import time
import threading

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ CƠ BẢN
# ==============================================================================

# 🚨 CẢNH BÁO: CHẠY TEST XONG NHỚ LÊN WEB KAFI BẤM ĐĂNG XUẤT ĐỂ HỦY TOKEN NÀY NHÉ!
JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJ4NWMiOlsiTUlJQzZqQ0NBZEtnQXdJQkFnSUdBWThBRjRoUU1BMEdDU3FHU0liM0RRRUJDd1VBTURZeE5EQXlCZ05WQkFNTUswNXlPRUp1ZUhSeWJYazJSRm95VmtOYU5UVnBjbVF5WkU5S2Rta3pRbGxSV0RaUVdHaFBNVVpEUmtFd0hoY05NalF3TkRJeE1EazFPREV6V2hjTk1qVXdNakUxTURrMU9ERXpXakEyTVRRd01nWURWUVFEREN0T2NqaENibmgwY20xNU5rUmFNbFpEV2pVMWFYSmtNbVJQU25acE0wSlpVVmcyVUZob1R6RkdRMFpCTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFxNnRFVE9pRE1Cd3VTTFA3QlB6M1ZyL2VBVm96SDVSbXNhRUtMRW9tVXpPRDBKS3lVV2xPRTlBRnAxczhyUlAvTmFpRzVHYStGcGdvWkY1d3FzeXc1a21iYlJKa1MzenFPWk5mSmdad1dXbzRneExhdzE1UXJGVDJ5ZDZZREx2SzJ5WGo0VGNUSXVtQ09pUEFOMFpBWk4xNDBYMjMzWDRyM082MW1aeVVEMW0xR1FDQnU5b3drY2ZiOW9RMVpqZitYeE5tS3B4ZVBES2xrRFJDM0ZSUkdMWmV6RXM3SHBYdllJcExBS0Z5YW4xREtlc2JwY2lFeUhGci9hdkJqKzJBNGRwVFFqZ3BmcjRZc2cwYkE5dkhwT2E5V0FKWisvSTJFVGdqYmF0eHR0bFZISUZZWDZPYW5FemMvY3FIQVhFSFlNQ0pxNEViQTVjWHk3UDllUGVrK3dJREFRQUJNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUF2SXRic0RtTUhWckRKVFl6OEdwQk0vbno5bklZUE5UYW5MNjdISjU5R1NMVzF2VkhmTHdLTWp1Ylh0VzdMQktZaVlGSHpNK1RHamd2aW1mVFdzU3phSXRJRTNjVHl5VXRHMy9Pc2J0T1M0Vm1yZWsyMzJWajBZbGFDeVVyeTJQU3B1UWVBMi93eGc5Nyt2UTVOQUVYbmpoSDZSM1FsT2JNZXc1SXdOZGpsekZlMjJmNUdKaHNxUi94RVNmSVE4MURvaEZmT2JhRmswZ3ZHQ2ZaeEEva0xySUF1MHc3VVpZTGdWTzgvUDlLR0NHWDc4RTZGZm96REZlbDFLU205eC9IQThnTm0xS0NQSlhGaE1oZGJoWE5SZWhUQW5jektudlpqcC9lS2UvQkNUaFdSWHl0ZUpicVI1WHZjRzk4eEZDYTZyYjFxVEUxb21FbkZJMVR4SU1HZyJdLCJhbGciOiJSUzI1NiJ9.eyJkZXZpY2VJbmZvIjp7ImRldmljZUlkIjoiMmU1NmI3MDItNTQ3ZC00NTYwLWFmNzAtNTQzMWRlODNiMGMyIiwiZGV2aWNlTmFtZSI6InVua25vd24iLCJkZXZpY2VNb2RlbCI6InVua25vd24iLCJkZXZpY2VPc1ZlcnNpb24iOiJ1bmtub3duIiwiZGV2aWNlT3MiOiJ1bmtub3duIn0sImV4cCI6MTn4MTUyNDU4NywiaXNzIjoicmhqQVR2UDZyMmdGOVU2Nmk3dmg5Q2V5Y3FzaU16anQiLCJsb2dpblVVSUQiOiJUT0tFTl9MT0dJTl80Mzc2MV8yMDI2MDYxNTEwNTYyN18yMDI2MDYxNTE4NTYyN185ZDY2OGY1My1lNGYwLTRmOGEtOWEyZS1kM2EwYzViM2Q2YWEiLCJpYXQiOjE3ODE0OTU3ODcsImNsaWVudElkIjoiNTY5NzYiLCJjaWQiOiJkMTU2ZWNhNS1jNTNkLTQ3M2ItOTBjZC00M2NlMWVlNmNmZmYiLCJpc3Jlc2V0IjoiTiIsInNnSWRzIjpbMSwzLDEyLDgsMTQsOSwxMSw1LDM1LDI4LDMwLDUyLDU1LDgwLDgzLDg0LDEwNiwxMDksMTE5XSwidWQiOnsiZXgiOnsiY29yZVVzZXJJZCI6IjAwMDEwMTg5MjEiLCJsZXZlbCI6IkNVU1RPTUVSIiwic3ViTnVtYmVycyI6W3siYWNjb3VudHR5cGVuYW1lIjoiQ0FTSCAtIE4xIDAuMTUlIDEyJSIsImlzb3duZXIiOiJZIiwidmFsZGF0ZSI6IjA3LzEwLzIwMjQiLCJzdWJUeXBlIjoiRVFVSVRZIiwic2hvcnRhY2N0bm8iOiIwMSIsIm1ydHlwZSI6Ik4iLCJhdXRvYWR2IjoiWSIsImFjY291bnR0eXBlYnJpZWZuYW1lIjoiRmVlIDAuMTUlIE1hcmdpbiAxMiUiLCJhY2NvdW50dHlwZSI6IjAwMTEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidmFhY2N0bm9saXN0IjoiS0FGNjQ5MjgyMSIsImF1dGh0eXBlIjoiMSIsImF1dGhjb2RlIjoiQURXSU5QVVQvQ0FTSFRSQU5TL0NBU0hUUkFOU0VORERBVEUvQ09ORF9PUkRFUi9DT05GSVJNT1JERVIvREVQT1NJVC9FWFRFTkQvR1JPVVBfT1JERVIvSVNTVUVJTlBVVC9PUkRJTlBVVC9SRVNFVFBBU1MvU1RPQ0tUUkFOUy9UQUtFSU4iLCJtb2JpbGVzbXMiOiIwOTQ4NjQ5MjgyIiwiYWNjb3VudG5vIjoiMDAwMTAyMzU1NyIsIm9wZW5kYXRlIjoiMjAyNC0xMC0wN1QwMDowMDowMFoiLCJ2aWEiOiJBIiwic3ViTnVtYmVyIjoiMDAwMTAyMzU1NyIsImFjY291bnRuYW1lIjoiTmd1eeG7hW4gQW5oIFF1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MH0seyJhY2NvdW50dHlwZW5hbWUiOiJNQVJHSU4gLSBOMSAwLjE1JSAxMiUiLCJpc293bmVyIjoiWSIsInZhbGRhdGUiOiIwNy8xMC8yMDI0Iiwic3ViVHlwZSI6IkVRVUlUWSIsInNob3J0YWNjdG5vIjoiMDYiLCJtcnR5cGUiOiJUIiwiYXV0b2FkdiI6IlkiLCJhY2NvdW50dHlwZWJyaWVmbmFtZSI6IkZlZSAwLjE1JSBNYXJnaW4gMTIlIiwiYWNvdW50dHlwZSI6IjAwMTIiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6ZmFsc2UsLCJ2YWFjY3Rub2xpc3QiOiJLQUY2NDkyODI2IiwiYXV0aHR5cGUiOiIxIiwiYXV0aGNvZGUiOiJBRFdJTlBVVC9DQVNIVFJBTlMvQ0FTSFRSQU5TRU5EREFURS9DT05EX09SREVSL0NPTkZJUk1PUkRFUi9ERVBPU0lUL0VYVEVORC9HUk9VUF9PUkRFUi9JU1NVRUlOUFVUL09SRElOUFVUL1JFU0VUUEFTUy9TVE9DS1RSQU5TL1RBS0VJTiIsIm1vYmlsZXNtcyI6IjA5NDg2NDkyODIiLCJhY2NvdW50bm8iOiIwMDAxMDIzNTU4Iiwib3BlbmRhdGUiOiIyMDI0LTEwLTA3VDAwOjAwOjAwWiIsInZpYSI6IkEiLCJzdWJOdW1iZXIiOiIwMDAxMDIzNTU4IiwiYWNjb3VudG5hbWUiOiJOZ3V54buFbiBBbmggUXXDom4iLCJjdXN0b2R5Y2QiOiIwNDlDNjQ5MjgyIiwibXJjcmxpbWl0bWF4IjoxMDAwMDAwMDAwfSx7InJlYWNjdG5vIjoiMDAwMTAwMDAwMTAwMDEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidDBpbWxpbWl0IjoiMCIsInZhYWNjdG5vIjoiS0FGNjQ5MjgyOCIsInN1YlR5cGUiOiJERVJJVkFUSVZFUyIsInN0YXR1cyI6IkEiLCJkdGFTdGF0dXMiOiJBIiwiZG1BY2N0bm8iOiIwNDlDNjQ5MjgyIiwiYWZ0eXBlIjoiMDAwMyIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTciLCJjZENvbnRlbnQiOiIwMDAxMDIzNTU3IiwiY2Z0eXBlIjoiMDAwMSIsImF2bGNhc2hvbmhhbmQiOiIwIn1dfSwiaSI6NDM3NjEsInUiOiIwNDlDNjQ5MjgyIiwicklkcyI6WzFdfSwia2NVc2VySWQiOiIyMzEyNDkyZi05YWJlLTQ3M2YtYTZhMy1mZTc4ZWMwNWZmMzUiLCJmbGV4QWNjb3VudE51bWJlciI6IjA0OUM2NDkyODIiLCJjdXN0b21Vc2VybmFtZSI6IjA0OWM2NDkyODIifQ.baf5Zww3juu9xcMW_w3QODnYUn5mBJZOFU9aUUdKO2Q1gFtWtUTdSzOd0Pb0V95xWaDWtAZo6z6rViNvLPaeut1x8XF7twjE3l3KaCbJh5MNf4J5yGkSyHV55hrFPXZjJ5ppZqLXZZZYMqBLUVv8eLi_gAjFUwmWuy3ALfAWVNLBBRkFRmcYhfxt92KcE2WHttsOFInJ0JRSQTXhejXQQE5-y40TQUf22XWOHezx1hnw5jYqBq6GQTRwlO_rPtANaVlYL3VkDOTY_VH7WJwMws_t4HSNvgzutClGQ-Db3s4757OiN4Y-4qIHsoOWyrHfGx7qIL9UCpPP1lwidRQpng"

# Mã chứng khoán muốn theo dõi
SYMBOL_TO_WATCH = "CTD"

# Tọa độ máy chủ FiinTrade
NEGOTIATE_URL = "https://wl-realtime.fiintrade.vn/RealtimeHub/negotiate?negotiateVersion=1"
WS_BASE_URL = "wss://wl-realtime.fiintrade.vn/RealtimeHub"

# Giấy tờ tùy thân (Headers)
custom_headers = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin: https://banggia.kafi.vn",
    "Accept-Language: vi-VN,vi;q=0.9",
    f"Authorization: Bearer {JWT_TOKEN}"
]

# ==============================================================================
# 2. CÁC HÀM XỬ LÝ NGHIỆP VỤ (GIỮ NGUYÊN GỐC CỦA BẠN)
# ==============================================================================

def get_fresh_connection_id():
    """Hàm tự động gọi POST lên API để lấy Connection ID mới nhất"""
    print("🎫 Đang mang Thẻ VIP đến hệ thống FiinTrade xin vé (Connection ID)...")
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://banggia.kafi.vn"
    }
    try:
        response = requests.post(NEGOTIATE_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            conn_id = data.get("connectionId") or data.get("connectionToken")
            print(f"✅ Đã nhận được vé qua cửa: {conn_id}")
            return conn_id
        else:
            print(f"❌ Xin vé thất bại (Mã {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Lỗi khi gọi đàm phán HTTP: {e}")
        return None

def subscribe_to_stock(ws, symbol):
    time.sleep(1) 
    try:
        # Đăng ký kênh Tick (Đã có bản đồ Index chuẩn)
        payload_tick = {
            "arguments": [f"Realtime.Tick.{symbol}"],
            "invocationId": "45",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_tick) + chr(30))
        
        # GIĂNG LƯỚI TÌM KÊNH SỔ LỆNH: Đăng ký thử các tên miền phổ biến nhất của FiinTrade
        potential_quote_channels = ["Quote", "BidAsk", "Depth", "MarketDepth", "OrderBook"]
        for idx, channel in enumerate(potential_quote_channels):
            payload_quote = {
                "arguments": [f"Realtime.{channel}.{symbol}"],
                "invocationId": str(50 + idx),
                "target": "JoinGroup",
                "type": 1
            }
            ws.send(json.dumps(payload_quote) + chr(30))

        print(f"🎯 Đã đăng ký kênh Khớp lệnh và giăng lưới Sổ lệnh cho {symbol}!")
        print("="*60)
    except Exception as e:
        pass

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
                    
                    if not raw_data_list or code != SYMBOL_TO_WATCH:
                        continue
                        
                    raw_string = raw_data_list[0]
                    parts = raw_string.split("|")
                    
                    # 1. XỬ LÝ KÊNH TICK (ĐÃ CÓ BẢN ĐỒ CHUẨN)
                    if "Tick" in str(channel_name):
                        if len(parts) >= 18:
                            total_vol = parts[0]
                            match_price = parts[13]
                            match_vol = parts[17]
                            price_change = parts[15]
                            print(f"🔥 [KHỚP LỆNH] Giá: {match_price} ({price_change}đ) | KL khớp: {match_vol} | Tổng KL: {total_vol}")
                    
                    # 2. XỬ LÝ LƯỚI SỔ LỆNH (TÌM KÊNH CHỨA BƯỚC GIÁ)
                    elif any(c in str(channel_name) for c in ["Quote", "BidAsk", "Depth", "OrderBook"]):
                        print(f"\n✅ [BẮT ĐƯỢC SỔ LỆNH] Tên kênh chính xác là: {channel_name}")
                        print(f"Chuỗi dữ liệu: {raw_string}")
                        print("-" * 60)

    except Exception as e: 
        pass

# ==============================================================================
# 3. SỰ KIỆN WEBSOCKET CORÊ (ĐÃ FIX LỖI RECONNECT VÀ HIỂN THỊ SỔ LỆNH CHI TIẾT)
# ==============================================================================

def on_message(ws, message):
    try:
        # Tách các gói tin bằng ký tự phân cách chr(30) của SignalR
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': 
                continue # Bỏ qua gói tin Ping giữ mạng của server
            
            if msg == '{}':
                print("🎉 HANDSHAKE THÀNH CÔNG!")
                threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL_TO_WATCH)).start()
                continue

            data = json.loads(msg)
            
            # 1. BẮT DỮ LIỆU SNAPSHOT (GIÁ CHỐT)
            if data.get("type") == 3 and data.get("invocationId") == "41":
                result = data.get("result")
                if result and isinstance(result, list):
                    print(f"\n📸 SNAPSHOT ĐẦU PHIÊN | Mã: {result[5]} | Giá snapshot: {result[12]} | Tổng Vol: {result[0]}")
                continue
            
            # 2. BỘ LỌC THÁM TỬ - QUÉT TOÀN BỘ LUỒNG DỮ LIỆU TRONG PHIÊN
            if data.get("type") == 1 and data.get("target") == "ReceiveMessage":
                args = data.get("arguments", [])
                if args and isinstance(args, list):
                    item = args[0]
                    
                    # 💡 Mẹo cốt lõi: Lấy cả 'chanel' (1 chữ n) hoặc 'channel' (2 chữ n) để chống server đổi luật
                    channel_name = item.get("chanel") or item.get("channel") or ""
                    code = item.get("code", "")
                    raw_data_list = item.get("data", [])
                    
                    if not raw_data_list:
                        continue
                        
                    raw_string = raw_data_list[0]
                    parts = raw_string.split("|")
                    
                    # A. BÓC TÁCH LUỒNG TICK (KHỚP LỆNH LIÊN TỤC)
                    if "Tick" in str(channel_name):
                        if len(parts) > 10:
                            price = parts[10]
                            vol = parts[15]
                            print(f"🔥 TICK Khớp Lệnh | Mã: {code:4} | Giá: {price} | Khối lượng: {vol}")
                    
                    # B. BÓC TÁCH LUỒNG TICKER (SỔ LỆNH BID/ASK) -> Dùng từ khóa 'in' để quét cạn
                    elif "Ticker" in str(channel_name):
                        print(f"📊 PHÁT HIỆN SỔ LỆNH (Ticker) | Mã: {code:4}")
                        print(f"   -> Chuỗi thô: {raw_string[:100]}...") # In hẳn 100 ký tự đầu để xem mảng giá mua/bán
                        
                    # C. NẾU CÓ LUỒNG DỮ LIỆU LẠ NÀO KHÁC ĐỔ VỀ
                    else:
                        print(f"📡 Kênh lạ xuất hiện [{channel_name}] | Mã: {code} | Data: {raw_string[:50]}")

    except Exception as e: 
        # Bật dòng này lên để nếu code có gõ nhầm dòng nào thì nó báo ngay lập tức
        print(f"❌ Lỗi xử lý dữ liệu: {e}")

def on_error(ws, error): 
    print(f"❌ Lỗi WebSocket: {error}")

def on_close(ws, close_status_code, close_msg): 
    print(f"🔌 Mất kết nối cổng mạng (Mã: {close_status_code}).")

def on_open(ws):
    print("🚀 Kết nối cáp thành công! Đang gửi thư xác nhận (Handshake)...")
    ws.send('{"protocol":"json","version":1}' + chr(30))

# ==============================================================================
# 4. CHẠY CHƯƠNG TRÌNH & ĐỘNG CƠ TỰ PHỤC HỒI (AUTO-RECONNECT + HEARTBEAT)
# ==============================================================================

def start_trading_bot():
    while True:
        # BƯỚC 1: XIN VÉ TỪ FIINTRADE (Nằm trong loop để luôn làm mới ID khi Reconnect)
        fresh_id = get_fresh_connection_id()
        
        if fresh_id:
            # BƯỚC 2: RÁP VÉ VÀO ĐƯỜNG LINK WEB-SOCKET
            final_ws_url = f"{WS_BASE_URL}?id={fresh_id}"
            print(f"🔗 Mở cổng WebSocket tới: {final_ws_url}")
            
            websocket.enableTrace(False)
            
            # BƯỚC 3: MỞ KẾT NỐI VÀ LẮNG NGHE
            ws = websocket.WebSocketApp(
                final_ws_url, 
                header=custom_headers, 
                on_open=on_open, 
                on_message=on_message, 
                on_error=on_error, 
                on_close=on_close
            )
            
            # 🌟 ĐÂY CHÍNH LÀ THUỐC TRỊ LỖI 10054:
            # Cứ mỗi 15 giây, thư viện tự động Ping qua lại với server để giữ kết nối sống (Keep-Alive)
            ws.run_forever(ping_interval=15, ping_timeout=10)
        
        # Nếu bị server đá hoặc mất mạng, chương trình sẽ không crash rơi tự do nữa
        print("⏳ Hệ thống tự động Reconnect lại sau 5 giây...")
        time.sleep(5)

if __name__ == "__main__":
    start_trading_bot()