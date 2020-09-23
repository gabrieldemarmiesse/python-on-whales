import python_on_whales.utils


def test_project_root():
    assert (python_on_whales.utils.PROJECT_ROOT / "setup.py").exists()
