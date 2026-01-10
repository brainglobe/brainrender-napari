"""Integration tests for the dataset widget."""

import pytest

from brainrender_napari.brainrender_dataset_widget import (
    BrainrenderDatasetWidget,
)


@pytest.fixture
def dataset_widget(make_napari_viewer):
    """Fixture to create a dataset widget for testing."""
    viewer = make_napari_viewer()
    return BrainrenderDatasetWidget(viewer)


def test_dataset_widget_init(dataset_widget):
    """Test that the dataset widget can be instantiated."""
    assert dataset_widget is not None
    assert hasattr(dataset_widget, 'dataset_manager_view')
    assert hasattr(dataset_widget, 'database_search_widget')


def test_dataset_widget_has_search_widget(dataset_widget):
    """Test that the widget contains a database search widget."""
    assert dataset_widget.database_search_widget is not None


def test_dataset_widget_has_manager_view(dataset_widget):
    """Test that the widget contains a dataset manager view."""
    assert dataset_widget.dataset_manager_view is not None
