"""
Reine, UI-unabhaengige Business-Logik fuer Filterung und Pagination der
Collection - ausgelagert aus app.py, damit sie sich ohne Streamlit-Kontext
testen laesst.
"""


def filter_releases(
    releases: list[dict],
    genres: list[str] | None = None,
    styles: list[str] | None = None,
    formats: list[str] | None = None,
    search: str | None = None,
    year_range: tuple[int, int] | None = None,
) -> list[dict]:
    """Wendet alle aktiven Filter (UND-verknuepft) auf die Release-Liste an.

    Innerhalb eines Filters (z.B. mehrere ausgewaehlte Genres) gilt ODER:
    ein Release passt, wenn mindestens eines seiner Genres ausgewaehlt ist.
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
    """Anzahl Seiten (aufgerundet), mindestens 1 - auch bei 0 Treffern soll
    es eine (leere) Seite 1 geben, statt einer Division-durch-sinnlos-0-Situation."""
    if page_size <= 0:
        raise ValueError("page_size muss positiv sein")
    return max(1, -(-item_count // page_size))  # ceil division ohne math.ceil


def clamp_page(page: int, total_pages: int) -> int:
    """Haelt die angeforderte Seite innerhalb [1, total_pages] - z.B. wenn
    ein neuer, engerer Filter weniger Seiten ergibt als die zuvor aktive Seite."""
    return min(max(page, 1), total_pages)


def paginate(items: list[dict], page: int, page_size: int) -> list[dict]:
    """Gibt die Items fuer die angefragte (1-indexierte) Seite zurueck."""
    start = (page - 1) * page_size
    return items[start : start + page_size]
