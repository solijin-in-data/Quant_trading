import pandas as pd

# ===== 1. CẤU HÌNH ĐƯỜNG DẪN =====
file_path = r"C:\Users\tuana\Downloads\Quant\Data\BAF.csv"
output_path = r"C:\Users\tuana\Downloads\Quant\Data\BAF_Adjusted_Final.xlsx"

# ===== 2. ĐỌC VÀ CLEAN DỮ LIỆU (Code của bạn đã fix tên cột) =====
df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip()

# Xử lý Ngày
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

# Xử lý Giá (Xóa dấu phẩy và ép kiểu số)
price_cols = ["Close", "Open", "High", "Low"]
for col in price_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Xử lý Volume (M, K)
if "Volume" in df.columns:
    def convert_volume(x):
        x = str(x).upper().strip()
        if "M" in x: return float(x.replace("M", "")) * 1_000_000
        if "K" in x: return float(x.replace("K", "")) * 1_000
        return pd.to_numeric(x, errors="coerce")
    df["Volume"] = df["Volume"].apply(convert_volume)

# Xử lý % Change (Sửa tên cột thành %_Change theo file thực tế)
target_pct_col = "%_Change" if "%_Change" in df.columns else "% Change"
if target_pct_col in df.columns:
    df[target_pct_col] = df[target_pct_col].astype(str).str.replace("%", "", regex=False)
    df[target_pct_col] = pd.to_numeric(df[target_pct_col], errors="coerce")

# ===== 3. TÍNH GIÁ ĐIỀU CHỈNH (ADJUSTED PRICE) =====
def apply_adjustment(df_price):
    df_price = df_price.dropna(subset=['Date', 'Close']).sort_values('Date')
    df_price['Adj_Close'] = df_price['Close'].astype(float)
    
    # Khai báo sự kiện doanh nghiệp của BAF
    events = [
        {'date': '2024-05-17', 'stock_div': 0.17, 'iss_ratio': 0.476767, 'iss_price': 10000},
        {'date': '2022-05-09', 'stock_div': 0.84, 'iss_ratio': 0, 'iss_price': 0}
    ]
    
    for ev in events:
        ex_date = pd.to_datetime(ev['date'])
        mask_before = df_price['Date'] < ex_date
        if mask_before.any():
            p_before = df_price.loc[mask_before, 'Adj_Close'].iloc[-1]
            # Công thức điều chỉnh
            p_theo = (p_before + ev['iss_price'] * ev['iss_ratio']) / (1 + ev['stock_div'] + ev['iss_ratio'])
            adj_factor = p_theo / p_before
            df_price.loc[mask_before, 'Adj_Close'] *= adj_factor
            
    return df_price.sort_values('Date', ascending=False)

# Thực thi tính toán
df_final = apply_adjustment(df)

# ===== 4. XUẤT FILE =====
df_final.to_excel(output_path, index=False)

print("\n✅ HOÀN THÀNH!")
print(f"📁 File đã lưu tại: {output_path}")
print(df_final[['Date', 'Close', 'Adj_Close']].head())