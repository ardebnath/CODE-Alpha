from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import threading
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
MAIN_DIR = ROOT_DIR / "Maine File"
DATA_DIR = BASE_DIR / "engine_data"
SCRIPT_DIR = DATA_DIR / "saved_scripts"
LOGS_PATH = DATA_DIR / "execution_logs.json"

if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from alpha import AlphaInterpreter, AlphaLanguageError, AlphaTranslator  # noqa: E402


INDEX_FILE = BASE_DIR / "index.html"
STYLE_FILE = BASE_DIR / "style.css"
SCRIPT_FILE = BASE_DIR / "studio.js"
MANIFEST_FILE = BASE_DIR / "manifest.webmanifest"
SERVICE_WORKER_FILE = BASE_DIR / "sw.js"

SERVER_STATE = {
    "host": "127.0.0.1",
    "port": 8095,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8095"],
}

ENGINE_TEMPLATES = {
    "contact_form": {
        "key": "contact_form",
        "title": "Contact Form Saver",
        "description": "Validate a website contact form and save the lead.",
        "source": """$ Alpha Website Logic Engine template: contact form
if form_email == "" then
    set website_result = {
        "ok": false,
        "message": "Email is required before this form can be saved."
    }
otherwise
    set lead_key = "lead_" + replace_text(split_text(to_text(timestamp_text()), " ")[0], "-", "_")
    store(
        lead_key,
        {
            "type": "contact_form",
            "name": form_name,
            "email": form_email,
            "message": form_message,
            "submitted_at": timestamp_text()
        }
    )

    set website_result = {
        "ok": true,
        "message": "Lead saved by Alpha Website Logic Engine.",
        "lead_key": lead_key
    }
    note "Saved contact form for " + form_name
end
""",
    },
    "admin_approval": {
        "key": "admin_approval",
        "title": "Admin Approval Rule",
        "description": "Approve or reject admin actions based on role and request details.",
        "source": """$ Template: admin approval
if admin_role == "manager" or admin_role == "owner" then
    set website_result = {
        "ok": true,
        "approved": true,
        "message": "Request approved for admin role " + admin_role,
        "action": admin_action
    }
    note "Approved " + admin_action
otherwise
    set website_result = {
        "ok": false,
        "approved": false,
        "message": "This admin role cannot approve the request.",
        "action": admin_action
    }
    note "Approval blocked for role " + admin_role
end
""",
    },
    "inventory_guard": {
        "key": "inventory_guard",
        "title": "Inventory Guard",
        "description": "Protect stock updates and warn when quantity becomes low.",
        "source": """$ Template: inventory update
set next_total = form_current_stock - form_order_count

if next_total < 0 then
    set website_result = {
        "ok": false,
        "message": "You cannot sell more items than you have in stock."
    }
otherwise
    set website_result = {
        "ok": true,
        "message": "Inventory updated.",
        "item": form_item_name,
        "next_total": next_total,
        "warning": next_total < 5
    }
    note "Inventory updated for " + form_item_name
end
""",
    },
    "dashboard_widget": {
        "key": "dashboard_widget",
        "title": "Dashboard Widget Data",
        "description": "Return a simple dashboard summary for admin tools.",
        "source": """$ Template: dashboard widget
set website_result = {
    "ok": true,
    "widget_title": "Leads Overview",
    "cards": [
        {"label": "Saved records", "value": length(records())},
        {"label": "Latest action", "value": admin_action},
        {"label": "Current page", "value": admin_page}
    ]
}

note "Dashboard summary generated"
""",
    },
}


def _timestamp_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


class EngineStorageError(ValueError):
    """Raised when the website engine storage request is invalid."""


