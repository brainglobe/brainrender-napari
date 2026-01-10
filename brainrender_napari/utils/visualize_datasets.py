"""Utilities for visualizing atlas-registered datasets as napari layers."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np
from brainglobe_atlasapi import BrainGlobeAtlas
from napari.viewer import Viewer
from napari.utils.notifications import show_error, show_info

from brainrender_napari.utils.download_datasets import (
    get_dataset_path,
    load_dataset_data,
)


def _resize_to_match(data: np.ndarray, target_shape: tuple) -> np.ndarray:
    """Resize array to match target shape using center crop/pad."""
    result = np.zeros(target_shape, dtype=data.dtype)
    
    # Calculate crop/pad for each dimension
    for dim in range(min(len(data.shape), len(target_shape))):
        if data.shape[dim] > target_shape[dim]:
            # Crop
            start = (data.shape[dim] - target_shape[dim]) // 2
            data = np.take(data, range(start, start + target_shape[dim]), axis=dim)
        elif data.shape[dim] < target_shape[dim]:
            # Pad
            pad_before = (target_shape[dim] - data.shape[dim]) // 2
            pad_after = target_shape[dim] - data.shape[dim] - pad_before
            pad_width = [(0, 0)] * len(data.shape)
            pad_width[dim] = (pad_before, pad_after)
            data = np.pad(data, pad_width, mode='constant')
    
    # Copy to result
    slices = tuple(slice(0, min(data.shape[i], target_shape[i])) for i in range(len(target_shape)))
    result[slices] = data[slices]
    
    return result


def fix_atlas_layer_visibility(viewer: Viewer, atlas_name: str = None):
    """
    Public function to fix layer visibility issues when atlas makes everything black.
    
    Call this if the screen goes black after adding an atlas.
    This function:
    1. Makes reference layer visible (provides background instead of black)
    2. Ensures dataset layers are on top of annotation layer
    3. Maintains tooltip functionality
    
    Parameters
    ----------
    viewer : Viewer
        The napari viewer instance
    atlas_name : str, optional
        Atlas name to fix. If None, fixes all atlases in viewer.
    """
    if atlas_name:
        atlas_names = [atlas_name]
    else:
        # Find all atlas names in viewer
        atlas_names = set()
        for layer in viewer.layers:
            if "_annotation" in layer.name or "_reference" in layer.name:
                # Extract atlas name (format: "atlas_name_annotation" or "atlas_name_reference")
                parts = layer.name.rsplit("_", 1)
                if len(parts) == 2:
                    atlas_names.add(parts[0])
    
    for atlas in atlas_names:
        _ensure_proper_layer_visibility(viewer, atlas)


def _ensure_proper_layer_visibility(viewer: Viewer, atlas_name: str):
    """
    Ensure proper layer visibility and ordering to prevent black screen.
    
    When atlas annotation layer is added, it can cover everything. This function:
    1. Makes reference layer visible (provides background instead of black) - CRITICAL FIX
    2. Ensures dataset layers are on top of annotation layer
    3. Maintains tooltip functionality
    
    Layer order (bottom to top):
    - Reference (visible, provides background)
    - Annotation (visible, for tooltips)
    - Dataset layers (visible, on top)
    """
    # Find all atlas layers
    atlas_annotation_layers = [
        l for l in viewer.layers 
        if atlas_name in l.name and "annotation" in l.name
    ]
    atlas_reference_layers = [
        l for l in viewer.layers 
        if atlas_name in l.name and "reference" in l.name
    ]
    
    # CRITICAL FIX: Make reference layer visible to prevent black screen
    # The reference layer provides the anatomical background image
    for ref_layer in atlas_reference_layers:
        ref_layer.visible = True  # This fixes the black screen!
    
    # Find dataset layers (streamlines, points, volume)
    dataset_layers = [
        l for l in viewer.layers 
        if ("_streamlines" in l.name or "_points" in l.name or "_volume" in l.name)
        and atlas_name not in l.name
    ]
    
    # Ensure dataset layers are on TOP of annotation layer so they're visible
    if atlas_annotation_layers and dataset_layers:
        annotation_idx = viewer.layers.index(atlas_annotation_layers[0])
        
        for dataset_layer in dataset_layers:
            dataset_idx = viewer.layers.index(dataset_layer)
            dataset_layer.visible = True  # Ensure visible
            
            # Move dataset layer above annotation if needed
            # This ensures neurons/streamlines show on top of the annotation
            if dataset_idx < annotation_idx:
                # Move to position after annotation (above it)
                viewer.layers.move(dataset_idx, annotation_idx + 1)
            elif dataset_idx > annotation_idx:
                # Already above, but move to very top to ensure maximum visibility
                try:
                    viewer.layers.move(dataset_idx, len(viewer.layers) - 1)
                except Exception:
                    pass  # If move fails, layer is already in good position


def _build_neuron_paths(points: np.ndarray, connections: list) -> list:
    """
    Build connected paths from point connections.
    
    Takes a list of (parent_idx, child_idx) connections and creates
    path segments that can be visualized in napari as connected lines.
    Each connection becomes a line segment showing the neuron structure.
    
    Parameters
    ----------
    points : np.ndarray
        Array of shape (N, 3) with point coordinates in napari order (z, y, x)
    connections : list
        List of (parent_idx, child_idx) tuples
        
    Returns
    -------
    list
        List of path arrays, each path is a (2, 3) array representing a line segment
        from parent to child point
    """
    paths = []
    # For each connection, create a 2-point path segment (line)
    for parent_idx, child_idx in connections:
        if 0 <= parent_idx < len(points) and 0 <= child_idx < len(points):
            # Create a path segment connecting parent to child
            # This represents a branch/segment of the neuron
            path_segment = np.array([
                points[parent_idx],  # Start point (parent node)
                points[child_idx]    # End point (child node)
            ])
            paths.append(path_segment)
    return paths


def _add_connected_points(
    viewer: Viewer, 
    points: np.ndarray, 
    connections: list, 
    dataset_id: str,
    scale: list = None
):
    """
    Fallback method: Add points and draw connections using multiple approaches.
    """
    if scale is None:
        scale = [1.0, 1.0, 1.0]
    
    # Add points layer
    points_layer = viewer.add_points(
        points,
        name=f"{dataset_id}_streamlines",
        size=4,
        face_color="cyan",
        opacity=1.0,
        blending="translucent",
        scale=scale,  # Match atlas coordinate system
        out_of_slice_display=True,  # Keep visible during 3D rotation
    )
    
    # Try to add connections as separate line segments using shapes
    if connections:
        try:
            # Create line segments for each connection
            line_segments = []
            for p_idx, c_idx in connections[:100]:  # Limit to first 100 for performance
                if 0 <= p_idx < len(points) and 0 <= c_idx < len(points):
                    segment = np.array([points[p_idx], points[c_idx]])
                    line_segments.append(segment)
            
            if line_segments:
                # Add as a separate shapes layer for connections
                viewer.add_shapes(
                    line_segments,
                    shape_type='path',
                    name=f"{dataset_id}_connections",
                    edge_color="lightblue",
                    edge_width=1,
                    opacity=0.8,
                    blending="translucent",
                )
        except Exception:
            pass  # If shapes fail, just show points
    
    return points_layer


def _detect_file_format(file_path: Path) -> str:
    """Detect the actual file format by reading file header."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(20)
            
        # Check for NRRD format
        if header.startswith(b'NRRD') or b'NRRD' in header[:10]:
            return "nrrd"
        
        # Check for JPEG
        if header.startswith(b'\xff\xd8\xff'):
            return "jpeg"
        
        # Check for PNG
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return "png"
        
        # Check for TIFF
        if header.startswith(b'\x49\x49\x2a\x00') or header.startswith(b'\x4d\x4d\x00\x2a'):
            return "tiff"
        
        # Check for GIF
        if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return "gif"
        
        # Default based on extension
        ext = file_path.suffix.lower()
        if ext == '.nrrd':
            return "nrrd"
        elif ext in ['.jpg', '.jpeg']:
            return "jpeg"
        elif ext == '.png':
            return "png"
        elif ext in ['.tif', '.tiff']:
            return "tiff"
        
        return "unknown"
    except Exception:
        return "unknown"


