import pytest

from brainrender_napari.widgets.atlas_manager_dialog import (
    AtlasManagerDialog,
)


@pytest.mark.parametrize("action", ["Download", "Update"])
def test_download_update_dialog(action, qtbot):
    """Check download dialog constructor and buttons connections"""
    dialog = AtlasManagerDialog("example_mouse_100um", action)
    with qtbot.waitSignal(dialog.accepted):
        dialog.ok_button.click()

    with qtbot.waitSignal(dialog.rejected):
        dialog.cancel_button.click()


@pytest.mark.parametrize("action", ["Download", "Update"])
def test_download_update_dialog_raises(action):
    """Check download dialog constructor errors on invalid input"""
    with pytest.raises(ValueError) as e:
        _ = AtlasManagerDialog("wrong_atlas_name", action)
        assert [action, "invalid atlas name"] in e
