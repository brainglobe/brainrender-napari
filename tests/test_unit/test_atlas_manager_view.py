import shutil
from pathlib import Path

import pytest

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


@pytest.fixture
def atlas_manager_view(qtbot):
    return AtlasManagerView()


def test_update_atlas_confirmed(
    qtbot,
    mock_newer_atlas_version_available,
    atlas_manager_view,
):
    """The order of fixtures matters here:
    call mock before view constructor!"""
    outdated_atlas_directory = (
        Path.home() / ".brainglobe/example_mouse_100um_v1.1"
    )
    updated_atlas_directory = (
        Path.home() / ".brainglobe/example_mouse_100um_v1.2"
    )
    assert (
        outdated_atlas_directory.exists()
        and not updated_atlas_directory.exists()
    )
    local_version_index = atlas_manager_view.model().index(0, 2)
    assert atlas_manager_view.model().data(local_version_index) == "1.1"

    with qtbot.waitSignal(
        atlas_manager_view.update_atlas_confirmed,
        timeout=150000,  # assumes atlas can be updated in 2.5 minutes!
    ) as update_atlas_confirmed_signal:
        # replace with double-click on view?
        model_index = atlas_manager_view.model().index(0, 0)
        atlas_manager_view.setCurrentIndex(model_index)
        atlas_manager_view._on_update_atlas_confirmed()

    assert atlas_manager_view.model().data(local_version_index) == "1.2"
    assert update_atlas_confirmed_signal.args == ["example_mouse_100um"]
    assert (
        updated_atlas_directory.exists()
        and not outdated_atlas_directory.exists()
    )


@pytest.mark.parametrize(
    "row",
    [
        1,  # "allen_mouse_10um"
        6,  # "allen_human_500um"
    ],
)
def test_double_click_on_not_yet_downloaded_atlas_row(
    atlas_manager_view, mocker, double_click_on_view, row
):
    """Check for a few yet-to-be-downloaded atlases that double-clicking
    them on the atlas table view executes the download dialog.
    """

    model_index = atlas_manager_view.model().index(row, 1)
    atlas_manager_view.setCurrentIndex(model_index)

    dialog_exec_mock = mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.AtlasManagerDialog.exec"
    )
    double_click_on_view(atlas_manager_view, model_index)
    dialog_exec_mock.assert_called_once()


def test_download_confirmed_callback(atlas_manager_view, qtbot):
    """Checks that confirming atlas download creates local copy of
    example atlas files and emits expected signal.

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

    with qtbot.waitSignal(
        atlas_manager_view.download_atlas_confirmed,
        timeout=150000,  # assumes atlas can be installed in 2.5 minutes!
    ) as download_atlas_confirmed_signal:
        model_index = atlas_manager_view.model().index(0, 0)
        atlas_manager_view.setCurrentIndex(model_index)
        atlas_manager_view._on_download_atlas_confirmed()

    assert download_atlas_confirmed_signal.args == ["example_mouse_100um"]
    for file in expected_filenames:
        assert Path.exists(file)
