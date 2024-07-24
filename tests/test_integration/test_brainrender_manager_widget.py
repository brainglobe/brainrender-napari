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
