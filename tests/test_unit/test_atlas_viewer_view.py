import traceback

import pytest
from qtpy.QtCore import QModelIndex, Qt

from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_viewer_view import (
    AtlasViewerView,
)


@pytest.fixture
def atlas_viewer_view(qtbot) -> AtlasViewerView:
    """Fixture to provide a valid atlas table view.

    Depends on qtbot fixture to provide the qt event loop.
    """
    return AtlasViewerView()


def _find_row_for_atlas(view, atlas_name):
    """Helper to find the proxy model row index for a given atlas name."""
    for row in range(view.proxy_model.rowCount()):
        index = view.proxy_model.index(row, 0)
        if view.proxy_model.data(index) == atlas_name:
            return row
    return None


def test_atlas_view_valid_selection_example(atlas_viewer_view):
    """Checks selected_atlas_name for example_mouse_100um."""
    row = _find_row_for_atlas(atlas_viewer_view, "example_mouse_100um")
    assert row is not None
    model_index = atlas_viewer_view.model().index(row, 0)
    atlas_viewer_view.setCurrentIndex(model_index)
    assert atlas_viewer_view.selected_atlas_name() == "example_mouse_100um"


def test_atlas_view_valid_selection_allen(atlas_viewer_view):
    """Checks selected_atlas_name for allen_mouse_100um."""
    row = _find_row_for_atlas(atlas_viewer_view, "allen_mouse_100um")
    assert row is not None
    model_index = atlas_viewer_view.model().index(row, 0)
    atlas_viewer_view.setCurrentIndex(model_index)
    assert atlas_viewer_view.selected_atlas_name() == "allen_mouse_100um"


def test_atlas_view_invalid_selection(atlas_viewer_view):
    """Checks that selected_atlas_name throws an assertion error
    if current index is invalid."""
    with pytest.raises(AssertionError):
        atlas_viewer_view.setCurrentIndex(QModelIndex())
        atlas_viewer_view.selected_atlas_name()


def test_atlas_view_not_downloaded_selection(qtbot, atlas_viewer_view):
    """Checks that selected_atlas_name raises an assertion error
    if current index is valid, but not a downloaded atlas.
    """
    # Find a non-downloaded atlas
    non_downloaded_row = None
    for row in range(atlas_viewer_view.proxy_model.rowCount()):
        index = atlas_viewer_view.proxy_model.index(row, 0)
        name = atlas_viewer_view.proxy_model.data(index)
        source_index = atlas_viewer_view.proxy_model.mapToSource(index)
        local_ver_index = source_index.siblingAtColumn(2)
        local_ver = atlas_viewer_view.source_model.data(local_ver_index)
        if local_ver == "n/a":
            non_downloaded_row = row
            break

    if non_downloaded_row is not None:
        with qtbot.capture_exceptions() as exceptions:
            model_index = atlas_viewer_view.model().index(
                non_downloaded_row, 0
            )
            atlas_viewer_view.setCurrentIndex(model_index)
        assert len(exceptions) == 1
        _, exception, collected_traceback = exceptions[0]
        assert isinstance(exception, AssertionError)
        assert (
            "selected_atlas_name"
            in traceback.format_tb(collected_traceback)[0]
        )


def test_hover_atlas_viewer_view(atlas_viewer_view, mocker):
    """Check tooltip is called when hovering over view"""
    row = _find_row_for_atlas(atlas_viewer_view, "example_mouse_100um")
    assert row is not None
    # Access the source model for tooltip (proxy delegates tooltip role)
    source_index = atlas_viewer_view.proxy_model.mapToSource(
        atlas_viewer_view.proxy_model.index(row, 1)
    )

    get_tooltip_text_mock = mocker.patch(
        "brainrender_napari.widgets"
        ".atlas_viewer_view.AtlasViewerView.get_tooltip_text"
    )

    atlas_viewer_view.source_model.data(source_index, Qt.ToolTipRole)
    get_tooltip_text_mock.assert_called_once()


@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
        "osten_mouse_100um",
    ],
)
def test_double_click_on_locally_available_atlas_row(
    atlas_viewer_view, double_click_on_view, qtbot, expected_atlas_name
):
    """Check for locally available low-res atlases that double-clicking
    them on the atlas table view emits a signal with their expected names.
    """
    row = _find_row_for_atlas(atlas_viewer_view, expected_atlas_name)
    assert row is not None, f"Could not find {expected_atlas_name} in viewer"
    model_index = atlas_viewer_view.model().index(row, 1)
    atlas_viewer_view.setCurrentIndex(model_index)

    with qtbot.waitSignal(
        atlas_viewer_view.add_atlas_requested
    ) as add_atlas_requested_signal:
        double_click_on_view(atlas_viewer_view, model_index)

    assert add_atlas_requested_signal.args == [expected_atlas_name]


def test_additional_reference_menu(atlas_viewer_view, qtbot, mocker):
    """Checks callback to additional reference menu calls QMenu exec
    and emits expected signal"""
    row = _find_row_for_atlas(atlas_viewer_view, "example_mouse_100um")
    assert row is not None
    model_index = atlas_viewer_view.model().index(row, 0)
    atlas_viewer_view.setCurrentIndex(model_index)

    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QAction

    x = atlas_viewer_view.rowViewportPosition(row)
    y = atlas_viewer_view.columnViewportPosition(1)
    position = QPoint(x, y)
    qmenu_exec_mock = mocker.patch(
        "brainrender_napari.widgets.atlas_viewer_view.QMenu.exec"
    )
    qmenu_exec_mock.return_value = QAction("reference")

    with qtbot.waitSignal(
        atlas_viewer_view.additional_reference_requested
    ) as additional_reference_requested_signal:
        atlas_viewer_view.customContextMenuRequested.emit(position)

    qmenu_exec_mock.assert_called_once()
    assert additional_reference_requested_signal.args == ["reference"]


def test_get_tooltip():
    """Check tooltip on an example in the downloaded test data"""
    tooltip_text = AtlasViewerView.get_tooltip_text("example_mouse_100um")
    assert format_atlas_name("example_mouse_100um") in tooltip_text
    assert "add to viewer" in tooltip_text


def test_get_tooltip_invalid_name():
    """Check tooltip on non-existent test data"""
    with pytest.raises(ValueError) as e:
        _ = AtlasViewerView.get_tooltip_text("wrong_atlas_name")
        assert "invalid atlas name" in e


def test_sorting_enabled(atlas_viewer_view):
    """Check that sorting is enabled on the viewer view."""
    assert atlas_viewer_view.isSortingEnabled()


def test_proxy_model_exists(atlas_viewer_view):
    """Check that the viewer view uses a proxy model."""
    assert atlas_viewer_view.proxy_model is not None
    assert atlas_viewer_view.source_model is not None
