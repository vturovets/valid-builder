# Implementation Plan

**Project:** Validation Rules Extraction Tool

### Understanding of SRS/SDD

- **Goal:** Build a Python CLI tool that reads a single Kotlin or OpenAPI 3.0.x YAML file, extracts validation rules via rule-based heuristics, and outputs an RFC4180 CSV catalog with rule IDs, descriptions, source file/lines, endpoint info (for OpenAPI), and dependencies; errors abort output, warnings allow completion.

- **Main components:** CLI layer, configuration manager (.env + CLI overrides), input type dispatcher, Kotlin analyzer, OpenAPI analyzer, intermediate Rule model, dependency resolver (with cycle warning), rule ID manager, description generator, CSV writer (atomic, RFC4180), logging utilities, and test harness with golden files.

- **High-level TDD flow:**
  
  1. CLI/config dispatch basics and error handling.
  
  2. CSV writer correctness (quoting/escaping).
  
  3. Rule ID and dependency resolution.
  
  4. Kotlin analyzer extraction (sample file to expected CSV).
  
  5. OpenAPI analyzer extraction (sample YAML to expected CSV).
  
  6. End-to-end CLI runs (success, warnings, errors).
  
  7. Logging/exit-code behavior and cleanup on errors.

---

### Step-by-Step Executable Implementation Plan (TDD-first)

1. **Project skeleton & config loading**
   
   - Files: `src/cli.py`, `src/config.py`, `src/logging_utils.py`, `src/__init__.py`.
   
   - Tests: `tests/test_cli_args.py`, `tests/test_config.py`, `tests/test_logging_utils.py`.
   
   - Validate: parsing CLI args (`--output`, optional `--lang`, default output), .env defaults precedence, logger setup to stdout/stderr with levels.
   
   - Focus on failure when input missing/unsupported, success path just logs detection message.

2. **CSV writer (RFC4180) utilities**
   
   - File: `src/csv_writer.py`.
   
   - Tests: `tests/test_csv_writer.py`.
   
   - Cover quoting rules, newline handling, escape of quotes, atomic write (temp then rename), no partial file on failure.

3. **Rule model, ID manager, dependency resolver**
   
   - Files: `src/models.py`, `src/rule_id_manager.py`, `src/dependency_resolver.py`.
   
   - Tests: `tests/test_rule_model.py`, `tests/test_rule_ids.py`, `tests/test_dependencies.py`.
   
   - Check: deterministic ordering by source type/file/line; ID assignment starting from configured default; conversion of internal deps to IDs; cycle detection logs warning but does not fail; comma-separated `Depends on`.

4. **Description generator (templates)**
   
   - File: `src/description.py`.
   
   - Tests: `tests/test_description_kotlin.py`, `tests/test_description_openapi.py`.
   
   - Ensure simple templating for conditions/throws (Kotlin) and required/enums/arrays/request-body (OpenAPI).

5. **Kotlin analyzer (rule-based)**
   
   - File: `src/analyzers/kotlin_analyzer.py`.
   
   - Tests:
     
     - `tests/test_kotlin_sample_golden.py` (end-to-end on `docs/RequestValidator_sample.kt` comparing output CSV to SRS sample).
     
     - `tests/test_kotlin_patterns.py` (unit-level regex/heuristic coverage for if+throw, require/check, annotations).
   
   - Validate line ranges, dependency between guard and validation, description text matches golden, warnings for unrecognized constructs (non-fatal).

6. **OpenAPI analyzer (ruamel.yaml with line numbers)**
   
   - File: `src/analyzers/openapi_analyzer.py`.
   
   - Tests:
     
     - `tests/test_openapi_sample_golden.py` (end-to-end on `docs/openapi-spec - sample.yml` vs expected CSV).
     
     - `tests/test_openapi_rules.py` (unit checks for required, enum, type, nested arrays, endpoint association).
   
   - Ensure endpoint string formatting (`<path> [METHOD]`), endpoint entity dotted paths, dependency chaining (request body → object → fields).

7. **Input dispatcher & orchestrator**
   
   - File: `src/orchestrator.py`.
   
   - Tests: `tests/test_dispatcher.py`, `tests/test_orchestrator_success.py`, `tests/test_orchestrator_errors.py`.
   
   - Validate file-type detection (extension/heuristic or `--lang` override), correct analyzer invoked, end-to-end flow populating IR, resolving deps/IDs, writing CSV, logging counts; error paths remove temp outputs.

8. **CLI end-to-end scenarios**
   
   - Tests:
     
     - `tests/test_cli_kotlin_end_to_end.py` (run main CLI on sample Kotlin; compare CSV).
     
     - `tests/test_cli_openapi_end_to_end.py` (run main CLI on sample OpenAPI).
     
     - `tests/test_cli_error_cases.py` (missing file, unsupported extension, corrupted YAML) checking exit codes, no output file, error logging.
     
     - `tests/test_cli_warning_cases.py` (simulated skipped constructs) ensuring warnings but exit 0.

9. **Logging and progress summaries**
   
   - Ensure INFO/WARNING/ERROR routed properly; final summary lines with counts; optional log file duplication if configured.
   
   - Tests can live in `tests/test_logging_summary.py`.

10. **Packaging and utilities**
    
    - Add `pyproject.toml` or `setup.cfg` for dependencies (`ruamel.yaml`, `python-dotenv`).
    
    - No implementation yet; tests will drive minimal code later.

This sequencing starts with infrastructure (config/logging/CSV), then core models and resolvers, then analyzers, and finally CLI orchestration and end-to-end coverage, matching the SRS/SDD expectations.
