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
    "port": 8090,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8090"],
}

KIDS_GUIDE = {
    "name": "Alpha Kids Studio",
    "tagline": "Play, learn, and build with friendly Alpha code.",
    "lessons": [
        {
            "id": "hello",
            "title": "Say Hello",
            "goal": "Write your first Alpha message.",
            "hint": "Use note with quotes to show words on the screen.",
            "challenge": "Change the name in the message to your own name.",
            "source": 'note "Hello, friend!"\n',
        },
        {
            "id": "count",
            "title": "Count Stars",
            "goal": "Use repeat to count with a loop.",
            "hint": "repeat number from 1 to 5 makes a counting loop.",
            "challenge": "Count up to 10 and print 'blast off' at the end.",
            "source": 'repeat number from 1 to 5\n    note "Star " + str(number)\nend\n',
        },
        {
            "id": "choice",
            "title": "Pick A Mood",
            "goal": "Use if and otherwise to make choices.",
            "hint": "Conditions need then, and each block closes with end.",
            "challenge": "Change the mood and add one more answer.",
            "source": 'set mood = "happy"\n\nif mood == "happy" then\n    note "Dance time!"\notherwise\n    note "Snack time!"\nend\n',
        },
        {
            "id": "story",
            "title": "Tiny Story",
            "goal": "Save words in variables and build a mini story.",
            "hint": "Use set to remember words, then join them with +.",
            "challenge": "Add a place and a funny ending.",
            "source": 'set hero = "Milo"\nset pet = "cat"\n\nnote hero + " and the " + pet + " found a rainbow door."\n',
        },
        {
            "id": "helper",
            "title": "Magic Helper",
            "goal": "Create a function you can use again and again.",
            "hint": "Functions start with function name(args) and use give to return a value.",
            "challenge": "Make the helper shout for two different names.",
            "source": 'function cheer(name)\n    give "You can do it, " + name + "!"\nend\n\nnote cheer("Aritra")\n',
        },
    ],
    "builders": [
        {
            "id": "greeting_card",
            "title": "Greeting Card",
            "description": "Build a colorful text card for a friend.",
            "tip": "Change the names and kind words to make it personal.",
            "source": 'set friend = "Ria"\nnote "Hello, " + friend + "!"\nnote "You are bright like a rainbow."\nnote "From Alpha Kids"\n',
        },
        {
            "id": "joke_machine",
            "title": "Joke Machine",
            "description": "Press run to hear a tiny silly joke.",
            "tip": "Change the animal and object to invent your own joke.",
            "source": 'set animal = "duck"\nset object = "boots"\nnote "Why did the " + animal + " wear " + object + "?"\nnote "Because the puddle was fancy!"\n',
        },
        {
            "id": "score_board",
            "title": "Score Board",
            "description": "Add numbers and celebrate the winner.",
            "tip": "Try changing the scores and see who wins.",
            "source": 'set mia = 7\nset leo = 9\n\nif leo > mia then\n    note "Leo wins!"\notherwise\n    note "Mia wins!"\nend\n',
        },
        {
            "id": "pet_club",
            "title": "Pet Club",
            "description": "Make a tiny pet object with class and functions.",
            "tip": "Change the pet name and the sound.",
            "source": 'class Pet\n    function __init__(self, name, sound)\n        set self.name = name\n        set self.sound = sound\n    end\n\n    function talk(self)\n        give self.name + " says " + self.sound\n    end\nend\n\nset buddy = Pet("Pico", "meow")\nnote buddy.talk()\n',
        },
    ],
    "coach_tips": [
        "Use note to show a message.",
        "Use set to save words or numbers.",
        "Every if, repeat, function, and class block ends with end.",
        "If code feels big, build it one small step at a time.",
    ],
    "celebrations": [
        "Great job! Your code just ran.",
        "Nice work! You made Alpha listen.",
        "Bright move! The program finished.",
        "Super! Keep building.",
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


class KidsRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaKidsHTTP/1.0"

    def do_GET(self) -> None:  # noqa: N802 - framework naming
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
            self._send_json(KIDS_GUIDE)
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

    def do_POST(self) -> None:  # noqa: N802 - framework naming
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

    def do_OPTIONS(self) -> None:  # noqa: N802 - framework naming
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - framework naming
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
    parser = argparse.ArgumentParser(description="Run Alpha Kids Studio in your browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8090, help="Server port. Default: 8090")
    parser.add_argument(
        "--share-lan",
        action="store_true",
        help="Bind to 0.0.0.0 so phones and tablets on the same Wi-Fi can join.",
    )
    args = parser.parse_args()

    host = "0.0.0.0" if args.share_lan else args.host
    SERVER_STATE["host"] = host
    SERVER_STATE["port"] = args.port
    SERVER_STATE["share_lan"] = args.share_lan
    SERVER_STATE["urls"] = _discover_urls(host, args.port, args.share_lan)

    server = ThreadingHTTPServer((host, args.port), KidsRequestHandler)
    print("Alpha Kids Studio running at:")
    for url in SERVER_STATE["urls"]:
        print(f"  {url}")
    if args.share_lan:
        print("Kid-friendly live sharing is ready on your trusted local network.")
    print("Press Ctrl+C to stop Alpha Kids Studio.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alpha Kids Studio...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
