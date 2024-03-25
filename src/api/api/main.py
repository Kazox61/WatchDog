from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from api.routers import user, player


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True
    ),
    Middleware(
        GZipMiddleware,
        minimum_size=500
    )
]

app = FastAPI(title="WatchDog", middleware=middleware)


routers = [
    # user.router,
    player.router,
]
for router in routers:
    app.include_router(router)


@app.get("/", include_in_schema=False, response_class=RedirectResponse)
async def docs():
    return f"/docs"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9089)
