import pandas as pd

def calculate_adjusted_price(df_price, df_events):
    # Tự động tìm và đổi tên cột để tránh lỗi KeyError
    # Tìm cột chứa chữ 'Ngày' hoặc 'Date'
    col_map = {}
    for col in df_price.columns:
        c_upper = col.upper().strip()
        if 'NGÀY' in c_upper or 'DATE' in c_upper:
            col_map[col] = 'Date'
        elif 'LẦN CUỐI' in c_upper or 'CLOSE' in c_upper or 'GIÁ' in c_upper:
            col_map[col] = 'Close'
    
    df_price = df_price.rename(columns=col_map)
    
    if 'Date' not in df_price.columns or 'Close' not in df_price.columns:
        print("❌ Lỗi: Không tìm thấy cột Ngày (Date) hoặc Giá (Close) trong file!")
        print(f"Các cột đang có: {list(df_price.columns)}")
        return None

    # Chuyển đổi dữ liệu
    df_price['Date'] = pd.to_datetime(df_price['Date'], dayfirst=True, errors='coerce')
    df_price = df_price.dropna(subset=['Date'])
    
    # Làm sạch số (xóa dấu chấm/phẩy phân cách hàng nghìn)
    if df_price['Close'].dtype == 'O':
        df_price['Close'] = df_price['Close'].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df_price['Close'] = pd.to_numeric(df_price['Close'], errors='coerce')
    df_price = df_price.dropna(subset=['Close'])

    # Sắp xếp và tính toán
    df_price = df_price.sort_values('Date').reset_index(drop=True)
    df_price['Adj_Close'] = df_price['Close'].astype(float)
    
    df_events['Ex_Date'] = pd.to_datetime(df_events['Ex_Date'])
    df_events = df_events.sort_values('Ex_Date', ascending=False)
    
    for _, row in df_events.iterrows():
        ex_date = row['Ex_Date']
        mask_before = df_price['Date'] < ex_date
        if not mask_before.any(): continue
            
        p_before = df_price.loc[mask_before, 'Adj_Close'].iloc[-1]
        num = p_before - row.get('Cash_Div', 0) + (row.get('Issue_Price', 0) * row.get('Issue_Ratio', 0))
        den = 1 + row.get('Stock_Div_Ratio', 0) + row.get('Issue_Ratio', 0)
        p_theoretical = num / den
        
        adj_factor = p_theoretical / p_before
        df_price.loc[mask_before, 'Adj_Close'] *= adj_factor
            
    return df_price.sort_values('Date', ascending=False)

# --- PHẦN ĐỌC FILE ---
file_path = r"C:\Users\tuana\Downloads\Quant\Data\BAF.xlsx"
encodings = ['utf-8-sig', 'cp1252', 'latin-1']
df = None

for enc in encodings:
    try:
        df = pd.read_csv(file_path, encoding=enc)
        break
    except:
        continue

if df is not None:
    # Sự kiện BAF (Ngày 17/5/2024 và 9/5/2022)
    df_events = pd.DataFrame({
        'Ex_Date': ['2024-05-17', '2022-05-09'],
        'Stock_Div_Ratio': [0.17, 0.84],
        'Issue_Ratio': [0.476767, 0.0],
        'Issue_Price': [10000, 0.0]
    })

    df_final = calculate_adjusted_price(df, df_events)
    
    if df_final is not None:
        df_final.to_csv("BAF_Adjusted_Final.csv", index=False, encoding='utf-8-sig')
        print("🚀 THÀNH CÔNG!")
        print("Đã tạo file: BAF_Adjusted_Final.csv")
        print(df_final[['Date', 'Close', 'Adj_Close']].head())
else:
    print("❌ Không thể đọc file. Kiểm tra lại đường dẫn.")