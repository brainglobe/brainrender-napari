from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_local_atlas_version,
)
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt

from brainrender_napari.utils.formatting import format_atlas_name


class _AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases.

    Intended to be used by proxy models, as a singleton.
    Proxy model classes should derive from :class:`AtlasSortFilterProxyModel`.

    This design choice facilitates low-code synchronisation
    across proxy models and their views.

    The singleton instance is exposed as `singleton_atlas_table_model`
    in this module. The implementation of the singleton is based on the fact
    that each Python module is imported only once.
    """

    def __init__(self):
        """Initialize the _AtlasTableModel."""
        super().__init__()
        self.column_headers = [
            "Raw name",
            "Atlas",
            "Local version",
            "Latest version",
        ]
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh model data by calling atlas API.

        Emits dataChanged to update proxy models.
        """
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

        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        assert top_left.isValid()
        assert bottom_right.isValid()
        # we use string comparison to check both have the same parent.
        assert top_left.parent().__str__() == bottom_right.parent().__str__()
        self.dataChanged.emit(top_left, bottom_right)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """Return the data to be displayed at the given index and role."""
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model, ie the number of atlases."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return len(self._data[0])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ) -> str:
        """Return the header data for the given section, orientation, and role.

        Args:
            section (int): The section index.
            orientation (Qt.Orientation): The orientation of the header.
            role (Qt.ItemDataRole): The role of the header data.

        Returns:
            Any: The header data for the given section, orientation, and role.

        Raises:
            ValueError: If the (horizontal) section value is unexpected.
        """
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section >= 0 and section < len(self.column_headers):
                return self.column_headers[section]
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)


singleton_atlas_table_model = _AtlasTableModel()
