import pytest

from brainrender_napari.widgets.structure_view import StructureView


@pytest.fixture
def structure_view(qtbot) -> StructureView:
    return StructureView()


@pytest.mark.parametrize(
    "column_clicked",
    [0, 1],  # we should be able to click on either column with the same result
)
def test_structure_view_valid_selection(structure_view, column_clicked):
    """Checks that the correct structure name is returned
    if a valid structure view index is selected."""
    structure_view.refresh("allen_mouse_100um")

    root_index = structure_view.rootIndex()
    root_mesh_index = structure_view.model().index(0, 0, root_index)
    vs_mesh_index = structure_view.model().index(
        0, column_clicked, root_mesh_index
    )
    assert vs_mesh_index.isValid()
    structure_view.setCurrentIndex(vs_mesh_index)
    assert structure_view.selected_structure_acronym() == "VS"


def test_structure_view_invalid_selection(structure_view):
    """Checks that selected_structure_name throws an assertion error
    if current index is invalid."""
    structure_view.refresh("allen_mouse_100um")
    with pytest.raises(AssertionError):
        structure_view.selected_structure_acronym()


@pytest.mark.parametrize(
    "atlas_name, expected_visibility",
    [
        ("allen_mouse_100um", True),  # is part of downloaded test data
        ("allen_human_500um", False),  #  is not part of download test data
    ],
)
def test_structure_view_visibility(
    atlas_name, expected_visibility, structure_view
):
    """Checks that the structure view is visible
    iff atlas has previously been downloaded."""
    structure_view.refresh(atlas_name)
    assert structure_view.isVisible() == expected_visibility


@pytest.mark.parametrize("show_structure_names", [True, False])
def test_structure_view_column_visibility(
    structure_view, show_structure_names
):
    """Checks the column visibility for a visible structure view"""
    structure_view.refresh("allen_mouse_100um", show_structure_names)
    assert not structure_view.isColumnHidden(0)  # acronym is always visible
    assert structure_view.isColumnHidden(2)  # id column is always hidden
    assert structure_view.isColumnHidden(1) != show_structure_names


@pytest.mark.parametrize(
    "column_clicked",
    [0, 1],  # we should be able to click on either column with the same result
)
def test_double_click_on_structure_row(
    structure_view, double_click_on_view, qtbot, column_clicked
):
    """Checks that expected signal is emitted when
    double-clicking on a row (indpendent of column) in the structure view"""
    structure_view.refresh("allen_mouse_100um", True)

    root_index = structure_view.rootIndex()
    root_mesh_index = structure_view.model().index(0, 0, root_index)
    assert root_mesh_index.isValid()
    vs_mesh_index = structure_view.model().index(
        0, column_clicked, root_mesh_index
    )
    assert vs_mesh_index.isValid()
    structure_view.setCurrentIndex(vs_mesh_index)
    with qtbot.waitSignal(
        structure_view.add_structure_requested
    ) as add_structure_requested_signal:
        double_click_on_view(structure_view, vs_mesh_index)

    assert add_structure_requested_signal.args == ["VS"]
