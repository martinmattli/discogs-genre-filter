"""
Tests for the pure filter/pagination logic in filters.py.
Deliberately no syntax/type checks - only business logic where a wrong
change (e.g. AND/OR swapped, an off-by-one in pagination) would actually
give the user wrong results.
"""
from filters import clamp_page, filter_releases, paginate, total_pages_for

SAMPLE = [
    {"artist": "Herbert", "title": "Leave Me Now", "genres": ["Electronic"], "styles": ["House"], "format": "Vinyl", "year": 2001},
    {"artist": "Neu!", "title": "Neu! 75", "genres": ["Rock"], "styles": ["Krautrock"], "format": "Vinyl", "year": 1975},
    {"artist": "Aphex Twin", "title": "Ambient Works", "genres": ["Electronic"], "styles": ["Ambient", "IDM"], "format": "CD", "year": 1994},
]


def test_no_filters_returns_everything():
    assert filter_releases(SAMPLE) == SAMPLE


def test_genre_filter_is_or_within_the_same_filter():
    # A release matches if at least one of its genres is in the selection -
    # not only on an exact match.
    result = filter_releases(SAMPLE, genres=["Electronic"])
    assert {r["title"] for r in result} == {"Leave Me Now", "Ambient Works"}


def test_multiple_filter_categories_are_and_combined():
    # Genre "Electronic" AND format "CD" -> only a single match, even
    # though "Electronic" alone would have two matches.
    result = filter_releases(SAMPLE, genres=["Electronic"], formats=["CD"])
    assert [r["title"] for r in result] == ["Ambient Works"]


def test_search_is_case_insensitive_and_matches_artist_or_title():
    result = filter_releases(SAMPLE, search="APHEX")
    assert [r["title"] for r in result] == ["Ambient Works"]

    result = filter_releases(SAMPLE, search="ambient works")
    assert [r["title"] for r in result] == ["Ambient Works"]


def test_year_range_is_inclusive_on_both_ends():
    result = filter_releases(SAMPLE, year_range=(1975, 1975))
    assert [r["title"] for r in result] == ["Neu! 75"]


def test_release_without_genres_never_matches_a_genre_filter():
    releases = [{"artist": "X", "title": "Y", "genres": None, "styles": None, "format": None, "year": None}]
    assert filter_releases(releases, genres=["Rock"]) == []


def test_total_pages_rounds_up_for_a_partial_last_page():
    assert total_pages_for(item_count=101, page_size=25) == 5  # 4 full + 1 partial page
    assert total_pages_for(item_count=100, page_size=25) == 4  # divides evenly
    assert total_pages_for(item_count=0, page_size=25) == 1    # no results -> still page 1


def test_clamp_page_keeps_page_within_bounds():
    assert clamp_page(page=5, total_pages=2) == 2  # e.g. after a narrowing filter
    assert clamp_page(page=0, total_pages=2) == 1
    assert clamp_page(page=1, total_pages=1) == 1


def test_paginate_returns_correct_slice():
    items = list(range(1, 11))  # 1..10
    assert paginate(items, page=1, page_size=3) == [1, 2, 3]
    assert paginate(items, page=4, page_size=3) == [10]  # last, partial page
