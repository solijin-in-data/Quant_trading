import requests
import websocket
import json
import time
import threading

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ CƠ BẢN
# ==============================================================================

# 🚨 CẢNH BÁO: CHẠY TEST XONG NHỚ LÊN WEB KAFI BẤM ĐĂNG XUẤT ĐỂ HỦY TOKEN NÀY NHÉ!
JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJ4NWMiOlsiTUlJQzZqQ0NBZEtnQXdJQkFnSUdBWThBRjRoUU1BMEdDU3FHU0liM0RRRUJDd1VBTURZeE5EQXlCZ05WQkFNTUswNXlPRUp1ZUhSeWJYazJSRm95VmtOYU5UVnBjbVF5WkU5S2Rta3pRbGxSV0RaUVdHaFBNVVpEUmtFd0hoY05NalF3TkRJeE1EazFPREV6V2hjTk1qVXdNakUxTURrMU9ERXpXakEyTVRRd01nWURWUVFEREN0T2NqaENibmgwY20xNU5rUmFNbFpEV2pVMWFYSmtNbVJQU25acE0wSlpVVmcyVUZob1R6RkdRMFpCTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFxNnRFVE9pRE1Cd3VTTFA3QlB6M1ZyL2VBVm96SDVSbXNhRUtMRW9tVXpPRDBKS3lVV2xPRTlBRnAxczhyUlAvTmFpRzVHYStGcGdvWkY1d3FzeXc1a21iYlJKa1MzenFPWk5mSmdad1dXbzRneExhdzE1UXJGVDJ5ZDZZREx2SzJ5WGo0VGNUSXVtQ09pUEFOMFpBWk4xNDBYMjMzWDRyM082MW1aeVVEMW0xR1FDQnU5b3drY2ZiOW9RMVpqZitYeE5tS3B4ZVBES2xrRFJDM0ZSUkdMWmV6RXM3SHBYdllJcExBS0Z5YW4xREtlc2JwY2lFeUhGci9hdkJqKzJBNGRwVFFqZ3BmcjRZc2cwYkE5dkhwT2E5V0FKWisvSTJFVGdqYmF0eHR0bFZISUZZWDZPYW5FemMvY3FIQVhFSFlNQ0pxNEViQTVjWHk3UDllUGVrK3dJREFRQUJNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUF2SXRic0RtTUhWckRKVFl6OEdwQk0vbno5bklZUE5UYW5MNjdISjU5R1NMVzF2VkhmTHdLTWp1Ylh0VzdMQktZaVlGSHpNK1RHamd2aW1mVFdzU3phSXRJRTNjVHl5VXRHMy9Pc2J0T1M0Vm1yZWsyMzJWajBZbGFDeVVyeTJQU3B1UWVBMi93eGc5Nyt2UTVOQUVYbmpoSDZSM1FsT2JNZXc1SXdOZGpsekZlMjJmNUdKaHNxUi94RVNmSVE4MURvaEZmT2JhRmswZ3ZHQ2ZaeEEva0xySUF1MHc3VVpZTGdWTzgvUDlLR0NHWDc4RTZGZm96REZlbDFLU205eC9IQThnTm0xS0NQSlhGaE1oZGJoWE5SZWhUQW5jektudlpqcC9lS2UvQkNUaFdSWHl0ZUpicVI1WHZjRzk4eEZDYTZyYjFxVEUxb21FbkZJMVR4SU1HZyJdLCJhbGciOiJSUzI1NiJ9.eyJkZXZpY2VJbmZvIjp7ImRldmljZUlkIjoiMmU1NmI3MDItNTQ3ZC00NTYwLWFmNzAtNTQzMWRlODNiMGMyIiwiZGV2aWNlTmFtZSI6InVua25vd24iLCJkZXZpY2VNb2RlbCI6InVua25vd24iLCJkZXZpY2VPc1ZlcnNpb24iOiJ1bmtub3duIiwiZGV2aWNlT3MiOiJ1bmtub3duIn0sImV4cCI6MTc4MTUyNDU4NywiaXNzIjoicmhqQVR2UDZyMmdGOVU2Nmk3dmc5Q2V5Y3FzaU16anQiLCJsb2dpblVVSUQiOiJUT0tFTl9MT0dJTl80Mzc2MV8yMDI2MDYxNTEwNTYyN18yMDI2MDYxNTE4NTYyN185ZDY2OGY1My1lNGYwLTRmOGEtOWEyZS1kM2EwYzViM2Q2YWEiLCJpYXQiOjE3ODE0OTU3ODcsImNsaWVudElkIjoiNTY5NzYiLCJjaWQiOiJkMTU2ZWNhNS1jNTNkLTQ3M2ItOTBjZC00M2NlMWVlNmNmZmYiLCJpc3Jlc2V0IjoiTiIsInNnSWRzIjpbMSwzLDEyLDgsMTQsOSwxMSw1LDM1LDI4LDMwLDUyLDU1LDgwLDgzLDg0LDEwNiwxMDksMTE5XSwidWQiOnsiZXgiOnsiY29yZVVzZXJJZCI6IjAwMDEwMTg5MjEiLCJsZXZlbCI6IkNVU1RPTUVSIiwic3ViTnVtYmVycyI6W3siYWNjb3VudHR5cGVuYW1lIjoiQ0FTSCAtIE4xIDAuMTUlIDEyJSIsImlzb3duZXIiOiJZIiwidmFsZGF0ZSI6IjA3LzEwLzIwMjQiLCJzdWJUeXBlIjoiRVFVSVRZIiwic2hvcnRhY2N0bm8iOiIwMSIsIm1ydHlwZSI6Ik4iLCJhdXRvYWR2IjoiWSIsImFjY291bnR0eXBlYnJpZWZuYW1lIjoiRmVlIDAuMTUlIE1hcmdpbiAxMiUiLCJhY2NvdW50dHlwZSI6IjAwMTEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidmFhY2N0bm9saXN0IjoiS0FGNjQ5MjgyMSIsImF1dGh0eXBlIjoiMSIsImF1dGhjb2RlIjoiQURXSU5QVVQvQ0FTSFRSQU5TL0NBU0hUUkFOU0VORERBVEUvQ09ORF9PUkRFUi9DT05GSVJNT1JERVIvREVQT1NJVC9FWFRFTkQvR1JPVVBfT1JERVIvSVNTVUVJTlBVVC9PUkRJTlBVVC9SRVNFVFBBU1MvU1RPQ0tUUkFOUy9UQUtFSU4iLCJtb2JpbGVzbXMiOiIwOTQ4NjQ5MjgyIiwiYWNjb3VudG5vIjoiMDAwMTAyMzU1NyIsIm9wZW5kYXRlIjoiMjAyNC0xMC0wN1QwMDowMDowMFoiLCJ2aWEiOiJBIiwic3ViTnVtYmVyIjoiMDAwMTAyMzU1NyIsImFjY291bnRuYW1lIjoiTmd1eeG7hW4gQW5oIFF1w6JuIiwiY3VzdG9keWNkIjoiMDQ5QzY0OTI4MiIsIm1yY3JsaW1pdG1heCI6MH0seyJhY2NvdW50dHlwZW5hbWUiOiJNQVJHSU4gLSBOMSAwLjE1JSAxMiUiLCJpc293bmVyIjoiWSIsInZhbGRhdGUiOiIwNy8xMC8yMDI0Iiwic3ViVHlwZSI6IkVRVUlUWSIsInNob3J0YWNjdG5vIjoiMDYiLCJtcnR5cGUiOiJUIiwiYXV0b2FkdiI6IlkiLCJhY2NvdW50dHlwZWJyaWVmbmFtZSI6IkZlZSAwLjE1JSBNYXJnaW4gMTIlIiwiYWNjb3VudHR5cGUiOiIwMDEyIiwiYWNjb3VudE51bWJlciI6IjA0OUM2NDkyODIiLCJpc0RlZmF1bHQiOmZhbHNlLCJ2YWFjY3Rub2xpc3QiOiJLQUY2NDkyODI2IiwiYXV0aHR5cGUiOiIxIiwiYXV0aGNvZGUiOiJBRFdJTlBVVC9DQVNIVFJBTlMvQ0FTSFRSQU5TRU5EREFURS9DT05EX09SREVSL0NPTkZJUk1PUkRFUi9ERVBPU0lUL0VYVEVORC9HUk9VUF9PUkRFUi9JU1NVRUlOUFVUL09SRElOUFVUL1JFU0VUUEFTUy9TVE9DS1RSQU5TL1RBS0VJTiIsIm1vYmlsZXNtcyI6IjA5NDg2NDkyODIiLCJhY2NvdW50bm8iOiIwMDAxMDIzNTU4Iiwib3BlbmRhdGUiOiIyMDI0LTEwLTA3VDAwOjAwOjAwWiIsInZpYSI6IkEiLCJzdWJOdW1iZXIiOiIwMDAxMDIzNTU4IiwiYWNjb3VudG5hbWUiOiJOZ3V54buFbiBBbmggUXXDom4iLCJjdXN0b2R5Y2QiOiIwNDlDNjQ5MjgyIiwibXJjcmxpbWl0bWF4IjoxMDAwMDAwMDAwfSx7InJlYWNjdG5vIjoiMDAwMTAwMDAwMTAwMDEiLCJhY2NvdW50TnVtYmVyIjoiMDQ5QzY0OTI4MiIsImlzRGVmYXVsdCI6dHJ1ZSwidDBpbWxpbWl0IjoiMCIsInZhYWNjdG5vIjoiS0FGNjQ5MjgyOCIsInN1YlR5cGUiOiJERVJJVkFUSVZFUyIsInN0YXR1cyI6IkEiLCJkdGFTdGF0dXMiOiJBIiwiZG1BY2N0bm8iOiIwNDlDNjQ5MjgyIiwiYWZ0eXBlIjoiMDAwMyIsInN1Yk51bWJlciI6IjAwMDEwMjM1NTciLCJjZENvbnRlbnQiOiIwMDAxMDIzNTU3IiwiY2Z0eXBlIjoiMDAwMSIsImF2bGNhc2hvbmhhbmQiOiIwIn1dfSwiaSI6NDM3NjEsInUiOiIwNDlDNjQ5MjgyIiwicklkcyI6WzFdfSwia2NVc2VySWQiOiIyMzEyNDkyZi05YWJlLTQ3M2YtYTZhMy1mZTc4ZWMwNWZmMzUiLCJmbGV4QWNjb3VudE51bWJlciI6IjA0OUM2NDkyODIiLCJjdXN0b21Vc2VybmFtZSI6IjA0OWM2NDkyODIifQ.baf5Zww3juu9xcMW_w3QODnYUn5mBJZOFU9aUUdKO2Q1gFtWtUTdSzOd0Pb0V95xWaDWtAZo6z6rViNvLPaeut1x8XF7twjE3l3KaCbJh5MNf4J5yGkSyHV55hrFPXZjJ5ppZqLXZZZYMqBLUVv8eLi_gAjFUwmWuy3ALfAWVNLBBRkFRmcYhfxt92KcE2WHttsOFInJ0JRSQTXhejXQQE5-y40TQUf22XWOHezx1hnw5jYqBq6GQTRwlO_rPtANaVlYL3VkDOTY_VH7WJwMws_t4HSNvgzutClGQ-Db3s4757OiN4Y-4qIHsoOWyrHfGx7qIL9UCpPP1lwidRQpng"

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
# 2. CÁC HÀM XỬ LÝ CHÍNH
# ==============================================================================

