from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtWidgets import QTableView

from brainrender_napari.data_models.atlas_table_model import AtlasTableModel


def create_atlas_proxy_model(
    source_model: AtlasTableModel,
) -> QSortFilterProxyModel:
    """Creates a shared proxy model configuration for atlas table views."""
    proxy_model = QSortFilterProxyModel()
    proxy_model.setSourceModel(source_model)
    proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
    proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)
    proxy_model.setDynamicSortFilter(True)
    return proxy_model


def enable_table_sorting(table_view: QTableView) -> None:
    """Enables clickable-header sorting on a table view."""
    table_view.setSortingEnabled(True)
    table_view.model().sort(-1)
