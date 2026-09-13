# 💿 Discogs Genre Filter

A lightweight, self-hosted tool to filter your own [Discogs](https://discogs.com)
record collection by genre, style, year, and format — something the
discogs.com collection view itself doesn't offer.

Discogs data is synced via a sync button into your own [Supabase](https://supabase.com)
(Postgres) database, then searched/filtered in a [Streamlit](https://streamlit.io)
frontend.

<!-- Add a screenshot here once you have one, e.g.: -->
<!-- ![App screenshot](docs/screenshot.png) -->

## Features

- Filter by genre, style, format, year, and free-text search (artist/title)
- Manual sync button (re-fetches the whole collection from Discogs)
- Simple password protection for personal use
- Pagination for large collections

## Setup

### 1. Get a Discogs Personal Access Token

[discogs.com/settings/developers](https://www.discogs.com/settings/developers) →
"Generate new token".

### 2. Create a Supabase project

1. Create a new project on [supabase.com](https://supabase.com) (free tier is enough)
2. In the SQL Editor, run the content of [`supabase/schema.sql`](supabase/schema.sql)
3. Under Project Settings → API: note down `SUPABASE_URL` and an API key
   (the `secret` key is recommended since the app writes to the database
   during sync — see the note in the file below)

### 3. Local setup

```bash
git clone https://github.com/<your-username>/discogs-genre-filter.git
cd discogs-genre-filter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in .env with your own values (Discogs token/username, Supabase URL/key, APP_PASSWORD)

streamlit run app.py
```

### 4. Deployment (optional, e.g. Streamlit Community Cloud)

1. Push the repo to GitHub
2. Connect the repo on [share.streamlit.io](https://share.streamlit.io)
3. Under "Secrets", enter the values from [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)
   (real values, not the placeholders)
4. The app is then reachable via a link — the password gate keeps it
   usable only by you

## Sync

The sync does not run automatically in the background — clicking
**"🔄 Sync with Discogs"** in the app re-fetches your entire collection
from Discogs and writes it (upsert) to Supabase. That's enough for
occasional use (e.g. after buying new records).

## Running tests

```bash
pip install -r requirements.txt
pytest
```

## Tech stack

- [Streamlit](https://streamlit.io) – frontend
- [Supabase](https://supabase.com) – Postgres database
- [Discogs API](https://www.discogs.com/developers) – data source

## License

MIT, see [LICENSE](LICENSE).
