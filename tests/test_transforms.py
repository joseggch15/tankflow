"""Unit tests básicos del pipeline (sin golden files por defecto)."""
import pandas as pd
import numpy as np
import pytest

from tankflow.transforms.time_features import add_time_features
from tankflow.transforms.deltas import compute_deltas, pivot_tanks_wide
from tankflow.analytics.gains import compute_gains, sumif_positive
from tankflow.config.models import PipelineConfig


@pytest.fixture
def cfg():
    return PipelineConfig()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Time": pd.to_datetime([
            "2026-01-14 08:00", "2026-01-14 08:01",
            "2026-01-14 08:00", "2026-01-14 08:01",
        ]),
        "Tank": [
            "LFO - Main Tank", "LFO - Main Tank",
            "LFO - 171-TK-03", "LFO - 171-TK-03",
        ],
        "Volume": [684720.16, 684820.16, 45791.34, 45900.00],
        "Volume Unit": ["Litres"] * 4,
        "Volume Type": ["Ambient"] * 4,
        "Entered By": [None] * 4,
    })


def test_time_features(sample_df):
    df = add_time_features(sample_df.copy())
    assert "Time2" in df.columns
    assert "Minute" in df.columns
    assert abs(df.iloc[0]["Time2"] - 8/24) < 1e-6
    assert df.iloc[0]["Minute"] == 0


def test_deltas(sample_df, cfg):
    df = compute_deltas(sample_df.copy(), cfg)
    main = df[df["Tank"] == cfg.main_tank].sort_values("Time")
    assert np.isnan(main.iloc[0]["delta"])
    assert abs(main.iloc[1]["delta"] - 100.0) < 0.01


def test_wide_and_gains(sample_df, cfg):
    df = add_time_features(sample_df.copy())
    df = compute_deltas(df, cfg)
    wide = pivot_tanks_wide(df, cfg)
    out = compute_gains(wide, cfg)
    assert "gain_virtual_tank_total" in out.columns


def test_sumif_positive():
    s = pd.Series([-10, 0, 50, 200, -5, 80])
    assert sumif_positive(s) == 330.0
