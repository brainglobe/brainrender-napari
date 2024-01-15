from typing import List

from bg_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_downloaded_atlases,
)
from bg_atlasapi.update_atlases import install_atlas

from brainrender_napari.data_models.atlas_table_proxy_model import (
    AtlasSortFilterProxyModel,
)
from brainrender_napari.utils.formatting import format_atlas_name
from brainrender_napari.widgets.atlas_manager_dialog import AtlasManagerDialog


class DownloadableAtlasesProxyModel(AtlasSortFilterProxyModel):
    """
    Proxy model for displaying downloadable atlases in a view.

    Downloadable atlases are atlases that are available through
    the BrainGlobe Atlas API, but have not been downloaded yet.

    The double-click action for this model results in the download
    of an atlas in a thread, after a cautionary dialog is shown.
    """

    def __init__(self, parent=None):
        """
        Initialize the DownloadableAtlasesProxyModel.

        In particular, link double-clicking to the install_atlas
        function of the BrainGlobe Atlas API.

        Parameters:
        - parent: The parent object (default: None)
        """
        self.perform_double_click_action = install_atlas
        super().__init__(parent)

    def column_headers_to_keep(self) -> List[str]:
        """
        Get the column headers to keep in the view.

        Returns:
        - A list of column headers to keep.
        """
        return ["Atlas", "Latest version"]

    def atlases_to_keep(self) -> List[str]:
        """
        Get the atlases to keep in the view.

        Returns:
        - A list of atlases to keep.
        """
        downloaded_atlases = get_downloaded_atlases()
        all_atlases = get_all_atlases_lastversions()
        return [
            atlas_name
            for atlas_name in all_atlases
            if atlas_name not in downloaded_atlases
        ]

    def construct_tooltip(self, atlas_name) -> str:
        """
        Construct the tooltip for an atlas, to inform users
        that double-clicking will download this atlas.

        Parameters:
        - atlas_name: The name of the atlas.

        Returns:
        - The constructed tooltip.
        """
        return f"{format_atlas_name(atlas_name)} (double-click to download)"

    def prepare_double_click_action(self, atlas_name):
        """
        Prepare the double-click action for an atlas by displaying a
        dialog warning the user that downloading may take a while.

        Parameters:
        - atlas_name: The name of the atlas.
        """
        download_dialog = AtlasManagerDialog(atlas_name, "Download")
        download_dialog.ok_button.clicked.connect(
            lambda: self._on_action_confirmed(atlas_name=atlas_name)
        )
        download_dialog.exec()
