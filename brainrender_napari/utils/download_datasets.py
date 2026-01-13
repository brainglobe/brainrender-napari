"""
Utility functions for downloading publicly available atlas-registered datasets.

This module provides functionality to download and manage atlas-registered datasets
such as cell positions, gene expression data, connectivity data, etc.
"""

import csv
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.request import urlretrieve

import numpy as np

from brainrender_napari.utils.dataset_apis import download_from_api
from brainrender_napari.utils.morphapi_integration import (
    get_database_searcher,
)

# Registry of available datasets
# This now primarily contains database templates for dynamic discovery
# Actual datasets are discovered and registered dynamically via database searches
AVAILABLE_DATASETS: Dict[str, Dict] = {
    # Datasets will be dynamically added when users search databases
}


def register_dynamic_dataset(neuron_data: Dict) -> str:
    """
    Register a dynamically discovered dataset (from database search).

    Parameters
    ----------
    neuron_data : Dict
        Neuron metadata dictionary

    Returns
    -------
    str
        Generated dataset ID
    """
    database = neuron_data.get("database", "unknown")
    neuron_id = neuron_data.get("id", "unknown")
    dataset_id = f"{database}_{neuron_id}"

    # Add to available datasets
    AVAILABLE_DATASETS[dataset_id] = {
        "name": neuron_data.get("name", f"{database} Neuron {neuron_id}"),
        "source": neuron_data.get("source", database),
        "description": (
            f"Neuron from {neuron_data.get('source', database)}. "
            f"Structure: {neuron_data.get('structure_area', 'Unknown')}, "
            f"Species: {neuron_data.get('species', 'Unknown')}"
        ),
        "api_source": database,
        "neuron_id": neuron_id,
        "format": neuron_data.get("format", "swc"),
        "atlas": neuron_data.get("atlas", "allen_mouse_25um"),
        "species": neuron_data.get("species", "mouse")
        .lower()
        .replace("mus musculus", "mouse"),
        "data_type": neuron_data.get("data_type", "streamlines"),
        "file_name": f"{neuron_id}.swc",
        "size_mb": 0.2,  # Estimated
        "structure_area": neuron_data.get("structure_area"),
        "structure_name": neuron_data.get("structure_name"),
    }

    return dataset_id


