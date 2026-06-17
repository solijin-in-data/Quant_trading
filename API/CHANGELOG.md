# Changelog

Tất cả những thay đổi đáng chú ý của dự án này sẽ được ghi lại trong file này.

## [Unreleased]
### Added
- [X] Xây dựng cơ chế tự động kết nối lại (Auto-reconnect) khi WebSocket bị ngắt.
- [ ] Chuyển đổi quản lý `JWT_TOKEN` từ code cứng sang file `.env`.
- [X] Tích hợp ghi log dữ liệu thô vào SQLite.

## [0.1.1] - 2026-06-18
### Added
- **[Feature] Cơ chế Auto-Reconnect:** Bọc toàn bộ quy trình khởi tạo trong vòng lặp `while True` để hệ thống tự tái cấu trúc kết nối khi xảy ra sự cố.
- **[Feature] Giăng lưới Sổ lệnh:** Gửi đồng thời nhiều payload `JoinGroup` dò tìm kênh dữ liệu mức giá (`BidAsk`, `Depth`, `OrderBook`).
- **[Feature] Defensive Code:** Hỗ trợ cơ chế lấy trường dữ liệu fallback (`chanel` hoặc `channel`) đề phòng Server thay đổi định dạng.

### Fixed
- **Sửa lỗi ngắt kết nối ẩn (Lỗi sập mạng 10054):** Tích hợp tham số `ping_interval=15` và `ping_timeout=10` vào hàm `ws.run_forever()` để duy trì trạng thái kết nối sống liên tục với Server.

## [0.1.0] - 2026-06-16
### Added
- Khởi tạo dự án kết nối dữ liệu Real-time.
- Hoàn thiện luồng Handshake với SignalR protocol.
- Thành công kết nối WebSocket tới server FiinTrade.
- [Feature] Lấy dữ liệu Snapshot (giá chốt phiên).
- [Feature] Đăng ký theo dõi luồng Tick (lệnh khớp) và Ticker (bước giá).
- Xây dựng hệ thống bóc tách dữ liệu (Parsing) cơ bản cho mã cổ phiếu.

### Fixed
- Sửa lỗi không nhận được dữ liệu do thiếu ký tự phân tách `chr(30)`.
- Xử lý lỗi ping/pong của máy chủ SignalR để tránh ngắt kết nối không mong muốn.