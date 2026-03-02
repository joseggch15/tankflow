"""Detección automática de eventos de delivery usando deltas positivos."""
from __future__ import annotations

import pandas as pd
from dataclasses import dataclass

from tankflow.config.models import PipelineConfig
from tankflow.analytics.gains import sumif_positive


@dataclass(frozen=True)
class DeliveryEvent:
    event_id: int
    tank: str
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    tls_volume: float
    row_count: int


def detect_delivery_events(df: pd.DataFrame, tank: str, cfg: PipelineConfig) -> list[DeliveryEvent]:
    """
    Detecta ventanas de delivery en un tanque dado.

    Idea (excel-like):
      - Usamos delta > gain_threshold SOLO para detectar el inicio/fin del evento.
      - El volumen TLS del evento se calcula como SUMIF(delta, ">0") dentro de la ventana (inclusive).

    Parámetros:
      - gain_threshold: umbral de detección
      - delivery_min_gap_minutes: gap máximo entre *picos* (delta>threshold) para el mismo evento
      - delivery_min_volume: mínimo TLS para aceptar el evento
    """
    if df.empty:
        return []

    required = {"Time", "Tank", "delta"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"detect_delivery_events missing columns: {sorted(missing)}")

    sub = df[df["Tank"] == tank].sort_values("Time").reset_index(drop=True).copy()
    # Filas que disparan detección
    gain_hits = sub[sub["delta"] > cfg.gain_threshold].copy()
    if gain_hits.empty:
        return []

    # Agrupar hits por gap
    gap_min = cfg.delivery_min_gap_minutes
    hit_diff = gain_hits["Time"].diff().dt.total_seconds().div(60.0)
    new_evt = (hit_diff.isna()) | (hit_diff > gap_min)
    gain_hits["evt"] = new_evt.cumsum() - 1

    events: list[DeliveryEvent] = []
    eid = 0

    for _, g in gain_hits.groupby("evt", sort=True):
        start = g["Time"].iloc[0]
        end = g["Time"].iloc[-1]

        # Ventana inclusive: todas las filas entre start y end
        window = sub[(sub["Time"] >= start) & (sub["Time"] <= end)]
        tls = sumif_positive(window["delta"].fillna(0.0))

        if tls >= cfg.delivery_min_volume:
            events.append(
                DeliveryEvent(
                    event_id=eid,
                    tank=tank,
                    start_time=start,
                    end_time=end,
                    tls_volume=round(float(tls), 2),
                    row_count=int(len(window)),
                )
            )
            eid += 1

    return events
