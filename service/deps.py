from typing import Callable, Awaitable

from runbox import DockerExecutor


def get_executor(url: str | None = None) -> Callable[[], Awaitable[DockerExecutor]]:
    executor: DockerExecutor | None = None
    inited = False

    async def getter() -> DockerExecutor:
        nonlocal executor
        nonlocal inited
        if not inited:
            executor = DockerExecutor(url)  # type: ignore
            inited = True
        return executor  # type: ignore

    return getter
