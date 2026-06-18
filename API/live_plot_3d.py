import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# Thiết lập giao diện figure 3D
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

def update_3d(frame):
    conn = sqlite3.connect("market_data.db")
    # Lấy 15 nhịp gần nhất để giữ đồ thị trực quan và mượt mà
    df = pd.read_sql_query("SELECT * FROM order_book ORDER BY id DESC LIMIT 15", conn)
    conn.close()
    
    if df.empty: return

    # 🔥 GIỮ GÓC XOAY: Lưu lại góc nhìn hiện tại do chuột của bạn đang giữ
    current_elev = ax.elev if ax.elev is not None else 25
    current_azim = ax.azim if ax.azim is not None else -75

    ax.cla() # Xóa đồ thị cũ để tái render nhịp mới
    
    # Đảo chuỗi thời gian để nhịp mới nhất luôn nằm ở tiền cảnh (gần mắt bạn nhất)
    df = df.iloc[::-1].reset_index(drop=True)
    
    # BƯỚC 1: Lấy danh sách GIÁ THỰC TẾ của nhịp mới nhất để làm nhãn trục X
    latest_row = df.iloc[-1]
    prices_x = []
    
    # 5 tầng Bid tốt nhất (b_p5 -> b_p1)
    for j in range(5, 0, -1): 
        prices_x.append(latest_row[f'b_p{j}'])
    # 5 tầng Ask tốt nhất (a_p1 -> a_p5)
    for j in range(1, 6): 
        prices_x.append(latest_row[f'a_p{j}'])
    
    # BƯỚC 2: Xây dựng ma trận Khối lượng tương ứng cho 10 cột giá này
    z_matrix = []
    for i in range(len(df)):
        row = df.iloc[i]
        vols = []
        for j in range(5, 0, -1): vols.append(row[f'b_v{j}']) # Khối lượng mua
        for j in range(1, 6): vols.append(row[f'a_v{j}'])     # Khối lượng bán
        z_matrix.append(vols)
        
    Z = np.array(z_matrix)
    
    # BƯỚC 3: Vẽ các cột Bar 3D và đổ màu tách biệt theo Phe (Mua = Xanh lá / Bán = Đỏ)
    for i in range(len(df)):      # Chạy qua từng nhịp thời gian (Trục Y)
        for j in range(10):       # Chạy qua 10 bước giá (Trục X)
            v_size = Z[i, j]
            if v_size == 0: continue # Bỏ qua ô trống để tối ưu CPU
            
            # Phân tách màu sắc:
            # j < 5 là phe Mua (Bids) -> Màu Xanh lá (Tường càng dày màu càng sáng)
            # j >= 5 là phe Bán (Asks) -> Màu Đỏ (Tường càng dày màu càng rực)
            if j < 5:
                c = '#00FF00' if v_size > 20000 else ('#32CD32' if v_size > 5000 else '#006400')
            else:
                c = '#FF0000' if v_size > 20000 else ('#FF4500' if v_size > 5000 else '#8B0000')
                
            # Vẽ khối hộp 3D cho từng ô lệnh
            ax.bar3d(j, i, 0, 0.6, 0.6, v_size, color=c, alpha=0.55, edgecolor='none')

    # BƯỚC 4: Định cấu hình các trục và đè nhãn giá thực tế
    ax.set_xticks(range(10))
    # Định dạng hiển thị giá có dấu phẩy ngăn cách (ví dụ: 72,400)
    ax.set_xticklabels([f"{p:,.0f}" if p and not np.isnan(p) else "" for p in prices_x], rotation=15, fontsize=8)
    
    # Giới hạn trục Y theo số nhịp dữ liệu đang hiển thị
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(range(len(df)))

    # Đặt tên nhãn trực quan
    ax.set_title("Real-time 3D Order Book Depth (Bid/Ask Split View)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Mức Giá Thực Tế (Bids bên trái | Asks bên phải)", fontsize=9, labelpad=10)
    ax.set_ylabel("Thời gian (Nhịp lùi về quá khứ)", fontsize=9)
    ax.set_zlabel("Khối lượng (Volume)", fontsize=9)
    
    # 🔥 KHÓA GÓC NHÌN: Ép đồ thị nhịp mới phải tuân theo góc xoay chuột hiện tại của bạn
    ax.view_init(elev=current_elev, azim=current_azim)

# Cập nhật livetime GIỮ NGUYÊN tốc độ 1000ms (1 giây) theo yêu cầu
ani = FuncAnimation(fig, update_3d, interval=1000, cache_frame_data=False)
plt.tight_layout()
plt.show()