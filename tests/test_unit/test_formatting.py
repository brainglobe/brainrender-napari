from brainrender_napari.utils.formatting import format_bytes


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