def add_dataset_to_viewer(dataset_id: str, viewer: Viewer, atlas_name: str = None):
    """
    Add a downloaded dataset to the napari viewer as appropriate layer types.
    
    This function preserves all original brainrender-napari features including:
    - Structure label tooltips on hover/zoom
    - Proper coordinate alignment with atlas
    - Compatibility with existing atlas layers

    Parameters
    ----------
    dataset_id : str
        The dataset identifier
    viewer : Viewer
        The napari viewer instance
    atlas_name : str, optional
        The atlas name to use. If None, will use the dataset's required atlas.

    Raises
    ------
    ValueError
        If dataset is not downloaded or cannot be visualized
    """
    dataset_path = get_dataset_path(dataset_id)
    if not dataset_path:
        raise ValueError(f"Dataset '{dataset_id}' is not downloaded")

    # Load metadata
    metadata_path = dataset_path / "metadata.json"
    import json

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Get atlas name
    if atlas_name is None:
        atlas_name = metadata.get("atlas")
        if not atlas_name:
            show_error(
                f"Dataset '{dataset_id}' does not specify a required atlas."
            )
            return

    data_type = metadata.get("data_type", "points")

    try:
        # Check if atlas layers already exist in viewer
        existing_atlas_annotation = None
        existing_atlas_reference = None
        for layer in viewer.layers:
            if atlas_name in layer.name:
                if "annotation" in layer.name:
                    existing_atlas_annotation = layer
                elif "reference" in layer.name:
                    existing_atlas_reference = layer
        
        # Load the atlas (needed for coordinate conversion)
        bg_atlas = BrainGlobeAtlas(atlas_name=atlas_name)

        # Load dataset data
        data = load_dataset_data(dataset_id)

        # Add to viewer based on data type
        if data_type == "points":
            _add_points_dataset(data, viewer, dataset_id, bg_atlas, existing_atlas_annotation)
        elif data_type == "volume":
            _add_volume_dataset(data, viewer, dataset_id, bg_atlas, metadata, existing_atlas_annotation)
        elif data_type == "streamlines":
            _add_streamlines_dataset(data, viewer, dataset_id, bg_atlas, existing_atlas_annotation)
        else:
            show_error(
                f"Data type '{data_type}' is not yet supported for visualization."
            )

        # After adding dataset, ensure proper layer visibility and ordering
        # This fixes the black screen issue when atlas is added before or after neurons
        _ensure_proper_layer_visibility(viewer, atlas_name)
        
        show_info(
            f"Dataset '{metadata.get('name', dataset_id)}' added to viewer.\n"
            "✓ Reference layer is visible (background)\n"
            "✓ Dataset layer is on top (visible)\n"
            "✓ Annotation layer is visible for tooltips\n"
            "Use dimension slider (horizontal arrow) to navigate slices. Hover over atlas to see structure names."
        )

    except Exception as e:
        show_error(f"Failed to visualize dataset: {str(e)}")
        raise


