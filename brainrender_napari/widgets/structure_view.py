"""The purpose of this file is to provide interactive item,
model and view classes for the structures that form part of an atlas.
The view is only visible if the atlas is downloaded."""

from typing import Dict, List

from brainglobe_atlasapi.list_atlases import get_downloaded_atlases
from brainglobe_atlasapi.structure_tree_util import get_structures_tree
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import QTreeView, QWidget

from brainrender_napari.utils.load_user_data import (
    read_atlas_structures_from_file,
)


class StructureTreeItem(QStandardItem):
    """A class to hold items in a tree model."""

    def __init__(self, data, parent=None):
        self.parent_item = parent
        self.item_data = data
        self.child_items = []

    def appendChild(self, item):
        self.child_items.append(item)

    def child(self, row):
        return self.child_items[row]

    def childCount(self):
        return len(self.child_items)

    def columnCount(self):
        return len(self.item_data)

    def data(self, column):
        try:
            return self.item_data[column]
        except IndexError:
            return None

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0


class StructureTreeModel(QAbstractItemModel):
    """Implementation of a read-only QAbstractItemModel to hold
    the structure tree information provided by the Atlas API in a Qt Model"""

    def __init__(self, data: List, parent=None):
        super().__init__()
        self.root_item = StructureTreeItem(data=("acronym", "name", "id"))
        self.build_structure_tree(data, self.root_item)

    def build_structure_tree(self, structures: List, root: StructureTreeItem):
        """Build the structure tree given a list of structures."""
        tree = get_structures_tree(structures)
        structure_id_dict = {}
        for structure in structures:
            structure_id_dict[structure["id"]] = structure

        inserted_items: Dict[int, StructureTreeItem] = {}
        for n_id in tree.expand_tree():  # sorts nodes by default,
            # so parents will always be already in the QAbstractItemModel
            # before their children
            node = tree.get_node(n_id)
            acronym = structure_id_dict[node.identifier]["acronym"]
            name = structure_id_dict[node.identifier]["name"]
            if (
                len(structure_id_dict[node.identifier]["structure_id_path"])
                == 1
            ):
                parent_item = root
            else:
                parent_id = tree.parent(node.identifier).identifier
                parent_item = inserted_items[parent_id]

            item = StructureTreeItem(
                data=(acronym, name, node.identifier), parent=parent_item
            )
            parent_item.appendChild(item)
            inserted_items[node.identifier] = item

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """Provides read-only data for a given index if
        intended for display, otherwise None."""
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def rowCount(self, parent: StructureTreeItem):
        """Returns the number of rows(i.e. children) of an item"""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent: StructureTreeItem):
        """The number of columns of an item."""
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.root_item.columnCount()

    def parent(self, index: QModelIndex):
        """The first-column index of parent of the item
        at a given index. Returns an empty index if the root,
        or an invalid index, is passed.
        """
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent=QModelIndex()):
        """The index of the item at (row, column) with a given parent.
        By default, the given parent is assumed to be the root."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()


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
