from __future__ import annotations

from data.models.media_item import MediaItem


SAMPLE_MEDIA: list[MediaItem] = [
    MediaItem(
        id="series-twin-peaks",
        title="Twin Peaks",
        media_type="series",
        description=(
            "An FBI agent investigates a murder in a strange small town with dark, "
            "surreal mystery and 1990s American atmosphere."
        ),
        release_year=1990,
        genres=["crime", "mystery", "drama"],
        moods=["dark", "surreal", "nostalgic"],
        source="sample/TMDB",
        rating=8.8,
        popularity=0.88,
    ),
    MediaItem(
        id="series-x-files",
        title="The X-Files",
        media_type="series",
        description=(
            "Two FBI agents investigate unexplained paranormal cases across America "
            "in a dark and mysterious 1990s series."
        ),
        release_year=1993,
        genres=["crime", "mystery", "sci-fi"],
        moods=["dark", "nostalgic"],
        source="sample/TMDB",
        rating=8.6,
        popularity=0.84,
    ),
    MediaItem(
        id="series-true-detective",
        title="True Detective",
        media_type="series",
        description="A dark crime anthology with philosophical detectives and intense investigations.",
        release_year=2014,
        genres=["crime", "drama", "mystery"],
        moods=["dark"],
        source="sample/TMDB",
        rating=8.9,
        popularity=0.90,
    ),
    MediaItem(
        id="music-lofi",
        title="Lo-fi Chill Beats",
        media_type="music",
        description="Soft instrumental beats for studying, relaxing and unwinding after a tiring day.",
        release_year=None,
        genres=["chill"],
        moods=["calm"],
        source="sample/Spotify",
        rating=7.8,
        popularity=0.71,
    ),
    MediaItem(
        id="music-no-surprises",
        title="No Surprises - Radiohead",
        media_type="music",
        description="A gentle alternative rock song with calm sound, melancholy, and soft vocals.",
        release_year=1997,
        genres=["drama", "chill"],
        moods=["calm", "dark", "nostalgic"],
        source="sample/Spotify",
        rating=8.5,
        popularity=0.82,
    ),
    MediaItem(
        id="game-disco-elysium",
        title="Disco Elysium",
        media_type="game",
        description="A narrative detective role-playing game with political choices, mystery and dark humor.",
        release_year=2019,
        genres=["crime", "drama"],
        moods=["dark", "surreal"],
        source="sample/Game API",
        rating=9.1,
        popularity=0.86,
    ),
    MediaItem(
        id="movie-seven",
        title="Se7en",
        media_type="movie",
        description="Two detectives hunt a serial killer in a grim, dark crime thriller.",
        release_year=1995,
        genres=["crime", "mystery", "drama"],
        moods=["dark"],
        source="sample/OMDb",
        rating=8.6,
        popularity=0.87,
    ),
    MediaItem(
        id="series-friends",
        title="Friends",
        media_type="series",
        description="A warm comedy about a group of friends navigating life and relationships in New York.",
        release_year=1994,
        genres=["comedy"],
        moods=["calm", "nostalgic"],
        source="sample/TMDB",
        rating=8.2,
        popularity=0.91,
    ),
]
