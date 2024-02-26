import pytest
from brainglobe_atlasapi import BrainGlobeAtlas
from napari.layers import Image, Labels
from numpy import all, allclose
from qtpy.QtCore import QEvent, QPoint, Qt
from qtpy.QtGui import QMouseEvent

from brainrender_napari.napari_atlas_representation import (
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

    assert (
        atlas_representation._on_mouse_move in annotation.mouse_move_callbacks
    )
    assert (
        atlas_representation._on_mouse_move in reference.mouse_move_callbacks
    )

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


def test_add_additional_reference(make_napari_viewer):
    viewer = make_napari_viewer()
    atlas_name = "mpin_zfish_1um"
    additional_reference_name = "GAD1b"
    atlas = BrainGlobeAtlas(atlas_name=atlas_name)

    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_additional_reference(additional_reference_name)

    additional_reference = viewer.layers[0]
    assert len(viewer.layers) == 1
    assert (
        additional_reference.name
        == f"{atlas_name}_{additional_reference_name}_reference"
    )
    assert (
        atlas_representation._on_mouse_move
        in additional_reference.mouse_move_callbacks
    )


@pytest.mark.parametrize(
    "cursor_position, expected_tooltip_text",
    [
        ((6500.0, 4298.5, 9057.6), "Caudoputamen | Left"),
        ((-1000, 0, 0), ""),  # outside image
    ],
)
def test_viewer_tooltip(
    make_napari_viewer, mocker, cursor_position, expected_tooltip_text
):
    """Checks that the custom callback for mouse movement sets the expected
    tooltip text."""
    viewer = make_napari_viewer()
    atlas_name = "allen_mouse_100um"
    atlas = BrainGlobeAtlas(atlas_name=atlas_name)
    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_to_viewer()
    annotation = viewer.layers[1]

    event = QMouseEvent(
        QEvent.MouseMove,
        QPoint(0, 0),  # any pos will do to check text
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # a slight hacky mock of event.pos to circumvent
    # the napari read-only wrapper around qt events
    mock_event = mocker.patch.object(event, "pos", return_value=(50, 50))
    viewer.cursor.position = cursor_position
    atlas_representation._on_mouse_move(annotation, mock_event)
    assert atlas_representation._tooltip.text() == expected_tooltip_text


def test_too_quick_mouse_move_keyerror(make_napari_viewer, mocker):
    """Quickly moving the cursor position can cause
    structure_from_coords to be called with a background label.
    This test checks that we handle that case gracefully."""
    viewer = make_napari_viewer()
    atlas_name = "allen_mouse_100um"
    atlas = BrainGlobeAtlas(atlas_name=atlas_name)
    atlas_representation = NapariAtlasRepresentation(atlas, viewer)
    atlas_representation.add_to_viewer()
    annotation = viewer.layers[1]

    event = QMouseEvent(
        QEvent.MouseMove,
        QPoint(0, 0),  # any pos will do to check text
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # a slight hacky mock of event.pos to circumvent
    # the napari read-only wrapper around qt events
    mock_event = mocker.patch.object(event, "pos", return_value=(0, 0))
    viewer.cursor.position = (6500.0, 4298.5, 9057.6)

    # Mock the case where a quick mouse move calls structure_from_coords
    # with key 0 (background)
    mock_structure_from_coords = mocker.patch.object(
        atlas_representation.bg_atlas,
        "structure_from_coords",
        side_effect=KeyError(),
    )

    atlas_representation._on_mouse_move(annotation, mock_event)
    mock_structure_from_coords.assert_called_once()
    assert atlas_representation._tooltip.text() == ""
