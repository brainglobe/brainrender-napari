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

_docs_links_html = """
<h3>
<p>Atlas visualisation</p>
<p><a href="https://brainglobe.info" style="color:gray;">Website</a></p>
<p><a href="https://brainglobe.info/tutorials/visualise-atlas-napari.html" style="color:gray;">Tutorial</a></p>
<p><a href="https://github.com/brainglobe/brainrender-napari" style="color:gray;">Source</a></p>
<p><a href="https://doi.org/10.7554/eLife.65751" style="color:gray;">Citation</a></p>
<p><small>For help, hover the cursor over the atlases/regions.</small>
</h3>
"""  # noqa: E501


def _docs_links_widget():
    docs_links_widget = QLabel(_docs_links_html)
    docs_links_widget.setOpenExternalLinks(True)
    return docs_links_widget


def _logo_widget():
    return QLabel(_logo_html)


def header_widget(parent: QWidget = None):
    box = QGroupBox(parent)
    box.setFlat(True)
    box.setLayout(QHBoxLayout())
    box.layout().addWidget(_logo_widget())
    box.layout().addWidget(_docs_links_widget())
    return box
