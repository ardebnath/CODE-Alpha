from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk
    from tkinter.scrolledtext import ScrolledText
except ModuleNotFoundError as error:  # pragma: no cover - depends on local Python build
    raise SystemExit(
        "Tkinter is required for Alpha desktop software. "
        "Use a standard Python 3.11+ installation that includes tkinter."
    ) from error


APP_TITLE = "Alpha Language System Software"
STARTUP_PASSWORD = "aritra1234"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILE = PROJECT_ROOT / "Maine File" / "alpha.py"
EXAMPLES_DIR = PROJECT_ROOT / "Examples"


def load_alpha_runtime() -> Any:
    spec = importlib.util.spec_from_file_location("alpha_runtime_desktop", RUNTIME_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Alpha runtime from {RUNTIME_FILE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AlphaInterpreter = load_alpha_runtime().AlphaInterpreter


def authorize_desktop_startup() -> None:
    gate = tk.Tk()
    gate.withdraw()
    gate.update_idletasks()

    try:
        for attempt in range(3):
            typed_password = simpledialog.askstring(
                APP_TITLE,
                "Enter startup password:",
                show="*",
                parent=gate,
            )
            if typed_password == STARTUP_PASSWORD:
                return
            if typed_password is None:
                messagebox.showwarning(APP_TITLE, "Startup cancelled.", parent=gate)
                raise SystemExit(1)

            remaining = 2 - attempt
            if remaining > 0:
                messagebox.showerror(
                    APP_TITLE,
                    f"Wrong password. {remaining} attempt(s) left.",
                    parent=gate,
                )
            else:
                messagebox.showerror(
                    APP_TITLE,
                    "Access denied. Desktop Alpha software did not start.",
                    parent=gate,
                )
    finally:
        gate.destroy()

    raise SystemExit(1)


class AlphaDesktopSoftware(tk.Tk):
    BG = "#07111d"
    PANEL = "#10263a"
    PANEL_SOFT = "#0b1b2b"
    PANEL_STRONG = "#081420"
    EDITOR = "#08131f"
    BORDER = "#2c4a60"
    TEXT = "#eef4f9"
    MUTED = "#9ab3c7"
    ACCENT = "#ffb84d"
    SKY = "#6ad9ff"
    SUCCESS = "#4bd6a4"
    DANGER = "#ff7a7a"

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1520x920")
        self.minsize(1180, 760)
        self.configure(bg=self.BG)

        self.interpreter = AlphaInterpreter()
        self.guide_payload: dict[str, Any] = {}
        self.sample_titles: dict[str, str] = {}
        self.rules: list[dict[str, Any]] = []
        self.bridges: list[dict[str, Any]] = []
        self.packages: dict[str, dict[str, Any]] = {}
        self.history: dict[str, dict[str, Any]] = {}
        self.run_snapshots: dict[str, dict[str, Any]] = {}
        self.current_file: Path | None = None

        self.status_text = tk.StringVar(value="Ready")
        self.info_text = tk.StringVar(value="Desktop software is ready.")
        self.file_text = tk.StringVar(value="Workspace file: unsaved draft")
        self.sample_choice = tk.StringVar(value="")
        self.samples_metric_text = tk.StringVar(value="0 starter programs")
        self.packages_metric_text = tk.StringVar(value="0 packages available")
        self.history_metric_text = tk.StringVar(value="0 recent runs")
        self.runtime_metric_text = tk.StringVar(value="Desktop Alpha runtime")

        self._setup_style()
        self._build_ui()
        self.bind_all("<Control-Return>", self.run_alpha_event)
        self.bind_all("<Control-s>", self.save_file_event)
        self.bind_all("<Control-o>", self.open_file_event)
        self.refresh_all()
        self.after(50, self.load_default_sample)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=self.BG, foreground=self.TEXT)
        style.configure("TNotebook", background=self.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.PANEL_SOFT, foreground=self.MUTED, padding=(18, 11))
        style.map("TNotebook.Tab", background=[("selected", self.PANEL)], foreground=[("selected", self.ACCENT)])
        style.configure("TButton", background=self.PANEL_SOFT, foreground=self.TEXT, bordercolor=self.BORDER, padding=(12, 8))
        style.map("TButton", background=[("active", self.PANEL)], foreground=[("active", self.TEXT)])
        style.configure("Accent.TButton", background=self.ACCENT, foreground="#1d1200", bordercolor=self.ACCENT, padding=(12, 8))
        style.map("Accent.TButton", background=[("active", "#f2a238")], foreground=[("active", "#1d1200")])
        style.configure("TCombobox", fieldbackground=self.EDITOR, background=self.PANEL, foreground=self.TEXT, arrowcolor=self.ACCENT)
        style.map("TCombobox", fieldbackground=[("readonly", self.EDITOR)], foreground=[("readonly", self.TEXT)])
        style.configure("Treeview", background=self.EDITOR, fieldbackground=self.EDITOR, foreground=self.TEXT, rowheight=28)
        style.configure("Treeview.Heading", background=self.PANEL_SOFT, foreground=self.ACCENT)
        style.map("Treeview", background=[("selected", "#244359")], foreground=[("selected", self.TEXT)])

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1, bd=0)

    def _metric_card(self, parent: tk.Widget, title: str, variable: tk.StringVar, accent: str) -> tk.Frame:
        card = tk.Frame(parent, bg=self.PANEL_SOFT, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        tk.Label(card, text=title, bg=self.PANEL_SOFT, fg=accent, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            card,
            textvariable=variable,
            bg=self.PANEL_SOFT,
            fg=self.TEXT,
            justify="left",
            wraplength=180,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=14, pady=(0, 12))
        return card

    def _style_listbox(self, widget: tk.Listbox, *, width: int | None = None) -> None:
        widget.configure(
            bg=self.EDITOR,
            fg=self.TEXT,
            selectbackground="#244359",
            selectforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        if width is not None:
            widget.configure(width=width)

    def _text_box(self, parent: tk.Widget, *, read_only: bool, wrap: str, font_size: int = 10) -> ScrolledText:
        widget = ScrolledText(
            parent,
            wrap=wrap,
            undo=not read_only,
            bg=self.EDITOR,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground="#27465a",
            selectforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=12,
            font=("Cascadia Code", font_size),
        )
        if read_only:
            widget.configure(state="disabled")
        return widget

    @staticmethod
    def set_readonly(widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def set_status(self, text: str, color: str, info: str) -> None:
        self.status_text.set(text)
        tone = {
            self.TEXT: self.PANEL_SOFT,
            self.ACCENT: "#3a2914",
            self.SUCCESS: "#173125",
            self.DANGER: "#3b171d",
            self.SKY: "#163448",
        }
        self.status_value.configure(fg=color, bg=tone.get(color, self.PANEL_SOFT))
        self.info_text.set(info)

    def _build_ui(self) -> None:
        header = self._card(self)
        header.pack(fill="x", padx=18, pady=(18, 10))
        hero = tk.Frame(header, bg=self.PANEL)
        hero.pack(fill="x", padx=18, pady=18)

        hero_left = tk.Frame(hero, bg=self.PANEL)
        hero_left.pack(side="left", fill="both", expand=True)
        hero_right = tk.Frame(hero, bg=self.PANEL)
        hero_right.pack(side="right", padx=(18, 0))

        tk.Label(hero_left, text=APP_TITLE, bg=self.PANEL, fg=self.TEXT, font=("Georgia", 24, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(
            hero_left,
            text="Desktop Alpha studio with the same Bluear_cod color language: deep navy, soft cyan, warm orange, and success green.",
            bg=self.PANEL,
            fg=self.MUTED,
            justify="left",
            wraplength=640,
            font=("Segoe UI", 11),
        ).pack(anchor="w")

        tag_row = tk.Frame(hero_left, bg=self.PANEL)
        tag_row.pack(anchor="w", pady=(14, 0))
        tk.Label(tag_row, text="Desktop Mode", bg=self.PANEL_SOFT, fg=self.ACCENT, padx=12, pady=6, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        tk.Label(tag_row, text="Same Alpha Colors", bg=self.PANEL_SOFT, fg=self.SKY, padx=12, pady=6, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        tk.Label(tag_row, text="Error Highlight Ready", bg=self.PANEL_SOFT, fg=self.SUCCESS, padx=12, pady=6, font=("Segoe UI", 9, "bold")).pack(side="left")

        metrics_top = tk.Frame(hero_right, bg=self.PANEL)
        metrics_top.pack(fill="x")
        metrics_bottom = tk.Frame(hero_right, bg=self.PANEL)
        metrics_bottom.pack(fill="x", pady=(10, 0))
        self._metric_card(metrics_top, "Samples", self.samples_metric_text, self.ACCENT).pack(side="left", padx=(0, 10))
        self._metric_card(metrics_top, "Packages", self.packages_metric_text, self.SKY).pack(side="left")
        self._metric_card(metrics_bottom, "History", self.history_metric_text, self.SUCCESS).pack(side="left", padx=(0, 10))
        self._metric_card(metrics_bottom, "Runtime", self.runtime_metric_text, self.ACCENT).pack(side="left")

        self.main_tabs = ttk.Notebook(self)
        self.main_tabs.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.workspace_tab = tk.Frame(self.main_tabs, bg=self.BG)
        self.guide_tab = tk.Frame(self.main_tabs, bg=self.BG)
        self.packages_tab = tk.Frame(self.main_tabs, bg=self.BG)
        self.history_tab = tk.Frame(self.main_tabs, bg=self.BG)
        self.main_tabs.add(self.workspace_tab, text="Workspace")
        self.main_tabs.add(self.guide_tab, text="Guide")
        self.main_tabs.add(self.packages_tab, text="Packages")
        self.main_tabs.add(self.history_tab, text="History")

        self._build_workspace_tab()
        self._build_guide_tab()
        self._build_packages_tab()
        self._build_history_tab()

        status = self._card(self)
        status.pack(fill="x", padx=18, pady=(0, 18))
        status.grid_columnconfigure(1, weight=1)
        tk.Label(status, text="Status", bg=self.PANEL, fg=self.ACCENT, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))
        self.status_value = tk.Label(status, textvariable=self.status_text, bg=self.PANEL_SOFT, fg=self.TEXT, font=("Segoe UI", 10, "bold"), padx=14, pady=6)
        self.status_value.grid(row=0, column=1, sticky="w", padx=(0, 18), pady=(14, 4))
        tk.Label(status, text="Info", bg=self.PANEL, fg=self.ACCENT, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", padx=18, pady=4)
        tk.Label(status, textvariable=self.info_text, bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10), justify="left", wraplength=900).grid(row=1, column=1, sticky="ew", padx=(0, 18), pady=4)
        tk.Label(status, text="File", bg=self.PANEL, fg=self.ACCENT, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", padx=18, pady=(4, 14))
        tk.Label(status, textvariable=self.file_text, bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10), justify="left", wraplength=900).grid(row=2, column=1, sticky="ew", padx=(0, 18), pady=(4, 14))

    def _build_workspace_tab(self) -> None:
        wrapper = tk.Frame(self.workspace_tab, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=4, pady=4)

        toolbar = self._card(wrapper)
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, text="Starter Program", bg=self.PANEL, fg=self.ACCENT, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(18, 10), pady=14)

        self.sample_combo = ttk.Combobox(toolbar, textvariable=self.sample_choice, state="readonly", width=30)
        self.sample_combo.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        self.sample_combo.bind("<<ComboboxSelected>>", self.on_workspace_sample_selected)

        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side="left", padx=(0, 8), pady=10)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side="left", padx=(0, 8), pady=10)
        ttk.Button(toolbar, text="Clear", command=self.clear_editor).pack(side="left", padx=(0, 8), pady=10)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all).pack(side="left", padx=(0, 8), pady=10)
        ttk.Button(toolbar, text="Run Alpha", style="Accent.TButton", command=self.run_alpha).pack(side="left", padx=(0, 18), pady=10)

        body = tk.PanedWindow(wrapper, orient="horizontal", sashwidth=10, bg=self.BG, bd=0, relief="flat")
        body.pack(fill="both", expand=True)

        editor_card = self._card(body)
        result_card = self._card(body)
        body.add(editor_card, stretch="always", minsize=560)
        body.add(result_card, stretch="always", minsize=400)

        tk.Label(editor_card, text="Alpha Editor", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        tk.Label(
            editor_card,
            text="Readable Alpha code with source-line error highlight and direct desktop execution.",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18, pady=(0, 10))
        self.editor = self._text_box(editor_card, read_only=False, wrap="none", font_size=11)
        self.editor.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.editor.tag_configure("error_line", background="#3b171d", foreground="#ffd1d1", underline=True)

        tk.Label(result_card, text="Result Center", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Label(
            result_card,
            text="See the output, translated Python, and issue report without leaving the workspace.",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18, pady=(4, 0))
        self.result_tabs = ttk.Notebook(result_card)
        self.result_tabs.pack(fill="both", expand=True, padx=18, pady=16)
        output_frame = tk.Frame(self.result_tabs, bg=self.BG)
        python_frame = tk.Frame(self.result_tabs, bg=self.BG)
        issues_frame = tk.Frame(self.result_tabs, bg=self.BG)
        self.result_tabs.add(output_frame, text="Output")
        self.result_tabs.add(python_frame, text="Generated Python")
        self.result_tabs.add(issues_frame, text="Issues")
        self.output_view = self._text_box(output_frame, read_only=True, wrap="word")
        self.output_view.pack(fill="both", expand=True)
        self.python_view = self._text_box(python_frame, read_only=True, wrap="none")
        self.python_view.pack(fill="both", expand=True)
        self.issues_view = self._text_box(issues_frame, read_only=True, wrap="word")
        self.issues_view.pack(fill="both", expand=True)
        self.set_readonly(self.output_view, "Output will appear here.")
        self.set_readonly(self.python_view, "Translated Python will appear here.")
        self.set_readonly(self.issues_view, "No run issues yet.")

    def _build_guide_tab(self) -> None:
        tabs = ttk.Notebook(self.guide_tab)
        tabs.pack(fill="both", expand=True, padx=4, pady=4)

        samples_page = self._card(tabs)
        rules_page = self._card(tabs)
        bridges_page = self._card(tabs)
        runtime_page = self._card(tabs)
        tabs.add(samples_page, text="Starter Programs")
        tabs.add(rules_page, text="Rules")
        tabs.add(bridges_page, text="Bridges")
        tabs.add(runtime_page, text="Runtime")

        samples_left = tk.Frame(samples_page, bg=self.PANEL)
        samples_left.pack(side="left", fill="y", padx=(18, 10), pady=16)
        samples_right = tk.Frame(samples_page, bg=self.PANEL)
        samples_right.pack(side="left", fill="both", expand=True, padx=(0, 18), pady=16)

        tk.Label(samples_left, text="Starter Programs", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.samples_list = tk.Listbox(samples_left)
        self._style_listbox(self.samples_list, width=28)
        self.samples_list.pack(fill="both", expand=True)
        self.samples_list.bind("<<ListboxSelect>>", self.on_guide_sample_selected)
        self.samples_list.bind("<Double-Button-1>", lambda _event: self.load_selected_guide_sample())
        ttk.Button(samples_left, text="Load Into Workspace", command=self.load_selected_guide_sample).pack(anchor="e", pady=(10, 0))

        tk.Label(samples_right, text="Sample Preview", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.sample_preview = self._text_box(samples_right, read_only=True, wrap="none")
        self.sample_preview.pack(fill="both", expand=True)

        tk.Label(rules_page, text="Language Rules", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.rules_list = tk.Listbox(rules_page)
        self._style_listbox(self.rules_list)
        self.rules_list.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.rules_list.bind("<<ListboxSelect>>", self.on_rule_selected)
        self.rule_detail = self._text_box(rules_page, read_only=True, wrap="word")
        self.rule_detail.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        tk.Label(bridges_page, text="Alpha Bridges", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.bridges_list = tk.Listbox(bridges_page)
        self._style_listbox(self.bridges_list)
        self.bridges_list.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.bridges_list.bind("<<ListboxSelect>>", self.on_bridge_selected)
        self.bridge_detail = self._text_box(bridges_page, read_only=True, wrap="word")
        self.bridge_detail.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        tk.Label(runtime_page, text="Runtime Requirements", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.runtime_view = self._text_box(runtime_page, read_only=True, wrap="word")
        self.runtime_view.pack(fill="both", expand=True, padx=18, pady=(0, 16))

    def _build_packages_tab(self) -> None:
        card = self._card(self.packages_tab)
        card.pack(fill="both", expand=True, padx=4, pady=4)
        tk.Label(card, text="Package Manager", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(card, text="Install or remove Alpha packages with the same desktop palette and clean detail view.", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 10))

        body = tk.PanedWindow(card, orient="horizontal", sashwidth=10, bg=self.PANEL, bd=0, relief="flat")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        left = tk.Frame(body, bg=self.PANEL)
        right = tk.Frame(body, bg=self.PANEL)
        body.add(left, stretch="always", minsize=280)
        body.add(right, stretch="always", minsize=420)

        self.packages_list = tk.Listbox(left)
        self._style_listbox(self.packages_list)
        self.packages_list.pack(fill="both", expand=True, pady=(0, 10))
        self.packages_list.bind("<<ListboxSelect>>", self.on_package_selected)
        actions = tk.Frame(left, bg=self.PANEL)
        actions.pack(fill="x")
        ttk.Button(actions, text="Refresh", command=self.refresh_packages).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Install", style="Accent.TButton", command=self.install_selected_package).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Remove", command=self.remove_selected_package).pack(side="left")

        tk.Label(right, text="Package Detail", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.package_detail = self._text_box(right, read_only=True, wrap="word")
        self.package_detail.pack(fill="both", expand=True)

    def _build_history_tab(self) -> None:
        card = self._card(self.history_tab)
        card.pack(fill="both", expand=True, padx=4, pady=4)
        header = tk.Frame(card, bg=self.PANEL)
        header.pack(fill="x", padx=18, pady=(16, 8))
        tk.Label(header, text="Recent Runs", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(header, text="Refresh", command=self.refresh_history).pack(side="right")
        tk.Label(card, text="Track execution history and load current-session source snapshots back into the editor.", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 10))

        body = tk.PanedWindow(card, orient="horizontal", sashwidth=10, bg=self.PANEL, bd=0, relief="flat")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        left = tk.Frame(body, bg=self.PANEL)
        right = tk.Frame(body, bg=self.PANEL)
        body.add(left, stretch="always", minsize=420)
        body.add(right, stretch="always", minsize=420)

        self.history_tree = ttk.Treeview(left, columns=("id", "status", "created", "duration"), show="headings")
        for column, title, width in (("id", "Run", 90), ("status", "Status", 120), ("created", "Created", 220), ("duration", "Duration ms", 130)):
            self.history_tree.heading(column, text=title)
            self.history_tree.column(column, width=width, anchor="w")
        self.history_tree.pack(fill="both", expand=True, pady=(0, 10))
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_selected)
        ttk.Button(left, text="Load Run Source", command=self.load_selected_run_source).pack(anchor="e")
        tk.Label(right, text="Run Detail", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.history_detail = self._text_box(right, read_only=True, wrap="word")
        self.history_detail.pack(fill="both", expand=True)

    def refresh_all(self) -> None:
        self.guide_payload = self.interpreter.get_guide_payload()
        self.populate_samples()
        self.populate_rules()
        self.populate_bridges()
        self.populate_runtime()
        self.refresh_packages()
        self.refresh_history()
        self.update_metrics()
        self.set_status("Ready", self.TEXT, "Guide, packages, and history refreshed from the Alpha runtime.")

    def update_metrics(self) -> None:
        sample_total = len(self.guide_payload.get("sample_programs", {}))
        installed_total = sum(1 for package in self.packages.values() if package.get("installed"))
        package_total = len(self.packages)
        history_total = len(self.history)
        runtime_text = self.guide_payload.get("tagline", "Desktop Alpha runtime")

        self.samples_metric_text.set(f"{sample_total} starter programs ready")
        self.packages_metric_text.set(f"{installed_total}/{package_total} packages installed" if package_total else "0 packages available")
        self.history_metric_text.set(f"{history_total} recent runs tracked")
        self.runtime_metric_text.set(runtime_text)

    def populate_samples(self) -> None:
        programs = self.guide_payload.get("sample_programs", {})
        self.sample_titles = {record["title"]: key for key, record in programs.items()}
        titles = list(self.sample_titles)
        self.sample_combo["values"] = titles
        self.samples_list.delete(0, tk.END)
        for title in titles:
            self.samples_list.insert(tk.END, title)
        if titles:
            default_key = self.guide_payload.get("default_sample")
            default_title = programs.get(default_key, {}).get("title", titles[0])
            if not self.sample_choice.get():
                self.sample_choice.set(default_title)
            self.samples_list.selection_clear(0, tk.END)
            self.samples_list.selection_set(titles.index(default_title))
            self.update_sample_preview(default_title)

    def populate_rules(self) -> None:
        self.rules = self.guide_payload.get("rules", [])
        self.rules_list.delete(0, tk.END)
        for rule in self.rules:
            self.rules_list.insert(tk.END, f"{rule['keyword']}  |  {rule['syntax']}")
        if self.rules:
            self.rules_list.selection_set(0)
            self.show_rule_detail(0)

    def populate_bridges(self) -> None:
        self.bridges = self.guide_payload.get("bridges", [])
        self.bridges_list.delete(0, tk.END)
        for bridge in self.bridges:
            self.bridges_list.insert(tk.END, f"{bridge['name']}  |  {bridge['notes']}")
        if self.bridges:
            self.bridges_list.selection_set(0)
            self.show_bridge_detail(0)

    def populate_runtime(self) -> None:
        requirements = self.guide_payload.get("requirements", [])
        modules = self.guide_payload.get("safe_modules", [])
        notes = self.guide_payload.get("extension_notes", [])
        text = ["Requirements", "------------"]
        text.extend(f"- {item}" for item in requirements)
        text.extend(["", "Safe Modules", "------------", ", ".join(modules) if modules else "(none)", "", "Extension Notes", "---------------"])
        text.extend(f"- {item}" for item in notes)
        self.set_readonly(self.runtime_view, "\n".join(text))

    def refresh_packages(self) -> None:
        package_list = self.interpreter.list_available_packages()
        self.packages = {record["name"]: record for record in package_list}
        self.packages_list.delete(0, tk.END)
        for package in package_list:
            state = "Installed" if package["installed"] else "Available"
            self.packages_list.insert(tk.END, f"{package['title']}  |  {state}")
        if package_list:
            self.packages_list.selection_set(0)
            self.show_package_detail(package_list[0]["name"])
        else:
            self.set_readonly(self.package_detail, "No packages are available.")
        self.update_metrics()

    def refresh_history(self) -> None:
        runs = self.interpreter.recent_runs(limit=18)
        self.history = {str(run["id"]): run for run in runs}
        self.history_tree.delete(*self.history_tree.get_children())
        for run in runs:
            self.history_tree.insert("", "end", iid=str(run["id"]), values=(f"#{run['id']}", run["status"], run["created_at"], f"{float(run['duration_ms']):.2f}"))
        if runs:
            self.history_tree.selection_set(str(runs[0]["id"]))
            self.show_history_detail(str(runs[0]["id"]))
        else:
            self.set_readonly(self.history_detail, "No Alpha runs have been recorded yet.")
        self.update_metrics()

    def load_default_sample(self) -> None:
        if self.editor.get("1.0", "end-1c").strip():
            return
        default_key = self.guide_payload.get("default_sample")
        if default_key:
            self.load_sample(default_key)

    def update_sample_preview(self, title: str) -> None:
        key = self.sample_titles.get(title)
        if not key:
            return
        self.set_readonly(self.sample_preview, self.guide_payload["sample_programs"][key]["source"].strip())

    def show_rule_detail(self, index: int) -> None:
        rule = self.rules[index]
        self.set_readonly(self.rule_detail, f"Keyword: {rule['keyword']}\nSyntax: {rule['syntax']}\n\n{rule['description']}")

    def show_bridge_detail(self, index: int) -> None:
        bridge = self.bridges[index]
        self.set_readonly(self.bridge_detail, f"Bridge: {bridge['name']}\nNotes: {bridge['notes']}\n\n{bridge['description']}")

    def show_package_detail(self, name: str) -> None:
        package = self.packages[name]
        detail = [
            f"Package: {package['title']}",
            f"Name: {package['name']}",
            f"State: {'Installed' if package['installed'] else 'Available'}",
            f"Tags: {', '.join(package['tags']) or '(none)'}",
            f"Exports: {', '.join(package['exports']) or '(none)'}",
            "",
            package["description"],
        ]
        self.set_readonly(self.package_detail, "\n".join(detail))

    def show_history_detail(self, run_id: str) -> None:
        run = self.history[run_id]
        snapshot = self.run_snapshots.get(run_id)
        detail = [f"Run: #{run['id']}", f"Status: {run['status']}", f"Created: {run['created_at']}", f"Duration: {float(run['duration_ms']):.2f} ms", f"Error: {run['error_text'] or 'None'}"]
        if snapshot:
            detail.extend(["", "Source Snapshot", "---------------", snapshot["source_code"] or "(empty)", "", "Output Snapshot", "---------------", snapshot["output_text"] or "(no output)"])
        self.set_readonly(self.history_detail, "\n".join(detail))

    def load_sample(self, sample_key: str) -> None:
        record = self.guide_payload["sample_programs"].get(sample_key)
        if not record:
            messagebox.showerror(APP_TITLE, f"Sample '{sample_key}' was not found.")
            return
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", f"{record['source'].strip()}\n")
        self.sample_choice.set(record["title"])
        self.current_file = None
        self.file_text.set(f"Workspace file: sample '{record['title']}'")
        self.clear_error_highlight()
        self.set_readonly(self.output_view, "Output will appear here.")
        self.set_readonly(self.python_view, "Translated Python will appear here.")
        self.set_readonly(self.issues_view, "No run issues yet.")
        self.main_tabs.select(self.workspace_tab)
        self.set_status("Sample loaded", self.TEXT, f"Loaded starter program '{record['title']}'.")

    def on_workspace_sample_selected(self, _event: Any = None) -> None:
        key = self.sample_titles.get(self.sample_choice.get())
        if key:
            self.load_sample(key)

    def on_guide_sample_selected(self, _event: Any = None) -> None:
        selection = self.samples_list.curselection()
        if selection:
            self.update_sample_preview(self.samples_list.get(selection[0]))

    def load_selected_guide_sample(self) -> None:
        selection = self.samples_list.curselection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Select a starter program first.")
            return
        key = self.sample_titles.get(self.samples_list.get(selection[0]))
        if key:
            self.load_sample(key)

    def on_rule_selected(self, _event: Any = None) -> None:
        selection = self.rules_list.curselection()
        if selection:
            self.show_rule_detail(selection[0])

    def on_bridge_selected(self, _event: Any = None) -> None:
        selection = self.bridges_list.curselection()
        if selection:
            self.show_bridge_detail(selection[0])

    def on_package_selected(self, _event: Any = None) -> None:
        selection = self.packages_list.curselection()
        if selection:
            name = list(self.packages)[selection[0]]
            self.show_package_detail(name)

    def on_history_selected(self, _event: Any = None) -> None:
        selection = self.history_tree.selection()
        if selection:
            self.show_history_detail(selection[0])

    def clear_error_highlight(self) -> None:
        self.editor.tag_remove("error_line", "1.0", tk.END)

    def highlight_error_line(self, line_number: int | None) -> None:
        self.clear_error_highlight()
        if not line_number:
            return
        start = f"{line_number}.0"
        self.editor.tag_add("error_line", start, f"{line_number}.0 lineend+1c")
        self.editor.see(start)

    def run_alpha(self) -> None:
        source = self.editor.get("1.0", "end-1c")
        if not source.strip():
            messagebox.showinfo(APP_TITLE, "Write some Alpha code before running.")
            return

        self.main_tabs.select(self.workspace_tab)
        self.set_status("Running", self.ACCENT, "Running Alpha code in the desktop software...")
        self.update_idletasks()

        result = self.interpreter.run(source)
        if result.run_id is not None:
            self.run_snapshots[str(result.run_id)] = result.to_dict()

        self.set_readonly(self.output_view, result.output_text or "(Program completed with no output.)")
        self.set_readonly(self.python_view, result.translated_code or "(No translated Python was produced.)")

        if result.error_text:
            self.set_status("Error", self.DANGER, result.error_text)
            self.set_readonly(self.issues_view, result.error_text)
            self.highlight_error_line(result.error_line)
            self.result_tabs.select(2)
        else:
            self.set_status("Success", self.SUCCESS, f"Run #{result.run_id} finished in {float(result.duration_ms):.2f} ms.")
            self.set_readonly(self.issues_view, "No runtime or translation issues.")
            self.clear_error_highlight()
            self.result_tabs.select(0)

        self.refresh_history()

    def clear_editor(self) -> None:
        self.editor.delete("1.0", tk.END)
        self.clear_error_highlight()
        self.current_file = None
        self.file_text.set("Workspace file: unsaved draft")
        self.set_readonly(self.output_view, "Output will appear here.")
        self.set_readonly(self.python_view, "Translated Python will appear here.")
        self.set_readonly(self.issues_view, "No run issues yet.")
        self.set_status("Ready", self.TEXT, "Workspace cleared.")

    def open_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Open Alpha file",
            initialdir=str(EXAMPLES_DIR if EXAMPLES_DIR.exists() else PROJECT_ROOT),
            filetypes=[("Alpha files", "*.alpha"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return
        path = Path(file_path)
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", path.read_text(encoding="utf-8"))
        self.current_file = path
        self.clear_error_highlight()
        self.file_text.set(f"Workspace file: {path}")
        self.set_status("File opened", self.TEXT, f"Opened file '{path.name}'.")

    def save_file(self) -> None:
        path = self.current_file
        if path is None:
            file_path = filedialog.asksaveasfilename(
                title="Save Alpha file",
                initialdir=str(EXAMPLES_DIR if EXAMPLES_DIR.exists() else PROJECT_ROOT),
                defaultextension=".alpha",
                filetypes=[("Alpha files", "*.alpha"), ("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not file_path:
                return
            path = Path(file_path)
        path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self.current_file = path
        self.file_text.set(f"Workspace file: {path}")
        self.set_status("Saved", self.SUCCESS, f"Saved file '{path.name}'.")

    def install_selected_package(self) -> None:
        selection = self.packages_list.curselection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Select a package to install.")
            return
        name = list(self.packages)[selection[0]]
        try:
            record = self.interpreter.install_package(name)
        except Exception as error:  # noqa: BLE001 - shown in desktop UI
            messagebox.showerror(APP_TITLE, str(error))
            return
        self.refresh_packages()
        self.set_status("Package installed", self.SUCCESS, f"Installed package '{record['title']}'.")

    def remove_selected_package(self) -> None:
        selection = self.packages_list.curselection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Select a package to remove.")
            return
        name = list(self.packages)[selection[0]]
        if not self.interpreter.remove_package(name):
            messagebox.showinfo(APP_TITLE, f"Package '{name}' was not installed.")
            return
        self.refresh_packages()
        self.set_status("Package removed", self.ACCENT, f"Removed package '{name}'.")

    def load_selected_run_source(self) -> None:
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Select a recent run first.")
            return
        snapshot = self.run_snapshots.get(selection[0])
        if not snapshot or not snapshot.get("source_code"):
            messagebox.showinfo(APP_TITLE, "This run has no source snapshot in the current desktop session.")
            return
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", snapshot["source_code"])
        self.main_tabs.select(self.workspace_tab)
        self.clear_error_highlight()
        self.set_status("Run source loaded", self.TEXT, f"Loaded source from run #{selection[0]}.")

    def run_alpha_event(self, _event: Any) -> str:
        self.run_alpha()
        return "break"

    def save_file_event(self, _event: Any) -> str:
        self.save_file()
        return "break"

    def open_file_event(self, _event: Any) -> str:
        self.open_file()
        return "break"


def main() -> None:
    authorize_desktop_startup()
    app = AlphaDesktopSoftware()
    app.mainloop()


if __name__ == "__main__":
    main()
