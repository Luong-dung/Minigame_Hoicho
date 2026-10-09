# Minigame N-puzzle ảnh

Minigame xếp hình chạy trực tiếp trên trình duyệt. Chương trình tự động đọc
tất cả ảnh trong thư mục `image/`, cắt ảnh thành các mảnh và tạo bàn chơi
N-puzzle. Số lượng ảnh không cố định; mỗi ảnh có thể có kích thước và tỉ lệ
khác nhau.

## Yêu cầu

- Python 3.9 trở lên
- Trình duyệt hiện đại có hỗ trợ JavaScript và Canvas

Chương trình chỉ sử dụng thư viện chuẩn của Python, không cần cài thêm package.

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

- Chọn ảnh và độ khó: `3x3`, `3x4`, `4x4`, `4x5` hoặc `5x5`.
- Bấm **Ảnh ngẫu nhiên** để chuyển sang một ảnh khác trong danh sách.
- Bấm vào mảnh ảnh cạnh ô trống để di chuyển.
- Có thể dùng các phím mũi tên.
- Bấm **Gợi ý** để xem ảnh gốc trong 3 giây; mỗi ván được tối đa 3 lần.
- Nút **Trộn ảnh mới** bắt đầu ván mới.
- Nút **Xem đáp án** đưa bàn chơi về trạng thái hoàn chỉnh.
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
