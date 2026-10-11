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
tải lại trang. Không cần sửa mã nguồn. Sau khi thêm hoặc thay ảnh, khởi động
lại server để cập nhật kết quả kiểm tra các mảnh quá giống nhau.

## Cách chơi

- Chọn ảnh và độ khó theo bảng bên dưới. Kích thước mỗi bậc được cố định.
- Ở các bậc thường, xem ảnh đầy đủ trước khi chơi. Bấm **Bắt đầu** mới trộn
  bàn và chạy đồng hồ đếm ngược. Chế độ Tắt đèn có thêm 10 giây ghi nhớ bàn đã trộn.
- Bấm **Ảnh ngẫu nhiên** để chuyển sang một ảnh khác trong danh sách.
- Bấm vào mảnh ảnh cạnh ô trống để di chuyển.
- Ô trống có nền sọc và nhãn **Ô TRỐNG**, nên vẫn dễ nhận biết khi ảnh có phông trắng.
- Khi server khởi động, chương trình quét trước các cặp mảnh của từng ảnh
  và kích thước. Frontend khóa các bậc không hợp lệ; Dễ, Trung bình và Tắt đèn
  cùng dùng kết quả kiểm tra 3×3.
- Có thể dùng các phím mũi tên để di chuyển ô trống theo đúng hướng mũi tên.
- Ở các bậc thường, bấm **Gợi ý** để xem ảnh gốc trong 3 giây; mỗi ván tối đa
  3 lần. Chế độ Tắt đèn dùng nút **Bật đèn** theo luật riêng bên dưới.
- Khi đang chơi, ảnh và độ khó được khóa. Nút **Kết thúc / Chuẩn bị ván mới**
  bỏ ván hiện tại và trở về bước xem ảnh; cần bấm **Bắt đầu** để chơi tiếp.
- Nút **Đầu hàng** kết thúc ván và hiển thị đáp án.
- Thống kê số nước đi và thời gian còn lại được hiển thị ở bảng điều khiển.
- Hết giờ thì kết thúc ván, khóa thao tác và hiển thị ảnh hoàn chỉnh.
  Thời gian vẫn trôi khi chuyển tab; thao tác được kiểm tra hạn trước khi tính nước đi.

## Cấu hình độ khó

| Bậc | Bàn | Độ sâu trộn | Thời hạn |
|---|---|---|---:|
| Dễ | 3×3 | Chính xác 6–10 nước tối ưu | 60 giây |
| Trung bình | 3×3 | Chính xác 14–18 nước tối ưu | 90 giây |
| Khó | 3×4 | Trộn 30 nước hợp lệ; khoảng cách Manhattan ít nhất 12 | 120 giây |
| Rất khó | 4×4 | Trộn 50 nước hợp lệ; khoảng cách Manhattan ít nhất 20 | 180 giây |

Hai bậc 3×3 dùng tìm kiếm theo chiều rộng từ bàn hoàn chỉnh để chọn bàn đúng
độ sâu. Các bậc lớn trộn bằng nước đi hợp lệ, tránh đảo ngược ngay nước vừa đi.
Khoảng cách Manhattan là cận dưới số nước cần giải, không phải số nước tối ưu.
Mọi bàn được tạo đều giải được. Thời hạn là cấu hình thử nghiệm cho hội trại,
có thể chỉnh trong `frontend/puzzle.js` sau khi cho người mới chơi thử.

## Chế độ đặc biệt: Tắt đèn — Ghép bằng trí nhớ

Chọn **Đặc biệt: Tắt đèn** trong danh sách độ khó:

- Bàn 3×3 có độ sâu chính xác 6–10 nước tối ưu.
- Bấm **Bắt đầu** để xem bàn đã trộn trong 10 giây; chưa được di chuyển.
- Sau đó các mảnh bị úp, ô trống vẫn hiện rõ. Có 90 giây để ghép bằng trí nhớ.
- Có 3 lần **Bật đèn**, mỗi lần hiện toàn bộ bàn đang chơi trong 2 giây.
  Vẫn có thể di chuyển khi đèn sáng; đồng hồ không dừng. Không dùng gợi ý ảnh gốc.
- Thắng, hết giờ hoặc đầu hàng đều hiện ảnh hoàn chỉnh.
- Khi chuyển tab, thời gian ghi nhớ và chơi vẫn trôi; quay lại không được thêm thời gian.

## Kiểm tra

Tại thư mục `game1_N_puzzle`, chạy bằng Node.js (không cần cài thư viện):

```powershell
node --test test_puzzle.js test_game.js
```

## Cấu trúc

```text
game1_N_puzzle/
├── minigame.py
├── frontend/
│   ├── index.html
│   ├── puzzle.js
│   └── game.js
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

`frontend/puzzle.js` chứa cấu hình và logic tạo bàn; `frontend/game.js`
quản lý xem ảnh, tải ảnh, ván chơi và đếm ngược. Mảnh ảnh được cắt và lưu một
lần khi chuẩn bị ván, không cắt lại theo từng nước đi. Kết quả tải ảnh cũ bị
bỏ qua khi người chơi đổi ảnh nhanh.
