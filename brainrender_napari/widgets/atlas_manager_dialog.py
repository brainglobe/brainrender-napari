from brainglobe_atlasapi.list_atlases import get_all_atlases_lastversions
from qtpy.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class AtlasManagerDialog(QDialog):
    """A modal dialog to ask users to confirm they'd like to download/update
    the selected atlas, and warn them that it may be slow.
    """

    def __init__(self, atlas_name: str, action: str) -> None:
        if atlas_name in get_all_atlases_lastversions().keys():
            super().__init__()

            self.setWindowTitle(f"{action} {atlas_name} Atlas")
            self.setModal(True)

            self.label = QLabel("Are you sure?\n(It may take a while)")
            self.ok_button = QPushButton("Yes")
            self.ok_button.clicked.connect(self.accept)
            self.cancel_button = QPushButton("No")
            self.cancel_button.clicked.connect(self.reject)

            button_layout = QHBoxLayout()
            button_layout.addWidget(self.ok_button)
            button_layout.addWidget(self.cancel_button)

            layout = QVBoxLayout()
            layout.addWidget(self.label)
            layout.addLayout(button_layout)
            self.setLayout(layout)
        else:
            raise ValueError(
                "Atlas manager dialog constructor"
                "called with invalid atlas name."
            )
