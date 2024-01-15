"""The purpose of this file is to provide interactive table view to download
and update atlases. Users interacting with the table can request to
* download an atlas (double-click on row of a not-yet downloaded atlas)
* update an atlas (double-click on row of outdated local atlas)
They can also hover over an up-to-date local atlas and see that
it's up to date.

It is designed to be agnostic from the viewer framework by emitting signals
that any interested observers can connect to.
"""

from qtpy.QtWidgets import QTableView, QWidget

from brainrender_napari.data_models.atlas_table_proxy_model import (
    AtlasSortFilterProxyModel,
)


class AtlasView(QTableView):
    def __init__(
        self, model: AtlasSortFilterProxyModel, parent: QWidget = None
    ):
        """Initialises an atlas table view with latest atlas versions.

        Also responsible for appearance, behaviour on selection, and
        setting up signal-slot connections.
        """
        super().__init__(parent)
        self.setModel(model)
        self.setEnabled(True)
        self.verticalHeader().hide()
        self.resizeColumnsToContents()

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        assert hasattr(model, "row_double_clicked")
        self.doubleClicked.connect(self._on_row_double_clicked)

    def _on_row_double_clicked(self):
        self.model().row_double_clicked(
            self.selectionModel().currentIndex().row()
        )
