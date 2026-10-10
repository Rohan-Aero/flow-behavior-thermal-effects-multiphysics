-- 06 LC1 (free expansion) versus LC2 (axially restrained) for every case with both solved (LC2 = support S1).
SELECT case_code, MAX(case_group) AS case_group,
       MAX(CASE WHEN metric_id = 'struct.lc1.max_von_mises' THEN value END)           AS lc1_max_vm_mpa,
       MAX(CASE WHEN metric_id = 'struct.lc2.max_von_mises' THEN value END)           AS lc2_max_vm_mpa,
       ROUND(MAX(CASE WHEN metric_id = 'struct.lc2.max_von_mises' THEN value END) /
             MAX(CASE WHEN metric_id = 'struct.lc1.max_von_mises' THEN value END), 2) AS lc2_over_lc1,
       MAX(CASE WHEN metric_id = 'struct.lc1.max_total_deformation' THEN value END)   AS lc1_max_deformation_mm,
       MAX(CASE WHEN metric_id = 'struct.lc2.mean_axial_stress' THEN value END)       AS lc2_mean_axial_mpa,
       MAX(CASE WHEN metric_id = 'struct.lc2.yield_utilisation' THEN value END)       AS lc2_yield_utilisation
FROM v_results
WHERE solver = 'ANSYS Mechanical' AND analysis_type = 'static_structural_thermal'
  AND (support_condition IS NULL OR support_condition = 'S1')
GROUP BY case_code
HAVING lc1_max_vm_mpa IS NOT NULL AND lc2_max_vm_mpa IS NOT NULL
ORDER BY lc2_max_vm_mpa DESC;
