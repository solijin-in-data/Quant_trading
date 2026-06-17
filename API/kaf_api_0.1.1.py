import requests
import websocket
import json
import time
import threading

# ==============================================================================
# 1. CẤU HÌNH THÔNG SỐ CƠ BẢN
# ==============================================================================

# 🚨 CẢNH BÁO: CHẠY TEST XONG NHỚ LÊN WEB KAFI BẤM ĐĂNG XUẤT ĐỂ HỦY TOKEN NÀY NHÉ!
JWT_TOKEN = ""

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