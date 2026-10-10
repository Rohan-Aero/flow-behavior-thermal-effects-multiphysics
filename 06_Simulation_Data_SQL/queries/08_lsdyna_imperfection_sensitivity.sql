-- 08 LS-DYNA imperfection sensitivity (elastic-only model). Amplitude A is the numerical sensitivity amplitude
-- (max lateral nodal value of the imposed mode), not a tolerance. Compared with the perfect-geometry path C0.
-- physical_validity: states beyond the source's own VM/S_y(T) = 1 indicator are model outputs, not physical.
WITH ls AS (
    SELECT v.case_code,
           MAX(CASE WHEN v.metric_id = 'lsdyna.n_at_lambda1'               THEN v.value END) AS n_at_lambda1_kn,
           MAX(CASE WHEN v.metric_id = 'lsdyna.onset_lambda'               THEN v.value END) AS onset_lambda,
           MAX(CASE WHEN v.metric_id = 'lsdyna.vm_at_lambda1'              THEN v.value END) AS vm_at_lambda1_mpa,
           MAX(CASE WHEN v.metric_id = 'lsdyna.vm_at_lambda1'              THEN v.physical_validity END) AS vm_at_lambda1_validity,
           MAX(CASE WHEN v.metric_id = 'lsdyna.lateral_max_at_lambda1p3'   THEN v.value END) AS lateral_at_1p3_mm,
           MAX(CASE WHEN v.metric_id = 'lsdyna.end_sway_at_lambda1p3'      THEN v.value END) AS end_sway_at_1p3_mm,
           MAX(CASE WHEN v.metric_id = 'lsdyna.yield_indicator_lambda'     THEN v.value END) AS yield_indicator_lambda
    FROM v_results v
    WHERE v.solver = 'LS-DYNA' AND v.analysis_type = 'nonlinear_implicit_thermal_buckling'
    GROUP BY v.case_code)
SELECT ls.case_code, p.value AS amplitude_mm,
       ls.n_at_lambda1_kn,
       ROUND(100.0 * (ls.n_at_lambda1_kn - ref.n_at_lambda1_kn) / ref.n_at_lambda1_kn, 2) AS n_at_lambda1_pct_vs_c0,
       ls.onset_lambda, ls.yield_indicator_lambda,
       ls.vm_at_lambda1_mpa, ls.vm_at_lambda1_validity,
       ls.lateral_at_1p3_mm, ls.end_sway_at_1p3_mm
FROM ls
JOIN simulation_cases c ON c.case_code = ls.case_code
JOIN case_parameters p ON p.case_id = c.case_id AND p.parameter = 'imperfection_amplitude'
JOIN ls AS ref ON ref.case_code = 'C0_A0p0'
ORDER BY p.value;
