import pandas as pd

# ===== FILE PATH =====
file_path = r"C:\Users\tuana\Downloads\Quant\Data\BAF.csv"

# ===== READ EXCEL =====
df = pd.read_csv(
    file_path,
    encoding="utf-8-sig"
)

# ===== KIỂM TRA CỘT =====
print("Các cột đang có:")
print(df.columns.tolist())

# ===== CHUẨN HÓA TÊN CỘT =====
df.columns = df.columns.str.strip()

# ===== DATE =====
if "Date" in df.columns:

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

# ===== PRICE COLUMNS =====
price_cols = ["Close", "Open", "High", "Low"]

for col in price_cols:

    if col in df.columns:

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
        )

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# ===== VOLUME =====
if "Volume" in df.columns:

    def convert_volume(x):

        x = str(x).upper().strip()

        if "M" in x:
            return float(x.replace("M", "")) * 1_000_000

        elif "K" in x:
            return float(x.replace("K", "")) * 1_000

        return pd.to_numeric(x, errors="coerce")

    df["Volume"] = df["Volume"].apply(convert_volume)

# ===== % CHANGE =====
if "% Change" in df.columns:

    df["% Change"] = (
        df["% Change"]
        .astype(str)
        .str.replace("%", "", regex=False)
    )

    df["% Change"] = pd.to_numeric(
        df["% Change"],
        errors="coerce"
    )

# ===== EXPORT =====
output_path = r"C:\Users\tuana\Downloads\Quant\Data\BAF_clean.xlsx"

df.to_excel(
    output_path,
    index=False
)

print("\n✅ Thành công!")
print(df.dtypes)
print(f"\n📁 File đã lưu tại:\n{output_path}")