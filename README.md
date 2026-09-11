# 💿 Discogs Genre Filter

Ein schlankes, selbst gehostetes Tool, um die eigene [Discogs](https://discogs.com)
Plattensammlung nach Genre, Style, Jahr und Format zu filtern — etwas, das
discogs.com selbst in der Collection-Ansicht nicht bietet.

Discogs-Daten werden per Sync-Button in eine eigene [Supabase](https://supabase.com)
(Postgres) Datenbank geschrieben und dann in einem [Streamlit](https://streamlit.io)
Frontend durchsucht/gefiltert.

## Features

- Filter nach Genre, Style, Format, Jahr und Freitextsuche (Artist/Titel)
- Manueller Sync-Button (holt die komplette Collection neu von Discogs)
- Einfacher Passwortschutz für den persönlichen Gebrauch

## Setup

### 1. Discogs Personal Access Token holen

[discogs.com/settings/developers](https://www.discogs.com/settings/developers) →
"Generate new token".

### 2. Supabase-Projekt anlegen

1. Neues Projekt auf [supabase.com](https://supabase.com) erstellen (Free Tier reicht)
2. Im SQL Editor den Inhalt von [`supabase/schema.sql`](supabase/schema.sql) ausführen
3. Unter Project Settings → API: `SUPABASE_URL` und einen Key (`anon` reicht für
   dieses Setup, da nur du Zugriff hast) notieren

### 3. Lokal einrichten

```bash
git clone https://github.com/<dein-username>/discogs-genre-filter.git
cd discogs-genre-filter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env mit deinen Werten befüllen (Discogs Token/Username, Supabase URL/Key, APP_PASSWORD)

streamlit run app.py
```

### 4. Deployment (optional, z.B. Streamlit Community Cloud)

1. Repo auf GitHub pushen
2. Auf [share.streamlit.io](https://share.streamlit.io) das Repo verbinden
3. Unter "Secrets" die Werte aus [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)
   eintragen (echte Werte, nicht die Platzhalter)
4. App ist dann per Link erreichbar — durch den Passwortschutz bleibt sie
   trotzdem nur für dich nutzbar

## Sync

Der Sync läuft nicht automatisch im Hintergrund — Klick auf **"🔄 Mit Discogs
synchronisieren"** in der App holt deine komplette Collection neu von Discogs
und schreibt sie (upsert) in Supabase. Reicht für den gelegentlichen Gebrauch
(z.B. nach dem Kauf neuer Platten).

## Tech Stack

- [Streamlit](https://streamlit.io) – Frontend
- [Supabase](https://supabase.com) – Postgres-Datenbank
- [Discogs API](https://www.discogs.com/developers) – Datenquelle

## Lizenz

MIT, siehe [LICENSE](LICENSE).
