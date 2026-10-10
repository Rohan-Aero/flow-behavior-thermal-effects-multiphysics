-- 12b Missing-data report: results stored as not reported (with the reason) plus metrics the sources do not provide
-- for a run, and planned cases that were not run. Nothing here has been filled in or inferred.
SELECT 'result_not_reported' AS kind, case_code, run_code, metric_id AS item, value_status AS status, missing_reason AS reason
FROM v_results
WHERE value_status <> 'reported'
UNION ALL
SELECT 'data_gap', c.case_code, r.run_code, v.check_name, v.status, v.detail
FROM validation_checks v
JOIN simulation_cases c ON c.case_id = v.case_id
LEFT JOIN solver_runs r ON r.run_id = v.run_id
WHERE v.check_origin = 'data_gap'
ORDER BY kind DESC, case_code, run_code, item;
