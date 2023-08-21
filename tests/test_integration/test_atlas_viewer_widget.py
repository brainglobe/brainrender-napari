"""These tests should just check that the subwidget signal and napari
are connected as expected. Lower level tests should happen in the tests
for the widget themselves."""

import pytest

from brainrender_napari.brainrender_widget import BrainrenderWidget


@pytest.fixture
def atlas_viewer(make_napari_viewer) -> BrainrenderWidget:
    """Fixture to expose the atlas viewer widget to tests.

    Simultaneously acts as a smoke test that the widget
    can be instantiated without crashing."""
    viewer = make_napari_viewer()
    return BrainrenderWidget(viewer)


def test_download_confirmed_refreshes_view(atlas_viewer, mocker):
    structure_view_refresh_mock = mocker.patch(
        "brainrender_napari.brainrender_widget.StructureView.refresh"
    )
    atlas_viewer.atlas_table_view.download_atlas_confirmed.emit(
        "allen_mouse_10um"
    )
    structure_view_refresh_mock.assert_called_once_with("allen_mouse_10um")


@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
        "osten_mouse_100um",
    ],
)
def test_double_click_on_locally_available_atlas_row(
    atlas_viewer, mocker, qtbot, expected_atlas_name
):
    """Check for a few local low-res atlases that double-clicking them
    on the atlas table view calls the expected atlas representation function.
    """
    add_atlas_to_viewer_mock = mocker.patch(
        "brainrender_napari.brainrender_widget"
        ".NapariAtlasRepresentation.add_to_viewer"
    )
    with qtbot.waitSignal(atlas_viewer.atlas_table_view.add_atlas_requested):
        atlas_viewer.atlas_table_view.add_atlas_requested.emit(
            expected_atlas_name
        )
    add_atlas_to_viewer_mock.assert_called_once()


def test_structure_row_double_clicked(atlas_viewer, mocker):
    """Checks that when the structure view widgets emit "VS" and
    the allen_mouse_100um atlas is selected, the NapariAtlasRepresentation
    function in the expected way.
    """
    add_structure_to_viewer_mock = mocker.patch(
        "brainrender_napari.brainrender_widget"
        ".NapariAtlasRepresentation.add_structure_to_viewer"
    )
    atlas_viewer.atlas_table_view.selectRow(4)  # allen_mouse_100um is in row 4

    atlas_viewer.structure_view.add_structure_requested.emit("VS")
    add_structure_to_viewer_mock.assert_called_once_with("VS")
