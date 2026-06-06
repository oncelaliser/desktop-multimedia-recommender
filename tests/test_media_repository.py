import sqlite3

from data.db.repositories.media_repository import MediaRepository
from data.models.media_item import MediaItem


def _repo() -> MediaRepository:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return MediaRepository(conn)


def _item(id: str = "test-1", media_type: str = "movie") -> MediaItem:
    return MediaItem(
        id=id,
        title="Test Film",
        media_type=media_type,
        description="A test item.",
        release_year=2020,
        genres=["drama"],
        moods=["dark"],
        source="test",
        external_id="tt1234567",
        rating=7.5,
        popularity=0.5,
    )


def test_save_and_list() -> None:
    repo = _repo()
    repo.save(_item())
    items = repo.list_media()
    assert len(items) == 1
    assert items[0].title == "Test Film"
    assert items[0].genres == ["drama"]
    assert items[0].rating == 7.5


def test_save_many_and_count() -> None:
    repo = _repo()
    repo.save_many([_item("a"), _item("b"), _item("c")])
    assert repo.count() == 3


def test_filter_by_media_type() -> None:
    repo = _repo()
    repo.save(_item("m1", "movie"))
    repo.save(_item("s1", "series"))
    movies = repo.list_media(media_type="movie")
    assert len(movies) == 1
    assert movies[0].media_type == "movie"


def test_cache_set_and_get() -> None:
    repo = _repo()
    repo.cache_set("tmdb:crime:1", "TMDB", '{"results": []}')
    result = repo.cache_get("tmdb:crime:1")
    assert result == '{"results": []}'


def test_cache_miss_returns_none() -> None:
    repo = _repo()
    assert repo.cache_get("nonexistent") is None


def test_upsert_on_duplicate_id() -> None:
    repo = _repo()
    repo.save(_item())
    updated = MediaItem(
        id="test-1", title="Updated", media_type="movie",
        description="", release_year=2021, source="test",
    )
    repo.save(updated)
    items = repo.list_media()
    assert len(items) == 1
    assert items[0].title == "Updated"
