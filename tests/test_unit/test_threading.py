from importlib import reload

import napari.qt

from brainrender_napari.utils import threading


def test_apply_on_atlas_in_thread(qtbot, mocker):
    """
    Checks the apply_on_atlas_in_thread function
    - calls its first argument (a function) on its second argument (a string)
    - returns its second argument

    We manually replace the @thread_worker decorator during this test,
    so the function is executed in the same thread. This ensures
    coverage picks up lines inside the method.
    """

    # replace the @thread_worker decorator with an identity function
    def identity(func):
        return func

    napari.qt.thread_worker = identity
    reload(threading)
    assert threading.thread_worker == identity

    # check that mock_dummy_apply is applied as expected
    mock_dummy_apply = mocker.Mock()
    actual = threading.apply_on_atlas_in_thread(
        mock_dummy_apply, "example_mouse_100um"
    )
    expected = "example_mouse_100um"
    assert actual == expected
    mock_dummy_apply.assert_called_once_with(expected)
