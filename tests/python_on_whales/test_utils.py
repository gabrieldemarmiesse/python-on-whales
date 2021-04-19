import python_on_whales.utils


def test_project_root():
    assert (python_on_whales.utils.PROJECT_ROOT / "setup.py").exists()


def test_environment_variables_propagation(monkeypatch):
    monkeypatch.setenv("SOME_VARIABLE", "dododada")

    stdout = python_on_whales.utils.run(
        ["bash", "-c", "echo $SOME_VARIABLE && echo $OTHER_VARIABLE"],
        capture_stdout=True,
        env={"OTHER_VARIABLE": "dudu"},
    )
    assert stdout == "dododada\ndudu"
