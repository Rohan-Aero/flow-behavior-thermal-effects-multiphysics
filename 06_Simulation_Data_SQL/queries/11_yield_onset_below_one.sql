-- 11 Recorded yield-onset load factors below 1.0 (family 'yield_onset', dimensionless factors only).
-- The two metrics are NOT interchangeable: struct.first_yield_factor scales the linear LC2 state; the LS-DYNA
-- indicator is the first lambda at which nodal VM/S_y(T) = 1 on the nonlinear (bending-including) elastic path.
-- Everything past such a point in the elastic-only LS-DYNA model is not physical behaviour.
SELECT v.case_code, v.solver, v.metric_id, v.value AS load_factor, m.description,
       (SELECT n.value FROM v_results n WHERE n.run_code = v.run_code AND n.metric_id = 'lsdyna.yield_indicator_n') AS n_at_indicator_kn,
       m.caveat
FROM v_results v
JOIN metrics m USING (metric_id)
WHERE v.quantity_family = 'yield_onset' AND v.units = '-' AND v.value_status = 'reported' AND v.value < 1.0
ORDER BY v.value;
