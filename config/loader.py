"""Carga de configuración YAML a PipelineConfig."""
from __future__ import annotations

from pathlib import Path
import yaml

from .models import PipelineConfig


def load_config(path: str | Path = "tankflow/config/settings.yaml") -> PipelineConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Mezcla de secciones (pipeline/tanks/analytics/dispenses/output) en un modelo flat
    merged: dict = {}
    for section in ("pipeline", "tanks", "analytics", "dispenses", "output"):
        merged |= (raw.get(section) or {})

    return PipelineConfig(**merged)
