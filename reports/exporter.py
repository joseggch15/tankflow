"""Export de resultados a XLSX y/o CSV."""
from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def export_results(
    sheets: dict[str, pd.DataFrame],
    results_dir: str,
    base_name: str = "tankflow_output",
    export_xlsx: bool = True,
    export_csv: bool = True,
) -> None:
    out = Path(results_dir)
    out.mkdir(parents=True, exist_ok=True)

    if export_csv:
        for sheet_name, df in sheets.items():
            csv_path = out / f"{base_name}_{sheet_name}.csv"
            df.to_csv(csv_path, index=False)
            logger.info("CSV exported: %s", csv_path)

    if export_xlsx:
        xlsx_path = out / f"{base_name}.xlsx"
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                # Excel permite máx 31 chars por nombre de hoja
                df.to_excel(writer, sheet_name=str(sheet_name)[:31], index=False)
        logger.info("XLSX exported: %s", xlsx_path)
