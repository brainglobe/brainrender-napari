import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.layers import Image, Labels, Surface

from brainglobe_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)


@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        ("example_mouse_100um"),
        ("allen_mouse_100um"),
        ("osten_mouse_100um"),
    ],
)
def test_add_to_viewer(make_napari_viewer, expected_atlas_name):
    """Checks that calling add_to_viewer() adds the expected number of
    layers, of the expected type and with the expected name.
    """
    viewer = make_napari_viewer()
    atlas = BrainGlobeAtlas(atlas_name=expected_atlas_name)
    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_to_viewer()
    assert len(viewer.layers) == 3

    assert viewer.layers[2].name == f"{expected_atlas_name}_mesh"
    assert viewer.layers[1].name == f"{expected_atlas_name}_annotation"
    assert viewer.layers[0].name == f"{expected_atlas_name}_reference"

    assert isinstance(viewer.layers[2], Surface)
    assert isinstance(viewer.layers[1], Labels)
    assert isinstance(viewer.layers[0], Image)
