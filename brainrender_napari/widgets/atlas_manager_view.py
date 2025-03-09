"""The purpose of this file is to provide interactive table view to download
and update atlases. Users interacting with the table can request to
* download an atlas (double-click on row of a not-yet downloaded atlas)
* update an atlas (double-click on row of outdated local atlas)
They can also hover over an up-to-date local atlas and see that
it's up to date.

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""

from typing import Callable

from brainglobe_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_downloaded_atlases,
)
from brainglobe_atlasapi.update_atlases import install_atlas, update_atlas
from napari.qt import thread_worker
from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableView,
    QWidget,
)

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_dialog import AtlasManagerDialog


class AtlasManagerView(QTableView):
    download_atlas_confirmed = Signal(str)
    update_atlas_confirmed = Signal(str)

    def __init__(self, parent: QWidget = None):
        """Initialises an atlas table view with latest atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)

        self.table = AtlasTableModel(AtlasManagerView)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.table)
        self.setModel(self.proxy)

        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.doubleClicked.connect(self._on_row_double_clicked)
        self.hidden_columns = ["Raw name"]  # hide raw name
        for col in self.hidden_columns:
            self.hideColumn(self.table.column_headers.index(col))

    def _apply_filters(self, query: str):
        """Filters the table view based on the query."""
        self.proxy.setFilterFixedString(query)
        return

    def _on_row_double_clicked(self):
        atlas_name = self.selected_atlas_name()
        if atlas_name in get_downloaded_atlases():
            up_to_date = get_atlases_lastversions()[atlas_name]["updated"]
            if not up_to_date:
                update_dialog = AtlasManagerDialog(atlas_name, "Update")
                update_dialog.ok_button.clicked.connect(
                    self._on_update_atlas_confirmed
                )
                update_dialog.exec()
        else:
            download_dialog = AtlasManagerDialog(atlas_name, "Download")
            download_dialog.ok_button.clicked.connect(
                self._on_download_atlas_confirmed
            )
            download_dialog.exec()

    def _on_download_atlas_confirmed(self):
        """Downloads the currently selected atlas and signals this."""
        atlas_name = self.selected_atlas_name()
        worker = self._apply_in_thread(install_atlas, atlas_name)
        worker.returned.connect(self.download_atlas_confirmed.emit)
        worker.start()

    def _on_update_atlas_confirmed(self):
        """Updates the currently selected atlas and signals this."""
        atlas_name = self.selected_atlas_name()
        worker = self._apply_in_thread(update_atlas, atlas_name)
        worker.returned.connect(self.update_atlas_confirmed.emit)
        worker.start()

    def selected_atlas_name(self) -> str:
        """A single place to get a valid selected atlas name."""
        selected_index = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        selected_atlas_name_index = selected_index.siblingAtColumn(0)
        selected_atlas_name = self.table.data(selected_atlas_name_index)
        return selected_atlas_name

    @thread_worker
    def _apply_in_thread(self, apply: Callable, atlas_name: str):
        """Calls `apply` on the given atlas in a separate thread."""
        apply(atlas_name)
        self.table.refresh_data()
        return atlas_name

    @classmethod
    def get_tooltip_text(cls, atlas_name: str):
        """Returns the atlas name as a formatted string,
        as well as instructions on how to interact with the atlas."""
        if atlas_name in get_downloaded_atlases():
            is_up_to_date = get_atlases_lastversions()[atlas_name]["updated"]
            if is_up_to_date:
                tooltip_text = f"{format_atlas_name(atlas_name)} is up-to-date"
            else:  # needs updating
                tooltip_text = (
                    f"{format_atlas_name(atlas_name)} (double-click to update)"
                )
        elif atlas_name in get_all_atlases_lastversions().keys():
            tooltip_text = (
                f"{format_atlas_name(atlas_name)} (double-click to download)"
            )
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text


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
        l = self.layout = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        q = self.query_field = QLineEdit(self)
        q.setPlaceholderText("Search...")
        q.textChanged.connect(self.apply)

        l.addWidget(QLabel("Query:"))
        l.addWidget(q)

        c = self.column_field = QComboBox()
        c.addItems(self.atlas_manager_view.table.column_headers)
        c.insertItem(0, "Any")
        for col in self.atlas_manager_view.hidden_columns:
            c.removeItem(c.findText(col))
        c.setCurrentIndex(0)
        c.currentIndexChanged.connect(self.apply)

        l.addWidget(QLabel("Column:"))
        l.addWidget(c)
        return

    def clear(self):
        self.atlas_manager_view.table.proxy.setFilterFixedString("")

    def closeEvent(self, event):
        """Cleans up the widget when it is closed."""
        self.query_field.textChanged.disconnect(self.apply)
        self.column_field.currentIndexChanged.disconnect(self.apply)
        self.clear()
        return

    def apply(self):
        """Apply filters."""
        query = self.query_field.text()
        column = self.column_field.currentText()

        if column == "Any":
            self.atlas_manager_view.proxy.setFilterKeyColumn(-1)
        else:
            column_index = self.atlas_manager_view.table.column_headers.index(
                column
            )
            self.atlas_manager_view.proxy.setFilterKeyColumn(column_index)

        self.atlas_manager_view.proxy.setFilterCaseSensitivity(
            Qt.CaseInsensitive
        )
        self.atlas_manager_view._apply_filters(query)
        return
