"""Serve the cup-and-mouse browser game.

Run from this directory with:

    python minigame.py

Then open http://127.0.0.1:8001 in a browser.
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
from collections import OrderedDict
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "frontend" / "index.html"
DEFAULT_CUP_COUNT = 6
MIN_CUP_COUNT = 3
MAX_CUP_COUNT = 12
MODES = {"random", "smart"}
MAX_BODY_BYTES = 4096
MAX_SESSIONS = 500


def as_int(value: object, name: str) -> int:
    """Chỉ nhận số nguyên thật (không nhận bool, float, chuỗi)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} phải là số nguyên.")
    return value


class Game:
    """Luật chơi và trạng thái ván chơi, giữ trên server.

    Quy ước thời gian: ở lượt t người chơi mở một cốc, đúng lúc đó chuột đang
    ở vị trí p_t. Nếu cốc trùng p_t thì thắng, nếu không chuột chạy sang một ô
    kề để thành p_{t+1}.
    """

    def __init__(self) -> None:
        self.cup_count = DEFAULT_CUP_COUNT
        self.reset()

    def reset(self, mode: str = "random", cup_count: int = DEFAULT_CUP_COUNT) -> None:
        if mode not in MODES:
            raise ValueError("Chế độ không hợp lệ.")
        if not MIN_CUP_COUNT <= cup_count <= MAX_CUP_COUNT:
            raise ValueError(
                f"Số cốc phải từ {MIN_CUP_COUNT} đến {MAX_CUP_COUNT}."
            )
        self.cup_count = cup_count
        self.mode = mode
        self._max_moves = (
            2 * cup_count - 4
            if mode == "smart"
            else random.randint(cup_count, cup_count + 2)
        )
        self.moves = 0
        self.finished = False
        self.won = False
        self.revealed_position: int | None = None
        # Chế độ random: vị trí thật của chuột ở lượt kế tiếp.
        self.mouse_position = random.randrange(cup_count)
        # Chế độ smart: mọi vị trí chuột có thể đang ở ở lượt kế tiếp
        # (chuột chỉ "chốt" vị trí khi ván kết thúc).
        self.candidates: set[int] = set(range(cup_count))

    @property
    def max_moves(self) -> int:
        return self._max_moves

    def _neighbors(self, position: int) -> list[int]:
        return [
            p for p in (position - 1, position + 1) if 0 <= p < self.cup_count
        ]

    def _finish(self, won: bool, position: int, message: str, cup: int) -> dict[str, object]:
        self.finished = True
        self.won = won
        self.revealed_position = position
        return {
            "won": won,
            "finished": True,
            "moves": self.moves,
            "opened_cup": cup,
            "mouse_position": position,
            "message": message,
        }

    def _miss(self, message: str, cup: int) -> dict[str, object]:
        return {
            "won": False,
            "finished": False,
            "moves": self.moves,
            "opened_cup": cup,
            "mouse_position": None,
            "message": message,
        }

    def _lose(self, position: int, cup: int) -> dict[str, object]:
        return self._finish(
            False,
            position,
            f"Hết {self.max_moves} lượt! Chuột đã thoát, bạn thua.",
            cup,
        )

    def open_cup(self, cup: int) -> dict[str, object]:
        if not 0 <= cup < self.cup_count:
            raise ValueError("Cốc không hợp lệ.")
        if self.finished:
            raise ValueError("Ván chơi đã kết thúc.")

        self.moves += 1
        if self.mode == "smart":
            return self._open_smart(cup)
        return self._open_random(cup)

    def _open_random(self, cup: int) -> dict[str, object]:
        position = self.mouse_position
        if cup == position:
            return self._finish(True, position, "Bắt được chuột rồi! Bạn thắng!", cup)
        if self.moves >= self.max_moves:
            return self._lose(position, cup)
        self.mouse_position = random.choice(self._neighbors(position))
        return self._miss("Không có chuột! Chuột đã chạy sang một ô bên cạnh.", cup)

    def _open_smart(self, cup: int) -> dict[str, object]:
        remaining = self.candidates - {cup}
        if not remaining:
            # Mọi vị trí có thể đều bị cốc này chặn: chuột chắc chắn ở đây.
            return self._finish(
                True,
                cup,
                "Bắt được chuột rồi! Không còn ô nào để chuột chạy.",
                cup,
            )
        if self.moves >= self.max_moves:
            # Chốt chuột ở một vị trí hợp lệ mà người chơi đã bỏ lỡ.
            return self._lose(random.choice(sorted(remaining)), cup)
        self.candidates = {
            n for p in remaining for n in self._neighbors(p)
        }
        return self._miss("Chuột thông minh đã đổi vị trí.", cup)

    def state(self) -> dict[str, object]:
        return {
            "cup_count": self.cup_count,
            "max_moves": self.max_moves,
            "mode": self.mode,
            "moves": self.moves,
            "finished": self.finished,
            "won": self.won,
            "mouse_position": self.revealed_position if self.finished else None,
        }


