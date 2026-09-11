"""
Streamlit-Frontend: zeigt die in Supabase gespeicherte Discogs-Collection
an, mit Filtern nach Genre/Style/Jahr/Format sowie einem manuellen
Sync-Button.

Passwort-Schutz: einfaches Gate ueber st.secrets["APP_PASSWORD"] bzw.
die Umgebungsvariable APP_PASSWORD (lokal via .env).
"""
import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

from filters import clamp_page, filter_releases, paginate, total_pages_for
from sync import sync_discogs_to_supabase

load_dotenv()

st.set_page_config(page_title="Meine Plattensammlung", page_icon="💿", layout="wide")


def get_secret(name: str) -> str | None:
    # st.secrets wird auf Streamlit Cloud genutzt, os.environ lokal (.env).
    # Existiert keine secrets.toml (lokaler Fall), wirft st.secrets bei jedem
    # Zugriff einen Fehler statt einfach leer zu sein -> abfangen.
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def check_password() -> bool:
    expected = get_secret("APP_PASSWORD")
    if not expected:
        st.error("APP_PASSWORD ist nicht konfiguriert (.env oder st.secrets).")
        return False

    if st.session_state.get("authenticated"):
        return True

    pw = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if pw == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    return False


@st.cache_data(ttl=60)
def load_releases() -> list[dict]:
    supabase = create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY"))

    # PostgREST liefert pro Request standardmaessig max. 1000 Zeilen - fuer
    # groessere Sammlungen muessen wir seitenweise nachladen (.range()).
    page_size = 1000
    all_rows = []
    start = 0
    while True:
        response = supabase.table("releases").select("*").range(start, start + page_size - 1).execute()
        batch = response.data
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    return all_rows


def main():
    st.title("💿 Meine Plattensammlung")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Mit Discogs synchronisieren"):
            progress = st.progress(0.0, text="Starte Sync...")

            def on_progress(page, total):
                progress.progress(page / total, text=f"Seite {page}/{total}")

            with st.spinner("Synchronisiere..."):
                count = sync_discogs_to_supabase(progress_cb=on_progress)
            st.cache_data.clear()
            st.success(f"{count} Releases synchronisiert.")

    releases = load_releases()
    if not releases:
        st.info("Noch keine Daten. Klicke auf 'Mit Discogs synchronisieren'.")
        return

    all_genres = sorted({g for r in releases for g in (r.get("genres") or [])})
    all_styles = sorted({s for r in releases for s in (r.get("styles") or [])})
    all_formats = sorted({r["format"] for r in releases if r.get("format")})

    with col1:
        st.caption(f"{len(releases)} Platten in der Sammlung")

    years = [r["year"] for r in releases if r.get("year")]
    min_year, max_year = (min(years), max(years)) if years else (None, None)

    # Alle Filter-Widgets in einem Formular: der Rerun (und damit das erneute
    # Filtern/Rendern) passiert erst beim Klick auf "Filter anwenden", nicht
    # bei jeder einzelnen Widget-Aenderung - spart Rechenzeit bei grossen
    # Sammlungen.
    with st.sidebar.form("filter_form"):
        st.header("Filter")
        selected_genres = st.multiselect("Genre", all_genres)
        selected_styles = st.multiselect("Style", all_styles)
        selected_formats = st.multiselect("Format", all_formats)
        search = st.text_input("Suche (Artist/Titel)")
        if years:
            year_range = st.slider("Jahr", min_year, max_year, (min_year, max_year))
        else:
            year_range = None
        st.form_submit_button("✅ Filter anwenden")

    filtered = filter_releases(
        releases,
        genres=selected_genres,
        styles=selected_styles,
        formats=selected_formats,
        search=search,
        year_range=year_range,
    )

    st.write(f"**{len(filtered)}** Treffer")

    # Pagination: bei Filteraenderung automatisch zurueck auf Seite 1 springen,
    # sonst wuerde man z.B. auf Seite 5 landen, obwohl der neue Filter nur
    # 2 Seiten Ergebnisse hat.
    filter_signature = (
        tuple(selected_genres), tuple(selected_styles), tuple(selected_formats),
        search, year_range,
    )
    if st.session_state.get("_filter_signature") != filter_signature:
        st.session_state["_filter_signature"] = filter_signature
        st.session_state["page"] = 1

    page_size = st.sidebar.selectbox("Eintraege pro Seite", [25, 50, 100], index=1)
    total_pages = total_pages_for(len(filtered), page_size)
    page = clamp_page(st.session_state.get("page", 1), total_pages)

    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if st.button("⬅️ Zurück", disabled=page <= 1):
            page -= 1
    with nav_cols[1]:
        st.markdown(f"<div style='text-align:center'>Seite {page} von {total_pages}</div>", unsafe_allow_html=True)
    with nav_cols[2]:
        if st.button("Weiter ➡️", disabled=page >= total_pages):
            page += 1
    st.session_state["page"] = page

    page_items = paginate(filtered, page, page_size)

    for r in page_items:
        cols = st.columns([1, 5])
        with cols[0]:
            if r.get("cover_url"):
                st.image(r["cover_url"], width=80)
        with cols[1]:
            st.markdown(f"**{r.get('artist')} — {r.get('title')}** ({r.get('year') or '?'})")
            tags = (r.get("genres") or []) + (r.get("styles") or [])
            if tags:
                st.caption(" · ".join(tags))
        st.divider()


if __name__ == "__main__":
    if check_password():
        main()
