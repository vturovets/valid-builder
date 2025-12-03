# Solution Design Document – Validation Rules Extraction Tool (CLI, Python)

---

## 1. Purpose and Scope

**Purpose.**  
Design a Python-based CLI application that reads a single input file (Kotlin source code or OpenAPI 3.0.x YAML), extracts validation rules, and produces a human-friendly CSV catalogue of those rules for business analysts (BA).

**Scope (v1).**

- Single input file per run.

- Supported inputs:
  
  - Kotlin source (`.kt`).
  
  - OpenAPI 3.0.x YAML (`.yml`, `.yaml`).

- Extraction method: **rule-based (regex / structural analysis)** only. LLM and hybrid modes are configured but not used in v1.

- Output: one RFC4180-compliant CSV file (UTF-8) with columns:
  
  `Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on`

---

## 2. High-Level Requirements Mapping

### 2.1 Functional

- Parse input file, detect validation rules, and write CSV with required columns.

- Identify rule artifacts:
  
  - **Kotlin**: `if` + `throw`, `require`, `check`, annotations (`@NotNull`), regex usages.
  
  - **OpenAPI**: `required`, `enum`, `type`, `minLength`, `maxLength`, `minimum`, `pattern`, `format`, `oneOf`, `allOf`, regex.

- Generate human-friendly descriptions.

- Track:
  
  - Source file path and line ranges.
  
  - Endpoint & endpoint entity (for OpenAPI).
  
  - Dependencies between rules (including cyclic; cyclics indicated with warnings).

- CLI usage pattern:  
  `<app> <source file> --output <filename.csv>` (output optional; default `output.csv` in CWD).

### 2.2 Non-functional

- **Reliability**: No partial CSV files on ERROR.

- **Logging**: INFO/WARNING/ERROR with timestamps, to stdout/stderr (optional log file).

- **Testability**: sample Kotlin and OpenAPI files must be covered with automated tests that reproduce the sample CSVs exactly.

- **Extensibility**: modular architecture to accommodate additional languages, methods (LLM, hybrid), and UI/web front-ends later.

---

## 3. Architecture Overview

### 3.1 Logical Components

1. **CLI Layer**
   
   - Parses command-line arguments.
   
   - Resolves configuration (.env + CLI flags).
   
   - Selects appropriate parser (Kotlin vs OpenAPI).

2. **Configuration Manager**
   
   - Loads `.env` (defaults for everything, no mandatory config errors).
   
   - Provides:
     
     - Rule ID format (e.g. `RULE-001`).
     
     - Endpoint / endpoint entity titles for YAML (e.g. `parameters`, `requestBody`, `responses`).
     
     - LLM parameters (present but unused in v1).
     
     - Optional log file path.

3. **Input Type Dispatcher**
   
   - Determines if file is Kotlin or OpenAPI based on:
     
     - Explicit CLI flag (if provided), or
     
     - File extension + simple heuristic (e.g. presence of `openapi:` or `paths:` in YAML).

4. **Parsing & Extraction Layer**
   
   - **Kotlin Analyzer** – line-based plus regex/structural heuristics.
   
   - **OpenAPI Analyzer** – YAML/AST walker preserving line numbers.
   
   - Both produce a common **Intermediate Rule Model** (IR).

5. **Dependency Resolver**
   
   - Builds rule dependency graph (`Depends on`).
   
   - Detects cycles and logs WARNING if found (no failure).

6. **Rule ID & Ordering Manager**
   
   - Assigns unique rule IDs using configured pattern.
   
   - Orders rules by source file and line range before writing.

7. **Description Generator**
   
   - Converts technical expressions into human-friendly rule descriptions, using templates and basic phrase assembly.

8. **CSV Writer**
   
   - Emits RFC4180-compliant CSV:
     
     - Comma separator.
     
     - Double-quote as quote char.
     
     - Quote only fields that contain comma, quote, or newline.
     
     - Escape `"` as `""`.

9. **Logging & Error Handling**
   
   - Standardized logging utilities.
   
   - Exit codes:
     
     - `0` – success (possibly with warnings).
     
     - Non-zero – fatal errors, no CSV created/left behind.

