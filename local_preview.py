"""Local preview HTTP server for the mobile PWA folder (docs/)."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import webbrowser

DOCS_DIR = Path(__file__).resolve().parent / "docs"


def get_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class NoCacheStaticHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="PWA 로컬 미리보기 서버")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    handler = partial(NoCacheStaticHandler, directory=str(DOCS_DIR))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    local_url = f"http://localhost:{args.port}"
    lan_url = f"http://{get_lan_ip()}:{args.port}"
    print("=" * 56)
    print("  대전 캐시백 주유 지도 PWA 미리보기")
    print(f"  PC 주소     : {local_url}")
    print(f"  모바일 주소 : {lan_url}")
    print("  종료하려면 Ctrl+C")
    print("=" * 56)

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(local_url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
