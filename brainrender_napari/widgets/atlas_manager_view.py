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
from qtpy.QtCore import QModelIndex, QSortFilterProxyModel, Qt, Signal
from qtpy.QtWidgets import (
    QTableView,
    QWidget,
)

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_dialog import AtlasManagerDialog


class AtlasManagerView(QTableView):
    download_atlas_confirmed = Signal(str)
    update_atlas_confirmed = Signal(str)
    progress_updated = Signal(
        int, int, str, object
    )  # completed, total, atlas_name, operation_type

    def __init__(self, parent: QWidget = None) -> None:
        """Initialises an atlas table view with latest atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)

        self.source_model = AtlasTableModel(AtlasManagerView)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.setModel(self.proxy_model)

        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.doubleClicked.connect(self._on_row_double_clicked)
        self.hidden_columns = ["Raw name"]  # hide raw name
        for col in self.hidden_columns:
            self.hideColumn(self.source_model.column_headers.index(col))

    def _on_row_double_clicked(self) -> None:
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
            download_dialog = AtlasManagerDialog(
                atlas_name=atlas_name, action="Download"
            )
            download_dialog.ok_button.clicked.connect(
                self._on_download_atlas_confirmed
            )
            download_dialog.exec()

    def _on_download_atlas_confirmed(self) -> None:
        """Downloads the currently selected atlas and signals this."""
        atlas_name: str = self.selected_atlas_name()

        worker = self._apply_in_thread(
            install_atlas,
            atlas_name,
            fn_update=lambda completed, total: self.progress_updated.emit(
                completed, total, atlas_name, "Downloading"
            ),
        )
        worker.returned.connect(
            lambda result: [
                self.download_atlas_confirmed.emit(result),
                self.source_model.refresh_data(),
            ]
        )
        worker.start()

    def _on_update_atlas_confirmed(self) -> None:
        """Updates the currently selected atlas and signals this."""
        atlas_name = self.selected_atlas_name()

        worker = self._apply_in_thread(
            update_atlas,
            atlas_name,
            fn_update=lambda completed, total: self.progress_updated.emit(
                completed, total, atlas_name, "Updating"
            ),
        )
        worker.returned.connect(
            lambda result: [
                self.update_atlas_confirmed.emit(result),
                self.source_model.refresh_data(),
            ]
        )
        worker.start()

    def selected_atlas_name(self) -> str:
        """A single place to get a valid selected atlas name."""
        selected_index: QModelIndex = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        selected_atlas_name_index: QModelIndex = (
            selected_index.siblingAtColumn(0)
        )
        selected_atlas_name = self.proxy_model.data(selected_atlas_name_index)
        return selected_atlas_name

    @thread_worker
    def _apply_in_thread(self, apply: Callable, *args, **kwargs):
        """Helper function that executes the specified function
        in a separate thread."""
        return apply(*args, **kwargs)

    @classmethod
    def get_tooltip_text(cls, atlas_name: str) -> str:
        """Returns the atlas name as a formatted string,
        as well as instructions on how to interact with the atlas."""
        if atlas_name in get_downloaded_atlases():
            is_up_to_date = get_atlases_lastversions()[atlas_name]["updated"]
            if is_up_to_date:
                tooltip_text: str = (
                    f"{format_atlas_name(atlas_name)} is up-to-date"
                )
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
