"""Ingesta robusta de CSVs de tanques y archivos de transacciones (outflow/delivery)."""
from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

from tankflow.config.models import PipelineConfig

logger = logging.getLogger(__name__)


def _strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _parse_volume_series(s: pd.Series, thousands_sep: str) -> pd.Series:
    # Acepta numérico o str con separador de miles
    if s.dtype == object:
        return s.astype(str).str.replace(thousands_sep, "", regex=False).replace("nan", pd.NA).astype(float)
    return s.astype(float)


def read_tank_volumes(path: str | Path, cfg: PipelineConfig) -> pd.DataFrame:
    """
    Lee el CSV de volúmenes históricos de tanques.
    Espera columnas:
      Time, Tank, Volume Unit, Volume, Volume Type, Entered By
    Maneja: separadores de miles, fechas dd/mm/yyyy HH:MM, nulos.
    """
    path = Path(path)
    logger.info("Reading tank volumes from %s", path)
    df = pd.read_csv(path, dtype={"Volume": str, "Entered By": str}, keep_default_na=False)
    df = _strip_cols(df)

    required = {"Time", "Tank", "Volume", "Volume Unit", "Volume Type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Tank volumes CSV missing columns: {sorted(missing)}")

    df["Volume"] = _parse_volume_series(df["Volume"], cfg.thousands_sep)
    df["Time"] = pd.to_datetime(df["Time"], format=cfg.date_format, errors="raise")
    df["Entered By"] = df.get("Entered By", pd.Series([pd.NA] * len(df))).replace("", pd.NA)

    logger.info("Loaded %s rows | tanks: %s", f"{len(df):,}", sorted(df["Tank"].unique().tolist()))
    return df


def read_dispenses_or_deliveries(path: str | Path, cfg: PipelineConfig) -> tuple[str, pd.DataFrame]:
    """
    Lee un CSV que puede ser:
    A) outflow/dispenses (Lane/Meter columns u otras columnas con Time/Tank/Volume)
    B) delivery_transaction (Product, Collected At, Tank, Volume, ...)

    Retorna (kind, df_normalized)
      kind in {"dispenses", "deliveries"}
      df_normalized siempre con columnas mínimas:
        - Time (datetime)
        - Tank (str)
        - Volume (float)
    """
    path = Path(path)
    logger.info("Reading transactions from %s", path)
    df = pd.read_csv(path, keep_default_na=False)
    df = _strip_cols(df)

    # Detectar formato delivery_transaction
    if "Collected At" in df.columns and "Volume" in df.columns and "Tank" in df.columns:
        df["Volume"] = _parse_volume_series(df["Volume"], cfg.thousands_sep)
        df["Time"] = pd.to_datetime(df["Collected At"], format=cfg.date_format, errors="raise")
        out = df[["Time", "Tank", "Volume"]].copy()
        return "deliveries", out

    # Formato long mínimo (Time/Tank/Volume)
    if {"Time", "Tank", "Volume"}.issubset(df.columns):
        df["Volume"] = _parse_volume_series(df["Volume"], cfg.thousands_sep) if "Volume" in df.columns else 0.0
        df["Time"] = pd.to_datetime(df["Time"], format=cfg.date_format, errors="coerce")
        if df["Time"].isna().all():
            # intento general (por si viene ISO)
            df["Time"] = pd.to_datetime(df["Time"], errors="raise")
        out = df[["Time", "Tank", "Volume"]].copy()
        return "dispenses", out

    # Formato wide con lanes/meters en columnas
    lane_cols = [c for c in cfg.lane_columns if c in df.columns]
    meter_cols = [c for c in cfg.meter_columns if c in df.columns]
    time_col = "Time" if "Time" in df.columns else ("Collected At" if "Collected At" in df.columns else None)
    if time_col and (lane_cols or meter_cols):
        df["Time"] = pd.to_datetime(df[time_col], format=cfg.date_format, errors="coerce")
        if df["Time"].isna().all():
            df["Time"] = pd.to_datetime(df[time_col], errors="raise")

        melt_cols = lane_cols + meter_cols
        melted = df[["Time"] + melt_cols].melt(id_vars=["Time"], var_name="Tank", value_name="Volume")
        melted["Volume"] = _parse_volume_series(melted["Volume"], cfg.thousands_sep).fillna(0.0)
        melted = melted[melted["Volume"].fillna(0.0) != 0.0].copy()
        return "dispenses", melted[["Time", "Tank", "Volume"]].copy()

    raise ValueError(
        "Unrecognized transactions CSV format. Provide columns like (Collected At, Tank, Volume) or (Time, Tank, Volume) or (Time + lane/meter columns). "
        f"Got columns: {df.columns.tolist()}"
    )
