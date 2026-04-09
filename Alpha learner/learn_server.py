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
    "port": 8110,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8110"],
}

ALPHA_LEARN_GUIDE = {
    "name": "Alpha Learn",
    "tagline": "A beginner coding platform for learning Alpha one clear step at a time.",
    "tracks": [
        {
            "id": "foundations",
            "title": "Foundations",
            "summary": "Start with messages, variables, and clean readable syntax.",
            "goal": "Learn how Alpha reads like simple instructions.",
            "color": "gold",
        },
        {
            "id": "logic",
            "title": "Logic Path",
            "summary": "Make decisions and repeat work with friendly code blocks.",
            "goal": "Use if, otherwise, and repeat with confidence.",
            "color": "sky",
        },
        {
            "id": "builders",
            "title": "Builder Path",
            "summary": "Create helpers, objects, and small tools using real Alpha features.",
            "goal": "Graduate from tiny examples into useful programs.",
            "color": "mint",
        },
    ],
    "lessons": [
        {
            "id": "hello_alpha",
            "track_id": "foundations",
            "title": "Hello Alpha",
            "level": "Starter",
            "duration": "5 min",
            "goal": "Print your first message with Alpha.",
            "explain": "Use note to show words in the output. If the text is in quotes, Alpha prints it exactly.",
            "hint": "Type note, then a quoted message like \"Hello\".",
            "challenge": "Change the message so it says hello from your own name.",
            "checkpoint": "Run code that prints at least one line.",
            "keywords": ["note"],
            "source": 'note "Hello from Alpha Learn!"\n',
        },
        {
            "id": "remember_values",
            "track_id": "foundations",
            "title": "Remember Values",
            "level": "Starter",
            "duration": "7 min",
            "goal": "Save text and numbers using set.",
            "explain": "Variables let Alpha remember values. Use set name = value, then use the name again later.",
            "hint": "Try set learner = \"Aritra\" and note learner.",
            "challenge": "Save your age or favorite number and print both pieces of information.",
            "checkpoint": "Use set at least once and print the saved value.",
            "keywords": ["set", "note"],
            "source": 'set learner = "Bluear_cod"\nset score = 5\n\nnote learner\nnote score\n',
        },
        {
            "id": "make_choices",
            "track_id": "logic",
            "title": "Make Choices",
            "level": "Beginner",
            "duration": "8 min",
            "goal": "Use if and otherwise to choose between two paths.",
            "explain": "Conditions let your program react. if needs then, and each block closes with end.",
            "hint": "Compare a variable with == and add otherwise for the second branch.",
            "challenge": "Add one more message when the condition is true.",
            "checkpoint": "Write an if block that ends with end.",
            "keywords": ["if", "otherwise", "end"],
            "source": 'set weather = "sunny"\n\nif weather == "sunny" then\n    note "Take your shades."\notherwise\n    note "Carry an umbrella."\nend\n',
        },
        {
            "id": "repeat_steps",
            "track_id": "logic",
            "title": "Repeat Steps",
            "level": "Beginner",
            "duration": "9 min",
            "goal": "Use repeat to count and loop through work.",
            "explain": "repeat can count through a range or loop through a list. This helps when you do the same job many times.",
            "hint": "Use repeat number from 1 to 5 and print number inside the block.",
            "challenge": "Count to 10 and print \"done\" after the loop.",
            "checkpoint": "Run a repeat loop without errors.",
            "keywords": ["repeat", "end"],
            "source": 'repeat number from 1 to 5\n    note "Step " + str(number)\nend\n',
        },
        {
            "id": "build_helpers",
            "track_id": "builders",
            "title": "Build Helpers",
            "level": "Builder",
            "duration": "10 min",
            "goal": "Write a function you can reuse.",
            "explain": "Functions package a task into a name. Use give to return a result from the function.",
            "hint": "function greet(name) opens a reusable block, and give sends back the final answer.",
            "challenge": "Call your helper with two different names.",
            "checkpoint": "Create a function and call it at least once.",
            "keywords": ["function", "give", "end"],
            "source": 'function greet(name)\n    give "Welcome, " + name + "!"\nend\n\nnote greet("Student")\n',
        },
        {
            "id": "build_objects",
            "track_id": "builders",
            "title": "Build Objects",
            "level": "Builder",
            "duration": "12 min",
            "goal": "Create a small class with data and behavior.",
            "explain": "Classes help group related values and methods. They are useful when your programs start growing bigger.",
            "hint": "Use class Name, then add a function __init__ and another function for behavior.",
            "challenge": "Change the class to describe a robot, pet, or player.",
            "checkpoint": "Create one object and call one method.",
            "keywords": ["class", "function", "set", "give", "end"],
            "source": 'class Badge\n    function __init__(self, title)\n        set self.title = title\n    end\n\n    function show(self)\n        give "Badge: " + self.title\n    end\nend\n\nset star = Badge("First Run")\nnote star.show()\n',
        },
        {
            "id": "real_project",
            "track_id": "builders",
            "title": "Mini Project Report",
            "level": "Builder",
            "duration": "15 min",
            "goal": "Combine variables, loops, and functions into a mini report program.",
            "explain": "This lesson connects the pieces. Alpha becomes powerful when you join many small readable ideas into one program.",
            "hint": "Use a function, loop over scores, and print the result.",
            "challenge": "Add a highest score or average score line.",
            "checkpoint": "Run a complete mini program with more than one block.",
            "keywords": ["function", "repeat", "note", "give", "end"],
            "source": 'function total_scores(values)\n    set total = 0\n\n    repeat value in values\n        set total = total + value\n    end\n\n    give total\nend\n\nset scores = [88, 94, 79]\nnote "Total score"\nnote total_scores(scores)\n',
        },
    ],
    "glossary": [
        {"term": "note", "meaning": "Show text or values in the output area."},
        {"term": "set", "meaning": "Create or update a variable so Alpha remembers a value."},
        {"term": "if", "meaning": "Run a block only when a condition is true."},
        {"term": "otherwise", "meaning": "The fallback block after an if condition."},
        {"term": "repeat", "meaning": "Loop through a range or list of values."},
        {"term": "function", "meaning": "A reusable named block of code."},
        {"term": "give", "meaning": "Return a value from a function."},
        {"term": "class", "meaning": "A blueprint for building objects with values and methods."},
        {"term": "end", "meaning": "Close the current Alpha block."},
    ],
    "quick_wins": [
        {
            "title": "Daily Greeting",
            "description": "Make a one-line program that prints a kind message every morning.",
            "source": 'note "Today is a good day to build with Alpha."\n',
        },
        {
            "title": "Tiny Counter",
            "description": "Count your practice rounds from 1 to 3.",
            "source": 'repeat round from 1 to 3\n    note round\nend\n',
        },
        {
            "title": "Mood Checker",
            "description": "Choose a message based on your current mood.",
            "source": 'set mood = "ready"\n\nif mood == "ready" then\n    note "Let us code."\notherwise\n    note "Take one deep breath and try again."\nend\n',
        },
    ],
    "quizzes": [
        {
            "id": "quiz_one",
            "question": "Which Alpha keyword prints text to the output?",
            "options": ["set", "note", "repeat", "give"],
            "answer_index": 1,
            "explain": "note is the Alpha keyword for showing output.",
        },
        {
            "id": "quiz_two",
            "question": "Which keyword closes an if, repeat, function, or class block?",
            "options": ["stop", "finally", "end", "catch"],
            "answer_index": 2,
            "explain": "Every Alpha block closes with end.",
        },
        {
            "id": "quiz_three",
            "question": "What does give do inside a function?",
            "options": ["Starts a loop", "Returns a value", "Creates a class", "Imports a module"],
            "answer_index": 1,
            "explain": "give returns the final value from a function.",
        },
    ],
    "coach_notes": [
        "Read the code out loud. Alpha often makes sense when you hear it like a sentence.",
        "When you get stuck, change only one small thing and run again.",
        "A clean block always ends with end.",
        "Start with a working example, then make it your own.",
    ],
    "milestones": [
        "First successful run",
        "Three lessons completed",
        "Completed one full track",
        "Built a mini project",
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


class LearnRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaLearnHTTP/1.0"

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
            self._send_json(ALPHA_LEARN_GUIDE)
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
    parser = argparse.ArgumentParser(description="Run Alpha Learn in your browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8110, help="Server port. Default: 8110")
    parser.add_argument(
        "--share-lan",
        action="store_true",
        help="Bind Alpha Learn to 0.0.0.0 so phones and PCs on the same Wi-Fi can open it.",
    )
    args = parser.parse_args()

    host = "0.0.0.0" if args.share_lan else args.host
    SERVER_STATE["host"] = host
    SERVER_STATE["port"] = args.port
    SERVER_STATE["share_lan"] = args.share_lan
    SERVER_STATE["urls"] = _discover_urls(host, args.port, args.share_lan)

    server = ThreadingHTTPServer((host, args.port), LearnRequestHandler)
    print("Alpha Learn is running at:")
    for url in SERVER_STATE["urls"]:
        print(f"  {url}")
    if args.share_lan:
        print("Alpha Learn live sharing is enabled on this trusted local network.")
    print("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alpha Learn...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
