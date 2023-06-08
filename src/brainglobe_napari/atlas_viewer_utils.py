import json
from pathlib import Path

from bg_atlasapi import BrainGlobeAtlas


def write_atlas_metadata_cache(
    atlas: BrainGlobeAtlas, brainglobe_dir: str = None
):
    """Caches the atlas metadata in a `.json` in the BrainGlobe directory."""
    if not brainglobe_dir:
        brainglobe_dir = Path.home() / ".brainglobe"
    with open(
        brainglobe_dir / f"{atlas.atlas_name}-metadata.json",
        "w",
    ) as metadata_cache:
        json.dump(atlas.metadata, metadata_cache)


def read_atlas_metadata_cache(atlas_name: str, brainglobe_dir: str = None):
    """Reads atlas metadata cached in a `.json` in the BrainGlobe directory."""
    if not brainglobe_dir:
        brainglobe_dir = Path.home() / ".brainglobe"
    with open(
        brainglobe_dir / f"{atlas_name}-metadata.json",
    ) as metadata_cache:
        return json.loads(metadata_cache.read())
