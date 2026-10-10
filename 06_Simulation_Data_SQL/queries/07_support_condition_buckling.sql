-- 07 Support-condition comparison for the baseline (P00): linear eigenvalue buckling factor and load for S1/S2/S3,
-- set against the first-yield factor. lambda1 is a LINEAR EIGENVALUE (ideal tube, no imperfection, no plasticity),
-- not a collapse load and not a factor of safety. P_cr / reaction must reproduce lambda1 (consistency column).
WITH s AS (
    SELECT support_condition AS support,
           MAX(CASE WHEN metric_id = 'buck.eig_lambda1'           THEN value END) AS lambda1,
           MAX(CASE WHEN metric_id = 'buck.eig_pcr'               THEN value END) AS pcr_kn,
           MAX(CASE WHEN metric_id = 'struct.lc2.end_reaction_axial' THEN value END) AS reaction_n,
           MAX(CASE WHEN metric_id = 'struct.first_yield_factor'  THEN value END) AS first_yield_factor,
           MAX(CASE WHEN metric_id = 'struct.lc2.max_von_mises'   THEN value END) AS static_max_vm_mpa
    FROM v_results
    WHERE case_code = 'P00' AND solver = 'ANSYS Mechanical' AND support_condition IS NOT NULL
    GROUP BY support_condition)
SELECT s.support, s.lambda1, s.pcr_kn, s.reaction_n,
       ROUND(s.pcr_kn * 1000.0 / s.reaction_n, 4) AS pcr_over_reaction,
       s.first_yield_factor, s.static_max_vm_mpa,
       CASE WHEN s.lambda1 < s.first_yield_factor THEN 'eigenvalue buckling first' ELSE 'first yield first' END
           AS lower_of_the_two_idealised,
       v.source_status AS source_classification
FROM s
LEFT JOIN validation_checks v ON v.run_id = (SELECT run_id FROM solver_runs WHERE run_code = 'P00:mech:buckling:' || s.support)
                             AND v.check_name = 'governing_mechanism_idealised'
ORDER BY s.lambda1;
