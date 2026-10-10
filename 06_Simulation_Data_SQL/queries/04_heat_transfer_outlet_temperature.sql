-- 04 Heat-transfer rate and outlet temperature across the CFD design cases. Bulk temperature rise = T_out - T_in
-- (T_in from case_parameters). Thickness cases hold the total heat input constant, so q'' differs there.
WITH par AS (
    SELECT c.case_id, c.case_code,
           MAX(CASE WHEN cp.parameter = 'outer_wall_heat_flux' THEN cp.value END) AS heat_flux_w_m2,
           MAX(CASE WHEN cp.parameter = 'inlet_temperature'    THEN cp.value END) AS t_in_k
    FROM simulation_cases c JOIN case_parameters cp USING (case_id) GROUP BY c.case_id),
m AS (
    SELECT case_code,
           MAX(CASE WHEN metric_id = 'cfd.q_heated_wall'     THEN value END) AS q_w,
           MAX(CASE WHEN metric_id = 'cfd.t_out_bulk'        THEN value END) AS t_out_k,
           MAX(CASE WHEN metric_id = 'cfd.t_solid_max_facet' THEN value END) AS t_solid_max_k
    FROM v_results
    WHERE solver = 'ANSYS Fluent' AND (mesh_level IS NULL OR mesh_level = 'medium')
    GROUP BY case_code),
d AS (SELECT m.*, par.heat_flux_w_m2, m.t_out_k - par.t_in_k AS bulk_rise_k
      FROM m JOIN par USING (case_code))
SELECT d.case_code, d.heat_flux_w_m2, d.q_w,
       ROUND(100.0 * (d.q_w - b.q_w) / b.q_w, 3)                 AS pct_q_vs_p00,
       d.t_out_k, ROUND(d.bulk_rise_k, 3)                          AS bulk_rise_k,
       ROUND(100.0 * (d.bulk_rise_k - b.bulk_rise_k) / b.bulk_rise_k, 2) AS pct_rise_vs_p00,
       d.t_solid_max_k, ROUND(d.t_solid_max_k - b.t_solid_max_k, 3) AS dk_solid_max_vs_p00
FROM d JOIN d AS b ON b.case_code = 'P00'
ORDER BY d.t_solid_max_k DESC;
