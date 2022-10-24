from pydantic import BaseSettings, BaseModel


class UvicornSetting(BaseModel):
    host: str = '127.0.0.1'
    port: int = '8080'
    workers: int = 1
    reload: bool = True


class Settings(BaseSettings):
    uvicorn: UvicornSetting


settings = Settings(
    _env_file='.env',
    _env_file_encoding='utf-8',
)
