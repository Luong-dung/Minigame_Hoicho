# Game 2 - Bắt chuột dưới cốc

Minigame chạy trong trình duyệt, dùng Python để xử lý luật chơi:

Người chơi chọn một trong bốn bậc cố định hoặc chế độ đặc biệt **Chuột đào tẩu**.
Số cốc và số lượt do server quyết định.

## Bốn bậc độ khó

| Bậc | Tên | Số cốc | Di chuyển sau mỗi lần mở trượt | Lượt tối đa |
|---|---|---:|---|---:|
| 1 | Chuột thường | 5 | Ngẫu nhiên sang 1 ô liền kề | 4 |
| 2 | Chuột thông minh | 8 | Né khi còn đường thoát, đi 1 ô | 12 |
| 3 | Chuột trùm | 8 | Né, đi theo chu kỳ 1 → 2 ô | 13 |
| 4 | Chuột siêu trùm | 8 | Né, đi theo chu kỳ 1 → 2 → 3 ô | 14 |
| 5 (đặc biệt) | Chuột đào tẩu | 7 | Người chơi làm chuột, chạy 1 ô sau mỗi lần máy mở trượt | 10 lần săn |

## Luật chơi các bậc 1–4

- Cốc được đánh số từ trái sang phải, bắt đầu từ 1.
- Người chơi mở một cốc mỗi lượt. Chuột chỉ di chuyển nếu mở trượt và ván còn lượt.
- Chuột chọn một hướng cho mỗi lần di chuyển, đi đủ số bước; chạm biên thì
  bật ngược vào trong. Chu kỳ bắt đầu ở 1 ô khi tạo ván mới.
- Giao diện hiển thị số ô chuột sẽ đi nếu lần mở tiếp theo trượt.
- Bắt được chuột thì thắng; hết lượt mà chưa bắt được thì thua và hiện vị trí chuột.

Ở bậc 1, chuột có vị trí thật được chọn ngẫu nhiên từ đầu ván. Mở đúng cốc
là thắng; mở trượt thì chuột chọn ngẫu nhiên một ô liền kề hợp lệ.

Ở bậc 2–4, server giữ tập hợp tất cả vị trí chuột có thể đang ở, thay vì
chốt một vị trí từ đầu. Khi mở cốc, server loại vị trí đó khỏi tập hợp.
Nếu không còn vị trí nào khác, người chơi thắng. Nếu còn, chuột né được và
các vị trí còn lại được chuyển theo luật di chuyển để tạo tập hợp cho lượt sau.
Cốc vừa mở vẫn có thể chứa chuột ở lượt sau và có thể được chọn lại.

Muốn thắng các bậc này, người chơi cần ép mọi khả năng về một cốc.
Vị trí và số lượng vị trí khả thi không được gửi cho trình duyệt khi ván đang diễn ra.
Các bậc 2, 3, 4 đã được kiểm chứng có chiến thuật đảm bảo thắng, với số lượt
tối thiểu lần lượt là **12, 13, 14**. Không liệt kê chuỗi mở cốc ở đây để tránh lộ lời giải.

## Đặc biệt: Chuột đào tẩu

Chọn **Đặc biệt — Chuột đào tẩu** để đổi vai: bạn làm chuột, máy làm thợ săn.

- Có 7 cốc. Chọn chỗ trốn ban đầu, rồi bấm **Máy săn** để máy mở một cốc.
- Nếu máy mở trúng vị trí bạn, bạn thua. Nếu thoát, chọn một cốc liền kề để chạy
  đúng 1 ô; không được đứng yên. Sau đó bấm **Máy săn** cho lần săn tiếp theo.
- Sống sót qua 10 lần mở cốc là thắng; không cần chạy sau lần thứ 10.
- Đầu ván, máy chọn một nhánh và giữ nguyên cả ván, mỗi nhánh có xác suất 20%:
  quét 2→6 rồi 6→2; quét 2→6 hai lần; quét 6→2 rồi 2→6;
  quét 6→2 hai lần; hoặc săn ngẫu nhiên.
- Bốn chuỗi quét đều đảm bảo bắt chuột trong tối đa 10 lượt khi chuột bắt buộc
  chạy 1 ô sau mỗi lần trượt. Nhánh ngẫu nhiên chọn đều trong cả 7 cốc ở mỗi lượt,
  có thể chọn lặp lại. 20% chọn nhánh ngẫu nhiên không phải tỷ lệ người chơi thắng.
- Máy không dùng vị trí thật của bạn để chọn cốc. Chiến thuật không đổi hoặc
  tính lại giữa ván; lựa chọn nhánh được giữ riêng trên server.
- Giao diện hiển thị vị trí của bạn, cốc máy vừa mở và các cốc có thể chạy tới;
  không tiết lộ các chuỗi săn, xác suất chọn nhánh hoặc cốc máy sẽ chọn tiếp theo.
  Chi tiết chiến thuật ở README dành cho người tổ chức.

## Chạy game

Yêu cầu Python 3.9 trở lên. Không cần cài thêm thư viện.

Mở PowerShell tại thư mục `game2_mount`:

```powershell
python .\minigame.py
```

Mở trình duyệt tại <http://127.0.0.1:8001>.

Có thể đổi cổng:

```powershell
python .\minigame.py --port 8080
```

Luật chơi được thực hiện trong `minigame.py`; giao diện ở `frontend/index.html`
chỉ gửi lựa chọn của người chơi tới API Python và hiển thị kết quả.

Sau khi sửa code Python, khởi động lại server. Sau khi sửa giao diện, tải lại trang.

## Kiểm tra

Chạy tại thư mục `game2_mount`:

```powershell
python -m unittest -v test_minigame
```

Các bài kiểm tra trong `test_minigame.py` bao gồm cấu hình bốn bậc, dữ liệu
đầu vào, thắng/thua, giới hạn lượt, bật ngược ở biên, nhịp di chuyển và tìm
chiến thuật ngắn nhất bằng duyệt các trạng thái khả thi.
Chế độ đào tẩu được kiểm tra thêm bốn chuỗi săn, nhánh ngẫu nhiên, thứ tự
thao tác, di chuyển hợp lệ và kết quả ở lần săn cuối.

## API

Mỗi phiên trình duyệt có ván riêng, nhận diện bằng cookie.

| API | Chức năng |
|---|---|
| `GET /api/state` | Lấy trạng thái ván hiện tại |
| `POST /api/new-game` | Tạo ván với JSON `{"level": 1}`; bậc 1–4, chế độ đào tẩu là 5 |
| `POST /api/open` | Mở cốc với JSON `{"cup": 0}`; chỉ số API bắt đầu từ 0 |
| `POST /api/escape` | Đào tẩu: `{"action":"choose","cup":0}`, `{"action":"hunt"}` hoặc `{"action":"move","cup":1}` |

API tạo ván dùng `level`; không còn dùng `mode` và `cup_count` để chọn cấu hình.