def get_available_datasets(
    species: Optional[str] = None, data_type: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Get list of available datasets, optionally filtered by species or data type.

    Note: Datasets are now primarily discovered dynamically via database searches.

    Parameters
    ----------
    species : str, optional
        Filter by species ('mouse', 'fish', etc.)
    data_type : str, optional
        Filter by data type ('points', 'volume', 'streamlines', etc.)

    Returns
    -------
    Dict[str, Dict]
        Dictionary mapping dataset IDs to their metadata
    """
    datasets = AVAILABLE_DATASETS.copy()

    if species:
        datasets = {
            k: v for k, v in datasets.items() if v.get("species") == species
        }

    if data_type:
        datasets = {
            k: v
            for k, v in datasets.items()
            if v.get("data_type") == data_type
        }

    return datasets


def get_downloaded_datasets() -> List[str]:
    """
    Get list of locally downloaded dataset IDs.

    Returns
    -------
    List[str]
        List of dataset IDs that have been downloaded
    """
    brainglobe_dir = Path.home() / ".brainglobe"
    datasets_dir = brainglobe_dir / "datasets"

    if not datasets_dir.exists():
        return []

    downloaded = []
    for dataset_dir in datasets_dir.iterdir():
        if dataset_dir.is_dir() and (dataset_dir / "metadata.json").exists():
            try:
                with open(dataset_dir / "metadata.json") as f:
                    metadata = json.load(f)
                    dataset_id = metadata.get("dataset_id")
                    if dataset_id:
                        # Verify the actual data file exists
                        file_name = metadata.get("file_name")
                        if file_name and (dataset_dir / file_name).exists():
                            downloaded.append(dataset_id)
                        elif not file_name:
                            # If no file_name in metadata, check for common file extensions
                            data_files = (
                                list(dataset_dir.glob("*.swc"))
                                + list(dataset_dir.glob("*.csv"))
                                + list(dataset_dir.glob("*.nrrd"))
                            )
                            if data_files:
                                downloaded.append(dataset_id)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                # Skip corrupted or unreadable metadata files
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not read metadata from {dataset_dir}: {e}"
                )
                continue

    return downloaded


def get_dataset_path(dataset_id: str) -> Optional[Path]:
    """
    Get the local path for a downloaded dataset.

    Parameters
    ----------
    dataset_id : str
        The dataset identifier

    Returns
    -------
    Path or None
        Path to the dataset directory if it exists, None otherwise
    """
    brainglobe_dir = Path.home() / ".brainglobe"
    datasets_dir = brainglobe_dir / "datasets"
    dataset_dir = datasets_dir / dataset_id

    if dataset_dir.exists() and (dataset_dir / "metadata.json").exists():
        return dataset_dir

    return None


def download_dataset(
    dataset_id: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """
    Download an atlas-registered dataset.

    Parameters
    ----------
    dataset_id : str
        The dataset identifier
    progress_callback : Callable, optional
        Function called with (completed, total) bytes during download

    Returns
    -------
    Path
        Path to the downloaded dataset directory

    Raises
    ------
    ValueError
        If dataset_id is not available
    RuntimeError
        If download fails
    """
    if dataset_id not in AVAILABLE_DATASETS:
        raise ValueError(f"Dataset '{dataset_id}' is not available")

    dataset_metadata = AVAILABLE_DATASETS[dataset_id]

    # Check if already downloaded
    existing_path = get_dataset_path(dataset_id)
    if existing_path:
        return existing_path

    # Create datasets directory
    brainglobe_dir = Path.home() / ".brainglobe"
    datasets_dir = brainglobe_dir / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)

    dataset_dir = datasets_dir / dataset_id
    dataset_dir.mkdir(exist_ok=True)

    metadata_path = dataset_dir / "metadata.json"

    # Download data files - check if using API or direct URL
    api_source = dataset_metadata.get("api_source")
    url = dataset_metadata.get("url")

    # Determine filename from metadata or default to 'data'
    filename = dataset_metadata.get(
        "file_name", f"data.{dataset_metadata.get('format', 'dat')}"
    )
    data_file_path = dataset_dir / filename

    try:
        # Use morphapi for downloading neurons from databases
        if api_source in ["mouselight", "allen", "neuromorpho"]:
            try:
                searcher = get_database_searcher()
                neuron_id = dataset_metadata.get("neuron_id")

                if neuron_id is None:
                    raise ValueError(
                        f"Dataset '{dataset_id}' requires a neuron_id. "
                        "This dataset was likely not properly registered from a database search."
                    )

                downloaded_file = searcher.download_neuron(
                    database=api_source,
                    neuron_id=neuron_id,
                    destination_dir=dataset_dir,
                    progress_callback=progress_callback,
                )
                # File is already downloaded and saved
                if downloaded_file and downloaded_file.exists():
                    # Update metadata with actual filename and ensure dataset_id is correct
                    dataset_metadata["file_name"] = downloaded_file.name
                    # Save/update metadata AFTER successful download
                    with open(metadata_path, "w") as f:
                        json.dump(
                            {
                                "dataset_id": dataset_id,  # Ensure this matches the directory name
                                **dataset_metadata,
                            },
                            f,
                            indent=4,
                        )
                    return dataset_dir
                else:
                    raise FileNotFoundError(
                        f"Downloaded file not found: {downloaded_file}"
                    )
            except ImportError as e:
                import shutil

                shutil.rmtree(dataset_dir, ignore_errors=True)
                raise RuntimeError(
                    f"morphapi is required for downloading from {api_source}. "
                    f"Install with: pip install morphapi"
                ) from e
            except Exception as e:
                import shutil

                shutil.rmtree(dataset_dir, ignore_errors=True)
                raise RuntimeError(
                    f"Failed to download from {api_source}: {str(e)}"
                ) from e

        # If we reach here, we need to download via URL (for non-API datasets)
        if not url:
            raise ValueError(
                f"No URL or API source provided for dataset {dataset_id}"
            )

        # Download using requests (better for progress tracking) or urlretrieve
        try:
            # Try using the API download function first (better progress tracking)
            download_from_api(url, data_file_path, progress_callback)
        except ImportError:
            # Fallback to urlretrieve if requests not available (shouldn't happen)
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = block_num * block_size
                    progress_callback(min(downloaded, total_size), total_size)

            urlretrieve(
                url,
                str(data_file_path),
                reporthook=report_progress if progress_callback else None,
            )

        # For URL-based downloads, save metadata after successful download
        with open(metadata_path, "w") as f:
            json.dump(
                {
                    "dataset_id": dataset_id,
                    **dataset_metadata,
                },
                f,
                indent=4,
            )
    except Exception as e:
        # Clean up on failure
        import shutil

        shutil.rmtree(dataset_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to download dataset: {str(e)}") from e

    return dataset_dir


def load_dataset_data(dataset_id: str) -> Any:
    """
    Load data from a downloaded dataset.

    For 'points' (csv) and 'streamlines' (swc), returns numpy arrays of coordinates.
    For 'volume' (nrrd), returns the Path object (as loading nrrd requires extra deps).

    Parameters
    ----------
    dataset_id : str
        The dataset identifier

    Returns
    -------
    Any
        The loaded dataset data or Path object depending on format.

    Raises
    ------
    ValueError
        If dataset is not downloaded
    """
    dataset_path = get_dataset_path(dataset_id)
    if not dataset_path:
        raise ValueError(f"Dataset '{dataset_id}' is not downloaded")

    metadata_path = dataset_path / "metadata.json"
    with open(metadata_path) as f:
        metadata = json.load(f)

    file_format = metadata.get("format", "npy")
    file_name = metadata.get("file_name", f"data.{file_format}")
    data_file = dataset_path / file_name

    if not data_file.exists():
        # Fallback to older naming convention if file_name wasn't found
        data_file = dataset_path / f"data.{file_format}"
        if not data_file.exists():
            return None

    # Handle different formats
    if file_format == "npy":
        return np.load(data_file)

    elif file_format == "json":
        with open(data_file) as f:
            return json.load(f)

    elif file_format == "csv":
        # Assumes CSV with header, columns for x, y, z
        points = []
        with open(data_file, "r") as f:
            reader = csv.reader(f)
            # Skip header if it exists (heuristic: check if first item is string)
            # For robustness in this demo, we just try to parse floats
            for row in reader:
                try:
                    # Attempt to grab first 3 columns as coords
                    coords = [float(x) for x in row[:3]]
                    points.append(coords)
                except ValueError:
                    continue  # Skip header or malformed lines
        return np.array(points)

    elif file_format == "swc":
        # SWC parser preserving parent-child relationships for proper neuron visualization
        # SWC format: id, type, x, y, z, radius, parent_id
        # Returns a dictionary with 'points' (coordinates) and 'connections' (parent-child pairs)
        nodes = {}  # id -> [x, y, z, radius, type, parent_id]
        with open(data_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        node_id = int(float(parts[0]))  # ID
                        node_type = int(float(parts[1]))  # Type
                        x = float(parts[2])  # X coordinate (microns)
                        y = float(parts[3])  # Y coordinate (microns)
                        z = float(parts[4])  # Z coordinate (microns)
                        radius = float(parts[5])  # Radius
                        parent_id = int(
                            float(parts[6])
                        )  # Parent ID (-1 for root)
                        nodes[node_id] = [
                            x,
                            y,
                            z,
                            radius,
                            node_type,
                            parent_id,
                        ]
                    except (ValueError, IndexError):
                        continue

        # Convert to numpy array for backward compatibility, but also return connection info
        if nodes:
            # Sort by node ID to maintain order
            sorted_ids = sorted(nodes.keys())
            points = np.array(
                [
                    [nodes[nid][0], nodes[nid][1], nodes[nid][2]]
                    for nid in sorted_ids
                ]
            )

            # Build connections list (parent -> child pairs)
            connections = []
            id_to_index = {nid: idx for idx, nid in enumerate(sorted_ids)}
            for node_id, node_data in nodes.items():
                parent_id = node_data[5]  # parent_id
                if (
                    parent_id != -1
                    and parent_id in id_to_index
                    and node_id in id_to_index
                ):
                    # Connect parent to child
                    connections.append(
                        (id_to_index[parent_id], id_to_index[node_id])
                    )

            # Return both points and connections as a dictionary
            return {
                "points": points,  # (N, 3) array of [x, y, z] in microns
                "connections": connections,  # List of (parent_idx, child_idx) tuples
                "radii": np.array(
                    [nodes[nid][3] for nid in sorted_ids]
                ),  # Radii for each point
            }
        else:
            return {
                "points": np.array([]),
                "connections": [],
                "radii": np.array([]),
            }

    elif file_format == "nrrd":
        # Return the path so napari can open it directly with 'viewer.open(path)'
        # This avoids adding a pynrrd dependency to this specific file.
        return data_file

    else:
        # Default fallback: return path
        return data_file
