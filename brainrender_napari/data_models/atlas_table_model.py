from brainglobe_atlasapi.list_atlases import (
    get_all_atlases_lastversions,
    get_atlases_lastversions,
    get_local_atlas_version,
)
from napari.settings import get_settings
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import QTableView

from brainrender_napari.utils.formatting import format_atlas_name


def _extract_species_from_name(atlas_name: str) -> str:
    """Heuristically extract species from an atlas name.

    Atlas names follow the convention: source_species_resolution
    e.g. 'allen_mouse_100um' -> 'Mouse'
         'mpin_zfish_1um' -> 'Zfish'
         'kim_unified_25um' -> 'Unified'
    """
    parts = atlas_name.split("_")
    if len(parts) >= 3:
        # species is typically the second token
        # but some atlases like 'kim_dev_mouse_25um' have extra tokens
        # attempt to find common species keywords
        species_keywords = {
            "mouse": "Mouse",
            "rat": "Rat",
            "zfish": "Zebrafish",
            "zebrafish": "Zebrafish",
            "human": "Human",
            "axolotl": "Axolotl",
            "prairie_vole": "Prairie vole",
            "bluebrain_barrels": "Mouse",
        }
        name_lower = atlas_name.lower()
        for keyword, species in species_keywords.items():
            if keyword in name_lower:
                return species
        # fallback: capitalize second token
        return parts[1].capitalize()
    return "Unknown"


class AtlasTableModel(QAbstractTableModel):
    """A table data model for atlases."""

    def __init__(self, view_type: QTableView):
        super().__init__()
        self.column_headers: list[str] = [
            "Raw name",
            "Atlas",
            "Local version",
            "Latest version",
            "Species",
        ]
        assert hasattr(view_type, "get_tooltip_text"), (
            "Views for this model must implement"
            "a `classmethod` called `get_tooltip_text`"
        )
        self.view_type: QTableView = view_type
        self.refresh_data()

    def refresh_data(self):
        """Refresh model data by calling atlas API"""
        all_atlases: dict[str, str] = get_all_atlases_lastversions()
        local_atlases = get_atlases_lastversions().keys()
        data = []
        for name, latest_version in all_atlases.items():
            species = _extract_species_from_name(name)

            if name in local_atlases:
                # Try to read species from metadata for accuracy
                try:
                    from brainrender_napari.utils.load_user_data import (
                        read_atlas_metadata_from_file,
                    )

                    metadata = read_atlas_metadata_from_file(atlas_name=name)
                    if "species" in metadata:
                        # metadata species is like "Mus musculus"
                        # use common name from it
                        species_map = {
                            "Mus musculus": "Mouse",
                            "Rattus norvegicus": "Rat",
                            "Danio rerio": "Zebrafish",
                            "Homo sapiens": "Human",
                            "Ambystoma mexicanum": "Axolotl",
                            "Microtus ochrogaster": "Prairie vole",
                        }
                        latin = metadata["species"]
                        species = species_map.get(latin, latin)
                except Exception:
                    pass  # keep heuristic species

                data.append(
                    [
                        name,
                        format_atlas_name(name),
                        get_local_atlas_version(name),
                        latest_version,
                        species,
                    ]
                )
            else:
                data.append(
                    [
                        name,
                        format_atlas_name(name),
                        "n/a",
                        latest_version,
                        species,
                    ]
                )

        self._data = data

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.ToolTipRole:
            hovered_atlas_name = self._data[index.row()][0]
            return self.view_type.get_tooltip_text(hovered_atlas_name)
        if role == Qt.BackgroundRole:

            theme = get_settings().appearance.theme  # 'dark' or 'light'

            local_version = self._data[index.row()][2]
            if local_version == "n/a":
                if theme == "dark":
                    return QBrush(QColor(80, 80, 80))  # dark grey
                return QBrush(Qt.lightGray)  # light grey
            else:
                latest_version = self._data[index.row()][3]
                if local_version == latest_version:
                    # Up-to-date atlas: normal background (default)
                    return None
                # Out-of-date atlas:
                if theme == "dark":
                    return QBrush(QColor(255, 140, 0))  # dark amber
                return QBrush(QColor(255, 191, 0))  # light amber

        return None

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._data[0])

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Customises the horizontal header data of model,
        and raises an error if an unexpected column is found."""
        if role == Qt.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section >= 0 and section < len(self.column_headers):
                return self.column_headers[section]
            else:
                raise ValueError("Unexpected horizontal header value.")
        else:
            return super().headerData(section, orientation, role)

    def get_unique_species(self) -> list[str]:
        """Returns a sorted list of unique species in the data."""
        species_set = set()
        species_col = self.column_headers.index("Species")
        for row in self._data:
            species_set.add(row[species_col])
        return sorted(species_set)
