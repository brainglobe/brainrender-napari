import pytest

from brainrender_napari.widgets.structure_view import StructureView


@pytest.fixture
def structure_view(qtbot) -> StructureView:
    return StructureView()


def test_structure_view_valid_selection(structure_view):
    """Checks that the correct structure name is returned if a valid structure view index is selected."""
    structure_view.refresh("allen_mouse_100um")

    root_index = structure_view.rootIndex()
    root_mesh_index = structure_view.model().index(0, 0, root_index)
    vs_mesh_index = structure_view.model().index(0, 0, root_mesh_index)
    assert vs_mesh_index.isValid()
    structure_view.setCurrentIndex(vs_mesh_index)
    assert structure_view.selected_structure_name() == "VS"


def test_structure_view_invalid_selection(structure_view):
    """Checks that selected_structure_name throws an assertion error if current index is invalid."""
    structure_view.refresh("allen_mouse_100um")
    with pytest.raises(AssertionError):
        structure_view.selected_structure_name()


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
    """Checks that the structure view is visible iff atlas has previously been downloaded."""
    structure_view.refresh(atlas_name)
    assert structure_view.isVisible() == expected_visibility


def test_double_click_on_structure_row(
    structure_view, double_click_on_view, qtbot
):
    """Checks that expected signal is emitted when double-clicking on a row in the structure view"""
    structure_view.refresh("allen_mouse_100um")

    root_index = structure_view.rootIndex()
    root_mesh_index = structure_view.model().index(0, 0, root_index)
    vs_mesh_index = structure_view.model().index(0, 0, root_mesh_index)
    assert vs_mesh_index.isValid()
    structure_view.setCurrentIndex(vs_mesh_index)
    with qtbot.waitSignal(
        structure_view.add_structure_requested
    ) as add_structure_requested_signal:
        double_click_on_view(structure_view, vs_mesh_index)

    assert add_structure_requested_signal.args == ["VS"]
