import re
from typing import List

from pydantic import BaseModel as OriginalBaseModel

def snakecase_to_camelcase(string):
    # https://stackoverflow.com/q/19053707
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), string)


class BaseModel(OriginalBaseModel):
    # https://medium.com/analytics-vidhya/camel-case-models-with-fast-api-and-pydantic-5a8acb6c0eee

    class Config:
        alias_generator = snakecase_to_camelcase
        allow_population_by_field_name = True


class Game(BaseModel):
    id: int
    name: str
    manifest_path: str
    install_path: str
    size: int
    store_url: str
    img_url: str


class Library(BaseModel):
    id: int
    path: str
    install_path: str
    apps_path: str
    size: int
    free_bytes: int
    games: List[Game]


class Archive(Library):
    max_size: int