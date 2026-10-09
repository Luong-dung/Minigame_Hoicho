"""Browser sliding-puzzle minigame.

Run from this directory with:

    python minigame.py

Then open http://127.0.0.1:8000 in a browser. Images are discovered from the
neighbouring ``image`` directory every time the page is loaded.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse


ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "image"

FRONTEND_DIR = ROOT / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


class GameHandler(SimpleHTTPRequestHandler):
    """Serve the frontend, image API, and files from the minigame directory."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

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
        if path == "/api/images":
            images = sorted(
                quote(file.name) for file in IMAGE_DIR.iterdir()
                if file.is_file() and (mimetypes.guess_type(file.name)[0] or "").startswith("image/")
            )
            body = json.dumps([f"/image/{name}" for name in images]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the image sliding puzzle in a browser.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()
    if not IMAGE_DIR.is_dir():
        raise SystemExit(f"Image directory does not exist: {IMAGE_DIR}")
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
