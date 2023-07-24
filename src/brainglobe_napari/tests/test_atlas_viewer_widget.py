import shutil
from pathlib import Path
from typing import Tuple

import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.viewer import Viewer
from qtpy.QtCore import Qt

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


def test_download_confirmed_callback(make_atlas_viewer):
    """Checks that confirming atlas download creates local copy of
    example atlas files.

    Test setup consists of remembering the expected files and folders
    of a preexisting atlas and then removing them. This allows checking
    that the function triggers the creation of the same local copy
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
    atlas_viewer._on_download_atlas_confirmed()

    for file in expected_filenames:
        assert Path.exists(file)


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
        (14, "osten_mouse_100um"),
    ],
)
def test_double_click_on_locally_available_atlas_row(
    make_atlas_viewer, double_click_on_view, row, expected_atlas_name
):
    """Check for a few locally available low-res atlases that double-clicking
    them on the atlas table view adds the layers with their expected names.
    """
    viewer, atlas_viewer = make_atlas_viewer

    model_index = atlas_viewer.atlas_table_view.model().index(row, 0)
    atlas_viewer.atlas_table_view.setCurrentIndex(model_index)

    double_click_on_view(atlas_viewer.atlas_table_view, model_index)

    assert len(viewer.layers) == 2
    assert viewer.layers[1].name == f"{expected_atlas_name}_annotation"
    assert viewer.layers[0].name == f"{expected_atlas_name}_reference"


@pytest.mark.parametrize(
    "row, expected_atlas_name",
    [
        (1, "allen_mouse_100um"),  # not part of downloaded test data
        (5, "mpin_zfish_1um"),  # not part of downloaded test data
    ],
)
def test_double_click_on_not_yet_downloaded_atlas_row(
    make_atlas_viewer, mocker, double_click_on_view, row, expected_atlas_name
):
    """Check for a few yet-to-be-downloaded atlases that double-clicking
    them on the atlas table view executes the download dialog.
    """
    _, atlas_viewer = make_atlas_viewer

    model_index = atlas_viewer.atlas_table_view.model().index(row, 0)
    atlas_viewer.atlas_table_view.setCurrentIndex(model_index)

    dialog_exec_mock = mocker.patch(
        "brainglobe_napari.atlas_viewer_widget.AtlasDownloadDialog.exec"
    )
    # weirdly, to correctly emulate a double-click
    # you need to click first. Also, note that the view
    # needs to be interacted with via its viewport
    double_click_on_view(atlas_viewer.atlas_table_view, model_index)
    dialog_exec_mock.assert_called_once()


def test_structure_row_double_clicked(
    make_atlas_viewer, mocker, double_click_on_view
):
    """Checks that clicking the add_structure_button with
    the allen_mouse_100um atlas and its VS submesh selected
    in the widget views calls the NapariAtlasRepresentation
    function in the expected way.
    """
    _, atlas_viewer = make_atlas_viewer
    add_structure_to_viewer_mock = mocker.patch(
        "brainglobe_napari.atlas_viewer_widget"
        ".NapariAtlasRepresentation.add_structure_to_viewer"
    )
    atlas_viewer.atlas_table_view.selectRow(4)  # allen_mouse_100um is in row 4

    # find and select first sub-item of root mesh in structure tree view
    root_index = atlas_viewer.structure_tree_view.rootIndex()
    root_mesh_index = atlas_viewer.structure_tree_view.model().index(
        0, 0, root_index
    )
    vs_mesh_index = atlas_viewer.structure_tree_view.model().index(
        0, 0, root_mesh_index
    )
    assert vs_mesh_index.isValid()
    atlas_viewer.structure_tree_view.setCurrentIndex(vs_mesh_index)

    double_click_on_view(atlas_viewer.structure_tree_view, vs_mesh_index)

    # First sub-item in tree view expected to be "VS"
    add_structure_to_viewer_mock.assert_called_once_with("VS")


@pytest.mark.parametrize(
    "row, expected_visibility",
    [
        (4, True),  # allen_mouse_100um is part of downloaded test data
        (5, False),  # mpin_fish_1um is not part of download test data
    ],
)
def test_add_structure_visibility(make_atlas_viewer, row, expected_visibility):
    """Checks that the structure tree view and add structure buttons
    are visible iff atlas has previously been downloaded."""
    _, atlas_viewer = make_atlas_viewer
    atlas_viewer.show()  # show tree view ancestor for sensible check
    atlas_viewer.atlas_table_view.selectRow(row)
    assert atlas_viewer.structure_tree_view.isVisible() == expected_visibility


def test_get_tooltip_downloaded():
    tooltip_text = AtlasViewerWidget.get_tooltip_text("example_mouse_100um")
    assert "example_mouse" in tooltip_text
    assert "add to viewer" in tooltip_text


def test_get_tooltip_not_locally_available():
    tooltip_text = AtlasViewerWidget.get_tooltip_text("mpin_zfish_1um")
    assert "mpin_zfish_1um" in tooltip_text
    assert "double-click to download" in tooltip_text


def test_get_tooltip_invalid_name():
    with pytest.raises(ValueError) as e:
        _ = AtlasViewerWidget.get_tooltip_text("wrong_atlas_name")
        assert "invalid atlas name" in e


def test_hover_atlas_table_view(make_atlas_viewer, mocker, qtbot):
    _, atlas_viewer = make_atlas_viewer
    view = atlas_viewer.atlas_table_view
    index = view.model().index(2, 1)

    get_tooltip_text_mock = mocker.patch(
        "brainglobe_napari.atlas_viewer_widget"
        ".AtlasViewerWidget.get_tooltip_text"
    )

    view.model().data(index, Qt.ToolTipRole)

    get_tooltip_text_mock.assert_called_once()
