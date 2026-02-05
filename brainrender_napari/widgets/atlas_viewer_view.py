"""The purpose of this file is to provide an interactive table view
to request adding of atlas images. Users interacting it can request to
* add annotation and reference images (double-click on row of local atlas)
* add additional references (right-click on a row and select from  menu)

It is designed to be agnostic from the viewer framework by emitting signals
that interested observers can connect to.
"""

from typing import Tuple

from brainglobe_atlasapi.list_atlases import (
    get_downloaded_atlases,
)
from qtpy.QtCore import QModelIndex, Qt, Signal, QSortFilterProxyModel
from qtpy.QtWidgets import QMenu, QTableView, QWidget

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
)


class DownloadedOnlyProxyModel(QSortFilterProxyModel):
    """
    A Custom Proxy Model that filters out any atlas not currently downloaded.
    This replaces the need for manually hiding rows, which breaks when sorting.
    """
    def filterAcceptsRow(self, source_row, source_parent):
        # 1. Check if it matches the Search Bar text (Standard behavior)
        matches_search = super().filterAcceptsRow(source_row, source_parent)
        if not matches_search:
            return False

        # 2. Check if it is Downloaded (Custom Rule)
        source_model = self.sourceModel()
        # Atlas Name is in Column 0
        index = source_model.index(source_row, 0, source_parent)
        atlas_name = source_model.data(index)

        return atlas_name in get_downloaded_atlases()


class AtlasViewerView(QTableView):
    add_atlas_requested = Signal(str)
    no_atlas_available = Signal()
    additional_reference_requested = Signal(str)
    selected_atlas_changed = Signal(str)

    def __init__(self, parent: QWidget = None) -> None:
        """Initialises a table view with locally available atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)

        # 1. Setup Source Model
        self.source_model = AtlasTableModel(AtlasViewerView)

        # 2. Setup Custom Proxy Model (Filters non-downloaded & Sorts)
        self.proxy_model = DownloadedOnlyProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # 3. Apply Proxy Model to View
        self.setModel(self.proxy_model)

        # 4. Enable Sorting
        self.setSortingEnabled(True)

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
        self.selectionModel().currentChanged.connect(self._on_current_changed)

        # Define columns to hide (and store in attribute for Filter widget)
        self.hidden_columns = ["Raw name", "Local version", "Latest version"]

        for column_header in self.hidden_columns:
            if column_header in self.source_model.column_headers:
                index_to_hide = self.source_model.column_headers.index(column_header)
                self.hideColumn(index_to_hide)

        if len(get_downloaded_atlases()) == 0:
            self.no_atlas_available.emit()

        # Note: We no longer need the loop to hideRow() here.
        # The DownloadedOnlyProxyModel handles it automatically.

    def selected_atlas_name(self) -> str:
        """A single place to get a valid selected atlas name.
        Updated to handle Proxy mapping."""
        # Get the index from the View (Sorted/Filtered Index)
        selected_proxy_index: QModelIndex = self.selectionModel().currentIndex()
        
        if not selected_proxy_index.isValid():
            return None

        # Map Proxy Index -> Source Index
        selected_source_index = self.proxy_model.mapToSource(selected_proxy_index)
        
        # Get data from Source Model
        selected_atlas_name_index = selected_source_index.siblingAtColumn(0)
        selected_atlas_name = self.source_model.data(selected_atlas_name_index)
        
        assert selected_atlas_name in get_downloaded_atlases()
        return selected_atlas_name

    def _on_context_menu_requested(self, position: Tuple[float]) -> None:
        """Returns a context menu with a list of additional references for the
        currently selected atlas if the atlas has any. If the user selects one
        of the additional references, this is signalled.
        """
        selected_atlas_name: str = self.selected_atlas_name()
        # Guard clause in case selection is empty
        if not selected_atlas_name:
            return

        metadata = read_atlas_metadata_from_file(
            atlas_name=selected_atlas_name
        )
        if (
            "additional_references" in metadata.keys()
            and metadata["additional_references"]
        ):
            global_position = self.viewport().mapToGlobal(position)
            additional_reference_menu = QMenu()

            for additional_reference in metadata["additional_references"]:
                additional_reference_menu.addAction(additional_reference)

            selected_item = additional_reference_menu.exec(global_position)
            if selected_item:
                self.additional_reference_requested.emit(selected_item.text())

    def _on_row_double_clicked(self) -> None:
        """Emits add_atlas_requested if the currently
        selected atlas is available locally."""
        atlas_name = self.selected_atlas_name()
        if atlas_name:
            self.add_atlas_requested.emit(atlas_name)

    def _on_current_changed(self) -> None:
        """Emits a signal with the newly selected atlas name"""
        name = self.selected_atlas_name()
        if name:
            self.selected_atlas_changed.emit(name)

    @classmethod
    def get_tooltip_text(cls, atlas_name: str) -> str:
        """Returns the atlas metadata as a formatted string,
        as well as instructions on how to interact with the atlas."""
        if atlas_name in get_downloaded_atlases():
            metadata = read_atlas_metadata_from_file(atlas_name=atlas_name)
            metadata_as_string = ""
            for key, value in metadata.items():
                metadata_as_string += f"{key}:\t{value}\n"
            tooltip_text: str = (
                f"{format_atlas_name(name=atlas_name)}"
                f" (double-click to add to viewer)"
                f"\n{metadata_as_string}"
            )
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text