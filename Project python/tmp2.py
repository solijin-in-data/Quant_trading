import requests
import pandas as pd
from datetime import datetime
import time

# --- CẤU HÌNH ---
SYMBOL = "CTD"
EXCHANGE = "HOSE"
START_DATE_STR = "01/01/2020"
END_DATE_STR = datetime.now().strftime("%d/%m/%Y")
TARGET_DATE = datetime(2020, 1, 1) # Ngày dừng lại

API_URL = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": f"https://cafef.vn/du-lieu/lich-su-giao-dich/hose/{SYMBOL.lower()}-3.chn",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch_page(page_index):
    """Lấy dữ liệu theo số trang, truyền TỔNG THỜI GIAN để CafeF biết mà chia trang"""
    params = {
        "Symbol": SYMBOL,
        "Exchange": EXCHANGE,
        "StartDate": START_DATE_STR, # BẮT BUỘC có để xin toàn bộ cục dữ liệu 6 năm
        "EndDate": END_DATE_STR,
        "PageIndex": page_index,
        "PageSize": 20
    }
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get("Success"):
                return json_data.get("Data", {}).get("Data", [])
        return []
    except Exception as e:
        print(f"\nLỗi tại trang {page_index}: {e}")
        return []

# --- CHƯƠNG TRÌNH CHÍNH ---
all_results = []
current_page = 1
stop_collecting = False

print(f"🚀 Đang quét dữ liệu {SYMBOL} từ {END_DATE_STR} lùi về {START_DATE_STR}...")

while not stop_collecting:
    print(f"Đang lấy trang {current_page}...", end=" ", flush=True)
    
    data_page = fetch_page(current_page)
    
    if not data_page:
        print("Empty (Hết dữ liệu). Dừng.")
        break
        
    print(f"OK ({len(data_page)} dòng)", end=" ")
    
    for row in data_page:
        # Chuyển đổi ngày để kiểm tra xem đã lùi tới mốc 2020 chưa
        row_date = datetime.strptime(row['Ngay'], "%d/%m/%Y")
        
        if row_date < TARGET_DATE:
            stop_collecting = True
            print(f"\n✅ Đã chạm tới ngày mục tiêu: {row['Ngay']}. Dừng quét.")
            break
            
        all_results.append(row)
    
    if not stop_collecting and data_page:
        print(f"| Ngày cuối trang: {data_page[-1]['Ngay']}")

    current_page += 1
    time.sleep(0.5) 

# --- LƯU FILE ---
if all_results:
    df = pd.DataFrame(all_results)
    df.drop_duplicates(subset=['Ngay'], inplace=True)
    
    file_name = f"GDKN_{SYMBOL}_FULL.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n📊 HOÀN THÀNH! Tổng cộng thu được {len(df)} phiên giao dịch.")
    print(f"📁 Đã lưu vào file: {file_name}")
else:
    print("\n❌ Không lấy được dữ liệu nào.")