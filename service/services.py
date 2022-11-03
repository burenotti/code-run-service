import asyncio
from asyncio import Queue
from enum import Enum
from functools import singledispatchmethod
from pathlib import Path
from typing import Any, Type, TypeVar, Protocol, AsyncGenerator

from fastapi import Depends
from runbox import DockerExecutor
from runbox.build_stages import (
    Pipeline, BasePipeline,
    StreamType
)
from starlette.websockets import WebSocket

from service import messages
from service.messages import (
    InputMessageType, InputMessage, Execute,
    Terminate, AddFiles, WriteStdin, Restart, LogMessage
)
from service.pipelines import PipelineFactory
from service.settings import settings

T = TypeVar('T', covariant=True)


class AsyncGetter(Protocol[T]):

    async def __call__(self) -> T:
        ...


def pipeline_singleton(
        dir_path: Path,
        stages_map: dict[str, str] | None = None,
        class_: Type[Pipeline] = BasePipeline,
) -> AsyncGetter[PipelineFactory]:
    factory: PipelineFactory | None = None
    stages = stages_map or dict(settings.runbox.stages)

    async def get() -> PipelineFactory:
        nonlocal factory
        if factory is None:
            factory = PipelineFactory.load_pipelines(dir_path, stages, class_)
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


class ExecutionService:
    class State(str, Enum):
        setup = "code_setup"
        run = "run"
        finish = "finish"

    def __init__(
            self,
            selector: PipelineFactory = Depends(get_selector),
            executor: DockerExecutor = Depends(get_executor),
            observer: WebsocketObserver = Depends(get_websocket_observer),
    ):
        self.current_state = self.State.setup
        self.observer = observer
        self.executor = executor
        self.selector = selector
        self.initial_state: dict[str, Any] = {
            'code': [],
        }
        self.pipeline: Pipeline | None = None
        self.pipeline_task: asyncio.Task[None] | None = None

    def set_language(self, language: str, version: str) -> None:
        print("Set language:", language, version)
        self.pipeline = self.selector.get(language, version)
        self.pipeline.with_observer(self.observer)
        self.pipeline.with_executor(self.executor)

    @singledispatchmethod
    async def handle_message(self, message: Any) -> None:
        print("Unprocessable message: ", message)

    @handle_message.register
    async def write_files(self, message: AddFiles):
        print("Write:", message.files)
        self.initial_state['code'].extend(message.files)
        self.pipeline.with_initial_state(self.initial_state)  # type: ignore

    @handle_message.register
    async def terminate(self, _: Terminate) -> None:
        if self.pipeline_task is not None:
            self.pipeline_task.cancel()

    @handle_message.register
    async def run(self, message: Execute):
        print("Execute", message.command)

        async def task():
            await self.pipeline.execute_group('setup')
            await self.pipeline.execute_group('run')

        self.pipeline_task = asyncio.create_task(task())

    @handle_message.register
    async def write_stdin(self, message: WriteStdin) -> None:
        print("WriteStdin: ", message.content)
        await self.observer.put_stdin(message.content)
