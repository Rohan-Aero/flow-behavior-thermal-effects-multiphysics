-- 01 CFD mesh comparison: P00 on the coarse (51,840), medium (159,840) and fine (500,580) cell meshes.
-- Pivots one row per metric, adds the percentage change between meshes and the source's own mesh-independence
-- status (A clearly convergent ... D geometry/faceting affected, E inconclusive). Status is NULL where the source
-- table has no entry for that quantity. Raw changes are NOT discretisation-only: for several quantities most of
-- the coarse->medium change is polygon-geometry (see the status basis in validation_checks).
WITH mesh AS (
    SELECT metric_id, quantity_family, units,
           MAX(CASE mesh_level WHEN 'coarse' THEN value END) AS coarse,
           MAX(CASE mesh_level WHEN 'medium' THEN value END) AS medium,
           MAX(CASE mesh_level WHEN 'fine'   THEN value END) AS fine,
           MAX(CASE mesh_level WHEN 'medium' THEN
               'mesh_independence:' || substr(source_field, 6, instr(source_field, ''', column') - 6) END) AS status_key
    FROM v_results
    WHERE case_code = 'P00' AND mesh_level IS NOT NULL
    GROUP BY metric_id, quantity_family, units)
SELECT m.metric_id, m.units, m.coarse, m.medium, m.fine,
       ROUND(100.0 * (m.medium - m.coarse) / m.coarse, 3) AS pct_coarse_to_medium,
       ROUND(100.0 * (m.fine - m.medium) / m.medium, 3)   AS pct_medium_to_fine,
       v.source_status AS source_mesh_status
FROM mesh m
LEFT JOIN validation_checks v ON v.check_name = m.status_key AND v.check_origin = 'source_recorded'
ORDER BY m.quantity_family, m.metric_id;
