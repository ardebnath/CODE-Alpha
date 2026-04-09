from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
import re
import secrets
import socket
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from alpha import AlphaInterpreter


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
INDEX_FILE = BASE_DIR / "index.html"
STYLE_FILE = BASE_DIR / "style.css"
STUDIO_SCRIPT_FILE = BASE_DIR / "studio.js"
MANIFEST_FILE = BASE_DIR / "manifest.webmanifest"
SERVICE_WORKER_FILE = BASE_DIR / "sw.js"
USER_DATA_DIR = ROOT_DIR / "alpha_user_data"
USER_ACCOUNTS_DIR = USER_DATA_DIR / "users"
INTERPRETER = AlphaInterpreter()
STARTUP_PASSWORD = "aritra1234"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 14
SERVER_STATE = {
    "host": "127.0.0.1",
    "port": 8080,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8080"],
}


def _require_startup_password() -> None:
    for attempt in range(3):
        try:
            typed_password = getpass.getpass("Enter Alpha startup password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nStartup cancelled.")
            raise SystemExit(1) from None

        if typed_password == STARTUP_PASSWORD:
            print("Password accepted. Starting Alpha Studio...")
            return

        remaining = 2 - attempt
        if remaining > 0:
            print(f"Wrong password. {remaining} attempt(s) left.")

    print("Access denied. Alpha Studio did not start.")
    raise SystemExit(1)


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


def _timestamp_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class StudioAccountError(ValueError):
    """Raised when a studio account or project request is invalid."""


class StudioAuthError(PermissionError):
    """Raised when a protected studio action needs an authenticated user."""


