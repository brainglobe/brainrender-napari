import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.layers import Image, Labels, Surface
from numpy import allclose

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
    Also checks that reference and annotation image have the same extents.
    """
    viewer = make_napari_viewer()
    atlas = BrainGlobeAtlas(atlas_name=expected_atlas_name)
    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_to_viewer()
    assert len(viewer.layers) == 3

    mesh, annotation, reference = (
        viewer.layers[2],
        viewer.layers[1],
        viewer.layers[0],
    )

    assert mesh.name == f"{expected_atlas_name}_mesh"
    assert annotation.name == f"{expected_atlas_name}_annotation"
    assert reference.name == f"{expected_atlas_name}_reference"

    assert isinstance(mesh, Surface)
    assert isinstance(annotation, Labels)
    assert isinstance(reference, Image)

    assert allclose(annotation.extent.world, reference.extent.world)
