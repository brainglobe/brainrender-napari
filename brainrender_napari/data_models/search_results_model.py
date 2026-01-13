"""Data model for displaying database search results."""

from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt


class SearchResultsModel(QAbstractTableModel):
    """Table model for displaying neuron search results from databases."""

    def __init__(self, results: list):
        super().__init__()
        self.column_headers = [
            "ID",
            "Name",
            "Source",
            "Structure Area",
            "Species",
            "Database",
        ]
        self._results = results

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._results)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.column_headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._results):
            return None

        neuron = self._results[row]

        # Map columns to data
        column_mapping = {
            0: str(neuron.get("id", "N/A")),
            1: str(neuron.get("name", "Unknown")),
            2: str(neuron.get("source", "Unknown")),
            3: str(
                neuron.get(
                    "structure_area", neuron.get("structure_name", "N/A")
                )
            ),
            4: str(neuron.get("species", "Unknown")),
            5: str(neuron.get("database", "unknown")),
        }

        return column_mapping.get(col, "")

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        if (
            role == Qt.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and section < len(self.column_headers)
        ):
            return self.column_headers[section]
        return None

    def get_neuron_at_index(self, index: QModelIndex):
        """Get the full neuron data for a given index."""
        if not index.isValid():
            return None
        row = index.row()
        if 0 <= row < len(self._results):
            return self._results[row]
        return None
