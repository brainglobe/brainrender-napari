from brainglobe_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_local_atlas_version,
)
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtWidgets import QTableView

from brainrender_napari.utils.formatting import format_atlas_name


class AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self, view_type: QTableView):
        super().__init__()
        self.column_headers = [
            "Raw name",
            "Atlas",
            "Local version",
            "Latest version",
        ]
        assert hasattr(
            view_type, "get_tooltip_text"
        ), "Views for this model must implement"
        "a `classmethod` called `get_tooltip_text`"
        self.view_type = view_type
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh model data by calling atlas API"""
        all_atlases = get_all_atlases_lastversions()
        data = []
        for name, latest_version in all_atlases.items():
            if name in get_atlases_lastversions().keys():
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

    def rowCount(self, index: QModelIndex = QModelIndex()):
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
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
