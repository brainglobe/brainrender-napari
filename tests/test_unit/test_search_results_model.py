"""Tests for search results table model."""

from qtpy.QtCore import QModelIndex, Qt

from brainrender_napari.data_models.search_results_model import SearchResultsModel


def test_search_results_model_init():
    """Test initializing search results model."""
    results = [
        {
            "id": "123",
            "name": "Test Neuron",
            "source": "Allen",
            "structure_area": "VISp",
            "species": "mouse",
            "database": "allen",
        }
    ]
    model = SearchResultsModel(results)
    
    assert model.rowCount() == 1
    assert model.columnCount() == 6


def test_search_results_model_data():
    """Test getting data from model."""
    results = [
        {
            "id": "123",
            "name": "Test Neuron",
            "source": "Allen Brain Atlas",
            "structure_area": "VISp",
            "structure_name": "Primary visual area",
            "species": "mouse",
            "database": "allen",
        }
    ]
    model = SearchResultsModel(results)
    
    # Test ID column
    index = model.index(0, 0)
    assert model.data(index) == "123"
    
    # Test Name column
    index = model.index(0, 1)
    assert model.data(index) == "Test Neuron"
    
    # Test Source column
    index = model.index(0, 2)
    assert model.data(index) == "Allen Brain Atlas"
    
    # Test Structure Area column
    index = model.index(0, 3)
    assert model.data(index) == "VISp"
    
    # Test Species column
    index = model.index(0, 4)
    assert model.data(index) == "mouse"
    
    # Test Database column
    index = model.index(0, 5)
    assert model.data(index) == "allen"


def test_search_results_model_header():
    """Test model header data."""
    model = SearchResultsModel([])
    
    assert model.headerData(0, Qt.Orientation.Horizontal, Qt.DisplayRole) == "ID"
    assert model.headerData(1, Qt.Orientation.Horizontal, Qt.DisplayRole) == "Name"
    assert model.headerData(2, Qt.Orientation.Horizontal, Qt.DisplayRole) == "Source"
    assert model.headerData(3, Qt.Orientation.Horizontal, Qt.DisplayRole) == "Structure Area"
    assert model.headerData(4, Qt.Orientation.Horizontal, Qt.DisplayRole) == "Species"
    assert model.headerData(5, Qt.Orientation.Horizontal, Qt.DisplayRole) == "Database"


def test_search_results_model_get_neuron_at_index():
    """Test getting full neuron data at index."""
    neuron_data = {
        "id": "456",
        "name": "Another Neuron",
        "source": "MouseLight",
        "structure_area": "MOs",
        "species": "mouse",
        "database": "mouselight",
    }
    model = SearchResultsModel([neuron_data])
    
    index = model.index(0, 0)
    retrieved = model.get_neuron_at_index(index)
    
    assert retrieved == neuron_data


def test_search_results_model_get_neuron_at_index_invalid():
    """Test getting neuron data with invalid index."""
    model = SearchResultsModel([])
    
    invalid_index = QModelIndex()
    result = model.get_neuron_at_index(invalid_index)
    
    assert result is None


def test_search_results_model_multiple_results():
    """Test model with multiple search results."""
    results = [
        {"id": "1", "name": "Neuron 1", "database": "allen"},
        {"id": "2", "name": "Neuron 2", "database": "allen"},
        {"id": "3", "name": "Neuron 3", "database": "mouselight"},
    ]
    model = SearchResultsModel(results)
    
    assert model.rowCount() == 3
    
    assert model.data(model.index(0, 1)) == "Neuron 1"
    assert model.data(model.index(1, 1)) == "Neuron 2"
    assert model.data(model.index(2, 1)) == "Neuron 3"


def test_search_results_model_missing_fields():
    """Test model handles missing optional fields."""
    results = [
        {
            "id": "789",
            "database": "allen",
            # Missing name, source, structure_area, species
        }
    ]
    model = SearchResultsModel(results)
    
    assert model.data(model.index(0, 0)) == "789"
    assert model.data(model.index(0, 1)) == "Unknown"
    assert model.data(model.index(0, 2)) == "Unknown"
    assert model.data(model.index(0, 3)) == "N/A"
    assert model.data(model.index(0, 4)) == "Unknown"
    assert model.data(model.index(0, 5)) == "allen"
