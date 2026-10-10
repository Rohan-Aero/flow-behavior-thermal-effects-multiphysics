-- 13 Linear eigenvalue buckling factors below 1.0 (stability criterion exceeded at the applied load level).
-- Different from yield onset (query 11). lambda1 < 1 means the linear stability criterion indicates loss of stability
-- before the applied LC2 load; it is not a collapse prediction and not a factor of safety.
SELECT v.case_code, v.solver, v.support_condition, v.value AS lambda1, ROUND(1 - v.value, 5) AS shortfall_from_1,
       p.value AS pcr_kn, c.detail AS source_note
FROM v_results v
LEFT JOIN v_results p ON p.run_code = v.run_code AND p.metric_id = 'buck.eig_pcr'
LEFT JOIN validation_checks c ON c.run_id = (SELECT run_id FROM solver_runs WHERE run_code = v.run_code)
                             AND c.check_name = 'linear_stability_lambda1_below_1'
WHERE v.metric_id = 'buck.eig_lambda1' AND v.value < 1.0
ORDER BY v.value;
