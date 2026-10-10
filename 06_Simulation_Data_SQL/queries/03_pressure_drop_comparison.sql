-- 03 Pressure-drop comparison across all verified CFD design cases (medium-mesh family), ranked, with the
-- case parameters and the change against the baseline P00. C00 is the pipeline control (must equal P00).
WITH par AS (
    SELECT c.case_code, c.case_group,
           MAX(CASE WHEN cp.parameter = 'inlet_velocity'       THEN cp.value END) AS velocity_m_s,
           MAX(CASE WHEN cp.parameter = 'outer_wall_heat_flux' THEN cp.value END) AS heat_flux_w_m2,
           MAX(CASE WHEN cp.parameter = 'wall_thickness'       THEN cp.value END) AS thickness_mm
    FROM simulation_cases c JOIN case_parameters cp USING (case_id)
    GROUP BY c.case_id),
dp AS (SELECT case_code, value AS dp_pa FROM v_results
       WHERE metric_id = 'cfd.dp_static' AND (mesh_level IS NULL OR mesh_level = 'medium')),
re AS (SELECT case_code, value AS re_out FROM v_results
       WHERE metric_id = 'cfd.re_out' AND (mesh_level IS NULL OR mesh_level = 'medium'))
SELECT dp.case_code, par.case_group, par.velocity_m_s, par.heat_flux_w_m2, par.thickness_mm,
       dp.dp_pa,
       ROUND(100.0 * (dp.dp_pa - base.dp_pa) / base.dp_pa, 3) AS pct_vs_p00,
       RANK() OVER (ORDER BY dp.dp_pa DESC) AS rank_highest_dp,
       re.re_out
FROM dp
JOIN par USING (case_code)
JOIN re  USING (case_code)
JOIN dp AS base ON base.case_code = 'P00'
ORDER BY dp.dp_pa DESC;
