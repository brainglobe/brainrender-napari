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


@pytest.mark.parametrize(
    "row, expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
    ],
)
def test_atlas_view_valid_selection(
    row, expected_atlas_name, atlas_viewer_view
):
    """Checks selected_atlas_name for valid current indices"""
    model_index = atlas_viewer_view.model().index(row, 0)
    atlas_viewer_view.setCurrentIndex(model_index)
    assert atlas_viewer_view.selected_atlas_name() == expected_atlas_name


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
    with qtbot.capture_exceptions() as exceptions:
        # should raise because human atlas (row 6) is not available
        # exception raised within qt loop in this case.
        model_index = atlas_viewer_view.model().index(6, 0)
        atlas_viewer_view.setCurrentIndex(model_index)
    assert len(exceptions) == 1
    _, exception, collected_traceback = exceptions[0]  # ignore type
    assert isinstance(exception, AssertionError)
    assert "selected_atlas_name" in traceback.format_tb(collected_traceback)[0]


def test_hover_atlas_viewer_view(atlas_viewer_view, mocker):
    """Check tooltip is called when hovering over view"""
    index = atlas_viewer_view.model().index(2, 1)

    get_tooltip_text_mock = mocker.patch(
        "brainrender_napari.widgets"
        ".atlas_viewer_view.AtlasViewerView.get_tooltip_text"
    )

    atlas_viewer_view.model().data(index, Qt.ToolTipRole)

    get_tooltip_text_mock.assert_called_once()


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
        (14, "osten_mouse_100um"),
    ],
)
def test_double_click_on_locally_available_atlas_row(
    atlas_viewer_view, double_click_on_view, qtbot, row, expected_atlas_name
):
    """Check for a few locally available low-res atlases that double-clicking
    them on the atlas table view emits a signal with their expected names.
    """
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
    atlas_viewer_view.selectRow(
        0
    )  # example atlas + mock additional reference is in row 0
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QAction

    x = atlas_viewer_view.rowViewportPosition(0)
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


def test_downloaded_only_proxy_model_filters_non_downloaded(
    atlas_viewer_view,
):
    """Test DownloadedOnlyProxyModel filters non-downloaded atlases."""
    # The proxy model should only show downloaded atlases
    from brainglobe_atlasapi.list_atlases import get_downloaded_atlases

    downloaded_count = len(get_downloaded_atlases())
    proxy_count = atlas_viewer_view.proxy_model.rowCount()

    # Should match exactly
    assert proxy_count == downloaded_count


def test_downloaded_only_proxy_model_with_filter(atlas_viewer_view):
    """Test that DownloadedOnlyProxyModel works with text filtering."""
    # Apply a text filter
    atlas_viewer_view.proxy_model.setFilterFixedString("mouse")

    # Should still only show downloaded atlases that match "mouse"
    assert atlas_viewer_view.proxy_model.rowCount() > 0

    # Verify all visible rows are downloaded
    from brainglobe_atlasapi.list_atlases import get_downloaded_atlases

    downloaded = get_downloaded_atlases()
    for row in range(atlas_viewer_view.proxy_model.rowCount()):
        index = atlas_viewer_view.proxy_model.index(row, 0)
        atlas_name = atlas_viewer_view.proxy_model.data(index)
        assert atlas_name in downloaded


def test_proxy_model_sorting_maintains_download_filter(
    atlas_viewer_view, qtbot
):
    """Test that sorting doesn't break the downloaded-only filter."""
    from brainglobe_atlasapi.list_atlases import get_downloaded_atlases

    initial_count = atlas_viewer_view.proxy_model.rowCount()
    downloaded_count = len(get_downloaded_atlases())

    assert initial_count == downloaded_count

    # Sort by column 1 (Atlas name)
    atlas_viewer_view.sortByColumn(1, Qt.AscendingOrder)
    qtbot.wait(100)

    # Count should remain the same after sorting
    sorted_count = atlas_viewer_view.proxy_model.rowCount()
    assert sorted_count == downloaded_count
    assert sorted_count == initial_count


def test_proxy_model_rejects_non_matching_search(atlas_viewer_view):
    """Test that proxy model correctly rejects rows that don't match search."""
    # Set a filter that won't match any atlas
    atlas_viewer_view.proxy_model.setFilterFixedString("xyznonexistent")

    # Should show 0 rows
    assert atlas_viewer_view.proxy_model.rowCount() == 0

    # Clear filter
    atlas_viewer_view.proxy_model.setFilterFixedString("")

    # Should show downloaded atlases again
    from brainglobe_atlasapi.list_atlases import get_downloaded_atlases

    assert atlas_viewer_view.proxy_model.rowCount() == len(
        get_downloaded_atlases()
    )
