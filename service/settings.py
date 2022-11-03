from pathlib import Path
from typing import Mapping

from pydantic import BaseSettings, BaseModel


class RunboxSettings(BaseModel):
    docker_url: str | None = None
    cfg_dir: Path = './pipelines'

    stages: Mapping[str, str] = {
        "use_sandbox": "runbox.build_stages.stages:UseSandbox",
        "use_volume": "runbox.build_stages.stages:UseVolume",
        "write_files": "service.stages:WriteFiles"
    }


class UvicornSetting(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8080
    workers: int = 1
    reload: bool = True


class Settings(BaseSettings):
    uvicorn: UvicornSetting = UvicornSetting()
    runbox: RunboxSettings = RunboxSettings()


settings = Settings(
    _env_file='.env',
    _env_file_encoding='utf-8',
)
