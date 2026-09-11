-- Schema fuer die Discogs-Collection.
-- In Supabase: SQL Editor -> New query -> diesen Inhalt einfuegen -> Run.

-- instance_id ist der Primary Key (nicht id/release_id), weil die Collection
-- mehrere Exemplare desselben Release enthalten kann (id waere dann doppelt).
create table if not exists releases (
    instance_id bigint primary key,      -- Discogs collection instance_id (eindeutig pro Exemplar)
    id bigint,                           -- Discogs release_id (kann mehrfach vorkommen)
    artist text,
    title text,
    year int,
    label text,
    format text,
    genres text[],                       -- z.B. {Rock, Electronic}
    styles text[],                       -- z.B. {"Deep House", "Krautrock"}
    cover_url text,
    added_at timestamptz,
    synced_at timestamptz default now()
);

create index if not exists releases_genres_idx on releases using gin (genres);
create index if not exists releases_styles_idx on releases using gin (styles);
