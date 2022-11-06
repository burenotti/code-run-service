import pydantic
from fastapi import APIRouter, Path, WebSocket, Depends
from starlette.websockets import WebSocketDisconnect

from service.messages import ProtocolError, Terminate
from service.pipelines import LanguageInfo, PipelineFactory
from service.services import (
    parse_message, ExecutionService,
    get_selector
)

router = APIRouter(
    prefix="/code",
    tags=["Code", "Execution"],
)


@router.get('/languages')
async def languages(
        selector: PipelineFactory = Depends(get_selector)
) -> list[LanguageInfo]:
    return selector.languages()


@router.websocket('/run/{language}/{version}')
async def run_code(
        ws: WebSocket,
        language: str = Path(title="Programming Language, that will be used, to run code"),
        version: str = Path(title="Version of chosen langauge"),
        service: ExecutionService = Depends(),
):
    service.set_language(language, version)
    await ws.accept()
    while True:
        try:
            raw_message = await ws.receive_json(mode="text")
            message = parse_message(raw_message)
            await service.handle_message(message)
        except pydantic.ValidationError:
            await ws.send_json(ProtocolError(reason="Bad Request").dict())
        except WebSocketDisconnect:
            await service.terminate(Terminate())
