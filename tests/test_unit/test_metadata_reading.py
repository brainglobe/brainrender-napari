import pytest
from brainglobe_atlasapi import BrainGlobeAtlas

from brainrender_napari.utils.load_user_data import (
    read_atlas_metadata_from_file,
    read_atlas_structures_from_file,
)


def test_metadata_reading():
    """Checks that metadata read from file matches original metadata"""
    atlas = BrainGlobeAtlas("example_mouse_100um")
    expected_metadata = atlas.metadata
    file_metadata = read_atlas_metadata_from_file(atlas.atlas_name)
    assert file_metadata == expected_metadata


@pytest.mark.parametrize(
    "atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
        "osten_mouse_100um",
    ],
)
def test_structures_reading(atlas_name):
    """Checks that structures read from file match original structures."""
    atlas = BrainGlobeAtlas(atlas_name)
    expected_structures = atlas.structures
    file_structures = read_atlas_structures_from_file(atlas_name)

    # Compare the structures
    assert file_structures == expected_structures


def test_structures_reading_contains_required_keys():
    """Checks that structure data contains expected keys."""
    structures = read_atlas_structures_from_file("allen_mouse_100um")

    # Verify it's a dictionary
    assert isinstance(structures, dict)

    # Check that structures have expected properties
    # Get any structure to test
    if structures:
        first_structure_key = list(structures.keys())[0]
        structure = structures[first_structure_key]

        # Verify expected keys exist
        assert "acronym" in structure or "name" in structure


def test_structures_reading_root_structure():
    """Checks that the root structure is present in the structures file."""
    structures = read_atlas_structures_from_file("allen_mouse_100um")

    # Root should always exist
    assert "root" in structures or 997 in structures


@pytest.mark.parametrize(
    "atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
    ],
)
def test_metadata_and_structures_consistency(atlas_name):
    """Verify metadata and structures can both be read for same atlas."""
    # Both operations should succeed without errors
    metadata = read_atlas_metadata_from_file(atlas_name)
    structures = read_atlas_structures_from_file(atlas_name)

    assert metadata is not None
    assert structures is not None
    assert isinstance(metadata, dict)
    assert isinstance(structures, dict)
