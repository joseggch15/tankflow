"""Modelos Pydantic v2 para configuración y (opcionalmente) esquemas de entrada."""
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class PipelineConfig(BaseModel):
    # ── parsing/tiempo ────────────────────────────────────────────────────
    timezone: str = "America/Bogota"
    date_format: str = "%d/%m/%Y %H:%M"
    thousands_sep: str = ","
    decimal_sep: str = "."

    # ── tanques ───────────────────────────────────────────────────────────
    main_tank: str = "LFO - Main Tank"
    virtual_tanks: list[str] = [
        "LFO - 171-TK-03",
        "LFO - 171-TK-04",
        "LFO - 171-TK-05",
    ]
    volume_unit: str = "Litres"
    volume_type: str = "Ambient"

    # ── analytics ─────────────────────────────────────────────────────────
    gain_threshold: float = 70.0
    delivery_min_gap_minutes: int = 5
    delivery_min_volume: float = 500.0
    delivery_match_max_minutes: int = 120  # matching con deliveries (opcional)

    # ── dispenses/outflow ─────────────────────────────────────────────────
    lane_columns: list[str] = ["Lane1", "Lane2", "Lane3"]
    meter_columns: list[str] = ["Meter_846", "Meter_847", "Meter_848"]

    # ── output/logging ────────────────────────────────────────────────────
    export_xlsx: bool = True
    export_csv: bool = True
    results_dir: str = "outputs/"
    log_level: str = "INFO"


# ── (Opcional) esquemas de filas ------------------------------------------------
class TankVolumeRow(BaseModel):
    time: str = Field(..., alias="Time")
    tank: str = Field(..., alias="Tank")
    volume_unit: Literal["Litres"] = Field(..., alias="Volume Unit")
    volume: float = Field(..., alias="Volume")
    volume_type: str = Field(..., alias="Volume Type")
    entered_by: Optional[str] = Field(default=None, alias="Entered By")

    @field_validator("volume", mode="before")
    @classmethod
    def parse_volume(cls, v: str | float) -> float:
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return float(v)


class DeliveryTransactionRow(BaseModel):
    product: Optional[str] = Field(default=None, alias="Product")
    collected_at: str = Field(..., alias="Collected At")
    tank: str = Field(..., alias="Tank")
    docket_number: Optional[str] = Field(default=None, alias="Docket Number")
    supplier: Optional[str] = Field(default=None, alias="Supplier")
    confirmed: Optional[str] = Field(default=None, alias="Confirmed")
    type: Optional[str] = Field(default=None, alias="Type")
    volume_unit: Optional[str] = Field(default=None, alias="Volume Unit")
    volume: float = Field(..., alias="Volume")

    @field_validator("volume", mode="before")
    @classmethod
    def parse_volume(cls, v: str | float) -> float:
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return float(v)
