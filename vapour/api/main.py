from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from .. import steam
from .models import Library

app = FastAPI()

def get_libraries():
    return [Library(id=i, **dict(lib)) for i, lib in enumerate(steam.libs)]

@app.get("/libraries/")
def read_libraries():
    return get_libraries()

@app.get("/libraries/{id}")
def read_library(id: int):
    return get_libraries()[id]