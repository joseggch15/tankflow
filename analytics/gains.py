"""Detección de inflow (ganancias) en virtual tanks y conciliación con Main Tank."""
from __future__ import annotations

import numpy as np
import pandas as pd
from tankflow.config.models import PipelineConfig


def compute_gains(df_wide: pd.DataFrame, cfg: PipelineConfig) -> pd.DataFrame:
    """
    Calcula gains por virtual tank y totales de conciliación.
    Requiere un DataFrame 'wide' con columnas delta_<tank_suffix>.
    """
    df = df_wide.copy()
    vt_suffixes = [t.split(" - ")[-1] for t in cfg.virtual_tanks]

    for sfx in vt_suffixes:
        col = f"delta_{sfx}"
        if col in df.columns:
            df[f"gain_{sfx}"] = np.where(df[col] > cfg.gain_threshold, df[col], 0.0)
        else:
            df[f"gain_{sfx}"] = 0.0

    gain_cols = [f"gain_{sfx}" for sfx in vt_suffixes]
    df["gain_virtual_tank_total"] = df[gain_cols].sum(axis=1)

    mt_sfx = cfg.main_tank.split(" - ")[-1]
    mt_col = f"delta_{mt_sfx}"
    if mt_col in df.columns:
        df["mt_delta_vt"] = df[mt_col] - df["gain_virtual_tank_total"]
    else:
        df["mt_delta_vt"] = np.nan

    return df


def sumif_positive(series: pd.Series) -> float:
    """Replica SUMIF(range, '>0') de Excel."""
    return float(series[series > 0].sum())
