"""
A napari widget to view atlases.

Atlases that are exposed by the Brainglobe atlas API are
shown in a table view using the Qt model/view framework
[Qt Model/View framework](https://doc.qt.io/qt-6/model-view-programming.html)

Users can download and add the atlas images/structures as layers to the viewer.
"""
from bg_atlasapi import BrainGlobeAtlas
from bg_atlasapi.list_atlases import get_downloaded_atlases
from napari.viewer import Viewer
from qtpy.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.napari_atlas_representation import (
    NapariAtlasRepresentation,
)
from brainrender_napari.utils.brainglobe_logo import header_widget
from brainrender_napari.widgets.atlas_table_view import AtlasTableView
from brainrender_napari.widgets.structure_view import StructureView


class BrainrenderWidget(QWidget):
    """The purpose of this class is
    * to hold atlas visualisation widgets for napari
    * coordinate between these widgets and napari by
        * creating appropriate signal-slot connections
        * creating napari representations as requested
    """

    def __init__(self, napari_viewer: Viewer):
        """Instantiates the atlas viewer widget
        and sets up coordinating connections"""
        super().__init__()

        self._viewer = napari_viewer
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(header_widget())

        # create widgets
        self.atlas_table_view = AtlasTableView(parent=self)

        self.show_structure_names = QCheckBox()
        self.show_structure_names.setChecked(False)
        self.show_structure_names.setText("Show region names")
        self.show_structure_names.setToolTip(
            "Tick to show region names, untick to show acronyms only."
        )
        self.show_structure_names.hide()

        self.structure_view = StructureView(parent=self)

        # add widgets to the layout as group boxes
        self.atlas_table_group = QGroupBox("Atlas table view")
        self.atlas_table_group.setToolTip(
            "Double-click on row to download/add annotations and reference\n"
            "Right-click to add additional reference images (if any exist)"
        )
        self.atlas_table_group.setLayout(QVBoxLayout())
        self.atlas_table_group.layout().addWidget(self.atlas_table_view)
        self.layout().addWidget(self.atlas_table_group)

        self.structure_tree_group = QGroupBox("3D Atlas region meshes")
        self.structure_tree_group.setToolTip(
            "Double-click on an atlas region to add its mesh to the viewer.\n"
            "Meshes will only show if the display is set to 3D.\n"
            "Toggle 2D/3D display using the square/cube icon on the\n"
            "lower left of the napari window."
        )
        self.structure_tree_group.setLayout(QVBoxLayout())
        self.structure_tree_group.layout().addWidget(self.show_structure_names)
        self.structure_tree_group.layout().addWidget(self.structure_view)
        self.structure_tree_group.hide()
        self.layout().addWidget(self.structure_tree_group)

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

        # connect show structure name signals
        self.show_structure_names.clicked.connect(
            self._on_show_structure_names_clicked
        )

        # connect structure view signals
        self.structure_view.add_structure_requested.connect(
            self._on_add_structure_requested
        )

    def _on_download_atlas_confirmed(self, atlas_name):
        """Ensure structure view is displayed if new atlas downloaded."""
        show_structure_names = self.show_structure_names.isChecked()
        self.structure_view.refresh(atlas_name, show_structure_names)

    def _on_add_structure_requested(self, structure_name: str):
        """Add given structure as napari atlas representation"""
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
        """Add additional reference as napari atlas representation"""
        atlas = BrainGlobeAtlas(self.atlas_table_view.selected_atlas_name())
        atlas_representation = NapariAtlasRepresentation(atlas, self._viewer)
        atlas_representation.add_additional_reference(
            additional_reference_name
        )

    def _on_atlas_selection_changed(self, atlas_name: str):
        """Refreshes the structure view to match the changed atlas selection"""
        show_structure_names = self.show_structure_names.isChecked()
        self.structure_view.refresh(atlas_name, show_structure_names)
        is_downloaded = atlas_name in get_downloaded_atlases()
        self.show_structure_names.setVisible(is_downloaded)
        self.structure_tree_group.setVisible(is_downloaded)

    def _on_add_atlas_requested(self, atlas_name: str):
        """Add reference and annotation as napari atlas representation"""
        selected_atlas = BrainGlobeAtlas(atlas_name)
        selected_atlas_representation = NapariAtlasRepresentation(
            selected_atlas, self._viewer
        )
        selected_atlas_representation.add_to_viewer()

    def _on_show_structure_names_clicked(self):
        atlas_name = self.atlas_table_view.selected_atlas_name()
        show_structure_names = self.show_structure_names.isChecked()
        self.structure_view.refresh(atlas_name, show_structure_names)
