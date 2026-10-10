# Game 2 - Bắt chuột dưới cốc

Minigame chạy trong trình duyệt, dùng Python để xử lý luật chơi:

- Có thể chọn từ 3 đến 12 chiếc cốc xếp thành một hàng.
- Chuột bắt đầu ẩn dưới một cốc ngẫu nhiên.
- Nếu mở đúng cốc, người chơi thắng.
- Nếu mở sai, chuột di chuyển sang một trong các ô kề bên.
- Chế độ thường có số lượt ngẫu nhiên từ `n` đến `n+2`; chế độ smart có
  `2n - 4` lượt (`n` là số cốc).
- Chọn chế độ **Ronaldo hay Messi** để chuột luôn chọn ô kề bên có lợi nhất,
  tránh xa vị trí cốc người chơi vừa mở.
- Ở chế độ này, cốc người chơi vừa chọn sẽ bị khóa trong lượt đó. Danh sách
  vị trí chuột hiện tại được ánh xạ sang các ô `+1` hoặc `-1`, rồi loại cốc
  vừa chọn. Khi người chơi đổi sang cốc khác, cốc cũ được mở khóa và có thể
  xuất hiện lại trong danh sách. Khi danh sách mới rỗng, game kết luận người
  chơi đã bắt được chuột.
- Lịch sử di chuyển được khóa và không hiển thị cho người chơi để tránh lộ
  quy luật của chế độ chuột thông minh.
- Chế độ smart không hiển thị số vị trí chuột còn khả dĩ.

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
