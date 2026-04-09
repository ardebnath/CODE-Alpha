from __future__ import annotations

import argparse
import builtins as builtins_module
import csv as csv_module
import datetime as datetime_module
import importlib
import importlib.util
import json
import random as random_module
import re
import sqlite3
import sys
import threading
import traceback
import time as time_module
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Any, Callable


def _load_rules_module():
    rules_path = Path(__file__).resolve().parents[1] / "Rouls File" / "rulls.py"
    spec = importlib.util.spec_from_file_location("alpha_rules", rules_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Alpha rules from {rules_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RULES = _load_rules_module()


class AlphaLanguageError(Exception):
    """Raised when Alpha source code cannot be translated or executed."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        column_number: int | None = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.column_number = column_number


@dataclass
class ImportRequest:
    module_name: str
    alias: str
    line_number: int


@dataclass
class CompiledAlpha:
    python_code: str
    imports: list[ImportRequest]
    source_line_map: list[int]


@dataclass
class AlphaRunResult:
    source_code: str
    translated_code: str
    output_text: str
    error_text: str | None
    duration_ms: float
    status: str
    run_id: int | None
    error_line: int | None
    error_column: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_code": self.source_code,
            "translated_code": self.translated_code,
            "output_text": self.output_text,
            "error_text": self.error_text,
            "duration_ms": round(self.duration_ms, 3),
            "status": self.status,
            "run_id": self.run_id,
            "error_line": self.error_line,
            "error_column": self.error_column,
        }


class AlphaDatabase:
    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        with self._lock, self._connect() as connection:
            connection.executescript(schema_sql)
            connection.commit()

    def record_run(
        self,
        source_code: str,
        translated_code: str,
        status: str,
        output_text: str,
        error_text: str | None,
        duration_ms: float,
    ) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO execution_runs (
                    source_code,
                    translated_code,
                    status,
                    output_text,
                    error_text,
                    duration_ms
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_code, translated_code, status, output_text, error_text, duration_ms),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def set_value(self, key: str, value: Any) -> Any:
        payload = self._encode(value)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO key_value_store (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, payload),
            )
            connection.commit()
        return value

    def get_value(self, key: str, default: Any = None) -> Any:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT value_json FROM key_value_store WHERE key = ?",
                (key,),
            ).fetchone()

        if row is None:
            return default

        return self._decode(row["value_json"])

    def delete_value(self, key: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM key_value_store WHERE key = ?",
                (key,),
            )
            connection.commit()
        return cursor.rowcount > 0

    def list_values(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT key, value_json, updated_at
                FROM key_value_store
                ORDER BY key
                """
            ).fetchall()

        return [
            {
                "key": row["key"],
                "value": self._decode(row["value_json"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def recent_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, status, duration_ms, created_at, error_text
                FROM execution_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "status": row["status"],
                "duration_ms": row["duration_ms"],
                "created_at": row["created_at"],
                "error_text": row["error_text"],
            }
            for row in rows
        ]

    def install_package(
        self,
        name: str,
        title: str,
        description: str,
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO installed_packages (name, title, description, version, installed_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    version = excluded.version
                """,
                (name, title, description, version),
            )
            connection.commit()

        return {
            "name": name,
            "title": title,
            "description": description,
            "version": version,
        }

    def remove_package(self, name: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM installed_packages WHERE name = ?",
                (name,),
            )
            connection.commit()
        return cursor.rowcount > 0

    def installed_packages(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT name, title, description, version, installed_at
                FROM installed_packages
                ORDER BY name
                """
            ).fetchall()

        return [
            {
                "name": row["name"],
                "title": row["title"],
                "description": row["description"],
                "version": row["version"],
                "installed_at": row["installed_at"],
            }
            for row in rows
        ]

    def is_package_installed(self, name: str) -> bool:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM installed_packages WHERE name = ?",
                (name,),
            ).fetchone()
        return row is not None

    def run_read_only_query(self, query: str) -> list[dict[str, Any]]:
        clean_query = query.strip()
        if not clean_query:
            raise AlphaLanguageError("SQL bridge received an empty query.")

        first_word = clean_query.split(None, 1)[0].lower()
        if first_word not in {"select", "with", "pragma"}:
            raise AlphaLanguageError(
                "The SQL bridge is read-only. Use SELECT, WITH, or PRAGMA queries."
            )

        with self._lock, self._connect() as connection:
            rows = connection.execute(clean_query).fetchall()

        return [dict(row) for row in rows]

    @staticmethod
    def _encode(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=True, sort_keys=True)
        except TypeError:
            return json.dumps(str(value), ensure_ascii=True)

    @staticmethod
    def _decode(raw_value: str) -> Any:
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value


class AlphaTranslator:
    BLOCK_OPENERS = {"if", "unless", "while", "repeat", "function", "class", "try", "with"}
    REOPENERS = {"otherwise if", "otherwise", "catch", "finally"}

    def __init__(self, source_code: str) -> None:
        self.source_code = source_code
        self.aliases = sorted(
            RULES.KEYWORD_ALIASES.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    def translate(self) -> CompiledAlpha:
        python_lines: list[str] = []
        imports: list[ImportRequest] = []
        source_line_map: list[int] = []
        indent_level = 0
        in_block_comment = False

        for line_number, raw_line in enumerate(self.source_code.splitlines(), start=1):
            cleaned_line, in_block_comment = self._strip_alpha_comments(
                raw_line,
                in_block_comment,
            )
            cleaned_line = cleaned_line.strip()
            if not cleaned_line:
                continue

            canonical_line = self._canonicalize_line(cleaned_line)
            canonical_line = self._replace_literals_outside_strings(canonical_line)

            if canonical_line == "end":
                indent_level -= 1
                if indent_level < 0:
                    raise AlphaLanguageError(
                        f"Line {line_number}: 'end' does not match an open block."
                    )
                continue

            if canonical_line.startswith("otherwise if "):
                indent_level = self._dedent_for_reopener(indent_level, line_number, "otherwise if")
                statement = self._translate_if_statement(canonical_line, line_number, prefix="elif")
                python_lines.append(self._indent(indent_level) + statement)
                source_line_map.append(line_number)
                indent_level += 1
                continue

            if canonical_line == "otherwise":
                indent_level = self._dedent_for_reopener(indent_level, line_number, "otherwise")
                python_lines.append(self._indent(indent_level) + "else:")
                source_line_map.append(line_number)
                indent_level += 1
                continue

            if canonical_line.startswith("catch"):
                indent_level = self._dedent_for_reopener(indent_level, line_number, "catch")
                python_lines.append(
                    self._indent(indent_level)
                    + self._translate_catch_statement(canonical_line, line_number)
                )
                source_line_map.append(line_number)
                indent_level += 1
                continue

            if canonical_line == "finally":
                indent_level = self._dedent_for_reopener(indent_level, line_number, "finally")
                python_lines.append(self._indent(indent_level) + "finally:")
                source_line_map.append(line_number)
                indent_level += 1
                continue

            translated_line, opens_block, import_request = self._translate_simple_statement(
                canonical_line,
                line_number,
            )

            if import_request is not None:
                imports.append(import_request)
                continue

            python_lines.append(self._indent(indent_level) + translated_line)
            source_line_map.append(line_number)

            if opens_block:
                indent_level += 1

        if indent_level != 0:
            raise AlphaLanguageError("The Alpha source ended before all blocks were closed with 'end'.")

        return CompiledAlpha(
            python_code="\n".join(python_lines) if python_lines else "pass",
            imports=imports,
            source_line_map=source_line_map if source_line_map else [1],
        )

    def _translate_simple_statement(
        self,
        line: str,
        line_number: int,
    ) -> tuple[str, bool, ImportRequest | None]:
        if line.startswith("use "):
            return "", False, self._translate_import_statement(line, line_number)

        if line.startswith("if "):
            return self._translate_if_statement(line, line_number, prefix="if"), True, None

        if line.startswith("unless "):
            return self._translate_unless_statement(line, line_number), True, None

        if line.startswith("while "):
            match = re.fullmatch(r"while\s+(.+?)\s+do", line)
            if not match:
                raise AlphaLanguageError(
                    f"Line {line_number}: while blocks must end with 'do'."
                )
            return f"while {match.group(1)}:", True, None

        if line.startswith("repeat "):
            range_match = re.fullmatch(
                r"repeat\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+step\s+(.+))?",
                line,
            )
            if range_match:
                step = range_match.group(4)
                if step is None:
                    return (
                        f"for {range_match.group(1)} in alpha_range({range_match.group(2)}, {range_match.group(3)}):",
                        True,
                        None,
                    )
                return (
                    f"for {range_match.group(1)} in alpha_range({range_match.group(2)}, {range_match.group(3)}, {step}):",
                    True,
                    None,
                )

            match = re.fullmatch(r"repeat\s+(.+?)\s+in\s+(.+)", line)
            if not match:
                raise AlphaLanguageError(
                    f"Line {line_number}: repeat blocks must look like 'repeat item in items'."
                )
            return f"for {match.group(1)} in {match.group(2)}:", True, None

        if line.startswith("function "):
            match = re.fullmatch(r"function\s+([A-Za-z_]\w*)\((.*?)\)", line)
            if not match:
                raise AlphaLanguageError(
                    f"Line {line_number}: function blocks must look like 'function name(arg1, arg2)'."
                )
            return f"def {match.group(1)}({match.group(2)}):", True, None

        if line.startswith("class "):
            return self._translate_class_statement(line, line_number), True, None

        if line == "try":
            return "try:", True, None

        if line.startswith("with "):
            match = re.fullmatch(r"with\s+(.+?)\s+do", line)
            if not match:
                raise AlphaLanguageError(
                    f"Line {line_number}: with blocks must end with 'do'."
                )
            return f"with {match.group(1)}:", True, None

        if line.startswith("set "):
            assignment = line[4:].strip()
            if "=" not in assignment:
                raise AlphaLanguageError(
                    f"Line {line_number}: set statements must contain '='."
                )
            return assignment, False, None

        if line.startswith("package "):
            return self._translate_package_statement(line, line_number), False, None

        if line.startswith("assert "):
            return f"assert {line[7:]}", False, None

        if line.startswith("raise "):
            return f"raise AlphaLanguageError({line[6:]})", False, None

        if line == "note":
            return "alpha_print()", False, None

        if line.startswith("note "):
            return f"alpha_print({line[5:]})", False, None

        if line.startswith("give "):
            return f"return {line[5:]}", False, None

        if line == "give":
            return "return", False, None

        if line == "stop":
            return "break", False, None

        if line == "skip":
            return "continue", False, None

        return line, False, None

    def _translate_if_statement(self, line: str, line_number: int, prefix: str) -> str:
        pattern = r"(?:if|otherwise if)\s+(.+?)\s+then"
        match = re.fullmatch(pattern, line)
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: if blocks must end with 'then'."
            )
        return f"{prefix} {match.group(1)}:"

    def _translate_unless_statement(self, line: str, line_number: int) -> str:
        match = re.fullmatch(r"unless\s+(.+?)\s+then", line)
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: unless blocks must end with 'then'."
            )
        return f"if not ({match.group(1)}):"

    def _translate_class_statement(self, line: str, line_number: int) -> str:
        match = re.fullmatch(
            r"class\s+([A-Za-z_]\w*)(?:\((.+)\)|\s+(?:extends|from)\s+(.+))?",
            line,
        )
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: class blocks must look like 'class Person', "
                "'class Person(Base)', or 'class Person extends Base'."
            )

        class_name = match.group(1)
        base_expression = match.group(2) or match.group(3)
        if base_expression:
            return f"class {class_name}({base_expression.strip()}):"
        return f"class {class_name}:"

    def _translate_package_statement(self, line: str, line_number: int) -> str:
        match = re.fullmatch(
            r"package\s+([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?",
            line,
        )
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: package must look like 'package text_tools' or 'package text_tools as tools'."
            )

        package_name = match.group(1)
        alias = match.group(2)
        if alias:
            return f'{alias} = alpha_require_package("{package_name}", alias="{alias}")'
        return f'alpha_require_package("{package_name}")'

    def _translate_catch_statement(self, line: str, line_number: int) -> str:
        match = re.fullmatch(r"catch(?:\s+([A-Za-z_]\w*))?", line)
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: catch must be 'catch' or 'catch err'."
            )

        exception_name = match.group(1)
        if exception_name:
            return f"except Exception as {exception_name}:"
        return "except Exception:"

    def _translate_import_statement(self, line: str, line_number: int) -> ImportRequest:
        match = re.fullmatch(
            r"use\s+([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?",
            line,
        )
        if not match:
            raise AlphaLanguageError(
                f"Line {line_number}: use statements must look like 'use math' or 'use math as m'."
            )

        module_name = match.group(1)
        alias = match.group(2) or module_name

        if module_name not in RULES.SAFE_MODULES:
            allowed = ", ".join(sorted(RULES.SAFE_MODULES))
            raise AlphaLanguageError(
                f"Line {line_number}: module '{module_name}' is not allowed. Use one of: {allowed}."
            )

        return ImportRequest(module_name=module_name, alias=alias, line_number=line_number)

    def _dedent_for_reopener(self, indent_level: int, line_number: int, keyword: str) -> int:
        indent_level -= 1
        if indent_level < 0:
            raise AlphaLanguageError(
                f"Line {line_number}: '{keyword}' does not have a matching open block."
            )
        return indent_level

    @staticmethod
    def _indent(level: int) -> str:
        return "    " * level

    @staticmethod
    def _strip_alpha_comments(line: str, in_block_comment: bool) -> tuple[str, bool]:
        result: list[str] = []
        in_single_quote = False
        in_double_quote = False
        escaped = False
        index = 0

        while index < len(line):
            if in_block_comment:
                if line.startswith("$$", index):
                    in_block_comment = False
                    index += 2
                else:
                    index += 1
                continue

            character = line[index]

            if escaped:
                result.append(character)
                escaped = False
                index += 1
                continue

            if character == "\\":
                escaped = True
                result.append(character)
                index += 1
                continue

            if character == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                result.append(character)
                index += 1
                continue

            if character == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                result.append(character)
                index += 1
                continue

            if not in_single_quote and not in_double_quote:
                if line.startswith("$$", index):
                    in_block_comment = True
                    index += 2
                    continue

                if character in {"#", "$"}:
                    break

            result.append(character)
            index += 1

        return "".join(result), in_block_comment

    def _canonicalize_line(self, line: str) -> str:
        lowered = line.lower()
        for alias, canonical in self.aliases:
            if lowered == alias:
                return canonical
            if lowered.startswith(alias + " "):
                return canonical + line[len(alias):]
        return line

    @staticmethod
    def _replace_literals_outside_strings(text: str) -> str:
        result: list[str] = []
        token: list[str] = []
        in_single_quote = False
        in_double_quote = False
        escaped = False

        def flush_token() -> None:
            if not token:
                return
            word = "".join(token)
            replacement = RULES.BOOLEAN_LITERALS.get(word.lower(), word)
            result.append(replacement)
            token.clear()

        for character in text:
            if in_single_quote or in_double_quote:
                result.append(character)
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == "'" and in_single_quote:
                    in_single_quote = False
                elif character == '"' and in_double_quote:
                    in_double_quote = False
                continue

            if character == "'":
                flush_token()
                in_single_quote = True
                result.append(character)
                continue

            if character == '"':
                flush_token()
                in_double_quote = True
                result.append(character)
                continue

            if character.isalnum() or character == "_":
                token.append(character)
            else:
                flush_token()
                result.append(character)

        flush_token()
        return "".join(result)


