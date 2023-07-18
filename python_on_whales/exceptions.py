from typing import List, Optional

PARAMETER_BLACKLIST = ['--password']


def sanitized_command_string(command_launched: List[str]) -> str:
    """
    iterates through the command launched and replaces the 
    value for the paramter in the PARAMETER_BLACKLIST

    Args:
        command_launched (List[str]): The docker command launched

    Returns:
        str: the joined 'command_launched' string containing *** for the parameter sanitized
    """
    sanitized_command = command_launched.copy()
    for item in PARAMETER_BLACKLIST:
        if item in command_launched:
            sanitized_command[sanitized_command.index(item)+1] = "***"
    return " ".join(sanitized_command)


class DockerException(Exception):
    def __init__(
        self,
        command_launched: List[str],
        return_code: int,
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
    ):
        self.docker_command: List[str] = command_launched
        self.return_code: int = return_code
        if stdout is None:
            self.stdout: Optional[str] = None
        else:
            self.stdout: Optional[str] = stdout.decode()
        if stderr is None:
            self.stderr: Optional[str] = None
        else:
            self.stderr: Optional[str] = stderr.decode()
        command_launched_str = sanitized_command_string(
            command_launched=self.docker_command)
        error_msg = (
            f"The docker command executed was `{command_launched_str}`.\n"
            f"It returned with code {return_code}\n"
        )
        if stdout is not None:
            error_msg += f"The content of stdout is '{self.stdout}'\n"
        else:
            error_msg += (
                "The content of stdout can be found above the "
                "stacktrace (it wasn't captured).\n"
            )
        if stderr is not None:
            error_msg += f"The content of stderr is '{self.stderr}'\n"
        else:
            error_msg += (
                "The content of stderr can be found above the "
                "stacktrace (it wasn't captured)."
            )
        super().__init__(error_msg)


class NoSuchContainer(DockerException):
    pass


class NoSuchImage(DockerException):
    pass


class NoSuchService(DockerException):
    pass


class NotASwarmManager(DockerException):
    pass


class NoSuchVolume(DockerException):
    pass
