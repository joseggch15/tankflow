from __future__ import annotations

import traceback
from typing import Optional

import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from tankflow.pipeline import run_pipeline


class PipelineWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    finished_success = pyqtSignal(dict)
    finished_error = pyqtSignal(str)

    def __init__(
        self,
        tank_csv: str,
        transactions_csv: Optional[str],
        config_path: str,
        date_start: Optional[str],
        date_end: Optional[str],
        output_dir: Optional[str],
        base_name: str,
    ):
        super().__init__()
        self.tank_csv = tank_csv
        self.transactions_csv = transactions_csv
        self.config_path = config_path
        self.date_start = date_start
        self.date_end = date_end
        self.output_dir = output_dir
        self.base_name = base_name

    def run(self):
        try:
            def cb(pct: int, msg: str):
                self.progress_updated.emit(int(pct), str(msg))

            date_range = None
            if self.date_start and self.date_end:
                date_range = (self.date_start, self.date_end)

            results = run_pipeline(
                tank_csv=self.tank_csv,
                transactions_csv=self.transactions_csv,
                config_path=self.config_path,
                date_range=date_range,
                base_name=self.base_name,
                results_dir_override=self.output_dir,
                progress_cb=cb,
            )
            self.finished_success.emit(results)
        except Exception as e:
            tb = traceback.format_exc()
            self.finished_error.emit(f"{e}\n\n{tb}")
