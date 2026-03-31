"""Tests for the species filter widget."""

import pytest
from qtpy.QtCore import QSortFilterProxyModel

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel
from brainrender_napari.widgets.species_filter_widget import (
    SpeciesFilterWidget,
)


@pytest.fixture
def species_filter_setup(qtbot, mocker):
    """Create a species filter widget with mocked model."""
    mock_view = mocker.Mock(spec=["get_tooltip_text"])
    source_model = AtlasTableModel(view_type=mock_view)
    proxy_model = QSortFilterProxyModel()
    proxy_model.setSourceModel(source_model)

    widget = SpeciesFilterWidget(
        proxy_model=proxy_model,
        source_model=source_model,
    )
    qtbot.addWidget(widget)
    return widget, proxy_model, source_model


def test_species_filter_has_all_species_option(species_filter_setup):
    """Check that 'All Species' is the first item."""
    widget, _, _ = species_filter_setup
    assert widget.combo.itemText(0) == "All Species"


def test_species_filter_has_unique_species(species_filter_setup):
    """Check that the combo has species from atlas data."""
    widget, _, source_model = species_filter_setup
    expected_species = source_model.get_unique_species()
    for species in expected_species:
        assert widget.combo.findText(species) >= 0


def test_species_filter_all_species_clears_filter(species_filter_setup):
    """Check that selecting 'All Species' clears the filter."""
    widget, proxy_model, _ = species_filter_setup
    widget.combo.setCurrentText("All Species")
    # Should show all rows
    assert proxy_model.rowCount() == proxy_model.sourceModel().rowCount()


def test_species_filter_filters_by_species(species_filter_setup):
    """Check that selecting a specific species filters the rows."""
    widget, proxy_model, source_model = species_filter_setup
    species_list = source_model.get_unique_species()
    if len(species_list) > 0:
        test_species = species_list[0]
        widget.combo.setCurrentText(test_species)
        # All visible rows should have this species
        species_col = source_model.column_headers.index("Species")
        for row in range(proxy_model.rowCount()):
            index = proxy_model.index(row, species_col)
            assert proxy_model.data(index) == test_species


def test_species_filter_refresh(species_filter_setup):
    """Check that refresh repopulates the combo box."""
    widget, _, _ = species_filter_setup
    original_count = widget.combo.count()
    widget.refresh()
    assert widget.combo.count() == original_count


def test_species_changed_signal(species_filter_setup, qtbot):
    """Check that changing species emits species_changed signal."""
    widget, _, source_model = species_filter_setup
    species_list = source_model.get_unique_species()
    if len(species_list) > 0:
        with qtbot.waitSignal(widget.species_changed, timeout=1000):
            widget.combo.setCurrentText(species_list[0])
