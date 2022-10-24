import uvicorn

from service.app import app
from service.settings import settings

if __name__ == '__main__':
    uvicorn.run(
        app=app,
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        reload=settings.uvicorn.reload,
        workers=settings.uvicorn.workers,
    )