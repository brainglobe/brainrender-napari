__version__ = "0.0.1"

from ._reader import napari_get_reader
from ._sample_data import make_sample_data
from ._widget import ExampleQWidget, example_magic_widget

__all__ = (
    "napari_get_reader",
    "make_sample_data",
    "ExampleQWidget",
    "example_magic_widget",
)
