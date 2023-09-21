"""The purpose of this file is to provide interactive item,
model and view classes for the structures that form part of an atlas.
The view is only visible if the atlas is downloaded."""

from bg_atlasapi.list_atlases import get_downloaded_atlases
from qtpy.QtCore import QModelIndex, Signal
from qtpy.QtWidgets import QTreeView, QWidget

from brainrender_napari.data_models.structure_tree_model import (
    StructureTreeModel,
)
from brainrender_napari.utils.load_user_data import (
    read_atlas_structures_from_file,
)


class StructureView(QTreeView):
    add_structure_requested = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.doubleClicked.connect(self._on_row_double_clicked)

        def resize_acronym_column():
            self.resizeColumnToContents(0)

        self.expanded.connect(resize_acronym_column)

    def refresh(
        self, selected_atlas_name: str, show_structure_names: bool = False
    ):
        """Updates the structure tree view with the currently selected atlas.
        The view is only visible if the selected atlas has been downloaded.
        Resets the current index either way.
        """
        if selected_atlas_name in get_downloaded_atlases():
            structures = read_atlas_structures_from_file(selected_atlas_name)
            region_model = StructureTreeModel(structures)
            self.setModel(region_model)
            if show_structure_names:
                self.showColumn(1)
            else:
                self.hideColumn(1)
            self.hideColumn(2)  # don't show structure id
            self.setExpandsOnDoubleClick(False)
            self.setHeaderHidden(True)
            self.setWordWrap(False)
            self.expandToDepth(0)
            self.show()
        else:
            self.hide()
        self.setCurrentIndex(QModelIndex())

    def selected_structure_acronym(self) -> str:
        """A single place to get a valid selected structure"""
        selected_index = self.selectionModel().currentIndex()
        assert selected_index.isValid()
        acronym_index = selected_index.siblingAtColumn(0)
        selected_structure_acronym = self.model().data(acronym_index)
        return selected_structure_acronym

    def _on_row_double_clicked(self):
        self.add_structure_requested.emit(self.selected_structure_acronym())
