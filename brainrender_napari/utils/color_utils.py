"""Utilities for building colormaps from atlas structure metadata."""

import numpy as np
from brainglobe_atlasapi import BrainGlobeAtlas


def build_colormap_from_structures(
    bg_atlas: BrainGlobeAtlas,
) -> dict:
    """Build a color dict mapping structure IDs to RGBA colours.

    Iterates over all structures in the atlas and maps each
    structure's integer ID to its normalised RGB triplet.
    Background (ID=0) is mapped to transparent.

    Parameters
    ----------
    bg_atlas : BrainGlobeAtlas
        A BrainGlobe atlas instance.

    Returns
    -------
    dict
        A dictionary mapping integer structure IDs to RGBA arrays
        (values normalised to 0.0–1.0) suitable for napari's
        Labels layer `color` parameter.
    """
    color_dict = {0: np.array([0.0, 0.0, 0.0, 0.0])}  # background

    for structure_id, structure_info in bg_atlas.structures.items():
        if isinstance(structure_id, int):
            rgb = structure_info.get("rgb_triplet", [128, 128, 128])
            color_dict[structure_id] = np.array(
                [rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 1.0]
            )

    return color_dict
