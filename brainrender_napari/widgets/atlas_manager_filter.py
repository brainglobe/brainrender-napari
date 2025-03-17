from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView

# TODO: add tooltip to fields in filter widget


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
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.upper_row = QHBoxLayout()
        self.layout.addLayout(self.upper_row)

        self.lower_row = QHBoxLayout()
        self.lower_row.setSpacing(10)
        self.layout.addLayout(self.lower_row)

        self.query_field = QLineEdit(self)
        self.query_field.setPlaceholderText("Search...")
        self.query_field.textChanged.connect(self.apply)

        self.upper_row.addWidget(QLabel("Query:"))
        self.upper_row.addWidget(self.query_field)

        self.column_field = QComboBox()
        self.column_field.addItems(
            self.atlas_manager_view.source_model.column_headers
        )
        self.column_field.insertItem(0, "Any")
        for col in self.atlas_manager_view.hidden_columns:
            self.column_field.removeItem(self.column_field.findText(col))
        self.column_field.setCurrentIndex(0)
        self.column_field.currentIndexChanged.connect(self.apply)

        self.lower_row.addWidget(QLabel("Column:"))
        self.lower_row.addWidget(self.column_field)

        self.downloaded_only_checkbox = QCheckBox("Downloaded only")
        self.downloaded_only_checkbox.stateChanged.connect(self.apply)
        self.lower_row.addWidget(self.downloaded_only_checkbox)

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
        downloaded_only = self.downloaded_only_checkbox.isChecked()

        # TODO: if downloaded_only_checkbox is checked, filter
        # only downloaded atlases, i.e. drop where local version = "n/a"

        # needs custom filtering solution, see:
        # https://www.dayofthenewdan.com/2013/02/09/Qt_QSortFilterProxyModel.html

        if downloaded_only:
            pass

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
