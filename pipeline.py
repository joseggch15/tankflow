"""TankFlow Pipeline – entrypoint principal (orquestador + CLI)."""
from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd
import typer

from tankflow.config.loader import load_config
from tankflow.config.models import PipelineConfig
from tankflow.io.readers import read_tank_volumes, read_dispenses_or_deliveries
from tankflow.transforms.time_features import add_time_features
from tankflow.transforms.deltas import compute_deltas, pivot_tanks_wide
from tankflow.analytics.gains import compute_gains
from tankflow.analytics.delivery_detection import detect_delivery_events
from tankflow.reports.pivots import (
    summary_tank_per_hour,
    dispenses_summary,
    delivery_events_table,
    delivery_transactions_table,
)
from tankflow.reports.exporter import export_results

logger = logging.getLogger(__name__)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_pipeline(
    tank_csv: str,
    transactions_csv: str | None = None,
    config_path: str = "tankflow/config/settings.yaml",
    date_range: tuple[str, str] | None = None,
    base_name: str = "tankflow_output",
) -> dict[str, pd.DataFrame]:
    """
    Ejecuta el pipeline completo.

    Parámetros:
      - tank_csv: CSV de historical tank volumes
      - transactions_csv: opcional (puede ser dispenses/outflow o deliveries)
      - date_range: (start, end) strings parseables por pandas (recomendado dd/mm/yyyy HH:MM)
    """
    cfg: PipelineConfig = load_config(config_path)
    _setup_logging(cfg.log_level)

    # 1) Ingesta tank volumes
    df = read_tank_volumes(tank_csv, cfg)

    # Filtro de rango
    if date_range:
        start = pd.to_datetime(date_range[0], format=cfg.date_format, errors="coerce")
        end = pd.to_datetime(date_range[1], format=cfg.date_format, errors="coerce")
        if pd.isna(start) or pd.isna(end):
            # fallback general
            start = pd.to_datetime(date_range[0], errors="raise")
            end = pd.to_datetime(date_range[1], errors="raise")
        df = df[(df["Time"] >= start) & (df["Time"] <= end)].copy()
        logger.info("Filtered tank volumes to %s → %s | rows=%s", start, end, f"{len(df):,}")

    # 2) Time features
    df = add_time_features(df)

    # 3) Deltas
    df = compute_deltas(df, cfg)

    # 4) Wide + gains
    df_wide = pivot_tanks_wide(df, cfg)
    df_wide = compute_gains(df_wide, cfg)

    # 5) Delivery events por tanque
    events = []
    for tank in [cfg.main_tank] + cfg.virtual_tanks:
        ev = detect_delivery_events(df, tank, cfg)
        logger.info("Tank %s: detected %d events", tank, len(ev))
        events.extend(ev)

    # 6) Reportes
    results: dict[str, pd.DataFrame] = {}
    results["dataset_per_hour"] = df
    results["global_analysis"] = df_wide
    results["summary_tank_per_hour"] = summary_tank_per_hour(df)
    results["delivery_events"] = delivery_events_table(events)

    # 7) Opcional: transacciones (dispenses o deliveries)
    if transactions_csv:
        kind, df_tx = read_dispenses_or_deliveries(transactions_csv, cfg)
        df_tx = add_time_features(df_tx)
        if kind == "dispenses":
            results["dispenses_summary"] = dispenses_summary(df_tx)
        else:
            # deliveries
            results["delivery_transactions"] = delivery_transactions_table(df_tx)

    # 8) Export
    export_results(
        results,
        results_dir=cfg.results_dir,
        base_name=base_name,
        export_xlsx=cfg.export_xlsx,
        export_csv=cfg.export_csv,
    )
    logger.info("Pipeline completed successfully.")
    return results


app = typer.Typer(add_completion=False)

@app.command()
def main(
    tank_csv: str = typer.Argument(..., help="Path to historical tank volumes CSV"),
    transactions_csv: str = typer.Option(None, "--transactions-csv", help="Path to dispenses/outflow or delivery transactions CSV"),
    config: str = typer.Option("tankflow/config/settings.yaml", help="Config YAML path"),
    date_start: str = typer.Option(None, help="Start datetime (dd/mm/yyyy HH:MM or ISO)"),
    date_end: str = typer.Option(None, help="End datetime (dd/mm/yyyy HH:MM or ISO)"),
    base_name: str = typer.Option("tankflow_output", help="Base name for exported files"),
):
    date_range = (date_start, date_end) if date_start and date_end else None
    run_pipeline(
        tank_csv=tank_csv,
        transactions_csv=transactions_csv,
        config_path=config,
        date_range=date_range,
        base_name=base_name,
    )


if __name__ == "__main__":
    app()
