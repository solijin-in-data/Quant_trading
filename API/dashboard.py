import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import time

st.set_page_config(layout="wide")
st.title("⚡ Realtime Market Liquidity Map")

def get_data():
    conn = sqlite3.connect("market_data.db")
    # SỬA Ở ĐÂY: Đọc cột 'price_change' và đổi tên tạm thành 'aggressor' cho Pandas DataFrame
    df_trades = pd.read_sql_query("SELECT id, timestamp, symbol, price, volume, price_change AS aggressor, total_volume FROM trades", conn)
    conn.close() # Nên đóng kết nối sau khi đọc xong để tránh kẹt DB
    return df_trades

# Tạo nơi chứa biểu đồ
chart_placeholder = st.empty()

while True:
    try:
        df = get_data()
        if not df.empty:
            # Vẽ biểu đồ Heatmap của các lệnh khớp
            fig = px.scatter(df, x="timestamp", y="price", color="aggressor", 
                             size="volume", color_continuous_scale="RdYlGn",
                             title="Realtime Trade Flow (Xanh: Buy, Đỏ: Sell)")
            
            with chart_placeholder.container():
                st.plotly_chart(fig, use_container_width=True)
        
        time.sleep(1) # Cập nhật mỗi 1 giây
        
    except Exception as e:
        # Giúp Dashboard không bị sập (crash) nếu DB đang bận ghi dữ liệu
        time.sleep(1)
        pass