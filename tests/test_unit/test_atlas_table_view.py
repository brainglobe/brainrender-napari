import shutil
from pathlib import Path

import pytest
from qtpy.QtCore import QModelIndex, Qt

from brainrender_napari.widgets.atlas_table_view import (
    AtlasTableModel,
    AtlasTableView,
)


@pytest.fixture
def atlas_table_view(qtbot) -> AtlasTableView:
    """Fixture to provide a valid atlas table view.

    Depends on qtbot fixture to provide the qt event loop.
    """
    return AtlasTableView()


@pytest.mark.parametrize(
    "row, expected_atlas_name",
    [
        (4, "allen_mouse_100um"),  # part of downloaded test data
        (6, "allen_human_500um"),  # not part of downloaded test data
    ],
)
def test_atlas_table_view_valid_selection(
    row, expected_atlas_name, atlas_table_view
):
    """Checks selected_atlas_name for valid current indices"""
    model_index = atlas_table_view.model().index(row, 0)
    atlas_table_view.setCurrentIndex(model_index)
    assert atlas_table_view.selected_atlas_name() == expected_atlas_name


def test_atlas_table_view_invalid_selection(atlas_table_view):
    """Checks that selected_atlas_name throws an assertion error
    if current index is invalid."""
    with pytest.raises(AssertionError):
        atlas_table_view.setCurrentIndex(QModelIndex())
        atlas_table_view.selected_atlas_name()


def test_hover_atlas_table_view(atlas_table_view, mocker):
    """Check tooltip is called when hovering over view"""
    index = atlas_table_view.model().index(2, 1)

    get_tooltip_text_mock = mocker.patch(
        "brainrender_napari.widgets"
        ".atlas_table_view.AtlasTableModel._get_tooltip_text"
    )

    atlas_table_view.model().data(index, Qt.ToolTipRole)

    get_tooltip_text_mock.assert_called_once()


@pytest.mark.parametrize(
    "column, expected_header",
    [
        (0, "Atlas name"),
        (1, "Latest version"),
    ],
)
def test_model_header(atlas_table_view, column, expected_header):
    """Check the table model has expected header data"""
    assert (
        atlas_table_view.model().headerData(
            column, Qt.Orientation.Horizontal, Qt.DisplayRole
        )
        == expected_header
    )


def test_model_header_invalid_column(atlas_table_view):
    """Check the table model throws as expected for invalid column"""
    invalid_column = 2
    with pytest.raises(ValueError):
        atlas_table_view.model().headerData(
            invalid_column, Qt.Orientation.Horizontal, Qt.DisplayRole
        )


def test_get_tooltip_downloaded():
    """Check tooltip on an example in the downloaded test data"""
    tooltip_text = AtlasTableModel._get_tooltip_text("example_mouse_100um")
    assert "example_mouse" in tooltip_text
    assert "add to viewer" in tooltip_text


def test_get_tooltip_not_locally_available():
    """Check tooltip on an example in not-downloaded test data"""
    tooltip_text = AtlasTableModel._get_tooltip_text("allen_human_500um")
    assert "allen_human_500um" in tooltip_text
    assert "double-click to download" in tooltip_text


def test_get_tooltip_invalid_name():
    """Check tooltip on non-existent test data"""
    with pytest.raises(ValueError) as e:
        _ = AtlasTableModel._get_tooltip_text("wrong_atlas_name")
        assert "invalid atlas name" in e


@pytest.mark.parametrize(
    "row",
    [
        1,  # "allen_mouse_10um"
        6,  # "allen_human_500um"
    ],
)
def test_double_click_on_not_yet_downloaded_atlas_row(
    atlas_table_view, mocker, double_click_on_view, row
):
    """Check for a few yet-to-be-downloaded atlases that double-clicking
    them on the atlas table view executes the download dialog.
    """

    model_index = atlas_table_view.model().index(row, 0)
    atlas_table_view.setCurrentIndex(model_index)

    dialog_exec_mock = mocker.patch(
        "brainrender_napari.widgets.atlas_table_view.AtlasDownloadDialog.exec"
    )
    double_click_on_view(atlas_table_view, model_index)
    dialog_exec_mock.assert_called_once()


@pytest.mark.parametrize(
    "row,expected_atlas_name",
    [
        (0, "example_mouse_100um"),
        (4, "allen_mouse_100um"),
        (14, "osten_mouse_100um"),
    ],
)
def test_double_click_on_locally_available_atlas_row(
    atlas_table_view, double_click_on_view, qtbot, row, expected_atlas_name
):
    """Check for a few locally available low-res atlases that double-clicking
    them on the atlas table view emits a signal with their expected names.
    """
    model_index = atlas_table_view.model().index(row, 0)
    atlas_table_view.setCurrentIndex(model_index)

    with qtbot.waitSignal(
        atlas_table_view.add_atlas_requested
    ) as add_atlas_requested_signal:
        double_click_on_view(atlas_table_view, model_index)

    assert add_atlas_requested_signal.args == [expected_atlas_name]


def test_additional_reference_menu(atlas_table_view, qtbot, mocker):
    """Checks callback to additional reference menu calls QMenu exec
    and emits expected signal"""
    atlas_table_view.selectRow(5)  # mpin_zfish_1um is in row 5
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QAction

    x = atlas_table_view.rowViewportPosition(5)
    y = atlas_table_view.columnViewportPosition(0)
    position = QPoint(x, y)
    qmenu_exec_mock = mocker.patch(
        "brainrender_napari.widgets.atlas_table_view.QMenu.exec"
    )
    qmenu_exec_mock.return_value = QAction("mock_additional_reference")

    with qtbot.waitSignal(
        atlas_table_view.additional_reference_requested
    ) as additional_reference_requested_signal:
        atlas_table_view.customContextMenuRequested.emit(position)

    qmenu_exec_mock.assert_called_once()
    assert additional_reference_requested_signal.args == [
        "mock_additional_reference"
    ]


def test_download_confirmed_callback(atlas_table_view, qtbot):
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
        atlas_table_view.download_atlas_confirmed,
        timeout=150000,  # assumes atlas can be installed in 2.5 minutes!
    ) as download_atlas_confirmed_signal:
        model_index = atlas_table_view.model().index(0, 0)
        atlas_table_view.setCurrentIndex(model_index)
        atlas_table_view._on_download_atlas_confirmed()

    assert download_atlas_confirmed_signal.args == ["example_mouse_100um"]
    for file in expected_filenames:
        assert Path.exists(file)
