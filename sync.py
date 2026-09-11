"""
Holt die Discogs-Collection des konfigurierten Users und schreibt sie
(upsert) in die Supabase-Tabelle `releases`.

Kann eigenstaendig laufen (python sync.py) oder aus app.py importiert
und per Button getriggert werden.
"""
import os
import time

import requests
from supabase import Client, create_client

DISCOGS_API = "https://api.discogs.com"
USER_AGENT = "discogs-genre-filter/1.0"
PAGE_SIZE = 100


def _supabase_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def _fetch_collection_page(username: str, token: str, page: int, max_attempts: int = 3) -> dict:
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            # Token bewusst per Header statt als Query-Parameter: landet die
            # URL in einer Fehlermeldung (z.B. bei einem Connection-Error),
            # waere der Token sonst im Klartext sichtbar.
            resp = requests.get(
                f"{DISCOGS_API}/users/{username}/collection/folders/0/releases",
                params={"page": page, "per_page": PAGE_SIZE},
                headers={"User-Agent": USER_AGENT, "Authorization": f"Discogs token={token}"},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Transiente Netzwerkfehler (z.B. Connection Reset) mit kurzer
            # Pause erneut versuchen, statt den ganzen Sync abbrechen zu lassen.
            last_error = e
            if attempt < max_attempts:
                time.sleep(2 * attempt)
    raise last_error


def fetch_all_releases(username: str, token: str, progress_cb=None) -> list[dict]:
    """Holt alle Seiten der Collection. progress_cb(seite, seiten_total) optional."""
    releases = []
    page = 1
    while True:
        data = _fetch_collection_page(username, token, page)
        releases.extend(data.get("releases", []))

        pagination = data.get("pagination", {})
        total_pages = pagination.get("pages", page)
        if progress_cb:
            progress_cb(page, total_pages)

        if page >= total_pages:
            break
        page += 1
        time.sleep(1)  # Discogs Rate-Limit: max 60 req/min mit Token

    return releases


def _to_row(item: dict) -> dict:
    info = item.get("basic_information", {})
    return {
        "id": info.get("id"),
        "instance_id": item.get("instance_id"),
        "artist": ", ".join(a.get("name", "") for a in info.get("artists", [])),
        "title": info.get("title"),
        "year": info.get("year") or None,
        "label": ", ".join(l.get("name", "") for l in info.get("labels", [])),
        "format": ", ".join(f.get("name", "") for f in info.get("formats", [])),
        "genres": info.get("genres", []),
        "styles": info.get("styles", []),
        "cover_url": info.get("cover_image"),
        "added_at": item.get("date_added"),
    }


def sync_discogs_to_supabase(progress_cb=None) -> int:
    """Fuehrt einen vollstaendigen Sync durch. Gibt die Anzahl synchronisierter Releases zurueck."""
    username = os.environ["DISCOGS_USERNAME"]
    token = os.environ["DISCOGS_TOKEN"]

    releases = fetch_all_releases(username, token, progress_cb=progress_cb)
    rows = [_to_row(r) for r in releases if r.get("instance_id")]

    supabase = _supabase_client()
    # In Batches upserten, um sehr grosse Collections nicht in einem Request zu senden
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("releases").upsert(batch, on_conflict="instance_id").execute()

    return len(rows)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    count = sync_discogs_to_supabase(progress_cb=lambda p, t: print(f"Seite {p}/{t}"))
    print(f"Fertig. {count} Releases synchronisiert.")
