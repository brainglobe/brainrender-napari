"""Interactive table view to download and visualize atlas-registered datasets.

Users interacting with the table can request to:
* download a dataset (double-click on row of a not-yet downloaded dataset)
* visualize a dataset (right-click on a downloaded dataset)

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""

from typing import Callable

from brainglobe_atlasapi.list_atlases import get_downloaded_atlases
from napari.qt import thread_worker
from napari.utils.notifications import show_error, show_info
from qtpy.QtCore import QModelIndex, QSortFilterProxyModel, Qt, QTimer, Signal
from qtpy.QtWidgets import QMenu, QTableView, QWidget

from brainrender_napari.data_models.dataset_table_model import DatasetTableModel
from brainrender_napari.utils.download_datasets import (
    download_dataset,
    get_available_datasets,
    get_downloaded_datasets,
)


class DatasetManagerView(QTableView):
    """Table view for managing atlas-registered datasets."""

    download_dataset_confirmed = Signal(str)
    visualize_dataset_requested = Signal(str)
    progress_updated = Signal(
        int, int, str, object
    )  # completed, total, dataset_id, operation_type

    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the dataset manager table view."""
        super().__init__(parent)

        self.source_model = DatasetTableModel(DatasetManagerView)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.setModel(self.proxy_model)

        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )

        self.doubleClicked.connect(self._on_row_double_clicked)

        # Hide Dataset ID column (internal use only)
        self.hideColumn(self.source_model.column_headers.index("Dataset ID"))
        
        # Set row height to show 4-5 rows at a time
        self.verticalHeader().setDefaultSectionSize(30)  # Reasonable row height
        self.setMinimumHeight(150)  # Minimum height to show ~5 rows
        self.setMaximumHeight(600)  # Maximum height to avoid taking too much space

    def _on_row_double_clicked(self) -> None:
        """Handle double-click on a row."""
        dataset_id = self.selected_dataset_id()
        status = self._get_dataset_status(dataset_id)

        if status == "Downloaded":
            show_info(
                f"Dataset '{self._get_dataset_name(dataset_id)}' is already downloaded. Right-click to visualize."
            )
        elif status == "Atlas Required":
            required_atlas = get_available_datasets()[dataset_id].get("atlas")
            show_error(
                f"Please download the required atlas '{required_atlas}' first before downloading this dataset."
            )
        else:
            # Available - trigger download
            self._on_download_dataset_confirmed()

    def _on_download_dataset_confirmed(self) -> None:
        """Downloads the currently selected dataset and signals this."""
        dataset_id: str = self.selected_dataset_id()

        # Check if atlas is available
        available_datasets = get_available_datasets()
        if dataset_id not in available_datasets:
            show_error(f"Dataset '{dataset_id}' is not available.")
            return

        metadata = available_datasets[dataset_id]
        required_atlas = metadata.get("atlas")
        if required_atlas and required_atlas not in get_downloaded_atlases():
            show_error(
                f"Please download the required atlas '{required_atlas}' first."
            )
            return

        worker = self._apply_in_thread(
            download_dataset,
            dataset_id,
            progress_callback=lambda completed, total: self.progress_updated.emit(
                completed, total, dataset_id, "Downloading"
            ),
        )
        worker.returned.connect(
            lambda result: self._on_download_complete(dataset_id)
        )
        worker.errored.connect(
            lambda error: show_error(
                f"Failed to download dataset: {str(error)}"
            )
        )
        worker.start()

    def _on_context_menu_requested(self, position) -> None:
        """Show context menu for right-click actions."""
        dataset_id = self.selected_dataset_id()
        status = self._get_dataset_status(dataset_id)

        global_position = self.viewport().mapToGlobal(position)
        context_menu = QMenu()

        if status == "Downloaded":
            visualize_action = context_menu.addAction("Visualize dataset")
            visualize_action.triggered.connect(
                lambda: self.visualize_dataset_requested.emit(dataset_id)
            )
            context_menu.addSeparator()

        if status != "Downloaded":
            download_action = context_menu.addAction("Download dataset")
            download_action.triggered.connect(
                self._on_download_dataset_confirmed
            )

        selected_action = context_menu.exec(global_position)

    def selected_dataset_id(self) -> str:
        """Get the dataset ID of the currently selected row."""
        selected_index: QModelIndex = self.selectionModel().currentIndex()
        if not selected_index.isValid():
            raise ValueError("No dataset selected")

        # Get dataset ID from first column (which is hidden)
        dataset_id_index: QModelIndex = (
            self.proxy_model.mapToSource(selected_index).siblingAtColumn(0)
        )
        dataset_id = self.source_model.data(dataset_id_index)
        return dataset_id

    def _get_dataset_status(self, dataset_id: str) -> str:
        """Get the status of a dataset."""
        row_count = self.source_model.rowCount()
        for row in range(row_count):
            dataset_id_index = self.source_model.index(row, 0)
            if self.source_model.data(dataset_id_index) == dataset_id:
                status_index = self.source_model.index(row, 6)  # Status column
                return self.source_model.data(status_index)
        return "Unknown"

    def _get_dataset_name(self, dataset_id: str) -> str:
        """Get the display name of a dataset."""
        available_datasets = get_available_datasets()
        if dataset_id in available_datasets:
            return available_datasets[dataset_id].get("name", dataset_id)
        return dataset_id

    def _on_download_complete(self, dataset_id: str):
        """Handle successful download completion."""
        # Small delay to ensure file system operations complete
        QTimer.singleShot(100, lambda: self._refresh_after_download(dataset_id))
    
    def _refresh_after_download(self, dataset_id: str):
        """Refresh the table after download completes."""
        # Refresh the model to update status
        self.source_model.refresh_data()
        # Resize columns to fit new data
        self.resizeColumnsToContents()
        # Emit signal for other components
        self.download_dataset_confirmed.emit(dataset_id)
        # Show notification (only once)
        show_info(
            f"Dataset '{self._get_dataset_name(dataset_id)}' downloaded successfully!"
        )

    @thread_worker
    def _apply_in_thread(self, apply: Callable, *args, **kwargs):
        """Helper function that executes the specified function in a separate thread."""
        try:
            return apply(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Download failed: {str(e)}") from e
