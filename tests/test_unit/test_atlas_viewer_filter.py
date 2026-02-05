import pytest
from brainglobe_atlasapi.list_atlases import get_downloaded_atlases

from brainrender_napari.widgets.atlas_viewer_view import AtlasViewerView


@pytest.fixture
def atlas_viewer_view(qtbot):
    """Fixture to provide an atlas viewer view with its integrated filter."""
    return AtlasViewerView()


def filter_data(query, data):
    """Helper function to filter data based on query."""
    return list(filter(lambda row_attr: query.lower() in row_attr.lower(), data))


def test_filter_initialization(atlas_viewer_view):
    """Test that the filter widget is properly initialized."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    # Create a filter widget
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    assert filter_widget.atlas_viewer_view is not None
    assert filter_widget.query_field is not None
    assert filter_widget.column_field is not None
    assert filter_widget.query_field.placeholderText() == "Search..."
    assert filter_widget.column_field.itemText(0) == "Any"


def test_no_filter_shows_all_downloaded(atlas_viewer_view):
    """Test that with no filter, all downloaded atlases are shown."""
    atlas_viewer_view.proxy_model.setFilterFixedString("")
    downloaded_atlases = get_downloaded_atlases()
    assert atlas_viewer_view.proxy_model.rowCount() == len(downloaded_atlases)


@pytest.mark.parametrize(
    "query, expected_min_results",
    [
        ("mouse", 2),  # Should find at least example_mouse and allen_mouse
        ("100um", 2),  # Should find multiple 100um atlases
        ("osten", 1),  # Should find osten_mouse_100um
    ],
)
def test_filter_query_any_column(atlas_viewer_view, query, expected_min_results):
    """Test filtering with 'Any' column selected."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Set filter to "Any" column
    filter_widget.column_field.setCurrentText("Any")
    filter_widget.query_field.setText(query)
    filter_widget.apply()
    
    assert atlas_viewer_view.proxy_model.rowCount() >= expected_min_results


def test_filter_specific_column(atlas_viewer_view):
    """Test filtering on a specific column."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Set filter to "Atlas" column
    filter_widget.column_field.setCurrentText("Atlas")
    filter_widget.query_field.setText("example")
    filter_widget.apply()
    
    # Should find example_mouse_100um
    assert atlas_viewer_view.proxy_model.rowCount() >= 1


def test_filter_case_insensitive(atlas_viewer_view):
    """Test that filtering is case-insensitive."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Test lowercase
    filter_widget.query_field.setText("mouse")
    filter_widget.apply()
    lowercase_results = atlas_viewer_view.proxy_model.rowCount()
    
    # Test uppercase
    filter_widget.query_field.setText("MOUSE")
    filter_widget.apply()
    uppercase_results = atlas_viewer_view.proxy_model.rowCount()
    
    # Test mixed case
    filter_widget.query_field.setText("MoUsE")
    filter_widget.apply()
    mixedcase_results = atlas_viewer_view.proxy_model.rowCount()
    
    # All should return the same results
    assert lowercase_results == uppercase_results == mixedcase_results


def test_filter_clears_results(atlas_viewer_view):
    """Test that clearing the filter restores all results."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Get initial count
    initial_count = atlas_viewer_view.proxy_model.rowCount()
    
    # Apply a filter
    filter_widget.query_field.setText("osten")
    filter_widget.apply()
    filtered_count = atlas_viewer_view.proxy_model.rowCount()
    
    # Verify filter reduced results
    assert filtered_count < initial_count
    
    # Clear the filter
    filter_widget.query_field.setText("")
    filter_widget.apply()
    
    # Verify we're back to initial count
    assert atlas_viewer_view.proxy_model.rowCount() == initial_count


def test_filter_no_matches(atlas_viewer_view):
    """Test filtering with a query that matches nothing."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    filter_widget.query_field.setText("xyznonexistentatlas123")
    filter_widget.apply()
    
    assert atlas_viewer_view.proxy_model.rowCount() == 0


def test_filter_and_selected_atlas_name(atlas_viewer_view):
    """Test that filtering works correctly with selection."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Apply a filter for osten
    filter_widget.query_field.setText("osten")
    filter_widget.apply()
    
    # Select the first (and likely only) result
    atlas_viewer_view.selectRow(0)
    
    # Verify the selected atlas contains "osten"
    selected_name = atlas_viewer_view.selected_atlas_name()
    assert selected_name is not None
    assert "osten" in selected_name.lower()


def test_filter_column_selector_excludes_hidden_columns(atlas_viewer_view):
    """Test that hidden columns are not in the column selector dropdown."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Get all items in the column selector
    column_items = [
        filter_widget.column_field.itemText(i)
        for i in range(filter_widget.column_field.count())
    ]
    
    # Verify hidden columns are not in the dropdown
    for hidden_col in atlas_viewer_view.hidden_columns:
        assert hidden_col not in column_items


def test_filter_signal_connection(atlas_viewer_view):
    """Test that text changes trigger the apply method."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Get initial count
    initial_count = atlas_viewer_view.proxy_model.rowCount()
    
    # Change text (this should automatically call apply via signal)
    filter_widget.query_field.setText("example")
    
    # Verify the filter was applied
    assert atlas_viewer_view.proxy_model.rowCount() < initial_count


def test_filter_column_change_triggers_apply(atlas_viewer_view):
    """Test that changing the column dropdown triggers reapplication of filter."""
    from brainrender_napari.widgets.atlas_viewer_filter import AtlasViewerFilter
    
    filter_widget = AtlasViewerFilter(atlas_viewer_view)
    
    # Set a search query
    filter_widget.query_field.setText("mouse")
    
    # Get count with "Any" column
    any_column_count = atlas_viewer_view.proxy_model.rowCount()
    
    # Change to "Atlas" column
    filter_widget.column_field.setCurrentText("Atlas")
    
    # Get count with "Atlas" column
    atlas_column_count = atlas_viewer_view.proxy_model.rowCount()
    
    # Both should have results (might be the same or different)
    assert any_column_count > 0
    assert atlas_column_count > 0