def _add_points_dataset(
    data: np.ndarray, viewer: Viewer, dataset_id: str, atlas: BrainGlobeAtlas, existing_atlas_layer=None
):
    """
    Add point data (e.g., cell positions) to the viewer.

    Points should be in atlas coordinates (microns).
    Preserves all original atlas features including tooltips.
    """
    if data.size == 0:
        show_error("Dataset contains no data points.")
        return

    # Convert from microns to pixel space if needed
    # Assuming data is in shape (N, 3) for 3D coordinates
    if len(data.shape) != 2 or data.shape[1] != 3:
        show_error(
            f"Expected points data in shape (N, 3), got {data.shape}"
        )
        return

    # CRITICAL: Convert from microns to pixel space and reorder for napari
    # SWC files from morphapi/Allen have coordinates in microns: [x, y, z]
    # Atlas layers use pixel coordinates
    # Napari expects coordinates in (z, y, x) order for 3D points!
    
    resolution = atlas.resolution  # e.g., [25.0, 25.0, 25.0] microns per pixel for allen_mouse_25um
    
    if len(resolution) >= 3:
        # Convert from microns to pixels
        # SWC format: data[:, 0] = x_micron, data[:, 1] = y_micron, data[:, 2] = z_micron
        x_pixel = data[:, 0] / resolution[0]  # X in pixels
        y_pixel = data[:, 1] / resolution[1]  # Y in pixels
        z_pixel = data[:, 2] / resolution[2]  # Z in pixels
        
        # CRITICAL: Napari uses (z, y, x) order for 3D coordinates!
        # Reorder from [x, y, z] to [z, y, x] for napari
        points_pixel = np.column_stack([z_pixel, y_pixel, x_pixel])
        
        # Validate coordinates are within atlas bounds
        # Atlas shape is (Z, Y, X) in pixels
        atlas_shape = atlas.annotation.shape
        if len(atlas_shape) >= 3:
            valid_mask = (
                (points_pixel[:, 0] >= 0) & (points_pixel[:, 0] < atlas_shape[0]) &  # Z bounds
                (points_pixel[:, 1] >= 0) & (points_pixel[:, 1] < atlas_shape[1]) &  # Y bounds
                (points_pixel[:, 2] >= 0) & (points_pixel[:, 2] < atlas_shape[2])    # X bounds
            )
            valid_count = np.sum(valid_mask)
            if valid_count < len(points_pixel):
                show_info(f"Placed {valid_count}/{len(points_pixel)} points within atlas bounds. "
                         f"Atlas shape: {atlas_shape}, Resolution: {resolution} μm/pixel")
                points_pixel = points_pixel[valid_mask]
            else:
                show_info(f"All {len(points_pixel)} points are within atlas bounds. "
                         f"Atlas shape: {atlas_shape}, Resolution: {resolution} μm/pixel")
    else:
        # Fallback: assume data is already in correct format
        points_pixel = data
        show_info("Using data as-is (atlas resolution format unexpected)")

    # CRITICAL: Use the same coordinate system as atlas layers
    # Atlas layers use pixel space with default scale [1,1,1]
    # We need to match this exactly to ensure proper alignment
    
    # Get the scale from existing atlas layer if available, otherwise use [1,1,1]
    # This ensures neurons are in the same coordinate space as the atlas
    scale = None
    if existing_atlas_layer is not None:
        try:
            # Use the same scale as the atlas layer for perfect alignment
            scale = existing_atlas_layer.scale
        except AttributeError:
            scale = [1.0, 1.0, 1.0]  # Default pixel space scale
    else:
        # Check if atlas layers exist in viewer
        atlas_layers = [l for l in viewer.layers if atlas.atlas_name in l.name]
        if atlas_layers:
            try:
                scale = atlas_layers[0].scale  # Match atlas layer scale
            except AttributeError:
                scale = [1.0, 1.0, 1.0]
        else:
            scale = [1.0, 1.0, 1.0]  # Default: pixel space scale
    
    # Add as points layer - coordinates in napari's (z, y, x) pixel space
    # Using the same scale as atlas ensures perfect alignment and visibility during rotation
    points_layer = viewer.add_points(
        points_pixel,
        name=f"{dataset_id}_points",
        size=8,  # Size for visibility
        face_color="red",
        opacity=1.0,  # Full opacity to ensure visibility
        blending="translucent",  # Translucent blending so it shows over annotation
        scale=scale,  # Match atlas coordinate system for proper alignment
        out_of_slice_display=True,  # CRITICAL: Keep visible during 3D rotation/zoom
    )
    
    # CRITICAL: Ensure points layer is on TOP of annotation layer
    # This prevents the annotation layer from covering the points
    atlas_annotation_layers = [
        l for l in viewer.layers 
        if atlas.atlas_name in l.name and "annotation" in l.name
    ]
    
    if atlas_annotation_layers:
        # Move points layer above annotation layer
        annotation_idx = viewer.layers.index(atlas_annotation_layers[0])
        points_idx = viewer.layers.index(points_layer)
        
        # If points is below annotation, move it above
        if points_idx < annotation_idx:
            # Move to position after annotation
            viewer.layers.move(points_idx, annotation_idx + 1)
        elif points_idx > annotation_idx:
            # Already above, but ensure it's visible - move to end (top)
            viewer.layers.move(points_idx, len(viewer.layers) - 1)
    
    # Ensure layer is visible
    points_layer.visible = True
    
    # CRITICAL: Configure for 3D rotation visibility
    # Ensure points remain visible when rotating/zooming with touchpad
    if hasattr(points_layer, 'out_of_slice_display'):
        points_layer.out_of_slice_display = True  # Show points outside current slice in 3D
    
    # Ensure points layer stays visible during 3D rotations
    try:
        if viewer.dims.ndisplay == 3:
            points_layer.visible = True
            # Move to top to prevent occlusion
            if points_layer in viewer.layers:
                viewer.layers.move(viewer.layers.index(points_layer), len(viewer.layers) - 1)
    except Exception:
        pass
    
    # Also find and ensure reference layer is visible (for background instead of black)
    atlas_reference_layers = [
        l for l in viewer.layers 
        if atlas.atlas_name in l.name and "reference" in l.name
    ]
    for ref_layer in atlas_reference_layers:
        # Make reference visible so we have background instead of black
        ref_layer.visible = True