class EngineStorage:
    def __init__(self, scripts_dir: Path, logs_path: Path) -> None:
        self.scripts_dir = scripts_dir
        self.logs_path = logs_path
        self._lock = threading.RLock()
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.logs_path.exists():
            self.logs_path.write_text("[]", encoding="utf-8")

    def ensure_template_script(self, template: dict[str, str]) -> None:
        with self._lock:
            script_path = self._script_path(template["key"])
            if script_path.exists():
                return
            self._write_script_files(
                key=template["key"],
                name=template["title"],
                description=template["description"],
                code=template["source"],
            )

    def list_scripts(self) -> list[dict[str, Any]]:
        with self._lock:
            scripts = []
            for metadata_path in sorted(
                self.scripts_dir.glob("*.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            ):
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(metadata, dict):
                    continue
                script_path = self._script_path(str(metadata.get("key", metadata_path.stem)))
                scripts.append(
                    {
                        "key": str(metadata.get("key", metadata_path.stem)),
                        "name": str(metadata.get("name", metadata_path.stem)),
                        "description": str(metadata.get("description", "")),
                        "updated_at": str(metadata.get("updated_at", _timestamp_text())),
                        "path": self._relative_text(script_path),
                    }
                )
            return scripts

    def save_script(self, name: str, code: str, description: str = "") -> dict[str, Any]:
        display_name = str(name or "").strip()
        if not display_name:
            raise EngineStorageError("Script name is required.")
        script_key = self._normalize_key(display_name)
        with self._lock:
            return self._write_script_files(
                key=script_key,
                name=display_name,
                description=str(description or ""),
                code=str(code or ""),
            )

    def load_script(self, key: str) -> dict[str, Any]:
        script_key = self._normalize_key(key)
        with self._lock:
            script_path = self._script_path(script_key)
            metadata_path = self._metadata_path(script_key)
            if not script_path.exists() or not metadata_path.exists():
                raise EngineStorageError("That saved Alpha script was not found.")

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            return {
                "script": {
                    "key": str(metadata.get("key", script_key)),
                    "name": str(metadata.get("name", script_key)),
                    "description": str(metadata.get("description", "")),
                    "updated_at": str(metadata.get("updated_at", _timestamp_text())),
                    "path": self._relative_text(script_path),
                },
                "code": script_path.read_text(encoding="utf-8"),
            }

    def delete_script(self, key: str) -> dict[str, Any]:
        script_key = self._normalize_key(key)
        loaded = self.load_script(script_key)
        with self._lock:
            self._script_path(script_key).unlink(missing_ok=True)
            self._metadata_path(script_key).unlink(missing_ok=True)
        return loaded["script"]

    def append_log(self, entry: dict[str, Any]) -> None:
        with self._lock:
            logs = self._read_logs_unlocked()
            logs.append(entry)
            logs = logs[-40:]
            self.logs_path.write_text(json.dumps(logs, ensure_ascii=True, indent=2), encoding="utf-8")

    def recent_logs(self, limit: int = 18) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self._read_logs_unlocked()[-limit:]))

    def _write_script_files(
        self,
        *,
        key: str,
        name: str,
        description: str,
        code: str,
    ) -> dict[str, Any]:
        now = _timestamp_text()
        metadata = {
            "key": key,
            "name": name,
            "description": description,
            "updated_at": now,
        }
        script_path = self._script_path(key)
        metadata_path = self._metadata_path(key)
        script_path.write_text(code, encoding="utf-8")
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")
        return {
            "key": key,
            "name": name,
            "description": description,
            "updated_at": now,
            "path": self._relative_text(script_path),
        }

    def _read_logs_unlocked(self) -> list[dict[str, Any]]:
        try:
            raw = json.loads(self.logs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    @staticmethod
    def _normalize_key(name: str) -> str:
        text = str(name or "").strip().lower()
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"[^a-z0-9_-]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("._-")
        if not text:
            raise EngineStorageError("Script key must include letters or numbers.")
        return text[:64]

    def _script_path(self, key: str) -> Path:
        return self.scripts_dir / f"{key}.alpha"

    def _metadata_path(self, key: str) -> Path:
        return self.scripts_dir / f"{key}.json"

    @staticmethod
    def _relative_text(path: Path) -> str:
        try:
            return path.relative_to(ROOT_DIR).as_posix()
        except ValueError:
            return path.as_posix()


class WebsiteLogicEngine(AlphaInterpreter):
    def run_logic(
        self,
        source_code: str,
        *,
        script_name: str,
        form_data: dict[str, Any] | None = None,
        admin_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_time = perf_counter()
        translated_code = ""
        output_lines: list[str] = []
        error_text: str | None = None
        error_line: int | None = None
        error_column: int | None = None
        status = "ok"
        compiled = None
        current_import_line: int | None = None
        environment: dict[str, Any] | None = None

        safe_form = self._json_safe(form_data or {})
        safe_admin = self._json_safe(admin_data or {})
        if not isinstance(safe_form, dict):
            safe_form = {}
        if not isinstance(safe_admin, dict):
            safe_admin = {}

        try:
            compiled = AlphaTranslator(source_code).translate()
            translated_code = compiled.python_code
            environment = self._build_environment(output_lines)
            environment.update(
                {
                    "form_data": safe_form,
                    "admin_data": safe_admin,
                    "request_data": {
                        "form": safe_form,
                        "admin": safe_admin,
                    },
                    "website_result": {
                        "ok": True,
                        "message": "Alpha logic finished without a custom website_result.",
                    },
                    "form_value": lambda name, default=None: safe_form.get(str(name), default),
                    "admin_value": lambda name, default=None: safe_admin.get(str(name), default),
                    "engine_info": {
                        "script_name": script_name,
                        "executed_at": _timestamp_text(),
                    },
                }
            )

            for key, value in safe_form.items():
                normalized = self._safe_name(key)
                environment[f"form_{normalized}"] = value
            for key, value in safe_admin.items():
                normalized = self._safe_name(key)
                environment[f"admin_{normalized}"] = value

            for import_request in compiled.imports:
                current_import_line = import_request.line_number
                environment[import_request.alias] = self._resolve_safe_module(import_request.module_name)

            current_import_line = None
            compiled_code = compile(compiled.python_code, "<alpha_website_logic>", "exec")
            exec(compiled_code, environment, environment)
        except Exception as exc:  # noqa: BLE001
            status = "error"
            error_line, error_column = self._resolve_error_location(exc, compiled, current_import_line)
            error_text = self._format_error_text(exc, error_line, error_column)

        duration_ms = (perf_counter() - start_time) * 1000
        output_text = "\n".join(output_lines)
        run_id = self.database.record_run(
            source_code=source_code,
            translated_code=translated_code,
            status=status,
            output_text=output_text,
            error_text=error_text,
            duration_ms=duration_ms,
        )

        website_result = {}
        if environment is not None:
            website_result = self._json_safe(environment.get("website_result"))
            if not isinstance(website_result, (dict, list, str, int, float, bool)) and website_result is not None:
                website_result = {"value": str(website_result)}

        return {
            "source_code": source_code,
            "translated_code": translated_code,
            "output_text": output_text,
            "error_text": error_text,
            "duration_ms": round(duration_ms, 3),
            "status": status,
            "run_id": run_id,
            "error_line": error_line,
            "error_column": error_column,
            "website_result": website_result,
            "context": {
                "form_data": safe_form,
                "admin_data": safe_admin,
                "script_name": script_name,
            },
        }

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        return str(value)

    @staticmethod
    def _safe_name(value: Any) -> str:
        text = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value or "").strip().lower())
        text = re.sub(r"_+", "_", text).strip("_")
        if not text:
            return "value"
        if text[0].isdigit():
            return f"value_{text}"
        return text


