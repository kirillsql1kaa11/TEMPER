from __future__ import annotations
import sys
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QSpinBox, QPlainTextEdit, QMessageBox
)

from .paths import list_targets
from .cleaner import CleanOptions, clean_path, CleanStats

APP_TITLE = "TempCleaner"
BG = "#0B0620"
PANEL = "#130B2E"
TEXT = "#EDE9FE"
MUTED = "#B8A8FF"
BORDER = "rgba(167,139,250,0.25)"

def qss() -> str:
    return f"""
    QWidget {{
        background: {BG};
        color: {TEXT};
        font-family: Segoe UI;
        font-size: 12px;
    }}
    QLabel#title {{
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#subtitle {{
        color: {MUTED};
    }}
    QComboBox, QSpinBox {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 10px;
        min-width: 260px;
    }}
    QPlainTextEdit {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 10px;
    }}
    QPushButton {{
        background: rgba(167,139,250,0.16);
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 800;
        min-width: 140px;
    }}
    QPushButton:hover {{
        background: rgba(167,139,250,0.24);
    }}
    QPushButton:pressed {{
        background: rgba(167,139,250,0.30);
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border-radius: 6px;
        border: 1px solid {BORDER};
        background: {PANEL};
    }}
    QCheckBox::indicator:checked {{
        background: rgba(167,139,250,0.35);
        border: 1px solid rgba(167,139,250,0.55);
    }}
    """

class Worker(QThread):
    log = Signal(str)
    done = Signal(object)

    def __init__(self, path, opts: CleanOptions):
        super().__init__()
        self.path = path
        self.opts = opts

    def run(self):
        stats = clean_path(self.path, self.opts, log_cb=lambda s: self.log.emit(s))
        self.done.emit(stats)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(860, 540)
        self.setStyleSheet(qss())

        self.targets = list_targets()
        self.worker: Worker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("TempCleaner")
        title.setObjectName("title")
        subtitle = QLabel("Очистка TEMP. По умолчанию: dry-run + только старше 1 дня.")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        row = QHBoxLayout()
        self.cmb = QComboBox()
        for t in self.targets:
            self.cmb.addItem(f"{t.title} — {t.path}", t.key)
        row.addWidget(QLabel("Target:"))
        row.addWidget(self.cmb, 1)

        self.days = QSpinBox()
        self.days.setMinimum(0)
        self.days.setMaximum(3650)
        self.days.setValue(1)
        row.addWidget(QLabel("Older than (days):"))
        row.addWidget(self.days)
        root.addLayout(row)

        row2 = QHBoxLayout()
        self.chk_dry = QCheckBox("Dry-run (только показать)")
        self.chk_dry.setChecked(True)
        self.chk_dirs = QCheckBox("Удалять пустые папки")
        self.chk_dirs.setChecked(True)
        row2.addWidget(self.chk_dry)
        row2.addWidget(self.chk_dirs)
        row2.addStretch(1)

        self.btn_clear = QPushButton("Clear log")
        self.btn_clear.clicked.connect(lambda: self.log.setPlainText(""))
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.on_run)
        row2.addWidget(self.btn_clear)
        row2.addWidget(self.btn_run)
        root.addLayout(row2)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        root.addWidget(self.log, 1)
        self._append("Ready.")

    def _append(self, s: str):
        self.log.appendPlainText(s)

    def _set_busy(self, busy: bool):
        for w in (self.cmb, self.days, self.chk_dry, self.chk_dirs, self.btn_run):
            w.setEnabled(not busy)
        self.btn_run.setText("Running…" if busy else "Run")

    def on_run(self):
        key = self.cmb.currentData()
        tg = next((t for t in self.targets if t.key == key), None)
        if not tg:
            QMessageBox.warning(self, APP_TITLE, "Target not found.")
            return

        opts = CleanOptions(
            older_days=int(self.days.value()),
            dry_run=bool(self.chk_dry.isChecked()),
            include_dirs=bool(self.chk_dirs.isChecked()),
        )

        self._append("—" * 60)
        self._append(f"Target: {tg.title}")
        self._append(f"Path: {tg.path}")
        self._append(f"older_days={opts.older_days} dry_run={opts.dry_run} dirs={opts.include_dirs}")
        if tg.requires_admin:
            self._append("Note: этот путь часто требует прав администратора.")

        self._set_busy(True)
        self.worker = Worker(tg.path, opts)
        self.worker.log.connect(self._append)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, stats: CleanStats):
        freed_mb = stats.bytes_freed / (1024 * 1024)
        self._append("")
        self._append(f"Done. deleted_files={stats.deleted_files} deleted_dirs={stats.deleted_dirs} "
                     f"skipped={stats.skipped} errors={stats.errors} freed≈{freed_mb:.2f} MB")
        self._set_busy(False)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
