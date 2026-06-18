# Changelog

Tất cả những thay đổi đáng chú ý của dự án này sẽ được ghi lại trong file này.

## [Unreleased]
### Added
- [X] Xây dựng cơ chế tự động kết nối lại (Auto-reconnect) khi WebSocket bị ngắt.
- [ ] Xây dựng database thu thập dữ liệu backtest
- [ ] Update logic tính toán 



## [0.6.0] - 2026-06-18
### 🚀 Nâng cấp hệ thống (Major Update)
- **Mở rộng Order Book:** Nâng cấp khả năng thu thập dữ liệu từ 3 tầng lên đầy đủ **10 tầng** (Bid/Ask) từ WebSocket.
- **Tái cấu trúc Database:** - Cập nhật schema bảng `order_book` để lưu trữ 20 cột giá và khối lượng (10 Bid, 10 Ask) thay vì giới hạn như trước.
    - Chuyển đổi sang phương thức chèn dữ liệu động (`placeholders`) để tối ưu hiệu năng ghi.
- **Tối ưu hóa xử lý:** - Duy trì logic phân tích HFT hiện tại bằng cách tách biệt dữ liệu: sử dụng 3 mức tốt nhất cho tính toán tín hiệu (Signal Engine) và lưu trữ toàn bộ 10 mức vào SQLite.
    - Cải thiện độ ổn định khi xử lý chuỗi tin nhắn WebSocket (phân tách ký tự `chr(30)` hiệu quả hơn).
### 🧠 Nâng cấp tư duy phân tích (Core Engine)
- **Chuyển đổi sang Notional Value:** Thay thế ngưỡng cố định (`volume > threshold`) bằng `Notional Threshold` (Price × Volume). Điều này giúp bot thích nghi với mọi mã cổ phiếu (ví dụ: CTD) thay vì phải tinh chỉnh thủ công cho từng mã.
- **Phân tách hành vi dòng lệnh (Deep Flow Analysis):**
    - Logic cũ bị nhầm lẫn giữa *Hủy lệnh* (Cancel) và *Khớp lệnh* (Consumed).
    - Cập nhật cơ chế tính toán Delta: `Delta = (Current_Vol - Prev_Vol)`. Nếu `Delta < 0` mà có `Traded_Vol` -> Phân loại chính xác là "Hủy lệnh" hay "Khớp lệnh".
- **Phát hiện Iceberg/Replenishment:** Thiết lập bộ nhận diện mới: nếu lệnh vừa bị khớp (`Traded_Vol > 0`) mà `Delta` của mức giá đó vẫn tăng -> Xác định là hành vi tiếp tế thanh khoản (Iceberg/Refill).
- **Reset Logic thông minh:** `ticks_survived` và `absorbed_volume` không còn đếm vô tận mà sẽ tự động `reset` sau khi mức giá đã đạt ngưỡng cảnh báo (Passive Absorption), tránh sai lệch dữ liệu tích lũy.

### 🛠 Cải tiến kỹ thuật
- **Schema Database:** Mở rộng lên 10 tầng Order Book để phục vụ phân tích sâu.
- **Tối ưu hóa performance:** Chuyển sang sử dụng `placeholders` cho các câu lệnh SQL INSERT, giảm tải IO cho database.
- **Kết nối:** Nâng cấp cơ chế `ping/pong` để duy trì WebSocket ổn định trong phiên giao dịch có biến động cao.
- Tăng cường khả năng chịu lỗi khi parsing dữ liệu WebSocket đầu vào.
- Cấu trúc lại file để tách biệt rõ ràng giữa logic Database và luồng xử lý thời gian thực.
- Cập nhật cơ chế `ping_interval` và `ping_timeout` để duy trì kết nối WebSocket bền bỉ hơn trong môi trường mạng không ổn định.



## [0.5.1-Beta] - 2026-06-18
### Added
- Mở rộng cấu trúc lưu trữ cơ sở dữ liệu `order_book` lên đầy đủ 10 tầng (Mua/Bán) đồng thời tự động hóa chuỗi tham số placeholders (`?`) động để tối ưu câu lệnh `INSERT INTO`.

