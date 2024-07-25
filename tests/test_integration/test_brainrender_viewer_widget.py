"""These tests should just check that the subwidget signal and napari
are connected as expected. Lower level tests should happen in the tests
for the widget themselves."""

import pytest

from brainrender_napari.brainrender_viewer_widget import (
    BrainrenderViewerWidget,
)


@pytest.fixture
def viewer_widget(make_napari_viewer) -> BrainrenderViewerWidget:
    """Fixture to expose the atlas viewer widget to tests.

    Simultaneously acts as a smoke test that the widget
    can be instantiated without crashing."""
    viewer = make_napari_viewer()
    return BrainrenderViewerWidget(viewer)


@pytest.mark.parametrize(
    "expected_visibility, atlas",
    [
        (True, "example_mouse_100um"),  # part of downloaded data
        (False, "allen_mouse_10um"),  # not part of downloaded data
    ],
)
def test_checkbox_visibility(
    viewer_widget, mocker, expected_visibility, atlas
):
    checkbox_visibility_mock = mocker.patch(
        "brainrender_napari.brainrender_viewer_widget.QCheckBox.setVisible"
    )
    viewer_widget._on_atlas_selection_changed(atlas)
    checkbox_visibility_mock.assert_called_once_with(expected_visibility)


@pytest.mark.parametrize(
    "expected_atlas_name",
    [
        "example_mouse_100um",
        "allen_mouse_100um",
        "osten_mouse_100um",
    ],
)
def test_double_click_on_locally_available_atlas_row(
    viewer_widget, mocker, qtbot, expected_atlas_name
):
    """Check for a few local low-res atlases that double-clicking them
    on the atlas viewer view calls the expected atlas representation function.
    """
    add_atlas_to_viewer_mock = mocker.patch(
        "brainrender_napari.brainrender_viewer_widget"
        ".NapariAtlasRepresentation.add_to_viewer"
    )
    with qtbot.waitSignal(viewer_widget.atlas_viewer_view.add_atlas_requested):
        viewer_widget.atlas_viewer_view.add_atlas_requested.emit(
            expected_atlas_name
        )
    add_atlas_to_viewer_mock.assert_called_once()


def test_structure_row_double_clicked(viewer_widget, mocker):
    """Checks that when the structure view widgets emit "VS" and
    the allen_mouse_100um atlas is selected, the NapariAtlasRepresentation
    function is called in the expected way.
    """
    add_structure_to_viewer_mock = mocker.patch(
        "brainrender_napari.brainrender_viewer_widget"
        ".NapariAtlasRepresentation.add_structure_to_viewer"
    )
    viewer_widget.atlas_viewer_view.selectRow(
        4
    )  # allen_mouse_100um is in row 4

    viewer_widget.structure_view.add_structure_requested.emit("VS")
    add_structure_to_viewer_mock.assert_called_once_with("VS")


def test_add_additional_reference_selected(viewer_widget, mocker):
    """Checks that when the atlas viewer view requests an additional
    reference, the NapariAtlasRepresentation function is called in
    the expected way."""
    add_additional_reference_mock = mocker.patch(
        "brainrender_napari.brainrender_viewer_widget"
        ".NapariAtlasRepresentation.add_additional_reference"
    )
    viewer_widget.atlas_viewer_view.selectRow(5)  # mpin_zfish_1um is in row 5
    assert (
        viewer_widget.atlas_viewer_view.selected_atlas_name()
        == "mpin_zfish_1um"
    )
    additional_reference_name = "GAD1b"
    viewer_widget.atlas_viewer_view.additional_reference_requested.emit(
        additional_reference_name
    )
    add_additional_reference_mock.assert_called_once_with(
        additional_reference_name
    )


def test_show_structures_checkbox(viewer_widget, mocker):
    structure_view_refresh_mock = mocker.patch(
        "brainrender_napari.brainrender_viewer_widget.StructureView.refresh"
    )
    viewer_widget.atlas_viewer_view.selectRow(
        0
    )  # example_mouse_100um is in row 0
    structure_view_refresh_mock.assert_called_with(
        "example_mouse_100um", False
    )

    viewer_widget.show_structure_names.click()
    assert structure_view_refresh_mock.call_count == 2
    structure_view_refresh_mock.assert_called_with("example_mouse_100um", True)


def test_structure_view_tooltip(viewer_widget):
    for expected_keyword in [
        "double-click",
        "atlas region",
        "add",
        "3d",
        "mesh",
        "display",
        "toggle",
        "viewer",
    ]:
        assert (
            expected_keyword
            in viewer_widget.structure_tree_group.toolTip().lower()
        )


def test_atlas_viewer_view_tooltip(viewer_widget):
    for expected_keyword in [
        "double-click",
        "add",
        "annotations",
        "reference",
        "right-click",
        "additional",
    ]:
        assert (
            expected_keyword
            in viewer_widget.atlas_viewer_group.toolTip().lower()
        )
