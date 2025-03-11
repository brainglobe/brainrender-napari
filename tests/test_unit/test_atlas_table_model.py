import pytest
from napari.settings import get_settings
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel


@pytest.fixture
def atlas_table_model(mocker):
    mock_view = mocker.Mock(spec=["get_tooltip_text"])
    return AtlasTableModel(view_type=mock_view)


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


def test_model_header_invalid_view():
    """Checks that the model complains
    if its view_type is not valid."""
    with pytest.raises(AssertionError) as error:
        _ = AtlasTableModel(view_type=None)
        assert "Views" in error
        assert "classmethod" in error
        assert "get_tooltip_text" in error


def test_background_color_for_outdated_atlas(atlas_table_model, mock_newer_atlas_version_available):
    """
    For out-of-date atlas (local_version=“1.1”, latest_version=“1.2”),
    Test to verify that the amber color is returned according to the theme.
    """
    index = atlas_table_model.index(0, 0)
    theme = get_settings().appearance.theme

    index = atlas_table_model.index(row, 0)
    brush = atlas_table_model.data(index, role=Qt.BackgroundRole)
    assert isinstance(brush, QBrush)

    if theme == "dark":
        expected_rgb = (255, 140, 0)  # dark amber
    else:
        expected_rgb = (255, 191, 0)  # light amber

    # Retrieve QColor from the retrieved QBrush
    # and verify RGB (ignoring alpha values)
    actual_rgb = brush.color().getRgb()[:3]
    assert (
        actual_rgb == expected_rgb
    ), f"Expected RGB {expected_rgb}, but got {actual_rgb}"