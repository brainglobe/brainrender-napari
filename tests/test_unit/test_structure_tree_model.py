import pytest
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt

from brainrender_napari.data_models.structure_tree_model import (
    StructureTreeItem,
    StructureTreeModel,
)

# Sample hierarchical structure data for testing
# Simplified structure based on Allen Mouse Brain Atlas
# root -> grey -> Cerebrum -> Cerebral cortex -> Isocortex
# root -> grey -> Hindbrain -> Medulla
SAMPLE_STRUCTURES = [
    {"id": 997, "acronym": "root", "name": "root", "structure_id_path": [997]},
    {
        "id": 8,
        "acronym": "grey",
        "name": "Basic cell groups and regions",
        "structure_id_path": [997, 8],
    },
    {
        "id": 56,
        "acronym": "CH",
        "name": "Cerebrum",
        "structure_id_path": [997, 8, 56],
    },
    {
        "id": 68,
        "acronym": "CTX",
        "name": "Cerebral cortex",
        "structure_id_path": [997, 8, 56, 68],
    },
    {
        "id": 315,
        "acronym": "Isocortex",
        "name": "Isocortex",
        "structure_id_path": [997, 8, 56, 68, 315],
    },
    {
        "id": 1009,
        "acronym": "HB",
        "name": "Hindbrain",
        "structure_id_path": [997, 8, 1009],
    },
    {
        "id": 1065,
        "acronym": "MY",
        "name": "Medulla",
        "structure_id_path": [997, 8, 1009, 1065],
    },
]


@pytest.fixture
def structure_tree_model() -> StructureTreeModel:
    """Fixture to create a StructureTreeModel with sample data."""
    return StructureTreeModel(data=SAMPLE_STRUCTURES)


def test_model_initialization(structure_tree_model):
    """Test if the model initializes correctly and builds the tree."""
    assert isinstance(structure_tree_model, QAbstractItemModel)
    assert structure_tree_model.root_item is not None
    # Check root item header data
    assert structure_tree_model.root_item.data(0) == "acronym"
    assert structure_tree_model.root_item.data(1) == "name"
    assert structure_tree_model.root_item.data(2) == "id"

    # Check the actual top-level item displayed in the model
    # The model's top-level item should correspond to the data's root node (ID 997)
    assert structure_tree_model.rowCount(QModelIndex()) == 1 # Only 'root' under the invisible model root
    first_level_index = structure_tree_model.index(0, 0, QModelIndex())
    assert first_level_index.isValid() # Good practice to check validity

    # Assert that the first top-level item's acronym is 'root'
    assert structure_tree_model.data(first_level_index, Qt.DisplayRole) == "root" # <-- Changed 'grey' to 'root'


def test_column_count(structure_tree_model):
    """Test the columnCount method."""
    # Root item should have 3 columns (acronym, name, id)
    assert structure_tree_model.columnCount(QModelIndex()) == 3

    # A valid child item index should also report 3 columns
    grey_index = structure_tree_model.index(0, 0, QModelIndex())
    assert structure_tree_model.columnCount(grey_index) == 3


@pytest.mark.parametrize(
    "row, col, parent_coords, expected_data",
    [
        # Data for 'CH' (child 0 of 'grey')
        (0, 0, (0, 0), "CH"),
        (0, 1, (0, 0), "Cerebrum"),
        (0, 2, (0, 0), 56),
        # Data for 'HB' (child 1 of 'grey')
        (1, 0, (0, 0), "HB"),
        (1, 1, (0, 0), "Hindbrain"),
        (1, 2, (0, 0), 1009),
        # Data for 'Isocortex' (child 0 of 'CTX', which is child 0 of 'CH'...)
        (0, 0, (0, 0, 0, 0), "Isocortex"),
        (0, 1, (0, 0, 0, 0), "Isocortex"),
        (0, 2, (0, 0, 0, 0), 315),
    ],
)
def test_data_retrieval(
    structure_tree_model, row, col, parent_coords, expected_data
):
    """Test retrieving data using the data() method for various items."""
    parent_index = QModelIndex()
    if parent_coords:
        # Navigate down the tree to get the correct parent index
        current_parent_index = QModelIndex()
        for parent_row in parent_coords:
            current_parent_index = structure_tree_model.index(
                parent_row, 0, current_parent_index
            )
            assert current_parent_index.isValid()  # Ensure navigation is valid
        parent_index = current_parent_index

    index = structure_tree_model.index(row, col, parent_index)
    assert index.isValid()
    assert structure_tree_model.data(index, Qt.DisplayRole) == expected_data

    # Test non-display role returns None
    assert structure_tree_model.data(index, Qt.ToolTipRole) is None

    # Test invalid index returns None
    invalid_index = QModelIndex()
    assert structure_tree_model.data(invalid_index, Qt.DisplayRole) is None


