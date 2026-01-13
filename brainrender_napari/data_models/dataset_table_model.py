"""Data model for atlas-registered datasets table."""

from typing import Optional

from brainglobe_atlasapi.list_atlases import get_downloaded_atlases
from napari.settings import get_settings
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtGui import QBrush, QColor

from brainrender_napari.utils.download_datasets import (
    get_available_datasets,
    get_downloaded_datasets,
)


class DatasetTableModel(QAbstractTableModel):
    """A table data model for atlas-registered datasets."""

    def __init__(self, view_type=None):
        super().__init__()
        self.column_headers: list[str] = [
            "Dataset ID",
            "Dataset Name",
            "Species",
            "Atlas",
            "Data Type",
            "Size",
            "Status",
        ]
        self.view_type = view_type
        self._species_filter: Optional[str] = None
        self._data_type_filter: Optional[str] = None
        self.refresh_data()

    def set_filters(
        self, species: Optional[str] = None, data_type: Optional[str] = None
    ):
        """Set filters for the dataset table."""
        self._species_filter = species
        self._data_type_filter = data_type
        self.refresh_data()

    def refresh_data(self):
        """Refresh model data by fetching available datasets."""
        self.beginResetModel()  # Notify view that we're about to change data

        available_datasets = get_available_datasets(
            species=self._species_filter, data_type=self._data_type_filter
        )
        downloaded_datasets = get_downloaded_datasets()

        data = []
        for dataset_id, metadata in available_datasets.items():
            # Check if required atlas is downloaded
            required_atlas = metadata.get("atlas")
            atlas_downloaded = (
                required_atlas in get_downloaded_atlases()
                if required_atlas
                else True
            )

            status = (
                "Downloaded"
                if dataset_id in downloaded_datasets
                else "Available"
            )
            if required_atlas and not atlas_downloaded:
                status = "Atlas Required"

            data.append(
                [
                    dataset_id,
                    metadata.get("name", "Unknown"),
                    metadata.get("species", "Unknown"),
                    metadata.get("atlas", "N/A"),
                    metadata.get("data_type", "Unknown"),
                    f"{metadata.get('size_mb', 0):.1f} MB",
                    status,
                ]
            )

        self._data = data
        self.endResetModel()  # Notify view that data has changed

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        if role == Qt.ToolTipRole:
            dataset_id = self._data[index.row()][0]
            available_datasets = get_available_datasets()
            if dataset_id in available_datasets:
                metadata = available_datasets[dataset_id]
                description = metadata.get(
                    "description", "No description available"
                )
                return f"{metadata.get('name')}\n\n{description}\n\nStatus: {self._data[index.row()][6]}"

        if role == Qt.BackgroundRole:
            theme = get_settings().appearance.theme  # 'dark' or 'light'

            status = self._data[index.row()][6]
            if status == "Downloaded":
                # Green tint for downloaded datasets
                if theme == "dark":
                    return QBrush(QColor(50, 120, 50))  # dark green
                return QBrush(QColor(200, 255, 200))  # light green
            elif status == "Atlas Required":
                # Yellow/amber tint for datasets requiring atlas
                if theme == "dark":
                    return QBrush(QColor(150, 100, 0))  # dark amber
                return QBrush(QColor(255, 220, 150))  # light amber
            # Available datasets get default background

        return None

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        if not self._data:
            return len(self.column_headers)
        return len(self._data[0])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Customises the horizontal header data of model."""
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section >= 0 and section < len(self.column_headers):
                return self.column_headers[section]
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)
