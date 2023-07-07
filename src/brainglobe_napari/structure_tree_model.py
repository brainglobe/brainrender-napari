from typing import List

from bg_atlasapi.structure_tree_util import get_structures_tree
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt


class StructureTreeItem:
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
    def __init__(self, data: List, parent=None):
        super().__init__()
        self.root_item = StructureTreeItem(data=("Atlas regions", "-1"))
        self.setupModelData(data, self.root_item)

    def setupModelData(self, regions: List, root: StructureTreeItem = None):
        tree = get_structures_tree(regions)
        region_id_dict = {}
        for region in regions:
            region_id_dict[region["id"]] = region

        inserted_items = {}
        for n_id in tree.expand_tree():  # sorts nodes by default,
            # so parents will always be already in the QAbstractItemModel
            # before their children
            node = tree.get_node(n_id)
            acronym = region_id_dict[node.identifier]["acronym"]
            if len(region_id_dict[node.identifier]["structure_id_path"]) == 1:
                parent_item = root
            else:
                parent_id = tree.parent(node.identifier).identifier
                parent_item = inserted_items[parent_id]

            item = StructureTreeItem(
                data=(acronym, node.identifier), parent=parent_item
            )
            parent_item.appendChild(item)
            inserted_items[node.identifier] = item

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        """Make read-only, but selectable"""
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def rowCount(self, parent: StructureTreeItem):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent: StructureTreeItem):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.root_item.columnCount()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root_item.data(section)

        return None

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent):
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
