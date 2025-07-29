import pytest
from brainglobe_atlasapi.list_atlases import get_all_atlases_lastversions

from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView

all_atlases_names = get_all_atlases_lastversions().keys()
all_atlases_versions = get_all_atlases_lastversions().values()


@pytest.fixture
def atlas_manager_view(qtbot):
    return AtlasManagerView()


def filter_data(query, data):
    return list(filter(lambda row_attr: query in row_attr, data))


def test_no_filter(atlas_manager_view):
    atlas_manager_view.proxy_model.setFilterFixedString("")
    assert atlas_manager_view.proxy_model.rowCount() == len(all_atlases_names)


@pytest.mark.parametrize(
    "query, data, column_name",
    [
        ("mouse", all_atlases_names, "Any"),
        (
            "50",
            all_atlases_names,
            "Atlas",
        ),  # 50um or 500um is in the atlas name
        ("1.2", all_atlases_versions, "Latest version"),
    ],
)
def test_filter_query(atlas_manager_view, query, data, column_name):
    filtered_data = filter_data(query, data)

    if column_name == "Any":
        column_index = -1
    else:
        column_index = atlas_manager_view.source_model.column_headers.index(
            column_name
        )

    atlas_manager_view.proxy_model.setFilterFixedString(query)
    atlas_manager_view.proxy_model.setFilterKeyColumn(column_index)
    assert atlas_manager_view.proxy_model.rowCount() == len(filtered_data)


def test_filter_and_selected_name(atlas_manager_view):
    atlas_manager_view.proxy_model.setFilterFixedString("kim_dev_mouse")
    atlas_manager_view.proxy_model.setFilterKeyColumn(-1)
    atlas_manager_view.selectRow(0)
    assert "kim_dev_mouse" in atlas_manager_view.selected_atlas_name()
