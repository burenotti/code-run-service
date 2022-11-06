from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Type, Mapping

from pydantic import BaseModel
from runbox.build_stages import Pipeline, load_stages, JsonPipelineLoader, PipelineLoader
from runbox.build_stages.pipeline import AsyncBasePipeline

from service.settings import settings


@dataclass(slots=True, frozen=True)
class PipelineMeta:
    language: str
    version: str
    loader: PipelineLoader
    is_default: bool = False


class LanguageInfo(BaseModel):
    language: str
    versions: list[str]
    default_version: str | None = None


class AppAsyncPipeline(AsyncBasePipeline):

    async def on_finalize(self) -> None:
        ...

    async def on_group_done(self, group: str) -> None:
        print(f"Done: {group}")

    async def on_group_failed(self, group: str) -> None:
        print(f"Failed: {group}")


class PipelineFactory:

    def __init__(self, pipelines: list[PipelineMeta]):
        self.pipelines = pipelines
        self._pipeline_class: Type[Pipeline] = AsyncBasePipeline

    def set_pipeline_class(self, class_: Type[Pipeline]) -> None:
        self._pipeline_class = class_

    def get(self, language: str, version: str) -> Pipeline:
        selected: PipelineLoader | None = None
        for pipe in self.pipelines:
            if pipe.language == language:
                if pipe.version == version:
                    selected = pipe.loader

                if pipe.is_default:
                    selected = pipe.loader

        if selected is None:
            raise ValueError(f"Suitable pipeline for {language} {version} not found")

        return selected.fill(self._pipeline_class())

    def languages(self) -> list[LanguageInfo]:
        langs = []
        for lang, group in groupby(self.pipelines, key=lambda meta: meta.language):
            default: str | None = None
            versions: list[str] = []
            item: PipelineMeta
            for item in group:
                if item.is_default:
                    default = item.version
                versions.append(item.version)
                langs.append(LanguageInfo(language=lang, versions=versions, default_version=default))
        return langs

    @classmethod
    def load_pipelines(
            cls,
            dir_path: Path | str,
            stages_map: Mapping[str, str] = settings.runbox.stages,
    ) -> "PipelineFactory":
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)

        pipelines: list[PipelineMeta] = []
        stages = load_stages(dict(stages_map))
        for file in dir_path.iterdir():
            if file.suffix == ".json" and file.is_file():
                loader = JsonPipelineLoader(
                    path=file,
                    stage_getter=lambda stage_name: stages[stage_name],
                )
                pipeline = PipelineMeta(
                    language=loader.meta['language'],
                    version=loader.meta['version'],
                    is_default=loader.meta.get('version', False),
                    loader=loader,
                )
                pipelines.append(pipeline)

        return PipelineFactory(pipelines)
