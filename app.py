"""
Streamlit frontend: displays the Discogs collection stored in Supabase,
with filters by genre/style/year/format plus a manual sync button.

Password protection: a simple gate via st.secrets["APP_PASSWORD"] or the
APP_PASSWORD environment variable (locally via .env).
"""
import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

from filters import clamp_page, filter_releases, paginate, total_pages_for
from sync import sync_discogs_to_supabase

load_dotenv()

st.set_page_config(page_title="My Record Collection", page_icon="💿", layout="wide")


def get_secret(name: str) -> str | None:
    # st.secrets is used on Streamlit Cloud, os.environ locally (.env).
    # If no secrets.toml exists (the local case), st.secrets raises an error
    # on every access instead of just being empty -> catch it.
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def check_password() -> bool:
    expected = get_secret("APP_PASSWORD")
    if not expected:
        st.error("APP_PASSWORD is not configured (.env or st.secrets).")
        return False

    if st.session_state.get("authenticated"):
        return True

    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


@st.cache_data(ttl=60)
def load_releases() -> list[dict]:
    supabase = create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY"))

    # PostgREST returns at most 1000 rows per request by default - for
    # larger collections we need to page through with .range().
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
    st.title("💿 My Record Collection")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Sync with Discogs"):
            progress = st.progress(0.0, text="Starting sync...")

            def on_progress(page, total):
                progress.progress(page / total, text=f"Page {page}/{total}")

            with st.spinner("Syncing..."):
                count = sync_discogs_to_supabase(progress_cb=on_progress)
            st.cache_data.clear()
            st.success(f"{count} releases synced.")

    releases = load_releases()
    if not releases:
        st.info("No data yet. Click 'Sync with Discogs'.")
        return

    all_genres = sorted({g for r in releases for g in (r.get("genres") or [])})
    all_styles = sorted({s for r in releases for s in (r.get("styles") or [])})
    all_formats = sorted({r["format"] for r in releases if r.get("format")})

    with col1:
        st.caption(f"{len(releases)} records in the collection")

    years = [r["year"] for r in releases if r.get("year")]
    min_year, max_year = (min(years), max(years)) if years else (None, None)

    # All filter widgets in one form: the rerun (and therefore the
    # re-filtering/re-rendering) only happens on "Apply filters", not on
    # every single widget change - saves compute time for large collections.
    with st.sidebar.form("filter_form"):
        st.header("Filters")
        selected_genres = st.multiselect("Genre", all_genres)
        selected_styles = st.multiselect("Style", all_styles)
        selected_formats = st.multiselect("Format", all_formats)
        search = st.text_input("Search (artist/title)")
        if years:
            year_range = st.slider("Year", min_year, max_year, (min_year, max_year))
        else:
            year_range = None
        st.form_submit_button("✅ Apply filters")

    filtered = filter_releases(
        releases,
        genres=selected_genres,
        styles=selected_styles,
        formats=selected_formats,
        search=search,
        year_range=year_range,
    )

    st.write(f"**{len(filtered)}** results")

    # Pagination: jump back to page 1 automatically when a filter changes,
    # otherwise you might land on page 5 even though the new filter only
    # has 2 pages of results.
    filter_signature = (
        tuple(selected_genres), tuple(selected_styles), tuple(selected_formats),
        search, year_range,
    )
    if st.session_state.get("_filter_signature") != filter_signature:
        st.session_state["_filter_signature"] = filter_signature
        st.session_state["page"] = 1

    page_size = st.sidebar.selectbox("Items per page", [25, 50, 100], index=1)
    total_pages = total_pages_for(len(filtered), page_size)
    page = clamp_page(st.session_state.get("page", 1), total_pages)

    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if st.button("⬅️ Previous", disabled=page <= 1):
            page -= 1
    with nav_cols[1]:
        st.markdown(f"<div style='text-align:center'>Page {page} of {total_pages}</div>", unsafe_allow_html=True)
    with nav_cols[2]:
        if st.button("Next ➡️", disabled=page >= total_pages):
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
