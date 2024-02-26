import os
import shutil
from pathlib import Path

import pytest
from brainglobe_atlasapi import BrainGlobeAtlas, config, list_atlases
from qtpy.QtCore import Qt


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
        ("example_mouse_100um", "v1.2"),
        ("allen_mouse_100um", "v1.2"),
        ("osten_mouse_100um", "v1.1"),
        ("mpin_zfish_1um", "v1.0"),
    ]
    for atlas_name, version in preexisting_atlases:
        if not Path.exists(
            Path.home() / f".brainglobe/{atlas_name}_{version}"
        ):
            _ = BrainGlobeAtlas(atlas_name)


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
    current_version_path = Path.home() / ".brainglobe/example_mouse_100um_v1.2"
    older_version_path = Path.home() / ".brainglobe/example_mouse_100um_v1.1"
    assert current_version_path.exists() and not older_version_path.exists()

    current_version_path.rename(older_version_path)
    assert older_version_path.exists() and not current_version_path.exists()
    assert (
        list_atlases.get_atlases_lastversions()["example_mouse_100um"][
            "latest_version"
        ]
        == "1.2"
    )
    assert list_atlases.get_local_atlas_version("example_mouse_100um") == "1.1"

    yield  # run test with outdated version

    # cleanup: ensure version is up-to-date again
    if older_version_path.exists():
        shutil.rmtree(path=older_version_path)
        _ = BrainGlobeAtlas("example_mouse_100um")
    assert current_version_path.exists() and not older_version_path.exists()