def test_parent_method(structure_tree_model):
    """Test the parent() method."""
    # Parent of root's child ('grey') should be invalid (root)
    grey_index = structure_tree_model.index(0, 0, QModelIndex())
    assert grey_index.isValid()
    root_parent = structure_tree_model.parent(grey_index)
    assert not root_parent.isValid()

    # Parent of 'CH' (child of 'grey') should be 'grey'
    ch_index = structure_tree_model.index(0, 0, grey_index)
    assert ch_index.isValid()
    grey_parent = structure_tree_model.parent(ch_index)
    assert grey_parent.isValid()
    assert grey_parent.internalPointer() == grey_index.internalPointer()
    assert grey_parent.row() == grey_index.row()
    assert grey_parent.column() == 0  # Parent index always has column 0

    # Parent of 'Isocortex' should be 'CTX'
    ctx_index = structure_tree_model.index(0, 0, ch_index)
    isocortex_index = structure_tree_model.index(0, 0, ctx_index)
    assert isocortex_index.isValid()
    ctx_parent = structure_tree_model.parent(isocortex_index)
    assert ctx_parent.isValid()
    assert ctx_parent.internalPointer() == ctx_index.internalPointer()
    assert ctx_parent.row() == ctx_index.row()

    # Parent of an invalid index should be invalid
    invalid_parent = structure_tree_model.parent(QModelIndex())
    assert not invalid_parent.isValid()


def test_index_method_invalid(structure_tree_model):
    """Test the index() method for invalid inputs."""
    # Invalid row (relative to invisible root)
    assert not structure_tree_model.index(
        99, 0, QModelIndex()
    ).isValid(), "Should return invalid index for out-of-bounds row"

    # Invalid column (relative to invisible root)
    assert not structure_tree_model.index(
        0, 99, QModelIndex()
    ).isValid(), "Should return invalid index for out-of-bounds column"

    # Create an index that should be invalid due to row/column bounds
    invalid_index_created = structure_tree_model.index(99, 99, QModelIndex())
    # Assert that the created index is indeed invalid
    assert not invalid_index_created.isValid(), "Index created with invalid row/col should be invalid"

    # Optional: Test invalid row/column relative to a *valid* item deeper in the tree
    root_data_index = structure_tree_model.index(0, 0, QModelIndex())
    assert root_data_index.isValid() # Ensure we have a valid parent first

    # Invalid row relative to the 'root' data node
    assert not structure_tree_model.index(
        99, 0, root_data_index
    ).isValid(), "Should return invalid index for out-of-bounds row relative to valid parent"

    # Invalid column relative to the 'root' data node
    assert not structure_tree_model.index(
        0, 99, root_data_index
    ).isValid(), "Should return invalid index for out-of-bounds column relative to valid parent"

# --- Tests for StructureTreeItem (though mostly tested via the model) ---


def test_structure_tree_item():
    """Basic tests for StructureTreeItem."""
    parent_data = ("p_acr", "p_name", 1)
    child_data = ("c_acr", "c_name", 2)
    parent_item = StructureTreeItem(data=parent_data)
    child_item = StructureTreeItem(data=child_data, parent=parent_item)
    parent_item.appendChild(child_item)

    assert parent_item.childCount() == 1
    assert parent_item.columnCount() == 3
    assert parent_item.data(0) == "p_acr"
    assert parent_item.data(1) == "p_name"
    assert parent_item.data(2) == 1
    assert parent_item.data(3) is None  # Index out of bounds
    assert parent_item.parent() is None
    assert parent_item.row() == 0  # Root item row is 0

    assert child_item.childCount() == 0
    assert child_item.columnCount() == 3
    assert child_item.data(0) == "c_acr"
    assert child_item.parent() == parent_item
    assert child_item.row() == 0  # First child of parent_item
