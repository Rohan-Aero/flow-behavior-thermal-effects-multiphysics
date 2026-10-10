-- 10 Southwell characteristic-load estimate versus the maximum load actually reached in each LS-DYNA run.
-- These are different metrics: the Southwell value is an extrapolated estimate; the maximum reached is a run
-- result. It is an instability point only where N later decreases (interior maximum); otherwise the run
-- stopped at lambda = 1.3 with N still rising. Both are elastic-model outputs (see n_max_validity).
SELECT s.case_code, s.amplitude_mm,
       s.southwell_ncr_kn  AS southwell_estimate_kn,
       s.southwell_status,
       s.n_max_kn          AS max_load_reached_kn,
       s.lambda_at_n_max,
       CASE s.n_max_is_interior WHEN 1 THEN 'interior maximum (N later decreases)'
            ELSE 'end of analysis, N still rising: not an instability point' END AS nature_of_max_load,
       ROUND(100.0 * s.n_max_kn / s.southwell_ncr_kn, 2) AS reached_pct_of_southwell,
       ROUND(100.0 * s.n_max_kn / (SELECT value FROM v_results WHERE case_code = 'P00' AND solver = 'ANSYS Mechanical'
                                    AND support_condition = 'S1' AND metric_id = 'buck.eig_pcr'), 2) AS reached_pct_of_mech_eigen,
       s.n_max_validity
FROM v_lsdyna_case_summary s
WHERE s.case_status <> 'not_run'
ORDER BY s.amplitude_mm;
