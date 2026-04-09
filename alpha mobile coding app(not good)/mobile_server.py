from __future__ import annotations

import argparse
import json
import socket
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
MAIN_DIR = ROOT_DIR / "Maine File"

if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from alpha import AlphaInterpreter  # noqa: E402


INDEX_FILE = BASE_DIR / "index.html"
STYLE_FILE = BASE_DIR / "style.css"
SCRIPT_FILE = BASE_DIR / "studio.js"
MANIFEST_FILE = BASE_DIR / "manifest.webmanifest"
SERVICE_WORKER_FILE = BASE_DIR / "sw.js"

INTERPRETER = AlphaInterpreter()
SERVER_STATE = {
    "host": "127.0.0.1",
    "port": 8100,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8100"],
}

MOBILE_GUIDE = {
    "name": "Alpha Mobile Coding App",
    "tagline": "A phone-first Alpha app for writing and running code anywhere.",
    "quick_snippets": [
        {"title": "note", "insert": 'note "Hello from my phone!"\n'},
        {"title": "set", "insert": "set name = \"Alpha\"\n"},
        {"title": "if", "insert": "if true then\n    note \"It works\"\nend\n"},
        {"title": "repeat", "insert": "repeat number from 1 to 5\n    note number\nend\n"},
        {"title": "function", "insert": "function greet(name)\n    note \"Hello, \" + name\nend\n"},
        {"title": "class", "insert": "class Friend\n    function __init__(self, name)\n        set self.name = name\n    end\nend\n"},
    ],
    "featured_sample_keys": [
        "hello_world",
        "random_time_demo",
        "class_demo",
        "package_demo",
        "database_demo",
        "feature_showcase",
    ],
    "tips": [
        "Tap a snippet chip to insert Alpha code quickly on your phone.",
        "Use Save to keep code on this device with local browser storage.",
        "Install this app from your browser menu to open it like a mobile app.",
        "Press Run and then switch to Result to read output or the translated Python.",
    ],
}


def _discover_urls(host: str, port: int, share_lan: bool) -> list[str]:
    urls = [f"http://127.0.0.1:{port}"]

    if host not in {"127.0.0.1", "localhost"} or share_lan:
        candidate_ips: set[str] = set()
        try:
            hostname = socket.gethostname()
            for ip_address in socket.gethostbyname_ex(hostname)[2]:
                if ip_address and not ip_address.startswith("127."):
                    candidate_ips.add(ip_address)
        except OSError:
            pass

        for ip_address in sorted(candidate_ips):
            urls.append(f"http://{ip_address}:{port}")

    return urls


def _build_mobile_payload() -> dict[str, object]:
    base_payload = INTERPRETER.get_guide_payload()
    sample_programs = base_payload.get("sample_programs", {})
    featured_samples = []
    for sample_key in MOBILE_GUIDE["featured_sample_keys"]:
        if sample_key in sample_programs:
            featured_samples.append(
                {
                    "key": sample_key,
                    "title": sample_programs[sample_key]["title"],
                    "source": sample_programs[sample_key]["source"],
                }
            )

    return {
        "name": MOBILE_GUIDE["name"],
        "tagline": MOBILE_GUIDE["tagline"],
        "quick_snippets": MOBILE_GUIDE["quick_snippets"],
        "featured_samples": featured_samples,
        "tips": MOBILE_GUIDE["tips"],
        "requirements": base_payload.get("requirements", []),
        "rules": base_payload.get("rules", []),
    }


class MobileRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaMobileHTTP/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed_url = urlparse(self.path)
        route = parsed_url.path

        if route in {"/", "/index.html"}:
            self._send_file(INDEX_FILE, "text/html; charset=utf-8")
            return

        if route == "/style.css":
            self._send_file(STYLE_FILE, "text/css; charset=utf-8")
            return

        if route == "/studio.js":
            self._send_file(SCRIPT_FILE, "application/javascript; charset=utf-8")
            return

        if route == "/manifest.webmanifest":
            self._send_file(MANIFEST_FILE, "application/manifest+json; charset=utf-8")
            return

        if route == "/sw.js":
            self._send_file(SERVICE_WORKER_FILE, "application/javascript; charset=utf-8")
            return

        if route == "/api/guide":
            self._send_json(_build_mobile_payload())
            return

        if route == "/api/system":
            self._send_json(
                {
                    "host": SERVER_STATE["host"],
                    "port": SERVER_STATE["port"],
                    "share_lan": SERVER_STATE["share_lan"],
                    "urls": SERVER_STATE["urls"],
                }
            )
            return

        self._send_json(
            {"error": f"Route '{route}' was not found."},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_POST(self) -> None:  # noqa: N802
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        payload = self._read_json_payload()
        if payload is None:
            return

        if route == "/api/run":
            source_code = str(payload.get("code", ""))
            result = INTERPRETER.run(source_code)
            self._send_json(result.to_dict())
            return

        self._send_json(
            {"error": f"Route '{route}' was not found."},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _read_json_payload(self) -> dict[str, object] | None:
        raw_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if not raw_body:
            return {}

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {"error": "The browser sent invalid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return None

        if not isinstance(payload, dict):
            self._send_json(
                {"error": "The JSON body must be an object."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return None

        return payload

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json(
                {"error": f"File '{path.name}' was not found."},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        raw_payload = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw_payload)))
        self.end_headers()
        self.wfile.write(raw_payload)

    def _send_common_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Alpha Mobile Coding App in your browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8100, help="Server port. Default: 8100")
    parser.add_argument(
        "--share-lan",
        action="store_true",
        help="Bind to 0.0.0.0 so phones on the same trusted Wi-Fi can open the app.",
    )
    args = parser.parse_args()

    host = "0.0.0.0" if args.share_lan else args.host
    SERVER_STATE["host"] = host
    SERVER_STATE["port"] = args.port
    SERVER_STATE["share_lan"] = args.share_lan
    SERVER_STATE["urls"] = _discover_urls(host, args.port, args.share_lan)

    server = ThreadingHTTPServer((host, args.port), MobileRequestHandler)
    print("Alpha Mobile Coding App running at:")
    for url in SERVER_STATE["urls"]:
        print(f"  {url}")
    if args.share_lan:
        print("Phone sharing is enabled on your trusted local network.")
    print("Press Ctrl+C to stop the mobile app server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alpha Mobile Coding App...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
