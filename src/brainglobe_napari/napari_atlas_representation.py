from dataclasses import dataclass

from bg_atlasapi import BrainGlobeAtlas
from meshio import Mesh
from napari.viewer import Viewer


@dataclass
class NapariAtlasRepresentation:
    """Representation of a BG atlas as napari layers"""

    bg_atlas: BrainGlobeAtlas
    viewer: Viewer

    def add_to_viewer(self):
        """Adds the annotation and reference images,
        and the top-level "root" mesh, to the viewer, in that order.

        The reference image's visibility is off, the others' is on.
        """
        self.viewer.add_image(
            self.bg_atlas.reference,
            name=f"{self.bg_atlas.atlas_name}_reference",
            visible=False,
        )
        self.viewer.add_labels(
            self.bg_atlas.annotation,
            name=f"{self.bg_atlas.atlas_name}_annotation",
        )

        root_mesh = self.bg_atlas.mesh_from_structure("root")
        self._add_mesh(root_mesh, name=f"{self.bg_atlas.atlas_name}_mesh")

    def _add_mesh(self, mesh: Mesh, name: str = None):
        """Helper function to add a mesh as a surface layer to the viewer.

        mesh: the mesh to add
        name: name for the surface layer
        """
        points = mesh.points
        for i in range(3):
            points[:, i] /= self.bg_atlas.resolution[i]
        cells = mesh.cells[0].data
        self.viewer.add_surface(
            (points, cells),
            name=name,
            opacity=0.4,
            blending="translucent_no_depth",
        )
