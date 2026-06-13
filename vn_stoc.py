from vnstock import register_user
from vnstock.api.quote import Quote
import pandas as pd

# Khai báo API Key của bạn
register_user(api_key="vnstock_083866c9884986cb1c3b5c34734efb12")

# Danh sách các nguồn hỗ trợ tốt trong v4.x để chạy vòng lặp dự phòng
cac_nguon_thu_nghiem = ['dnse', 'kbs']
data_da_lay_duoc = False

for nguon in cac_nguon_thu_nghiem:
    print(f"\n🔄 [THỬ NGHIỆM] Đang kết nối tới nguồn: {nguon.upper()}...")
    try:
        q = Quote(symbol='CTD', source=nguon)
        
        # 1. Lấy dữ liệu Sổ lệnh (Price Depth)
        print(f"📥 Đang tải Sổ lệnh từ {nguon.upper()}...")
        df_price_depth = q.price_depth()
        
        print(f"\n📊 KẾT QUẢ SỔ LỆNH CHỜ ({nguon.upper()}):")
        print("-" * 60)
        print(df_price_depth)
        print("-" * 60)
        
        # 2. Lấy dữ liệu Lịch sử khớp lệnh (Intraday)
        print(f"📥 Đang tải Lịch sử khớp lệnh từ {nguon.upper()}...")
        df_intraday = q.intraday()
        
        print(f"\n📊 KẾT QUẢ KHỚP LỆNH CHI TIẾT ({nguon.upper()}):")
        print("-" * 60)
        if isinstance(df_intraday, pd.DataFrame) and not df_intraday.empty:
            print(df_intraday.head(10))
        else:
            print(df_intraday)
        print("-" * 60)
        
        # Nếu chạy đến đây không lỗi thì đặt trạng thái thành công và dừng vòng lặp
        data_da_lay_duoc = True
        print(f"✅ Lấy dữ liệu thành công từ nguồn {nguon.upper()}!")
        break
        
    except Exception as e:
        print(f"❌ Nguồn {nguon.upper()} gặp lỗi: {e}")
        print("Đang chuyển sang nguồn tiếp theo...")

if not data_da_lay_duoc:
    print("\n⚠️ Tất cả các nguồn đều thất bại. Nguyên nhân khả thi nhất:")
    print("1. Hệ thống API của các CTCK đang bảo trì định kỳ vào cuối tuần.")
    print("2. Thư viện vnstock bản 4.0.4 đang bị lỗi đồng bộ lõi với Python 3.13.")