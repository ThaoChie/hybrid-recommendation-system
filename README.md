# AuraShop — Hybrid Recommendation E-Commerce

Dự án Hệ thống Thương mại Điện tử gợi ý sản phẩm thông minh (Content-Based Filtering + Popularity Scoring).

Vì yêu cầu phần **AI Model** chạy trực tiếp trên máy thật (không dùng Docker để tránh nặng máy), hướng dẫn này được thiết kế **từ con số 0** cho một máy tính mới hoàn toàn, chỉ có VS Code và Docker Desktop.

---

## KIẾN TRÚC HỆ THỐNG
1. **Frontend + Backend (Django):** Chạy trong Docker (cổng `8080`).
2. **Database (MySQL 8.0):** Chạy trong Docker (cổng `3307`).
3. **AI Model (FastAPI):** Chạy **trực tiếp** trên máy thật bằng Python (cổng `8000`).

---

## HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN

Để chạy được dự án, bạn sẽ làm theo 3 bước lớn: Khởi động Database (bằng Docker), Khởi động AI (bằng Python), và Khởi động Web (bằng Docker). Dưới đây là hướng dẫn chi tiết cho cả Windows và macOS.

### BƯỚC 1: Cài đặt Python 3.11 (Chỉ làm 1 lần)
Máy mới chưa có môi trường, bắt buộc bạn phải cài Python để chạy AI Model.

**Dành cho Windows:**
1. Tải Python 3.11 tại: https://www.python.org/downloads/windows/
2. Chọn "Windows installer (64-bit)".
3. Mở file cài đặt, **BẮT BUỘC TICK VÀO Ô "Add Python to PATH"** ở dưới cùng.
4. Bấm "Install Now" và đợi cài xong.

**Dành cho macOS:**
1. Mở Terminal và cài Homebrew (nếu chưa có):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Cài Python 3.11 qua brew:
   ```bash
   brew install python@3.11
   ```

---

### BƯỚC 2: Clone Code và Khởi động Database (MySQL)

1. Mở **VS Code**, chọn **Terminal -> New Terminal** và gõ lệnh tải code:
   ```bash
   git clone <đường-dẫn-repo-github> DACN
   cd DACN
   ```

2. Đảm bảo phần mềm **Docker Desktop** đã được mở và đang chạy.

3. Khởi động MySQL Database:
   ```bash
   docker compose up db -d
   ```
   *Đợi khoảng 30 giây để Database khởi động hoàn tất.*

---

### BƯỚC 3: Khởi động AI Model Service (Chạy trực tiếp trên máy)

Mở một **Terminal mới** trong VS Code (bấm phím dấu cộng `+` trên bảng Terminal), sau đó làm theo hệ điều hành của bạn:

**👉 Nếu bạn dùng Windows (PowerShell/CMD):**
```powershell
cd model

# Tạo và kích hoạt môi trường ảo (Virtual Environment)
python -m venv venv2
.\venv2\Scripts\activate

# Cài đặt thư viện AI (Có thể mất 2-5 phút)
pip install -r requirements.txt
pip install "numpy<2"

# Sinh mảng dữ liệu (Chỉ cần chạy lệnh này ở lần đầu tiên mở project trên máy mới)
python train_offline.py

# Bật API Server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**👉 Nếu bạn dùng macOS:**
```bash
cd model

# Tạo và kích hoạt môi trường ảo (Virtual Environment)
python3.11 -m venv venv2
source venv2/bin/activate

# Cài đặt thư viện AI (Có thể mất 2-5 phút)
pip install -r requirements.txt
pip install "numpy<2"

# Sinh mảng dữ liệu (Chỉ cần chạy lệnh này ở lần đầu tiên mở project trên máy mới)
python3.11 train_offline.py

# Bật API Server
python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

⏳ *Khi terminal hiện dòng chữ **"All engines ready. Total products: 8000"**, hãy CỨ ĐỂ YÊN TERMINAL NÀY CHẠY, không được tắt.*

---

### BƯỚC 4: Khởi động Website (Django)
Mở một **Terminal mới** nữa trong VS Code (để giữ AI đang chạy) và đảm bảo bạn đang ở thư mục gốc `DACN`, gõ lệnh:

```bash
docker compose up web -d
```
Docker sẽ tự động tải thư viện, cấu hình database và bật website. 

---

## 🌐 TRUY CẬP VÀ SỬ DỤNG

Sau khi cả 3 bước trên hoàn thành, truy cập vào trình duyệt:
- **Web Frontend (Trang mua sắm):** [http://localhost:8080](http://localhost:8080)
- **Web Admin (Quản lý):** [http://localhost:8080/admin/](http://localhost:8080/admin/)
- **API AI (Test Recommendation):** [http://localhost:8000/docs](http://localhost:8000/docs)

### Import Dữ liệu Mẫu
Nếu database của bạn đang trống (mới tinh), hãy mở terminal thứ 3 và nạp dữ liệu:

1. **Khởi tạo danh mục:**
   - Mac/Linux: `curl -X POST http://localhost:8080/api/v1/products/init_categories/`
   - Windows PowerShell: `Invoke-RestMethod -Method POST -Uri "http://localhost:8080/api/v1/products/init_categories/"`

2. **Import dữ liệu Sản phẩm (Ví dụ Làm đẹp - ID 1):**
   - Mac/Linux:
     ```bash
     curl -X POST http://localhost:8080/api/v1/products/import_csv/ -F "file=@./model/data/tiki_cham_soc_da_mat_cleaned_final.csv" -F "category_id=1"
     ```
   - Windows PowerShell:
     ```powershell
     $form = @{ file = Get-Item ".\model\data\tiki_cham_soc_da_mat_cleaned_final.csv"; category_id = "1" }
     Invoke-RestMethod -Method POST -Uri "http://localhost:8080/api/v1/products/import_csv/" -Form $form
     ```

## 🛠 XỬ LÝ LỖI (TROUBLESHOOTING)
- **Lỗi `Connection refused :3307`:** Database MySQL khởi động chưa xong. Hãy đợi thêm 30s.
- **Lỗi `Numpy is not available` ở Bước 3:** Lệnh cài Numpy bị lỗi version, đảm bảo bạn đã gõ đúng `pip install "numpy<2"`.
- **Lỗi Website không truy cập được (Port 8080 bị chiếm):** Chạy `docker compose down`, tắt các app đang chiếm port và chạy lại `docker compose up web -d`.
