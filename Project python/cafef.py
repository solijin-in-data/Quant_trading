import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH ---
SYMBOL = "CTD"
EXCHANGE = "HOSE"
START_DATE_STR = "01/01/2020"
END_DATE_STR = datetime.now().strftime("%d/%m/%Y")
# URL API bạn tìm thấy trong tab Network
API_URL = "https://cafef.vn/du-lieu/GDKhoiNgoai.ashx" 

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": f"https://cafef.vn/du-lieu/lich-su-giao-dich/hose/{SYMBOL}-3.chn"
}

def get_data_by_range(start_date, end_date):
    """Gửi request lấy dữ liệu trong 1 khoảng thời gian"""
    params = {
        "Symbol": SYMBOL,
        "Exchange": EXCHANGE,
        "StartDate": start_date,
        "EndDate": end_date,
        "PageIndex": 1,
        "PageSize": 100 # Để 100 để lấy hết ~22 phiên của 1 tháng trong 1 lần gọi
    }
    
    try:
        response = requests.get(API_URL, params=params, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("Success"):
                # Dữ liệu nằm trong json_data['Data']['Data'] tùy theo cấu trúc thực tế bạn thấy
                # Ở đây mình giả định cấu trúc trả về là list các object
                return json_data.get("Data", {}).get("Data", [])
        return []
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu {start_date} - {end_date}: {e}")
        return []

# --- CHƯƠNG TRÌNH CHÍNH ---
all_results = []
current_start = datetime.strptime(START_DATE_STR, "%d/%m/%Y")
final_end = datetime.strptime(END_DATE_STR, "%d/%m/%Y")

print(f"Bắt đầu thu thập dữ liệu {SYMBOL} từ {START_DATE_STR}...")

while current_start < final_end:
    # Tính ngày kết thúc của đợt này (cộng thêm 30 ngày)
    current_end = current_start + timedelta(days=30)
    if current_end > final_end:
        current_end = final_end
        
    s_str = current_start.strftime("%d/%m/%Y")
    e_str = current_end.strftime("%d/%m/%Y")
    
    print(f"Đang lấy dữ liệu từ {s_str} đến {e_str}...")
    
    data_chunk = get_data_by_range(s_str, e_str)
    if data_chunk:
        all_results.extend(data_chunk)
        print(f" -> Lấy được {len(data_chunk)} dòng.")
    else:
        print(" -> Không có dữ liệu hoặc lỗi.")
        
    # Nghỉ 1 chút để tránh bị server chặn (Rate limit)
    time.sleep(1)
    
    # Nhảy tới kỳ tiếp theo (ngày tiếp theo sau ngày kết thúc cũ)
    current_start = current_end + timedelta(days=1)

# --- LƯU DỮ LIỆU ---
if all_results:
    df = pd.DataFrame(all_results)
    file_name = f"GDKN_{SYMBOL}_2020_Present.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\nXong! Đã lưu {len(all_results)} dòng vào file: {file_name}")
else:
    print("\nKhông thu thập được dữ liệu nào.")