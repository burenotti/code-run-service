import pydantic
from fastapi import (
    APIRouter, Path, WebSocket, Depends,
    WebSocketDisconnect
)

from service.messages import ProtocolError, Terminate
from service.pipelines import LanguageInfo, PipelineFactory
from service.services import (
    parse_message, ExecutionService,
    get_selector, StateError, ExecutionState
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
    if version == 'default':
        service.set_language(language, None)
    else:
        service.set_language(language, version)
    await ws.accept()
    disconnected = False
    while not disconnected:
        try:
            raw_message = await ws.receive_json(mode="text")
            message = parse_message(raw_message)
            await service.handle_message(message)
        except StateError as why:
            await ws.send_text(ProtocolError(reason=why.reason).json())
        except pydantic.ValidationError:
            await ws.send_text(ProtocolError(reason="Bad Request").json())
        except (WebSocketDisconnect, RuntimeError):
            disconnected = True
            if service.current_state != ExecutionState.terminated:
                await service.terminate(Terminate())
