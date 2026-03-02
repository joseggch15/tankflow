from __future__ import annotations

import platform
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QWidget

PALETTE = {
    "primary_700": "#1565C0",
    "primary_600": "#1E88E5",
    "primary_800": "#0D47A1",
    "primary_50":  "#E3F2FD",
    "primary_txt_on": "#FFFFFF",

    "accent_700": "#F57C00",

    "success_600": "#2E7D32",
    "error_600":   "#C62828",
    "error_50":    "#FFEBEE",
    "warn_600":    "#ED6C02",
    "warn_50":     "#FFFBEA",
    "info_600":    "#0288D1",

    "neutral_900": "#111827",
    "neutral_700": "#374151",
    "neutral_600": "#4B5563",
    "neutral_500": "#6B7280",
    "neutral_400": "#9CA3AF",
    "neutral_300": "#D1D5DB",
    "neutral_200": "#E5E7EB",
    "neutral_100": "#F3F4F6",
    "neutral_50":  "#F9FAFB",
    "panel_bg":    "#F5F7FA",
    "white":       "#FFFFFF",
}


def _base_font() -> QFont:
    system = platform.system()
    family = (
        "Segoe UI"
        if system == "Windows"
        else ("SF Pro Text" if system == "Darwin" else "Sans Serif")
    )
    return QFont(family, 10)


def apply_app_theme(app: QApplication) -> None:
    app.setFont(_base_font())
    app.setStyleSheet(build_qss())


def mark_error(widget: QWidget, on: bool) -> None:
    widget.setProperty("hasError", bool(on))
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def build_qss() -> str:
    p = PALETTE
    return f"""
QWidget {{
  background: {p['neutral_50']};
  color: {p['neutral_900']};
  font-family: "{_base_font().family()}", "Segoe UI", "SF Pro Text", sans-serif;
}}

QGroupBox {{
  background: {p['panel_bg']};
  border: 1px solid {p['neutral_200']};
  border-radius: 8px;
  margin-top: 14px;
}}
QGroupBox::title {{
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 8px;
  margin-left: 6px;
  color: {p['neutral_700']};
  font-weight: 600;
}}

/* Inputs */
QLineEdit, QComboBox, QDateTimeEdit {{
  background: {p['white']};
  border: 1px solid {p['neutral_300']};
  border-radius: 8px;
  padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
  border: 1px solid {p['primary_700']};
}}
QLineEdit[hasError="true"], QComboBox[hasError="true"], QDateTimeEdit[hasError="true"] {{
  border: 1px solid {p['error_600']};
  background: {p['error_50']};
}}

/* Buttons */
QPushButton {{
  background: {p['neutral_100']};
  border: 1px solid {p['neutral_300']};
  border-radius: 8px;
  padding: 8px 12px;
}}
QPushButton[variant="primary"] {{
  background: {p['primary_700']};
  border: 1px solid {p['primary_700']};
  color: {p['primary_txt_on']};
}}
QPushButton[variant="primary"]:hover {{ background: {p['primary_600']}; }}
QPushButton[variant="primary"]:pressed {{ background: {p['primary_800']}; }}

QPushButton[variant="secondary"] {{
  background: {p['neutral_100']};
  border: 1px solid {p['neutral_300']};
  color: {p['neutral_900']};
}}
QPushButton[variant="text"] {{
  background: transparent;
  border: none;
  color: {p['primary_700']};
  padding: 6px 8px;
}}
QPushButton[danger="true"] {{
  background: {p['error_600']};
  border-color: {p['error_600']};
  color: {p['white']};
}}

/* Tabs */
QTabWidget::pane {{
  border: 1px solid {p['neutral_200']};
  border-radius: 8px;
  background: {p['white']};
  top: -2px;
}}
QTabBar::tab {{
  background: {p['neutral_100']};
  color: {p['neutral_700']};
  padding: 8px 12px;
  margin-right: 2px;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}}
QTabBar::tab:selected {{
  background: {p['white']};
  color: {p['neutral_900']};
  border: 1px solid {p['neutral_200']};
  border-bottom-color: {p['white']};
}}

/* Tables */
QHeaderView::section {{
  background: {p['white']};
  color: {p['neutral_700']};
  padding: 6px 8px;
  border: 1px solid {p['neutral_200']};
  font-weight: 600;
}}
QTableView {{
  gridline-color: {p['neutral_200']};
  selection-background-color: {p['primary_50']};
  selection-color: {p['neutral_900']};
  alternate-background-color: {p['neutral_100']};
  background: {p['white']};
}}
"""
