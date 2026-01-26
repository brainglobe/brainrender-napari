import json

from brainglobe_atlasapi import config
from brainglobe_atlasapi.list_atlases import get_local_atlas_version


def read_atlas_metadata_from_file(atlas_name: str):
    """Reads atlas metadata stored in a `.json` in the BrainGlobe directory."""
    brainglobe_dir = config.get_brainglobe_dir()
    with open(
        brainglobe_dir
        / f"{atlas_name}_v{get_local_atlas_version(atlas_name=atlas_name)}"
        / "metadata.json",
    ) as metadata_file:
        return json.loads(metadata_file.read())


def read_atlas_structures_from_file(atlas_name: str):
    """Reads structure info from a '.json' in the BrainGlobe directory."""
    brainglobe_dir = config.get_brainglobe_dir()
    with open(
        brainglobe_dir
        / f"{atlas_name}_v{get_local_atlas_version(atlas_name=atlas_name)}"
        / "structures.json",
    ) as metadata_file:
        return json.loads(metadata_file.read())
