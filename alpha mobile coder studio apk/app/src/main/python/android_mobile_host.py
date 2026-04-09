from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import socket
import sys
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


PY_ROOT = Path(__file__).resolve().parent
MAIN_DIR = PY_ROOT / "Maine File"
RULES_DIR = PY_ROOT / "Rouls File"
LIBRARY_ASSET_DIR = PY_ROOT / "Libary"
PACKAGES_ASSET_DIR = PY_ROOT / "Packages"

if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

import alpha as alpha_module  # type: ignore
from alpha import AlphaInterpreter  # type: ignore


INDEX_FILE = MAIN_DIR / "index.html"
STYLE_FILE = MAIN_DIR / "style.css"
STUDIO_SCRIPT_FILE = MAIN_DIR / "studio.js"
MANIFEST_FILE = MAIN_DIR / "manifest.webmanifest"
SERVICE_WORKER_FILE = MAIN_DIR / "sw.js"
PACKAGED_DATABASE_SCHEMA = LIBRARY_ASSET_DIR / "database.sql"
PACKAGED_REGISTRY_FILE = PACKAGES_ASSET_DIR / "registry.json"

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 14

RUNTIME_LOCK = threading.RLock()
SERVER_INSTANCE: ThreadingHTTPServer | None = None
SERVER_THREAD: threading.Thread | None = None
SERVER_URL = ""
WORKSPACE_ROOT = PY_ROOT
USER_DATA_DIR = PY_ROOT / "alpha_user_data"
INTERPRETER: AlphaInterpreter | None = None
ACCOUNT_STORE: "StudioUserStore | None" = None
SESSION_STORE: "StudioSessionStore | None" = None
SERVER_STATE = {
    "host": "127.0.0.1",
    "port": 8135,
    "share_lan": False,
    "urls": ["http://127.0.0.1:8135"],
    "platform": "android_apk",
}


def _timestamp_text() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class StudioAccountError(ValueError):
    """Raised when a studio account or project request is invalid."""


class StudioAuthError(PermissionError):
    """Raised when a protected studio action needs an authenticated user."""


class StudioUserStore:
    USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,31}$")

    def __init__(self, users_dir: Path, root_dir: Path) -> None:
        self.users_dir = users_dir
        self.root_dir = root_dir
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

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> dict[str, str | int]:
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
            return path.relative_to(self.root_dir).as_posix()
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


