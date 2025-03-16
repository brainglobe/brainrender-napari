import pytest

from brainrender_napari.atlas_progress_bar import AtlasProgressBar

@pytest.fixture
def progress_bar(qtbot):
  widget = AtlasProgressBar()
  qtbot.addWidget(widget)
  return widget


def test_progress_bar_initialization(progress_bar):
  """
  Test that progress bar is initialized with correct properties.
  """
  assert progress_bar.isTextVisible()
  assert not progress_bar.isVisible() # should be hidden by default
  assert "text-align: center" in progress_bar.styleSheet()


def test_update_progress(progress_bar):
  """
  Test that update_progress method updates the progress bar correctly.
  """
  assert not progress_bar.isVisible()

  progress_bar.update_progress(50, 100, "test_atlas", "Downloading")

  assert progress_bar.isVisible()
  assert progress_bar.value() == 50
  assert progress_bar.maximum() == 100

  text = progress_bar.text()
  assert "Downloading" in text
  assert "test_atlas" in text
  assert "50%" in text


def test_operation_completed(progress_bar):
  """
  Test that operation_completed hides the progress bar.
  """
  progress_bar.update_progress(50, 100, "test_atlas", "Downloading")
  assert progress_bar.isVisible()

  progress_bar.operation_completed()

  assert not progress_bar.isVisible()
  assert progress_bar.value() == progress_bar.maximum()


def test_completed_doesnt_exceed_total(progress_bar):
  """
  Test that completed value is capped at total.
  """
  progress_bar.update_progress(150, 100, "test_atlas", "Downloading")

  assert progress_bar.value() == 100