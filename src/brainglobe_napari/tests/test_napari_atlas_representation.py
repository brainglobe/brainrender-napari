from bg_atlasapi import BrainGlobeAtlas

from brainglobe_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)


def test_add_to_viewer(make_napari_viewer):
    viewer = make_napari_viewer()
    atlas_name = "allen_mouse_100um"
    atlas_representation = NapariAtlasRepresentation(
        BrainGlobeAtlas(atlas_name=atlas_name)
    )
    atlas_representation.add_to_viewer(viewer=viewer)
    assert len(viewer.layers) == 2
    assert viewer.layers[1].name == f"{atlas_name}_annotation"
    assert viewer.layers[0].name == f"{atlas_name}_reference"
