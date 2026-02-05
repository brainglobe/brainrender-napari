from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

from brainrender_napari.widgets.atlas_viewer_view import AtlasViewerView


class AtlasViewerFilter(QWidget):
    """Implements simple query-based filtering for the atlas table view,
    allowing users to search for specific atlases."""

    def __init__(
        self, atlas_viewer_view: AtlasViewerView, parent: QWidget = None
    ):
        super().__init__(parent)
        self.atlas_viewer_view = atlas_viewer_view
        self.setup_ui()

    def setup_ui(self):
        """Creates embedded widgets and attaches these within a layout."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # Search Box
        self.query_field = QLineEdit(self)
        self.query_field.setPlaceholderText("Search...")
        self.query_field.textChanged.connect(self.apply)
        self.layout.addWidget(QLabel("Query:"))
        self.layout.addWidget(self.query_field)

        # Column Selector
        self.column_field = QComboBox()
        # Use source_model to get headers
        self.column_field.addItems(
            self.atlas_viewer_view.source_model.column_headers
        )
        self.column_field.insertItem(0, "Any")

        # Remove hidden columns from the dropdown
        for col in self.atlas_viewer_view.hidden_columns:
            idx = self.column_field.findText(col)
            if idx >= 0:
                self.column_field.removeItem(idx)

        self.column_field.setCurrentIndex(0)
        self.column_field.currentIndexChanged.connect(self.apply)
        self.layout.addWidget(QLabel("Column:"))
        self.layout.addWidget(self.column_field)

    def apply(self):
        """Updates proxy's internal state based on input and
        applies filter."""
        query = self.query_field.text()
        column = self.column_field.currentText()

        if column == "Any":
            self.atlas_viewer_view.proxy_model.setFilterKeyColumn(-1)
        else:
            column_index = (
                self.atlas_viewer_view.source_model.column_headers.index(
                    column
                )
            )
            self.atlas_viewer_view.proxy_model.setFilterKeyColumn(column_index)

        # apply filter
        self.atlas_viewer_view.proxy_model.setFilterFixedString(query)
