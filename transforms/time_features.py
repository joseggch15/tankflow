"""Equivalentes Python de las fórmulas de tiempo en Excel."""
from __future__ import annotations

import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega:
      - Time2: fracción del día (equivalente a MOD(Time, 1) en Excel)
      - Minute: minuto del timestamp
      - Hour: hora del día
      - Date: fecha (date)
    Requiere columna Time (datetime64[ns]).
    """
    if "Time" not in df.columns:
        raise ValueError("add_time_features requires a 'Time' column")

    out = df.copy()
    # MOD(serial_excel,1) = (segundos del día) / 86400
    out["Time2"] = (
        out["Time"].dt.hour * 3600
        + out["Time"].dt.minute * 60
        + out["Time"].dt.second
    ) / 86400.0
    out["Minute"] = out["Time"].dt.minute
    out["Hour"] = out["Time"].dt.hour
    out["Date"] = out["Time"].dt.date
    return out
