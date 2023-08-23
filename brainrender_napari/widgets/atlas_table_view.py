"""The purpose of this file is to provide interactive model and view classes
for a table holding atlases. Users interacting with the table can request to
* download an atlas (double-click on row of a not-yet downloaded atlas)
* add annotation and reference images (double-click on row of local atlas)
* add additional references (right-click on a row and select from  menu)

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""
from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_downloaded_atlases,
)
from bg_atlasapi.update_atlases import install_atlas
from napari.qt import thread_worker
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from qtpy.QtWidgets import QMenu, QTableView, QWidget

from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
)
from brainrender_napari.widgets.atlas_download_dialog import (
    AtlasDownloadDialog,
)


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
                return "Latest version"
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)

    @classmethod
    def _get_tooltip_text(cls, atlas_name: str):
        """Returns the atlas metadata as a formatted string,
        as well as instructions on how to interact with the atlas."""
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
        """Initialises an atlas table view with latest atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
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
        """Returns a context menu with a list of additional references for the
        currently selected atlas if the atlas is downloaded and has any. If the
        user selects one of the additional references, this is signalled.
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
                    self.additional_reference_requested.emit(
                        selected_item.text()
                    )

    def _on_row_double_clicked(self):
        """Emits add_atlas_requested if the currently
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

    def _on_download_atlas_confirmed(self):
        """Downloads an atlas and signals that this has happened."""
        atlas_name = self.selected_atlas_name()
        worker = self._install_atlas_in_thread(atlas_name)
        worker.returned.connect(self.download_atlas_confirmed.emit)
        worker.start()

    @thread_worker
    def _install_atlas_in_thread(self, atlas_name: str):
        """Installs the currently selected atlas in a separate thread."""
        install_atlas(atlas_name)
        return atlas_name

    def _on_current_changed(self):
        """Emits a signal with the newly selected atlas name"""
        self.selected_atlas_changed.emit(self.selected_atlas_name())
