import pytest

from brainrender_napari.atlas_version_manager_widget import (
    AtlasVersionManagerWidget,
)


@pytest.fixture
def atlas_version_manager_widget(qtbot) -> AtlasVersionManagerWidget:
    """A fixture to provide a version manager widget.

    Depends on qtbot so Qt event loop is started.
    """
    return AtlasVersionManagerWidget()


def test_refresh_calls_view_constructor(atlas_version_manager_widget, mocker):
    """Checks that refreshing the version manager widget
    calls the view's constructor."""
    atlas_manager_view_mock = mocker.patch(
        "brainrender_napari.atlas_version_manager_widget.AtlasManagerView"
    )
    atlas_version_manager_widget._refresh()
    atlas_manager_view_mock.assert_called_once_with(
        parent=atlas_version_manager_widget
    )


def test_refresh_on_download(qtbot, mocker):
    """Checks that when the view signals an atlas has been downloaded,
    the version manager widget is refreshed."""
    refresh_mock = mocker.patch(
        "brainrender_napari.atlas_version_manager_widget.AtlasVersionManagerWidget._refresh"
    )
    # Don't use atlas_version_manager_widget fixture here,
    # because otherwise mocking is ineffectual!
    atlas_version_manager_widget = AtlasVersionManagerWidget()
    with qtbot.waitSignal(
        atlas_version_manager_widget.atlas_manager_view.download_atlas_confirmed
    ):
        atlas_version_manager_widget.atlas_manager_view.download_atlas_confirmed.emit(
            "allen_mouse_100um"
        )
    refresh_mock.assert_called_once_with("allen_mouse_100um")


def test_refresh_on_update(qtbot, mocker):
    """Checks that when the view signals an atlas has been updated,
    the version manager widget is updated."""
    refresh_mock = mocker.patch(
        "brainrender_napari.atlas_version_manager_widget"
        ".AtlasVersionManagerWidget._refresh"
    )
    # Don't use atlas_version_manager_widget fixture here,
    # because otherwise mocking is ineffectual!
    atlas_version_manager_widget = AtlasVersionManagerWidget()
    with qtbot.waitSignal(
        atlas_version_manager_widget.atlas_manager_view.update_atlas_confirmed
    ):
        atlas_version_manager_widget.atlas_manager_view.update_atlas_confirmed.emit(
            "allen_mouse_100um"
        )
    refresh_mock.assert_called_once_with("allen_mouse_100um")