10. **Testing Harness**
    
    - Golden-file tests for sample inputs vs expected CSV outputs.

### 3.2 High-Level Flow

1. **Startup**
   
   - CLI parses arguments.
   
   - Config Manager loads `.env`.
   
   - Logger initialized.

2. **Input Dispatch**
   
   - Determine file type.
   
   - Log input file path and detected type (INFO).

3. **Extraction**
   
   - For Kotlin: Kotlin Analyzer → IR rules.
   
   - For OpenAPI: OpenAPI Analyzer → IR rules.
   
   - Log number of rules detected and skipped (INFO/WARNING).

4. **Post-processing**
   
   - Dependency Resolver updates IR with `depends_on` references.
   
   - Rule ID Manager assigns IDs.
   
   - Description Generator finalizes descriptions.

5. **Output**
   
   - CSV Writer writes to temp file and atomically renames to final path.
   
   - Log success / warnings summary.

---

## 4. Technology Choices

- **Language:** Python 3.11+ (no OS-specific dependencies).

- **CLI:** `argparse` (standard) or `click` (if we want nicer UX).

- **Config:** `python-dotenv` for `.env` handling.

- **YAML:** `ruamel.yaml` to preserve line numbers and comments reliably.

- **Kotlin parsing:**
  
  - v1: **line-based + regex + structural heuristics**, not a full AST.
  
  - Optional enhancement: integrate `tree-sitter` for Kotlin later.

- **CSV:** Python’s built-in `csv` module with custom dialect.

- **Logging:** Python `logging` module, with configuration for:
  
  - Simple, timestamped console output.
  
  - Optional log file via config.

---

## 5. Configuration Design

All configuration lives in `.env`, with sane defaults so that **no configuration error stops the run**.

### 5.1 Core Parameters (suggested)

- `DEFAULT_RULE_ID="RULE-001"`
  
  - Parsed into:
    
    - PREFIX: `RULE`
    
    - START: `1`
    
    - WIDTH: `3` (inferred from `001`).

- `OPENAPI_ENDPOINT_ENTITIES="parameters,requestBody,responses"`
  
  - Comma-separated list of entity names to treat as endpoint entities for OpenAPI.

- `LLM_METHOD="rule-based"` (v1 fixed)

- `LLM_MODEL=""`, `LLM_URL=""`, `LLM_API_KEY=""` (ignored in v1, but reserved).

- `LOG_FILE=""` – when non-empty, logs are duplicated to file.

- `LOG_LEVEL="INFO"` – can be overridden.

### 5.2 CLI Overrides

- `--output` – override output CSV filename (default `output.csv`).

- `--lang {kotlin,openapi}` – optional; bypass auto-detection.

- `--config` – optional path to `.env`; otherwise default to `.env` in CWD.

Precedence: **CLI > .env > built-in defaults**.

---

## 6. Data Model

### 6.1 Intermediate Rule Model (`Rule`)

```text
Rule
- internal_id: UUID or incremental internal int
- rule_id: str | None          # e.g. "RULE-001" (assigned later)
- description: str             # human-friendly description
- source_file: str             # input file path / name
- start_line: int              # inclusive
- end_line: int                # inclusive
- endpoint: str | None         # "/v3/... [POST]" for OpenAPI; None for Kotlin
- endpoint_entity: str | None  # e.g. "PackageSearchRequestParams.from[]"
- depends_on_internal: set[int]# internal ids of dependencies (pre-ID)
- depends_on_ids: set[str]     # final rule_id references (for CSV)
- source_type: enum("KOTLIN","OPENAPI")
- meta: dict                   # e.g. { "raw_expr": "...", "pattern": "require" }
```

### 6.2 In-memory Collections

- `rules: List[Rule]` – gathered from analyzers.

- `rule_by_internal_id: Dict[int, Rule]`

- `graph: Dict[int, Set[int]]` – dependency edges (`parent → child`).

---

## 7. Kotlin Analyzer Design

### 7.1 Parsing Strategy (v1, Regex-Based)

Given v1 is explicitly rule-based, we avoid a full compiler front-end and use:

