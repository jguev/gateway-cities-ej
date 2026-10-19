-- 010_exide_hex.sql
-- Aggregate Exide parcels into 200 m hexagons (analytics), then publish
-- a privacy-safe summary (published). Safe to rerun.

DROP TABLE IF EXISTS analytics.exide_hex CASCADE;

CREATE TABLE analytics.exide_hex AS
WITH grid AS (
    SELECT h.i, h.j, h.geom
    FROM ST_HexagonGrid(
        200,  -- hexagon side length, meters (EPSG:3310)
        (SELECT ST_SetSRID(ST_Extent(geometry)::geometry, 3310)
         FROM staging.dtsc_parcels)
    ) AS h
),
parcel_points AS (
    SELECT status, lead_ppm, ST_PointOnSurface(geometry) AS pt
    FROM staging.dtsc_parcels
)
SELECT
    g.i,
    g.j,
    count(*)                                        AS n_parcels,
    count(p.lead_ppm)                               AS n_sampled,
    count(*) FILTER (WHERE p.status = 'no_access')  AS n_no_access,
    count(*) FILTER (WHERE p.status = 'cleaned')    AS n_cleaned,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY p.lead_ppm) AS median_lead_ppm,
    avg((p.lead_ppm >= 80)::int)                    AS share_over_80,
    avg((p.lead_ppm >= 400)::int)                   AS share_over_400,
    g.geom
FROM grid g
JOIN parcel_points p ON ST_Intersects(g.geom, p.pt)
GROUP BY g.i, g.j, g.geom;

ALTER TABLE analytics.exide_hex ADD PRIMARY KEY (i, j);
CREATE INDEX ON analytics.exide_hex USING gist (geom);

-- Published: hexagons with fewer than 10 parcels are dropped entirely;
-- lead statistics are hidden unless at least 10 parcels were sampled.
CREATE VIEW published.exide_hex_summary AS
SELECT
    row_number() OVER (ORDER BY i, j)::int AS hex_id,
    i,
    j,
    n_parcels,
    round(n_no_access::numeric / n_parcels, 2) AS share_no_access,
    round(n_cleaned::numeric / n_parcels, 2)   AS share_cleaned,
    CASE WHEN n_sampled >= 10 THEN n_sampled END AS n_sampled,
    CASE WHEN n_sampled >= 10
         THEN round(median_lead_ppm::numeric) END AS median_lead_ppm,
    CASE WHEN n_sampled >= 10
         THEN round(share_over_80::numeric, 2) END AS share_over_80,
    CASE WHEN n_sampled >= 10
         THEN round(share_over_400::numeric, 2) END AS share_over_400,
    geom
FROM analytics.exide_hex
WHERE n_parcels >= 10;

-- The boundary and facility are public information.
DROP VIEW IF EXISTS published.pia_boundary;
CREATE VIEW published.pia_boundary AS
SELECT row_number() OVER ()::int AS id, geometry AS geom
FROM staging.dtsc_pia_boundary;

DROP VIEW IF EXISTS published.exide_facility;
CREATE VIEW published.exide_facility AS
SELECT row_number() OVER ()::int AS id, geometry AS geom
FROM staging.dtsc_facility;