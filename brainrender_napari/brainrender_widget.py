"""
A napari widget to view atlases.

Atlases that are exposed by the Brainglobe atlas API are
shown in a table view using the Qt model/view framework
[Qt Model/View framework](https://doc.qt.io/qt-6/model-view-programming.html)

Users can download and add the atlas images/structures as layers to the viewer.
"""
from bg_atlasapi import BrainGlobeAtlas
from napari.viewer import Viewer
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)
from brainrender_napari.widgets.atlas_table_view import AtlasTableView
from brainrender_napari.widgets.structure_view import StructureView


class BrainrenderWidget(QWidget):
    """The purpose of this class is
    * to hold atlas visualisation widgets for napari
    * coordinate between these widgets and napari by creating appropriate connections and napari representations
    """

    def __init__(self, napari_viewer: Viewer):
        """Instantiates the atlas viewer widget
        and sets up coordinating connections"""
        super().__init__()

        self._viewer = napari_viewer
        self.setLayout(QVBoxLayout())

        # create widgets and add them to the layout
        self.atlas_table_view = AtlasTableView(parent=self)
        self.structure_view = StructureView(parent=self)
        self.layout().addWidget(self.atlas_table_view)
        self.layout().addWidget(self.structure_view)

        # connect atlas view widget signals
        self.atlas_table_view.download_atlas_confirmed.connect(
            self._on_download_atlas_confirmed
        )
        self.atlas_table_view.add_atlas_requested.connect(
            self._on_add_atlas_requested
        )
        self.atlas_table_view.additional_reference_requested.connect(
            self._on_additional_reference_requested
        )
        self.atlas_table_view.selected_atlas_changed.connect(
            self._on_atlas_selection_changed
        )

        # connect structure view signals
        self.structure_view.add_structure_requested.connect(
            self._on_add_structure_requested
        )

    def _on_download_atlas_confirmed(self, atlas_name):
        """Ensures the structure view is displayed if an atlas is newly downloaded."""
        self.structure_view.refresh(atlas_name)

    def _on_add_structure_requested(self, structure_name: str):
        """Creates a napari atlas representation and asks it to add a given structure to the viewer."""
        selected_atlas = BrainGlobeAtlas(
            self.atlas_table_view.selected_atlas_name()
        )
        selected_atlas_representation = NapariAtlasRepresentation(
            selected_atlas, self._viewer
        )
        selected_atlas_representation.add_structure_to_viewer(structure_name)

    def _on_additional_reference_requested(
        self, additional_reference_name: str
    ):
        """Creates a napari atlas representation and asks it to add a given additional reference to the viewer"""
        atlas = BrainGlobeAtlas(self.atlas_table_view.selected_atlas_name())
        atlas_representation = NapariAtlasRepresentation(atlas, self._viewer)
        atlas_representation.add_additional_reference(
            additional_reference_name
        )

    def _on_atlas_selection_changed(self, atlas_name: str):
        """Refreshes the structure view to match the changed atlas selection"""
        self.structure_view.refresh(atlas_name)

    def _on_add_atlas_requested(self, atlas_name: str):
        """Creates a napari atlas representation and asks it to add the reference and annotation images for the given atlas to the viewer."""
        selected_atlas = BrainGlobeAtlas(atlas_name)
        selected_atlas_representation = NapariAtlasRepresentation(
            selected_atlas, self._viewer
        )
        selected_atlas_representation.add_to_viewer()
