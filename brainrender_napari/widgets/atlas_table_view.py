from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_downloaded_atlases,
)
from bg_atlasapi.update_atlases import install_atlas
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from qtpy.QtWidgets import QMenu, QTableView, QWidget

from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
)
from brainrender_napari.widgets.atlas_download_dialog import (
    AtlasDownloadDialog,
)

"""The purpose of this file is to provide interactive model and view classes for a table holding atlases.
Users interacting with the table can request to
* download an atlas (by double-clicking on a row containing a non-yet downloaded atlas)
* add annotation and reference images (by double-clicking on a row of a locally available atlas)
* add additional reference images (by right-clicking on a row and selecting from a context menu)

It is designed to be agnostic from the viewer framework by emitting signals that any interested observers can connect to.
"""


class AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.ToolTipRole:
            hovered_atlas_name = self._data[index.row()][0]
            return AtlasTableModel._get_tooltip_text(hovered_atlas_name)

    def rowCount(self, index: QModelIndex):
        return len(self._data)

    def columnCount(self, index: QModelIndex):
        return len(self._data[0])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Customises the horizontal header data of model,
        and raises an error if an unexpected column is found."""
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section == 0:
                return "Atlas name"
            elif section == 1:
                return "Latest Version"
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)

    @classmethod
    def _get_tooltip_text(cls, atlas_name: str):
        if atlas_name in get_downloaded_atlases():
            metadata = read_atlas_metadata_from_file(atlas_name)
            metadata_as_string = ""
            for key, value in metadata.items():
                metadata_as_string += f"{key}:\t{value}\n"

            tooltip_text = f"{atlas_name} (double-click to add to viewer)\
            \n{metadata_as_string}"
        elif atlas_name in get_all_atlases_lastversions().keys():
            tooltip_text = f"{atlas_name} (double-click to download)"
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text


class AtlasTableView(QTableView):
    add_atlas_requested = Signal(str)
    download_atlas_confirmed = Signal(str)
    additional_reference_requested = Signal(str)
    selected_atlas_changed = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        atlases = get_all_atlases_lastversions()
        data = [[name, version] for name, version in atlases.items()]

        self.setModel(AtlasTableModel(data))
        self.setEnabled(True)
        self.verticalHeader().hide()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )

        self.doubleClicked.connect(self._on_row_double_clicked)

        self.selectionModel().currentChanged.connect(self._on_current_changed)

    def selected_atlas_name(self):
        """A single place to get a valid selected atlas name."""
        selected_index = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        selected_atlas_name_index = selected_index.siblingAtColumn(0)
        selected_atlas_name = self.model().data(selected_atlas_name_index)
        return selected_atlas_name

    def _on_context_menu_requested(self, position):
        """Returns a context menu with a list of additional references for the currently selected atlas
        if the atlas is downloaded and there are any.
        If the user selects one of the additional references, this is signalled.
        """
        selected_atlas_name = self.selected_atlas_name()
        if selected_atlas_name in get_downloaded_atlases():
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
                    self.additional_reference_requested(selected_item.text())

    def _on_row_double_clicked(self):
        """Adds annotation and reference to the viewer if the currently
        selected atlas is available locally. Asks the user to confirm
        they'd like to download the atlas otherwise."""
        atlas_name = self.selected_atlas_name()
        if atlas_name in get_downloaded_atlases():
            self.add_atlas_requested.emit(atlas_name)
        else:
            download_dialog = AtlasDownloadDialog(atlas_name)
            download_dialog.ok_button.clicked.connect(
                self._on_download_atlas_confirmed
            )
            download_dialog.exec()

    def _on_download_atlas_confirmed(self, atlas_name: str):
        """Downloads an atlas and signals that this has happened."""
        install_atlas(atlas_name)
        self.download_atlas_confirmed.emit(atlas_name)

    def _on_current_changed(self):
        self.selected_atlas_changed.emit(self.selected_atlas_name())
