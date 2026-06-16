// Khởi tạo giỏ chứa dữ liệu
window.uniqueRecords = new Map();

// TẠO NÚT BẤM LƯU DỮ LIỆU HIỂN THỊ TRÊN MÀN HÌNH
let btn = document.createElement("button");
btn.innerText = "🛑 ĐANG GHI HÌNH... KHI NÀO CUỘN XONG BẤM VÀO ĐÂY ĐỂ LƯU TẤT CẢ! 🛑";
btn.style.cssText = "position:fixed; top:20px; right:20px; z-index:999999; padding:20px; background:#e74c3c; color:white; font-size:16px; font-weight:bold; cursor:pointer; border:3px solid white; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);";
document.body.appendChild(btn);

// BẬT CAMERA QUAY LÉN (Quét 5 lần 1 giây)
window.recordInterval = setInterval(() => {
    let rows = document.querySelectorAll('div[class*="list-row"]');
    let newCount = 0;
    
    rows.forEach(row => {
        let fullText = row.innerText.trim();
        // Nhận diện dòng có chứa thời gian
        if (/^\d{2}:\d{2}:\d{2}/.test(fullText)) {
            let timeText = fullText.substring(0, 8);
            let key = timeText + "|" + fullText.replace(/\s+/g, '');
            
            // Nếu là lệnh mới chưa có trong giỏ thì lụm ngay
            if (!window.uniqueRecords.has(key)) {
                window.uniqueRecords.set(key, row.outerHTML);
                newCount++;
            }
        }
    });
    
    if (newCount > 0) {
        console.log(`📸 Tạch tạch... Đã chụp được tổng cộng: ${window.uniqueRecords.size} lệnh`);
        btn.innerText = `🛑 ĐANG GHI HÌNH... ĐÃ CHỤP ĐƯỢC [ ${window.uniqueRecords.size} LỆNH ] - CUỘN TIẾP ĐI! 🛑`;
    }
}, 200);

// XỬ LÝ KHI BẠN BẤM NÚT LƯU
btn.onclick = () => {
    clearInterval(window.recordInterval); // Tắt camera
    
    // Đóng gói HTML
    let fullHTML = `<div style="width: 100%; height: auto;">\n`;
    window.uniqueRecords.forEach((html) => { fullHTML += html + "\n"; });
    fullHTML += `</div>`;

    // Tải file về
    let blob = new Blob([fullHTML], { type: "text/plain;charset=utf-8" });
    let url = URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = "CTD_Full_Data_Manual.txt"; // Tên file tải về
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Đổi màu nút để báo hiệu thành công
    btn.innerText = `✅ ĐÃ LƯU THÀNH CÔNG ${window.uniqueRecords.size} LỆNH VÀO MÁY!`;
    btn.style.background = "#2ecc71";
    setTimeout(() => btn.remove(), 5000); // Nút tự biến mất sau 5 giây
    
    console.log(`🎉 HOÀN TẤT TUYỆT ĐỐI! Đã xuất ${window.uniqueRecords.size} lệnh.`);
};

console.log("🟢 BOT GHI HÌNH ĐÃ CHẠY! BẠN HÃY DÙNG CHUỘT CUỘN SỔ LỆNH LÊN XUỐNG ĐI NHÉ.");


# Order Book Data Collection

## Overview

This project uses a browser-based data collection script to capture intraday order book transaction records from the FireAnt trading interface for research and quantitative analysis purposes.

The objective is to reconstruct order flow and market microstructure dynamics that are not directly available through standard historical OHLCV datasets.

---

## Collection Process

### Step 1: Open Order Book

1. Access the target stock on FireAnt.
2. Open the detailed order book / matched orders panel.
3. Open the browser Developer Console (`F12`).

### Step 2: Execute Data Capture Script

Paste the provided JavaScript collector into the browser console.

The script performs the following tasks:

* Creates a floating control button on the page.
* Continuously scans visible order book rows every 200 milliseconds.
* Detects records containing timestamp information (`HH:MM:SS`).
* Stores unique transactions in memory.
* Prevents duplicate captures using a composite key:

  ```
  timestamp + row content
  ```

### Step 3: Manual Scrolling

Since FireAnt loads historical records dynamically, the user manually scrolls through the order book.

As new rows become visible:

* The script automatically captures them.
* Previously captured rows are ignored.
* The total number of unique records is displayed in real time.

### Step 4: Export Data

After reaching the desired historical depth:

1. Click the export button.
2. The collector stops scanning.
3. All captured records are combined into a single HTML/text file.
4. The file is downloaded locally.

Example output:

```text
CTD_Full_Data_Manual.txt
```

---

## Captured Information

Depending on the FireAnt layout, each record may contain:

* Execution time
* Matched price
* Matched volume
* Buy/Sell indicator
* Additional order flow metadata

---

## Current Limitations

* Requires manual scrolling.
* Depends on FireAnt front-end structure.
* DOM class changes may require script updates.
* Collection speed is limited by browser rendering.
* Not suitable for real-time low-latency trading systems.

---

## Future Improvements

Planned upgrades include:

* Automated scrolling
* Direct API integration
* Incremental database storage
* Real-time order flow streaming
* Multi-stock parallel collection
* Market microstructure feature generation

---

## Research Applications

The collected order book data can be used to develop:

* Order Book Imbalance indicators
* Order Flow Momentum signals
* Liquidity Vacuum detection
* Absorption analysis
* Spoofing detection
* Machine Learning alpha factors
* Intraday market microstructure studies

