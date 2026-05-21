import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH ---
SYMBOL = "CTD"
EXCHANGE = "HOSE"
START_DATE_STR = "01/01/2020"
END_DATE_STR = datetime.now().strftime("%d/%m/%Y")

# URL MỚI CHUẨN XÁC TỪ ẢNH F12 CỦA BẠN
API_URL = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx" 

# Cập nhật Header y hệt trình duyệt Edge/Chrome của bạn
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    "Referer": f"https://cafef.vn/du-lieu/lich-su-giao-dich/hose/{SYMBOL.lower()}-3.chn",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def get_data_by_range(start_date, end_date):
    """Gửi request GET với bộ tham số (Query String) chuẩn"""
    params = {
        "Symbol": SYMBOL,
        "Exchange": EXCHANGE,
        "StartDate": start_date,
        "EndDate": end_date,
        "PageIndex": 1,
        "PageSize": 100 # Vẫn để 100 để lấy trọn tháng
    }
    
    try:
        # Quay lại dùng GET và params như ảnh F12
        response = requests.get(API_URL, params=params, headers=headers)
        
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("Success"):
                return json_data.get("Data", {}).get("Data", [])
        return []
    except Exception as e:
        print(f"Lỗi: {e}")
        return []

# --- CHƯƠNG TRÌNH CHÍNH ---
all_results = []
current_start = datetime.strptime(START_DATE_STR, "%d/%m/%Y")
final_end = datetime.strptime(END_DATE_STR, "%d/%m/%Y")

print(f"Bắt đầu thu thập dữ liệu {SYMBOL} từ {START_DATE_STR}...")

# Dùng requests.Session() để tự động giữ lại Cookie nếu CafeF cấp
session = requests.Session()

while current_start <= final_end:
    current_end = current_start + timedelta(days=30)
    if current_end > final_end:
        current_end = final_end
        
    s_str = current_start.strftime("%d/%m/%Y")
    e_str = current_end.strftime("%d/%m/%Y")
    
    print(f"Đang lấy: {s_str} -> {e_str}", end=" ")
    
    data_chunk = get_data_by_range(s_str, e_str)
    if data_chunk:
        all_results.extend(data_chunk)
        print(f"... OK ({len(data_chunk)} dòng)")
    else:
        print("... Không có dữ liệu")
        
    time.sleep(2) 
    
    current_start = current_end + timedelta(days=1)

# --- XỬ LÝ VÀ LƯU DỮ LIỆU ---
if all_results:
    df = pd.DataFrame(all_results)
    
    # Lọc trùng và sắp xếp
    df.drop_duplicates(subset=['Ngay'], inplace=True)
    df['Ngay_Date'] = pd.to_datetime(df['Ngay'], format="%d/%m/%Y")
    df.sort_values(by='Ngay_Date', ascending=False, inplace=True)
    df.drop(columns=['Ngay_Date'], inplace=True)
    
    file_name = f"GDKN_{SYMBOL}.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n🎉 THÀNH CÔNG! Đã lưu {len(df)} phiên giao dịch vào file: {file_name}")
else:
    print("\nThất bại. Nếu vẫn không được, chúng ta sẽ phải copy tay cái chuỗi Cookie dài ngoằng kia vào code.")