### Fixed
- **Triệt tiêu lỗi Race Condition luồng dữ liệu:** Thay thế hàm xóa sạch `.clear()` của cấu trúc lưu trữ `traded_vol_at_bid/ask` bằng cơ chế xóa đích danh mức giá `del self.state.traded_vol_at_bid[p]` ngay sau khi tính toán lượng hấp thụ/nhồi lệnh. Đảm bảo tính toán đúng lượng `REPLENISHMENT` (Iceberg) khi WebSocket trả về gói tin bất đồng bộ liên tiếp.
- **Vá lỗ hổng rò rỉ bộ nhớ (Memory Leak):** Tích hợp bộ dọn dẹp Garbage Collection tự động bên trong `process_book()`. Toàn bộ các mức giá nằm ngoài khoảng biên độ $\pm20$ bước giá so với giá thị trường hiện tại (Spread) sẽ bị loại bỏ hoàn toàn khỏi bộ nhớ RAM, ngăn chặn tình trạng tràn bộ nhớ (Out-Of-Memory) khi treo bot dài ngày.



## [0.5.0-Alpha-HFT] 
### Added
- **[Tính năng] Thuật toán tìm kiếm thanh khoản ẩn (Iceberg/Replenishment):** So sánh chênh lệch giữa khối lượng sổ lệnh thực tế với khối lượng kỳ vọng sau khớp lệnh để phát hiện các lệnh nhồi ẩn từ cá mập.
- **[Tính năng] Đo lường tuổi thọ tường lệnh (Persistent Wall):** Lưu vết thời gian thiết lập lệnh lớn (`birth_time`), lọc bỏ nhiễu lệnh ảo (Spoofing) bằng cách theo dõi ngưỡng duy trì ổn định > 30 giây.
- **[Kỹ thuật] Đồng bộ hóa dữ liệu DB cũ:** Hàm `init_db()` tự động ánh xạ trường `price_change` để tương thích ngược với cấu trúc bảng cũ mà không làm gián đoạn mã nguồn phân tích Core Engine.

### Fixed
- **[Sửa lỗi] Race Condition & Memory Leak:** Tái cấu trúc cơ chế giải phóng bộ nhớ của các từ điển theo dõi khối lượng khớp `traded_vol_at_X`. Thay thế phương thức xóa toàn bộ bằng cơ chế xóa đích danh theo mức giá được xử lý, đảm bảo hệ thống chạy liên tục không bị tràn bộ nhớ RAM (OOM) hoặc tính toán sai lệch thể tích.



## [0.4.0-Alpha-HFT] 
### Added
- **[Kỹ thuật] Kiến trúc hướng sự kiện (Event-Driven Architecture):** Tách cấu trúc hệ thống thành 3 tầng xử lý biệt lập (`MarketState` -> `EventEngine` -> `SignalInterpreter`) để tối ưu hóa khả năng bảo trì và nâng cấp thuật toán độc lập.
- **[Thuật toán] Bộ lọc Tick Test nguyên bản:** Triển khai cơ chế tự động dò tìm vị thế lệnh chủ động (Aggressor Side - Mua/Bán chủ động) dựa trên chênh lệch bước giá của các Tick khớp lệnh liên tục.
- **[Thuật toán] Trọng số hóa OBI (Weighted OBI):** Chuyển đổi công thức OBI truyền thống sang mô hình có trọng số giảm dần theo khoảng cách bước giá ($1.0 \rightarrow 0.8 \rightarrow 0.6$), gia tăng độ nhạy cho các tín hiệu ép giá vùng biên.
- **[Tính năng] Dò bẫy lệnh Spoofing:** Phát triển cấu trúc so khớp dữ liệu Sổ lệnh kép (`current_book` đối ứng với `prev_book`) để nhận diện hành vi rút lệnh, hủy lệnh tường quy mô lớn của các tài khoản tạo lập thị trường.