STORAGE = EngineStorage(SCRIPT_DIR, LOGS_PATH)
ENGINE = WebsiteLogicEngine()
for template in ENGINE_TEMPLATES.values():
    STORAGE.ensure_template_script(template)


def _build_guide_payload() -> dict[str, Any]:
    return {
        "name": "Alpha Website Logic Engine",
        "tagline": "Use Alpha as the readable scripting layer behind websites, forms, and admin tools.",
        "templates": list(ENGINE_TEMPLATES.values()),
        "saved_scripts": STORAGE.list_scripts(),
        "recent_logs": STORAGE.recent_logs(limit=12),
        "features": [
            "Run Alpha scripts with website form data and admin data",
            "Save reusable website logic scripts in this product folder",
            "Expose a public execute endpoint for websites or forms",
            "Inspect translated Python, logs, and structured website_result output",
        ],
        "tips": [
            "Scripts can read direct values like form_name or admin_role.",
            "Use website_result to return JSON-like output to the website or admin tool.",
            "Use store and fetch when you want Alpha to save or read persistent records.",
            "The public API route is /api/public/execute with a saved script key.",
        ],
        "default_form_data": {
            "name": "Aritra",
            "email": "aritra@example.com",
            "message": "Hello from the website form",
            "item_name": "Notebook",
            "current_stock": 18,
            "order_count": 4,
        },
        "default_admin_data": {
            "role": "manager",
            "action": "approve_order",
            "page": "orders_dashboard",
        },
    }


class EngineRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaWebsiteEngine/1.0"

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
            self._send_json(_build_guide_payload())
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

        if route == "/api/logs":
            self._send_json({"logs": STORAGE.recent_logs(limit=18)})
            return

        self._send_json({"error": f"Route '{route}' was not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        payload = self._read_json_payload()
        if payload is None:
            return

        try:
            if route == "/api/run":
                result = ENGINE.run_logic(
                    str(payload.get("code", "")),
                    script_name=str(payload.get("script_name", "unsaved_logic")),
                    form_data=self._dict_payload(payload.get("form_data")),
                    admin_data=self._dict_payload(payload.get("admin_data")),
                )
                self._append_log(result)
                self._send_json(result)
                return

            if route == "/api/scripts/save":
                script = STORAGE.save_script(
                    str(payload.get("name", "")),
                    str(payload.get("code", "")),
                    str(payload.get("description", "")),
                )
                self._send_json(
                    {
                        "script": script,
                        "saved_scripts": STORAGE.list_scripts(),
                    }
                )
                return

            if route == "/api/scripts/load":
                loaded = STORAGE.load_script(str(payload.get("script_key", "")))
                self._send_json(loaded)
                return

            if route == "/api/scripts/delete":
                deleted = STORAGE.delete_script(str(payload.get("script_key", "")))
                self._send_json(
                    {
                        "deleted": deleted,
                        "saved_scripts": STORAGE.list_scripts(),
                    }
                )
                return

            if route == "/api/public/execute":
                loaded = STORAGE.load_script(str(payload.get("script_key", "")))
                result = ENGINE.run_logic(
                    str(loaded["code"]),
                    script_name=str(loaded["script"]["key"]),
                    form_data=self._dict_payload(payload.get("form_data")),
                    admin_data=self._dict_payload(payload.get("admin_data")),
                )
                self._append_log(result)
                self._send_json(result)
                return

            self._send_json({"error": f"Route '{route}' was not found."}, status=HTTPStatus.NOT_FOUND)
        except EngineStorageError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _append_log(self, result: dict[str, Any]) -> None:
        STORAGE.append_log(
            {
                "logged_at": _timestamp_text(),
                "script_name": result["context"]["script_name"],
                "status": result["status"],
                "duration_ms": result["duration_ms"],
                "error_text": result["error_text"],
                "output_text": result["output_text"],
                "website_result": result["website_result"],
            }
        )

    @staticmethod
    def _dict_payload(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _read_json_payload(self) -> dict[str, Any] | None:
        raw_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if not raw_body:
            return {}

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "Request body must be valid JSON."}, status=HTTPStatus.BAD_REQUEST)
            return None

        if not isinstance(payload, dict):
            self._send_json({"error": "JSON payload must be an object."}, status=HTTPStatus.BAD_REQUEST)
            return None

        return payload

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json({"error": f"File '{path.name}' was not found."}, status=HTTPStatus.NOT_FOUND)
            return

        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
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
    parser = argparse.ArgumentParser(description="Run Alpha Website Logic Engine in your browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8095, help="Server port. Default: 8095")
    parser.add_argument(
        "--share-lan",
        action="store_true",
        help="Bind to 0.0.0.0 so devices on the same Wi-Fi can open the engine dashboard.",
    )
    args = parser.parse_args()

    host = "0.0.0.0" if args.share_lan else args.host
    SERVER_STATE["host"] = host
    SERVER_STATE["port"] = args.port
    SERVER_STATE["share_lan"] = args.share_lan
    SERVER_STATE["urls"] = _discover_urls(host, args.port, args.share_lan)

    server = ThreadingHTTPServer((host, args.port), EngineRequestHandler)
    print("Alpha Website Logic Engine running at:")
    for url in SERVER_STATE["urls"]:
        print(f"  {url}")
    if args.share_lan:
        print("LAN sharing is enabled for the website logic engine.")
    print("Press Ctrl+C to stop the engine.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alpha Website Logic Engine...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
