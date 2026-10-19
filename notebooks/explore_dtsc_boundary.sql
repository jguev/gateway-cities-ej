-- Exploration: do DTSC parcels fall outside the PIA boundary?
-- Output is aggregate counts only (safe to share).
-- Run: psql -d gateway_cities -f notebooks/explore_dtsc_boundary.sql

WITH boundary AS (
    SELECT ST_Union(geometry) AS geom FROM staging.dtsc_pia_boundary
),
parcels AS (
    SELECT status, ST_PointOnSurface(geometry) AS pt
    FROM staging.dtsc_parcels
)
SELECT
    ST_Within(p.pt, b.geom)                 AS inside_pia,
    p.status,
    count(*)                                AS n_parcels,
    round(max(ST_Distance(p.pt, b.geom)))   AS max_meters_outside
FROM parcels p, boundary b
GROUP BY 1, 2
ORDER BY 1, 2;