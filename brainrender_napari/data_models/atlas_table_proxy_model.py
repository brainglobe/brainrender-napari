from typing import List

from qtpy.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    Qt,
    Signal,
)

from brainrender_napari.data_models.atlas_table_model import (
    singleton_atlas_table_model,
)
from brainrender_napari.utils.napari_in_thread import apply_in_thread


class AtlasSortFilterProxyModel(QSortFilterProxyModel):
    """
    A custom proxy model for filtering and sorting atlas data,
    to be used as an abstract class.

    Encapsulates
    - the complexity of dealing with source indices and proxy indices
    - functionality to execute (potentially slow) actions in a separate thread
    - some error handling
    These actions are triggered by double-clicking on a row.

    It defines a minimal API for derived classes to implement.
    It enforces this API by raising NotImplementedError for functions that
    derived classes must implement.
    """

    double_click_action_performed = Signal(str)

    def __init__(self, parent: QObject = None):
        """
        Initialize the AtlasSortFilterProxyModel.

        Parameters:
            parent (QObject): The parent object.

        Raises:
            AssertionError: If the derived class does not have
                the required attribute 'perform_double_click_action'.
        """
        super().__init__(parent)
        assert hasattr(
            self, "perform_double_click_action"
        ), f"Classes derived from {type(self)} need an attribute function"
        " called 'perform_double_click_action'"
        self.setSourceModel(singleton_atlas_table_model)
        self.sourceModel().dataChanged.connect(
            self.invalidateFilter
        )  # ensure proxymodel gets updated when sourcemodel changes.

    def setSourceModel(self, sourceModel: QAbstractItemModel) -> None:
        """
        Set the source model for the proxy model. Validates the source model
        before calling the parent class's equivalent.

        Parameters:
            sourceModel (QAbstractItemModel): The source model.

        Raises:
            AssertionError: If the source model does not have
                the required attribute 'column_headers'.
        """
        assert hasattr(
            sourceModel, "column_headers"
        ), "Source models for this proxy model "
        "need an attribute called column_headers."
        return super().setSourceModel(sourceModel)

    def column_headers_to_keep(self) -> List[str]:
        """
        Get the list of column headers to keep.

        Returns:
            List[str]: The list of column headers to keep.

        Raises:
            NotImplementedError:
                If the derived class does not implement this method.
        """
        raise NotImplementedError(
            f"Classes derived from {type(self)} need to "
            "implement column_headers_to_keep"
        )

    def atlases_to_keep(self) -> List[str]:
        """
        Get the list of atlases to keep.

        Returns:
            List[str]: The list of atlases to keep.

        Raises:
            NotImplementedError:
                If the derived class does not implement this method.
        """
        raise NotImplementedError(
            f"Classes derived from {type(self)} "
            "need to implement atlases_to_keep"
        )

    def construct_tooltip(self, atlas_name) -> str:
        """
        Construct the tooltip text for the given atlas name.

        Parameters:
            atlas_name (str): The name of the atlas.

        Returns:
            str: The constructed tooltip text.

        Raises:
            NotImplementedError:
                If the derived class does not implement this method.
        """
        raise NotImplementedError(
            f"Classes derived from {type(self)} need"
            "to implement construct_tooltip"
        )

    def prepare_double_click_action(self, atlas_name):
        """
        Prepare for the double click action on the given atlas name.
        This may be useful to e.g. display a dialog before peforming
        a slow action in a thread.

        Parameters:
            atlas_name (str): The name of the atlas.

        Raises:
            NotImplementedError:
                If the derived class does not implement this method.
        """
        raise NotImplementedError(
            f"Classes derived from {type(self)}"
            "need to implement _prepare_double_click_action"
        )

    def perform_double_click_action(self):
        """
        Perform the double click action.

        Raises:
            NotImplementedError:
                If the derived class does not implement this method.
        """
        raise NotImplementedError(
            f"Classes derived from {type(self)}"
            "need to implement perform_double_click_action"
        )

    def filterAcceptsColumn(
        self, source_column: int, source_parent: QModelIndex
    ) -> bool:
        """
        Determine if the column should be accepted for filtering,
        depending on column names in the derived class.

        Parameters:
            source_column (int): The source column index.
            source_parent (QModelIndex): The source parent index.

        Returns:
            bool: True if the column should be accepted, False otherwise.
        """
        indices_to_keep = [
            self.sourceModel().column_headers.index(column)
            for column in self.column_headers_to_keep()
        ]
        return source_column in indices_to_keep

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        """
        Determine if the row should be accepted for filtering,
        depending on the atlases_to_keep function.

        Parameters:
            source_row (int): The source row index.
            source_parent (QModelIndex): The source parent index.

        Returns:
            bool: True if the row should be accepted, False otherwise.
        """
        atlas_name_source_index = self.sourceModel().index(source_row, 0)
        atlas_name = self.sourceModel().data(atlas_name_source_index)
        return atlas_name in self.atlases_to_keep()

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """
        Get the data for the given index and role.

        Parameters:
            index (QModelIndex): The index of the data.
            role (int): The role of the data.

        Returns:
            The data for the given index and role.
        """
        if role == Qt.DisplayRole:
            source_index = self.mapToSource(index)
            return self.sourceModel().data(source_index, role)
        if role == Qt.ToolTipRole:
            source_index = self.mapToSource(index)
            source_name_index = source_index.siblingAtColumn(0)
            hovered_atlas_name = self.sourceModel().data(source_name_index)
            return self.get_tooltip_text(hovered_atlas_name)

    def row_double_clicked(self, selected_proxy_row):
        """
        Handle the double click action on the selected row.

        Parameters:
            selected_proxy_row (int): The selected proxy row index.

        Raises:
            ValueError: If the selected atlas name is invalid.
        """
        selected_proxy_index = self.index(selected_proxy_row, 0)
        selected_source_index = self.mapToSource(selected_proxy_index)
        raw_name_source_index = selected_source_index.siblingAtColumn(0)
        selected_atlas_name = self.sourceModel().data(raw_name_source_index)
        if selected_atlas_name in self.atlases_to_keep():
            self.prepare_double_click_action(selected_atlas_name)
        else:
            raise ValueError(
                "Row double clicked called with"
                "invalid atlas name: {selected_atlas_name}."
            )

    def _on_action_confirmed(self, atlas_name):
        """
        Perform this model's action on the given atlas in a separate thread.
        Signal when this action has been performed.

        Parameters:
            atlas_name (str): The name of the atlas.
        """
        worker = apply_in_thread(self.perform_double_click_action, atlas_name)
        worker.returned.connect(self.double_click_action_performed.emit)
        worker.returned.connect(self.sourceModel().refresh_data)
        worker.start()

    def get_tooltip_text(self, atlas_name: str):
        """
        Get the tooltip text for the given atlas name.

        Parameters:
            atlas_name (str): The name of the atlas.

        Returns:
            str: The tooltip text.

        Raises:
            ValueError: If the atlas name is invalid.
        """
        if atlas_name in self.atlases_to_keep():
            tooltip_text = self.construct_tooltip(atlas_name)
        else:
            raise ValueError("Tooltip text called with invalid atlas name.")
        return tooltip_text
