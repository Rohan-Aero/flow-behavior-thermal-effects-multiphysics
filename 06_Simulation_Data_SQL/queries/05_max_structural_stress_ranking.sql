-- 05 Maximum von Mises stress ranked within each load case (LC1 free expansion, LC2 axially restrained).
-- LC2 includes the three support scenarios of the baseline (S1/S2/S3) next to the parametric cases (all S1).
-- Utilisation = von Mises / S_y(T) at the critical node, recorded for LC2 in the sources.
SELECT v.load_case, RANK() OVER (PARTITION BY v.load_case ORDER BY v.value DESC) AS rank_in_load_case,
       v.case_code, v.case_group, v.support_condition, v.value AS max_von_mises_mpa, u.value AS yield_utilisation,
       v.physical_validity
FROM v_results v
LEFT JOIN v_results u ON u.run_code = v.run_code AND u.metric_id = 'struct.lc2.yield_utilisation'
WHERE v.metric_id IN ('struct.lc1.max_von_mises', 'struct.lc2.max_von_mises')
ORDER BY v.load_case, rank_in_load_case;
