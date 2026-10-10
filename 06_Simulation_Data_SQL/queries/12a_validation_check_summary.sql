-- 12a Summary of the validation records stored with the data, by origin, status and check family.
-- FAIL and DISCREPANCY sort first. 'source_recorded' = a status the project itself recorded; 'import_crosscheck' =
-- agreement test between two repository files made during import; 'data_gap' = missing data (see 12b).
SELECT check_origin, status,
       CASE WHEN instr(check_name, ':') > 0 THEN substr(check_name, 1, instr(check_name, ':') - 1) ELSE check_name END
           AS check_family,
       COUNT(*) AS n_checks, COUNT(DISTINCT case_id) AS n_cases
FROM validation_checks
GROUP BY check_origin, status, check_family
ORDER BY CASE status WHEN 'FAIL' THEN 0 WHEN 'DISCREPANCY' THEN 1 WHEN 'NOT_AVAILABLE' THEN 2 WHEN 'INFO' THEN 3 ELSE 4 END,
         check_origin, check_family;
