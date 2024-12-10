from dataclasses import dataclass

import numpy as np
from brainglobe_atlasapi import BrainGlobeAtlas
from meshio import Mesh
from napari.settings import get_settings
from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QLabel


@dataclass
class NapariAtlasRepresentation:
    """Representation of a BG atlas as napari layers, in pixel space."""

    bg_atlas: BrainGlobeAtlas
    viewer: Viewer
    mesh_opacity: float = 0.4
    mesh_blending: str = "translucent_no_depth"

    def __post_init__(self) -> None:
        """Setup a custom QLabel tooltip and enable napari layer tooltips"""
        self._tooltip = QLabel(self.viewer.window.qt_viewer.parent())
        self._tooltip.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self._tooltip.setAttribute(Qt.WA_ShowWithoutActivating)
        self._tooltip.setAlignment(Qt.AlignCenter)
        self._tooltip.setStyleSheet("color: black")
        napari_settings = get_settings()
        napari_settings.appearance.layer_tooltip_visibility = True

    def add_to_viewer(self):
        """Adds the reference and annotation images as layers to the viewer.

        The layers are connected to the mouse move callback to set tooltip.
        The reference image's visibility is off, the annotation's is on.
        """
        reference = self.viewer.add_image(
            self.bg_atlas.reference,
            name=f"{self.bg_atlas.atlas_name}_reference",
            visible=False,
        )

        annotation = self.viewer.add_labels(
            self.bg_atlas.annotation,
            name=f"{self.bg_atlas.atlas_name}_annotation",
        )

        annotation.mouse_move_callbacks.append(self._on_mouse_move)
        reference.mouse_move_callbacks.append(self._on_mouse_move)

    def add_structure_to_viewer(self, structure_name: str):
        """Adds the mesh of a structure to the viewer.
        The mesh will be rescaled to pixel space.

        structure_name: the id or acronym of the structure.
        """
        mesh = self.bg_atlas.mesh_from_structure(structure_name)
        scale = [1.0 / resolution for resolution in self.bg_atlas.resolution]
        color = self.bg_atlas.structures[structure_name]["rgb_triplet"]
        self._add_mesh(
            mesh,
            scale,
            name=f"{self.bg_atlas.atlas_name}_{structure_name}_mesh",
            color=color,
        )

    def _add_mesh(self, mesh: Mesh, scale: list, name: str, color=None):
        """Helper function to add a mesh as a surface layer to the viewer.

        mesh: the mesh to add
        scale: List of scaling factors for each axis
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
        self.viewer.add_surface((points, cells), scale=scale, **viewer_kwargs)

    def add_additional_reference(self, additional_reference_key: str):
        """Adds a given additional reference as a layer to the viewer.
        and connects it to the mouse move callback to set tooltip.
        """
        additional_reference = self.viewer.add_image(
            self.bg_atlas.additional_references[additional_reference_key],
            name=f"{self.bg_atlas.atlas_name}_{additional_reference_key}_reference",
        )
        additional_reference.mouse_move_callbacks.append(self._on_mouse_move)

    def _on_mouse_move(self, layer, event):
        """Adapts the tooltip according to the cursor position.

        The tooltip is only displayed if
        * the viewer is in 2D display
        * and the cursor is inside the annotation
        * and the user has not switched off layer tooltips.

        Note that layer, event input args are unused,
        because all the required info is in
        * the bg_atlas.structure_from_coords
        * the (screen) cursor position
        * the (napari) cursor position
        """
        cursor_position = self.viewer.cursor.position
        napari_settings = get_settings()
        tooltip_visibility = (
            napari_settings.appearance.layer_tooltip_visibility
        )
        if (
            tooltip_visibility
            and np.all(np.array(cursor_position) > 0)
            and self.viewer.dims.ndisplay == 2
        ):
            self._tooltip.move(QCursor.pos().x() + 20, QCursor.pos().y() + 20)
            try:
                structure_acronym = self.bg_atlas.structure_from_coords(
                    cursor_position, microns=False, as_acronym=True
                )
                structure_name = self.bg_atlas.structures[structure_acronym][
                    "name"
                ]
                hemisphere = self.bg_atlas.hemisphere_from_coords(
                    cursor_position, as_string=True, microns=False
                ).capitalize()
                tooltip_text = f"{structure_name} | {hemisphere}"
                self._tooltip.setText(tooltip_text)
                self._tooltip.adjustSize()
                self._tooltip.show()
            except (KeyError, IndexError):
                # cursor position outside the image or in the image background
                # so no tooltip to be displayed
                # this saves us a bunch of assertions and extra computation
                self._tooltip.setText("")
                self._tooltip.hide()
