from typing import Callable

from napari.qt import thread_worker


@thread_worker
def apply_on_atlas_in_thread(apply: Callable, atlas_name: str):
    """Calls `apply` on the given atlas name in a separate thread."""
    apply(atlas_name)
    return atlas_name
