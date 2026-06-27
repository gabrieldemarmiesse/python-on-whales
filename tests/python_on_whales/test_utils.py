import python_on_whales.utils
from python_on_whales.utils import (
    ProcessStream,
    format_cpuset,
    stream_stdout_and_stderr,
)


def test_format_cpuset_none():
    assert format_cpuset(None) is None


def test_format_cpuset_list_of_ints():
    assert format_cpuset([0, 2, 3]) == "0,2,3"


def test_format_cpuset_empty_list():
    assert format_cpuset([]) == ""


def test_format_cpuset_string_passthrough():
    # cpuset strings accepted by the CLI must be passed through unmodified so
    # ranges like "0-3" and mixes like "0-3,7" reach docker as-is.
    assert format_cpuset("0-3") == "0-3"
    assert format_cpuset("0,2") == "0,2"
    assert format_cpuset("0-3,7") == "0-3,7"


def test_format_cpuset_generator():
    assert format_cpuset(iter([1, 4])) == "1,4"


def test_environment_variables_propagation(monkeypatch):
    monkeypatch.setenv("SOME_VARIABLE", "dododada")

    stdout = python_on_whales.utils.run(
        ["bash", "-c", "echo $SOME_VARIABLE && echo $OTHER_VARIABLE"],
        capture_stdout=True,
        env={"OTHER_VARIABLE": "dudu"},
    )
    assert stdout == "dododada\ndudu"


def test_stream_stdout_and_stderr_interactive():
    proc = stream_stdout_and_stderr(["cat"], pipe_stdin=True)
    assert isinstance(proc, ProcessStream)
    proc.stdin.write(b"hello world\n")
    proc.stdin.close()
    output = list(proc)
    assert ("stdout", b"hello world\n") in output


def test_stream_stdout_and_stderr_interactive_multiple_lines():
    proc = stream_stdout_and_stderr(["cat"], pipe_stdin=True)
    proc.stdin.write(b"line1\n")
    proc.stdin.write(b"line2\n")
    proc.stdin.close()
    output = list(proc)
    stdout_lines = [line for source, line in output if source == "stdout"]
    assert b"line1\n" in stdout_lines
    assert b"line2\n" in stdout_lines


def test_stream_stdout_and_stderr_non_interactive():
    """Non-interactive mode returns ProcessStream with stdin=None."""
    result = stream_stdout_and_stderr(["echo", "hi"])
    assert isinstance(result, ProcessStream)
    assert result.stdin is None
    output = list(result)
    assert ("stdout", b"hi\n") in output
