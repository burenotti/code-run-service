import asyncio
import sys
import uvicorn

from service.settings import settings

if __name__ == '__main__':
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        config = uvicorn.Config(
            app='service.app:app',
            host=settings.uvicorn.host,
            port=settings.uvicorn.port,
            reload=settings.uvicorn.reload,
            workers=settings.uvicorn.workers,
        )
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    else:
        uvicorn.run(
            app='service.app:app',
            host=settings.uvicorn.host,
            port=settings.uvicorn.port,
            reload=settings.uvicorn.reload,
            workers=settings.uvicorn.workers,
        )
