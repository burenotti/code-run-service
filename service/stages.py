from pathlib import Path

from pydantic import BaseModel
from runbox import Mount
from runbox.build_stages import BuildState, SharedState
from runbox.models import DockerProfile, File


class WriteFiles:
    class Params(BaseModel):
        key: str
        file_keys: list[str]
        volume: str
        profile: DockerProfile

    def __init__(self, params: Params):
        self._is_setup = False
        self._is_disposed = False
        self.params = params

    @property
    def is_setup(self) -> bool:
        return self._is_setup

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @staticmethod
    def get_files(keys: list[str], shared: SharedState) -> list[File]:
        collected_files: list[File] = []
        for key in keys:
            if files := shared.get(key):
                if isinstance(files, list) and all(isinstance(f, File) for f in files):
                    collected_files.extend(files)
                elif isinstance(files, File):
                    collected_files.append(files)
                else:
                    raise TypeError("Value is not a file or list of files")
            else:
                raise KeyError(f"Key '{key}' is not in shared state")
        return collected_files

    async def setup(self, state: BuildState) -> None:
        self._is_setup = True
        files = self.get_files(self.params.file_keys, state.shared)
        sandbox = await state.executor.create_container(
            DockerProfile(
                image="alpine:latest",
                cmd_template=None,
                workdir=Path('/tmp'),
                user='root',
            ),
            mounts=[
                Mount(
                    volume=state.shared[self.params.volume],
                    bind=Path('/tmp'),
                    readonly=False
                )
            ],
            files=files
        )
        await sandbox.delete()

    async def dispose(self) -> None:
        self._is_disposed = True
