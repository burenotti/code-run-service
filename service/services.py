import enum
from asyncio import Queue
from enum import Enum
from functools import singledispatchmethod
from pathlib import Path
from typing import Any, Type, TypeVar, Protocol, AsyncGenerator

from fastapi import Depends
from runbox import DockerExecutor
from runbox.build_stages import (
    Pipeline,
    StreamType
)
from runbox.build_stages.pipeline import AsyncBasePipeline
from starlette.websockets import WebSocket

from service import messages
from service.messages import (
    InputMessageType, InputMessage, Execute,
    Terminate, AddFiles, WriteStdin, Restart, LogMessage
)
from service.pipelines import PipelineFactory, AppAsyncPipeline
from service.settings import settings

T = TypeVar('T', covariant=True)


class AsyncGetter(Protocol[T]):

    async def __call__(self) -> T:
        ...


def pipeline_singleton(
        dir_path: Path,
        stages_map: dict[str, str] | None = None,
        class_: Type[Pipeline] = AppAsyncPipeline,
) -> AsyncGetter[PipelineFactory]:
    factory: PipelineFactory | None = None
    stages = stages_map or dict(settings.runbox.stages)

    async def get() -> PipelineFactory:
        nonlocal factory
        if factory is None:
            factory = PipelineFactory.load_pipelines(dir_path, stages)
            factory.set_pipeline_class(class_)
        return factory

    return get


def executor_singleton(url: str | None = None) -> AsyncGetter[DockerExecutor]:
    executor: DockerExecutor | None = None

    async def get() -> DockerExecutor:
        nonlocal executor
        if executor is None:
            executor = DockerExecutor(url)

        return executor

    return get


get_selector = pipeline_singleton(settings.runbox.cfg_dir)
get_executor = executor_singleton(settings.runbox.docker_url)


class WebsocketObserver:

    def __init__(self, ws: WebSocket):
        self.ws = ws
        self._stdin: Queue[str] = Queue()

    async def put_stdin(self, data: str) -> None:
        await self._stdin.put(data)

    @property
    async def stdin(self) -> AsyncGenerator[str, None]:
        while data := await self._stdin.get():
            yield data

    async def write_output(self, key: str, data: str, stream: StreamType):
        if stream == 1:
            message = LogMessage(content=data, stream=messages.StreamType.stdout)
        else:
            message = LogMessage(content=data, stream=messages.StreamType.stderr)

        await self.ws.send_text(message.json())


def get_websocket_observer(
        observer: WebsocketObserver = Depends(),
) -> WebsocketObserver:
    return observer


def parse_message(message: dict[str, Any]) -> InputMessage:
    type_map = {
        InputMessageType.execute: Execute,
        InputMessageType.terminate: Terminate,
        InputMessageType.add_files: AddFiles,
        InputMessageType.write_stdin: WriteStdin,
        InputMessageType.restart: Restart
    }

    message_type = InputMessage.parse_obj(message).type

    if message_type not in type_map:
        raise ValueError("Message type is incorrect")

    return type_map[message_type].parse_obj(message)


class ExecutionState(str, enum.Enum):
    setup = "setup"
    running = "running"
    finished = "finished"
    terminated = "terminated"


class StateError(Exception):

    def __init__(self, reason: str, state: ExecutionState):
        super().__init__(reason, state)
        self.reason = reason
        self.state = state


class ExecutionService:

    def __init__(
            self,
            ws: WebSocket,
            selector: PipelineFactory = Depends(get_selector),
            executor: DockerExecutor = Depends(get_executor),
            observer: WebsocketObserver = Depends(get_websocket_observer),
    ):
        self.ws = ws
        self.current_state = ExecutionState.setup
        self.observer = observer
        self.executor = executor
        self.selector = selector
        self.pipeline: AsyncBasePipeline | None = None
        self.initial_state: dict[str, Any] = {
            'code': [],
        }

    def set_language(self, language: str, version: str | None = None) -> None:
        print("Set language:", language, version)
        self.pipeline = self.selector.get(language, version)
        assert self.pipeline is not None
        self.pipeline.with_observer(self.observer)
        self.pipeline.with_executor(self.executor)

    @singledispatchmethod
    async def handle_message(self, message: Any) -> None:
        print("Unprocessable message: ", message)

    @handle_message.register
    async def write_files(self, message: AddFiles):
        if self.current_state != ExecutionState.setup:
            raise StateError("Writing files is not allowed on this step", self.current_state)

        print("Write:", message.files)
        self.initial_state['code'].extend(message.files)
        self.pipeline.with_initial_state(self.initial_state)  # type: ignore

    @handle_message.register
    async def terminate(self, _: Terminate) -> None:
        assert self.pipeline is not None

        if self.current_state != ExecutionState.running:
            raise StateError("Can't terminate sandbox, which is not running", self.current_state)

        self.current_state = ExecutionState.terminated
        await self.pipeline.terminate()
        await self.ws.close()

    @handle_message.register
    async def run(self, _: Execute):
        if self.current_state == ExecutionState.running:
            raise StateError("Sandbox is already running", self.current_state)
        elif self.current_state in (ExecutionState.finished, ExecutionState.terminated):
            raise StateError("Sandbox can be started only once", self.current_state)
        elif self.current_state != ExecutionState.setup:
            raise StateError("Can't execution is not allowed on this step", self.current_state)

        self.current_state = ExecutionState.running
        if self.pipeline is not None:
            for group in self.pipeline.groups:
                await self.pipeline.execute_group(group.name)

    @handle_message.register
    async def write_stdin(self, message: WriteStdin) -> None:
        if self.current_state != ExecutionState.running:
            raise StateError("Can write stdin only in running sandbox", self.current_state)
        print("WriteStdin: ", message.content)
        await self.observer.put_stdin(message.content)
