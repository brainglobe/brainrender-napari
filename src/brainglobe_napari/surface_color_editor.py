from qtpy.QtWidgets import QWidget, QTreeView

from qtpy.QtGui import QColor, QPainter

class SurfaceColorEditor(QWidget):
    """TODO"""

    def __init__(self, structure_tree_view: QTreeView) -> None:
        super().__init__()
        self.structure_tree_view = structure_tree_view
        self.structure_tree_view.clicked.connect(self._on_row_clicked)
        self._height = 24
        self.setFixedWidth(self._height)
        self.setFixedHeight(self._height)
        self.color = None
        self.hide()

    def _on_row_clicked(self):
        selected_index = self.structure_tree_view.selectionModel().currentIndex()
        if selected_index.isValid():
            selected_row = selected_index.row()
            selected_parent = selected_index.parent()
            # colour lives in column 2
            selected_color_index = self.structure_tree_view.model().index(selected_row, 2, selected_parent)
            self.color = self.structure_tree_view.model().data(selected_color_index)
            self.update()
            self.show()

    def paintEvent(self, event):
        """
        Paint the colorbox.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        if self.color:
            painter = QPainter(self)
            color = self.color
            painter.setPen(QColor(*list(color)))
            painter.setBrush(QColor(*list(color)))
            painter.drawRect(0, 0, self._height, self._height)