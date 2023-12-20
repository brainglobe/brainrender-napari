import pytest
from qtpy.QtCore import Qt

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel


@pytest.fixture
def atlas_table_model():
    return AtlasTableModel()


@pytest.mark.parametrize(
    "column, expected_header",
    [
        (0, "Raw name"),
        (1, "Atlas"),
        (2, "Local version"),
        (3, "Latest version"),
    ],
)
def test_model_header(atlas_table_model, column, expected_header):
    """Check the table model has expected header data
    both via the function and the member variable."""
    assert (
        atlas_table_model.headerData(
            column, Qt.Orientation.Horizontal, Qt.DisplayRole
        )
        == expected_header
    )
    assert atlas_table_model.column_headers[column] == expected_header


def test_model_header_invalid_column(atlas_table_model):
    """Check the table model throws a value error for invalid column"""
    invalid_column = 4
    with pytest.raises(ValueError):
        atlas_table_model.headerData(
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
