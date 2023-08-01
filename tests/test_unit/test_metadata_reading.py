from bg_atlasapi import BrainGlobeAtlas

from brainrender_napari.atlas_viewer_utils import read_atlas_metadata_from_file


def test_metadata_reading():
    """Checks that metadata read from file matches original metadata"""
    atlas = BrainGlobeAtlas("example_mouse_100um")
    expected_metadata = atlas.metadata
    file_metadata = read_atlas_metadata_from_file(atlas.atlas_name)
    assert file_metadata == expected_metadata
