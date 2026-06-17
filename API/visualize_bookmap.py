import sqlite3
import pandas as pd
import plotly.graph_objects as go

def render_heatmap():
    print("⏳ Đang truy xuất dữ liệu từ market_data.db...")
    conn = sqlite3.connect('market_data.db')

    # 1. Lấy dữ liệu từ Database
    df_book = pd.read_sql_query("SELECT * FROM order_book ORDER BY timestamp ASC", conn)
    df_trades = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp ASC", conn)
    conn.close()

    if df_book.empty:
        print("❌ Chưa có dữ liệu sổ lệnh. Hãy để hệ thống Trading chạy thêm một lúc thu thập data!")
        return

    print(f"📊 Đã tải {len(df_book)} khung hình sổ lệnh và {len(df_trades)} tick khớp lệnh.")

    # 2. Tiền xử lý dữ liệu Sổ lệnh (Tạo lưới 3D: X=Time, Y=Price, Z=Volume)
    heatmap_data = []
    
    # Bóc tách từng cột giá và volume trong sổ lệnh
    for _, row in df_book.iterrows():
        ts = row['timestamp']
        
        # Xử lý BIDS (Phe mua)
        for i in range(1, 4):
            if pd.notna(row[f'b_p{i}']): 
                heatmap_data.append({'time': ts, 'price': row[f'b_p{i}'], 'volume': row[f'b_v{i}']})
                
        # Xử lý ASKS (Phe bán)
        for i in range(1, 4):
            if pd.notna(row[f'a_p{i}']): 
                heatmap_data.append({'time': ts, 'price': row[f'a_p{i}'], 'volume': row[f'a_v{i}']})

    df_heat = pd.DataFrame(heatmap_data)
    
    # Gom nhóm và xoay trục (Pivot) để tạo lưới Grid (Ma trận) cho Heatmap
    pivot_heat = df_heat.pivot_table(index='price', columns='time', values='volume', aggfunc='sum').fillna(0)

    # 3. Vẽ biểu đồ với Plotly
    print("🎨 Đang render đồ họa 3D Heatmap...")
    fig = go.Figure()

    # Lớp 1: Bản đồ nhiệt (Liquidity Depth)
    # Dùng bảng màu 'Inferno' (Nền đen, thanh khoản cao sẽ sáng vàng rực rỡ)
    fig.add_trace(go.Heatmap(
        z=pivot_heat.values,
        x=pivot_heat.columns,
        y=pivot_heat.index,
        colorscale='Inferno', 
        showscale=True,
        name='Limit Orders'
    ))

    # Lớp 2: Quỹ đạo khớp lệnh (Trade Executions)
    if not df_trades.empty:
        # Tách lệnh Buy / Sell dựa trên Aggressor đã tính bằng thuật toán Lee-Ready
        buy_trades = df_trades[df_trades['aggressor'] == 1]
        sell_trades = df_trades[df_trades['aggressor'] == -1]

        # Bong bóng xanh cho Buy Aggressor
        fig.add_trace(go.Scatter(
            x=buy_trades['timestamp'], 
            y=buy_trades['price'],
            mode='markers',
            marker=dict(
                color='#00FF00', 
                size=buy_trades['volume'], 
                sizeref=2000, # Chỉnh thông số này nếu bong bóng quá to/nhỏ
                sizemin=3,
                line=dict(width=1, color='white')
            ),
            name='Aggressive Buy'
        ))
        
        # Bong bóng đỏ cho Sell Aggressor
        fig.add_trace(go.Scatter(
            x=sell_trades['timestamp'], 
            y=sell_trades['price'],
            mode='markers',
            marker=dict(
                color='#FF0000', 
                size=sell_trades['volume'], 
                sizeref=2000, # Chỉnh thông số này nếu bong bóng quá to/nhỏ
                sizemin=3,
                line=dict(width=1, color='white')
            ),
            name='Aggressive Sell'
        ))

    # Tùy chỉnh Layout chuẩn Terminal/Quant
    fig.update_layout(
        title="High-Frequency Limit Order Book & Trade Flow Heatmap",
        xaxis_title="Timeline",
        yaxis_title="Price Levels",
        template="plotly_dark", # Bắt buộc dùng Dark Theme để tôn màu Heatmap
        hovermode="closest",
        plot_bgcolor='rgb(10, 10, 10)',
        paper_bgcolor='rgb(10, 10, 10)'
    )

    # Tự động mở trình duyệt hiển thị kết quả
    fig.show()

if __name__ == "__main__":
    render_heatmap()