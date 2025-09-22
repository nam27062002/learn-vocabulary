from __future__ import annotations

import os
import sys
from pathlib import Path
import json
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

# Ensure project root on sys.path so Django scripts can import settings
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEV_TOOLS_DIR = PROJECT_ROOT / 'dev_tools'
SCRIPT_SQLITE_TO_ENV = DEV_TOOLS_DIR / 'migrate_sqlite_to_env_db.py'
SCRIPT_ENV_TO_SQLITE = DEV_TOOLS_DIR / 'migrate_env_db_to_sqlite.py'
SCRIPT_ENV_TO_NEW = DEV_TOOLS_DIR / 'migrate_env_db_to_new_server.py'
CONFIG_PATH = (PROJECT_ROOT / 'tools' / 'migrate_database' / 'db_migrator_config.json')

# Default DB settings (as provided in scripts) used on first run when no config exists
DEFAULT_SOURCE_DB = {
    'DATABASE_ENGINE': 'django.db.backends.postgresql',
    'DATABASE_NAME': 'learn_english_db_rjeh',
    'DATABASE_USER': 'learn_english_db_rjeh_user',
    'DATABASE_PASSWORD': 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8',
    'DATABASE_HOST': 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
    'DATABASE_PORT': '5432',
    'DATABASE_SSLMODE': '',
}

DEFAULT_TARGET_DB = {
    'NAME': 'learn_english_db_wuep',
    'USER': 'learn_english_db_wuep_user',
    'PASSWORD': 'RSZefSFspMPlsqz5MnxJeeUkKueWjSLH',
    'HOST': 'dpg-d32033juibrs739dn540-a.oregon-postgres.render.com',
    'PORT': '5432',
}


class ProcessWorker(QtCore.QObject):
    output = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(int)
    started = QtCore.pyqtSignal()

    def __init__(self, program: str, arguments: list[str], env: Optional[dict[str, str]] = None, cwd: Optional[str] = None):
        super().__init__()
        self.program = program
        self.arguments = arguments
        self.env = env or {}
        self.cwd = cwd or str(PROJECT_ROOT)
        self.proc: Optional[QtCore.QProcess] = None

    @QtCore.pyqtSlot()
    def run(self):
        self.proc = QtCore.QProcess()
        # Use system environment and update with provided env
        process_env = QtCore.QProcessEnvironment.systemEnvironment()
        for k, v in self.env.items():
            process_env.insert(k, v)
        self.proc.setProcessEnvironment(process_env)
        self.proc.setWorkingDirectory(self.cwd)
        self.proc.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)

        self.proc.readyReadStandardOutput.connect(self._handle_output)
        self.proc.finished.connect(self._handle_finished)

        self.started.emit()
        self.proc.start(program=self.program, arguments=self.arguments)

    def _handle_output(self):
        if not self.proc:
            return
        data = self.proc.readAllStandardOutput()
        try:
            text = bytes(data).decode('utf-8', errors='replace')
        except Exception:
            text = str(data)
        self.output.emit(text)

    def _handle_finished(self, exit_code: int, _status):
        self.finished.emit(exit_code)

    def terminate(self):
        if self.proc and self.proc.state() != QtCore.QProcess.ProcessState.NotRunning:
            self.proc.terminate()


class MigratorWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Database Migrator')
        self.resize(900, 700)

        self.worker_thread: Optional[QtCore.QThread] = None
        self.worker: Optional[ProcessWorker] = None

        self._build_ui()
        self._wire_events()

    def _build_ui(self):
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Migration type
        grp_type = QtWidgets.QGroupBox('Migration type')
        type_layout = QtWidgets.QHBoxLayout(grp_type)
        self.rad_sqlite_to_env = QtWidgets.QRadioButton('Local SQLite -> Env DB (server)')
        self.rad_env_to_sqlite = QtWidgets.QRadioButton('Env DB (server) -> Local SQLite')
        self.rad_env_to_new = QtWidgets.QRadioButton('Env DB (server) -> NEW server DB')
        self.rad_env_to_sqlite.setChecked(True)
        type_layout.addWidget(self.rad_env_to_sqlite)
        type_layout.addWidget(self.rad_sqlite_to_env)
        type_layout.addWidget(self.rad_env_to_new)
        layout.addWidget(grp_type)

        # Common options
        grp_common = QtWidgets.QGroupBox('Common options')
        form_common = QtWidgets.QFormLayout(grp_common)
        self.chk_yes = QtWidgets.QCheckBox("I'm sure. Proceed (destructive)")
        self.chk_keep_dump = QtWidgets.QCheckBox('Keep dump file')
        self.edit_dump_path = QtWidgets.QLineEdit()
        btn_browse_dump = QtWidgets.QPushButton('Browse...')
        h_dump = QtWidgets.QHBoxLayout()
        h_dump.addWidget(self.edit_dump_path)
        h_dump.addWidget(btn_browse_dump)
        form_common.addRow('Dump path (optional):', h_dump)
        form_common.addRow('', self.chk_keep_dump)
        form_common.addRow('', self.chk_yes)
        layout.addWidget(grp_common)

        # Options for Env -> SQLite
        grp_env_to_sqlite = QtWidgets.QGroupBox('Env -> SQLite options')
        form1 = QtWidgets.QFormLayout(grp_env_to_sqlite)
        self.chk_no_wipe = QtWidgets.QCheckBox('Do NOT delete db.sqlite3 (flush instead)')
        form1.addRow('', self.chk_no_wipe)
        layout.addWidget(grp_env_to_sqlite)

        # Options for Env -> New server
        grp_env_to_new = QtWidgets.QGroupBox('Env -> NEW server options')
        form2 = QtWidgets.QFormLayout(grp_env_to_new)
        self.chk_rebuild_schema = QtWidgets.QCheckBox('Rebuild schema on target (DROP/CREATE public)')
        self.edit_target_name = QtWidgets.QLineEdit()
        self.edit_target_user = QtWidgets.QLineEdit()
        self.edit_target_password = QtWidgets.QLineEdit()
        self.edit_target_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.edit_target_host = QtWidgets.QLineEdit()
        self.edit_target_port = QtWidgets.QLineEdit()
        form2.addRow('', self.chk_rebuild_schema)
        form2.addRow('Target NAME:', self.edit_target_name)
        form2.addRow('Target USER:', self.edit_target_user)
        form2.addRow('Target PASSWORD:', self.edit_target_password)
        form2.addRow('Target HOST:', self.edit_target_host)
        form2.addRow('Target PORT:', self.edit_target_port)
        layout.addWidget(grp_env_to_new)

        # Advanced source env override
        grp_env = QtWidgets.QGroupBox('Source Env DB overrides (optional)')
        form3 = QtWidgets.QFormLayout(grp_env)
        self.edit_engine = QtWidgets.QLineEdit()
        self.edit_name = QtWidgets.QLineEdit()
        self.edit_user = QtWidgets.QLineEdit()
        self.edit_password = QtWidgets.QLineEdit()
        self.edit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.edit_host = QtWidgets.QLineEdit()
        self.edit_port = QtWidgets.QLineEdit()
        self.edit_sslmode = QtWidgets.QLineEdit()
        form3.addRow('DATABASE_ENGINE:', self.edit_engine)
        form3.addRow('DATABASE_NAME:', self.edit_name)
        form3.addRow('DATABASE_USER:', self.edit_user)
        form3.addRow('DATABASE_PASSWORD:', self.edit_password)
        form3.addRow('DATABASE_HOST:', self.edit_host)
        form3.addRow('DATABASE_PORT:', self.edit_port)
        form3.addRow('DATABASE_SSLMODE:', self.edit_sslmode)
        layout.addWidget(grp_env)

        # Run controls
        h_controls = QtWidgets.QHBoxLayout()
        self.btn_run = QtWidgets.QPushButton('Run')
        self.btn_stop = QtWidgets.QPushButton('Stop')
        self.btn_stop.setEnabled(False)
        self.btn_save = QtWidgets.QPushButton('Save Config')
        self.btn_load = QtWidgets.QPushButton('Load Config')
        h_controls.addWidget(self.btn_run)
        h_controls.addWidget(self.btn_stop)
        h_controls.addWidget(self.btn_save)
        h_controls.addWidget(self.btn_load)
        h_controls.addStretch(1)
        layout.addLayout(h_controls)

        # Log output
        self.text_log = QtWidgets.QPlainTextEdit()
        self.text_log.setReadOnly(True)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self.text_log.setFont(font)
        layout.addWidget(self.text_log, 1)

        self.btn_browse_dump = btn_browse_dump
        self.grp_env_to_sqlite = grp_env_to_sqlite
        self.grp_env_to_new = grp_env_to_new

        self._update_group_visibility()
        # Prefill defaults on first run if no saved config
        if not CONFIG_PATH.exists():
            self._prefill_defaults()

    def _wire_events(self):
        self.rad_sqlite_to_env.toggled.connect(self._update_group_visibility)
        self.rad_env_to_sqlite.toggled.connect(self._update_group_visibility)
        self.rad_env_to_new.toggled.connect(self._update_group_visibility)
        self.btn_browse_dump.clicked.connect(self._choose_dump_path)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)

        # Try auto-load last used config
        QtCore.QTimer.singleShot(0, self._auto_load_config)

    def _update_group_visibility(self):
        self.grp_env_to_sqlite.setVisible(self.rad_env_to_sqlite.isChecked())
        self.grp_env_to_new.setVisible(self.rad_env_to_new.isChecked())

    def _choose_dump_path(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Select dump file path', str(PROJECT_ROOT), 'JSON (*.json);;All files (*.*)')
        if path:
            self.edit_dump_path.setText(path)

    def _append_log(self, text: str):
        self.text_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.text_log.insertPlainText(text)
        self.text_log.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def _prefill_defaults(self):
        # Source env overrides
        self.edit_engine.setText(DEFAULT_SOURCE_DB['DATABASE_ENGINE'])
        self.edit_name.setText(DEFAULT_SOURCE_DB['DATABASE_NAME'])
        self.edit_user.setText(DEFAULT_SOURCE_DB['DATABASE_USER'])
        self.edit_password.setText(DEFAULT_SOURCE_DB['DATABASE_PASSWORD'])
        self.edit_host.setText(DEFAULT_SOURCE_DB['DATABASE_HOST'])
        self.edit_port.setText(DEFAULT_SOURCE_DB['DATABASE_PORT'])
        self.edit_sslmode.setText(DEFAULT_SOURCE_DB['DATABASE_SSLMODE'])
        # Target new server defaults
        self.edit_target_name.setText(DEFAULT_TARGET_DB['NAME'])
        self.edit_target_user.setText(DEFAULT_TARGET_DB['USER'])
        self.edit_target_password.setText(DEFAULT_TARGET_DB['PASSWORD'])
        self.edit_target_host.setText(DEFAULT_TARGET_DB['HOST'])
        self.edit_target_port.setText(DEFAULT_TARGET_DB['PORT'])

    def _build_command(self) -> tuple[str, list[str], dict[str, str]]:
        if not self.chk_yes.isChecked():
            raise RuntimeError("Please confirm by checking the 'I'm sure' box.")

        py_exe = sys.executable
        args: list[str] = []
        env = {}

        # Common flags
        args.extend(['--yes'])
        if self.chk_keep_dump.isChecked():
            args.append('--keep-dump')
        dump_path = self.edit_dump_path.text().strip()
        if dump_path:
            args.extend(['--dump-path', dump_path])

        # Env overrides
        def set_if(key: str, edit: QtWidgets.QLineEdit):
            val = edit.text().strip()
            if val:
                env[key] = val
        set_if('DATABASE_ENGINE', self.edit_engine)
        set_if('DATABASE_NAME', self.edit_name)
        set_if('DATABASE_USER', self.edit_user)
        set_if('DATABASE_PASSWORD', self.edit_password)
        set_if('DATABASE_HOST', self.edit_host)
        set_if('DATABASE_PORT', self.edit_port)
        set_if('DATABASE_SSLMODE', self.edit_sslmode)

        if self.rad_env_to_sqlite.isChecked():
            script = str(SCRIPT_ENV_TO_SQLITE)
            if self.chk_no_wipe.isChecked():
                args.append('--no-wipe')
        elif self.rad_sqlite_to_env.isChecked():
            script = str(SCRIPT_SQLITE_TO_ENV)
        else:
            script = str(SCRIPT_ENV_TO_NEW)
            if self.chk_rebuild_schema.isChecked():
                args.append('--rebuild-schema')
            # Target overrides for new server
            def add_arg(flag: str, edit: QtWidgets.QLineEdit):
                val = edit.text().strip()
                if val:
                    args.extend([flag, val])
            add_arg('--target-name', self.edit_target_name)
            add_arg('--target-user', self.edit_target_user)
            add_arg('--target-password', self.edit_target_password)
            add_arg('--target-host', self.edit_target_host)
            add_arg('--target-port', self.edit_target_port)

        return py_exe, [script, *args], env

    def _on_run(self):
        try:
            program, arguments, env = self._build_command()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Validation', str(e))
            return

        self.text_log.clear()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker_thread = QtCore.QThread(self)
        self.worker = ProcessWorker(program, arguments, env=env, cwd=str(PROJECT_ROOT))
        self.worker.moveToThread(self.worker_thread)
        self.worker.output.connect(self._append_log)
        self.worker.finished.connect(self._on_finished)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def _on_stop(self):
        if self.worker:
            self.worker.terminate()
            self._append_log('\nTerminating...\n')

    def _on_finished(self, exit_code: int):
        self._append_log(f"\nProcess finished with exit code {exit_code}\n")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
            self.worker_thread = None
            self.worker = None

    # --- Config persistence ---
    def _collect_config(self) -> dict:
        if self.rad_env_to_sqlite.isChecked():
            migration_type = 'env_to_sqlite'
        elif self.rad_sqlite_to_env.isChecked():
            migration_type = 'sqlite_to_env'
        else:
            migration_type = 'env_to_new'

        cfg = {
            'migration_type': migration_type,
            'common': {
                'confirmed': self.chk_yes.isChecked(),
                'keep_dump': self.chk_keep_dump.isChecked(),
                'dump_path': self.edit_dump_path.text().strip(),
            },
            'env_overrides': {
                'DATABASE_ENGINE': self.edit_engine.text().strip(),
                'DATABASE_NAME': self.edit_name.text().strip(),
                'DATABASE_USER': self.edit_user.text().strip(),
                'DATABASE_PASSWORD': self.edit_password.text().strip(),
                'DATABASE_HOST': self.edit_host.text().strip(),
                'DATABASE_PORT': self.edit_port.text().strip(),
                'DATABASE_SSLMODE': self.edit_sslmode.text().strip(),
            },
            'env_to_sqlite': {
                'no_wipe': self.chk_no_wipe.isChecked(),
            },
            'env_to_new': {
                'rebuild_schema': self.chk_rebuild_schema.isChecked(),
                'target_name': self.edit_target_name.text().strip(),
                'target_user': self.edit_target_user.text().strip(),
                'target_password': self.edit_target_password.text().strip(),
                'target_host': self.edit_target_host.text().strip(),
                'target_port': self.edit_target_port.text().strip(),
            },
        }
        return cfg

    def _apply_config(self, cfg: dict):
        mt = cfg.get('migration_type', 'env_to_sqlite')
        self.rad_env_to_sqlite.setChecked(mt == 'env_to_sqlite')
        self.rad_sqlite_to_env.setChecked(mt == 'sqlite_to_env')
        self.rad_env_to_new.setChecked(mt == 'env_to_new')
        self._update_group_visibility()

        common = cfg.get('common', {})
        self.chk_yes.setChecked(common.get('confirmed', False))
        self.chk_keep_dump.setChecked(common.get('keep_dump', False))
        self.edit_dump_path.setText(common.get('dump_path', ''))

        env_ov = cfg.get('env_overrides', {})
        self.edit_engine.setText(env_ov.get('DATABASE_ENGINE', ''))
        self.edit_name.setText(env_ov.get('DATABASE_NAME', ''))
        self.edit_user.setText(env_ov.get('DATABASE_USER', ''))
        self.edit_password.setText(env_ov.get('DATABASE_PASSWORD', ''))
        self.edit_host.setText(env_ov.get('DATABASE_HOST', ''))
        self.edit_port.setText(env_ov.get('DATABASE_PORT', ''))
        self.edit_sslmode.setText(env_ov.get('DATABASE_SSLMODE', ''))

        e2s = cfg.get('env_to_sqlite', {})
        self.chk_no_wipe.setChecked(e2s.get('no_wipe', False))

        e2n = cfg.get('env_to_new', {})
        self.chk_rebuild_schema.setChecked(e2n.get('rebuild_schema', False))
        self.edit_target_name.setText(e2n.get('target_name', ''))
        self.edit_target_user.setText(e2n.get('target_user', ''))
        self.edit_target_password.setText(e2n.get('target_password', ''))
        self.edit_target_host.setText(e2n.get('target_host', ''))
        self.edit_target_port.setText(e2n.get('target_port', ''))

    def _on_save(self):
        cfg = self._collect_config()
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            QtWidgets.QMessageBox.information(self, 'Saved', f'Saved to\n{CONFIG_PATH}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Save failed', str(e))

    def _on_load(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self._apply_config(cfg)
            QtWidgets.QMessageBox.information(self, 'Loaded', f'Loaded from\n{CONFIG_PATH}')
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, 'Not found', f'No config found at\n{CONFIG_PATH}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Load failed', str(e))

    def _auto_load_config(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self._apply_config(cfg)
                self._append_log(f"Loaded config from {CONFIG_PATH}\n")
            except Exception as e:
                self._append_log(f"Failed to load config: {e}\n")

    def closeEvent(self, event: QtGui.QCloseEvent):
        # Auto-save last used config on close
        try:
            cfg = self._collect_config()
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MigratorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
