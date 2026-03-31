"""Tests for the color_utils module."""

import numpy as np
import pytest
from brainglobe_atlasapi import BrainGlobeAtlas

from brainrender_napari.utils.color_utils import (
    build_colormap_from_structures,
)


@pytest.mark.parametrize(
    "atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
    ],
)
def test_build_colormap_returns_dict(atlas_name):
    """Check that build_colormap_from_structures returns a dict."""
    atlas = BrainGlobeAtlas(atlas_name=atlas_name)
    color_dict = build_colormap_from_structures(atlas)
    assert isinstance(color_dict, dict)
    assert len(color_dict) > 0


def test_background_is_transparent():
    """Check that the background (ID=0) is mapped to transparent."""
    atlas = BrainGlobeAtlas(atlas_name="example_mouse_100um")
    color_dict = build_colormap_from_structures(atlas)
    assert 0 in color_dict
    np.testing.assert_array_almost_equal(
        color_dict[0], [0.0, 0.0, 0.0, 0.0]
    )


def test_colormap_values_are_normalized():
    """Check that all color values are in the range [0, 1]."""
    atlas = BrainGlobeAtlas(atlas_name="allen_mouse_100um")
    color_dict = build_colormap_from_structures(atlas)
    for structure_id, rgba in color_dict.items():
        assert len(rgba) == 4
        assert np.all(rgba >= 0.0)
        assert np.all(rgba <= 1.0)


def test_colormap_contains_known_structure():
    """Check that a known structure has the expected color."""
    atlas = BrainGlobeAtlas(atlas_name="allen_mouse_100um")
    color_dict = build_colormap_from_structures(atlas)

    # Get the structure info for 'root'
    root_info = atlas.structures["root"]
    root_id = root_info["id"]
    expected_rgb = root_info["rgb_triplet"]

    assert root_id in color_dict
    actual_rgba = color_dict[root_id]
    expected_rgba = np.array(
        [
            expected_rgb[0] / 255.0,
            expected_rgb[1] / 255.0,
            expected_rgb[2] / 255.0,
            1.0,
        ]
    )
    np.testing.assert_array_almost_equal(actual_rgba, expected_rgba)
