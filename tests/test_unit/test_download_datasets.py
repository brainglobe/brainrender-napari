"""Tests for dataset downloading functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from brainrender_napari.utils.download_datasets import (
    AVAILABLE_DATASETS,
    get_available_datasets,
    get_downloaded_datasets,
    get_dataset_path,
    load_dataset_data,
    register_dynamic_dataset,
)


class TestRegisterDynamicDataset:
    """Test dynamic dataset registration."""

    def test_register_dynamic_dataset(self):
        """Test registering a dynamically discovered dataset."""
        # Clear any existing datasets
        AVAILABLE_DATASETS.clear()
        
        neuron_data = {
            "database": "allen",
            "id": "12345",
            "name": "Test Neuron",
            "source": "Allen Brain Atlas",
            "structure_area": "VISp",
            "species": "mouse",
            "format": "swc",
            "atlas": "allen_mouse_25um",
            "data_type": "streamlines",
        }
        
        dataset_id = register_dynamic_dataset(neuron_data)
        
        assert dataset_id == "allen_12345"
        assert dataset_id in AVAILABLE_DATASETS
        assert AVAILABLE_DATASETS[dataset_id]["name"] == "Test Neuron"
        assert AVAILABLE_DATASETS[dataset_id]["species"] == "mouse"
        assert AVAILABLE_DATASETS[dataset_id]["data_type"] == "streamlines"
        assert AVAILABLE_DATASETS[dataset_id]["api_source"] == "allen"
        assert AVAILABLE_DATASETS[dataset_id]["neuron_id"] == "12345"
        
        # Cleanup
        AVAILABLE_DATASETS.clear()

    def test_register_dynamic_dataset_defaults(self):
        """Test registration with minimal data (uses defaults)."""
        AVAILABLE_DATASETS.clear()
        
        neuron_data = {
            "database": "mouselight",
            "id": "AA0001",
        }
        
        dataset_id = register_dynamic_dataset(neuron_data)
        
        assert dataset_id == "mouselight_AA0001"
        assert AVAILABLE_DATASETS[dataset_id]["atlas"] == "allen_mouse_25um"
        assert AVAILABLE_DATASETS[dataset_id]["format"] == "swc"
        assert AVAILABLE_DATASETS[dataset_id]["data_type"] == "streamlines"
        
        # Cleanup
        AVAILABLE_DATASETS.clear()


class TestGetAvailableDatasets:
    """Test getting available datasets with filtering."""

    def test_get_available_datasets_empty(self):
        """Test getting datasets when none are registered."""
        AVAILABLE_DATASETS.clear()
        datasets = get_available_datasets()
        assert isinstance(datasets, dict)
        assert len(datasets) == 0

    def test_get_available_datasets_filtered(self):
        """Test filtering datasets by species and data type."""
        AVAILABLE_DATASETS.clear()
        
        # Register test datasets
        register_dynamic_dataset({
            "database": "allen",
            "id": "1",
            "name": "Mouse Neuron",
            "species": "mouse",
            "data_type": "streamlines",
        })
        register_dynamic_dataset({
            "database": "allen",
            "id": "2",
            "name": "Fish Neuron",
            "species": "fish",
            "data_type": "points",
        })
        
        # Filter by species
        mouse_datasets = get_available_datasets(species="mouse")
        assert len(mouse_datasets) == 1
        assert "allen_1" in mouse_datasets
        
        # Filter by data type
        streamline_datasets = get_available_datasets(data_type="streamlines")
        assert len(streamline_datasets) == 1
        assert "allen_1" in streamline_datasets
        
        # Filter by both
        filtered = get_available_datasets(species="mouse", data_type="streamlines")
        assert len(filtered) == 1
        assert "allen_1" in filtered
        
        # Cleanup
        AVAILABLE_DATASETS.clear()


class TestGetDownloadedDatasets:
    """Test getting list of downloaded datasets."""

    def test_get_downloaded_datasets_empty(self, tmp_path, monkeypatch):
        """Test when no datasets are downloaded."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        downloaded = get_downloaded_datasets()
        assert isinstance(downloaded, list)
        assert len(downloaded) == 0

    def test_get_downloaded_datasets_with_data(self, tmp_path, monkeypatch):
        """Test getting downloaded datasets when they exist."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        # Create a mock downloaded dataset
        dataset_dir = datasets_dir / "test_dataset"
        dataset_dir.mkdir()
        
        metadata = {
            "dataset_id": "test_dataset",
            "name": "Test Dataset",
            "format": "swc",
            "file_name": "data.swc",  # Required for get_downloaded_datasets to recognize it
        }
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata))
        (dataset_dir / "data.swc").write_text("# SWC file\n1 1 0.0 0.0 0.0 1.0 -1\n")
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        downloaded = get_downloaded_datasets()
        assert isinstance(downloaded, list)
        assert "test_dataset" in downloaded


class TestGetDatasetPath:
    """Test getting dataset path."""

    def test_get_dataset_path_exists(self, tmp_path, monkeypatch):
        """Test getting path for existing dataset."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        dataset_dir = datasets_dir / "test_dataset"
        dataset_dir.mkdir()
        
        # Create metadata.json (required by get_dataset_path)
        metadata = {"dataset_id": "test_dataset"}
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata))
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        from brainrender_napari.utils.download_datasets import get_dataset_path
        path = get_dataset_path("test_dataset")
        assert path == dataset_dir

    def test_get_dataset_path_not_exists(self, tmp_path, monkeypatch):
        """Test getting path for non-existent dataset."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        from brainrender_napari.utils.download_datasets import get_dataset_path
        path = get_dataset_path("nonexistent")
        assert path is None


class TestLoadDatasetData:
    """Test loading dataset data files."""

    def test_load_dataset_data_swc(self, tmp_path, monkeypatch):
        """Test loading SWC file."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        dataset_dir = datasets_dir / "test_swc"
        dataset_dir.mkdir()
        
        # Create SWC file
        swc_content = """# SWC file format
1 1 0.0 0.0 0.0 1.0 -1
2 2 10.0 10.0 10.0 1.5 1
3 2 20.0 20.0 20.0 1.5 2
"""
        swc_file = dataset_dir / "test.swc"
        swc_file.write_text(swc_content)
        
        metadata = {
            "dataset_id": "test_swc",
            "format": "swc",
            "file_name": "test.swc",
        }
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata))
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        data = load_dataset_data("test_swc")
        
        assert isinstance(data, dict)
        assert "points" in data
        assert "connections" in data
        assert isinstance(data["points"], np.ndarray)
        assert len(data["points"]) == 3
        assert data["points"].shape[1] == 3  # x, y, z coordinates

    def test_load_dataset_data_npy(self, tmp_path, monkeypatch):
        """Test loading NPY file."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        dataset_dir = datasets_dir / "test_npy"
        dataset_dir.mkdir()
        
        # Create NPY file
        test_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        npy_file = dataset_dir / "data.npy"
        np.save(npy_file, test_data)
        
        metadata = {
            "dataset_id": "test_npy",
            "format": "npy",
            "file_name": "data.npy",
        }
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata))
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        data = load_dataset_data("test_npy")
        
        assert isinstance(data, np.ndarray)
        np.testing.assert_array_equal(data, test_data)

    def test_load_dataset_data_csv(self, tmp_path, monkeypatch):
        """Test loading CSV file."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        dataset_dir = datasets_dir / "test_csv"
        dataset_dir.mkdir()
        
        # Create CSV file
        csv_content = """x,y,z
1.0,2.0,3.0
4.0,5.0,6.0
7.0,8.0,9.0
"""
        csv_file = dataset_dir / "data.csv"
        csv_file.write_text(csv_content)
        
        metadata = {
            "dataset_id": "test_csv",
            "format": "csv",
            "file_name": "data.csv",
        }
        (dataset_dir / "metadata.json").write_text(json.dumps(metadata))
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        data = load_dataset_data("test_csv")
        
        assert isinstance(data, np.ndarray)
        assert len(data) == 3
        assert data.shape[1] == 3

    def test_load_dataset_data_not_found(self, tmp_path, monkeypatch):
        """Test loading non-existent dataset."""
        datasets_dir = tmp_path / ".brainglobe" / "datasets"
        datasets_dir.mkdir(parents=True)
        
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        with pytest.raises(ValueError, match="Dataset 'nonexistent' is not downloaded"):
            load_dataset_data("nonexistent")
