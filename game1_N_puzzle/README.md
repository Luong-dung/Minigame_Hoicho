# Minigame N-puzzle ảnh

Minigame xếp hình chạy trực tiếp trên trình duyệt. Chương trình tự động đọc
tất cả ảnh trong thư mục `image/`, cắt ảnh thành các mảnh và tạo bàn chơi
N-puzzle. Số lượng ảnh không cố định; mỗi ảnh có thể có kích thước và tỉ lệ
khác nhau.

## Yêu cầu

- Python 3.9 trở lên
- Trình duyệt hiện đại có hỗ trợ JavaScript và Canvas

Ảnh PNG được quét trước bằng thư viện chuẩn của Python khi server khởi động.
Các file JPEG cần dùng đúng định dạng JPEG; nếu chỉ đổi đuôi thành `.png` thì
server vẫn phục vụ ảnh nhưng không thể quét trước các mảnh của file đó.

## Chạy chương trình

Mở PowerShell tại thư mục này và chạy:

```powershell
python .\minigame.py
```

Mở trình duyệt tại [http://127.0.0.1:8000](http://127.0.0.1:8000).

Có thể chọn port khác:

```powershell
python .\minigame.py --port 8080
```

Dừng server bằng `Ctrl+C`.

## Thêm ảnh

Chép ảnh vào thư mục `image/`. Các định dạng ảnh được trình duyệt hỗ trợ
(`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, ...) sẽ được tự động liệt kê khi
tải lại trang. Không cần sửa mã nguồn.

## Cách chơi

- Chọn ảnh và độ khó: **Dễ** (`3×3`), **Trung bình** (`3×4`), **Khó** (`4×4`) hoặc **Rất khó** (`4×5`/`5×5`). Ở mức **Rất khó**, game tự chọn một kích thước hợp lệ.
- Bấm **Ảnh ngẫu nhiên** để chuyển sang một ảnh khác trong danh sách.
- Bấm vào mảnh ảnh cạnh ô trống để di chuyển.
- Ô trống có nền sọc và nhãn **Ô TRỐNG**, nên vẫn dễ nhận biết khi ảnh có phông trắng.
- Khi server khởi động, chương trình quét trước toàn bộ cặp mảnh của từng ảnh và kích thước. Frontend nhận danh sách này và khóa sẵn mức độ không hợp lệ; mức **Rất khó** tự chọn `4×5` hoặc `5×5` nếu kích thước đó hợp lệ.
- Có thể dùng các phím mũi tên để di chuyển ô trống theo đúng hướng mũi tên.
- Bấm **Gợi ý** để xem ảnh gốc trong 3 giây; mỗi ván được tối đa 3 lần.
- Nút **Trộn ảnh mới** bắt đầu ván mới.
- Nút **Đầu hàng** kết thúc ván và hiển thị đáp án.
- Thống kê số nước đi và thời gian được hiển thị ở bảng điều khiển.

## Cấu trúc

```text
minigame_N-puzzle/
├── minigame.py
├── frontend/
│   └── index.html
├── README.md
└── image/
    ├── bakhi.png
    ├── hus.png
    ├── khoa.png
    └── vnu.png
```

## Ghi chú kỹ thuật

Server Python đọc giao diện từ `frontend/index.html` và cung cấp giao diện tại `/`, API danh sách ảnh tại
`/api/images` và các file ảnh tại `/image/<tên-ảnh>`. Việc cắt ảnh được thực
hiện bằng Canvas trên trình duyệt; ảnh gốc không bị thay đổi.
# N-puzzle-game
