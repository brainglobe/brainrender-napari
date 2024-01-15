import pytest
from qtpy.QtCore import Qt

from brainrender_napari.data_models.downloadable_atlases_proxy_model import (
    DownloadableAtlasesProxyModel,
)
from brainrender_napari.data_models.downloaded_atlases_proxy_model import (
    DownloadedAtlasesProxyModel,
)
from brainrender_napari.widgets.atlas_view import AtlasView


@pytest.mark.parametrize(
    "ProxyModel",
    [DownloadableAtlasesProxyModel, DownloadedAtlasesProxyModel],
)
def test_view_connection(double_click_on_view, mocker, ProxyModel):
    """A check that the view delegates the double-clicked signal
    to its model."""
    model = ProxyModel()
    model.row_double_clicked = mocker.Mock(spec=model.row_double_clicked)
    view = AtlasView(model=model)

    model_index = view.model().index(1, 1)
    view.setCurrentIndex(model_index)
    double_click_on_view(view, model_index)

    model.row_double_clicked.assert_called_once()


def test_model_validation(qtbot):
    """A check that the view raises an error if the proxy model
    does not have a row_double_clicked attribute."""
    with pytest.raises(AttributeError) as e:
        model = DownloadableAtlasesProxyModel()
        del model.row_double_clicked
        _ = AtlasView(model)
    assert "row_double_clicked" in e.value.args[0]


def test_hover_atlas_view(qtbot, mocker):
    """Check tooltip is called when hovering over view"""
    view = AtlasView(DownloadableAtlasesProxyModel())
    index = view.model().index(2, 1)

    get_tooltip_text_mock = mocker.patch.object(
        view.model(), "get_tooltip_text"
    )

    view.model().data(index, Qt.ToolTipRole)

    get_tooltip_text_mock.assert_called_once()
