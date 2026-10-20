-- F19/F20/F21 PROPOSAL ONLY. DO NOT EXECUTE without explicit migration approval.
-- Additive structures: never drop, truncate, update, or backfill existing rows.
BEGIN;

CREATE TABLE IF NOT EXISTS public.traffic_collection_runs (
    id uuid PRIMARY KEY,
    scheduled_for timestamptz NOT NULL UNIQUE,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    outcome text NOT NULL DEFAULT 'running'
        CHECK (outcome IN ('running', 'success', 'partial', 'failed')),
    count_total integer NOT NULL DEFAULT 3 CHECK (count_total >= 0),
    count_succeeded integer NOT NULL DEFAULT 0 CHECK (count_succeeded >= 0),
    count_failed integer NOT NULL DEFAULT 0 CHECK (count_failed >= 0),
    safe_error_code text
);

CREATE TABLE IF NOT EXISTS public.traffic_observations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES public.traffic_collection_runs(id),
    origin text NOT NULL,
    destination text NOT NULL,
    retrieved_at timestamptz NOT NULL,
    distance_m integer NOT NULL CHECK (distance_m > 0),
    duration_seconds integer CHECK (duration_seconds >= 0),
    total_road_count integer NOT NULL CHECK (total_road_count >= 0),
    congested_count integer NOT NULL CHECK (congested_count >= 0),
    congested_distance_m integer NOT NULL CHECK (congested_distance_m >= 0),
    congestion_ratio numeric(7,3) NOT NULL CHECK (congestion_ratio BETWEEN 0 AND 100),
    source text NOT NULL DEFAULT 'kakao' CHECK (source = 'kakao'),
    UNIQUE (run_id, origin, destination)
);

CREATE TABLE IF NOT EXISTS public.traffic_article_publication (
    article_id bigint PRIMARY KEY REFERENCES public.traffic_news_articles(id),
    status text NOT NULL CHECK (status IN ('review', 'published', 'held')),
    changed_at timestamptz NOT NULL DEFAULT now(),
    changed_by text NOT NULL
);
CREATE TABLE IF NOT EXISTS public.traffic_article_publication_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    article_id bigint NOT NULL REFERENCES public.traffic_news_articles(id),
    old_status text,
    new_status text NOT NULL CHECK (new_status IN ('review', 'published', 'held')),
    changed_at timestamptz NOT NULL DEFAULT now(),
    changed_by text NOT NULL,
    note text
);
CREATE INDEX IF NOT EXISTS traffic_article_publication_events_article_time
    ON public.traffic_article_publication_events(article_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS public.traffic_operational_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_time timestamptz NOT NULL DEFAULT now(),
    source text NOT NULL CHECK (source IN ('kakao', 'collector', 'database')),
    event_type text NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('failure', 'recovery', 'warning')),
    safe_error_code text NOT NULL,
    http_status integer CHECK (http_status BETWEEN 100 AND 599),
    run_id uuid REFERENCES public.traffic_collection_runs(id),
    request_id uuid,
    occurrence_count integer NOT NULL DEFAULT 1 CHECK (occurrence_count > 0)
);
CREATE INDEX IF NOT EXISTS traffic_operational_events_time
    ON public.traffic_operational_events(event_time DESC);

-- All new tables are private by default for Data API roles; server-side
-- privileged connection policy must be verified separately before activation.
ALTER TABLE public.traffic_collection_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.traffic_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.traffic_article_publication ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.traffic_article_publication_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.traffic_operational_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.traffic_collection_runs, public.traffic_observations,
    public.traffic_article_publication, public.traffic_article_publication_events,
    public.traffic_operational_events FROM anon, authenticated;

COMMIT;
