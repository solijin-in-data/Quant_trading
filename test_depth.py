from vnstock_data import Market

# Khởi tạo con bot vnstock
stock = Vnstock()

print("=== ĐANG TẢI SỔ LỆNH CHỜ (MARKET DEPTH) TỪ VNSTOCK ===")
try:
    # Gọi hàm lấy order book của CTD từ nguồn TCBS hoặc SSI
    df_depth = stock.stock(symbol='CTD', source='TCBS').price.order_book()
    
    # In ra toàn bộ bảng dữ liệu để xem tên cột và cấu trúc
    print("\n📊 Cấu trúc DataFrame trả về:")
    print(df_depth)
    
    print("\n📋 Danh sách các cột chính xác:")
    print(df_depth.columns.tolist())

except Exception as e:
    print(f"❌ Lỗi khi gọi API của vnstock: {e}")