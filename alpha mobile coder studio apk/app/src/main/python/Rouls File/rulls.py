from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import collections as collections_module
import csv as csv_module
import datetime as datetime_module
import functools as functools_module
import itertools as itertools_module
import json as json_module
import math
import pathlib as pathlib_module
import random
import re as re_module
import statistics
import time as time_module


ROOT_DIR = Path(__file__).resolve().parents[1]
MAIN_DIR = ROOT_DIR / "Maine File"
RULES_DIR = ROOT_DIR / "Rouls File"
LIBRARY_DIR = ROOT_DIR / "Libary"
DATABASE_PATH = LIBRARY_DIR / "alpha_data.db"
DATABASE_SCHEMA_PATH = LIBRARY_DIR / "database.sql"


@dataclass(frozen=True)
class LanguageRule:
    keyword: str
    syntax: str
    description: str


@dataclass(frozen=True)
class LanguageBridge:
    name: str
    description: str
    notes: str


@dataclass(frozen=True)
class PackageDefinition:
    name: str
    title: str
    description: str
    exports: tuple[str, ...]
    tags: tuple[str, ...]


ALPHA_NAME = "Alpha"
ALPHA_TAGLINE = "A human-friendly interpreted language powered by a Python runtime."

BOOLEAN_LITERALS = {
    "true": "True",
    "false": "False",
    "nothing": "None",
    "null": "None",
}

KEYWORD_ALIASES = {
    "otherwise if": "otherwise if",
    "else if": "otherwise if",
    "elif": "otherwise if",
    "warna agar": "otherwise if",
    "otherwise": "otherwise",
    "else": "otherwise",
    "warna": "otherwise",
    "catch": "catch",
    "pakdo": "catch",
    "finally": "finally",
    "aakhir": "finally",
    "class": "class",
    "function": "function",
    "task": "function",
    "kaam": "function",
    "repeat": "repeat",
    "for": "repeat",
    "each": "repeat",
    "dohrao": "repeat",
    "while": "while",
    "jabtak": "while",
    "unless": "unless",
    "jab nahi": "unless",
    "if": "if",
    "agar": "if",
    "set": "set",
    "let": "set",
    "remember": "set",
    "keep": "set",
    "rakho": "set",
    "note": "note",
    "print": "note",
    "say": "note",
    "bolo": "note",
    "give": "give",
    "return": "give",
    "wapas": "give",
    "use": "use",
    "load": "use",
    "lao": "use",
    "package": "package",
    "plugin": "package",
    "try": "try",
    "koshish": "try",
    "with": "with",
    "saath": "with",
    "assert": "assert",
    "check": "assert",
    "raise": "raise",
    "throw": "raise",
    "stop": "stop",
    "break": "stop",
    "skip": "skip",
    "continue": "skip",
    "end": "end",
    "samapt": "end",
}

SAFE_MODULES = {
    "collections": collections_module,
    "csv": csv_module,
    "datetime": datetime_module,
    "functools": functools_module,
    "itertools": itertools_module,
    "json": json_module,
    "math": math,
    "pathlib": pathlib_module,
    "random": random,
    "re": re_module,
    "statistics": statistics,
    "time": time_module,
    "turtle": "turtle",
}

LANGUAGE_RULES = [
    LanguageRule("note", 'note "Hello, Alpha!"', "Write text or values to the output panel."),
    LanguageRule("set", 'set total = 10', "Create or update a variable with a readable assignment."),
    LanguageRule("$ comment", '$ this is one line comment text', "Ignore one full line or the rest of a line as a comment."),
    LanguageRule("$$ comment $$", "$$\nthis is multi line comment text\n$$", "Ignore a multi-line comment block until the closing $$ marker."),
    LanguageRule("if", "if total > 5 then", "Run a block only when a condition is true."),
    LanguageRule("otherwise", "otherwise", "Fallback block after an if statement."),
    LanguageRule("while", "while total < 100 do", "Repeat code while a condition stays true."),
    LanguageRule("repeat", "repeat item in numbers", "Loop through any iterable value."),
    LanguageRule(
        "repeat from",
        "repeat number from 1 to 10 step 2",
        "Loop through an inclusive numeric range using readable start, end, and step values.",
    ),
    LanguageRule(
        "class",
        "class Person",
        "Define an object with attributes and methods. You can also write 'class Student extends Person'.",
    ),
    LanguageRule("function", "function greet(name)", "Define reusable logic with named arguments."),
    LanguageRule("unless", "unless is_ready then", "Run a block only when a condition is false."),
    LanguageRule("package", "package collections_plus", "Load helpers from an installed Alpha package."),
    LanguageRule("give", "give total", "Return a value from a function."),
    LanguageRule("use", "use math", "Import a safe built-in Python module into Alpha."),
    LanguageRule("assert", 'assert total > 0, "total must stay positive"', "Stop execution when an important condition is false."),
    LanguageRule("raise", 'raise "Alpha error message"', "Raise a readable Alpha runtime error on purpose."),
    LanguageRule("try", "try", "Start an error-handling block."),
    LanguageRule("catch", "catch err", "Handle an exception raised inside try."),
    LanguageRule("with", 'with open("data.txt") as file do', "Use Python-style context managers when needed."),
    LanguageRule("end", "end", "Close the current Alpha block."),
]

