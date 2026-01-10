"""Tests for dataset visualization functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from brainglobe_atlasapi import BrainGlobeAtlas

from brainrender_napari.utils.visualize_datasets import (
    _build_neuron_paths,
    _add_points_dataset,
)


class TestBuildNeuronPaths:
    """Test building neuron paths from connections."""

    def test_build_neuron_paths(self):
        """Test building paths from point connections."""
        points = np.array([
            [0.0, 0.0, 0.0],  # Point 0
            [10.0, 10.0, 10.0],  # Point 1
            [20.0, 20.0, 20.0],  # Point 2
        ])
        connections = [(0, 1), (1, 2)]  # Connect 0->1, 1->2
        
        paths = _build_neuron_paths(points, connections)
        
        assert len(paths) == 2
        assert isinstance(paths[0], np.ndarray)
        assert paths[0].shape == (2, 3)  # 2 points, 3 coordinates
        np.testing.assert_array_equal(paths[0][0], points[0])
        np.testing.assert_array_equal(paths[0][1], points[1])

    def test_build_neuron_paths_empty(self):
        """Test building paths with no connections."""
        points = np.array([[0.0, 0.0, 0.0]])
        connections = []
        
        paths = _build_neuron_paths(points, connections)
        
        assert len(paths) == 0

    def test_build_neuron_paths_invalid_indices(self):
        """Test building paths with invalid connection indices."""
        points = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        connections = [(0, 1), (5, 10)]  # Second connection has invalid indices
        
        paths = _build_neuron_paths(points, connections)
        
        # Should only create path for valid connection
        assert len(paths) == 1


class TestAddPointsDataset:
    """Test adding point datasets to viewer."""

    @pytest.fixture
    def mock_atlas(self):
        """Create a mock atlas."""
        atlas = Mock(spec=BrainGlobeAtlas)
        atlas.resolution = [25.0, 25.0, 25.0]  # 25 microns per pixel
        atlas.annotation = np.zeros((528, 320, 456))  # (Z, Y, X) shape
        atlas.atlas_name = "allen_mouse_25um"
        return atlas

    @pytest.fixture
    def mock_viewer(self):
        """Create a mock napari viewer."""
        viewer = MagicMock()
        viewer.layers = MagicMock()
        viewer.layers.index = Mock(return_value=0)
        viewer.layers.move = Mock()
        viewer.dims.ndisplay = 2
        return viewer

    def test_add_points_dataset(self, mock_viewer, mock_atlas):
        """Test adding a points dataset."""
        # Create test data in microns: [x, y, z]
        # Convert to reasonable pixel coordinates
        # For 25um resolution, 1000 microns = 40 pixels
        data = np.array([
            [1000.0, 1000.0, 1000.0],  # Should become [40, 40, 40] in pixels
            [2000.0, 2000.0, 2000.0],  # Should become [80, 80, 80] in pixels
        ])
        
        with patch("brainrender_napari.utils.visualize_datasets.show_info"), \
             patch("brainrender_napari.utils.visualize_datasets.show_error"):
            _add_points_dataset(
                data, mock_viewer, "test_dataset", mock_atlas, None
            )
        
        # Verify add_points was called
        assert mock_viewer.add_points.called
        
        # Check that coordinates were converted and reordered
        call_args = mock_viewer.add_points.call_args
        points_added = call_args[0][0]  # First positional argument
        
        # Should be in (z, y, x) order
        assert points_added.shape == (2, 3)
        # Check approximate pixel values (allowing for float precision)
        np.testing.assert_allclose(points_added[0], [40.0, 40.0, 40.0], rtol=0.1)

    def test_add_points_dataset_empty(self, mock_viewer, mock_atlas):
        """Test adding empty dataset."""
        data = np.array([]).reshape(0, 3)
        
        with patch("brainrender_napari.utils.visualize_datasets.show_error") as mock_error:
            _add_points_dataset(
                data, mock_viewer, "test_dataset", mock_atlas, None
            )
        
        assert mock_error.called
        assert "no data points" in mock_error.call_args[0][0].lower()

    def test_add_points_dataset_wrong_shape(self, mock_viewer, mock_atlas):
        """Test adding dataset with wrong shape."""
        data = np.array([[1.0, 2.0]])  # Only 2D, should be 3D
        
        with patch("brainrender_napari.utils.visualize_datasets.show_error") as mock_error:
            _add_points_dataset(
                data, mock_viewer, "test_dataset", mock_atlas, None
            )
        
        assert mock_error.called

    def test_add_points_dataset_out_of_bounds(self, mock_viewer, mock_atlas):
        """Test adding points that are out of atlas bounds."""
        # Create points way outside atlas bounds
        # Atlas shape is (528, 320, 456) = (Z, Y, X)
        # 25um resolution, so max coords in microns: 13200, 8000, 11400
        # Use 20000 microns (800 pixels) - way outside
        data = np.array([
            [20000.0, 20000.0, 20000.0],
        ])
        
        with patch("brainrender_napari.utils.visualize_datasets.show_info") as mock_info:
            _add_points_dataset(
                data, mock_viewer, "test_dataset", mock_atlas, None
            )
        
        # Should show info about points outside bounds
        assert mock_info.called
        # Points outside bounds should be filtered out
        call_args = mock_viewer.add_points.call_args
        if call_args:  # If any points were added
            points_added = call_args[0][0]
            # Should be empty or filtered
            assert len(points_added) == 0 or len(points_added) < len(data)
