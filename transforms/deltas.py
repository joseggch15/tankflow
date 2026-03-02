"""Cálculo de deltas (diferencia entre lecturas consecutivas) por tanque."""
from __future__ import annotations

import pandas as pd
from tankflow.config.models import PipelineConfig


def compute_deltas(df: pd.DataFrame, cfg: PipelineConfig) -> pd.DataFrame:
    """
    Para cada tanque (Main + virtual tanks), ordena por Time y calcula:
      delta(t) = Volume(t) - Volume(t-1)

    Retorna el DataFrame con columna 'delta' añadida.
    """
    required = {"Time", "Tank", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"compute_deltas missing columns: {sorted(missing)}")

    tanks = [cfg.main_tank] + cfg.virtual_tanks
    out = df[df["Tank"].isin(tanks)].copy()
    out = out.sort_values(["Tank", "Time"]).reset_index(drop=True)
    out["delta"] = out.groupby("Tank", sort=False)["Volume"].diff()
    # Para comodidad visual, ordenamos por Time (como Excel)
    return out.sort_values("Time").reset_index(drop=True)


def pivot_tanks_wide(df: pd.DataFrame, cfg: PipelineConfig) -> pd.DataFrame:
    """
    Convierte formato long → wide:
      index = Time
      columnas = Volume_<suffix>, delta_<suffix>

    Suffix = parte final de "LFO - XXX".
    """
    tanks = [cfg.main_tank] + cfg.virtual_tanks
    sub = df[df["Tank"].isin(tanks)].copy()

    wide = sub.pivot_table(
        index="Time",
        columns="Tank",
        values=["Volume", "delta"],
        aggfunc="last",
    )

    # Flatten columns: (value, tank) → value_suffix
    flat_cols = []
    for val, tank in wide.columns:
        suffix = str(tank).split(" - ")[-1].strip()
        flat_cols.append(f"{val}_{suffix}")
    wide.columns = flat_cols

    wide = wide.reset_index()
    return wide
