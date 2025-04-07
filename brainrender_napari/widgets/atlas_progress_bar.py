"""
A progress bar widget specifically for atlas download and update operations.
"""

from qtpy.QtWidgets import QProgressBar, QWidget

from brainrender_napari.utils.formatting import format_bytes


class AtlasProgressBar(QProgressBar):
    """
    A specialized progress bar for atlas download and update operations.
    Displays operation type, atlas name, and transfer progress.
    """

    def __init__(self, parent: QWidget = None) -> None:
        """
        Initialize the progress bar with appropriate styling.
        """
        super().__init__(parent)

        self.setTextVisible(True)
        self.setStyleSheet("QProgressBar { text-align: center; }")
        self.hide()  # Hide by default until needed

    def update_progress(
        self, completed: int, total: int, atlas_name: str, operation_type: str
    ) -> None:
        """
        Update the progress bar with current download/update status.
        """
        # Calculate percentage and ensure it doesn't exceed 100%
        percentage: int = min(
            int((completed / total) * 100) if total > 0 else 0, 100
        )

        # Update progress bar state
        self.setMaximum(100)
        self.setValue(percentage)

        # Update format text
        self.setFormat(
            f"{operation_type} {atlas_name}... "
            f"{format_bytes(completed)} / {format_bytes(total)} "
            f"({percentage}%)"
        )

        # show the progress bar
        self.show()

    def operation_completed(self) -> None:
        """
        Called when an operation completes to reset and hide the progress bar.
        """
        self.setValue(self.maximum())
        self.hide()
