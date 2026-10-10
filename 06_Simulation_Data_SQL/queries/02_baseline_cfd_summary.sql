-- 02 Baseline CFD results (P00, medium mesh = the project reference), with run context and provenance.
SELECT v.quantity_family, v.metric_id, v.value, v.units,
       r.n_cells, r.iterations, r.converged, r.run_status,
       v.source_file, v.source_field
FROM v_results v
JOIN solver_runs r USING (run_code)
WHERE v.case_code = 'P00' AND v.mesh_level = 'medium'
ORDER BY v.quantity_family, v.metric_id;
