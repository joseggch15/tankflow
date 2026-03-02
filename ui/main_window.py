from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QGroupBox,
    QTabWidget, QTableView, QMessageBox, QProgressBar, QTextEdit,
    QDateTimeEdit, QCheckBox
)

from tankflow.ui.models import PandasTableModel
from tankflow.ui.workers import PipelineWorker


def _group(title: str, inner_layout) -> QGroupBox:
    box = QGroupBox(title)
    box.setLayout(inner_layout)
    return box


class FilePicker(QWidget):
    def __init__(self, label: str, button_text: str = "Browse…", file_filter: str = "*.csv *.xlsx *.yaml"):
        super().__init__()
        self.file_filter = file_filter
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.lbl = QLabel(label)
        self.path = QLineEdit()
        self.path.setPlaceholderText("Select a file…")
        self.btn = QPushButton(button_text)
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.lbl)
        layout.addWidget(self.path, 1)
        layout.addWidget(self.btn)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select file", "", self.file_filter)
        if p:
            self.path.setText(p)

    def value(self) -> str:
        return self.path.text().strip()

    def set_value(self, v: str) -> None:
        self.path.setText(v or "")


class TankFlowMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TankFlow – Tank Analysis")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Header
        header = QHBoxLayout()
        title = QLabel("🛢️ TankFlow – Pipeline")
        f = title.font()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # ── Inputs panel
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self.tank_csv = FilePicker("Tank volumes CSV:", file_filter="CSV (*.csv)")
        self.tx_csv = FilePicker("Transactions CSV (optional):", file_filter="CSV (*.csv)")
        self.cfg_file = FilePicker("Config YAML:", file_filter="YAML (*.yaml *.yml)")
        self.cfg_file.set_value(str(Path(__file__).resolve().parents[1] / "config" / "settings.yaml"))

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("outputs/ (default from config)")
        self.output_browse = QPushButton("Browse…")
        self.output_browse.clicked.connect(self._browse_dir)

        self.base_name = QLineEdit("tankflow_output")

        self.start_dt = QDateTimeEdit()
        self.start_dt.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDateTime(QDateTime.currentDateTime().addDays(-7))

        self.end_dt = QDateTimeEdit()
        self.end_dt.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setDateTime(QDateTime.currentDateTime())

        self.use_range = QCheckBox("Filter by date range")
        self.use_range.setChecked(True)

        grid.addWidget(self.tank_csv, 0, 0, 1, 3)
        grid.addWidget(self.tx_csv, 1, 0, 1, 3)
        grid.addWidget(self.cfg_file, 2, 0, 1, 3)

        grid.addWidget(QLabel("Output folder:"), 3, 0)
        grid.addWidget(self.output_dir, 3, 1)
        grid.addWidget(self.output_browse, 3, 2)

        grid.addWidget(QLabel("Base name:"), 4, 0)
        grid.addWidget(self.base_name, 4, 1, 1, 2)

        grid.addWidget(self.use_range, 5, 0)
        grid.addWidget(QLabel("Start:"), 6, 0)
        grid.addWidget(self.start_dt, 6, 1, 1, 2)
        grid.addWidget(QLabel("End:"), 7, 0)
        grid.addWidget(self.end_dt, 7, 1, 1, 2)

        # Actions
        actions = QHBoxLayout()
        self.run_btn = QPushButton("▶ Run Pipeline")
        self.run_btn.setProperty("variant", "primary")
        self.run_btn.clicked.connect(self._run)

        self.open_outputs_btn = QPushButton("📂 Open outputs folder")
        self.open_outputs_btn.setProperty("variant", "secondary")
        self.open_outputs_btn.clicked.connect(self._open_outputs)
        self.open_outputs_btn.setEnabled(False)

        actions.addWidget(self.run_btn)
        actions.addWidget(self.open_outputs_btn)
        actions.addStretch()

        panel = QVBoxLayout()
        panel.addLayout(grid)
        panel.addLayout(actions)

        root.addWidget(_group("Inputs", panel), 0)

        # ── Progress + log
        prog = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress_label = QLabel("Ready")
        prog.addWidget(self.progress, 1)
        prog.addWidget(self.progress_label)
        root.addLayout(prog)

        self.log = QTextEdit()
            self.log.setReadOnly(True)
            log_layout = QVBoxLayout()
            log_layout.addWidget(self.log)
            root.addWidget(_group("Log", log_layout), 0)

        # ── Results tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._tables: dict[str, tuple[QTableView, PandasTableModel, QLabel]] = {}
        self._worker: Optional[PipelineWorker] = None

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select output directory")
        if d:
            self.output_dir.setText(d)

    def _open_outputs(self):
        out_dir = self.output_dir.text().strip() or "outputs"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        # cross-platform open
        try:
            if os.name == "nt":
                os.startfile(out_dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f"open '{out_dir}'")
            else:
                os.system(f"xdg-open '{out_dir}'")
        except Exception:
            QMessageBox.information(self, "Outputs", f"Outputs folder: {out_dir}")

    def _append_log(self, text: str) -> None:
        self.log.append(text)

    def _validate_inputs(self) -> tuple[bool, str]:
        if not self.tank_csv.value():
            return False, "Please select the tank volumes CSV."
        if not Path(self.tank_csv.value()).exists():
            return False, "Tank volumes CSV path does not exist."
        if self.tx_csv.value() and not Path(self.tx_csv.value()).exists():
            return False, "Transactions CSV path does not exist."
        if self.cfg_file.value() and not Path(self.cfg_file.value()).exists():
            return False, "Config YAML path does not exist."
        return True, ""

    def _run(self):
        ok, msg = self._validate_inputs()
        if not ok:
            QMessageBox.warning(self, "Missing data", msg)
            return

        self.progress.setValue(0)
        self.progress_label.setText("Starting…")
        self.log.clear()
        self.tabs.clear()
        self._tables.clear()
        self.open_outputs_btn.setEnabled(False)

        date_start = None
        date_end = None
        if self.use_range.isChecked():
            date_start = self.start_dt.dateTime().toString("dd/MM/yyyy HH:mm")
            date_end = self.end_dt.dateTime().toString("dd/MM/yyyy HH:mm")

        self._worker = PipelineWorker(
            tank_csv=self.tank_csv.value(),
            transactions_csv=self.tx_csv.value() or None,
            config_path=self.cfg_file.value(),
            date_start=date_start,
            date_end=date_end,
            output_dir=self.output_dir.text().strip() or None,
            base_name=self.base_name.text().strip() or "tankflow_output",
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.finished_success.connect(self._on_success)
        self._worker.finished_error.connect(self._on_error)

        self.run_btn.setEnabled(False)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(int(pct))
        self.progress_label.setText(msg)
        self._append_log(f"{pct:3d}% | {msg}")

    def _on_success(self, results: dict):
        self.run_btn.setEnabled(True)
        self.progress.setValue(100)
        self.progress_label.setText("Done")
        self._append_log("Pipeline finished successfully.")

        # Crear tabs
        for name, df in results.items():
            if not isinstance(df, pd.DataFrame):
                continue

            # Para no congelar UI con tablas gigantes: renderizamos preview
            preview = df if len(df) <= 5000 else df.head(5000).copy()

            view = QTableView()
            view.setAlternatingRowColors(True)
            view.setSortingEnabled(True)

            model = PandasTableModel(preview)
            view.setModel(model)
            view.resizeColumnsToContents()

            info = QLabel(f"Rows: {len(df):,} | Showing: {len(preview):,}")
            info.setStyleSheet("color: #4B5563; padding: 4px 0;")

            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(8, 8, 8, 8)
            lay.addWidget(info)
            lay.addWidget(view, 1)

            self.tabs.addTab(container, name.replace("_", " ")[:18])
            self._tables[name] = (view, model, info)

        self.open_outputs_btn.setEnabled(True)

    def _on_error(self, err: str):
        self.run_btn.setEnabled(True)
        self.progress_label.setText("Error")
        self._append_log(err)
        QMessageBox.critical(self, "Pipeline error", err)
