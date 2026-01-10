"""
Integration with morphapi for downloading neurons from various databases.

This module provides wrappers around morphapi's API classes to search and
download neurons from Allen Brain Atlas, MouseLight, and NeuroMorpho.org.
"""

import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Try to import morphapi classes
try:
    from morphapi.api.allenmorphology import AllenMorphology
    from morphapi.api.mouselight import MouseLightAPI as MorphAPI_MouseLight
    from morphapi.api.neuromorphorg import NeuroMorpOrgAPI

    MORPHAPI_AVAILABLE = True
except ImportError:
    MORPHAPI_AVAILABLE = False
    logger.warning(
        "morphapi not installed. Install with: pip install morphapi"
    )


class DatabaseSearcher:
    """Helper class to search across different neuron databases."""

    def __init__(self):
        """Initialize database searchers."""
        self._allen_api = None
        self._mouselight_api = None
        self._neuromorpho_api = None

    @property
    def allen_api(self):
        """Lazy-load Allen API."""
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed. Install with: pip install morphapi")
        if self._allen_api is None:
            try:
                self._allen_api = AllenMorphology()
            except Exception as e:
                logger.error(f"Failed to initialize Allen API: {e}")
                raise
        return self._allen_api

    @property
    def mouselight_api(self):
        """Lazy-load MouseLight API."""
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed. Install with: pip install morphapi")
        if self._mouselight_api is None:
            try:
                self._mouselight_api = MorphAPI_MouseLight()
            except Exception as e:
                logger.error(f"Failed to initialize MouseLight API: {e}")
                raise
        return self._mouselight_api

    @property
    def neuromorpho_api(self):
        """Lazy-load NeuroMorpho API."""
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed. Install with: pip install morphapi")
        if self._neuromorpho_api is None:
            try:
                self._neuromorpho_api = NeuroMorpOrgAPI()
            except Exception as e:
                logger.error(f"Failed to initialize NeuroMorpho API: {e}")
                raise
        return self._neuromorpho_api

    def search_allen_neurons(
        self,
        structure_area: Optional[str] = None,
        species: str = "Mus musculus",
        limit: int = 50,
    ) -> List[Dict]:
        """
        Search for neurons in Allen Brain Atlas.

        Parameters
        ----------
        structure_area : str, optional
            Brain structure abbreviation (e.g., 'VISp', 'MOs')
        species : str
            Species name (default: 'Mus musculus' for mouse)
        limit : int
            Maximum number of results

        Returns
        -------
        List[Dict]
            List of neuron metadata dictionaries
        """
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed")

        try:
            api = self.allen_api
            neurons_df = api.neurons

            # Filter by species
            if species:
                neurons_df = neurons_df[neurons_df.species == species]

            # Filter by structure area if provided
            if structure_area:
                neurons_df = neurons_df[
                    neurons_df.structure_area_abbrev == structure_area
                ]

            # Limit results
            neurons_df = neurons_df.head(limit)

            # Convert to list of dicts
            results = []
            for _, row in neurons_df.iterrows():
                results.append({
                    "id": int(row.get("id", 0)),
                    "name": str(row.get("name", "Unknown")),
                    "species": str(row.get("species", "Unknown")),
                    "structure_area": str(row.get("structure_area_abbrev", "Unknown")),
                    "structure_name": str(row.get("structure_area_name", "Unknown")),
                    "hemisphere": str(row.get("structure_hemisphere", "Unknown")),
                    "transgenic_line": str(row.get("transgenic_line", "N/A")),
                    "source": "Allen Brain Atlas",
                    "database": "allen",
                    "format": "swc",
                    "data_type": "streamlines",
                    "atlas": "allen_mouse_25um",  # Default for mouse
                })
            return results
        except Exception as e:
            logger.error(f"Error searching Allen neurons: {e}")
            return []

    def search_mouselight_neurons(
        self,
        filter_regions: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Search for neurons in Janelia MouseLight database.

        Parameters
        ----------
        filter_regions : List[str], optional
            List of brain region abbreviations (e.g., ['MOs'])
        limit : int
            Maximum number of results

        Returns
        -------
        List[Dict]
            List of neuron metadata dictionaries
        """
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed")

        try:
            api = self.mouselight_api

            # Fetch metadata
            if filter_regions:
                metadata = api.fetch_neurons_metadata(
                    filterby="soma",
                    filter_regions=filter_regions
                )
            else:
                # Fetch all available (may be limited by API)
                metadata = api.fetch_neurons_metadata()

            # Limit results
            metadata = metadata[:limit]

            # Convert to standardized format
            results = []
            for neuron in metadata:
                results.append({
                    "id": neuron.get("idString", neuron.get("id", "Unknown")),
                    "name": neuron.get("idString", neuron.get("name", "Unknown")),
                    "species": "Mus musculus",
                    "structure_area": neuron.get("somaLocation", {}).get("brainAcronym", "Unknown"),
                    "structure_name": neuron.get("somaLocation", {}).get("brainName", "Unknown"),
                    "source": "Janelia MouseLight",
                    "database": "mouselight",
                    "format": "swc",
                    "data_type": "streamlines",
                    "atlas": "allen_mouse_25um",
                })
            return results
        except Exception as e:
            logger.error(f"Error searching MouseLight neurons: {e}")
            return []

    def search_neuromorpho_neurons(
        self,
        species: str = "mouse",
        cell_type: Optional[str] = None,
        brain_region: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Search for neurons in NeuroMorpho.org database.

        Parameters
        ----------
        species : str
            Species name (e.g., 'mouse', 'rat')
        cell_type : str, optional
            Cell type (e.g., 'pyramidal', 'interneuron')
        brain_region : str, optional
            Brain region (e.g., 'neocortex', 'hippocampus')
        limit : int
            Maximum number of results

        Returns
        -------
        List[Dict]
            List of neuron metadata dictionaries
        """
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed")

        try:
            api = self.neuromorpho_api

            # Search for neurons
            metadata, _ = api.get_neurons_metadata(
                size=limit,
                species=species,
                cell_type=cell_type,
                brain_region=brain_region,
            )

            # Convert to standardized format
            results = []
            for neuron in metadata:
                results.append({
                    "id": neuron.get("neuron_name", "Unknown"),
                    "name": neuron.get("neuron_name", "Unknown"),
                    "species": neuron.get("species", species),
                    "cell_type": neuron.get("cell_type", cell_type or "Unknown"),
                    "brain_region": neuron.get("brain_region", brain_region or "Unknown"),
                    "source": "NeuroMorpho.org",
                    "database": "neuromorpho",
                    "format": "swc",
                    "data_type": "streamlines",
                    "atlas": "allen_mouse_25um" if "mouse" in species.lower() else None,
                })
            return results
        except Exception as e:
            logger.error(f"Error searching NeuroMorpho neurons: {e}")
            return []

    def download_neuron(
        self,
        database: str,
        neuron_id: any,
        destination_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """
        Download a neuron from the specified database.

        Parameters
        ----------
        database : str
            Database name ('allen', 'mouselight', 'neuromorpho')
        neuron_id : any
            Neuron identifier (int for Allen, str for others)
        destination_dir : Path
            Directory to save the downloaded file
        progress_callback : callable, optional
            Progress callback function

        Returns
        -------
        Path
            Path to downloaded file
        """
        if not MORPHAPI_AVAILABLE:
            raise ImportError("morphapi is not installed")

        destination_dir.mkdir(parents=True, exist_ok=True)

        if database == "allen":
            api = self.allen_api
            # Convert to int if string
            if isinstance(neuron_id, str) and neuron_id.isdigit():
                neuron_id = int(neuron_id)
            elif isinstance(neuron_id, str):
                raise ValueError(f"Allen neuron ID must be numeric, got: {neuron_id}")
            
            # Download using morphapi
            # morphapi's download_neurons returns paths to downloaded files (as strings or Path objects)
            try:
                downloaded_paths = api.download_neurons([neuron_id], load_neurons=False)
            except Exception as e:
                logger.error(f"morphapi download_neurons failed: {e}")
                raise RuntimeError(f"Failed to download Allen neuron {neuron_id}: {str(e)}") from e
            
            if downloaded_paths and len(downloaded_paths) > 0:
                # Handle both string paths and Path objects
                source_path = downloaded_paths[0]
                if isinstance(source_path, str):
                    source_file = Path(source_path)
                else:
                    source_file = Path(str(source_path))
                
                if source_file.exists():
                    # Copy to our destination
                    dest_file = destination_dir / source_file.name
                    import shutil
                    shutil.copy2(source_file, dest_file)
                    return dest_file
                else:
                    # Try looking in morphapi cache directory (morphapi may cache files there)
                    try:
                        from morphapi.paths_manager import Paths
                        paths = Paths()
                        # Try common cache locations
                        cache_dirs = [
                            Path(paths.allen_morphology_cache),
                            Path.home() / ".brainglobe" / "allen_morphology_cache",
                        ]
                        for cache_dir in cache_dirs:
                            cache_file = cache_dir / f"{neuron_id}.swc"
                            if cache_file.exists():
                                dest_file = destination_dir / cache_file.name
                                import shutil
                                shutil.copy2(cache_file, dest_file)
                                return dest_file
                    except Exception as cache_error:
                        logger.debug(f"Could not find file in cache: {cache_error}")
                    
                    raise FileNotFoundError(
                        f"Downloaded file not found at: {source_file}. "
                        f"morphapi returned: {downloaded_paths}"
                    )
            else:
                raise ValueError(
                    f"Failed to download neuron {neuron_id} - morphapi returned no paths. "
                    f"Response: {downloaded_paths}"
                )

        elif database == "mouselight":
            api = self.mouselight_api
            # Create a mock neuron dict for download
            neuron_dict = {"idString": str(neuron_id)}
            file_path = api.download_neurons(neuron_dict)
            
            if file_path and Path(file_path).exists():
                # Copy to destination
                dest_file = destination_dir / Path(file_path).name
                import shutil
                shutil.copy2(file_path, dest_file)
                return dest_file
            else:
                raise ValueError(f"Failed to download MouseLight neuron {neuron_id}")

        elif database == "neuromorpho":
            api = self.neuromorpho_api
            # Download by neuron name
            file_paths = api.download_neurons([str(neuron_id)])
            
            if file_paths and len(file_paths) > 0:
                source_file = Path(file_paths[0])
                if source_file.exists():
                    dest_file = destination_dir / source_file.name
                    import shutil
                    shutil.copy2(source_file, dest_file)
                    return dest_file
                else:
                    raise FileNotFoundError(f"Downloaded file not found: {source_file}")
            else:
                raise ValueError(f"Failed to download NeuroMorpho neuron {neuron_id}")
        else:
            raise ValueError(f"Unknown database: {database}")


# Global searcher instance
_searcher = None


def get_database_searcher() -> DatabaseSearcher:
    """Get or create the global database searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = DatabaseSearcher()
    return _searcher
