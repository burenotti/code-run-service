from enum import Enum

from pydantic import BaseModel
from runbox.models import File

__all__ = [
    'InputMessageType', 'InputMessage',
    'AddFiles', 'Terminate', 'WriteStdin',
    'Execute', 'Restart',

    'OutputMessageType', 'ErrorType',
    'OutputMessage', 'ErrorMessage',
    'LogMessage', 'ProtocolError',
]


class InputMessageType(str, Enum):
    add_files = "add_files"
    terminate = "terminate"
    write_stdin = "write_stdin"
    execute = "execute"
    restart = "restart"


class InputMessage(BaseModel):
    type: InputMessageType


class AddFiles(InputMessage):
    type = InputMessageType.add_files
    files: list[File]


class Terminate(InputMessage):
    type = InputMessageType.terminate


class WriteStdin(InputMessage):
    type = InputMessageType.write_stdin
    content: str


class Execute(InputMessage):
    type = InputMessageType.execute
    command: list[str] | None = None


class Restart(InputMessage):
    restart = InputMessageType.restart


class OutputMessageType(str, Enum):
    log = "log"
    error = "error"


class StreamType(str, Enum):
    stdout = "stdout"
    stderr = "stdin"


class ErrorType(str, Enum):
    protocol_error = "protocol_error"
    build_error = "error"
    runtime_error = "error"


class OutputMessage(BaseModel):
    type: OutputMessageType


class LogMessage(BaseModel):
    stream: StreamType
    content: str


class ErrorMessage(OutputMessage):
    type = OutputMessageType.error
    error_type: ErrorType
    is_critical: bool
    reason: str


class ProtocolError(ErrorMessage):
    error_type = ErrorType.protocol_error
    is_critical = False
