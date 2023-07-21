import pytest
from bg_atlasapi import BrainGlobeAtlas
from napari.layers import Image, Labels
from numpy import all, allclose

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


@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        ("example_mouse_100um"),
        ("allen_mouse_100um"),
        ("osten_mouse_100um"),
    ],
)
def test_add_structure_to_viewer(make_napari_viewer, expected_atlas_name):
    """Check that the root mesh extents __roughly__ match the size
    of the annnotations image."""
    viewer = make_napari_viewer()
    atlas = BrainGlobeAtlas(atlas_name=expected_atlas_name)

    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_structure_to_viewer("root")
    assert len(viewer.layers) == 1
    mesh = viewer.layers[0]

    # add other images so we can check mesh extents
    atlas_representation.add_to_viewer()
    annotation = viewer.layers[1]

    # check that in world coordinates, the root mesh fits within
    # a resolution step of the entire annotations image (not just
    # the annotations themselves) but that the mesh extents are more
    # than 75% of the annotation image extents.
    assert all(
        mesh.extent.world[0] > annotation.extent.world[0] - atlas.resolution
    )
    assert all(
        mesh.extent.world[1] < annotation.extent.world[1] + atlas.resolution
    )
    assert all(
        mesh.extent.world[1] - mesh.extent.world[0]
        > 0.75 * (annotation.extent.world[1] - annotation.extent.world[0])
    )


def test_structure_color(make_napari_viewer):
    """Checks that the default colour of a structure
    is propagated correctly to the corresponding napari layer
    """
    viewer = make_napari_viewer()
    atlas = BrainGlobeAtlas(atlas_name="allen_mouse_100um")

    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_structure_to_viewer("CTXsp")

    expected_RGB = atlas.structures["CTXsp"]["rgb_triplet"]
    actual_rgb = viewer.layers[0].vertex_colors[0]

    for a, e in zip(actual_rgb, expected_RGB):
        assert a * 255 == e