def _add_volume_dataset(
    data: Any, viewer: Viewer, dataset_id: str, atlas: BrainGlobeAtlas, metadata: Dict, existing_atlas_layer=None
):
    """
    Add volumetric data to the viewer.

    Supports NRRD files, image files (JPEG, PNG, TIFF), and numpy arrays.
    """
    file_format = metadata.get("format", "nrrd")
    
    # If data is a Path object, detect format and load it
    if isinstance(data, Path):
        if not data.exists():
            show_error(f"Volume file not found: {data}")
            return
        
        # Detect actual file format by reading header
        actual_format = _detect_file_format(data)
        
        volume_data = None
        error_messages = []
        
        # Load based on detected format
        if actual_format == "nrrd":
            # Try pynrrd first (most reliable for NRRD files)
            try:
                import pynrrd
                volume_data, header = pynrrd.read(str(data))
            except ImportError:
                error_messages.append("pynrrd not installed - install with: pip install pynrrd")
            except Exception as e:
                error_messages.append(f"pynrrd error: {str(e)}")
        
        # For images or if NRRD loading failed, use format-agnostic loading
        if volume_data is None:
            # Try PIL first (best format detection, ignores extension)
            try:
                from PIL import Image
                # PIL auto-detects format from file content, ignoring extension
                with Image.open(data) as img:
                    # Convert to grayscale
                    if img.mode != 'L':  # L is grayscale
                        img = img.convert('L')
                    img_array = np.array(img)
                    # Ensure 3D format for napari (add z-dimension)
                    if len(img_array.shape) == 2:
                        volume_data = img_array[np.newaxis, :, :]
                    else:
                        volume_data = img_array
            except ImportError:
                # PIL not available, try imageio with workaround for wrong extension
                try:
                    import imageio
                    # Create temporary file with correct extension so imageio uses right plugin
                    temp_ext = { "jpeg": ".jpg", "png": ".png", "tiff": ".tif" }.get(actual_format, ".jpg")
                    with tempfile.NamedTemporaryFile(suffix=temp_ext, delete=False) as tmp_file:
                        shutil.copy2(data, tmp_file.name)
                        try:
                            img = imageio.imread(tmp_file.name)
                            # Convert 2D to 3D
                            if len(img.shape) == 2:
                                volume_data = img[np.newaxis, :, :]
                            elif len(img.shape) == 3 and img.shape[2] == 3:
                                # RGB to grayscale
                                volume_data = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])[np.newaxis, :, :]
                            else:
                                volume_data = img
                        finally:
                            # Clean up temp file
                            try:
                                os.unlink(tmp_file.name)
                            except Exception:
                                pass
                except Exception as e:
                    error_messages.append(f"imageio workaround error: {str(e)}")
            except Exception as e:
                error_messages.append(f"PIL error: {str(e)}")
                # Last resort: try imageio directly (might fail due to extension)
                try:
                    import imageio
                    # Read as bytes and let imageio auto-detect
                    with open(data, 'rb') as f:
                        img_bytes = f.read()
                        img = imageio.imread(img_bytes)
                        if len(img.shape) == 2:
                            volume_data = img[np.newaxis, :, :]
                        elif len(img.shape) == 3 and img.shape[2] == 3:
                            volume_data = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])[np.newaxis, :, :]
                        else:
                            volume_data = img
                except Exception as e2:
                    error_messages.append(f"Final imageio attempt error: {str(e2)}")
            else:
                # For unknown formats or NRRD, try imageio generically
                try:
                    import imageio
                    # Try volume read first (for multi-dimensional data)
                    try:
                        volume_data = imageio.volread(str(data))
                    except Exception:
                        # Fallback to regular image read
                        try:
                            img = imageio.imread(str(data))
                            # Convert 2D to 3D by adding a singleton dimension
                            if len(img.shape) == 2:
                                volume_data = img[np.newaxis, :, :]
                            elif len(img.shape) == 3 and img.shape[2] == 3:
                                # RGB image - convert to grayscale
                                volume_data = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])[np.newaxis, :, :]
                            else:
                                volume_data = img
                        except Exception as e:
                            error_messages.append(f"imageio error: {str(e)}")
                except ImportError:
                    error_messages.append("imageio not installed - install with: pip install imageio")
        
        # If still no data, try napari's open method as last resort
        if volume_data is None:
            try:
                layers = viewer.open(str(data))
                if layers:
                    # Rename the layer to match our convention
                    for layer in layers:
                        layer.name = f"{dataset_id}_volume"
                        layer.opacity = 0.7
                    return
            except Exception as e:
                error_messages.append(f"napari.open() error: {str(e)}")
        
        if volume_data is not None:
            # Get atlas dimensions for alignment
            atlas_shape = atlas.reference.shape
            dataset_shape = volume_data.shape
            
            # Resize dataset to match atlas if dimensions don't match
            # Note: This is a simple resizing approach. For production, proper registration might be needed.
            if dataset_shape != atlas_shape:
                # Try scipy first (best quality)
                try:
                    from scipy import ndimage
                    # Calculate zoom factors for each dimension
                    zoom_factors = [atlas_shape[i] / dataset_shape[i] for i in range(min(len(atlas_shape), len(dataset_shape)))]
                    # Pad zoom_factors if needed
                    while len(zoom_factors) < len(dataset_shape):
                        zoom_factors.append(1.0)
                    
                    # Resize to match atlas dimensions
                    volume_data = ndimage.zoom(volume_data, zoom_factors, order=1, mode='constant')
                    # Crop or pad to exact match if needed
                    if volume_data.shape != atlas_shape:
                        volume_data = _resize_to_match(volume_data, atlas_shape)
                except ImportError:
                    # scipy not available, use PIL for 2D resizing
                    try:
                        from PIL import Image
                        # Handle 3D data by resizing each slice
                        if len(volume_data.shape) == 3 and volume_data.shape[0] > 1:
                            resized_slices = []
                            for z in range(min(volume_data.shape[0], atlas_shape[0])):
                                img = Image.fromarray(volume_data[z])
                                img_resized = img.resize((atlas_shape[2], atlas_shape[1]), Image.Resampling.LANCZOS)
                                resized_slices.append(np.array(img_resized))
                            volume_data = np.array(resized_slices)
                            # Pad or crop z dimension
                            if volume_data.shape[0] < atlas_shape[0]:
                                # Repeat last slice
                                last_slice = volume_data[-1:]
                                volume_data = np.concatenate([volume_data] + [last_slice] * (atlas_shape[0] - volume_data.shape[0]), axis=0)
                            elif volume_data.shape[0] > atlas_shape[0]:
                                # Take evenly spaced slices
                                indices = np.linspace(0, volume_data.shape[0]-1, atlas_shape[0], dtype=int)
                                volume_data = volume_data[indices]
                        else:
                            # 2D or single slice - resize and replicate
                            img_data = volume_data[0] if len(volume_data.shape) == 3 else volume_data
                            img = Image.fromarray(img_data)
                            img_resized = img.resize((atlas_shape[2], atlas_shape[1]), Image.Resampling.LANCZOS)
                            volume_data = np.array(img_resized)[np.newaxis, :, :]
                            # Replicate to match z dimension
                            if volume_data.shape[0] < atlas_shape[0]:
                                volume_data = np.repeat(volume_data, atlas_shape[0], axis=0)
                    except Exception as e:
                        # If resizing fails, show warning but continue
                        show_info(f"Note: Dataset dimensions ({dataset_shape}) don't match atlas ({atlas_shape}). "
                                 f"Layers may not align perfectly. Error: {str(e)}")
            
            # Note: Atlas layers use default scale (pixel space)
            # The dataset data is resized to match atlas pixel dimensions
            # Add as image layer - it should align since dimensions match
            
            # Check if this is actually a 2D projection (single or few slices)
            is_2d_projection = len(volume_data.shape) == 3 and volume_data.shape[0] == 1
            
            # Add volume layer - use default pixel space scale (same as atlas layers)
            # This ensures proper alignment with atlas annotation/reference layers
            # Atlas layers use default scale [1,1,1] in pixel space
            layer = viewer.add_image(
                volume_data,
                name=f"{dataset_id}_volume",
                opacity=0.25,  # Lower opacity so atlas shows through clearly
                colormap="hot",  # Better colormap for overlays (hot = yellow/red on dark)
                blending="translucent",  # Use translucent blending for better overlay
                # No scale parameter - uses default [1,1,1] like atlas layers (pixel space)
            )
            
            # Find atlas layers
            atlas_annotation_layers = [
                l for l in viewer.layers 
                if atlas.atlas_name in l.name and "annotation" in l.name
            ]
            atlas_reference_layers = [
                l for l in viewer.layers 
                if atlas.atlas_name in l.name and "reference" in l.name
            ]
            
            # CRITICAL FIX: Make reference layer visible to prevent black screen
            # The reference provides the background image
            for ref_layer in atlas_reference_layers:
                ref_layer.visible = True
            
            # Keep annotation visible for tooltips
            for annotation_layer in atlas_annotation_layers:
                annotation_layer.visible = True
            
            # CRITICAL: Move dataset layer ABOVE annotation layer so it's visible
            # We want: Reference (bottom, visible) -> Annotation (middle, visible, tooltips) -> Dataset (top, visible)
            # This way dataset is visible AND tooltips still work (annotation catches mouse events first)
            if atlas_annotation_layers:
                annotation_idx = viewer.layers.index(atlas_annotation_layers[0])
                dataset_idx = viewer.layers.index(layer)
                
                # If dataset is below annotation, move it above
                if dataset_idx < annotation_idx:
                    # Move dataset to position after annotation
                    viewer.layers.move(dataset_idx, annotation_idx + 1)
                # If already above, ensure it's at the top
                elif dataset_idx > annotation_idx:
                    viewer.layers.move(dataset_idx, len(viewer.layers) - 1)
            
            # Provide helpful message
            if is_2d_projection:
                show_info(
                    "Dataset added. This is a 2D projection image. "
                    "Use the dimension slider (horizontal arrow at bottom) to navigate through slices. "
                    "Hover over the atlas to see brain structure names. "
                    "Adjust opacity in layer controls (recommended: 0.2-0.4) to see both layers."
                )
            else:
                show_info(
                    f"Dataset added successfully. "
                    f"Use the dimension slider (horizontal arrow at bottom) to navigate slices. "
                    f"Hover over the atlas annotation layer to see brain structure names. "
                    f"Tip: Adjust dataset opacity (0.2-0.3) in layer controls if layers overlap."
                )
            
            return
        else:
            detected_info = f" (detected as {actual_format})" if actual_format != file_format else ""
            error_msg = f"Failed to load volume file: {data.name}{detected_info}\n\n"
            if error_messages:
                error_msg += "Errors encountered:\n" + "\n".join(f"  - {msg}" for msg in error_messages) + "\n\n"
            error_msg += "Solutions:\n"
            if actual_format == "nrrd":
                error_msg += "  1. Install pynrrd: pip install pynrrd\n"
            error_msg += "  2. Install/update imageio: pip install imageio\n"
            error_msg += "  3. Check if the file was downloaded correctly"
            show_error(error_msg)
            return
    
    # If data is already a numpy array
    elif isinstance(data, np.ndarray):
        if data.size == 0:
            show_error("Dataset contains no volume data.")
            return

        # Add as image layer
        viewer.add_image(
            data,
            name=f"{dataset_id}_volume",
            opacity=0.7,
            colormap="viridis",
        )
    else:
        show_error(f"Unsupported volume data type: {type(data)}")


