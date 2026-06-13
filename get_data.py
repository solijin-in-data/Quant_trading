import requests
import pandas as pd
from datetime import datetime

def lay_lich_su_gia_thuan(symbol="CTD", so_ngay=30):
    """
    Hàm lấy lịch sử giá (OHLCV) thuần túy không phụ thuộc vào thư viện vnstock
    """
    symbol = symbol.upper()
    print(f"🚀 [HỆ THỐNG TỰ CHẾ] Đang tải lịch sử giá mã {symbol} trực tiếp từ cổng mở...")
    
    # Sử dụng API đồ thị kỹ thuật (Candlestick) - Nguồn này cực kỳ ổn định
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlc/candles"
    
    # Tính toán mốc thời gian
    to_date = int(datetime.now().timestamp())
    from_date = to_date - (so_ngay * 24 * 3600)
    
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "resolution": "1D" # Nến ngày (Có thể đổi thành '1' nếu muốn lấy nến 1 phút)
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            raw_data = response.json()
            
            # Chuyển đổi cấu trúc mảng của Entrade thành DataFrame
            # Cấu trúc trả về thường là danh sách các mảng: [t, o, h, l, c, v]
            if isinstance(raw_data, list) and len(raw_data) > 0:
                df = pd.DataFrame(raw_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
                
                # Chuyển đổi timestamp thành ngày tháng đọc được
                df['Time'] = pd.to_datetime(df['Time'], unit='s').dt.date
                
                print("✅ TẢI DỮ LIỆU THÀNH CÔNG!")
                print("=" * 60)
                print(df.tail(10)) # In 10 ngày giao dịch gần nhất
                print("=" * 60)
                return df
            else:
                print("⚠️ Dữ liệu trả về trống hoặc sai cấu trúc.")
        else:
            print(f"❌ Lỗi kết nối API. Mã lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Lỗi hệ thống phát sinh: {e}")
    return None

if __name__ == "__main__":
    lay_lich_su_gia_thuan("CTD", so_ngay=20)