import pytest
from brainglobe_atlasapi import BrainGlobeAtlas

from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
    read_atlas_structures_from_file,
)


def test_metadata_reading():
    """Checks that metadata read via the atlas API is the atlas' own
    metadata, minus the nested entries that aren't useful in a tooltip.
    """
    atlas = BrainGlobeAtlas("example_mouse_100um")
    file_metadata = read_atlas_metadata_from_file(atlas.atlas_name)

    dropped_keys = {
        "coordinate_space",
        "terminology",
        "annotation_set",
        "template",
    }
    assert dropped_keys.isdisjoint(file_metadata)
    expected = {
        key: value
        for key, value in atlas.metadata.items()
        if key not in dropped_keys and key != "additional_references"
    }
    assert {
        key: value
        for key, value in file_metadata.items()
        if key != "additional_references"
    } == expected


def test_additional_references_are_flattened_to_names():
    """The additional references are dicts in the atlas metadata, but only
    their names are shown in the UI. `conftest` mocks one onto the example
    atlas.
    """
    atlas = BrainGlobeAtlas("example_mouse_100um")
    expected_names = [
        reference["name"]
        for reference in atlas.metadata["additional_references"]
    ]
    assert expected_names, "test setup should mock an additional reference"

    file_metadata = read_atlas_metadata_from_file(atlas.atlas_name)
    assert file_metadata["additional_references"] == expected_names


def test_structures_reading():
    """Structures are read via the atlas API and passed through as-is."""
    atlas = BrainGlobeAtlas("example_mouse_100um")
    assert (
        read_atlas_structures_from_file(atlas.atlas_name)
        == atlas.structures_list
    )


@pytest.mark.parametrize(
    "read_from_file",
    [read_atlas_metadata_from_file, read_atlas_structures_from_file],
)
def test_reads_are_cached(mocker, read_from_file):
    """Both readers instantiate a `BrainGlobeAtlas`, which is expensive, so
    repeated reads of the same atlas should be served from the cache."""
    atlas_mock = mocker.patch(
        "brainrender_napari.utils.load_user_data.BrainGlobeAtlas"
    )
    atlas_mock.return_value.metadata = {"name": "example_mouse_100um"}
    atlas_mock.return_value.structures_list = []

    read_from_file("example_mouse_100um")
    read_from_file("example_mouse_100um")

    atlas_mock.assert_called_once_with(
        atlas_name="example_mouse_100um", check_latest=False
    )
