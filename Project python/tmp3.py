import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH ---
SYMBOL = "CTD"
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime.now()
CHUNK_DAYS = 90 # Chia nhỏ 3 tháng/lần quét để server không bị ngợp

API_URL = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": f"https://cafef.vn/du-lieu/lich-su-giao-dich/hose/{SYMBOL.lower()}-3.chn",
    "X-Requested-With": "XMLHttpRequest"
}

all_results = []

print("BẮT ĐẦU QUÉT DỮ LIỆU THỰC SỰ...")

with requests.Session() as session:
    session.headers.update(HEADERS)
    
    current_start = START_DATE
    
    while current_start <= END_DATE:
        current_end = current_start + timedelta(days=CHUNK_DAYS)
        if current_end > END_DATE:
            current_end = END_DATE
            
        # 🔑 ĐIỂM CỐT LÕI: Gửi lên Server theo chuẩn Mỹ (Tháng/Ngày/Năm)
        api_start_str = current_start.strftime("%m/%d/%Y") 
        api_end_str = current_end.strftime("%m/%d/%Y")
        
        # In ra màn hình theo chuẩn Việt Nam cho dễ nhìn
        print_start = current_start.strftime("%d/%m/%Y")
        print_end = current_end.strftime("%d/%m/%Y")
        
        print(f"Đang lấy: {print_start} -> {print_end}...", end=" ", flush=True)
        
        page = 1
        chunk_data_count = 0
        
        while True:
            params = {
                "Symbol": SYMBOL,
                "Exchange": "HOSE",
                "StartDate": api_start_str, # Ép chuẩn MM/dd/yyyy
                "EndDate": api_end_str,     # Ép chuẩn MM/dd/yyyy
                "PageIndex": page,
                "PageSize": 100 
            }
            
            try:
                response = session.get(API_URL, params=params, timeout=10)
                if response.status_code == 200:
                    json_data = response.json()
                    data_page = json_data.get("Data", {}).get("Data", [])
                    
                    if not data_page:
                        break # Hết dữ liệu của cục 3 tháng này -> Chuyển cục tiếp theo
                        
                    all_results.extend(data_page)
                    chunk_data_count += len(data_page)
                    page += 1
                    time.sleep(1.5) # Dừng 0.1s giữa các trang
                else:
                    break
            except Exception as e:
                print(f"Lỗi mạng: {e}", end=" ")
                break
                
        print(f"OK ({chunk_data_count} dòng)")
        
        # Tiến lên mốc thời gian tiếp theo
        current_start = current_end + timedelta(days=1)

# --- LƯU FILE ---
if all_results:
    df = pd.DataFrame(all_results)
    # Loại bỏ các dòng trùng lặp (nếu có ngày bị gối lên nhau)
    df.drop_duplicates(subset=['Ngay'], inplace=True)
    
    # Sắp xếp lại dữ liệu theo thời gian thực (Từ cũ đến mới)
    df['Ngay_Date'] = pd.to_datetime(df['Ngay'], format='%d/%m/%Y')
    df.sort_values('Ngay_Date', ascending=True, inplace=True)
    df.drop(columns=['Ngay_Date'], inplace=True)
    
    file_name = f"GDKN_{SYMBOL}_PERFECT.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n📊 HOÀN THÀNH XUẤT SẮC! Tổng cộng thu được {len(df)} phiên giao dịch (Đúng dữ liệu thực tế).")
    print(f"📁 Đã lưu file chuẩn tại: {file_name}")
else:
    print("\n❌ Không lấy được dữ liệu.")