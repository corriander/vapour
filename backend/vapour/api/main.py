from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .. import steam
from .models import Library, Game, Archive

app = FastAPI(title="Vapour API", openapi_url="/openapi.json")
api_router = APIRouter()

origins = [
    "http://localhost:3000",
    "localhost:3000",
    "http://127.0.0.1:3000",
    "127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@api_router.get("/", tags=['root'])
async def read_root() -> dict:
    return {"message": "no data here"}


@api_router.get("/libraries/")
def read_libraries():
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.libs)]


@api_router.get("/libraries/{id}", response_model=Library)
def read_library(id: int):
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.libs)][id]


@api_router.get("/archives/")
def read_archives():
    return [Archive(id=i, **dict(lib)) for i, lib in enumerate(steam.archives)]


@api_router.get("/archives/{archive_id}/games/")
def read_archive_games(archive_id: int):
    return [Game(**dict(game)) for game in steam.archives[archive_id].games]


@api_router.get("/libraries/{library_id}/games/")
def read_library_games(library_id: int):
    return [Game(**dict(game)) for game in steam.libs[library_id].games]


@api_router.get("/games/")
def read_all_games():
    return [Game(**dict(game)) for lib in steam.libs for game in lib.games]


@api_router.get("/games/{game_id}", response_model=Game)
def read_game(game_id: int):
    return {
        game.id: game
        for game in [Game(**dict(game)) for lib in steam.libs for game in lib.games]
    }[game_id]


@api_router.get("/archived-games/")
def read_all_games():
    return [Game(**dict(game)) for archive in steam.archives for game in archive.games]


@api_router.get("/archived-games/{game_id}", response_model=Game)
def read_game(game_id: int):
    return {
        game.id: game
        for game in [
            Game(**dict(game)) for archive in steam.archives for game in archive.games
        ]
    }[game_id]


app.include_router(api_router)


def run():
    import uvicorn

    uvicorn.run(
        "vapour.api.main:app", host="0.0.0.0", port=8001, log_level="debug", reload=True
    )
