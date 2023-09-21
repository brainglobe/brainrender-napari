"""The purpose of this file is to provide interactive model and view classes
for a table holding atlases. Users interacting with the table can request to
* download an atlas (double-click on row of a not-yet downloaded atlas)
* add annotation and reference images (double-click on row of local atlas)
* add additional references (right-click on a row and select from  menu)

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""
from typing import Callable

from bg_atlasapi.list_atlases import (
    get_downloaded_atlases,
)
from bg_atlasapi.update_atlases import install_atlas, update_atlas
from napari.qt import thread_worker
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QTableView, QWidget

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
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

        self.setModel(AtlasTableModel())
        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.doubleClicked.connect(self._on_row_double_clicked)
        self.hideColumn(0)  # hide raw name

    def _on_row_double_clicked(self):
        atlas_name = self.selected_atlas_name()
        if atlas_name in get_downloaded_atlases():
            # check if update needed
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
        selected_atlas_name = self.model().data(selected_atlas_name_index)
        return selected_atlas_name

    @thread_worker
    def _apply_in_thread(self, apply: Callable, atlas_name: str):
        """Calls `apply` on the given atlas in a separate thread."""
        apply(atlas_name)
        self.model().refresh_data()
        return atlas_name
