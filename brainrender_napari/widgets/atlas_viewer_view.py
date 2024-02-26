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
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QMenu, QTableView, QWidget

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
)


class AtlasViewerView(QTableView):
    add_atlas_requested = Signal(str)
    no_atlas_available = Signal()
    additional_reference_requested = Signal(str)
    selected_atlas_changed = Signal(str)

    def __init__(self, parent: QWidget = None):
        """Initialises a table view with locally available atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)

        self.setModel(AtlasTableModel(AtlasViewerView))

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

        for column_header in ["Raw name", "Local version", "Latest version"]:
            index_to_hide = self.model().column_headers.index(column_header)
            self.hideColumn(index_to_hide)

        if len(get_downloaded_atlases()) == 0:
            self.no_atlas_available.emit()

        # hide atlases not available locally
        for row_index in range(self.model().rowCount()):
            index = self.model().index(row_index, 0)
            if self.model().data(index) not in get_downloaded_atlases():
                self.hideRow(row_index)

    def selected_atlas_name(self) -> str:
        """A single place to get a valid selected atlas name."""
        selected_index = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        selected_atlas_name_index = selected_index.siblingAtColumn(0)
        selected_atlas_name = self.model().data(selected_atlas_name_index)
        assert selected_atlas_name in get_downloaded_atlases()
        return selected_atlas_name

    def _on_context_menu_requested(self, position: Tuple[float]) -> None:
        """Returns a context menu with a list of additional references for the
        currently selected atlas if the atlas has any. If the user selects one
        of the additional references, this is signalled.
        """
        selected_atlas_name = self.selected_atlas_name()
        metadata = read_atlas_metadata_from_file(selected_atlas_name)
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
        self.add_atlas_requested.emit(atlas_name)

    def _on_current_changed(self) -> None:
        """Emits a signal with the newly selected atlas name"""
        self.selected_atlas_changed.emit(self.selected_atlas_name())

    @classmethod
    def get_tooltip_text(cls, atlas_name: str):
        """Returns the atlas metadata as a formatted string,
        as well as instructions on how to interact with the atlas."""
        if atlas_name in get_downloaded_atlases():
            metadata = read_atlas_metadata_from_file(atlas_name)
            metadata_as_string = ""
            for key, value in metadata.items():
                metadata_as_string += f"{key}:\t{value}\n"
            tooltip_text = f"{format_atlas_name(atlas_name)}\
                (double-click to add to viewer)\
                \n{metadata_as_string}"
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text
