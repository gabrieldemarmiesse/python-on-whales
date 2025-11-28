import logging

import python_on_whales.utils


def test_debug_level_logging(caplog):
    caplog.set_level(logging.DEBUG)
    command = ["echo", "hello"]
    python_on_whales.utils.run(command)
    assert " ".join(command) in caplog.text
