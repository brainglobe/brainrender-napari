from dataclasses import dataclass

import numpy as np
from bg_atlasapi import BrainGlobeAtlas
from meshio import Mesh
from napari.viewer import Viewer


@dataclass
class NapariAtlasRepresentation:
    """Representation of a BG atlas as napari layers"""

    bg_atlas: BrainGlobeAtlas
    viewer: Viewer
    mesh_opacity: float = 0.4
    mesh_blending: str = "translucent_no_depth"

    def add_to_viewer(self):
        """Adds the reference and annotation images to the viewer.

        The reference image's visibility is off, the annotation's is on.
        """
        reference = self.viewer.add_image(
            self.bg_atlas.reference,
            scale=self.bg_atlas.resolution,
            name=f"{self.bg_atlas.atlas_name}_reference",
            visible=False,
        )

        annotation = self.viewer.add_labels(
            self.bg_atlas.annotation,
            scale=self.bg_atlas.resolution,
            name=f"{self.bg_atlas.atlas_name}_annotation",
        )
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QLabel

        tooltip = QLabel(self.viewer.window.qt_viewer.parent())
        tooltip.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        tooltip.setAttribute(Qt.WA_ShowWithoutActivating)
        tooltip.setAlignment(Qt.AlignCenter)
        tooltip.setStyleSheet("color: black")

        # TODO:
        # docs, tests
        def on_mouse_move(layer, event):
            if annotation:
                pos = event.pos
                tooltip.move(pos[0], pos[1])
                structure_acronym = self.bg_atlas.structure_from_coords(
                    self.viewer.cursor.position, microns=True, as_acronym=True
                )
                structure_name = self.bg_atlas.structures[structure_acronym][
                    "name"
                ]
                hemisphere = self.bg_atlas.hemisphere_from_coords(
                    self.viewer.cursor.position, as_string=True, microns=True
                ).capitalize()
                tooltip_text = f"{structure_name} | {hemisphere}."
                tooltip.setText(tooltip_text)
                tooltip.show()
            else:
                tooltip.setText(
                    "An annotation image is needed to display tooltips."
                    "Add a new annotation image for this atlas"
                    "by double-clicking in the atlas table view"
                )

        annotation.mouse_move_callbacks.append(on_mouse_move)
        reference.mouse_move_callbacks.append(on_mouse_move)

    def add_structure_to_viewer(self, structure_name: str):
        """Adds the mesh of a structure to the viewer

        structure_name: the id or acronym of the structure.
        """
        mesh = self.bg_atlas.mesh_from_structure(structure_name)
        color = self.bg_atlas.structures[structure_name]["rgb_triplet"]
        self._add_mesh(
            mesh,
            name=f"{self.bg_atlas.atlas_name}_{structure_name}_mesh",
            color=color,
        )

    def _add_mesh(self, mesh: Mesh, name: str, color=None):
        """Helper function to add a mesh as a surface layer to the viewer.

        mesh: the mesh to add
        name: name for the surface layer
        color: RGB values (0-255) as a list to colour mesh with
        """
        points = mesh.points
        cells = mesh.cells[0].data
        viewer_kwargs = dict(
            name=name,
            opacity=self.mesh_opacity,
            blending=self.mesh_blending,
        )
        if color:
            # convert RGB (0-255) to rgb (0.0-1.0)
            viewer_kwargs["vertex_colors"] = np.repeat(
                [[float(c) / 255 for c in color]], len(points), axis=0
            )
        self.viewer.add_surface((points, cells), **viewer_kwargs)

    def add_additional_reference(self, additional_reference_key: str):
        self.viewer.add_image(
            self.bg_atlas.additional_references[additional_reference_key],
            scale=self.bg_atlas.resolution,
            name=f"{self.bg_atlas.atlas_name}_{additional_reference_key}_reference",
        )