1. **Preprocessing**
   
   - Read file into `List[str] lines`.
   
   - Keep track of line numbers (1-based).
   
   - Optionally strip comments or mark them for context but not logic.

2. **Construct Identification**
   
   Find candidate validation constructs:
   
   - **Guarded Validations**  
     Patterns:
     
     - `if (<condition>) { <validation-call> ... }`
     
     - Multi-line `if`-conditions.
     
     - `when` expressions followed by throws/validation.
   
   - **Direct Validations**
     
     - `require(<condition>)`
     
     - `check(<condition>)`
     
     - `throw <ValidationException>(...)`
     
     - `throwValidationException(...)`
     
     - `@NotNull`, `@Size`, or other annotations (where we know their semantics).

  Implemented via regex groups and simple stack-based brace tracking to determine block extent.

3. **Rule Extraction Heuristics**
   
   - **Rule boundaries**:
     
     - For `if` blocks: rule spans from start of `if` line to end of its block.
     
     - For validation functions: rule spans the function definition body lines.
   
   - **Combining constructs**:
     
     - For patterns like the sample (`validateChannelRequest` + `shouldValidateChannelMapping`), treat them as:
       
       - Rule A: condition under which validation is applied (combining call site and condition).
       
       - Rule B: actual validation logic that throws exception / rejects input.
   
   - **Dependency detection**:
     
     - If function `validateX` is only called inside guard `if (shouldValidateX(...))`, create:
       
       - Rule for `shouldValidateX` (when validation applies).
       
       - Rule for `validateX` (what happens in validation).
       
       - Add dependency: Rule(validateX) depends on Rule(shouldValidateX).
     
     - Implementation detail:
       
       - First pass: record all function definitions with line ranges.
       
       - Second pass: for each function call within others, record edges (caller → callee).
       
       - Third pass: for structural patterns that imply “only called under condition”, map to dependencies.

4. **Description Generation (Kotlin)**
   
   Use a template-based approach:
   
   - For `if (<condition>) then throw <Exception>("message")`:
     
     - Derive condition “subject MUST satisfy X; otherwise Y error is thrown.”
     
     - If message string present, incorporate message into description.
   
   - For `require(<condition>)`:
     
     - “ MUST satisfy `<condition>`; otherwise the call fails.”
   
   - For exception message patterns that clearly describe violation:
     
     - Use them verbatim (with minimal cleaning) in the “otherwise … error” part, as in the SRS example.

  For v1 we keep descriptions simple and conservative; BA can refine wording manually.

---

## 8. OpenAPI Analyzer Design

### 8.1 YAML Parsing and Line Numbers

- Use `ruamel.yaml` to load the OpenAPI spec and access line numbers for mappings and keys.

- Keep mapping: `node_id` → `(start_line, end_line)` (approx. `start_line` is where the key appears; `end_line` from last child node).

### 8.2 Endpoint and Schema Traversal

1. **Endpoints (`paths`)**
   
   - Iterate `paths.<path>.<method>` nodes.
   
   - For each method:
     
     - Build endpoint string: `"<path> [<METHOD>]"` (e.g. `"/v3/package/search/results [POST]"`).
     
     - Inspect `requestBody`:
       
       - If `required: true`, create a rule for “request body is required” referencing the associated schema ref.

2. **Schema Graph**
   
   - Walk `components.schemas`:
     
     - For each schema object:
       
       - Collect:
         
         - `required` array entries.
         
         - Properties and their constraints (`type`, `enum`, `minLength`, etc.).
       
       - Build a graph of schemas and their nested refs (`$ref`, `allOf`, `oneOf`).

3. **Rule Extraction**
   
   For each relevant construct:
   
   - **Required object fields**:
     
     - `required: [ from ]` under an object schema:
       
       - Rule: `<Schema> MUST contain <field>; description uses type info if available.`
   
   - **Array element constraints**:
     
     - For `type: array` with `items` referencing another schema:
       
       - Rule: property MUST be an array of `<ReferencedSchema>`.
   
   - **Enum constraints**:
     
     - `enum: ["AIRPORT"]`:
       
       - Rule: field MUST be one of the allowed values, with enumeration.
   
   - **Response schemas**:
     
     - Similar handling for response bodies; associate with endpoint if they are used as response schema.
   
   - Each rule is associated with:
     
     - `endpoint`: if schema is in the request/response path of a specific endpoint.
     
     - `endpoint_entity`: dotted path, e.g. `PackageSearchRequestParams.from[]`, `Holidays.offers[].Offer.productID`.