class StudioUserStore:
    USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,31}$")

    def __init__(self, users_dir: Path) -> None:
        self.users_dir = users_dir
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def register_user(self, username: str, password: str) -> dict[str, str | int]:
        canonical_username, display_username = self._normalize_username(username)
        password_text = self._validate_password(password, field_name="Password")

        with self._lock:
            user_dir = self._user_dir(canonical_username)
            if user_dir.exists():
                raise StudioAccountError("That username already exists. Please choose another one.")

            user_dir.mkdir(parents=True, exist_ok=True)
            self._projects_dir(canonical_username).mkdir(parents=True, exist_ok=True)

            now = _timestamp_text()
            password_salt = secrets.token_hex(16)
            profile = {
                "username": display_username,
                "canonical_username": canonical_username,
                "password_salt": password_salt,
                "password_hash": self._hash_password(password_text, password_salt),
                "created_at": now,
                "updated_at": now,
                "password_updated_at": now,
            }
            self._write_json(self._profile_path(canonical_username), profile)
            return self._user_payload_unlocked(profile)

    def authenticate_user(self, username: str, password: str) -> dict[str, str | int]:
        canonical_username, _ = self._normalize_username(username)

        with self._lock:
            profile = self._load_profile_unlocked(canonical_username)
            if not self._verify_password(profile, str(password or "")):
                raise StudioAccountError("Wrong username or password.")
            return self._user_payload_unlocked(profile)

    def change_password(self, username: str, current_password: str, new_password: str) -> dict[str, str | int]:
        canonical_username, _ = self._normalize_username(username)
        current_password_text = str(current_password or "")
        new_password_text = self._validate_password(new_password, field_name="New password")

        with self._lock:
            profile = self._load_profile_unlocked(canonical_username)
            if not self._verify_password(profile, current_password_text):
                raise StudioAccountError("Current password is wrong.")
            if current_password_text == new_password_text:
                raise StudioAccountError("New password must be different from the current password.")

            now = _timestamp_text()
            password_salt = secrets.token_hex(16)
            profile["password_salt"] = password_salt
            profile["password_hash"] = self._hash_password(new_password_text, password_salt)
            profile["updated_at"] = now
            profile["password_updated_at"] = now
            self._write_json(self._profile_path(canonical_username), profile)
            return self._user_payload_unlocked(profile)

    def get_user_summary(self, username: str) -> dict[str, str | int]:
        canonical_username, _ = self._normalize_username(username)
        with self._lock:
            profile = self._load_profile_unlocked(canonical_username)
            return self._user_payload_unlocked(profile)

    def list_projects(self, username: str) -> list[dict[str, str | int]]:
        canonical_username, _ = self._normalize_username(username)
        with self._lock:
            self._load_profile_unlocked(canonical_username)
            return self._list_projects_unlocked(canonical_username)

    def save_project(self, username: str, project_name: str, code: str) -> dict[str, str | int]:
        canonical_username, _ = self._normalize_username(username)
        display_name = str(project_name or "").strip()
        if not display_name:
            raise StudioAccountError("Project name is required before saving.")
        project_key = self._normalize_project_key(display_name)

        with self._lock:
            self._load_profile_unlocked(canonical_username)
            project_path = self._project_path(canonical_username, project_key)
            project_path.parent.mkdir(parents=True, exist_ok=True)
            project_path.write_text(str(code or ""), encoding="utf-8")
            self._write_json(
                self._project_metadata_path(canonical_username, project_key),
                {
                    "name": display_name,
                    "project_key": project_key,
                    "updated_at": _timestamp_text(),
                },
            )
            return self._project_payload_unlocked(canonical_username, project_path)

    def load_project(self, username: str, project_key: str) -> dict[str, object]:
        canonical_username, _ = self._normalize_username(username)
        normalized_project_key = self._normalize_project_key(project_key)

        with self._lock:
            self._load_profile_unlocked(canonical_username)
            project_path = self._project_path(canonical_username, normalized_project_key)
            if not project_path.exists():
                raise StudioAccountError("That saved project was not found.")

            return {
                "project": self._project_payload_unlocked(canonical_username, project_path),
                "code": project_path.read_text(encoding="utf-8"),
            }

    def delete_project(self, username: str, project_key: str) -> dict[str, str | int]:
        canonical_username, _ = self._normalize_username(username)
        normalized_project_key = self._normalize_project_key(project_key)

        with self._lock:
            self._load_profile_unlocked(canonical_username)
            project_path = self._project_path(canonical_username, normalized_project_key)
            if not project_path.exists():
                raise StudioAccountError("That saved project was not found.")

            project_payload = self._project_payload_unlocked(canonical_username, project_path)
            project_path.unlink()
            metadata_path = self._project_metadata_path(canonical_username, normalized_project_key)
            if metadata_path.exists():
                metadata_path.unlink()
            return project_payload

    def _user_payload_unlocked(self, profile: dict[str, str]) -> dict[str, str | int]:
        canonical_username = profile["canonical_username"]
        projects = self._list_projects_unlocked(canonical_username)
        return {
            "username": profile["username"],
            "canonical_username": canonical_username,
            "user_folder": self._relative_text(self._user_dir(canonical_username)),
            "project_folder": self._relative_text(self._projects_dir(canonical_username)),
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"],
            "project_count": len(projects),
        }

    def _list_projects_unlocked(self, canonical_username: str) -> list[dict[str, str | int]]:
        projects_dir = self._projects_dir(canonical_username)
        projects_dir.mkdir(parents=True, exist_ok=True)
        project_paths = sorted(
            projects_dir.glob("*.alpha"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return [self._project_payload_unlocked(canonical_username, path) for path in project_paths]

    def _project_payload_unlocked(self, canonical_username: str, project_path: Path) -> dict[str, str | int]:
        project_key = project_path.stem
        metadata = self._load_project_metadata_unlocked(canonical_username, project_key)
        source_code = project_path.read_text(encoding="utf-8")
        preview = "Empty Alpha file."
        for raw_line in source_code.splitlines():
            stripped_line = raw_line.strip()
            if stripped_line:
                preview = stripped_line[:120]
                break

        stat = project_path.stat()
        return {
            "name": metadata.get("name") or project_key,
            "project_key": project_key,
            "file_name": project_path.name,
            "folder": self._relative_text(project_path.parent),
            "updated_at": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            "size_bytes": stat.st_size,
            "preview": preview,
        }

    def _load_project_metadata_unlocked(self, canonical_username: str, project_key: str) -> dict[str, str]:
        metadata_path = self._project_metadata_path(canonical_username, project_key)
        if not metadata_path.exists():
            return {"name": project_key, "project_key": project_key}
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"name": project_key, "project_key": project_key}
        if not isinstance(metadata, dict):
            return {"name": project_key, "project_key": project_key}
        return {
            "name": str(metadata.get("name") or project_key),
            "project_key": str(metadata.get("project_key") or project_key),
        }

    def _load_profile_unlocked(self, canonical_username: str) -> dict[str, str]:
        profile_path = self._profile_path(canonical_username)
        if not profile_path.exists():
            raise StudioAccountError("That user account was not found.")
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise StudioAccountError("That user account could not be read.") from error
        if not isinstance(profile, dict):
            raise StudioAccountError("That user account could not be read.")
        return profile

    @staticmethod
    def _validate_password(password: str, *, field_name: str) -> str:
        text = str(password or "")
        if len(text) < 4:
            raise StudioAccountError(f"{field_name} must be at least 4 characters long.")
        return text

    @classmethod
    def _normalize_username(cls, username: str) -> tuple[str, str]:
        text = str(username or "").strip()
        if not cls.USERNAME_PATTERN.fullmatch(text):
            raise StudioAccountError(
                "Username must start with a letter and use 3-32 letters, numbers, _ or -."
            )
        return text.lower(), text

    @staticmethod
    def _normalize_project_key(project_name: str) -> str:
        text = str(project_name or "").strip().lower()
        if not text:
            raise StudioAccountError("Project name is required.")
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"[^a-z0-9_-]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("._-")
        if not text:
            raise StudioAccountError("Project name must include letters or numbers.")
        return text[:64]

    @staticmethod
    def _hash_password(password: str, salt_hex: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            200_000,
        ).hex()

    def _verify_password(self, profile: dict[str, str], password: str) -> bool:
        expected_hash = self._hash_password(password, profile["password_salt"])
        return hmac.compare_digest(expected_hash, profile["password_hash"])

    def _user_dir(self, canonical_username: str) -> Path:
        return self.users_dir / canonical_username

    def _projects_dir(self, canonical_username: str) -> Path:
        return self._user_dir(canonical_username) / "projects"

    def _profile_path(self, canonical_username: str) -> Path:
        return self._user_dir(canonical_username) / "profile.json"

    def _project_path(self, canonical_username: str, project_key: str) -> Path:
        return self._projects_dir(canonical_username) / f"{project_key}.alpha"

    def _project_metadata_path(self, canonical_username: str, project_key: str) -> Path:
        return self._projects_dir(canonical_username) / f"{project_key}.json"

    def _relative_text(self, path: Path) -> str:
        try:
            return path.relative_to(ROOT_DIR).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


class StudioSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, object]] = {}
        self._lock = threading.RLock()

    def create_session(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = {
                "username": username,
                "last_seen": time.time(),
            }
        return token

    def get_username(self, token: str | None) -> str | None:
        if not token:
            return None

        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None

            now = time.time()
            if now - float(session["last_seen"]) > SESSION_MAX_AGE_SECONDS:
                self._sessions.pop(token, None)
                return None

            session["last_seen"] = now
            return str(session["username"])

    def remove_session(self, token: str | None) -> None:
        if not token:
            return
        with self._lock:
            self._sessions.pop(token, None)


ACCOUNT_STORE = StudioUserStore(USER_ACCOUNTS_DIR)
SESSION_STORE = StudioSessionStore()


class AlphaRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaHTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler convention
        parsed_url = urlparse(self.path)
        route = parsed_url.path

        try:
            if route in {"/", "/index.html"}:
                self._send_file(INDEX_FILE, "text/html; charset=utf-8")
                return

            if route == "/style.css":
                self._send_file(STYLE_FILE, "text/css; charset=utf-8")
                return

            if route == "/studio.js":
                self._send_file(STUDIO_SCRIPT_FILE, "application/javascript; charset=utf-8")
                return

            if route == "/manifest.webmanifest":
                self._send_file(MANIFEST_FILE, "application/manifest+json; charset=utf-8")
                return

            if route == "/sw.js":
                self._send_file(SERVICE_WORKER_FILE, "application/javascript; charset=utf-8")
                return

            if route == "/api/guide":
                self._send_json(INTERPRETER.get_guide_payload())
                return

            if route == "/api/history":
                self._send_json({"runs": INTERPRETER.recent_runs(limit=12)})
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

            if route == "/api/packages":
                self._send_json(
                    {
                        "available_packages": INTERPRETER.list_available_packages(),
                        "installed_packages": INTERPRETER.list_installed_packages(),
                    }
                )
                return

            if route == "/api/account/status":
                self._send_json(self._account_state_payload(self._authenticated_username()))
                return

            if route == "/api/projects":
                username = self._require_authenticated_username()
                self._send_json(self._account_state_payload(username))
                return

            self._send_json(
                {"error": f"Route '{route}' was not found."},
                status=HTTPStatus.NOT_FOUND,
            )
        except StudioAuthError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.UNAUTHORIZED)
        except StudioAccountError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler convention
        parsed_url = urlparse(self.path)
        route = parsed_url.path

        payload = self._read_json_payload()
        if payload is None:
            return

        try:
            if route == "/api/run":
                source_code = payload.get("code", "")
                result = INTERPRETER.run(source_code)
                self._send_json(result.to_dict())
                return

            if route == "/api/packages/install":
                package_name = payload.get("name", "")
                record = INTERPRETER.install_package(package_name)
                self._send_json(
                    {
                        "installed": record,
                        "available_packages": INTERPRETER.list_available_packages(),
                        "installed_packages": INTERPRETER.list_installed_packages(),
                    }
                )
                return

            if route == "/api/packages/remove":
                package_name = payload.get("name", "")
                removed = INTERPRETER.remove_package(package_name)
                self._send_json(
                    {
                        "removed": removed,
                        "available_packages": INTERPRETER.list_available_packages(),
                        "installed_packages": INTERPRETER.list_installed_packages(),
                    }
                )
                return

            if route == "/api/account/register":
                user = ACCOUNT_STORE.register_user(
                    str(payload.get("username", "")),
                    str(payload.get("password", "")),
                )
                session_token = SESSION_STORE.create_session(str(user["canonical_username"]))
                response = self._account_state_payload(str(user["canonical_username"]))
                response["session"] = session_token
                response["message"] = f"User {user['username']} was created."
                self._send_json(response, status=HTTPStatus.CREATED)
                return

            if route == "/api/account/login":
                user = ACCOUNT_STORE.authenticate_user(
                    str(payload.get("username", "")),
                    str(payload.get("password", "")),
                )
                session_token = SESSION_STORE.create_session(str(user["canonical_username"]))
                response = self._account_state_payload(str(user["canonical_username"]))
                response["session"] = session_token
                response["message"] = f"Welcome back, {user['username']}."
                self._send_json(response)
                return

            if route == "/api/account/logout":
                SESSION_STORE.remove_session(self._session_token())
                self._send_json(
                    {
                        "authenticated": False,
                        "user": None,
                        "projects": [],
                        "user_data_folder": self._user_data_root_text(),
                        "message": "Signed out of Alpha Studio.",
                    }
                )
                return

            if route == "/api/account/password":
                username = self._require_authenticated_username()
                ACCOUNT_STORE.change_password(
                    username,
                    str(payload.get("current_password", "")),
                    str(payload.get("new_password", "")),
                )
                response = self._account_state_payload(username)
                response["message"] = "Password updated for this user."
                self._send_json(response)
                return

            if route == "/api/projects/save":
                username = self._require_authenticated_username()
                project = ACCOUNT_STORE.save_project(
                    username,
                    str(payload.get("name", "")),
                    str(payload.get("code", "")),
                )
                response = self._account_state_payload(username)
                response["project"] = project
                response["message"] = f"Saved project {project['name']}."
                self._send_json(response)
                return

            if route == "/api/projects/load":
                username = self._require_authenticated_username()
                loaded_project = ACCOUNT_STORE.load_project(
                    username,
                    str(payload.get("project_key") or payload.get("name") or ""),
                )
                response = self._account_state_payload(username)
                response.update(loaded_project)
                response["message"] = f"Loaded project {loaded_project['project']['name']}."
                self._send_json(response)
                return

            if route == "/api/projects/delete":
                username = self._require_authenticated_username()
                deleted_project = ACCOUNT_STORE.delete_project(
                    username,
                    str(payload.get("project_key") or payload.get("name") or ""),
                )
                response = self._account_state_payload(username)
                response["deleted"] = deleted_project
                response["message"] = f"Deleted project {deleted_project['name']}."
                self._send_json(response)
                return

            self._send_json(
                {"error": f"Route '{route}' was not found."},
                status=HTTPStatus.NOT_FOUND,
            )
        except StudioAuthError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.UNAUTHORIZED)
        except StudioAccountError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler convention
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - BaseHTTPRequestHandler API
        return

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

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Alpha-Session")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _read_json_payload(self) -> dict[str, object] | None:
        raw_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if not raw_body:
            return {}

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {"error": "Request body must be valid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return None

        if not isinstance(payload, dict):
            self._send_json(
                {"error": "JSON payload must be an object."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return None

        return payload

    def _session_token(self) -> str | None:
        token = str(self.headers.get("X-Alpha-Session", "")).strip()
        return token or None

    def _authenticated_username(self) -> str | None:
        return SESSION_STORE.get_username(self._session_token())

    def _require_authenticated_username(self) -> str:
        username = self._authenticated_username()
        if not username:
            raise StudioAuthError("Sign in to use personal saved projects and password settings.")
        return username

    def _account_state_payload(self, username: str | None) -> dict[str, object]:
        if not username:
            return {
                "authenticated": False,
                "user": None,
                "projects": [],
                "user_data_folder": self._user_data_root_text(),
            }

        return {
            "authenticated": True,
            "user": ACCOUNT_STORE.get_user_summary(username),
            "projects": ACCOUNT_STORE.list_projects(username),
            "user_data_folder": self._user_data_root_text(),
        }

    @staticmethod
    def _user_data_root_text() -> str:
        try:
            return USER_DATA_DIR.relative_to(ROOT_DIR).as_posix()
        except ValueError:
            return USER_DATA_DIR.as_posix()


def main() -> None:
    _require_startup_password()
    parser = argparse.ArgumentParser(description="Run Alpha Studio in your browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8080, help="Server port. Default: 8080")
    parser.add_argument(
        "--share-lan",
        action="store_true",
        help="Bind Alpha Studio to 0.0.0.0 so phones and PCs on the same Wi-Fi can open it.",
    )
    args = parser.parse_args()

    host = "0.0.0.0" if args.share_lan else args.host
    SERVER_STATE["host"] = host
    SERVER_STATE["port"] = args.port
    SERVER_STATE["share_lan"] = args.share_lan
    SERVER_STATE["urls"] = _discover_urls(host, args.port, args.share_lan)

    server = ThreadingHTTPServer((host, args.port), AlphaRequestHandler)
    print("Alpha Studio running at:")
    for url in SERVER_STATE["urls"]:
        print(f"  {url}")
    if args.share_lan:
        print("Live sharing is enabled for devices on the same trusted local network.")
    print("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alpha Studio...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
