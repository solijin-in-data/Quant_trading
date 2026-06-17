# Quant Trading Data Pipeline (FiinTrade/Kafi)

Dự án này cung cấp công cụ thu thập dữ liệu thời gian thực (Real-time Market Data) từ hệ thống FiinTrade thông qua Kafi dưới giao thức WebSocket (SignalR).

## Tính năng chính
- **Real-time Streaming:** Lắng nghe dữ liệu khớp lệnh (Tick) và sổ lệnh (Bid/Ask) liên tục.
- **Snapshot Support:** Tự động lấy dữ liệu đóng phiên ngay khi kết nối.
- **SignalR Integration:** Xử lý chuẩn giao thức SignalR với cơ chế Handshake và Message Separation.

## Cấu trúc thư mục
- `kafi_api_data.py`: Module chính xử lý kết nối WebSocket.
- `config.py` (Khuyến khích tạo): Lưu trữ các biến môi trường như JWT_TOKEN.

## Cách cài đặt
1. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install requests websocket-client

