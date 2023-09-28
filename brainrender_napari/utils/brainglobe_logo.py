from importlib.resources import files

from qtpy.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QWidget

brainglobe_logo = files("brainrender_napari").joinpath(
    "resources/brainglobe.png"
)

_logo_html = f"""
<h1>
<img src="{brainglobe_logo}"width="100">
<p>brainrender</p>
<\h1>
"""


def _docs_links_widget(tutorial_file_name: str, parent: QWidget = None):
    _docs_links_html = f"""
    <h3>
    <p>Atlas visualisation</p>
    <p><a href="https://brainglobe.info" style="color:gray;">Website</a></p>
    <p><a href="https://brainglobe.info/tutorials/{tutorial_file_name}" style="color:gray;">Tutorial</a></p>
    <p><a href="https://github.com/brainglobe/brainrender-napari" style="color:gray;">Source</a></p>
    <p><a href="https://doi.org/10.7554/eLife.65751" style="color:gray;">Citation</a></p>
    <p><small>For help, hover the cursor over the atlases/regions.</small>
    </h3>
    """  # noqa: E501
    docs_links_widget = QLabel(_docs_links_html, parent=parent)
    docs_links_widget.setOpenExternalLinks(True)
    return docs_links_widget


def _logo_widget(parent: QWidget = None):
    return QLabel(_logo_html, parent=None)


def header_widget(tutorial_file_name: str, parent: QWidget = None):
    box = QGroupBox(parent)
    box.setFlat(True)
    box.setLayout(QHBoxLayout())
    box.layout().addWidget(_logo_widget(parent=box))
    box.layout().addWidget(_docs_links_widget(tutorial_file_name, parent=box))
    return box
