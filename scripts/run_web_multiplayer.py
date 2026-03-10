"""Run full Tuxemon in browser with a hosted multiplayer server.

This launcher is for the full game (not the arcade prototype).
It starts:
- a headless multiplayer server (`run_tuxemon.py --headless --host-server`)
- a static HTTP server serving browser build output (`build/web`)

Build browser assets first with scripts/build_web_tuxemon.sh (or .bat on Windows),
or pass --build to do that automatically.
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
import subprocess
import sys
import threading
from pathlib import Path
from typing import Sequence


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-port", type=int, default=8000)
    parser.add_argument("--server-port", type=int, default=40081)
    parser.add_argument("--build", action="store_true", help="Build browser bundle before launch")
    parser.add_argument("--python-cmd", default=sys.executable)
    parser.add_argument("--web-dir", default="build/web")
    return parser.parse_args()


def build_command() -> list[str]:
    if sys.platform.startswith("win"):
        return ["cmd", "/c", "scripts\\build_web_tuxemon.bat"]
    return ["bash", "scripts/build_web_tuxemon.sh"]


def headless_command(python_cmd: str, server_port: int) -> list[str]:
    return [
        python_cmd,
        "run_tuxemon.py",
        "--headless",
        "--host-server",
        "--server-port",
        str(server_port),
    ]


def ensure_web_build(web_dir: Path) -> None:
    if not (web_dir / "index.html").exists():
        raise FileNotFoundError(
            "Browser build output not found at "
            f"{web_dir}. Run scripts/build_web_tuxemon.sh first."
        )


def start_static_server(web_dir: Path, http_port: int) -> ReusableTCPServer:
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(web_dir), **kwargs
    )
    server = ReusableTCPServer(("0.0.0.0", http_port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_subprocess(cmd: Sequence[str]) -> None:
    subprocess.run(list(cmd), check=True)


def main() -> None:
    args = parse_args()
    web_dir = Path(args.web_dir).resolve()

    if args.build:
        run_subprocess(build_command())

    ensure_web_build(web_dir)

    headless_proc = subprocess.Popen(headless_command(args.python_cmd, args.server_port))
    http_server = start_static_server(web_dir, args.http_port)

    print(f"[solamon] Serving full browser game: http://localhost:{args.http_port}")
    print(f"[solamon] Multiplayer headless server on port: {args.server_port}")

    try:
        headless_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        http_server.shutdown()
        if headless_proc.poll() is None:
            headless_proc.terminate()
            headless_proc.wait(timeout=10)


if __name__ == "__main__":
    main()
