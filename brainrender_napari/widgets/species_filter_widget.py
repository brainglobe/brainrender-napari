"""A reusable species filter widget for atlas table views.

Provides a QComboBox dropdown listing unique species from the atlas data,
with an "All Species" option to show everything.
"""

from qtpy.QtCore import QSortFilterProxyModel, Signal
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget


class SpeciesFilterWidget(QWidget):
    """A dropdown widget to filter atlas tables by species.

    Works with any QTableView that uses a QSortFilterProxyModel
    and an AtlasTableModel as the source model.
    """

    species_changed = Signal(str)

    def __init__(
        self,
        proxy_model: QSortFilterProxyModel,
        source_model,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)

        self.proxy_model = proxy_model
        self.source_model = source_model

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.label = QLabel("Species:")
        self.combo = QComboBox()
        self.combo.setToolTip(
            "Filter atlases by species. "
            "Select 'All Species' to show all atlases."
        )

        self._populate_species()
        self.combo.currentTextChanged.connect(self._on_species_changed)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combo)

    def _populate_species(self) -> None:
        """Populate the combo box with unique species."""
        self.combo.clear()
        self.combo.addItem("All Species")

        if hasattr(self.source_model, "get_unique_species"):
            species_list = self.source_model.get_unique_species()
            self.combo.addItems(species_list)

    def _on_species_changed(self, species: str) -> None:
        """Apply species filter to the proxy model."""
        species_col = self.source_model.column_headers.index("Species")

        if species == "All Species":
            # Clear the species filter
            self.proxy_model.setFilterKeyColumn(-1)
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterKeyColumn(species_col)
            self.proxy_model.setFilterFixedString(species)

        self.species_changed.emit(species)

    def refresh(self) -> None:
        """Refresh the species list (e.g. after downloading an atlas)."""
        current = self.combo.currentText()
        self._populate_species()
        index = self.combo.findText(current)
        if index >= 0:
            self.combo.setCurrentIndex(index)