4. **Dependencies**
   
   - Build hierarchical dependencies:
     
     - Request body required → `PackageSearchRequestParams` rules → `From` rules → etc.
     
     - Response object required → nested `Holidays.offers[].Offer` rules.
   
   - Implementation:
     
     - For each schema, we track its parent context:
       
       - If schema A is used in endpoint requestBody, rules of A depend on rule “request body required”.
       
       - If schema B is a required property of A, B’s rules depend on rule “A. required”.

  This yields the dependency relationships described in the OpenAPI worked example.

5. **Description Generation (OpenAPI)**
   
   Template-based:
   
   - Required body:  
     *“For the `<METHOD>` `<path>` endpoint, a `<mediaType>` request body conforming to `<Schema>` MUST be provided; requests without a body are invalid.”*
   
   - Required property:  
     *“The `<Schema>` object MUST contain a `<property>` property of type `<type>`. …”*
   
   - Enum:  
     *“The `<property>` field MUST be one of `<values>`; any other value is invalid.”*
   
   - Nested objects/arrays:  
     *“Each `<item>` in `<array>` MUST include `<field>` …”*

---

## 9. Dependency Resolver & Cycle Detection

### 9.1 Mapping Internal Dependencies to Rule IDs

1. After analyzers create `Rule` objects:
   
   - Build adjacency list `graph[internal_id] = set(child_internal_ids)`.

2. Assign rule IDs in a deterministic order:
   
   - Sort rules by `(source_type, source_file, start_line)`.
   
   - Starting from configured base `DEFAULT_RULE_ID`:
     
     - For each rule, assign next ID (e.g. `RULE-001`, `RULE-002`, …).

3. For each rule:
   
   - Convert `depends_on_internal` to `depends_on_ids` using the ID mapping.

### 9.2 Cycle Detection

- Run DFS or Kahn’s algorithm on `graph`.

- If cycle detected:
  
  - Log WARNING with involved rule IDs (once per cycle group).
  
  - Do not fail the run (AC5).

Optionally, we can also mark cyclical dependencies in logs or annotate descriptions (but not strictly required).

---

## 10. CSV Writer Design

Use Python’s `csv` module with a custom dialect:

- `delimiter = ","`

- `quotechar = '"'

- `quoting = csv.QUOTE_MINIMAL`

- `lineterminator = "\n"`

Rules:

- Only quote fields containing `,`, `"`, or newline.

- Double any internal `"` as `""` (handled by `csv` module).

- Always write header:
  
  ```text
  Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on
  ```

- `Lines` column: `"start-end"` string, e.g. `94-105`.

- `Depends on`: join multiple rule IDs by semicolon or comma (design choice; sample uses a single ID, so we’ll use comma-separated if multiple).

**Atomic write:**

- Write to `output.tmp` in target directory.

- On success, rename to final name (`output.csv` or user-specified).

- On error, delete `output.tmp`.

This satisfies the requirement that no partial CSV is left behind on ERROR.

---

## 11. Logging & Error Handling

### 11.1 Severity Levels

- **INFO** – normal progress:
  
  - “Reading source file …”
  
  - “Detected X validation rules. Skipped Y candidates.”
  
  - “Writing output file … / Completed successfully.”

- **WARNING** – non-fatal:
  
  - Skipped constructs.
  
  - Unexpected keywords.
  
  - Unable to infer endpoint entity precisely.
  
  - Cyclical dependency detected.

- **ERROR** – fatal:
  
  - Input file missing/ unreadable.
  
  - Unsupported or invalid format (e.g. broken YAML).
  
  - Internal errors in parsing/extraction.

Messages go to:

- `stdout`: INFO & final summary.

- `stderr`: WARNING and ERROR (or prefix `[WARNING]`, `[ERROR]` if single stream).

### 11.2 Failure & Partial Output Rules

