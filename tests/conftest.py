import json
import os
from pathlib import Path

import pytest
from brainglobe_atlasapi import (
    BrainGlobeAtlas,
    config,
    descriptors,
    list_atlases,
)
from brainglobe_atlasapi.list_atlases import (
    get_downloaded_atlases,
    get_local_atlas_version,
)
from qtpy.QtCore import Qt


def _local_atlas_version_dir(atlas_name, version=None):
    """Local directory holding a specific version of a downloaded atlas.

    Mirrors the layout the atlas API uses on disk. If ``version`` is None the
    currently downloaded version (folder form, e.g. ``3_0``) is used.
    """
    if version is None:
        version = get_local_atlas_version(atlas_name).replace(".", "_")
    return (
        config.get_brainglobe_dir()
        / "brainglobe-atlasapi"
        / descriptors.V3_ATLAS_ROOTDIR
        / atlas_name
        / version
    )


@pytest.fixture(autouse=True)
def mock_brainglobe_user_folders(monkeypatch):
    """Ensures user config and data is mocked during all local testing.

    User config and data need mocking to avoid interfering with user data.
    Mocking is achieved by turning user data folders used in tests into
    subfolders of a new ~/.brainglobe-tests folder instead of ~/.

    It is not sufficient to mock the home path in the tests, as this
    will leave later imports in other modules unaffected.

    GH actions workflow will test with default user folders.
    """
    if not os.getenv("GITHUB_ACTIONS"):
        home_path = Path.home()  # actual home path
        mock_home_path = home_path / ".brainglobe-tests"
        if not mock_home_path.exists():
            mock_home_path.mkdir()

        def mock_home():
            return mock_home_path

        monkeypatch.setattr(Path, "home", mock_home)

        # also mock global variables of config.py
        monkeypatch.setattr(
            config, "DEFAULT_PATH", mock_home_path / ".brainglobe"
        )
        monkeypatch.setattr(
            config, "CONFIG_DIR", mock_home_path / ".config" / "brainglobe"
        )
        monkeypatch.setattr(
            config, "CONFIG_PATH", config.CONFIG_DIR / config.CONFIG_FILENAME
        )
        mock_default_dirs = {
            "default_dirs": {
                "brainglobe_dir": mock_home_path / ".brainglobe",
                "interm_download_dir": mock_home_path / ".brainglobe",
            }
        }
        monkeypatch.setattr(config, "TEMPLATE_CONF_DICT", mock_default_dirs)


@pytest.fixture(autouse=True)
def setup_preexisting_local_atlases():
    """Automatically setup all tests to have three downloaded atlases
    in the test user data."""
    preexisting_atlases = [
        "example_mouse_100um",
        "allen_mouse_100um",
        "osten_mouse_100um",
    ]
    downloaded_atlases = get_downloaded_atlases()
    for atlas_name in preexisting_atlases:
        if atlas_name not in downloaded_atlases:
            _ = BrainGlobeAtlas(atlas_name)

    # Mock an additional reference for the example mouse.
    manifest_path = (
        _local_atlas_version_dir("example_mouse_100um") / "manifest.json"
    )
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            metadata_dict = json.loads(f.read())
        metadata_dict["additional_references"] = [
            {
                "name": "reference",
                "location": metadata_dict["template"]["location"],
            }
        ]
        with open(manifest_path, "w") as f:
            json.dump(metadata_dict, f, indent=4)


@pytest.fixture
def atlas_row():
    """Look up a model row by atlas name."""

    def _atlas_row(model, atlas_name):
        names = [model.index(row, 0).data() for row in range(model.rowCount())]
        return names.index(atlas_name)

    return _atlas_row


@pytest.fixture
def double_click_on_view(qtbot):
    """Fixture to avoid code repetition to emulate double-click on a view."""

    def inner_double_click_on_view(view, index):
        viewport_index_position = view.visualRect(index).center()

        # weirdly, to correctly emulate a double-click
        # you need to click first. Also, note that the view
        # needs to be interacted with via its viewport
        qtbot.mouseClick(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            pos=viewport_index_position,
        )
        qtbot.mouseDClick(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            pos=viewport_index_position,
        )

    return inner_double_click_on_view


@pytest.fixture
def mock_newer_atlas_version_available():
    """Simulate a locally downloaded atlas being out of date."""
    assert (
        list_atlases.folder_version_to_dotted(
            list_atlases.get_local_atlas_version("example_mouse_100um")
        )
        == list_atlases.get_atlases_lastversions()["example_mouse_100um"][
            "latest_version"
        ]
    ), "example_mouse_100um is expected to be up to date before mocking"

    older_version = "2_0"
    current_version_path = _local_atlas_version_dir("example_mouse_100um")
    older_version_path = _local_atlas_version_dir(
        "example_mouse_100um", older_version
    )
    assert current_version_path.exists() and not older_version_path.exists()

    current_version_path.rename(older_version_path)
    assert older_version_path.exists() and not current_version_path.exists()
    assert list_atlases.get_local_atlas_version(
        "example_mouse_100um"
    ) == older_version.replace("_", ".")

    yield  # run test with outdated version

    # cleanup: ensure version is up-to-date again
    if older_version_path.exists():
        older_version_path.rename(current_version_path)
    assert current_version_path.exists() and not older_version_path.exists()
