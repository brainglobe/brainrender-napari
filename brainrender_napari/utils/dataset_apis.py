"""
API handlers for downloading atlas-registered datasets from various sources.

This module provides API interaction classes similar to morphapi's pattern,
for fetching data from Allen Brain Atlas, MouseLight, and other sources.
"""

import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class AllenBrainAtlasAPI:
    """Handler for Allen Brain Atlas API endpoints."""

    BASE_URL = "https://api.brain-map.org/api/v2"

    @staticmethod
    def get_neuron_metadata(neuron_id: int) -> Dict:
        """Get metadata for a specific neuron by ID."""
        query = (
            f"{AllenBrainAtlasAPI.BASE_URL}/data/query.json?"
            f"criteria=model::ApiCellTypesSpecimenDetail,"
            f"rma::criteria,[id$eq{neuron_id}]"
        )
        response = requests.get(query)
        response.raise_for_status()
        data = response.json()
        return data.get("msg", [{}])[0] if data.get("msg") else {}

    @staticmethod
    def get_neuron_reconstruction_url(neuron_id: int) -> Optional[str]:
        """Get the download URL for a neuron's SWC reconstruction file."""
        query = (
            f"{AllenBrainAtlasAPI.BASE_URL}/data/query.json?"
            f"criteria=model::NeuronReconstruction,"
            f"rma::criteria,[specimen_id$eq{neuron_id}],"
            f"rma::include,well_known_files"
        )
        try:
            response = requests.get(query)
            response.raise_for_status()
            data = response.json()
            if not data.get("msg"):
                return None

            well_known_files = data["msg"][0].get("well_known_files", [])
            for file_info in well_known_files:
                file_path = file_info.get("path", "")
                # We want the plain .swc file, not .png or marker files
                if file_path.endswith(".swc") and "marker" not in file_path:
                    download_link = file_info.get("download_link")
                    if download_link:
                        # download_link from API might already be a full URL or start with /api/v2/
                        # Handle both cases to avoid duplication
                        if download_link.startswith("http"):
                            return download_link
                        elif download_link.startswith("/api/v2/"):
                            return f"https://api.brain-map.org{download_link}"
                        else:
                            return (
                                f"{AllenBrainAtlasAPI.BASE_URL}{download_link}"
                            )
            return None
        except Exception as e:
            logger.error(
                f"Error fetching reconstruction URL for neuron {neuron_id}: {e}"
            )
            return None

    @staticmethod
    def get_projection_image_url(
        experiment_id: int, downsample: int = 3
    ) -> str:
        """Get URL for projection density image."""
        return (
            f"{AllenBrainAtlasAPI.BASE_URL}/projection_image_download/"
            f"{experiment_id}?downsample={downsample}"
        )

    @staticmethod
    def search_neurons(
        structure_id: Optional[int] = None,
        transgenic_line: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Search for neurons matching criteria."""
        criteria = ["model::ApiCellTypesSpecimenDetail"]

        if structure_id:
            criteria.append(f"rma::criteria,[structure__id$eq{structure_id}]")
        if transgenic_line:
            criteria.append(f"rma::criteria,[line_name$eq{transgenic_line}]")

        criteria.append("rma::options[num_rows$eq{}]".format(limit))

        query = f"{AllenBrainAtlasAPI.BASE_URL}/data/query.json?criteria={','.join(criteria)}"
        try:
            response = requests.get(query)
            response.raise_for_status()
            data = response.json()
            return data.get("msg", [])
        except Exception as e:
            logger.error(f"Error searching neurons: {e}")
            return []


class MouseLightAPI:
    """Handler for Janelia MouseLight neuron database."""

    BASE_URL = "https://ml-neuronbrowser.janelia.org/api"

    @staticmethod
    def get_neuron_metadata(neuron_id: str) -> Dict:
        """Get metadata for a MouseLight neuron by ID (e.g., 'AA0001')."""
        query = f"{MouseLightAPI.BASE_URL}/neurons/{neuron_id}"
        try:
            response = requests.get(query)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching MouseLight neuron {neuron_id}: {e}")
            return {}

    @staticmethod
    def get_neuron_swc_url(neuron_id: str) -> Optional[str]:
        """Get the download URL for a MouseLight neuron SWC file."""
        # MouseLight API structure - this may need adjustment based on actual API
        # For now, using the BrainGlobe sample URL pattern
        return (
            f"https://raw.githubusercontent.com/brainglobe/morphapi/master/"
            f"examples/example_files/{neuron_id.lower()}.swc"
        )


def download_from_api(
    url: str,
    destination: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    Download a file from an API endpoint with progress tracking.

    Parameters
    ----------
    url : str
        URL to download from
    destination : Path
        Path where file should be saved
    progress_callback : Callable, optional
        Function called with (downloaded_bytes, total_bytes) during download
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Get file size if available
    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded, total_size)

    if progress_callback and total_size == 0:
        # If content-length wasn't available, call with downloaded size
        progress_callback(downloaded, downloaded)
