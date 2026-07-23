from brainglobe_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_local_atlas_version,
)
from napari.settings import get_settings
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import QTableView

from brainrender_napari.utils.formatting import format_atlas_name


class AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self, view_type: QTableView):
        super().__init__()
        self.column_headers: list[str] = [
            "Raw name",
            "Atlas",
            "Local version",
            "Latest version",
        ]
        assert hasattr(view_type, "get_tooltip_text"), (
            "Views for this model must implement"
            "a `classmethod` called `get_tooltip_text`"
        )
        self.view_type: QTableView = view_type
        self.refresh_data()

    def refresh_data(self):
        """Refresh model data by calling atlas API"""
        all_atlases: dict[str, str] = get_all_atlases_lastversions()
        local_atlases = get_atlases_lastversions().keys()
        data = []
        for name, latest_version in all_atlases.items():
            if name in local_atlases:
                data.append(
                    [
                        name,
                        format_atlas_name(name),
                        get_local_atlas_version(name),
                        latest_version,
                    ]
                )
            else:
                data.append(
                    [name, format_atlas_name(name), "n/a", latest_version]
                )

        self._data = data

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.ToolTipRole:
            hovered_atlas_name = self._data[index.row()][0]
            return self.view_type.get_tooltip_text(hovered_atlas_name)
        if role == Qt.BackgroundRole:

            theme = get_settings().appearance.theme  # 'dark' or 'light'

            local_version = self._data[index.row()][2]
            if local_version == "n/a":
                if theme == "dark":
                    return QBrush(QColor(80, 80, 80))  # dark grey
                return QBrush(Qt.lightGray)  # light grey
            else:
                latest_version = self._data[index.row()][3]
                if local_version == latest_version:
                    # Up-to-date atlas: normal background (default)
                    return None
                # Out-of-date atlas:
                if theme == "dark":
                    return QBrush(QColor(255, 140, 0))  # dark amber
                return QBrush(QColor(255, 191, 0))  # light amber

        return None

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._data[0])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Customises the horizontal header data of model,
        and raises an error if an unexpected column is found."""
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section >= 0 and section < len(self.column_headers):
                return self.column_headers[section]
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)
