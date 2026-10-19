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
-- Geometry is clipped to the PIA boundary for display; all parcels lie
-- inside the boundary, so clipping hides no data (checked 2026-10-19).
CREATE VIEW published.exide_hex_summary AS
WITH boundary AS (
    SELECT ST_Union(geometry) AS geom FROM staging.dtsc_pia_boundary
)
SELECT
    row_number() OVER (ORDER BY h.i, h.j)::int AS hex_id,
    h.i,
    h.j,
    CASE WHEN h.n_sampled >= 10 THEN 'reported'
         ELSE 'insufficient_samples' END AS data_status,
    h.n_parcels,
    round(h.n_no_access::numeric / h.n_parcels, 2) AS share_no_access,
    round(h.n_cleaned::numeric / h.n_parcels, 2)   AS share_cleaned,
    CASE WHEN h.n_sampled >= 10 THEN h.n_sampled END AS n_sampled,
    CASE WHEN h.n_sampled >= 10
         THEN round(h.median_lead_ppm::numeric) END AS median_lead_ppm,
    CASE WHEN h.n_sampled >= 10
         THEN round(h.share_over_80::numeric, 2) END AS share_over_80,
    CASE WHEN h.n_sampled >= 10
         THEN round(h.share_over_400::numeric, 2) END AS share_over_400,
    ST_Multi(ST_CollectionExtract(ST_Intersection(h.geom, b.geom), 3)) AS geom
FROM analytics.exide_hex h
CROSS JOIN boundary b
WHERE h.n_parcels >= 10;

-- The boundary and facility are public information.
DROP VIEW IF EXISTS published.pia_boundary;
CREATE VIEW published.pia_boundary AS
SELECT row_number() OVER ()::int AS id, geometry AS geom
FROM staging.dtsc_pia_boundary;

DROP VIEW IF EXISTS published.exide_facility;
CREATE VIEW published.exide_facility AS
SELECT row_number() OVER ()::int AS id, geometry AS geom
FROM staging.dtsc_facility;