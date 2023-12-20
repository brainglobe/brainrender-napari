from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_downloaded_atlases,
    get_local_atlas_version,
)
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt

from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
)


class AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self):
        super().__init__()
        self.column_headers = [
            "Raw name",
            "Atlas",
            "Local version",
            "Latest version",
        ]
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
                        self._format_name(name),
                        get_local_atlas_version(name),
                        latest_version,
                    ]
                )
            else:
                data.append(
                    [name, self._format_name(name), "n/a", latest_version]
                )

        self._data = data

    def _format_name(self, name: str) -> str:
        formatted_name = name.split("_")
        formatted_name[0] = formatted_name[0].capitalize()
        formatted_name[-1] = f"({formatted_name[-1].split('um')[0]} \u03BCm)"
        return " ".join([formatted for formatted in formatted_name])

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.ToolTipRole:
            hovered_atlas_name = self._data[index.row()][0]
            return AtlasTableModel._get_tooltip_text(hovered_atlas_name)

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

    @classmethod
    def _get_tooltip_text(cls, atlas_name: str):
        """Returns the atlas metadata as a formatted string,
        as well as instructions on how to interact with the atlas."""
        if atlas_name in get_downloaded_atlases():
            metadata = read_atlas_metadata_from_file(atlas_name)
            metadata_as_string = ""
            for key, value in metadata.items():
                metadata_as_string += f"{key}:\t{value}\n"

            tooltip_text = f"{atlas_name} (double-click to add to viewer)\
            \n{metadata_as_string}"
        elif atlas_name in get_all_atlases_lastversions().keys():
            tooltip_text = f"{atlas_name} (double-click to download)"
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text
