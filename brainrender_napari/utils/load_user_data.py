from functools import lru_cache

from brainglobe_atlasapi import BrainGlobeAtlas


@lru_cache(maxsize=32)
def read_atlas_metadata_from_file(atlas_name: str):
    """Reads atlas metadata from the local manifest in the BrainGlobe
    directory. Removes nested keys that are not relevant for the user.
    Converts the additional_references list of dicts to a list of names.

    Parameters
    ----------
    atlas_name : str
        Name of the atlas to read metadata for.

    Returns
    -------
    dict
        A dictionary containing the atlas metadata.
    """
    atlas = BrainGlobeAtlas(atlas_name=atlas_name, check_latest=False)

    keys_to_remove = [
        "coordinate_space",
        "terminology",
        "annotation_set",
        "template",
    ]

    metadata_dict = atlas.metadata
    metadata_dict = {
        k: v for k, v in metadata_dict.items() if k not in keys_to_remove
    }
    additional_references = metadata_dict.get("additional_references", [])
    if additional_references:
        additional_references = [ref["name"] for ref in additional_references]
        metadata_dict["additional_references"] = additional_references

    return metadata_dict


@lru_cache(maxsize=32)
def read_atlas_structures_from_file(atlas_name: str):
    """Reads atlas structure info from the local terminology file in the
    BrainGlobe directory.

    Parameters
    ----------
    atlas_name : str
        Name of the atlas to read structure info for.

    Returns
    -------
    list
        A list of dictionaries containing the structure info
    """
    atlas = BrainGlobeAtlas(atlas_name=atlas_name, check_latest=False)

    return atlas.structures_list
