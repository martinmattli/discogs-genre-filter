-- Schema for the Discogs collection.
-- In Supabase: SQL Editor -> New query -> paste this content -> Run.

-- instance_id is the primary key (not id/release_id), because the
-- collection can contain multiple copies of the same release (id would
-- then be duplicated).
create table if not exists releases (
    instance_id bigint primary key,      -- Discogs collection instance_id (unique per copy)
    id bigint,                           -- Discogs release_id (can occur more than once)
    artist text,
    title text,
    year int,
    label text,
    format text,
    genres text[],                       -- e.g. {Rock, Electronic}
    styles text[],                       -- e.g. {"Deep House", "Krautrock"}
    cover_url text,
    added_at timestamptz,
    synced_at timestamptz default now()
);

create index if not exists releases_genres_idx on releases using gin (genres);
create index if not exists releases_styles_idx on releases using gin (styles);