class AlphaInterpreter:
    def __init__(self) -> None:
        self.database = AlphaDatabase(RULES.DATABASE_PATH, RULES.DATABASE_SCHEMA_PATH)
        self.package_catalog = self._load_package_catalog()
        self.bridge_registry: dict[str, Callable[..., Any]] = {
            "sql": self._bridge_sql,
            "python_expr": self._bridge_python_expression,
            "packages": self._bridge_packages,
        }

    def register_bridge(self, name: str, handler: Callable[..., Any]) -> None:
        self.bridge_registry[name] = handler

    def run(self, source_code: str) -> AlphaRunResult:
        start_time = perf_counter()
        translated_code = ""
        output_lines: list[str] = []
        error_text: str | None = None
        error_line: int | None = None
        error_column: int | None = None
        status = "ok"
        compiled: CompiledAlpha | None = None
        current_import_line: int | None = None

        try:
            compiled = AlphaTranslator(source_code).translate()
            translated_code = compiled.python_code
            environment = self._build_environment(output_lines)

            for import_request in compiled.imports:
                current_import_line = import_request.line_number
                environment[import_request.alias] = self._resolve_safe_module(
                    import_request.module_name
                )

            current_import_line = None
            compiled_code = compile(compiled.python_code, "<alpha>", "exec")
            exec(compiled_code, environment, environment)
        except Exception as exc:  # noqa: BLE001 - surfaced to Alpha users on purpose
            status = "error"
            error_line, error_column = self._resolve_error_location(
                exc,
                compiled,
                current_import_line,
            )
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

        return AlphaRunResult(
            source_code=source_code,
            translated_code=translated_code,
            output_text=output_text,
            error_text=error_text,
            duration_ms=duration_ms,
            status=status,
            run_id=run_id,
            error_line=error_line,
            error_column=error_column,
        )

    def get_guide_payload(self) -> dict[str, Any]:
        return {
            "name": RULES.ALPHA_NAME,
            "tagline": RULES.ALPHA_TAGLINE,
            "requirements": RULES.PROJECT_REQUIREMENTS,
            "rules": [
                {
                    "keyword": rule.keyword,
                    "syntax": rule.syntax,
                    "description": rule.description,
                }
                for rule in RULES.LANGUAGE_RULES
            ],
            "bridges": [
                {
                    "name": bridge.name,
                    "description": bridge.description,
                    "notes": bridge.notes,
                }
                for bridge in RULES.LANGUAGE_BRIDGES
            ],
            "sample_programs": RULES.SAMPLE_PROGRAMS,
            "default_sample": RULES.DEFAULT_SAMPLE_KEY,
            "safe_modules": sorted(RULES.SAFE_MODULES),
            "available_packages": self.list_available_packages(),
            "installed_packages": self.list_installed_packages(),
            "extension_notes": RULES.EXTENSION_NOTES,
        }

    def recent_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.database.recent_runs(limit=limit)

    def _resolve_error_location(
        self,
        error: Exception,
        compiled: CompiledAlpha | None,
        import_line: int | None = None,
    ) -> tuple[int | None, int | None]:
        if isinstance(error, AlphaLanguageError):
            parsed_line = error.line_number
            if parsed_line is None:
                parsed_line = self._parse_line_number_from_message(str(error))
            return parsed_line, error.column_number

        if isinstance(error, SyntaxError):
            translated_line = getattr(error, "lineno", None)
            return (
                self._map_translated_line_to_source(translated_line, compiled),
                getattr(error, "offset", None),
            )

        traceback_frames = traceback.extract_tb(error.__traceback__)
        for frame in reversed(traceback_frames):
            if frame.filename == "<alpha>":
                return self._map_translated_line_to_source(frame.lineno, compiled), None

        return import_line, None

    @staticmethod
    def _parse_line_number_from_message(message: str) -> int | None:
        match = re.match(r"^Line\s+(\d+)", message)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _map_translated_line_to_source(
        translated_line: int | None,
        compiled: CompiledAlpha | None,
    ) -> int | None:
        if translated_line is None or compiled is None:
            return None
        if translated_line < 1 or translated_line > len(compiled.source_line_map):
            return None
        return compiled.source_line_map[translated_line - 1]

    @staticmethod
    def _format_error_text(
        error: Exception,
        error_line: int | None,
        error_column: int | None,
    ) -> str:
        base_message = str(error)
        if not base_message:
            base_message = f"{type(error).__name__}"
        elif not isinstance(error, AlphaLanguageError):
            base_message = f"{type(error).__name__}: {base_message}"

        if error_line is None:
            return base_message

        if base_message.startswith(f"Line {error_line}:") or base_message.startswith(
            f"Line {error_line},"
        ):
            return base_message

        if error_column is not None:
            return f"Line {error_line}, Column {error_column}: {base_message}"
        return f"Line {error_line}: {base_message}"

    def _build_environment(self, output_lines: list[str]) -> dict[str, Any]:
        safe_environment: dict[str, Any] = {
            "__builtins__": {
                "__build_class__": builtins_module.__build_class__,
            },
            "__name__": "__alpha__",
            "Exception": Exception,
            "AlphaLanguageError": AlphaLanguageError,
            "True": True,
            "False": False,
            "None": None,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "current_date": self._current_date,
            "current_datetime": self._current_datetime,
            "current_time": self._current_time,
            "dict": dict,
            "enumerate": enumerate,
            "float": float,
            "getattr": getattr,
            "hasattr": hasattr,
            "int": int,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "object": object,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "setattr": setattr,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "super": super,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            "alpha_print": lambda *args: self._alpha_print(output_lines, *args),
            "alpha_range": self._alpha_range,
            "bridge": self._call_bridge,
            "append_text": self._append_text,
            "available_packages": self.list_available_packages,
            "contains": lambda collection, item: item in collection,
            "erase": self.database.delete_value,
            "exists": self._path_exists,
            "fetch": self.database.get_value,
            "history": self.database.recent_runs,
            "insert_at": self._insert_at,
            "join_text": self._join_text,
            "keys_of": lambda value: list(value.keys()) if hasattr(value, "keys") else [],
            "length": len,
            "make_folder": self._make_folder,
            "package_install": self.install_package,
            "package_remove": self.remove_package,
            "pairs_of": lambda value: list(value.items()) if hasattr(value, "items") else [],
            "packages": self.list_installed_packages,
            "path_text": self._path_text,
            "pop_from": self._pop_from,
            "push": self._push,
            "random_choice": self._random_choice,
            "random_number": self._random_number,
            "read_csv_rows": self._read_csv_rows,
            "read_text": self._read_text,
            "read_json": json.loads,
            "records": self.database.list_values,
            "replace_text": lambda text, old, new: str(text).replace(str(old), str(new)),
            "reverse_items": self._reverse_items,
            "safe_open": self._safe_open,
            "slice_of": self._slice_of,
            "sleep_ms": self._sleep_ms,
            "sort_items": self._sort_items,
            "split_text": lambda text, separator=None: str(text).split(separator),
            "store": self.database.set_value,
            "timestamp_text": self._timestamp_text,
            "to_number": self._to_number,
            "to_text": self._to_text,
            "values_of": lambda value: list(value.values()) if hasattr(value, "values") else [],
            "write_csv_rows": self._write_csv_rows,
            "write_text": self._write_text,
            "write_json": lambda value: json.dumps(value, ensure_ascii=True, sort_keys=True),
        }

        safe_environment["open"] = self._safe_open

        def alpha_require_package(name: str, alias: str | None = None) -> Any:
            exports = self.require_package(name)
            namespace = SimpleNamespace(**exports)
            if alias:
                safe_environment[alias] = namespace
                return namespace

            safe_environment.update(exports)
            return namespace

        safe_environment["alpha_require_package"] = alpha_require_package
        return safe_environment

    @staticmethod
    def _alpha_print(output_lines: list[str], *values: Any) -> None:
        if not values:
            output_lines.append("")
            return
        output_lines.append(" ".join(str(value) for value in values))

    @staticmethod
    def _push(items: list[Any], value: Any) -> list[Any]:
        items.append(value)
        return items

    @staticmethod
    def _insert_at(items: list[Any], index: int, value: Any) -> list[Any]:
        items.insert(index, value)
        return items

    @staticmethod
    def _pop_from(items: list[Any], index: int = -1) -> Any:
        return items.pop(index)

    @staticmethod
    def _slice_of(value: Any, start: int | None = None, stop: int | None = None, step: int | None = None) -> Any:
        return value[slice(start, stop, step)]

    @staticmethod
    def _to_number(value: Any) -> float | int:
        text = str(value)
        if "." in text:
            return float(text)
        return int(text)

    @staticmethod
    def _to_text(value: Any) -> str:
        return str(value)

    @staticmethod
    def _join_text(items: Any, separator: str = "") -> str:
        return str(separator).join(str(item) for item in items)

    @staticmethod
    def _current_date() -> str:
        return datetime_module.date.today().isoformat()

    @staticmethod
    def _current_time() -> str:
        return datetime_module.datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _current_datetime() -> str:
        return datetime_module.datetime.now().isoformat(sep=" ", timespec="seconds")

    @staticmethod
    def _timestamp_text() -> str:
        return datetime_module.datetime.now().isoformat(sep=" ", timespec="seconds")

    @staticmethod
    def _sleep_ms(milliseconds: Any) -> bool:
        time_module.sleep(float(milliseconds) / 1000.0)
        return True

    @staticmethod
    def _random_choice(items: Any) -> Any:
        return random_module.choice(list(items))

    @staticmethod
    def _random_number(start: Any, end: Any) -> int:
        return random_module.randint(int(start), int(end))

    @staticmethod
    def _sort_items(items: Any, reverse: Any = False) -> list[Any]:
        try:
            return sorted(items, reverse=bool(reverse))
        except TypeError:
            return sorted(items, key=lambda item: str(item), reverse=bool(reverse))

    @staticmethod
    def _reverse_items(items: Any) -> list[Any]:
        values = list(items)
        values.reverse()
        return values

    @staticmethod
    def _alpha_range(start: Any, end: Any, step: Any | None = None) -> range:
        start_int = int(start)
        end_int = int(end)
        if step is None:
            step_int = 1 if end_int >= start_int else -1
        else:
            step_int = int(step)

        if step_int == 0:
            raise AlphaLanguageError("alpha_range step cannot be zero.")

        inclusive_end = end_int + (1 if step_int > 0 else -1)
        return range(start_int, inclusive_end, step_int)

    def _call_bridge(self, name: str, payload: Any, *extra: Any) -> Any:
        if name not in self.bridge_registry:
            available = ", ".join(sorted(self.bridge_registry))
            raise AlphaLanguageError(
                f"Unknown bridge '{name}'. Available bridges: {available}."
            )
        return self.bridge_registry[name](payload, *extra)

    def _bridge_sql(self, query: str, *_: Any) -> list[dict[str, Any]]:
        if not isinstance(query, str):
            raise AlphaLanguageError("The SQL bridge expects a SQL string.")
        return self.database.run_read_only_query(query)

    def _bridge_python_expression(self, expression: str, *_: Any) -> Any:
        if not isinstance(expression, str):
            raise AlphaLanguageError("The python_expr bridge expects a Python expression string.")

        safe_expression_globals = self._build_environment([])
        safe_expression_globals.update(
            {
                name: self._resolve_safe_module(name)
                for name in RULES.SAFE_MODULES
            }
        )
        return eval(expression, safe_expression_globals, safe_expression_globals)

    def _resolve_safe_module(self, module_name: str) -> Any:
        if module_name not in RULES.SAFE_MODULES:
            available = ", ".join(sorted(RULES.SAFE_MODULES))
            raise AlphaLanguageError(
                f"Module '{module_name}' is not allowed. Available modules: {available}."
            )

        module_value = RULES.SAFE_MODULES[module_name]
        if isinstance(module_value, str):
            return importlib.import_module(module_value)
        return module_value

    def _bridge_packages(self, command: str, *_: Any) -> Any:
        if not isinstance(command, str):
            raise AlphaLanguageError("The packages bridge expects a text command.")

        normalized = command.strip().lower()
        if normalized in {"installed", "list", "packages"}:
            return self.list_installed_packages()
        if normalized in {"available", "catalog"}:
            return self.list_available_packages()
        if normalized.startswith("install "):
            return self.install_package(normalized.split(" ", 1)[1].strip())
        if normalized.startswith("remove "):
            return self.remove_package(normalized.split(" ", 1)[1].strip())

        raise AlphaLanguageError(
            "Package bridge commands: installed, available, install <name>, remove <name>."
        )

    def _load_package_catalog(self) -> dict[str, dict[str, Any]]:
        registry_path = RULES.PACKAGE_REGISTRY_PATH
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        default_catalog = [
            {
                "name": package.name,
                "title": package.title,
                "description": package.description,
                "exports": list(package.exports),
                "tags": list(package.tags),
                "version": "1.0.0",
            }
            for package in RULES.PACKAGE_CATALOG
        ]

        if not registry_path.exists():
            registry_path.write_text(json.dumps(default_catalog, indent=2), encoding="utf-8")
            catalog_items = default_catalog
        else:
            try:
                catalog_items = json.loads(registry_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                catalog_items = default_catalog

        return {item["name"]: item for item in catalog_items}

    def list_available_packages(self) -> list[dict[str, Any]]:
        installed_names = {
            package["name"] for package in self.database.installed_packages()
        }
        packages: list[dict[str, Any]] = []

        for name in sorted(self.package_catalog):
            package = dict(self.package_catalog[name])
            package["installed"] = name in installed_names
            packages.append(package)

        return packages

    def list_installed_packages(self) -> list[dict[str, Any]]:
        return self.database.installed_packages()

    def install_package(self, package_name: str) -> dict[str, Any]:
        normalized = package_name.strip()
        if normalized not in self.package_catalog:
            available = ", ".join(sorted(self.package_catalog))
            raise AlphaLanguageError(
                f"Unknown package '{normalized}'. Available packages: {available}."
            )

        package = self.package_catalog[normalized]
        record = self.database.install_package(
            name=package["name"],
            title=package["title"],
            description=package["description"],
            version=package.get("version", "1.0.0"),
        )
        record["exports"] = package.get("exports", [])
        return record

    def remove_package(self, package_name: str) -> bool:
        return self.database.remove_package(package_name.strip())

    def require_package(self, package_name: str) -> dict[str, Callable[..., Any]]:
        normalized = package_name.strip()
        if normalized not in self.package_catalog:
            available = ", ".join(sorted(self.package_catalog))
            raise AlphaLanguageError(
                f"Unknown package '{normalized}'. Available packages: {available}."
            )

        if not self.database.is_package_installed(normalized):
            self.install_package(normalized)

        return self._build_package_exports(normalized)

    def _build_package_exports(self, package_name: str) -> dict[str, Callable[..., Any]]:
        if package_name == "collections_plus":
            return {
                "chunk_items": self._chunk_items,
                "group_by_key": self._group_by_key,
                "unique_items": self._unique_items,
            }
        if package_name == "text_tools":
            return {
                "slugify": self._slugify,
                "title_case": self._title_case,
                "word_count": self._word_count,
            }
        if package_name == "math_plus":
            return {
                "average_of": self._average_of,
                "clamp_value": self._clamp_value,
                "percent_of": self._percent_of,
            }

        raise AlphaLanguageError(
            f"Package '{package_name}' is registered but no export builder exists for it."
        )

    def _resolve_workspace_path(self, raw_path: str | Path) -> Path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = RULES.ROOT_DIR / path

        resolved = path.resolve()
        workspace_root = RULES.ROOT_DIR.resolve()
        if resolved != workspace_root and workspace_root not in resolved.parents:
            raise AlphaLanguageError(
                "Alpha file access must stay inside the project workspace."
            )
        return resolved

    def _path_exists(self, raw_path: str | Path) -> bool:
        return self._resolve_workspace_path(raw_path).exists()

    def _path_text(self, raw_path: str | Path) -> str:
        return str(self._resolve_workspace_path(raw_path))

    def _make_folder(self, raw_path: str | Path) -> str:
        path = self._resolve_workspace_path(raw_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def _read_text(self, raw_path: str | Path) -> str:
        path = self._resolve_workspace_path(raw_path)
        return path.read_text(encoding="utf-8")

    def _read_csv_rows(self, raw_path: str | Path) -> list[Any]:
        path = self._resolve_workspace_path(raw_path)
        with path.open("r", encoding="utf-8", newline="") as file_handle:
            reader = csv_module.DictReader(file_handle)
            if reader.fieldnames is None:
                file_handle.seek(0)
                plain_reader = csv_module.reader(file_handle)
                return [row for row in plain_reader]
            return [dict(row) for row in reader]

    def _write_text(self, raw_path: str | Path, content: Any) -> str:
        path = self._resolve_workspace_path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        return str(path)

    def _write_csv_rows(
        self,
        raw_path: str | Path,
        rows: Any,
        headers: Any = None,
    ) -> str:
        path = self._resolve_workspace_path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows_list = list(rows)

        with path.open("w", encoding="utf-8", newline="") as file_handle:
            if not rows_list:
                return str(path)

            first_row = rows_list[0]
            if isinstance(first_row, dict):
                header_list = list(headers) if headers is not None else list(first_row.keys())
                writer = csv_module.DictWriter(file_handle, fieldnames=header_list)
                writer.writeheader()
                writer.writerows(rows_list)
            else:
                writer = csv_module.writer(file_handle)
                if headers is not None:
                    writer.writerow(list(headers))
                writer.writerows(rows_list)

        return str(path)

    def _append_text(self, raw_path: str | Path, content: Any) -> str:
        path = self._resolve_workspace_path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(str(content))
        return str(path)

    def _safe_open(
        self,
        raw_path: str | Path,
        mode: str = "r",
        *args: Any,
        **kwargs: Any,
    ):
        path = self._resolve_workspace_path(raw_path)
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            path.parent.mkdir(parents=True, exist_ok=True)

        if "encoding" not in kwargs and "b" not in mode:
            kwargs["encoding"] = "utf-8"
        return path.open(mode, *args, **kwargs)

    @staticmethod
    def _chunk_items(items: Any, size: Any) -> list[list[Any]]:
        chunk_size = int(size)
        if chunk_size <= 0:
            raise AlphaLanguageError("chunk_items size must be greater than zero.")

        sequence = list(items)
        return [
            sequence[index:index + chunk_size]
            for index in range(0, len(sequence), chunk_size)
        ]

    @staticmethod
    def _unique_items(items: Any) -> list[Any]:
        result: list[Any] = []
        for item in items:
            if item not in result:
                result.append(item)
        return result

    @staticmethod
    def _group_by_key(items: Any, selector: Any) -> dict[Any, list[Any]]:
        grouped: dict[Any, list[Any]] = {}

        for item in items:
            if callable(selector):
                key = selector(item)
            elif hasattr(item, "get"):
                key = item.get(selector)
            else:
                key = getattr(item, str(selector), None)
            grouped.setdefault(key, []).append(item)

        return grouped

    @staticmethod
    def _slugify(text: Any) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", str(text).strip().lower())
        return normalized.strip("-")

    @staticmethod
    def _title_case(text: Any) -> str:
        return str(text).title()

    @staticmethod
    def _word_count(text: Any) -> int:
        return len(re.findall(r"\S+", str(text)))

    @staticmethod
    def _average_of(numbers: Any) -> float:
        values = list(numbers)
        if not values:
            raise AlphaLanguageError("average_of needs at least one value.")
        return sum(values) / len(values)

    @staticmethod
    def _clamp_value(value: Any, minimum: Any, maximum: Any) -> Any:
        return max(minimum, min(value, maximum))

    @staticmethod
    def _percent_of(part: Any, whole: Any) -> float:
        whole_value = float(whole)
        if whole_value == 0:
            raise AlphaLanguageError("percent_of cannot divide by zero.")
        return (float(part) / whole_value) * 100.0


def _read_source_from_argument(argument: str) -> str:
    path = Path(argument)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return argument


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Alpha language source code.")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Path to an Alpha source file or inline Alpha code.",
    )
    parser.add_argument(
        "--show-python",
        action="store_true",
        help="Show translated Python after running the Alpha code.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run the default Alpha sample program.",
    )

    args = parser.parse_args(argv)
    interpreter = AlphaInterpreter()

    if args.sample:
        source_code = RULES.SAMPLE_PROGRAMS[RULES.DEFAULT_SAMPLE_KEY]["source"]
    elif args.source:
        source_code = _read_source_from_argument(args.source)
    else:
        source_code = RULES.SAMPLE_PROGRAMS[RULES.DEFAULT_SAMPLE_KEY]["source"]

    result = interpreter.run(source_code)

    if result.output_text:
        print(result.output_text)

    if result.error_text:
        print(result.error_text, file=sys.stderr)

    if args.show_python:
        print("\n[Translated Python]")
        print(result.translated_code)

    return 1 if result.status == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
