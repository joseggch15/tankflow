"""Tablas pivot / agregaciones equivalentes a hojas Excel."""
from __future__ import annotations

import pandas as pd
from tankflow.analytics.delivery_detection import DeliveryEvent


def summary_tank_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Replica SummaryTankPerHour: Sum of Volume por Hour x Tank."""
    required = {"Hour", "Tank", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"summary_tank_per_hour missing columns: {sorted(missing)}")

    pivot = pd.pivot_table(
        df,
        index="Hour",
        columns="Tank",
        values="Volume",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot.columns.name = None
    return pivot.reset_index()


def dispenses_summary(df_tx: pd.DataFrame) -> pd.DataFrame:
    """Replica DispensesSummary: filas = Date x Hour, columnas = Tank, valor = Sum of Volume."""
    required = {"Date", "Hour", "Tank", "Volume"}
    missing = required - set(df_tx.columns)
    if missing:
        raise ValueError(f"dispenses_summary missing columns: {sorted(missing)}")

    pivot = pd.pivot_table(
        df_tx,
        index=["Date", "Hour"],
        columns="Tank",
        values="Volume",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot.columns.name = None
    return pivot.reset_index()


def delivery_events_table(events: list[DeliveryEvent]) -> pd.DataFrame:
    """Tabla simple (una fila por evento)."""
    rows = [
        dict(
            event_id=e.event_id,
            tank=e.tank,
            start_time=e.start_time,
            end_time=e.end_time,
            tls_volume=e.tls_volume,
            row_count=e.row_count,
        )
        for e in events
    ]
    return pd.DataFrame(rows)


def delivery_transactions_table(df_deliveries: pd.DataFrame) -> pd.DataFrame:
    """Normaliza deliveries (Time, Tank, Volume) a una tabla por día/hora."""
    if df_deliveries.empty:
        return df_deliveries
    # agrega por hora para comparar con pivots
    out = df_deliveries.copy()
    out["Date"] = out["Time"].dt.date
    out["Hour"] = out["Time"].dt.hour
    return (
        out.groupby(["Date", "Hour", "Tank"], as_index=False)["Volume"].sum()
    )
