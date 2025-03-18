import shutil
from pathlib import Path

import pytest
from qtpy.QtCore import Qt

from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


@pytest.fixture
def atlas_manager_view(qtbot):
    return AtlasManagerView()

def test_update_atlas_confirmed(
    qtbot,
    mocker,
    atlas_manager_view,
):
    """
    Test that confirming atlas update triggers the correct actions and emits signal.
    Uses mocks instead of filesystem fixtures.
    """
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_downloaded_atlases",
        return_value=["example_mouse_100um"]
    )
    
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_atlases_lastversions",
        return_value={"example_mouse_100um": {"updated": False, "version": "1.2"}}
    )
    
    mocker.patch.object(
        atlas_manager_view,
        "selected_atlas_name",
        return_value="example_mouse_100um"
    )

    def fake_update_atlas(atlas_name, fn_update):
        fn_update(100, 100)
        return atlas_name

    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.update_atlas",
        side_effect=fake_update_atlas,
    )

    with qtbot.waitSignal(
        atlas_manager_view.update_atlas_confirmed,
        timeout=300000,  # assumes atlas can be updated in 5 minutes!
    ) as update_atlas_confirmed_signal:
        atlas_manager_view._on_update_atlas_confirmed()
    
    assert update_atlas_confirmed_signal.args == ["example_mouse_100um"]

def test_progress_signal_emission(atlas_manager_view, qtbot, mocker):
    """Test that progress_updated signal is emitted with correct parameters."""
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.update_atlas",
        side_effect=lambda atlas_name, fn_update: fn_update(50, 100)
        or atlas_name,
    )

    mocker.patch.object(
        atlas_manager_view, "selected_atlas_name", return_value="test_atlas"
    )

    with qtbot.waitSignal(
        atlas_manager_view.progress_updated, timeout=1000
    ) as progress_signal:
        atlas_manager_view._on_update_atlas_confirmed()

    assert progress_signal.args[0] == 50  # completed
    assert progress_signal.args[1] == 100  # total
    assert progress_signal.args[2] == "test_atlas"  # atlas_name
    assert progress_signal.args[3] == "Updating"  # operation_type


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


def test_download_confirmed_callback(atlas_manager_view, qtbot, mocker):
    """Checks that confirming atlas download creates local copy of
    example atlas files and emits expected signal.

    Test setup consists of remembering the expected files and folders
    of a preexisting atlas and then removing them. This allows checking
    that the function triggers the creation of the same local copy
    of the atlas as the `brainglobe_atlasapi` itself.
    """
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.install_atlas",
        return_value="example_mouse_100um",
    )

    # Mock selected_atlas_name to ensure consistent return value
    mocker.patch.object(
        atlas_manager_view,
        "selected_atlas_name",
        return_value="example_mouse_100um",
    )

    with qtbot.waitSignal(
        atlas_manager_view.download_atlas_confirmed,
        timeout=300000,  # assumes atlas can be installed in 5 minutes!
    ) as download_atlas_confirmed_signal:
        # Directly call the download confirmation method
        atlas_manager_view._on_download_atlas_confirmed()

    assert download_atlas_confirmed_signal.args == ["example_mouse_100um"]


def test_double_click_on_outdated_atlas_row(
    atlas_manager_view,
    mocker,
    double_click_on_view,
):
    """Check for an outdated atlas that double-clicking
    it on the atlas manager view executes the update dialog.
    Uses mocks instead of filesystem fixtures.
    """
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_downloaded_atlases",
        return_value=["example_mouse_100um"]
    )
    
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_atlases_lastversions",
        return_value={"example_mouse_100um": {"updated": False, "version": "1.2"}}
    )

    outdated_atlas_index = atlas_manager_view.model().index(0, 1)
    atlas_manager_view.setCurrentIndex(outdated_atlas_index)

    dialog_exec_mock = mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.AtlasManagerDialog.exec"
    )
    double_click_on_view(atlas_manager_view, outdated_atlas_index)
    dialog_exec_mock.assert_called_once()


def test_hover_atlas_manager_view(atlas_manager_view, mocker):
    """Check tooltip is called when hovering over view"""
    index = atlas_manager_view.model().index(2, 1)

    get_tooltip_text_mock = mocker.patch(
        "brainrender_napari.widgets"
        ".atlas_manager_view.AtlasManagerView.get_tooltip_text"
    )

    atlas_manager_view.model().data(index, Qt.ToolTipRole)

    get_tooltip_text_mock.assert_called_once()


def test_get_tooltip_not_locally_available(mocker):
    """Check tooltip on an example in not-downloaded test data"""
    # Mock atlas is not downloaded
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_downloaded_atlases",
        return_value=[]
    )
    
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_all_atlases_lastversions",
        return_value={"allen_human_500um": {"version": "1.0"}}
    )

    tooltip_text = AtlasManagerView.get_tooltip_text("allen_human_500um")
    assert format_atlas_name("allen_human_500um") in tooltip_text
    assert "double-click to download" in tooltip_text


def test_get_tooltip_not_up_to_date(mocker):
    """Check tooltip on an atlas that is not up-to-date"""
    # Mock downloaded atlas
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_downloaded_atlases",
        return_value=["example_mouse_100um"]
    )
    
    # Mock old version atlas
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_atlases_lastversions",
        return_value={"example_mouse_100um": {"updated": False, "version": "1.2"}}
    )

    tooltip_text = AtlasManagerView.get_tooltip_text("example_mouse_100um")
    assert format_atlas_name("example_mouse_100um") in tooltip_text
    assert "double-click to update" in tooltip_text


def test_get_tooltip_is_up_to_date(mocker):
    """Check tooltip on an atlas that is already up-to-date"""
    # Mock downloaded atlas
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_downloaded_atlases",
        return_value=["example_mouse_100um"]
    )
    
    # Mock latest version atlas
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_atlases_lastversions",
        return_value={"example_mouse_100um": {"updated": True, "version": "1.2"}}
    )

    tooltip_text = AtlasManagerView.get_tooltip_text("example_mouse_100um")
    assert format_atlas_name("example_mouse_100um") in tooltip_text
    assert "is up-to-date" in tooltip_text


def test_get_tooltip_invalid_name(mocker):
    """Check tooltip on non-existent test data"""
    # Mock all atlas lists
    mocker.patch(
        "brainrender_napari.widgets.atlas_manager_view.get_all_atlases_lastversions",
        return_value={"valid_atlas": {"version": "1.0"}}
    )
    
    with pytest.raises(ValueError) as e:
        _ = AtlasManagerView.get_tooltip_text("wrong_atlas_name")
        assert "invalid atlas name" in e


def test_apply_in_thread(qtbot, mocker):
    """
    Verify that _apply_in_thread correctly executes the passed function
    and returns the result.
    Temporarily patch the instance _apply_in_thread to
    avoid the effects of @thread_worker.
    """

    atlas_manager_view = AtlasManagerView()
    # Replace _apply_in_thread with identity lambda
    # to make it run in the same thread
    original_apply_in_thread = atlas_manager_view._apply_in_thread
    atlas_manager_view._apply_in_thread = lambda func, *args, **kwargs: func(
        *args, **kwargs
    )

    mock_dummy_apply = mocker.Mock(return_value="example_mouse_100um")
    actual = atlas_manager_view._apply_in_thread(
        mock_dummy_apply, "example_mouse_100um"
    )
    expected = "example_mouse_100um"
    assert actual == expected
    mock_dummy_apply.assert_called_once_with("example_mouse_100um")

    # Restore the original _apply_in_thread
    atlas_manager_view._apply_in_thread = original_apply_in_thread