### Changed
- **Tái cấu trúc SQLite Schema:** Thay đổi trường lưu trữ `price_change` (độ lệch giá) thành nhãn định danh xu hướng `aggressor` để tối ưu hóa dữ liệu phục vụ các tác vụ chạy Backtest chiến lược Order Flow sau này.



## [0.3.0-Production-Ready]
### Added
- **[Feature] Cơ sở dữ liệu SQLite:** Tích hợp bộ đôi bảng lưu trữ `trades` và `order_book` tự động cập nhật thời gian thực qua hệ thống khóa đồng bộ hóa luồng (`db_lock`).
- **[Quant] Chỉ báo OBI & CVD:** Triển khai bộ đôi chỉ báo phân tích vi mô dòng tiền, tự động tính toán tỷ lệ mất cân bằng cung cầu bước giá và vị thế tích lũy khối lượng dòng lệnh.
- **[Quant] Thuật toán Absorption Tracking:** Phát triển công cụ theo dõi cục bộ (`local_cvd`, `local_volume`) tại từng mức giá đơn lẻ để chấm điểm và phát hiện hành vi "cá mập" chặn mua gom hàng ẩn danh.

### Changed
- **Nâng cấp kiến trúc State Engine:** Chuyển đổi toàn bộ biến tĩnh thành mô hình hướng đối tượng với `MarketState` đóng vai trò quản lý bộ nhớ đệm trạng thái, và `SignalEngine` độc lập xử lý điều kiện kích hoạt cảnh báo.
- **Tối ưu hiển thị:** Định dạng lại hàm xuất Terminal, tích hợp hiển thị trực quan các tín hiệu phức tạp đa dòng dưới dạng cây sơ đồ (`├─`, `└─`).



## [0.2.0-stable] 
### Added
- **[Feature] Giải mã Sổ lệnh (BidAsk Decoder):** Bóc tách gói tệp tin từ nguồn dữ liệu Fiintrade
- **[UI] Giao diện Bảng điện thu nhỏ:** Thiết kế cấu trúc hiển thị Sổ lệnh cân đối trên Terminal theo luồng dọc (Bán ở trên, Mua ở dưới), mô phỏng trực quan hành vi của độ sâu thị trường (Market Depth).
- **[UI] Đổ màu dòng lệnh (Tape Coloration):** Áp dụng bảng màu ANSI Standard định dạng cho luồng Khớp lệnh (`Tick`), giúp dễ dàng nhận biết lực mua/bán áp đảo ngay trên Terminal.

### Changed
- **Chuẩn hóa kiểu dữ liệu (Data Normalization):** Ép kiểu dữ liệu Giá từ dạng chuỗi thô (String) sang dạng số thực (`float`) để áp dụng cơ chế format số có dấu phẩy hàng nghìn (`:,.0f`).
- **Tối ưu hóa Output:** Loại bỏ bớt các log log thông báo handshake không cần thiết, giúp Terminal sạch sẽ và mượt mà hơn khi dữ liệu đổ về với tần suất cao.



## [0.1.2-beta] 
### Added
- **[Feature] Mở rộng lưới dò kênh:** Bổ sung thêm các kênh tiềm năng bao gồm `MarketDepth` và `OrderBook` vào danh sách Pub/Sub tự động.
- **[UI] Làm đẹp Terminal:** Tinh chỉnh định dạng in dữ liệu Khớp lệnh (`Vol khớp: :>5`) giúp căn lề thẳng hàng, dễ quan sát dòng lệnh giao dịch (Tape Reading).

### Changed
- **Tối ưu hóa mã nguồn (Refactoring):** Gom gọn luồng xử lý sự kiện, loại bỏ các hàm log Snapshot dư thừa để Terminal tập trung hoàn toàn vào luồng dữ liệu biến động cao (Streaming Data).
- **Phòng vệ Key lỗi:** Thay đổi logic bóc tách kênh, kiểm tra đồng thời cả `chanel` và `channel` bảo vệ hệ thống trước các bản cập nhật ngầm của Server phía FiinTrade.



## [0.1.1] 
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