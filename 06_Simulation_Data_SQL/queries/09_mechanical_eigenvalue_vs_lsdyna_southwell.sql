-- 09 Mechanical linear-eigenvalue critical load versus LS-DYNA estimates for the same model.
-- Three different quantities are listed, never merged: a linear eigenvalue load (ideal structure), the LS-DYNA
-- linear eigenvalue cross-check, and Southwell characteristic-load ESTIMATES from the nonlinear imperfect runs.
WITH mech AS (SELECT value AS pcr_kn FROM v_results
              WHERE case_code = 'P00' AND solver = 'ANSYS Mechanical' AND support_condition = 'S1'
                AND metric_id = 'buck.eig_pcr'),
rows AS (
    SELECT 1 AS ord, 'Mechanical linear eigenvalue (S1)' AS quantity, NULL AS amplitude_mm, pcr_kn AS load_kn FROM mech
    UNION ALL
    SELECT 2, 'LS-DYNA linear eigenvalue (12B G6)', NULL, value FROM v_results
     WHERE solver = 'LS-DYNA' AND metric_id = 'buck.eig_pcr'
    UNION ALL
    SELECT 3, 'LS-DYNA Southwell estimate, ' || v.case_code, p.value, v.value
      FROM v_results v
      JOIN simulation_cases c ON c.case_code = v.case_code
      JOIN case_parameters p ON p.case_id = c.case_id AND p.parameter = 'imperfection_amplitude'
     WHERE v.metric_id = 'lsdyna.southwell_ncr' AND v.value_status = 'reported')
SELECT quantity, amplitude_mm, load_kn,
       ROUND(load_kn - mech.pcr_kn, 2)                       AS diff_to_mechanical_kn,
       ROUND(100.0 * (load_kn / mech.pcr_kn - 1), 2)         AS pct_diff_to_mechanical,
       ROUND(load_kn / mech.pcr_kn, 4)                       AS ratio_to_mechanical
FROM rows, mech
ORDER BY ord, amplitude_mm;
