import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import re

def parse_and_analyze_fireant(file_path):
    print("=== BƯỚC 1: ĐANG ĐỌC VÀ BÓC TÁCH DỮ LIỆU HTML ===")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"❌ KHÔNG TÌM THẤY FILE TẠI ĐƯỜNG DẪN: {file_path}")
        return None
        
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Tìm tất cả các hàng lệnh dựa trên class list-row đặc trưng
    rows = soup.select('div[class*="list-row"]')
    
    records = []
    
    for row in rows:
        # Lấy tất cả các thẻ div con sâu nhất chứa text trực tiếp (ô dữ liệu)
        cells = [div for div in row.find_all("div") if div.text.strip() and not div.find("div")]
        
        # Lọc bỏ trùng lặp text liên tiếp do cấu trúc lồng
        unique_cells = []
        for c in cells:
            t = c.text.strip()
            if not unique_cells or t != unique_cells[-1]['text']:
                unique_cells.append({'text': t, 'element': c})
        
        # Một dòng chuẩn trên FireAnt luôn bóc ra được đúng 5 thông số
        if len(unique_cells) >= 5:
            time_val = unique_cells[0]['text']
            price_val = unique_cells[1]['text']
            change_val = unique_cells[2]['text']
            volume_val = unique_cells[3]['text']
            side_raw = unique_cells[4]['text']
            
            # KIỂM TRA ĐIỀU KIỆN AN TOÀN: Cột đầu tiên bắt buộc phải là định dạng Thời gian HH:MM:SS
            if re.match(r'^\d{2}:\d{2}:\d{2}$', time_val):
                # Chuẩn hóa Side (S của FireAnt là xanh -> BUY, B của FireAnt là đỏ -> SELL)
                if side_raw == 'S':
                    side = 'BUY'
                elif side_raw == 'B':
                    side = 'SELL'
                else:
                    side = 'UNKNOWN'
                    
                records.append({
                    "Time": time_val,
                    "Price": price_val,
                    "Change": change_val,
                    "Volume": volume_val,
                    "Side": side
                })

    df = pd.DataFrame(records)
    
    # PHƯƠNG ÁN DỰ PHÒNG 2: Nếu bộ lọc class thất bại, quét thô toàn bộ cấu trúc file dựa trên định dạng Giờ
    if df.empty:
        print("⚠️ Chuyển sang phương án quét thô tối ưu vị trí...")
        all_divs = [d for d in soup.find_all("div") if d.text.strip() and not d.find("div")]
        records_backup = []
        
        i = 0
        while i < len(all_divs) - 4:
            # Tìm ô có định dạng thời gian
            if re.match(r'^\d{2}:\d{2}:\d{2}$', all_divs[i].text.strip()):
                # Kiểm tra xem các ô tiếp theo có khớp cấu trúc (Giá, Biến động, Khối lượng, Side) không
                try:
                    time_v = all_divs[i].text.strip()
                    price_v = all_divs[i+1].text.strip()
                    change_v = all_divs[i+2].text.strip()
                    vol_v = all_divs[i+3].text.strip()
                    side_v = all_divs[i+4].text.strip()
                    
                    if side_v in ['B', 'S'] and ',' in vol_v or vol_v.isdigit():
                        records_backup.append({
                            "Time": time_v, "Price": price_v, "Change": change_v, 
                            "Volume": vol_v, "Side": 'BUY' if side_v == 'S' else 'SELL'
                        })
                        i += 5 # Nhảy qua hàng này
                        continue
                except:
                    pass
            i += 1
        df = pd.DataFrame(records_backup)
        
    if df.empty:
        print("❌ Thất bại hoàn toàn. Không thể nhận diện cấu trúc file HTML.")
        return None
        
    # Loại bỏ các dòng trùng lặp 
    df = df.drop_duplicates(subset=["Time", "Price", "Volume", "Side"]).reset_index(drop=True)
    
    # Đảo ngược để dữ liệu chạy xuôi dòng thời gian từ sáng tới chiều
    df = df.iloc[::-1].reset_index(drop=True)
    
    # CHUẨN HÓA SỐ LIỆU (Có xử lý an toàn lỗi chuỗi)
    df["Price"] = df["Price"].astype(str).str.replace(",", "", regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
    
    df["Volume"] = df["Volume"].astype(str).str.replace(",", "", regex=False).str.replace(".", "", regex=False)
    df["Volume"] = pd.to_numeric(df["Volume"], errors='coerce').fillna(0).astype(int)
    
    # Loại bỏ các dòng lỗi data nếu có
    df = df.dropna(subset=["Price"]).reset_index(drop=True)
    
    print(f"✅ Đã trích xuất thành công {len(df)} lệnh khớp sạch từ file HTML.")
    print("\n--- XEM TRƯỚC 5 LỆNH ĐẦU TIÊN TRONG PHIÊN ---")
    print(df.head().to_string())
    
    # =========================================================================
    print("\n=== BƯỚC 2: BOT ĐANG PHÂN TÍCH BẤT THƯỜNG SỔ LỆNH ===")
    
    # 1. Thuật toán quét LỆNH CÁ MẬP (IQR)
    q3 = df["Volume"].quantile(0.75)
    iqr = q3 - df["Volume"].quantile(0.25)
    whale_threshold = q3 + 3 * iqr
    whale_threshold = max(whale_threshold, df["Volume"].median() * 10)
    
    whale_trades = df[df["Volume"] >= whale_threshold]
    
    print(f"📌 Ngưỡng lệnh CÁ MẬP tự động xác định: >= {whale_threshold:,.0f} CP/lệnh")
    print(f"🚨 Phát hiện {len(whale_trades)} lệnh Cá mập hành động:")
    if not whale_trades.empty:
        print(whale_trades[["Time", "Price", "Volume", "Side"]].to_string(index=False))
    else:
        print("=> Không có lệnh cá mập nào vượt ngưỡng.")
        
    # 2. Thuật toán quét HFT ROBOT QUAY TAY (Trùng khít Giờ-Giá-Vol)
    df['Is_Abnormal_HFT'] = (df['Volume'] == df['Volume'].shift(1)) & \
                             (df['Price'] == df['Price'].shift(1)) & \
                             (df['Time'] == df['Time'].shift(1))
                             
    hft_trades = df[df['Is_Abnormal_HFT'] == True]
    print(f"\n🚨 Phát hiện {len(hft_trades)} lệnh có dấu hiệu ROBOT QUAY TAY:")
    if not hft_trades.empty:
        print(hft_trades[["Time", "Price", "Volume", "Side"]].head(10).to_string(index=False))
        if len(hft_trades) > 10:
            print(f"... và {len(hft_trades) - 10} lệnh tương tự khác.")
    else:
        print("=> Sổ lệnh sạch, không phát hiện robot quay tay.")
        
    # Lưu file kết quả sạch ra ổ D
    output_path = r"D:\Python\fireant_ticks_analyzed.csv"
    df.to_csv(output_path, index=False)
    print(f"\n💾 Đã phân tích xong và lưu bảng dữ liệu sạch vào: {output_path}")
    
    return df

# --- CHẠY BOT ---
file_name = r"D:\Python\fireant_source.html"
df_clean = parse_and_analyze_fireant(file_name)