LANGUAGE_BRIDGES = [
    LanguageBridge(
        "sql",
        "Run read-only SQL queries against Alpha's SQLite database.",
        'Example: bridge("sql", "SELECT key, value_json FROM key_value_store")',
    ),
    LanguageBridge(
        "python_expr",
        "Evaluate a safe Python expression when you want to extend Alpha quickly.",
        'Example: bridge("python_expr", "sum([1, 2, 3, 4])")',
    ),
    LanguageBridge(
        "packages",
        "Inspect installed Alpha packages and their exported helpers.",
        'Example: bridge("packages", "installed")',
    ),
]

PACKAGE_CATALOG = (
    PackageDefinition(
        name="collections_plus",
        title="Collections Plus",
        description="Extra list and dictionary helpers for complex data processing.",
        exports=("chunk_items", "group_by_key", "unique_items"),
        tags=("data", "collections", "utility"),
    ),
    PackageDefinition(
        name="text_tools",
        title="Text Tools",
        description="Formatting, slug generation, and text shaping helpers.",
        exports=("slugify", "title_case", "word_count"),
        tags=("text", "web", "utility"),
    ),
    PackageDefinition(
        name="math_plus",
        title="Math Plus",
        description="Higher-level math helpers useful for reports and analytics.",
        exports=("average_of", "clamp_value", "percent_of"),
        tags=("math", "analytics"),
    ),
)

PACKAGE_REGISTRY_PATH = ROOT_DIR / "Packages" / "registry.json"

