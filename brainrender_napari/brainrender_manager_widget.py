"""
A napari widget to download and update atlases.

Available atlases are shown in a table view using the Qt model/view framework
[Qt Model/View framework](https://doc.qt.io/qt-6/model-view-programming.html)
"""

from brainglobe_utils.qtpy.logo import header_widget
from napari.viewer import Viewer
from qtpy.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.widgets.atlas_manager_filter import AtlasManagerFilter
from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView
from brainrender_napari.widgets.atlas_progress_bar import AtlasProgressBar


class BrainrenderManagerWidget(QWidget):
    """The purpose of this class is
    * to hold atlas visualisation widgets for napari
    * coordinate between these widgets and napari
    """

    def __init__(self, napari_viewer: Viewer) -> None:
        """Instantiates the atlas viewer widget
        and sets up coordinating connections"""
        super().__init__()

        self._viewer: Viewer = napari_viewer
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(
            header_widget(
                "brainrender",
                "Atlas management",
                tutorial_file_name="manage-atlases-in-GUI.html",
                citation_doi="https://doi.org/10.21105/joss.02668",
                github_repo_name="brainrender-napari",
                help_text="For help, hover the cursor over the " "atlases.",
            )
        )

        # Create atlas manager layout as group box
        self.atlas_manager_group = QGroupBox("Atlas Manager")
        self.atlas_manager_group.setToolTip(
            "Double-click on row to download/update an atlas"
        )
        self.atlas_manager_group.setLayout(QVBoxLayout())
        self.layout().addWidget(self.atlas_manager_group)

        # Create the atlas manager view
        self.atlas_manager_view = AtlasManagerView(parent=self)
        self.atlas_manager_group.layout().addWidget(self.atlas_manager_view)

        # Create the atlas manager filter
        self.atlas_manager_filter = AtlasManagerFilter(
            atlas_manager_view=self.atlas_manager_view
        )
        self.atlas_manager_group.layout().addWidget(self.atlas_manager_filter)

        # Create the progress bar
        self.progress_bar = AtlasProgressBar(parent=self)
        self.atlas_manager_group.layout().addWidget(self.progress_bar)

        # Connect signals
        self.atlas_manager_view.progress_updated.connect(
            self.progress_bar.update_progress
        )
        self.atlas_manager_view.download_atlas_confirmed.connect(
            self.progress_bar.operation_completed
        )
        self.atlas_manager_view.update_atlas_confirmed.connect(
            self.progress_bar.operation_completed
        )
