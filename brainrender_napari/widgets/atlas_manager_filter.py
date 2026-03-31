from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


class AtlasManagerFilter(QWidget):
    """Implements simple query-based filtering for the atlas table view,
    allowing users to search for specific atlases."""

    def __init__(
        self, atlas_manager_view: AtlasManagerView, parent: QWidget = None
    ) -> None:
        super().__init__(parent)

        self.atlas_manager_view: AtlasManagerView = atlas_manager_view
        self.setup_ui()

    def setup_ui(self) -> None:
        """Creates embedded widgets and attaches these within a layout."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.query_field = QLineEdit(self)
        self.query_field.setPlaceholderText("Search...")
        self.query_field.textChanged.connect(self.apply)

        self.layout.addWidget(QLabel("Query:"))
        self.layout.addWidget(self.query_field)

        self.column_field = QComboBox()
        self.column_field.addItems(
            self.atlas_manager_view.source_model.column_headers
        )
        self.column_field.insertItem(0, "Any")
        for col in self.atlas_manager_view.hidden_columns:
            self.column_field.removeItem(self.column_field.findText(col))
        self.column_field.setCurrentIndex(0)
        self.column_field.currentIndexChanged.connect(self.apply)

        self.layout.addWidget(QLabel("Column:"))
        self.layout.addWidget(self.column_field)

        # Species filter
        self.species_field = QComboBox()
        self.species_field.setToolTip("Filter atlases by species")
        self._populate_species()
        self.species_field.currentTextChanged.connect(self._on_species_changed)

        self.layout.addWidget(QLabel("Species:"))
        self.layout.addWidget(self.species_field)

    def _populate_species(self) -> None:
        """Populate species combo from the source model."""
        self.species_field.clear()
        self.species_field.addItem("All Species")
        if hasattr(self.atlas_manager_view.source_model, "get_unique_species"):
            species_list = (
                self.atlas_manager_view.source_model.get_unique_species()
            )
            self.species_field.addItems(species_list)

    def _on_species_changed(self, species: str) -> None:
        """Apply species filter when species combo changes."""
        if species == "All Species":
            # Reset to the current text query filter
            self.apply()
        else:
            species_col = (
                self.atlas_manager_view.source_model.column_headers.index(
                    "Species"
                )
            )
            self.atlas_manager_view.proxy_model.setFilterKeyColumn(species_col)
            self.atlas_manager_view.proxy_model.setFilterFixedString(species)

    def apply(self) -> None:
        """Updates proxy's internal state based on input and
        applies filter."""
        # Reset species combo if user types a query
        if self.species_field.currentText() != "All Species":
            self.species_field.blockSignals(True)
            self.species_field.setCurrentIndex(0)
            self.species_field.blockSignals(False)

        query = self.query_field.text()
        column = self.column_field.currentText()

        if column == "Any":
            self.atlas_manager_view.proxy_model.setFilterKeyColumn(-1)
        else:
            column_index = (
                self.atlas_manager_view.source_model.column_headers.index(
                    column
                )
            )
            self.atlas_manager_view.proxy_model.setFilterKeyColumn(
                column_index
            )

        # apply filter
        self.atlas_manager_view.proxy_model.setFilterFixedString(query)
