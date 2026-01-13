"""
A napari widget to download and visualize atlas-registered datasets.

This widget allows users to browse, download, and visualize publicly available
atlas-registered datasets such as cell positions, gene expression data, etc.
"""

from typing import Dict

from brainglobe_utils.qtpy.logo import header_widget
from napari.qt import thread_worker
from napari.utils.notifications import show_error
from napari.viewer import Viewer
from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.utils.download_datasets import (
    download_dataset,
    get_available_datasets,
    register_dynamic_dataset,
)
from brainrender_napari.utils.visualize_datasets import add_dataset_to_viewer
from brainrender_napari.widgets.atlas_progress_bar import AtlasProgressBar
from brainrender_napari.widgets.database_search_widget import (
    DatabaseSearchWidget,
)
from brainrender_napari.widgets.dataset_manager_view import DatasetManagerView


class BrainrenderDatasetWidget(QWidget):
    """
    Main widget for downloading and visualizing atlas-registered datasets.

    This widget coordinates between:
    * Dataset browser/viewer (table of available datasets)
    * Progress tracking (download progress)
    * Visualization (adding datasets to napari viewer)
    """

    def __init__(self, napari_viewer: Viewer) -> None:
        """Initialize the dataset widget."""
        super().__init__()

        self._viewer: Viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # Add header
        self.layout().addWidget(
            header_widget(
                "brainrender",
                "Atlas-registered datasets",
                tutorial_file_name=None,
                citation_doi="https://doi.org/10.21105/joss.02668",
                github_repo_name="brainrender-napari",
                help_text="Search databases and download atlas-registered datasets.",
            )
        )

        # Create database search widget
        self.database_search_widget = DatabaseSearchWidget(parent=self)
        self.layout().addWidget(self.database_search_widget)

        # Create dataset manager group for downloaded datasets
        self.dataset_manager_group = QGroupBox("Downloaded Datasets")
        self.dataset_manager_group.setToolTip(
            "List of downloaded datasets.\n"
            "Double-click on a row to download a dataset.\n"
            "Right-click on a downloaded dataset to visualize it."
        )
        self.dataset_manager_group.setLayout(QVBoxLayout())

        # Create filter controls
        filter_group = QGroupBox("Filters")
        filter_group.setLayout(QHBoxLayout())

        # Species filter
        species_label = QLabel("Species:")
        self.species_filter = QComboBox()
        self.species_filter.addItem("All")
        self.species_filter.addItems(["mouse", "zebrafish", "human"])
        self.species_filter.currentTextChanged.connect(self._on_filter_changed)

        # Data type filter
        data_type_label = QLabel("Data Type:")
        self.data_type_filter = QComboBox()
        self.data_type_filter.addItem("All")
        self.data_type_filter.addItems(["points", "volume", "streamlines"])
        self.data_type_filter.currentTextChanged.connect(
            self._on_filter_changed
        )

        filter_group.layout().addWidget(species_label)
        filter_group.layout().addWidget(self.species_filter)
        filter_group.layout().addWidget(data_type_label)
        filter_group.layout().addWidget(self.data_type_filter)
        filter_group.layout().addStretch()

        self.dataset_manager_group.layout().addWidget(filter_group)

        # Create the dataset manager view
        self.dataset_manager_view = DatasetManagerView(parent=self)
        self.dataset_manager_group.layout().addWidget(
            self.dataset_manager_view
        )

        self.layout().addWidget(self.dataset_manager_group)

        # Create progress bar
        self.progress_bar = AtlasProgressBar(parent=self)
        self.layout().addWidget(self.progress_bar)

        # Connect signals from dataset manager view
        self.dataset_manager_view.progress_updated.connect(
            self.progress_bar.update_progress
        )
        self.dataset_manager_view.download_dataset_confirmed.connect(
            self._on_dataset_downloaded
        )
        self.dataset_manager_view.visualize_dataset_requested.connect(
            self._on_visualize_dataset
        )

        # Connect signals from database search widget
        self.database_search_widget.neuron_selected.connect(
            self._on_neuron_selected_from_search
        )
        self.database_search_widget.search_results_updated.connect(
            self._on_search_results_updated
        )

    def _on_filter_changed(self) -> None:
        """Update the dataset table when filters change."""
        species_filter = (
            self.species_filter.currentText()
            if self.species_filter.currentText() != "All"
            else None
        )
        data_type_filter = (
            self.data_type_filter.currentText()
            if self.data_type_filter.currentText() != "All"
            else None
        )

        # Apply filters to the model
        self.dataset_manager_view.source_model.set_filters(
            species=species_filter, data_type=data_type_filter
        )

    def _on_dataset_downloaded(self, dataset_id: str) -> None:
        """Handle successful dataset download."""
        self.progress_bar.operation_completed()
        # Dataset table will auto-refresh via the model

    def _on_neuron_selected_from_search(self, neuron: Dict) -> None:
        """Handle neuron selection from database search - trigger download."""
        try:
            # Register the neuron as a dataset
            dataset_id = register_dynamic_dataset(neuron)

            # Trigger download using thread worker
            @thread_worker
            def download_worker():
                def progress_callback(current, total):
                    self.dataset_manager_view.progress_updated.emit(
                        current, total, dataset_id, "Downloading"
                    )

                return download_dataset(
                    dataset_id, progress_callback=progress_callback
                )

            worker = download_worker()
            worker.returned.connect(
                lambda result: self._on_neuron_download_complete(
                    dataset_id, neuron
                )
            )
            worker.errored.connect(
                lambda error: show_error(
                    f"Failed to download neuron: {str(error)}"
                )
            )
            worker.start()

        except Exception as e:
            show_error(f"Failed to download selected neuron: {str(e)}")

    def _on_neuron_download_complete(
        self, dataset_id: str, neuron: Dict
    ) -> None:
        """Handle completion of neuron download."""
        # Don't show notification here - it will be shown by _on_download_complete in dataset_manager_view
        # Just refresh and update progress bar
        self.dataset_manager_view.source_model.refresh_data()
        self.progress_bar.operation_completed()

    def _on_search_results_updated(self, results: list) -> None:
        """Handle search results update - refresh the dataset table."""
        self.dataset_manager_view.source_model.refresh_data()

    def _on_visualize_dataset(self, dataset_id: str) -> None:
        """Handle request to visualize a dataset."""
        try:
            # Get the atlas name from dataset metadata
            available_datasets = get_available_datasets()
            if dataset_id not in available_datasets:
                return

            atlas_name = available_datasets[dataset_id].get("atlas")
            if not atlas_name:
                show_error(
                    f"Dataset '{dataset_id}' does not specify a required atlas."
                )
                return

            # Add dataset to viewer
            add_dataset_to_viewer(
                dataset_id=dataset_id,
                viewer=self._viewer,
                atlas_name=atlas_name,
            )
        except Exception as e:
            show_error(f"Failed to visualize dataset: {str(e)}")
