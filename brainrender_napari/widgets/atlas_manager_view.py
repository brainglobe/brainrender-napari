"""The purpose of this file is to provide interactive table view to download
and update atlases. Users interacting with the table can request to
* download an atlas (double-click on row of a not-yet downloaded atlas)
* update an atlas (double-click on row of outdated local atlas)
They can also hover over an up-to-date local atlas and see that
it's up to date.

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""

from typing import Callable, Optional

from brainglobe_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_downloaded_atlases,
)
from brainglobe_atlasapi.update_atlases import install_atlas, update_atlas
from napari.qt import thread_worker
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QProgressBar,
    QTableView,
    QWidget,
)

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_dialog import AtlasManagerDialog


def _format_bytes(num_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"


def install_atlas_with_progress(atlas_name: str, fn_update: Callable):
    """
    By passing fn_update when instantiating BrainGlobeAtlas
    Progress information during the downlaod progress is
    retrieved so that the actual progress (%) can be updated
    """
    install_atlas(atlas_name, fn_update=fn_update)
    return atlas_name


def update_atlas_with_progress(atlas_name: str, fn_update: Callable):
    """
    When updating an existing atlas, it should also be possible to pass
    fn_update to get the actual progress (%)
    """
    update_atlas(atlas_name, fn_update=fn_update)
    return atlas_name


class AtlasManagerView(QTableView):
    download_atlas_confirmed = Signal(str)
    update_atlas_confirmed = Signal(str)
    progress_updated = Signal(int, int, str, object)

    def __init__(self, parent: QWidget = None):
        """Initialises an atlas table view with latest atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)

        self._progress_bar: Optional[QProgressBar] = None

        self.setModel(AtlasTableModel(AtlasManagerView))
        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.doubleClicked.connect(self._on_row_double_clicked)
        self.hideColumn(
            self.model().column_headers.index("Raw name")
        )  # hide raw name
        self.progress_updated.connect(self._update_progress_bar_from_signal)

    def set_progress_bar(self, progress_bar: QProgressBar):
        """
        Assign a QProgressBar from the parent widget.
        This bar will be used to show download/update progress
        """
        self._progress_bar = progress_bar
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setStyleSheet(
            "QProgressBar { text-align: center; }"
        )

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

    def _start_worker(
        self, operation: Callable, atlas_name: str, signal: Signal
    ):
        """
        Helper function that combines progress bar generation,
        update processing, worker activation, and signal issuance.
        Displays a QProgressBar in the plugin widget.
        """
        if not self._progress_bar:
            # If there's no progress bar set, just run the operation
            worker = self._apply_in_thread(
                operation, atlas_name, lambda c, t: None
            )
            worker.returned.connect(lambda result: signal.emit(result))
            worker.start()
            return

        # Reset and show the progress bar
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        operation_name = (
            "Downloading"
            if operation == install_atlas_with_progress
            else "Updating"
        )
        self._progress_bar.setFormat(
            f"{operation_name} {atlas_name}... 0.00 B / 0.00 B (%p%)"
        )

        self._progress_bar.show()

        def update_fn(completed, total):
            self.progress_updated.emit(completed, total, atlas_name, operation)

        worker = self._apply_in_thread(operation, atlas_name, update_fn)
        worker.returned.connect(
            lambda result: (
                self._progress_bar.setValue(self._progress_bar.maximum()),
                self._progress_bar.hide(),
                signal.emit(result),
            )
        )
        worker.start()

    def _update_progress_bar_from_signal(
        self, completed: int, total: int, atlas_name: str, operation: Callable
    ):
        assert self._progress_bar is not None, "Progress bar is not set"
        percentage = min(
            int((completed / total) * 100) if total > 0 else 0, 100
        )
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(percentage)
        operation_type = (
            "Downloading"
            if operation == install_atlas_with_progress
            else "Updating"
        )
        self._progress_bar.setFormat(
            f"{operation_type} {atlas_name}... "
            f"{_format_bytes(completed)} / {_format_bytes(total)} "
            f"({percentage}%)"
        )

    def _on_download_atlas_confirmed(self):
        """Downloads the currently selected atlas and signals this."""
        atlas_name = self.selected_atlas_name()
        self._start_worker(
            install_atlas_with_progress,
            atlas_name,
            self.download_atlas_confirmed,
        )

    def _on_update_atlas_confirmed(self):
        """Updates the currently selected atlas and signals this."""
        atlas_name = self.selected_atlas_name()
        self._start_worker(
            update_atlas_with_progress, atlas_name, self.update_atlas_confirmed
        )

    def selected_atlas_name(self) -> str:
        """A single place to get a valid selected atlas name."""
        selected_index = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        selected_atlas_name_index = selected_index.siblingAtColumn(0)
        selected_atlas_name = self.model().data(selected_atlas_name_index)
        return selected_atlas_name

    @thread_worker
    def _apply_in_thread(self, apply: Callable, *args, **kwargs):
        """Helper function that executes the specified function
        in a background threaseparate thread."""
        return apply(*args, **kwargs)

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