def _add_streamlines_dataset(
    data: Any, viewer: Viewer, dataset_id: str, atlas: BrainGlobeAtlas, existing_atlas_layer=None
):
    """
    Add streamline/connectivity data to the viewer.
    
    For SWC files, this creates connected neuron paths showing the full morphology.
    Neurons are properly fitted inside the atlas using coordinate transformation.
    """
    # Handle SWC format with connections (from improved parser)
    if isinstance(data, dict) and 'points' in data and 'connections' in data:
        points_microns = data['points']  # (N, 3) array [x, y, z] in microns
        connections = data['connections']  # List of (parent_idx, child_idx) tuples
        radii = data.get('radii', None)
        
        if points_microns.size == 0:
            show_error("Dataset contains no streamline data.")
            return
            
        # CRITICAL: Convert from microns to pixel space and reorder for napari
        # SWC files contain coordinates in microns: [x, y, z]
        # Napari expects coordinates in (z, y, x) order for 3D!
        resolution = atlas.resolution  # e.g., [25.0, 25.0, 25.0] microns per pixel
        
        if len(resolution) >= 3 and len(points_microns.shape) == 2 and points_microns.shape[1] == 3:
            # Convert from microns to pixels
            x_pixel = points_microns[:, 0] / resolution[0]  # X in pixels
            y_pixel = points_microns[:, 1] / resolution[1]  # Y in pixels
            z_pixel = points_microns[:, 2] / resolution[2]  # Z in pixels
            
            # CRITICAL: Napari uses (z, y, x) order for 3D coordinates!
            # Reorder from [x, y, z] to [z, y, x] for napari
            points_pixel = np.column_stack([z_pixel, y_pixel, x_pixel])
            
            # Validate coordinates are within atlas bounds
            atlas_shape = atlas.annotation.shape  # (Z, Y, X) in pixels
            if len(atlas_shape) >= 3:
                valid_mask = (
                    (points_pixel[:, 0] >= 0) & (points_pixel[:, 0] < atlas_shape[0]) &  # Z bounds
                    (points_pixel[:, 1] >= 0) & (points_pixel[:, 1] < atlas_shape[1]) &  # Y bounds
                    (points_pixel[:, 2] >= 0) & (points_pixel[:, 2] < atlas_shape[2])    # X bounds
                )
                valid_indices = np.where(valid_mask)[0]
                valid_count = len(valid_indices)
                
                if valid_count == 0:
                    show_error(f"No streamline points are within atlas bounds. Atlas shape: {atlas_shape}, Resolution: {resolution} μm/pixel")
                    return
                elif valid_count < len(points_pixel):
                    show_info(f"Placed {valid_count}/{len(points_pixel)} streamline points within atlas bounds.")
                    # Filter points and update connections to only include valid indices
                    points_pixel = points_pixel[valid_mask]
                    # Create mapping from old indices to new indices
                    old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(valid_indices)}
                    # Filter connections to only include valid nodes
                    connections = [
                        (old_to_new[p], old_to_new[c]) 
                        for p, c in connections 
                        if p in old_to_new and c in old_to_new
                    ]
                    if radii is not None:
                        radii = radii[valid_mask]
                else:
                    show_info(f"All {len(points_pixel)} streamline points are within atlas bounds. Neuron properly fitted in atlas.")
            else:
                show_info("Using streamline data (atlas shape validation skipped)")
        else:
            show_error(f"Unexpected data format. Expected points array with shape (N, 3), got {points_microns.shape}")
            return
        
        # Create connected neuron visualization
        # For SWC files, we want to show the neuron as connected paths (branches)
        if connections and len(connections) > 0:
            # Build paths from connections
            paths = _build_neuron_paths(points_pixel, connections)
            
            # Get scale from atlas layer for proper coordinate alignment
            scale = [1.0, 1.0, 1.0]  # Default pixel space scale
            atlas_layers = [l for l in viewer.layers if atlas.atlas_name in l.name]
            if atlas_layers:
                try:
                    scale = atlas_layers[0].scale  # Match atlas layer scale
                except AttributeError:
                    pass
            
            # Add as shapes layer with paths (lines connecting parent to child nodes)
            # This properly shows the neuron morphology as connected branches
            if paths:
                try:
                    streamlines_layer = viewer.add_shapes(
                        paths,
                        shape_type='path',  # Draw connected path segments (lines)
                        name=f"{dataset_id}_streamlines",
                        edge_color="cyan",
                        edge_width=1.5,
                        opacity=1.0,
                        blending="translucent",
                        scale=scale,  # Match atlas coordinate system
                    )
                except Exception as e:
                    # Fallback if shapes don't work, use points with connection lines
                    show_info(f"Using points visualization (shapes error: {str(e)})")
                    streamlines_layer = _add_connected_points(
                        viewer, points_pixel, connections, dataset_id, scale
                    )
            else:
                # No valid paths - show as points
                streamlines_layer = viewer.add_points(
                    points_pixel,
                    name=f"{dataset_id}_streamlines",
                    size=4,
                    face_color="cyan",
                    opacity=1.0,
                    blending="translucent",
                )
        else:
            # Get scale from atlas layer for proper coordinate alignment
            scale = [1.0, 1.0, 1.0]  # Default pixel space scale
            atlas_layers = [l for l in viewer.layers if atlas.atlas_name in l.name]
            if atlas_layers:
                try:
                    scale = atlas_layers[0].scale  # Match atlas layer scale
                except AttributeError:
                    pass
            
            # No connections available - show as individual points
            streamlines_layer = viewer.add_points(
                points_pixel,
                name=f"{dataset_id}_streamlines",
                size=5,  # Visible size
                face_color="cyan",
                opacity=1.0,
                blending="translucent",
                scale=scale,  # Match atlas coordinate system
                out_of_slice_display=True,  # CRITICAL: Keep visible during 3D rotation
            )
        
        # CRITICAL: Configure layer for proper 3D visibility and rotation
        # Ensure neurons remain visible during rotation/zoom on touchpad
        streamlines_layer.visible = True
        
        # Enable 3D rendering properties
        # For shapes layer (paths), ensure it's visible in 3D mode
        if hasattr(streamlines_layer, 'out_of_slice_display'):
            streamlines_layer.out_of_slice_display = True  # Show paths outside current slice
        
        # Ensure layer stays visible when rotating/zooming
        # This is critical for touchpad gestures that rotate the view
        try:
            # Napari layers have properties for 3D rendering
            # Make sure the layer is configured for 3D display
            if viewer.dims.ndisplay == 3:
                # In 3D mode, ensure layer is visible
                streamlines_layer.visible = True
        except Exception:
            pass
        
        # Move layer to top to ensure visibility during rotation
        # This prevents the layer from being occluded by other layers
        try:
            if streamlines_layer in viewer.layers:
                viewer.layers.move(viewer.layers.index(streamlines_layer), len(viewer.layers) - 1)
        except Exception:
            pass
    
    # Handle legacy format (plain numpy array) for backward compatibility
    elif isinstance(data, np.ndarray):
        if data.size == 0:
            show_error("Dataset contains no streamline data.")
            return

        # If single array, treat as points (legacy SWC format without connections)
        if len(data.shape) == 2 and data.shape[1] == 3:
            # CRITICAL: Convert from microns to pixel space and reorder for napari
            # SWC files from morphapi contain coordinates in microns: [x, y, z]
            # Napari expects coordinates in (z, y, x) order for 3D points!
            
            resolution = atlas.resolution  # e.g., [25.0, 25.0, 25.0] microns per pixel
            
            if len(resolution) >= 3:
                # Convert from microns to pixels
                # SWC format: data[:, 0] = x_micron, data[:, 1] = y_micron, data[:, 2] = z_micron
                x_pixel = data[:, 0] / resolution[0]  # X in pixels
                y_pixel = data[:, 1] / resolution[1]  # Y in pixels
                z_pixel = data[:, 2] / resolution[2]  # Z in pixels
                
                # CRITICAL: Napari uses (z, y, x) order for 3D coordinates!
                # Reorder from [x, y, z] to [z, y, x] for napari
                points_pixel = np.column_stack([z_pixel, y_pixel, x_pixel])
                
                # Validate coordinates are within atlas bounds
                # Atlas shape is (Z, Y, X) in pixels
                atlas_shape = atlas.annotation.shape
                if len(atlas_shape) >= 3:
                    valid_mask = (
                        (points_pixel[:, 0] >= 0) & (points_pixel[:, 0] < atlas_shape[0]) &  # Z bounds
                        (points_pixel[:, 1] >= 0) & (points_pixel[:, 1] < atlas_shape[1]) &  # Y bounds
                        (points_pixel[:, 2] >= 0) & (points_pixel[:, 2] < atlas_shape[2])    # X bounds
                    )
                    valid_count = np.sum(valid_mask)
                    if valid_count < len(points_pixel):
                        show_info(f"Placed {valid_count}/{len(data)} streamline points within atlas bounds. "
                                 f"Atlas shape: {atlas_shape}, Resolution: {resolution} μm/pixel")
                        points_pixel = points_pixel[valid_mask]
                    else:
                        show_info(f"All {len(points_pixel)} streamline points are within atlas bounds.")
            else:
                # Fallback: assume data is already in correct format
                points_pixel = data
                show_info("Using streamline data as-is (atlas resolution format unexpected)")
            
            # Get scale from atlas layer for proper coordinate alignment
            scale = [1.0, 1.0, 1.0]  # Default pixel space scale
            atlas_layers = [l for l in viewer.layers if atlas.atlas_name in l.name]
            if atlas_layers:
                try:
                    scale = atlas_layers[0].scale
                except AttributeError:
                    pass
            
            # Legacy format: Add as points layer (no connections available)
            streamlines_layer = viewer.add_points(
                points_pixel,
                name=f"{dataset_id}_streamlines",
                size=6,  # Size for visibility
                face_color="cyan",  # Bright color for visibility
                opacity=1.0,  # Full opacity
                blending="translucent",  # Translucent so it shows over annotation
                scale=scale,  # Match atlas coordinate system
                out_of_slice_display=True,  # CRITICAL: Keep visible during 3D rotation/zoom
            )
            
            # Ensure layer is visible
            streamlines_layer.visible = True
            
            # CRITICAL: Ensure streamlines layer is on TOP of annotation layer
            # This prevents the annotation layer from covering the streamlines
            atlas_annotation_layers = [
                l for l in viewer.layers 
                if atlas.atlas_name in l.name and "annotation" in l.name
            ]
            
            if atlas_annotation_layers:
                # Move streamlines layer above annotation layer
                annotation_idx = viewer.layers.index(atlas_annotation_layers[0])
                streamlines_idx = viewer.layers.index(streamlines_layer)
                
                # If streamlines is below annotation, move it above
                if streamlines_idx < annotation_idx:
                    # Move to position after annotation
                    viewer.layers.move(streamlines_idx, annotation_idx + 1)
                elif streamlines_idx > annotation_idx:
                    # Already above, but ensure it's the topmost
                    # Move to end (top of rendering stack)
                    viewer.layers.move(streamlines_idx, len(viewer.layers) - 1)
            
            # Ensure layer is visible
            streamlines_layer.visible = True
            
            # Also find and ensure reference layer is visible (for background)
            atlas_reference_layers = [
                l for l in viewer.layers 
                if atlas.atlas_name in l.name and "reference" in l.name
            ]
            for ref_layer in atlas_reference_layers:
                # Make reference visible so we have background instead of black
                ref_layer.visible = True
                
        else:
            show_error(
                f"Unsupported streamline data format: {data.shape}"
            )
    else:
        show_error("Streamlines visualization not yet fully implemented.")


def get_dataset_info(dataset_id: str) -> Dict[str, Any]:
    """
    Get information about a downloaded dataset.

    Parameters
    ----------
    dataset_id : str
        The dataset identifier

    Returns
    -------
    Dict[str, Any]
        Dictionary containing dataset information
    """
    dataset_path = get_dataset_path(dataset_id)
    if not dataset_path:
        raise ValueError(f"Dataset '{dataset_id}' is not downloaded")

    metadata_path = dataset_path / "metadata.json"
    import json

    with open(metadata_path) as f:
        return json.load(f)
