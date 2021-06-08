import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from common.config import config
from common.database import Mongo
from routes import api, vrc, views

app = FastAPI(
    title="Discord2VRC",
    description="Web app for Discord2VRC",
    version="0.0.1",
    openapi_tags=[
        {"name": "api", "description": "Api endpoints"},
        {"name": "vrc", "description": "Endpoints for use in VRChat"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", Mongo.connect)
app.add_event_handler("shutdown", Mongo.close)
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(vrc.router, prefix="/vrc", tags=["vrc"])
app.include_router(views.router)
app.mount(
    "/",
    StaticFiles(directory=config["directories"]["staticdir"]),
    name="static",
)

if __name__ == "__main__":

    uvicorn.run("web:app", host="0.0.0.0", port=5000, reload=True)
