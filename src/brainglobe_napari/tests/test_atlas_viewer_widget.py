from typing import Tuple

import pytest
from napari.viewer import Viewer

from brainglobe_napari.atlas_viewer_widget import AtlasViewerWidget


@pytest.fixture
def make_atlas_viewer(make_napari_viewer) -> Tuple[Viewer, AtlasViewerWidget]:
    """Fixture to expose the atlas viewer widget to tests.
    Simultaneously acts as a smoke test that the widget can
    be instantiated without crashing."""
    viewer = make_napari_viewer()
    atlas_viewer = AtlasViewerWidget(viewer)
    return viewer, atlas_viewer


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
        (14, "osten_mouse_100um"),
    ],
)
def test_show_in_viewer_button(make_atlas_viewer, row, expected_atlas_name):
    """Check for a few low-res atlas selections that clicking the
    "Show in Viewer" button adds a layer with the expected name."""
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.atlas_table_view.selectRow(row)
    atlas_viewer.add_to_viewer.click()
    assert len(viewer.layers) == 2
    assert viewer.layers[1].name == f"{expected_atlas_name}_annotation"
    assert viewer.layers[0].name == f"{expected_atlas_name}_reference"


def test_show_in_viewer_button_no_selection(make_atlas_viewer):
    """Check that clicking "Show in Viewer" button without
    a selection does not add a layer."""
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.add_to_viewer.click()
    assert len(viewer.layers) == 0
