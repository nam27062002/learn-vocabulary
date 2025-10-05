import os
import sys
import threading
import queue
import subprocess
from pathlib import Path
from typing import Dict, List
import json

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


APP_TITLE = "Database Migration GUI"


class MigrationGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x720")

        # Paths
        self.script_dir = Path(__file__).resolve().parent
        # Project root assumed to be one level up from 'tools': <root>/tools/migrate_database/run_gui.py
        # script_dir = <root>/tools/migrate_database -> parents[0] = <root>/tools, parents[1] = <root>
        self.project_root = self.script_dir.parents[1] if len(self.script_dir.parents) >= 2 else self.script_dir.parent

    # UI State
        self.mode_var = tk.StringVar(value="env_to_sqlite")
        self.keep_dump_var = tk.BooleanVar(value=False)
        self.dump_path_var = tk.StringVar(value="")
        self.confirm_var = tk.BooleanVar(value=False)

        # Mode-specific
        self.no_wipe_var = tk.BooleanVar(value=False)  # env -> sqlite
        self.rebuild_schema_var = tk.BooleanVar(value=False)  # env -> new server

        # Target (new server) fields for env -> new server
        self.target_name_var = tk.StringVar()
        self.target_user_var = tk.StringVar()
        self.target_password_var = tk.StringVar()
        self.target_host_var = tk.StringVar()
        self.target_port_var = tk.StringVar()

        # Optional source env overrides (applies to modes using env DB as source/target)
        self.env_engine_var = tk.StringVar()
        self.env_name_var = tk.StringVar()
        self.env_user_var = tk.StringVar()
        self.env_password_var = tk.StringVar()
        self.env_host_var = tk.StringVar()
        self.env_port_var = tk.StringVar()
        self.env_sslmode_var = tk.StringVar()

        # Runtime process/thread
        self._proc = None  # type: ignore[assignment]
        self._reader_thread = None  # type: ignore[assignment]
        self._queue = queue.Queue()  # type: ignore[assignment]

        # Build UI
        self._build_ui()
        # Load persisted config if present
        try:
            cfg = self._load_config()
            self._apply_config_to_ui(cfg)
        except Exception as e:
            # Non-fatal; just log to UI later
            pass
        self._poll_log_queue()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Select Migration Mode", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        mode_frame = ttk.Frame(header)
        mode_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        for i in range(3):
            mode_frame.columnconfigure(i, weight=1)

        ttk.Radiobutton(mode_frame, text="Env ➜ SQLite (Local)", value="env_to_sqlite", variable=self.mode_var, command=self._on_mode_change).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="SQLite (Local) ➜ Env", value="sqlite_to_env", variable=self.mode_var, command=self._on_mode_change).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(mode_frame, text="Env ➜ New Server (Postgres)", value="env_to_new", variable=self.mode_var, command=self._on_mode_change).grid(row=0, column=2, sticky="w")

        # Options frame
        options = ttk.LabelFrame(self, text="Options")
        options.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for i in range(6):
            options.columnconfigure(i, weight=1)

        # Dump path controls
        ttk.Label(options, text="Dump path (optional)").grid(row=0, column=0, sticky="w", padx=(6, 4), pady=4)
        dump_entry = ttk.Entry(options, textvariable=self.dump_path_var)
        dump_entry.grid(row=0, column=1, columnspan=4, sticky="ew", pady=4)
        ttk.Button(options, text="Browse…", command=self._browse_dump).grid(row=0, column=5, sticky="e", padx=(4, 6), pady=4)

        ttk.Checkbutton(options, text="Keep dump file after run", variable=self.keep_dump_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=6)

        # Mode-specific area
        self.mode_specific = ttk.Frame(options)
        self.mode_specific.grid(row=2, column=0, columnspan=6, sticky="ew", padx=0, pady=(6, 0))
        self.mode_specific.columnconfigure(0, weight=1)
        self._build_mode_specific_content()

        # Env overrides
        env_box = ttk.LabelFrame(self, text="Environment DB Overrides (optional)")
        env_box.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        for i in range(12):
            env_box.columnconfigure(i, weight=1)

        def add_labeled(row: int, col: int, text: str, var: tk.StringVar):
            ttk.Label(env_box, text=text).grid(row=row, column=col, sticky="w", padx=(6, 4), pady=2)
            e = ttk.Entry(env_box, textvariable=var)
            e.grid(row=row, column=col + 1, sticky="ew", pady=2)

        add_labeled(0, 0, "DATABASE_ENGINE", self.env_engine_var)
        add_labeled(0, 2, "DATABASE_NAME", self.env_name_var)
        add_labeled(0, 4, "DATABASE_USER", self.env_user_var)
        add_labeled(1, 0, "DATABASE_PASSWORD", self.env_password_var)
        add_labeled(1, 2, "DATABASE_HOST", self.env_host_var)
        add_labeled(1, 4, "DATABASE_PORT", self.env_port_var)
        add_labeled(2, 0, "DATABASE_SSLMODE", self.env_sslmode_var)

        # Actions
        actions = ttk.Frame(self)
        actions.grid(row=3, column=0, sticky="ew", padx=10, pady=(6, 6))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=0)
        actions.columnconfigure(2, weight=0)
        actions.columnconfigure(3, weight=0)
        actions.columnconfigure(4, weight=0)

        self.confirm_chk = ttk.Checkbutton(actions, text="I understand this can CLEAR data on target", variable=self.confirm_var, command=self._update_run_button)
        self.confirm_chk.grid(row=0, column=0, sticky="w")
        self.run_btn = ttk.Button(actions, text="Run Migration", command=self._on_run, state="disabled")
        self.run_btn.grid(row=0, column=1, sticky="e", padx=(6, 0))
        self.stop_btn = ttk.Button(actions, text="Stop", command=self._on_stop, state="disabled")
        self.stop_btn.grid(row=0, column=2, sticky="e")
        self.load_btn = ttk.Button(actions, text="Load Config", command=self._on_load_config)
        self.load_btn.grid(row=0, column=3, sticky="e", padx=(6, 0))
        self.save_btn = ttk.Button(actions, text="Save Config", command=self._on_save_config)
        self.save_btn.grid(row=0, column=4, sticky="e")

        # Log
        log_frame = ttk.LabelFrame(self, text="Logs")
        log_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log = ScrolledText(log_frame, height=20, wrap=tk.WORD, state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        self.log.tag_config("INFO", foreground="#1e1e1e")
        self.log.tag_config("ERR", foreground="#b00020")
        self.log.tag_config("OK", foreground="#006400")

    # ------------------- Config persistence -------------------
    @property
    def _config_path(self) -> Path:
        return self.script_dir / "migration_config.json"

    def _default_config(self) -> Dict[str, object]:
        # Defaults mirror the embedded values in your scripts
        return {
            "last_mode": "env_to_sqlite",
            "options": {
                "keep_dump": False,
                "dump_path": "",
                "no_wipe": False,
                "rebuild_schema": False,
            },
            "env": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "learn_english_db_rjeh",
                "USER": "learn_english_db_rjeh_user",
                "PASSWORD": "rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8",
                "HOST": "dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com",
                "PORT": "5432",
                "SSLMODE": "",
            },
            "new_server_target": {
                "NAME": "learn_english_db_wuep",
                "USER": "learn_english_db_wuep_user",
                "PASSWORD": "RSZefSFspMPlsqz5MnxJeeUkKueWjSLH",
                "HOST": "dpg-d32033juibrs739dn540-a.oregon-postgres.render.com",
                "PORT": "5432",
            },
            "sqlite": {
                "PATH": str(self.project_root / "db.sqlite3"),
            },
        }

    def _load_config(self) -> Dict[str, object]:
        if not self._config_path.exists():
            return self._default_config()
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge defaults for missing keys
        default = self._default_config()
        def merge(d, s):
            for k, v in s.items():
                if k not in d:
                    d[k] = v
                elif isinstance(v, dict) and isinstance(d.get(k), dict):
                    merge(d[k], v)
        merge(data, default)
        return data

    def _apply_config_to_ui(self, cfg: Dict[str, object]) -> None:
        # Mode
        self.mode_var.set(str(cfg.get("last_mode", "env_to_sqlite")))
        self._build_mode_specific_content()
        # Options
        opts = cfg.get("options", {}) if isinstance(cfg.get("options"), dict) else {}
        self.keep_dump_var.set(bool(opts.get("keep_dump", False)))
        self.dump_path_var.set(str(opts.get("dump_path", "")))
        self.no_wipe_var.set(bool(opts.get("no_wipe", False)))
        self.rebuild_schema_var.set(bool(opts.get("rebuild_schema", False)))
        # Env overrides
        env = cfg.get("env", {}) if isinstance(cfg.get("env"), dict) else {}
        self.env_engine_var.set(str(env.get("ENGINE", "")))
        self.env_name_var.set(str(env.get("NAME", "")))
        self.env_user_var.set(str(env.get("USER", "")))
        self.env_password_var.set(str(env.get("PASSWORD", "")))
        self.env_host_var.set(str(env.get("HOST", "")))
        self.env_port_var.set(str(env.get("PORT", "")))
        self.env_sslmode_var.set(str(env.get("SSLMODE", "")))
        # New server target
        tgt = cfg.get("new_server_target", {}) if isinstance(cfg.get("new_server_target"), dict) else {}
        self.target_name_var.set(str(tgt.get("NAME", "")))
        self.target_user_var.set(str(tgt.get("USER", "")))
        self.target_password_var.set(str(tgt.get("PASSWORD", "")))
        self.target_host_var.set(str(tgt.get("HOST", "")))
        self.target_port_var.set(str(tgt.get("PORT", "")))

    def _read_ui_to_config(self) -> Dict[str, object]:
        cfg = self._default_config()
        cfg["last_mode"] = self.mode_var.get()
        cfg["options"] = {
            "keep_dump": self.keep_dump_var.get(),
            "dump_path": self.dump_path_var.get().strip(),
            "no_wipe": self.no_wipe_var.get(),
            "rebuild_schema": self.rebuild_schema_var.get(),
        }
        cfg["env"] = {
            "ENGINE": self.env_engine_var.get().strip(),
            "NAME": self.env_name_var.get().strip(),
            "USER": self.env_user_var.get().strip(),
            "PASSWORD": self.env_password_var.get().strip(),
            "HOST": self.env_host_var.get().strip(),
            "PORT": self.env_port_var.get().strip(),
            "SSLMODE": self.env_sslmode_var.get().strip(),
        }
        cfg["new_server_target"] = {
            "NAME": self.target_name_var.get().strip(),
            "USER": self.target_user_var.get().strip(),
            "PASSWORD": self.target_password_var.get().strip(),
            "HOST": self.target_host_var.get().strip(),
            "PORT": self.target_port_var.get().strip() or "5432",
        }
        cfg["sqlite"] = {
            "PATH": str(self.project_root / "db.sqlite3"),
        }
        return cfg

    def _on_save_config(self) -> None:
        try:
            cfg = self._read_ui_to_config()
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self._append_log(f"Saved config to {self._config_path}", tag="OK")
        except Exception as e:
            messagebox.showerror("Save Config", f"Failed to save config: {e}")

    def _on_load_config(self) -> None:
        try:
            cfg = self._load_config()
            self._apply_config_to_ui(cfg)
            self._append_log(f"Loaded config from {self._config_path}", tag="OK")
        except Exception as e:
            messagebox.showerror("Load Config", f"Failed to load config: {e}")

    def _build_mode_specific_content(self) -> None:
        # Clear previous
        for c in self.mode_specific.winfo_children():
            c.destroy()

        mode = self.mode_var.get()
        if mode == "env_to_sqlite":
            frm = ttk.Frame(self.mode_specific)
            frm.grid(row=0, column=0, sticky="ew")
            ttk.Checkbutton(frm, text="Do not delete db.sqlite3 (use flush)", variable=self.no_wipe_var).grid(row=0, column=0, sticky="w")
        elif mode == "sqlite_to_env":
            frm = ttk.Frame(self.mode_specific)
            frm.grid(row=0, column=0, sticky="ew")
            ttk.Label(frm, text="This will APPLY migrations on env and then CLEAR all data before loading from SQLite.").grid(row=0, column=0, sticky="w")
        elif mode == "env_to_new":
            frm = ttk.LabelFrame(self.mode_specific, text="Target (New Server) Credentials")
            frm.grid(row=0, column=0, sticky="ew")
            for i in range(6):
                frm.columnconfigure(i, weight=1)

            def add(row: int, col: int, label: str, var: tk.StringVar, show: str | None = None):
                ttk.Label(frm, text=label).grid(row=row, column=col, sticky="w", padx=(6, 4), pady=2)
                e = ttk.Entry(frm, textvariable=var, show=show)
                e.grid(row=row, column=col + 1, sticky="ew", pady=2)

            add(0, 0, "TARGET NAME", self.target_name_var)
            add(0, 2, "TARGET USER", self.target_user_var)
            add(0, 4, "TARGET PASSWORD", self.target_password_var, show="*")
            add(1, 0, "TARGET HOST", self.target_host_var)
            add(1, 2, "TARGET PORT", self.target_port_var)
            ttk.Checkbutton(frm, text="Rebuild schema (Postgres): DROP/CREATE public then migrate", variable=self.rebuild_schema_var).grid(row=2, column=0, columnspan=6, sticky="w", padx=(6, 0), pady=(6, 0))

    def _on_mode_change(self) -> None:
        self._build_mode_specific_content()

    def _browse_dump(self) -> None:
        path = filedialog.asksaveasfilename(title="Choose dump output path", defaultextension=".json", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            self.dump_path_var.set(path)

    def _append_log(self, text: str, tag: str = "INFO") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text, tag)
        if not text.endswith("\n"):
            self.log.insert("end", "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _update_run_button(self) -> None:
        if self.confirm_var.get() and self._proc is None:
            self.run_btn.configure(state="normal")
        else:
            self.run_btn.configure(state="disabled")

    def _on_run(self) -> None:
        if not self.confirm_var.get():
            messagebox.showwarning("Confirm", "Please acknowledge the destructive operation warning.")
            return

        try:
            cmd, env = self._build_command()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        self._start_process(cmd, env)

    def _on_stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._append_log("Process terminated by user.", tag="ERR")
            except Exception as e:
                self._append_log(f"Failed to terminate process: {e}", tag="ERR")

    def _build_command(self) -> tuple[List[str], Dict[str, str]]:
        mode = self.mode_var.get()
        py = sys.executable or "python"

        if mode == "env_to_sqlite":
            script = self.project_root / "dev_tools" / "migrate_env_db_to_sqlite.py"
            args = [str(script), "--yes"]
            if self.no_wipe_var.get():
                args.append("--no-wipe")
        elif mode == "sqlite_to_env":
            script = self.project_root / "dev_tools" / "migrate_sqlite_to_env_db.py"
            args = [str(script), "--yes"]
        elif mode == "env_to_new":
            script = self.project_root / "dev_tools" / "migrate_env_db_to_new_server.py"
            args = [str(script), "--yes"]
            # Target overrides
            if self.target_name_var.get().strip():
                args += ["--target-name", self.target_name_var.get().strip()]
            if self.target_user_var.get().strip():
                args += ["--target-user", self.target_user_var.get().strip()]
            if self.target_password_var.get().strip():
                args += ["--target-password", self.target_password_var.get().strip()]
            if self.target_host_var.get().strip():
                args += ["--target-host", self.target_host_var.get().strip()]
            if self.target_port_var.get().strip():
                args += ["--target-port", self.target_port_var.get().strip()]
            if self.rebuild_schema_var.get():
                args.append("--rebuild-schema")
        else:
            raise ValueError("Unknown mode selected")

        # Common options
        if self.keep_dump_var.get():
            args.append("--keep-dump")
        if self.dump_path_var.get().strip():
            args += ["--dump-path", self.dump_path_var.get().strip()]

        # Environment overrides
        env = os.environ.copy()
        if self.env_engine_var.get().strip():
            env["DATABASE_ENGINE"] = self.env_engine_var.get().strip()
        if self.env_name_var.get().strip():
            env["DATABASE_NAME"] = self.env_name_var.get().strip()
        if self.env_user_var.get().strip():
            env["DATABASE_USER"] = self.env_user_var.get().strip()
        if self.env_password_var.get().strip():
            env["DATABASE_PASSWORD"] = self.env_password_var.get().strip()
        if self.env_host_var.get().strip():
            env["DATABASE_HOST"] = self.env_host_var.get().strip()
        if self.env_port_var.get().strip():
            env["DATABASE_PORT"] = self.env_port_var.get().strip()
        if self.env_sslmode_var.get().strip():
            env["DATABASE_SSLMODE"] = self.env_sslmode_var.get().strip()

        # Build final command
        cmd = [py] + args
        return cmd, env

    def _start_process(self, cmd: List[str], env: Dict[str, str]) -> None:
        if self._proc is not None and self._proc.poll() is None:
            messagebox.showinfo("Already running", "A migration is already in progress.")
            return

        # UI state
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.confirm_chk.configure(state="disabled")
        self._append_log(f"Starting: {' '.join(cmd)}", tag="INFO")

        # Start subprocess
        try:
            self._proc = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as e:
            self._append_log(f"Failed to start process: {e}", tag="ERR")
            self._proc = None
            self._update_run_button()
            self.stop_btn.configure(state="disabled")
            self.confirm_chk.configure(state="normal")
            return

        # Reader thread
        def reader() -> None:
            assert self._proc is not None
            if self._proc.stdout is None:
                return
            try:
                for line in self._proc.stdout:
                    self._queue.put(line.rstrip("\n"))
            except Exception as e:  # pragma: no cover
                self._queue.put(f"[reader error] {e}")
            finally:
                pass

        self._reader_thread = threading.Thread(target=reader, daemon=True)
        self._reader_thread.start()

        # Watcher thread to detect completion
        def waiter() -> None:
            assert self._proc is not None
            self._proc.wait()
            code = self._proc.returncode
            self._queue.put(f"\nProcess finished with exit code {code}")
            self._queue.put("__PROC_DONE__")

        threading.Thread(target=waiter, daemon=True).start()

    def _poll_log_queue(self) -> None:
        try:
            while True:
                line = self._queue.get_nowait()
                if line == "__PROC_DONE__":
                    # Reset UI state
                    self._proc = None
                    self.stop_btn.configure(state="disabled")
                    self.confirm_chk.configure(state="normal")
                    self._update_run_button()
                    continue
                tag = "OK" if "completed successfully" in line.lower() else "INFO"
                if "error" in line.lower() or "traceback" in line.lower():
                    tag = "ERR"
                self._append_log(line, tag=tag)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_log_queue)


def main() -> None:
    app = MigrationGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