def get_fresh_connection_id():
    """Hàm tự động gọi POST lên API để lấy Connection ID mới nhất"""
    print("🎫 Đang mang Thẻ VIP đến hệ thống FiinTrade xin vé (Connection ID)...")
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://banggia.kafi.vn"
    }
    
    response = requests.post(NEGOTIATE_URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        conn_id = data.get("connectionId") or data.get("connectionToken")
        print(f"✅ Đã nhận được vé qua cửa: {conn_id}")
        return conn_id
    else:
        print(f"❌ Xin vé thất bại (Mã {response.status_code}): {response.text}")
        return None

def subscribe_to_stock(ws, symbol):
    """Hàm gửi các lệnh xin dữ liệu và đăng ký theo dõi phòng VIP"""
    time.sleep(1) # Nghỉ 1 nhịp để máy chủ chuẩn bị
    
    try:
        # LỆNH 1: XIN DỮ LIỆU CHỐT PHIÊN (SNAPSHOT) NGAY LẬP TỨC
        payload_snapshot = {
            "arguments": [symbol, "Tick", True],
            "invocationId": "41",
            "target": "SubscribePullMethod",
            "type": 1
        }
        ws.send(json.dumps(payload_snapshot) + chr(30))
        print(f"✅ Đã yêu cầu lấy giá chốt phiên (Snapshot) cho {symbol}")

        # LỆNH 2: XIN THEO DÕI KHỚP LỆNH TRỰC TIẾP (TICK)
        payload_tick = {
            "arguments": [f"Realtime.Tick.{symbol}"],
            "invocationId": "45",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_tick) + chr(30))
        print(f"✅ Đã đăng ký theo dõi TICK cho {symbol} (Sáng mai 9h sẽ tự nhảy)")

        # LỆNH 3: XIN THEO DÕI BƯỚC GIÁ MUA/BÁN (TICKER)
        payload_ticker = {
            "arguments": [f"Realtime.Ticker.{symbol}"],
            "invocationId": "46",
            "target": "JoinGroup",
            "type": 1
        }
        ws.send(json.dumps(payload_ticker) + chr(30))
        print(f"✅ Đã đăng ký theo dõi SỔ LỆNH cho {symbol}")
        print("⏳ Đang chờ máy chủ phản hồi...\n" + "-"*50)
        
    except Exception as e:
        print(f"❌ Lỗi khi Subscribe: {e}")

