"""
Pure, UI-independent business logic for filtering and paginating the
collection - extracted from app.py so it can be tested without a
Streamlit context.
"""


def filter_releases(
    releases: list[dict],
    genres: list[str] | None = None,
    styles: list[str] | None = None,
    formats: list[str] | None = None,
    search: str | None = None,
    year_range: tuple[int, int] | None = None,
) -> list[dict]:
    """Applies all active filters (AND-combined) to the release list.

    Within a single filter (e.g. several selected genres), OR applies:
    a release matches if at least one of its genres is selected.
    """
    filtered = releases

    if genres:
        wanted = set(genres)
        filtered = [r for r in filtered if set(r.get("genres") or []) & wanted]

    if styles:
        wanted = set(styles)
        filtered = [r for r in filtered if set(r.get("styles") or []) & wanted]

    if formats:
        wanted = set(formats)
        filtered = [r for r in filtered if r.get("format") in wanted]

    if search:
        needle = search.lower()
        filtered = [
            r for r in filtered
            if needle in (r.get("artist") or "").lower() or needle in (r.get("title") or "").lower()
        ]

    if year_range:
        lo, hi = year_range
        filtered = [r for r in filtered if r.get("year") and lo <= r["year"] <= hi]

    return filtered


def total_pages_for(item_count: int, page_size: int) -> int:
    """Number of pages (rounded up), at least 1 - even with 0 results there
    should be one (empty) page 1, instead of a meaningless division by 0 case."""
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    return max(1, -(-item_count // page_size))  # ceil division without math.ceil


def clamp_page(page: int, total_pages: int) -> int:
    """Keeps the requested page within [1, total_pages] - e.g. when a new,
    narrower filter results in fewer pages than the previously active page."""
    return min(max(page, 1), total_pages)


def paginate(items: list[dict], page: int, page_size: int) -> list[dict]:
    """Returns the items for the requested (1-indexed) page."""
    start = (page - 1) * page_size
    return items[start : start + page_size]
