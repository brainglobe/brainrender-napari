from typing import List

from bg_atlasapi.list_atlases import get_downloaded_atlases
from bg_atlasapi.update_atlases import update_atlas

from brainrender_napari.data_models.atlas_table_proxy_model import (
    AtlasSortFilterProxyModel,
)
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_dialog import AtlasManagerDialog


class DownloadedAtlasesProxyModel(AtlasSortFilterProxyModel):
    """
    Proxy model for displaying downloaded atlases in a table view.

    Downloadable atlases are atlases that are available through
    the BrainGlobe Atlas API, but have not been downloaded yet.

    The double-click action for this model results in the update
    of an atlas in a thread (if the atlas is not up-to-date),
    after a cautionary dialog is shown.
    """

    def __init__(self, parent=None):
        """
        Initialize the DownloadedAtlasesProxyModel.

        In particular, link double-clicking to the update_atlas
        function of the BrainGlobe Atlas API.

        Parameters:
        - parent: The parent object (default: None)
        """
        self.perform_double_click_action = update_atlas
        super().__init__(parent)

    def column_headers_to_keep(self) -> List[str]:
        """
        Get the column headers to keep in the table view.

        Returns:
        - A list of column headers to keep.
        """
        return ["Atlas", "Local version", "Latest version"]

    def atlases_to_keep(self) -> List[str]:
        """
        Get the downloaded atlases to keep in the table view.

        Returns:
        - A list of downloaded atlases to keep.
        """
        return get_downloaded_atlases()

    def construct_tooltip(self, atlas_name) -> str:
        """
        Construct the tooltip for a given atlas name, to inform
        users that double-clicking will update this atlas.

        Parameters:
        - atlas_name: The name of the atlas.

        Returns:
        - The constructed tooltip string.
        """
        return f"{format_atlas_name(atlas_name)} (double-click to update)"

    def prepare_double_click_action(self, atlas_name):
        """
        Prepare the double-click action for a given atlas by displaying a
        dialog warning the user that updating may take a while.

        Parameters:
        - atlas_name: The name of the atlas.
        """
        update_dialog = AtlasManagerDialog(atlas_name, "Update")
        update_dialog.ok_button.clicked.connect(
            lambda: self._on_action_confirmed(atlas_name=atlas_name)
        )
        update_dialog.exec()