# ==============================================================================
# 3. SỰ KIỆN WEBSOCKET
# ==============================================================================

def on_message(ws, message):
    try:
        # Tách các gói tin bằng ký tự phân cách chr(30) của SignalR
        raw_messages = message.split(chr(30))
        for msg in raw_messages:
            if not msg or msg == '{"type":6}': 
                # Bỏ qua Ping của máy chủ
                continue
            
            # Nếu nhận được {} => Handshake thành công
            if msg == '{}':
                print("🎉 HANDSHAKE THÀNH CÔNG!")
                # Mở luồng phụ để gửi lệnh đăng ký theo dõi cổ phiếu
                threading.Thread(target=subscribe_to_stock, args=(ws, SYMBOL_TO_WATCH)).start()
                return

            # Xử lý luồng dữ liệu trả về
            data = json.loads(msg)
            
            # [MỚI] BẮT DỮ LIỆU SNAPSHOT (CHỐT PHIÊN)
            if data.get("type") == 3 and data.get("invocationId") == "41":
                result = data.get("result")
                if result and isinstance(result, list):
                    # Dựa theo format: result[5] là mã, result[12] là giá, result[0] là Vol
                    print(f"\n📸 SNAPSHOT CUỐI NGÀY | Mã: {result[5]} | Giá: {result[12]} | Tổng Vol: {result[0]}")
            
            # Bắt dữ liệu Push từ máy chủ khi trong phiên (ReceiveMessage)
            if data.get("type") == 1 and data.get("target") == "ReceiveMessage":
                args = data.get("arguments", [])
                if args:
                    # Bóc tách luồng Tick (Lệnh khớp liên tục)
                    if args[0].get("chanel") == f"Realtime.Tick.{SYMBOL_TO_WATCH}" or args[0].get("chanel") == "Realtime.Tick":
                        code = args[0].get("code")
                        parts = args[0]["data"][0].split("|")
                        if len(parts) > 10:
                            price = parts[10]
                            vol = parts[15]
                            print(f"🔥 TICK Khớp Lệnh | Mã: {code:4} | Giá: {price} | Khối lượng: {vol}")
                            
                    # Bóc tách luồng Ticker (Bước giá Mua/Bán)
                    elif args[0].get("chanel") == f"Realtime.Ticker.{SYMBOL_TO_WATCH}" or args[0].get("chanel") == "Realtime.Ticker":
                        code = args[0].get("code")
                        parts = args[0]["data"][0].split("|")
                        print(f"📊 Sổ Lệnh (Bid/Ask) | Mã: {code:4} | Cập nhật mới: {parts[0][:15]}...")
                 
    except Exception as e: 
        pass

def on_error(ws, error): 
    print(f"❌ Lỗi WebSocket: {error}")

def on_close(ws, close_status_code, close_msg): 
    print(f"🔌 Ngắt kết nối (Mã: {close_status_code}).")

def on_open(ws):
    print("🚀 Kết nối cáp thành công! Đang gửi thư xác nhận (Handshake)...")
    ws.send('{"protocol":"json","version":1}' + chr(30))

# ==============================================================================
# 4. CHẠY CHƯƠNG TRÌNH
# ==============================================================================

if __name__ == "__main__":
    # BƯỚC 1: XIN VÉ TỪ FIINTRADE
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
        ws.keep_running = True
        ws.run_forever()