def _copy_default_registry(destination: Path) -> None:
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if PACKAGED_REGISTRY_FILE.exists():
        destination.write_text(PACKAGED_REGISTRY_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def _prepare_runtime(app_files_dir: str | Path) -> None:
    global WORKSPACE_ROOT, USER_DATA_DIR, INTERPRETER, ACCOUNT_STORE, SESSION_STORE

    workspace_root = Path(app_files_dir) / "alpha_mobile_coder_studio"
    library_dir = workspace_root / "Libary"
    packages_dir = workspace_root / "Packages"
    user_data_dir = workspace_root / "alpha_user_data"

    workspace_root.mkdir(parents=True, exist_ok=True)
    library_dir.mkdir(parents=True, exist_ok=True)
    packages_dir.mkdir(parents=True, exist_ok=True)
    user_data_dir.mkdir(parents=True, exist_ok=True)

    _copy_default_registry(packages_dir / "registry.json")

    alpha_module.RULES.ROOT_DIR = workspace_root
    alpha_module.RULES.MAIN_DIR = MAIN_DIR
    alpha_module.RULES.RULES_DIR = RULES_DIR
    alpha_module.RULES.LIBRARY_DIR = library_dir
    alpha_module.RULES.DATABASE_PATH = library_dir / "alpha_data.db"
    alpha_module.RULES.DATABASE_SCHEMA_PATH = PACKAGED_DATABASE_SCHEMA
    alpha_module.RULES.PACKAGE_REGISTRY_PATH = packages_dir / "registry.json"

    WORKSPACE_ROOT = workspace_root
    USER_DATA_DIR = user_data_dir
    INTERPRETER = AlphaInterpreter()
    ACCOUNT_STORE = StudioUserStore(user_data_dir / "users", workspace_root)
    SESSION_STORE = StudioSessionStore()


def _pick_open_port(preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 25):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No open localhost port was available for Alpha Mobile Coder Studio.")


def _wait_for_server(port: int, timeout_seconds: float = 6.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.35):
                return
        except OSError:
            time.sleep(0.06)
    raise RuntimeError("Alpha Mobile Coder Studio could not start its local server in time.")


def start_server(app_files_dir: str, preferred_port: int = 8135) -> str:
    global SERVER_INSTANCE, SERVER_THREAD, SERVER_URL, SERVER_STATE

    with RUNTIME_LOCK:
        if SERVER_INSTANCE is not None and SERVER_THREAD is not None and SERVER_THREAD.is_alive():
            return SERVER_URL

        _prepare_runtime(app_files_dir)
        port = _pick_open_port(preferred_port)
        SERVER_STATE = {
            "host": "127.0.0.1",
            "port": port,
            "share_lan": False,
            "urls": [f"http://127.0.0.1:{port}"],
            "platform": "android_apk",
        }
        SERVER_URL = SERVER_STATE["urls"][0]
        SERVER_INSTANCE = ThreadingHTTPServer(("127.0.0.1", port), AlphaRequestHandler)
        SERVER_INSTANCE.daemon_threads = True
        SERVER_THREAD = threading.Thread(
            target=SERVER_INSTANCE.serve_forever,
            name="AlphaMobileCoderStudioServer",
            daemon=True,
        )
        SERVER_THREAD.start()
        _wait_for_server(port)
        return SERVER_URL


def stop_server() -> None:
    global SERVER_INSTANCE, SERVER_THREAD, SERVER_URL
    with RUNTIME_LOCK:
        if SERVER_INSTANCE is not None:
            SERVER_INSTANCE.shutdown()
            SERVER_INSTANCE.server_close()
        SERVER_INSTANCE = None
        SERVER_THREAD = None
        SERVER_URL = ""


def _interpreter() -> AlphaInterpreter:
    if INTERPRETER is None:
        raise RuntimeError("Alpha interpreter is not ready.")
    return INTERPRETER


def _account_store() -> StudioUserStore:
    if ACCOUNT_STORE is None:
        raise RuntimeError("Alpha account storage is not ready.")
    return ACCOUNT_STORE


def _session_store() -> StudioSessionStore:
    if SESSION_STORE is None:
        raise RuntimeError("Alpha session storage is not ready.")
    return SESSION_STORE


class AlphaRequestHandler(BaseHTTPRequestHandler):
    server_version = "AlphaMobileHTTP/1.0"

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
                self._send_json(_interpreter().get_guide_payload())
                return

            if route == "/api/history":
                self._send_json({"runs": _interpreter().recent_runs(limit=12)})
                return

            if route == "/api/system":
                self._send_json(SERVER_STATE)
                return

            if route == "/api/packages":
                interpreter = _interpreter()
                self._send_json(
                    {
                        "available_packages": interpreter.list_available_packages(),
                        "installed_packages": interpreter.list_installed_packages(),
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
                result = _interpreter().run(source_code)
                self._send_json(result.to_dict())
                return

            if route == "/api/packages/install":
                package_name = payload.get("name", "")
                interpreter = _interpreter()
                record = interpreter.install_package(str(package_name))
                self._send_json(
                    {
                        "installed": record,
                        "available_packages": interpreter.list_available_packages(),
                        "installed_packages": interpreter.list_installed_packages(),
                    }
                )
                return

            if route == "/api/packages/remove":
                package_name = payload.get("name", "")
                interpreter = _interpreter()
                removed = interpreter.remove_package(str(package_name))
                self._send_json(
                    {
                        "removed": removed,
                        "available_packages": interpreter.list_available_packages(),
                        "installed_packages": interpreter.list_installed_packages(),
                    }
                )
                return

            if route == "/api/account/register":
                account_store = _account_store()
                session_store = _session_store()
                user = account_store.register_user(
                    str(payload.get("username", "")),
                    str(payload.get("password", "")),
                )
                session_token = session_store.create_session(str(user["canonical_username"]))
                response = self._account_state_payload(str(user["canonical_username"]))
                response["session"] = session_token
                response["message"] = f"User {user['username']} was created."
                self._send_json(response, status=HTTPStatus.CREATED)
                return

            if route == "/api/account/login":
                account_store = _account_store()
                session_store = _session_store()
                user = account_store.authenticate_user(
                    str(payload.get("username", "")),
                    str(payload.get("password", "")),
                )
                session_token = session_store.create_session(str(user["canonical_username"]))
                response = self._account_state_payload(str(user["canonical_username"]))
                response["session"] = session_token
                response["message"] = f"Welcome back, {user['username']}."
                self._send_json(response)
                return

            if route == "/api/account/logout":
                _session_store().remove_session(self._session_token())
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
                _account_store().change_password(
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
                project = _account_store().save_project(
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
                loaded_project = _account_store().load_project(
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
                deleted_project = _account_store().delete_project(
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
        return _session_store().get_username(self._session_token())

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

        account_store = _account_store()
        return {
            "authenticated": True,
            "user": account_store.get_user_summary(username),
            "projects": account_store.list_projects(username),
            "user_data_folder": self._user_data_root_text(),
        }

    @staticmethod
    def _user_data_root_text() -> str:
        try:
            return USER_DATA_DIR.relative_to(WORKSPACE_ROOT).as_posix()
        except ValueError:
            return USER_DATA_DIR.as_posix()
