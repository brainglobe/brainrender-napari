from dataclasses import dataclass

from bg_atlasapi import BrainGlobeAtlas
from napari.viewer import Viewer


@dataclass
class NapariAtlasRepresentation:
    """Representation of a BG atlas as napari layers"""

    bg_atlas: BrainGlobeAtlas

    def add_to_viewer(self, viewer: Viewer):
        """Adds the annotation and reference images to a viewer.

        The annotation image is on top, and visible,
        while the reference image is below it and invisible.
        """
        viewer.add_image(
            self.bg_atlas.reference,
            name=f"{self.bg_atlas.atlas_name}_reference",
            visible=False,
        )
        viewer.add_labels(
            self.bg_atlas.annotation,
            name=f"{self.bg_atlas.atlas_name}_annotation",
        )
