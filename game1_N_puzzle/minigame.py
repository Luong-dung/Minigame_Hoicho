"""Browser sliding-puzzle minigame.

Run from this directory with:

    python minigame.py

Then open http://127.0.0.1:8000 in a browser. Images are discovered from the
neighbouring ``image`` directory every time the page is loaded.
"""

from __future__ import annotations

import argparse
import json
import math
import mimetypes
import struct
import zlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "image"

FRONTEND_DIR = ROOT / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"
DIFFICULTIES = ((3, 3), (3, 4), (4, 4), (4, 5), (5, 5))
SIGNATURE_SIZE = 16
MEAN_PIXEL_DIFFERENCE = 3.0
DIFFERENT_PIXEL_RATIO = 0.05


def image_files() -> list[Path]:
    return sorted(
        file for file in IMAGE_DIR.iterdir()
        if file.is_file() and (mimetypes.guess_type(file.name)[0] or "").startswith("image/")
    )


def read_png(file: Path) -> tuple[int, int, bytes]:
    data = file.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("only PNG images are supported for puzzle validation")
    position = 8
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        chunk_type = data[position + 4:position + 8]
        chunk = data[position + 8:position + 8 + length]
        position += length + 12
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if bit_depth != 8 or compression != 0 or filtering != 0 or interlace != 0:
                raise ValueError("PNG must use 8-bit, non-interlaced format")
            if color_type not in (2, 6):
                raise ValueError("PNG must use RGB or RGBA format")
        elif chunk_type == b"IDAT":
            compressed.extend(chunk)
        elif chunk_type == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("PNG header is missing")
    channels = 4 if color_type == 6 else 3
    stride = width * channels
    raw = zlib.decompress(compressed)
    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    offset = 0
    for row in range(height):
        filter_type = raw[offset]
        offset += 1
        current = bytearray(raw[offset:offset + stride])
        offset += stride
        for index in range(stride):
            left = current[index - channels] if index >= channels else 0
            upper = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 255
            elif filter_type == 2:
                current[index] = (current[index] + upper) & 255
            elif filter_type == 3:
                current[index] = (current[index] + ((left + upper) // 2)) & 255
            elif filter_type == 4:
                estimate = left + upper - upper_left
                distances = (abs(estimate - left), abs(estimate - upper), abs(estimate - upper_left))
                current[index] = (current[index] + (left, upper, upper_left)[distances.index(min(distances))]) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter: {filter_type}")
        pixels[row * stride:(row + 1) * stride] = current
        previous = current
    return width, height, bytes(pixels)


def tile_signature(pixels: bytes, width: int, height: int, left: int, top: int,
                   tile_width: int, tile_height: int) -> list[tuple[int, int, int]]:
    channels = len(pixels) // (width * height)
    signature = []
    for row in range(SIGNATURE_SIZE):
        source_y = top + min(tile_height - 1, row * tile_height // SIGNATURE_SIZE)
        for col in range(SIGNATURE_SIZE):
            source_x = left + min(tile_width - 1, col * tile_width // SIGNATURE_SIZE)
            offset = (source_y * width + source_x) * channels
            signature.append(tuple(pixels[offset:offset + 3]))
    return signature


def tiles_are_indistinguishable(first: list[tuple[int, int, int]],
                                second: list[tuple[int, int, int]]) -> bool:
    differences = [
        sum(abs(first_pixel[channel] - second_pixel[channel]) for channel in range(3)) / 3
        for first_pixel, second_pixel in zip(first, second)
    ]
    mean_difference = sum(differences) / len(differences)
    different_ratio = sum(difference > 8 for difference in differences) / len(differences)
    return mean_difference <= MEAN_PIXEL_DIFFERENCE and different_ratio <= DIFFERENT_PIXEL_RATIO


def invalid_difficulties(file: Path) -> list[str]:
    width, height, pixels = read_png(file)
    scaled_width = 900
    scaled_height = max(1, round(scaled_width * height / width))
    invalid = []
    for rows, cols in DIFFICULTIES:
        pieces = []
        found_indistinguishable = False
        for row in range(rows):
            for col in range(cols):
                if row == rows - 1 and col == cols - 1:
                    continue
                left = math.floor(col * scaled_width / cols) * width // scaled_width
                top = math.floor(row * scaled_height / rows) * height // scaled_height
                tile_width = max(1, math.ceil(scaled_width / cols) * width // scaled_width)
                tile_height = max(1, math.ceil(scaled_height / rows) * height // scaled_height)
                piece = tile_signature(pixels, width, height, left, top, tile_width, tile_height)
                if any(tiles_are_indistinguishable(piece, previous) for previous in pieces):
                    found_indistinguishable = True
                    break
                pieces.append(piece)
            if found_indistinguishable:
                invalid.append(f"{rows}x{cols}")
                break
    return invalid


def build_validation_map() -> dict[str, list[str]]:
    validation = {}
    for file in image_files():
        if file.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            validation[file.name] = []
            continue
        try:
            validation[file.name] = invalid_difficulties(file)
        except (OSError, ValueError) as error:
            raise SystemExit(f"Cannot analyse image {file.name}: {error}") from error
    return validation


class GameHandler(SimpleHTTPRequestHandler):
    """Serve the frontend, image API, and files from the minigame directory."""

    validation_map: dict[str, list[str]] = {}

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
            images = [quote(file.name) for file in image_files()]
            body = json.dumps([f"/image/{name}" for name in images]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/validation":
            body = json.dumps(GameHandler.validation_map).encode("utf-8")
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
    print("Scanning invalid image-tile pairs...", flush=True)
    GameHandler.validation_map = build_validation_map()
    print("Scan complete. Server is ready.", flush=True)
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
