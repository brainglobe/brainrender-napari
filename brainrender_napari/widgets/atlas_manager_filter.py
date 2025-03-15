from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


class AtlasManagerFilter(QWidget):
    """Implements simple query-based filtering for the atlas table view,
    allowing users to search for specific atlases."""

    def __init__(
        self, atlas_manager_view: AtlasManagerView, parent: QWidget = None
    ):
        super().__init__(parent)

        self.atlas_manager_view = atlas_manager_view
        self.setup_ui()
        return

    def setup_ui(self):
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
        return

    def clear(self):
        self.atlas_manager_view.proxy_model.setFilterFixedString("")

    def closeEvent(self, event):
        """Cleans up the widget when it is closed."""
        self.query_field.textChanged.disconnect(self.apply)
        self.column_field.currentIndexChanged.disconnect(self.apply)
        self.clear()
        return

    def apply(self):
        """Updates proxy's internal state based on input and
        applies filter."""
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
        return
