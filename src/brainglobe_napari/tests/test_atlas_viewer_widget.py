import shutil
from pathlib import Path
from typing import Tuple

import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.viewer import Viewer

from brainglobe_napari.atlas_viewer_widget import AtlasViewerWidget


@pytest.fixture
def make_atlas_viewer(make_napari_viewer) -> Tuple[Viewer, AtlasViewerWidget]:
    """Fixture to expose the atlas viewer widget to tests.

    Downloads three atlases as test data, if not already there.

    Simultaneously acts as a smoke test that the widget and
    local atlas files can be instantiated without crashing."""
    viewer = make_napari_viewer()
    preexisting_atlases = [
        ("example_mouse_100um", "v1.2"),
        ("allen_mouse_100um", "v1.2"),
        ("osten_mouse_100um", "v1.1"),
    ]
    for atlas_name, version in preexisting_atlases:
        if not Path.exists(
            Path.home() / f".brainglobe/{atlas_name}_{version}"
        ):
            _ = BrainGlobeAtlas(atlas_name)

    atlas_viewer = AtlasViewerWidget(viewer)
    return viewer, atlas_viewer


def test_download_button(make_atlas_viewer):
    """Checks that download button creates local copy of example atlas files.

    Test setup consists of remembering the expected files and folders
    of a preexisting atlas and then removing them.This allows checking
    that the button triggers the creation of the same local copy
    of the atlas as the `bg_atlasapi` itself.
    """
    atlas_directory = Path.home() / ".brainglobe/example_mouse_100um_v1.2"
    expected_filenames = atlas_directory.iterdir()
    shutil.rmtree(
        path=atlas_directory
    )  # now remove local copy so button has to trigger download
    assert not Path.exists(
        atlas_directory
    )  # sanity check that local copy is gone

    _, atlas_viewer = make_atlas_viewer
    atlas_viewer.atlas_table_view.selectRow(0)
    atlas_viewer.download_selected_atlas.click()

    for file in expected_filenames:
        assert Path.exists(file)


def test_download_button_already_downloaded(make_atlas_viewer, mocker):
    """Check that hitting download a second time calls show_info.
    and does not call the `BrainGlobeAtlas` constructor.
    """
    _, atlas_viewer = make_atlas_viewer
    atlas_viewer.atlas_table_view.selectRow(0)
    atlas_viewer.download_selected_atlas.click()

    show_info_mock = mocker.patch(
        "brainglobe_napari.atlas_viewer_widget.show_info"
    )
    atlas_constructor_mock = mocker.patch(
        "brainglobe_napari.atlas_viewer_widget.BrainGlobeAtlas"
    )

    atlas_viewer.download_selected_atlas.click()

    show_info_mock.assert_called_once_with("Atlas already downloaded.")
    atlas_constructor_mock.assert_not_called()


def test_download_button_no_selection(make_atlas_viewer):
    """Smoke test to check downloading without selection doesn't crash"""
    _, atlas_viewer = make_atlas_viewer
    atlas_viewer.download_selected_atlas.click()


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
        (14, "osten_mouse_100um"),
    ],
)
def test_add_to_viewer_button(make_atlas_viewer, row, expected_atlas_name):
    """Check for a few low-res atlas selections that clicking the
    "Add to viewer" button adds the layers with their expected names."""
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.atlas_table_view.selectRow(row)
    atlas_viewer.add_to_viewer.click()

    assert len(viewer.layers) == 3
    assert viewer.layers[2].name == f"{expected_atlas_name}_mesh"
    assert viewer.layers[1].name == f"{expected_atlas_name}_annotation"
    assert viewer.layers[0].name == f"{expected_atlas_name}_reference"


def test_show_in_viewer_button_no_selection(make_atlas_viewer):
    """Check that clicking "Show in Viewer" button without
    a selection does not add a layer."""
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.add_to_viewer.click()
    assert len(viewer.layers) == 0