SAMPLE_PROGRAMS = {
    "hello_world": {
        "title": "Hello World",
        "source": """note "Hello from Alpha!"

set name = "world"

function greet(person)
    note "Hello, " + person + "!"
end

greet(name)
""",
    },
    "database_demo": {
        "title": "Database Demo",
        "source": """note "Saving a record into Alpha database"

store("language", {"name": "Alpha", "type": "interpreted"})
set saved = fetch("language")

note saved
note bridge("sql", "SELECT key, value_json FROM key_value_store ORDER BY key")
""",
    },
    "json_demo": {
        "title": "JSON Demo",
        "source": """set profile = {"name": "Bluear_cod", "tools": ["Alpha", "Python"]}

set raw = write_json(profile)
note raw
note read_json(raw)
""",
    },
    "comment_demo": {
        "title": "Comment Demo",
        "source": """$ This is a one line Alpha comment
note "Code before block comment"

$$
This whole block is ignored by Alpha.
You can write many lines here.
$$

set name = "Alpha"
note name $ inline one line comment after code
""",
    },
    "package_demo": {
        "title": "Package Demo",
        "source": """package text_tools
package math_plus

set words = "alpha is ready for mobile and desktop"
note slugify(words)
note title_case(words)
note word_count(words)
note percent_of(25, 80)
""",
    },
    "package_alias_demo": {
        "title": "Package Alias Demo",
        "source": """package text_tools as text_tools_lib
package math_plus as math_plus_lib

set text = "alpha package alias demo"
note text_tools_lib.slugify(text)
note math_plus_lib.percent_of(18, 24)
""",
    },
    "function_report_demo": {
        "title": "Function Report Demo",
        "source": """function total_scores(values)
    set total = 0

    repeat value in values
        set total = total + value
    end

    give total
end

set scores = [80, 92, 75]
note total_scores(scores)
note length(scores)
""",
    },
    "class_demo": {
        "title": "Class Demo",
        "source": """class Person
    function __init__(self, name)
        set self.name = name
    end

    function greet(self)
        give "Hello, " + self.name
    end
end

class Student extends Person
    function __init__(self, name, level)
        Person.__init__(self, name)
        set self.level = level
    end

    function describe(self)
        give self.greet() + " from level " + str(self.level)
    end
end

set learner = Student("Aritra", 3)
note learner.describe()
""",
    },
    "file_demo": {
        "title": "File Demo",
        "source": """make_folder("notes")

write_text("notes/alpha.txt", "Alpha line 1")
append_text("notes/alpha.txt", "\\nAlpha line 2")

note exists("notes/alpha.txt")
note read_text("notes/alpha.txt")
""",
    },
    "context_file_demo": {
        "title": "Context File Demo",
        "source": """make_folder("notes")

with open("notes/context_demo.txt", "w") as file do
    file.write("Alpha context manager demo")
end

with open("notes/context_demo.txt", "r") as file do
    note file.read()
end
""",
    },
    "error_demo": {
        "title": "Error Demo",
        "source": """try
    assert length([1, 2, 3]) == 3, "List size changed"
    raise "This is a sample Alpha error"
catch err
    note err
finally
    note "Error demo finished"
end
""",
    },
    "csv_report_demo": {
        "title": "CSV Report Demo",
        "source": """package math_plus

write_csv_rows(
    "reports/students.csv",
    [
        {"name": "Ali", "score": 80},
        {"name": "Sara", "score": 92},
        {"name": "Ravi", "score": 75}
    ]
)

set rows = read_csv_rows("reports/students.csv")
note rows
note average_of([80, 92, 75])
""",
    },
    "alias_demo": {
        "title": "Alias Demo",
        "source": """bolo "Alpha alias example"
rakho name = "Bluear_cod"

agar true then
    bolo name
end
""",
    },
    "turtle_bounce": {
        "title": "Turtle Bounce",
        "source": """use turtle

set window = turtle.Screen()
window.bgcolor("white")
window.title("Alpha Turtle Animation")
window.tracer(0)

set mover = turtle.Turtle()
mover.shape("circle")
mover.color("blue")
mover.penup()

repeat frame from 1 to 1200
    mover.forward(1)
    if mover.xcor() > 200 or mover.xcor() < -200 then
        mover.right(180)
    end
    window.update()
end

window.mainloop()
""",
    },
    "feature_showcase": {
        "title": "Feature Showcase",
        "source": """unless false then
    note "Unless logic is working"
end

repeat number from 1 to 5 step 2
    note number
end

set data = [1, 1, 2, 3, 3, 4]
package collections_plus
note unique_items(data)
note chunk_items(data, 2)
""",
    },
    "runtime_upgrade_demo": {
        "title": "Runtime Upgrade Demo",
        "source": """assert 2 + 2 == 4, "Math should work"

note current_date()
note current_time()
note timestamp_text()

set scores = [50, 20, 80, 20]
note sort_items(scores)
note reverse_items(scores)

write_csv_rows(
    "reports/demo.csv",
    [
        {"name": "Ali", "score": 80},
        {"name": "Sara", "score": 92}
    ]
)

note read_csv_rows("reports/demo.csv")
""",
    },
    "random_time_demo": {
        "title": "Random And Time Demo",
        "source": """note current_date()
note current_time()
note timestamp_text()

set colors = ["red", "green", "blue"]
note random_choice(colors)
note random_number(1, 10)
""",
    },
    "complex_flow": {
        "title": "Complex Flow",
        "source": """use math

set total = 0
set squares = []

repeat number in range(1, 6)
    push(squares, number * number)
    set total = total + math.sqrt(number)
end

if total > 8 then
    note "Square list:"
    note squares
    note round(total, 3)
otherwise
    note "Total was smaller than expected"
end
""",
    },
}

DEFAULT_SAMPLE_KEY = "hello_world"

PROJECT_REQUIREMENTS = [
    "Python 3.11 or newer",
    "A modern browser such as Chrome, Edge, or Firefox",
    "No third-party Python packages are required",
    "Phone and PC can use Alpha Studio on the same Wi-Fi when the server runs on 0.0.0.0",
]

EXTENSION_NOTES = [
    "Add new human-language keywords by extending KEYWORD_ALIASES.",
    "Add new safe Python modules by extending SAFE_MODULES.",
    "Add new bridges in AlphaInterpreter.register_bridge for SQL, other languages, or native tools.",
    "Add new packages by extending PACKAGE_CATALOG and the package export builder in the interpreter.",
]
