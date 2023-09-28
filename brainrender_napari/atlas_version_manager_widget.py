from qtpy.QtWidgets import QVBoxLayout, QWidget

from brainrender_napari.utils.brainglobe_logo import header_widget
from brainrender_napari.widgets.atlas_manager_view import AtlasManagerView


class AtlasVersionManagerWidget(QWidget):
    def __init__(self):
        """Instantiates the version manager widget
        and sets up coordinating connections"""
        super().__init__()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(
            header_widget(tutorial_file_name="update-atlas-napari.html")
        )

        # create widgets
        self.atlas_manager_view = AtlasManagerView(parent=self)
        self.layout().addWidget(self.atlas_manager_view)

        self.atlas_manager_view.download_atlas_confirmed.connect(self._refresh)

        self.atlas_manager_view.update_atlas_confirmed.connect(self._refresh)

    def _refresh(self) -> None:
        # refresh view once an atlas has been downloaded
        self.atlas_manager_view = AtlasManagerView(parent=self)
