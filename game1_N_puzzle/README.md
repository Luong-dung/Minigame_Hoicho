# Minigame N-puzzle ảnh

Minigame xếp hình chạy trực tiếp trên trình duyệt. Chương trình tự động đọc
tất cả ảnh trong thư mục `image/`, cắt ảnh thành các mảnh và tạo bàn chơi
N-puzzle. Số lượng ảnh không cố định; mỗi ảnh có thể có kích thước và tỉ lệ
khác nhau.

## Yêu cầu

- Python 3.9 trở lên
- Trình duyệt hiện đại có hỗ trợ JavaScript và Canvas
- Node.js hỗ trợ `node --test` nếu muốn chạy kiểm tra tự động

Server kiểm tra các mảnh giống nhau khi khởi động, hỗ trợ PNG RGB/RGBA,
8 bit, không interlace. PNG khác định dạng này có thể khiến server không
khởi động được. Ảnh không có chữ ký PNG (như JPEG, GIF, WebP) vẫn được
phục vụ nhưng không được kiểm tra các mảnh giống nhau.

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
  và kích thước. Frontend khóa các bậc không hợp lệ; Dễ và Trung bình dùng
  kết quả kiểm tra 3×3, Rất khó và Tắt đèn dùng kết quả kiểm tra 4×4.
- Có thể dùng các phím mũi tên để di chuyển ô trống theo đúng hướng mũi tên.
- Ở các bậc thường, bấm **Gợi ý** để xem ảnh gốc trong 3 giây; mỗi ván tối đa
  3 lần. Chế độ Tắt đèn dùng nút **Bật đèn** theo luật riêng bên dưới.
- Khi đang ghi nhớ bàn Tắt đèn hoặc đang chơi, ảnh và độ khó được khóa.
  Nút **Kết thúc / Chuẩn bị ván mới**
  bỏ ván hiện tại và trở về bước xem ảnh; cần bấm **Bắt đầu** để chơi tiếp.
- Nút **Đầu hàng** kết thúc ván và hiển thị đáp án.
- Thống kê số nước đi và thời gian còn lại được hiển thị ở bảng điều khiển.
- Hết giờ thì kết thúc ván, khóa thao tác và hiển thị ảnh hoàn chỉnh.
  Thời gian vẫn trôi khi chuyển tab; thao tác được kiểm tra hạn trước khi tính nước đi.

## Cấu hình độ khó

| Chế độ (`key`) | Bàn | Độ sâu trộn | Thời gian chơi | Hỗ trợ |
|---|---|---|---:|---|
| Dễ (`easy`) | 3×3 | Chính xác 6–10 nước tối ưu | 60 giây | 3 gợi ý, 3 giây/lần |
| Trung bình (`medium`) | 3×3 | Chính xác 14–18 nước tối ưu | 30 giây | 3 gợi ý, 3 giây/lần |
| Khó (`hard`) | 3×4 | Trộn 30 nước hợp lệ; Manhattan ≥ 12 | 90 giây | 3 gợi ý, 3 giây/lần |
| Rất khó (`very-hard`) | 4×4 | Trộn 50 nước hợp lệ; Manhattan ≥ 20 | 120 giây | 3 gợi ý, 3 giây/lần |
| Tắt đèn (`blackout`) | 4×4 | Trộn 10 nước hợp lệ; Manhattan ≥ 6 | 90 giây, sau 10 giây ghi nhớ | 3 lần bật đèn, 2 giây/lần |

Hai bậc 3×3 dùng tìm kiếm theo chiều rộng từ bàn hoàn chỉnh để chọn bàn đúng
độ sâu. Các bậc lớn trộn bằng nước đi hợp lệ, tránh đảo ngược ngay nước vừa đi.
Khoảng cách Manhattan là cận dưới số nước cần giải, không phải số nước tối ưu.
Mọi bàn được tạo đều giải được. Thời hạn là cấu hình thử nghiệm cho hội trại,
có thể chỉnh trong `frontend/puzzle.js` sau khi cho người mới chơi thử.
Số nước trộn là bước tạo bàn, không phải giới hạn số nước của người chơi;
ván chơi chỉ giới hạn thời gian. Các bàn lớn được thử tạo tối đa 200 lần
để đạt ngưỡng Manhattan; nếu không đạt, giao diện yêu cầu bấm Bắt đầu để thử lại.

## Chế độ đặc biệt: Tắt đèn — Ghép bằng trí nhớ

Chọn **Đặc biệt: Tắt đèn** trong danh sách độ khó:

- Bàn 4×4, trộn 10 nước hợp lệ và yêu cầu khoảng cách Manhattan ít nhất 6.
  Số nước tối ưu nằm trong khoảng 6–10; không trộn sâu như mức Rất khó.
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

Kiểm tra gồm độ sâu tối ưu 3×3, tính giải được và ngưỡng Manhattan của bàn lớn,
tải ảnh cũ, hết giờ, thắng/đầu hàng, tái sử dụng mảnh ảnh và các pha ghi nhớ,
úp mảnh, bật đèn của chế độ đặc biệt.

## Cấu trúc

```text
game1_N_puzzle/
├── minigame.py
├── frontend/
│   ├── index.html
│   ├── puzzle.js
│   └── game.js
├── README.md
├── test_puzzle.js
├── test_game.js
└── image/
    ├── bakhi.png
    ├── hus.png
    ├── khoa.png
    └── vnu.png
```

## Ghi chú kỹ thuật

| Đường dẫn | Chức năng |
|---|---|
| `/` | Giao diện chơi |
| `/api/images` | Danh sách URL ảnh, quét thư mục mỗi lần gọi |
| `/api/validation` | Các kích thước bị chặn theo tên ảnh, tính lúc server khởi động |
| `/image/<tên-ảnh>` | File ảnh |
| `/frontend/puzzle.js`, `/frontend/game.js` | Script của trò chơi |

Luật xếp hình, trạng thái ván và đồng hồ chạy trong trình duyệt; Python
phục vụ giao diện, ảnh và kết quả kiểm tra ảnh. Việc cắt ảnh dùng Canvas,
không thay đổi file ảnh gốc.

`frontend/puzzle.js` chứa cấu hình và logic tạo bàn; `frontend/game.js`
quản lý xem ảnh, tải ảnh, ván chơi và đếm ngược. Mảnh ảnh được cắt và lưu một
lần khi chuẩn bị ván, không cắt lại theo từng nước đi. Kết quả tải ảnh cũ bị
bỏ qua khi người chơi đổi ảnh nhanh.
