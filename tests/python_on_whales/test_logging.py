import logging

import python_on_whales.utils


def test_null_handler():
    logger = logging.getLogger("python_on_whales")
    assert any(isinstance(handler, logging.NullHandler) for handler in logger.handlers)


def test_default_level_is_debug():
    logger = logging.getLogger("python_on_whales")
    assert logger.level == logging.DEBUG


def test_logging_debug_env_var_disabled(caplog, monkeypatch):
    monkeypatch.setenv("PYTHON_ON_WHALES_DEBUG", "0")
    caplog.set_level(logging.DEBUG)
    command = ["echo", "hello"]
    python_on_whales.utils.run(command)
    assert " ".join(command) in caplog.text


def test_logging_debug_env_var_enabled(caplog, monkeypatch):
    monkeypatch.setenv("PYTHON_ON_WHALES_DEBUG", "1")
    caplog.set_level(logging.DEBUG)
    command = ["echo", "hello"]
    python_on_whales.utils.run(command)
    assert " ".join(command) not in caplog.text