- If ERROR before any rules extracted:
  
  - Exit non-zero.
  
  - Do not create CSV.

- If ERROR after some rules extracted but before CSV fully written:
  
  - Exit non-zero.
  
  - Delete partial temp file; CSV does not appear.

- If only WARNINGS:
  
  - Exit code 0.
  
  - Final message like:  
    `"Completed successfully. Extracted X rules. Y warnings."`

---

## 12. CLI Design

### 12.1 Usage

```bash
valid-builder <input_file> [--output OUTPUT.csv] [--lang {kotlin,openapi}] [--config path/to/.env]
```

Examples:

- Kotlin:
  
  ```bash
  valid-builder RequestValidator_sample.kt --output validation_rules.csv
  ```

- OpenAPI:
  
  ```bash
  valid-builder "openapi-spec - sample.yml" --output validation_rules.csv
  ```

### 12.2 Exit Codes

- `0` – success (possibly with warnings).

- `1` – general error (parse failure, internal exception).

- `2` – unsupported file type / format.

---

## 13. Testing Strategy

### 13.1 Unit and Integration Tests

- **Kotlin example test**
  
  - Input: `RequestValidator_sample.kt`.
  
  - Expected CSV: exactly as in Appendix A.1.3.
  
  - Test:
    
    - Run tool.
    
    - Compare output CSV content byte-for-byte against expected.

- **OpenAPI example test**
  
  - Input: `openapi-spec - sample.yml`.
  
  - Expected CSV: as in Appendix A.2.3.

- **Error-path tests**
  
  - Missing file.
  
  - Corrupted YAML.
  
  - Unsupported extension.
  
  - Logging content checks (e.g. presence of WARNING when skipping constructs).

### 13.2 Regression / Golden-file Tests

- Every time extraction logic changes, re-run tests against golden CSV outputs to ensure no unintentional drift in rule descriptions or IDs.

---

## 14. Extensibility & Future Enhancements

Although v1 uses only rule-based extraction, the architecture supports:

- **LLM-based extraction module**
  
  - Plug into the same Intermediate Rule Model.
  
  - Use on top of or instead of rule-based detection.
  
  - Could generate richer descriptions or detect nuanced rules.

- **Hybrid mode**
  
  - Run rule-based first; send ambiguous constructs to LLM to refine or confirm rules.

- **More languages / formats**
  
  - Java, JSON Schema, GraphQL, etc., each with its own analyzer implementing the “Rule Extractor” interface.

- **Service / Web UI**
  
  - Wrap CLI core in a REST API or a small web UI to upload files and download CSV.

---

## 15. Assumptions & Open Questions

I’ve filled a few gaps by making best-guess design choices; here are key assumptions and questions for you:

### 15.1 Assumptions

1. **Rule ordering**
   
   - Rules will be ordered by `(source_type, source_file, start_line)` in the CSV, not strictly by discovery order.

2. **Multiple dependencies**
   
   - `Depends on` will hold a comma-separated list of rule IDs if there are multiple dependencies.

3. **Endpoint entity paths**
   
   - Dotted path strings (e.g. `Holidays.offers[].Offer.productID`) are sufficient and do not need a stricter format.

4. **Kotlin coverage**
   
   - v1 will not fully understand all Kotlin language constructs; it will focus on the patterns listed in the SRS, skipping ambiguous cases with WARNINGS.

### 15.2 Clarification Questions

1. **Exact `Depends on` format when multiple parents exist**  
   Is a comma-separated list of rule IDs acceptable, or do you prefer another delimiter or separate rows? - A comma-separated list of rule ID is acceptable.

2. **Cyclic dependency indication**  
   Is logging a WARNING sufficient, or do you want an explicit marker in the CSV (e.g. prefix `CYCLE:` in `Depends on` for rules that are part of a cycle)? - Logging a WARNING is sufficient.

3. **Additional Kotlin rule sources**  
   Besides `require`, `check`, annotations, `if + throw`, and regex usage, are there any domain-specific exception names or helper methods (e.g. `failIfInvalid(...)`) we should treat as validation indicators in v1? - For v1 we assume that everything within a provided Kotlin input file has to do with validation.


