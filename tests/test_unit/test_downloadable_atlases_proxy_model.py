import shutil
from pathlib import Path

import pytest

from brainrender_napari.data_models.downloadable_atlases_proxy_model import (
    DownloadableAtlasesProxyModel,
)
from brainrender_napari.utils.formatting import format_atlas_name


@pytest.fixture
def downloadable_atlases(qtbot):
    return DownloadableAtlasesProxyModel()


@pytest.mark.parametrize(
    "atlas_name",
    ["allen_mouse_10um", "allen_human_500um"],
)
def test_atlases_present(downloadable_atlases, atlas_name):
    """Check some atlases are expectedly present"""
    assert atlas_name in downloadable_atlases.atlases_to_keep()


@pytest.mark.parametrize(
    "atlas_name",
    ["example_mouse_100um", "allen_mouse_100um"],
)
def test_atlases_absent(downloadable_atlases, atlas_name):
    """Check some atlases are expectedly absent"""
    assert atlas_name not in downloadable_atlases.atlases_to_keep()


@pytest.mark.parametrize(
    "atlas_name",
    ["allen_mouse_10um", "allen_human_500um"],
)
def test_double_click_on_not_yet_downloaded_atlas(
    downloadable_atlases, mocker, atlas_name
):
    """Check for a few yet-to-be-downloaded atlases that double-clicking
    them on the atlas table view executes the download dialog.
    """
    dialog_exec_mock = mocker.patch(
        "brainrender_napari.data_models.downloadable_atlases_proxy_model.AtlasManagerDialog.exec"
    )
    downloadable_atlases.prepare_double_click_action(atlas_name)
    dialog_exec_mock.assert_called_once()


def test_download_confirmed_callback(downloadable_atlases, qtbot):
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
        downloadable_atlases.double_click_action_performed,
        timeout=150000,  # assumes atlas can be installed in 2.5 minutes!
    ) as download_atlas_confirmed_signal:
        downloadable_atlases._on_action_confirmed("example_mouse_100um")

    assert download_atlas_confirmed_signal.args == ["example_mouse_100um"]
    for file in expected_filenames:
        assert Path.exists(file)


def test_get_tooltip(downloadable_atlases):
    """Check tooltip on an example in not-downloaded test data"""
    tooltip_text = downloadable_atlases.get_tooltip_text("allen_human_500um")
    assert format_atlas_name("allen_human_500um") in tooltip_text
    assert "double-click to download" in tooltip_text
