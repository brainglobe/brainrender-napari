import pytest
from brainglobe_atlasapi import list_atlases

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


@pytest.fixture
def atlas_manager_view(qtbot):
    return AtlasManagerView()


def test_filter_atlas_manager(atlas_manager_view):
    print(f"Downloaded atlases: {list_atlases.get_downloaded_atlases()}\n")
    print(f"Source model data: {atlas_manager_view.source_model._data}\n")
    print(
        f"Source model row count: \
        {atlas_manager_view.source_model.rowCount()}\n"
    )

    # atlas_manager_view.source_model.refresh_data()
    assert atlas_manager_view.proxy_model.rowCount() == 3

    atlas_manager_view.proxy_model.setFilterFixedString("mouse")
    assert atlas_manager_view.proxy_model.rowCount() == 3

    atlas_manager_view.proxy_model.setFilterFixedString("example")
    assert atlas_manager_view.proxy_model.rowCount() == 1

    column_index = atlas_manager_view.source_model.column_headers.index(
        "Local version"
    )

    atlas_manager_view.proxy_model.setFilterKeyColumn(column_index)
    atlas_manager_view.proxy_model.setFilterFixedString("1.2")
    assert atlas_manager_view.proxy_model.rowCount() == 1
