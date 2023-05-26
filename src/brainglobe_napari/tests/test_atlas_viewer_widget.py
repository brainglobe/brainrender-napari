from typing import Tuple

import pytest
from napari.viewer import Viewer

from brainglobe_napari.atlas_viewer_widget import AtlasViewerWidget


@pytest.fixture
def make_atlas_viewer(make_napari_viewer) -> Tuple[Viewer, AtlasViewerWidget]:
    viewer = make_napari_viewer()
    atlas_viewer = AtlasViewerWidget(viewer)
    return viewer, atlas_viewer


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (1, "allen_mouse_10um"),
        (4, "allen_mouse_100um"),
    ],
)
def test_add_annotation_button(make_atlas_viewer, row, expected_atlas_name):
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.atlas_table_view.selectRow(row)
    atlas_viewer.add_annotation_button.click()
    assert len(viewer.layers) == 1
    assert viewer.layers[0].name == expected_atlas_name


def test_add_annotations_button_no_selection(make_atlas_viewer):
    viewer, atlas_viewer = make_atlas_viewer

    atlas_viewer.add_annotation_button.click()
    assert len(viewer.layers) == 0
