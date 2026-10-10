-- 14 Provenance: which repository files feed the database, their SHA-256 at import, and how many records each supports.
SELECT sf.repo_path, sf.file_role, substr(sf.sha256, 1, 12) AS sha256_prefix, sf.size_bytes,
       (SELECT COUNT(*) FROM simulation_results s WHERE s.source_file_id = sf.source_file_id) AS results,
       (SELECT COUNT(*) FROM case_parameters p   WHERE p.source_file_id = sf.source_file_id) AS parameters,
       (SELECT COUNT(*) FROM solver_runs r       WHERE r.source_file_id = sf.source_file_id) AS runs,
       (SELECT COUNT(*) FROM validation_checks v WHERE v.source_file_id = sf.source_file_id) AS checks
FROM source_files sf
ORDER BY results DESC, sf.repo_path;
