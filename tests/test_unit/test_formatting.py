import pytest

from brainrender_napari.utils.formatting import format_atlas_name, format_bytes


def test_format_bytes():
    """
    Test if the format_bytes function converts units correctly.
    """
    assert format_bytes(500)
    assert format_bytes(500) == "500.00 B"
    assert format_bytes(1500) == "1.46 KB"
    assert format_bytes(1500000) == "1.43 MB"
    assert format_bytes(1500000000) == "1.40 GB"
    assert format_bytes(1500000000000) == "1.36 TB"


@pytest.mark.parametrize(
    "input_name, expected_output",
    [
        ("allen_mouse_100um", "Allen mouse (100 μm)"),
        ("example_mouse_100um", "Example mouse (100 μm)"),
        ("osten_mouse_100um", "Osten mouse (100 μm)"),
        ("allen_mouse_10um", "Allen mouse (10 μm)"),
        ("allen_human_500um", "Allen human (500 μm)"),
        ("kim_dev_mouse_25um", "Kim dev mouse (25 μm)"),
    ],
)
def test_format_atlas_name(input_name, expected_output):
    """Test that atlas names are formatted correctly with proper capitalization
    and micron symbol."""
    assert format_atlas_name(input_name) == expected_output


def test_format_atlas_name_capitalization():
    """Test that only the first word is capitalized."""
    result = format_atlas_name("allen_mouse_100um")
    assert result.startswith("Allen")
    assert "mouse" in result  # Should not be capitalized


def test_format_atlas_name_micron_symbol():
    """Test that the micron symbol (µm) is properly inserted."""
    result = format_atlas_name("example_mouse_100um")
    assert "μm" in result
    assert "(100 μm)" in result


def test_format_atlas_name_handles_different_resolutions():
    """Test formatting with various resolution values."""
    assert "(10 μm)" in format_atlas_name("test_atlas_10um")
    assert "(25 μm)" in format_atlas_name("test_atlas_25um")
    assert "(50 μm)" in format_atlas_name("test_atlas_50um")
    assert "(100 μm)" in format_atlas_name("test_atlas_100um")
    assert "(500 μm)" in format_atlas_name("test_atlas_500um")
