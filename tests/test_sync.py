"""
Tests for the Discogs -> DB row conversion in sync.py. This is the spot
with the most "business logic" in the sync (merging multiple artists/
labels/formats, handling missing fields) - and exactly where real bugs
have happened in the past (missing 'year', multiple copies of the same
release).
"""
from sync import _to_row

DISCOGS_ITEM = {
    "instance_id": 286003969,
    "date_added": "2018-03-12T18:50:47-07:00",
    "basic_information": {
        "id": 3991,
        "title": "Leave Me Now",
        "year": 2001,
        "formats": [{"name": "Vinyl"}],
        "labels": [{"name": "!K7 Records"}],
        "artists": [{"name": "Matthew Herbert"}],
        "genres": ["Electronic"],
        "styles": ["House"],
        "cover_image": "https://example.com/cover.jpg",
    },
}


def test_to_row_maps_basic_fields():
    row = _to_row(DISCOGS_ITEM)
    assert row["instance_id"] == 286003969
    assert row["id"] == 3991
    assert row["artist"] == "Matthew Herbert"
    assert row["title"] == "Leave Me Now"
    assert row["year"] == 2001
    assert row["genres"] == ["Electronic"]
    assert row["styles"] == ["House"]


def test_to_row_joins_multiple_artists_and_labels():
    item = {
        "instance_id": 1,
        "basic_information": {
            "id": 1,
            "artists": [{"name": "A"}, {"name": "B"}],
            "labels": [{"name": "Label X"}, {"name": "Label Y"}],
            "formats": [{"name": "Vinyl"}, {"name": "12\""}],
        },
    }
    row = _to_row(item)
    assert row["artist"] == "A, B"
    assert row["label"] == "Label X, Label Y"
    assert row["format"] == "Vinyl, 12\""


def test_to_row_handles_missing_optional_fields_gracefully():
    # e.g. releases without a known release year (Discogs often returns 0)
    item = {"instance_id": 2, "basic_information": {"id": 2, "year": 0}}
    row = _to_row(item)
    assert row["year"] is None
    assert row["artist"] == ""
    assert row["genres"] == []
