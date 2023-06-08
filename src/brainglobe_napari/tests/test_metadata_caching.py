from bg_atlasapi import BrainGlobeAtlas

from brainglobe_napari.atlas_viewer_utils import (
    read_atlas_metadata_cache,
    write_atlas_metadata_cache,
)


def test_metadata_caching():
    """Checks that metadata data read from cache matches original metadata"""
    atlas = BrainGlobeAtlas("example_mouse_100um")
    expected_metadata = atlas.metadata
    write_atlas_metadata_cache(atlas)
    cached_metadata = read_atlas_metadata_cache(atlas.atlas_name)
    assert cached_metadata == expected_metadata
