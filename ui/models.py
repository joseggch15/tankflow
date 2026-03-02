from __future__ import annotations

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant


class PandasTableModel(QAbstractTableModel):
    """Modelo mínimo para renderizar un DataFrame en QTableView."""

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def set_df(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if self._df is None else len(self._df.index)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if self._df is None else len(self._df.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid() or self._df is None:
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            if pd.isna(value):
                return ""
            # Evitar strings enormes
            s = str(value)
            return s if len(s) <= 200 else (s[:197] + "…")

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if self._df is None:
            return QVariant()
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(self._df.index[section])
