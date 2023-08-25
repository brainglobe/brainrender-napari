import pytest

from brainrender_napari.widgets.brain_region_view import BrainRegionView


@pytest.fixture
def brain_region_view(qtbot) -> BrainRegionView:
    return BrainRegionView()


@pytest.mark.parametrize(
    "column_clicked",
    [0, 1],  # we should be able to click on either column with the same result
)
def test_brain_region_view_valid_selection(brain_region_view, column_clicked):
    """Checks that the correct brain region name is returned
    if a valid brain region view index is selected."""
    brain_region_view.refresh("allen_mouse_100um")

    root_index = brain_region_view.rootIndex()
    root_mesh_index = brain_region_view.model().index(0, 0, root_index)
    vs_mesh_index = brain_region_view.model().index(
        0, column_clicked, root_mesh_index
    )
    assert vs_mesh_index.isValid()
    brain_region_view.setCurrentIndex(vs_mesh_index)
    assert brain_region_view.selected_brain_region_acronym() == "VS"


def test_brain_region_view_invalid_selection(brain_region_view):
    """Checks that selected_brain_region_name throws an assertion error
    if current index is invalid."""
    brain_region_view.refresh("allen_mouse_100um")
    with pytest.raises(AssertionError):
        brain_region_view.selected_brain_region_acronym()


@pytest.mark.parametrize(
    "atlas_name, expected_visibility",
    [
        ("allen_mouse_100um", True),  # is part of downloaded test data
        ("allen_human_500um", False),  #  is not part of download test data
    ],
)
def test_brain_region_view_visibility(
    atlas_name, expected_visibility, brain_region_view
):
    """Checks that the brain region view is visible
    iff atlas has previously been downloaded."""
    brain_region_view.refresh(atlas_name)
    assert brain_region_view.isVisible() == expected_visibility


@pytest.mark.parametrize("show_brain_region_names", [True, False])
def test_brain_region_view_column_visibility(
    brain_region_view, show_brain_region_names
):
    """Checks the column visibility for a visible brain region view"""
    brain_region_view.refresh("allen_mouse_100um", show_brain_region_names)
    assert not brain_region_view.isColumnHidden(0)  # acronym is always visible
    assert brain_region_view.isColumnHidden(2)  # id column is always hidden
    assert brain_region_view.isColumnHidden(1) != show_brain_region_names


@pytest.mark.parametrize(
    "column_clicked",
    [0, 1],  # we should be able to click on either column with the same result
)
def test_double_click_on_brain_region_row(
    brain_region_view, double_click_on_view, qtbot, column_clicked
):
    """Checks that expected signal is emitted when double-clicking on a row
    (independent of column) in the brain region view"""
    brain_region_view.refresh("allen_mouse_100um", True)

    root_index = brain_region_view.rootIndex()
    root_mesh_index = brain_region_view.model().index(0, 0, root_index)
    assert root_mesh_index.isValid()
    vs_mesh_index = brain_region_view.model().index(
        0, column_clicked, root_mesh_index
    )
    assert vs_mesh_index.isValid()
    brain_region_view.setCurrentIndex(vs_mesh_index)
    with qtbot.waitSignal(
        brain_region_view.add_brain_region_requested
    ) as add_brain_region_requested_signal:
        double_click_on_view(brain_region_view, vs_mesh_index)

    assert add_brain_region_requested_signal.args == ["VS"]
