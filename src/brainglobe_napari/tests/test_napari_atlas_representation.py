import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.layers import Image, Labels, Surface
from numpy import allclose, alltrue

from brainglobe_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)


@pytest.mark.parametrize("anisotropic", [True, False])
@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        ("example_mouse_100um"),
        ("allen_mouse_100um"),
        ("osten_mouse_100um"),
    ],
)
def test_add_to_viewer(make_napari_viewer, expected_atlas_name, anisotropic):
    """Checks that calling add_to_viewer() adds the expected number of
    layers, of the expected type and with the expected name.
    Also checks that reference and annotation image have the same extents.
    """
    viewer = make_napari_viewer()
    atlas = BrainGlobeAtlas(atlas_name=expected_atlas_name)

    if anisotropic:
        # make atlas anisotropic
        atlas.metadata["resolution"][0] *= 3
        atlas.metadata["resolution"][1] *= 2
        atlas._annotation = atlas.annotation[
            0 : len(atlas.annotation) : 3, 0 : len(atlas.annotation[0]) : 2, :
        ]
        atlas._reference = atlas.reference[
            0 : len(atlas.reference) : 3, 0 : len(atlas.reference[0]) : 2, :
        ]

    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_to_viewer()
    assert len(viewer.layers) == 2

    annotation, reference = (
        viewer.layers[1],
        viewer.layers[0],
    )
    assert annotation.name == f"{expected_atlas_name}_annotation"
    assert reference.name == f"{expected_atlas_name}_reference"

    assert isinstance(annotation, Labels)
    assert isinstance(reference, Image)

    assert allclose(annotation.extent.world, reference.extent.world)
