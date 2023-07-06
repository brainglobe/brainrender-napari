"""
A napari widget to view atlases.

Atlases that are exposed by the Brainglobe atlas API are
shown in a table view using the Qt model/view framework
[Qt Model/View framework](https://doc.qt.io/qt-6/model-view-programming.html)

Users can download and add the atlas as layers to the viewer.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from bg_atlasapi import BrainGlobeAtlas
from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_downloaded_atlases,
)
from bg_atlasapi.update_atlases import install_atlas
from napari.utils.notifications import show_info
from napari.viewer import Viewer
from qtpy import QtCore
from qtpy.QtCore import QModelIndex, Qt
from qtpy.QtWidgets import (
    QAbstractItemView,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from superqt import QCollapsible

from brainglobe_napari.atlas_viewer_utils import read_atlas_metadata_from_file
from brainglobe_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)


class AtlasTableModel(QtCore.QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

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


class AtlasViewerWidget(QWidget):
    """Widget to hold a selectable table view of atlases
    and other widgets to visualise atlases in napari.

    Internal state depends on currently selected row in the table view.
    """

    def __init__(self, napari_viewer: Viewer):
        """Instantiates the atlas viewer widget
        and sets up signal slot connections"""
        super().__init__()

        self._viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # setup atlas view
        self.atlas_table_view = QTableView()
        atlases = get_all_atlases_lastversions()
        data = [[name, version] for name, version in atlases.items()]

        self._model = AtlasTableModel(data)
        self.atlas_table_view.setModel(self._model)
        self.atlas_table_view.setEnabled(True)
        self.atlas_table_view.verticalHeader().hide()

        # select a single, entire row at a time.
        self.atlas_table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.atlas_table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self._selected_atlas_row = None
        self._selected_atlas_name = None

        # set up download button
        self.download_selected_atlas = QPushButton()
        self.download_selected_atlas.setText("Download selected atlas")

        def _on_download_selected_atlas_clicked():
            """Downloads the atlas currently selected in the table view.

            Download only happens if it's not available locally.
            Show's an info message otherwise.
            """
            if self._selected_atlas_row is not None:
                if self._selected_atlas_name not in get_downloaded_atlases():
                    install_atlas(self._selected_atlas_name)
                    self.refresh_info_box()
                else:
                    show_info("Atlas already downloaded.")

        self.download_selected_atlas.clicked.connect(
            _on_download_selected_atlas_clicked
        )

        # set up add button
        self.add_to_viewer = QPushButton()
        self.add_to_viewer.setText("Add to viewer")

        def _on_add_to_viewer_clicked():
            """Adds annotations as labels layer to the viewer."""
            if self._selected_atlas_row is not None:
                if self._selected_atlas_name in get_downloaded_atlases():
                    selected_atlas = BrainGlobeAtlas(self._selected_atlas_name)
                    selected_atlas_representation = NapariAtlasRepresentation(
                        selected_atlas, self._viewer
                    )
                    selected_atlas_representation.add_to_viewer()
                else:
                    show_info("Please download this atlas first.")

        self.add_to_viewer.clicked.connect(_on_add_to_viewer_clicked)

        # set up atlas info display
        self.atlas_info = QTextEdit(self)
        self.atlas_info.setReadOnly(True)

        # implement logic to update state when selection changes.
        def _on_selection_changed():
            """Updates the internally stored info about selected row."""
            selected_index = (
                self.atlas_table_view.selectionModel().currentIndex()
            )
            if selected_index.isValid():
                self._selected_atlas_row = selected_index.row()
                self._selected_atlas_name = self._model.data(
                    self._model.index(self._selected_atlas_row, 0)
                )
                self.refresh_info_box()
            else:
                self.atlas_info.setText("")

        self.atlas_table_view.selectionModel().selectionChanged.connect(
            _on_selection_changed
        )

        # add sub-widgets to top-level widget
        self.layout().addWidget(self.atlas_table_view)
        self.layout().addWidget(self.download_selected_atlas)
        self.layout().addWidget(self.add_to_viewer)
        
        atlas_info_collapsible = QCollapsible("Atlas info")
        atlas_info_collapsible.addWidget(self.atlas_info)
        self.layout().addWidget(atlas_info_collapsible)

    def refresh_info_box(self):
        if self._selected_atlas_name in get_downloaded_atlases():
            metadata = read_atlas_metadata_from_file(self._selected_atlas_name)
            metadata_as_string = ""
            for key, value in metadata.items():
                metadata_as_string += f"{key}:\t{value}\n"

            self.atlas_info.setText(
                f"Currently selected atlas: \
                    {self._selected_atlas_name} \
                    (available locally) \
                    {metadata_as_string}\n"
            )
        else:
            self.atlas_info.setText(
                f"Currently selected atlas: \
                    {self._selected_atlas_name} \
                    (not downloaded yet)"
            )
