from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import steam
from .models import Library, Game

app = FastAPI()

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
    allow_headers=['*']
)

@app.get("/", tags=['root'])
async def read_root() -> dict:
    return {"message": "no data here"}

@app.get("/libraries/")
def read_libraries():
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.libs)]

@app.get("/libraries/{id}", response_model=Library)
def read_library(id: int):
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.libs)][id]

@app.get("/archives/")
def read_archives():
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.archives)]

@app.get("/libraries/{library_id}/games/")
def read_library_games(library_id: int):
    return [Game(**dict(game)) for game in steam.libs[library_id].games]

@app.get("/games/")
def read_all_games():
    return [Game(**dict(game)) for lib in steam.libs for game in lib.games]

@app.get("/games/{game_id}", response_model=Game)
def read_game(game_id: int):
    return {game.id: game for game in [Game(**dict(game)) for lib in steam.libs for game in lib.games]}[game_id]