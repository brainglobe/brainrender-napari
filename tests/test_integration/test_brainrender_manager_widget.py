"""These tests should just check that the subwidget signal and napari
are connected as expected. Lower level tests should happen in the tests
for the widget themselves."""

import pytest

from brainrender_napari.brainrender_manager_widget import (
    BrainrenderManagerWidget,
)


@pytest.fixture
def manager_widget(make_napari_viewer) -> BrainrenderManagerWidget:
    """Fixture to expose the atlas viewer widget to tests.

    Simultaneously acts as a smoke test that the widget
    can be instantiated without crashing."""
    viewer = make_napari_viewer()
    return BrainrenderManagerWidget(viewer)


def test_atlas_manager_view_tooltip(manager_widget):
    for expected_keyword in [
        "double-click",
        "download/update",
        "row",
        "atlas",
    ]:
        assert (
            expected_keyword
            in manager_widget.atlas_manager_group.toolTip().lower()
        )


def test_signal_connections(manager_widget, qtbot, mocker):
    """Test that signals are correctly connected between components."""
    # Check that each signal has exactly one receiver connected
    assert (
        manager_widget.atlas_manager_view.receivers(
            manager_widget.atlas_manager_view.progress_updated
        )
        == 1
    )
    assert (
        manager_widget.atlas_manager_view.receivers(
            manager_widget.atlas_manager_view.download_atlas_confirmed
        )
        == 1
    )
    assert (
        manager_widget.atlas_manager_view.receivers(
            manager_widget.atlas_manager_view.update_atlas_confirmed
        )
        == 1
    )


def test_components_existence(manager_widget):
    """Test that all required components exist in the widget."""
    # Ensure that the required components are present
    assert hasattr(manager_widget, "atlas_manager_view")
    assert hasattr(manager_widget, "progress_bar")
    assert hasattr(manager_widget, "atlas_manager_group")