# Mỗi trình duyệt (cookie "sid") có một ván riêng.
sessions: OrderedDict[str, Game] = OrderedDict()
sessions_lock = Lock()


class GameHandler(BaseHTTPRequestHandler):
    sid: str | None = None

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        if self.sid:
            self.send_header(
                "Set-Cookie", f"sid={self.sid}; Path=/; HttpOnly; SameSite=Strict"
            )
        self.end_headers()
        self.wfile.write(body)

    def _get_game(self) -> Game:
        """Lấy ván của phiên hiện tại. Phải gọi khi đang giữ sessions_lock."""
        morsel = SimpleCookie(self.headers.get("Cookie", "")).get("sid")
        sid = morsel.value if morsel else None
        game = sessions.get(sid) if sid else None
        if game is None:
            sid = secrets.token_hex(16)
            game = Game()
            sessions[sid] = game
            while len(sessions) > MAX_SESSIONS:
                sessions.popitem(last=False)
        else:
            sessions.move_to_end(sid)
        self.sid = sid
        return game

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Content-Length không hợp lệ.") from None
        if not 0 <= length <= MAX_BODY_BYTES:
            raise ValueError("Nội dung yêu cầu không hợp lệ.")
        data = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(data, dict):
            raise ValueError("JSON phải là một đối tượng.")
        return data

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            body = INDEX_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/state":
            with sessions_lock:
                state = self._get_game().state()
            self._send_json(state)
            return
        self._send_json({"error": "Không tìm thấy trang."}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path not in ("/api/new-game", "/api/open"):
                self._send_json({"error": "Không tìm thấy API."}, status=404)
                return
            data = self._read_json()
            if path == "/api/new-game":
                mode = data.get("mode", "random")
                if not isinstance(mode, str):
                    raise ValueError("Chế độ không hợp lệ.")
                cup_count = as_int(data.get("cup_count", DEFAULT_CUP_COUNT), "Số cốc")
                with sessions_lock:
                    game = self._get_game()
                    game.reset(mode, cup_count)
                    result = game.state()
            else:
                if "cup" not in data:
                    raise ValueError("Thiếu cốc cần mở.")
                cup = as_int(data["cup"], "Cốc")
                with sessions_lock:
                    result = self._get_game().open_cup(cup)
            self._send_json(result)
        except ValueError as error:  # gồm cả JSONDecodeError
            self._send_json({"error": str(error)}, status=400)
        except Exception:
            self._send_json({"error": "Lỗi máy chủ."}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the cup-and-mouse minigame.")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    if not INDEX_FILE.is_file():
        raise SystemExit(f"Frontend entrypoint does not exist: {INDEX_FILE}")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), GameHandler)
    print(f"Open http://127.0.0.1:{args.port} in your browser (Ctrl+C to stop).")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGame server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()