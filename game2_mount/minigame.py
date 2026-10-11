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
LEVELS = {
    1: ("Chuột thường", 5, 4, "random"),
    2: ("Chuột thông minh", 8, 12, "smart"),
    3: ("Chuột trùm", 8, 13, "boss"),
    4: ("Chuột siêu trùm", 8, 14, "super_boss"),
    5: ("Chuột đào tẩu", 7, 10, "escape"),
}
# Zero-based indices: sweep cups 2–6, or 6–2, twice.
_FORWARD = tuple(range(1, 6))
_BACKWARD = _FORWARD[::-1]
HUNTER_PATTERNS = (
    _FORWARD + _BACKWARD, _FORWARD + _FORWARD,
    _BACKWARD + _FORWARD, _BACKWARD + _BACKWARD,
)
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
        self.reset()

    def reset(self, level: int = 1) -> None:
        level = as_int(level, "Bậc độ khó")
        if level not in LEVELS:
            raise ValueError("Chọn bậc 1–4 hoặc chế độ đặc biệt 5.")
        self.level = level
        self.level_name, self.cup_count, self._max_moves, self.mode = LEVELS[level]
        self.moves = 0
        self.finished = False
        self.won = False
        self.revealed_position: int | None = None
        # Chế độ random: vị trí thật của chuột ở lượt kế tiếp.
        self.mouse_position = random.randrange(self.cup_count)
        # Chế độ smart: mọi vị trí chuột có thể đang ở ở lượt kế tiếp
        # (chuột chỉ "chốt" vị trí khi ván kết thúc).
        self.candidates: set[int] = set(range(self.cup_count))
        self.escape_phase = "choose"
        self.hunter_cup: int | None = None
        self.hunter_strategy: int | None = None
        if self.mode == "escape":
            self.mouse_position = None
            # Five equally likely branches, selected once per game; kept private.
            self.hunter_strategy = random.randrange(5)

    def escape_action(self, action: str, cup: object = None) -> dict[str, object]:
        if self.mode != "escape" or self.finished:
            raise ValueError("Không thể thao tác chuột đào tẩu ở ván này.")
        if action in ("choose", "move"):
            position = as_int(cup, "Cốc")
            if not 0 <= position < self.cup_count:
                raise ValueError("Cốc không hợp lệ.")
            if action == "choose" and self.escape_phase == "choose":
                self.mouse_position = position
            elif action == "move" and self.escape_phase == "move":
                if position not in self._neighbors(self.mouse_position):
                    raise ValueError("Chuột phải chạy đúng 1 ô liền kề.")
                self.mouse_position = position
            else:
                raise ValueError("Chưa đến lượt thao tác này.")
            self.escape_phase = "hunt"
            message = "Đã vào chỗ trốn. Bấm Máy săn để tiếp tục."
        elif action == "hunt" and self.escape_phase == "hunt":
            # The strategy is fixed for the game and never reads the mouse.
            self.hunter_cup = (
                HUNTER_PATTERNS[self.hunter_strategy][self.moves]
                if self.hunter_strategy < 4 else random.randrange(self.cup_count)
            )
            self.moves += 1
            if self.hunter_cup == self.mouse_position:
                self.finished = True
                self.escape_phase = "finished"
                message = "Máy đã bắt được bạn! Chuột đào tẩu thất bại."
            elif self.moves == self.max_moves:
                self.finished = self.won = True
                self.escape_phase = "finished"
                message = f"Thoát đủ {self.max_moves} lần săn! Bạn thắng!"
            else:
                remaining = self.candidates - {self.hunter_cup}
                self.candidates = {n for p in remaining for n in self._neighbors(p)}
                self.escape_phase = "move"
                message = f"Máy mở cốc {self.hunter_cup + 1}, bạn thoát! Chọn một cốc liền kề để chạy."
        else:
            raise ValueError("Thao tác hoặc lượt chơi không hợp lệ.")
        return {**self.state(), "message": message}

    @property
    def movement_pattern(self) -> tuple[int, ...]:
        if self.mode == "super_boss":
            return (1, 2, 3)
        return (1, 2) if self.mode == "boss" else (1,)

    @property
    def next_step(self) -> int:
        """Số ô chuột đi nếu lần mở sắp tới trượt."""
        pattern = self.movement_pattern
        return pattern[self.moves % len(pattern)]

    def _destinations(self, position: int, steps: int) -> set[int]:
        # Chọn hướng một lần, đi đủ số bước; ở biên thì bật ngược.
        destinations = set()
        for direction in (-1, 1):
            current = position
            for _ in range(steps):
                if not 0 <= current + direction < self.cup_count:
                    direction = -direction
                current += direction
            destinations.add(current)
        return destinations

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
            "next_step": None,
        }

    def _miss(self, message: str, cup: int) -> dict[str, object]:
        return {
            "won": False,
            "finished": False,
            "moves": self.moves,
            "opened_cup": cup,
            "mouse_position": None,
            "message": message,
            "next_step": self.next_step,
        }

    def _lose(self, position: int, cup: int) -> dict[str, object]:
        return self._finish(
            False,
            position,
            f"Hết {self.max_moves} lượt! Chuột đã thoát, bạn thua.",
            cup,
        )

    def open_cup(self, cup: int) -> dict[str, object]:
        if self.mode == "escape":
            raise ValueError("Bạn là chuột; hãy dùng thao tác đào tẩu.")
        cup = as_int(cup, "Cốc")
        if not 0 <= cup < self.cup_count:
            raise ValueError("Cốc không hợp lệ.")
        if self.finished:
            raise ValueError("Ván chơi đã kết thúc.")

        self.moves += 1
        if self.mode != "random":
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
        pattern = self.movement_pattern
        steps = pattern[(self.moves - 1) % len(pattern)]
        self.candidates = {
            n for p in remaining for n in self._destinations(p, steps)
        }
        return self._miss(f"Không có chuột! Chuột đã đi {steps} ô.", cup)

    def state(self) -> dict[str, object]:
        return {
            "cup_count": self.cup_count,
            "max_moves": self.max_moves,
            "mode": self.mode,
            "level": self.level,
            "level_name": self.level_name,
            "movement_pattern": list(self.movement_pattern),
            "next_step": None if self.finished else self.next_step,
            "moves": self.moves,
            "finished": self.finished,
            "won": self.won,
            "mouse_position": self.mouse_position if self.mode == "escape" else self.revealed_position if self.finished else None,
            "escape_phase": self.escape_phase if self.mode == "escape" else None,
            "hunter_cup": self.hunter_cup if self.mode == "escape" else None,
            "legal_moves": self._neighbors(self.mouse_position) if self.mode == "escape" and self.escape_phase == "move" else [],
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
            if path not in ("/api/new-game", "/api/open", "/api/escape"):
                self._send_json({"error": "Không tìm thấy API."}, status=404)
                return
            data = self._read_json()
            if path == "/api/new-game":
                level = as_int(data.get("level", 1), "Bậc độ khó")
                with sessions_lock:
                    game = self._get_game()
                    game.reset(level)
                    result = game.state()
            elif path == "/api/escape":
                with sessions_lock:
                    result = self._get_game().escape_action(data.get("action"), data.get("cup"))
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
