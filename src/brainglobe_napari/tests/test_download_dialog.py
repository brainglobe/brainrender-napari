import pytest

from brainglobe_napari.atlas_download_dialog import AtlasDownloadDialog


def test_download_dialog(qtbot):
    """Check download dialog constructor and buttons connections"""
    dialog = AtlasDownloadDialog("example_mouse_100um")
    with qtbot.waitSignal(dialog.accepted):
        dialog.ok_button.click()

    with qtbot.waitSignal(dialog.rejected):
        dialog.cancel_button.click()


def test_download_dialog_raises():
    """Check download dialog constructor errors on invalid input"""
    with pytest.raises(ValueError) as e:
        _ = AtlasDownloadDialog("wrong_atlas_name")
        assert "invalid atlas name" in e
