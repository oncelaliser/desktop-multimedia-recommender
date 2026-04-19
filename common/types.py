from __future__ import annotations

from enum import Enum


class MediaType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    MUSIC = "music"
    GAME = "game"
