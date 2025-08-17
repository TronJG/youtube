# YouTube Downloader – FastAPI + yt-dlp

## Cách chạy (Windows / macOS / Linux)

1) Cài Python 3.9+ (đã có 3.12 càng tốt).
2) Mở Terminal / CMD, cd tới thư mục này, rồi tạo venv (khuyến nghị):
```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```
3) Cài thư viện:
```
pip install -r requirements.txt
```
> **Gợi ý:** Một số định dạng cần `ffmpeg` để hợp nhất video+audio. Cài ffmpeg rồi thêm vào PATH (Windows có thể dùng: https://www.gyan.dev/ffmpeg/builds/). Không bắt buộc cho các định dạng progressive mp4.

4) Chạy server:
```
uvicorn app:app --reload
```
Server sẽ chạy tại http://127.0.0.1:8000

5) Mở file `frontend/index.html` bằng trình duyệt. (Hoặc dùng Live Server / http-server).
   - Dán link YouTube → **Lấy thông tin** → chọn **Tải**.

## Endpoint
- `GET /api/info?url=...` → trả về thông tin video + danh sách định dạng.
- `GET /api/download?url=...&format_id=...` → tải file tương ứng (nếu bỏ `format_id` sẽ tải tốt nhất mp4).

## Lưu ý pháp lý
Chỉ sử dụng để tải nội dung **được phép** theo điều khoản của YouTube và luật sở tại. Bạn chịu trách nhiệm với việc sử dụng công cụ này.