from pathlib import Path
from typing import Mapping

from pydantic import BaseSettings, BaseModel


class RunboxSettings(BaseModel):
    docker_url: str | None = None
    cfg_dir: Path = Path('./pipelines')

    stages: Mapping[str, str] = {
        "use_sandbox": "runbox.build_stages.stages:UseSandbox",
        "use_volume": "runbox.build_stages.stages:UseVolume",
        "write_files": "runbox.build_stages.stages:WriteFiles"
    }

    class Config:
        env_prefix = 'RUNBOX__'


class UvicornSetting(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8080
    workers: int = 1
    reload: bool = True

    class Config:
        env_prefix = 'UVICORN__'


class Settings(BaseSettings):
    uvicorn: UvicornSetting = UvicornSetting()
    runbox: RunboxSettings = RunboxSettings()

    class Config:
        env_nested_delimiter = '__'


settings = Settings(
    _env_file='.env',
    _env_file_encoding='utf-8',
)
