# Software Requirements Specification

**Project:** Validation Rules Extraction Tool  
**Version:** 1   
**Owner:** Business Analyst Team

---

## 1. Context and Problem Statement

A business analyst needs a tool that reads source code/schema description and produces a human-friendly list of validation rules. The rules must be presented in a table which includes:

- A unique identifier for each rule;

- Reference to the specific line(s) in the source code/schema description;

- Cross-references to other rules if there are dependencies;

The final output document must be a CSV(UTF-8) file containing the table above.

---

## 2. Business Value

### 2.1 Objectives

- **Improve transparency of implemented logic**
  
  - Make implicit validation rules in code/schema description visible to non-technical stakeholders.

- **Support impact analysis & change management**
  
  - Quickly identify where a given validation lives in code/schema description and what depends on it.

- **Reduce manual documentation effort**
  
  - Automate the generation of rule catalogs instead of manually reading code/schema description.

- **Increase quality and consistency**
  
  - Allow comparison of implemented rules vs. business requirements or design documents.

- **Facilitate audits and compliance**
  
  - Provide an auditable list of rules and their code/schema description references.

### 2.2 Key Benefits

- Time savings for business analysts and developers.

- Reduced risk of missing rules during requirement analysis or regression impact analysis.

- Easier onboarding: newcomers understand system validations via readable rules list.

- Better collaboration: a shared artifact that links business language with code/schema description reality.

---

## 3. Stakeholders, Roles and Responsibilities

### 3.1 Stakeholders

- **Business Analyst (BA)** – Primary user.

### 3.2 Roles & Responsibilities

#### Business Analyst

- Select the source code/schema description file to analyze through simple command line interface (CLI).

- Run rule extraction.

- Review and refine human-friendly rule statements (edit text, add clarifications) in the output file manually.

---

## 4. High-Level Process Description (User Flows)

### 4.1. BA – Generate Rules from Source code/schema description

**Configure the application**

All configuration parameters are kept in .env file.

Specify the format and initial rule ID as `<rule_title>-<number>` ; the default value `RULE-001`. Every new run starts numbering from this ID.

Specify the endpoint, and endpoint entities titles, i.e. `parameters`, `requestBody`, `responses`; this is applicable if YAML file is selected as an input argument. If endpoint entities are missing, the whole endpoint schema is to be analyses

Specify model, API key and URL of LLM.

Specify method to be applied:

- rule-based (e.g. regex); is used by default;

- LLM; not for v1.

- hybrid (rule-based first and LLM - next); not for v1.

**Run Extraction**

- Specify a source code file or openApi YAML file as an argument of the CLI. The whole command would look as follows: `<the app> <source code/YAML file> --output: <filename.csv>`. If `--output: <filename>.csv` is missing, then use `output.csv` and place the file into the current working folder.

- The application parses code/schema description and identifies validation rules. Under validation rules, one should consider the presence of the following (see the table below) 
  
  | Data source           | Rule artifacts                                                                                                            |
  | --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
  | Kotlin code           | `if` + `throw`, `require`, `check`, annotations (e.g. `@NotNull`), regex expressions                                      |
  | OpenAPI specification | `required`, `enum`, `type`, `minLength`, `maxLength`, `minimum`, `pattern`, `format`, `oneOf`, `allOf`, regex expressions |

- The examples are presented in Appendix A. 

- The dependency detection uses the best-effort approach.

- Progress is displayed; errors and warnings are shown.

- If the run is successful, the output CSV file is created, and the relevant notification is displayed.

**The output file**

The application creates a CSV file which contains a table of detected rules, their sources in the source code file/schema description, and dependencies, if any:

- Unique Rule ID; e.g. `RULE-001`

- Human-friendly statement; e.g. `For region 'wr' with beneAdminFeesFeatureFlag=true, (target, medium) must match the configured channel mapping.`

- Source file path, e.g. `RequestValidator_an.kt`

- Line range(s), e.g. `101 - 121`

- Endpoint (`/holidays/packages/search` if schema description is being analyzed, otherwise empty),

- Endpoint entity (`parameters`,` requestBody`,` responses` etc, if schema description is being analyzed, otherwise empty),

- Detected dependencies / cross-references.

The header of the output file looks as follows:

`Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on`

The application creates a single CSV file per run.

**CSV quoting and escaping**

- The output file MUST be a comma-separated values (CSV) file compliant with RFC4180-style conventions.

- The field separator MUST be a comma (`,`).

- The quote character MUST be the double quote (`"`).

- Fields MUST be enclosed in double quotes **if and only if** they contain at least one of the following characters:
  
  - comma (`,`)
  
  - double quote (`"`)
  
  - newline (`\n` or `\r\n`)

- Inside a quoted field, any double quote (`"`) MUST be escaped by doubling it (`""`).

- Other characters MUST NOT be escaped.

- Each record MUST be on a separate line, terminated by a newline character (`\n` or `\r\n`).

### **4.2. Logging severity levels**

The application SHALL classify all messages into the following severity levels:

1. **INFO**
   
   - Describes normal progress and high-level lifecycle events.
   
   - Examples:
     
     - “Reading source file `<path>`…”
     
     - “Detected 12 validation rules.”
     
     - “Writing output file `validation_rules.csv`…”

2. **WARNING**
   
   - Indicates a non-fatal issue where the tool can still produce a **usable, but possibly incomplete** CSV output.
   
   - The run continues and exits with a success exit code (0), but warnings MUST be visible in the console summary.
   
   - Examples (non-exhaustive):
     
     - A Kotlin or OpenAPI construct could not be confidently interpreted as a rule, and the tool skipped it.
     
     - A field name could not be mapped to a human-friendly label; a fallback label was used.
     
     - An unexpected OpenAPI keyword was encountered and ignored.

3. **ERROR**
   
   - Indicates a **fatal** condition where the tool cannot produce a reliable output for the current run.
   
   - The run MUST terminate with a non-zero exit code, and MUST NOT create or update the CSV output file (or MUST delete any partially written file).
   
   - Examples (non-exhaustive):
     
     - Input file does not exist or cannot be read.
     
     - Input file format is unsupported or corrupted (e.g., invalid YAML/JSON, unreadable Kotlin AST).
     
     - Mandatory configuration is missing or invalid (e.g., no output path, invalid model/mode setting).
     
     - Internal error / unhandled exception during parsing or rule extraction.

### **4.3. Failure behavior and partial output**

1. **Single input file per run (v1 scope)**
   
   - If an **ERROR** occurs **before** any rules have been successfully extracted, the application:
     
     - SHALL terminate with a non-zero exit code.
     
     - SHALL NOT create the CSV output file.
   
   - If an **ERROR** occurs **after** some rules have already been extracted (e.g., internal error during a later phase), the application:
     
     - SHALL terminate with a non-zero exit code.
     
     - SHALL delete any partially written CSV output file (if created), so that consumers never see a partial file.
   
   - If only **WARNING** messages are produced:
     
     - The application SHALL complete the run, write the CSV file with all successfully extracted rules, and exit with code 0.
     
     - The presence of warnings SHALL be clearly indicated in the final console summary (e.g., “Completed with 3 warnings.”).

2. **Rule-level issues**
   
   - If a specific construct in the input cannot be reliably mapped to a validation rule, the application:
     
     - SHALL skip this construct.
     
     - SHALL log a WARNING describing the reason and, where possible, the file name and line range.
     
     - SHALL continue processing remaining constructs in the same file.

3. **Configuration errors**
   
   - No configuration errors are expected since all configuration parameters must have default values.

### **4.4 Logging and progress reporting**

1. **Console output**
   
   - The application SHALL write human-readable progress messages and summary information to `stdout`.
   
   - The application SHALL write WARNING and ERROR messages to `stderr` (or clearly prefix them, e.g. `[WARNING]`, `[ERROR]`).

2. **Log entry contents**  
   Each log entry SHOULD contain at least:
   
   - Timestamp (local or UTC).
   
   - Severity (e.g., INFO, WARNING, ERROR).
   
   - Message text.
   
   - Where applicable, the source file path and line range.
   
   **Example format (non-normative):**
- `2025-12-03T12:34:56Z INFO Reading source file: validations.kt`

- `2025-12-03T12:34:57Z WARNING Cannot interpret constraint at validations.kt:120-130 (skipping).`

- `2025-12-03T12:34:58Z ERROR Failed to parse YAML: offers.yaml`
3. **Progress reporting**
   
   - For each run, the application SHALL, at minimum, log the following INFO messages:
     
     - Start of processing, including the input file path.
     
     - Completion of parsing and rule extraction, including:
       
       - Number of rules detected.
       
       - Number of rules skipped due to warnings.
     
     - Start and completion of writing the CSV output file, including the output path.
     
     - Final status line summarizing the run, e.g.:
       
       - “Completed successfully. Extracted 25 rules. 3 warnings.”
       
       - “Failed with 1 error. See messages above.”

4. **Optional log file**
   
   - The application MAY support an optional configuration parameter (e.g., `LOG_FILE` or `--log-file`) to write all log messages to a file in addition to the console.
   
   - If enabled, the file SHOULD use the same logging format as the console output.

## 5. User Stories and Acceptance Criteria

---

#### US-BA-001: Run Validation Rules Extraction

**As a** Business Analyst  
**I want** to run automatic extraction of validation rules from the selected file  
**So that** I can generate a rules list without reading code/schema description line by line

**Acceptance Criteria**

- AC1: The applicationparses the specified source code/schema description according to the configured method.

- AC2: If parsing fails, the application shows and logs warnings/error messages.

- AC3: After successfull completion, the user can see the message that the output CSV file has been created. The name of the output file may or may not be specifed by the user. If the output file name is missing, use `output.csv` and place the file into the current working folder.

- AC4: The output CSV file contains the table with at least the following columns:
  
  - Rule ID
  
  - Description
  
  - Source file
  
  - Endpoint
  
  - Endpoint entity
  
  - Lines
  
  - Depends on.

- AC5: Cyclic dependencies are allowed but should be visually indicated (e.g., warning).

- AC6: If a validation rule cannot be extracted/shaped, the application displays the warning and proceeds to the next rule.

## 6. Technical Constraints & Assumptions

- Initial release targets a CLI Python application. For v1 just a single input file is allowed.

- Supported programming languages for v1: Kotlin, `openapi: 3.0.x` YAML

- Source code / schema description provided is trusted and free of malicious or sensitive content.

## 7. Non-functional requirements

7.1. Testability: The Kotlin and OpenAPI examples MUST be covered by automated tests producing exactly the sample CSVs.

7.2. The application should have modular architecture providing flexibility (e.g. adding new methods, API schema vulnerability analysis) and further development (e.g. introducting user interface, converting to a web app). 

## Appendix A

## A.1. Worked Example for Kotlin Source

### A.1.1. Input file

Example input file: `RequestValidator_sample.kt`  
Relevant fragment:

```kotlin
fun validateChannelRequest(channel: ListOfferChannel) {
    val region = SiteID.valueOf(channel.siteID.uppercase()).getRegion()
    if (shouldValidateChannelMapping(region)) {
        validateChannelMapping(channel.target, channel.medium)
    }
}

private fun shouldValidateChannelMapping(region: String): Boolean =
    region == "wr" && channelConfig.beneAdminFeesFeatureFlag

private fun validateChannelMapping(
    target: String,
    medium: String,
) {
    val targetKey = target.lowercase()
    val mediumValue = medium.uppercase()

    val isValidMapping =
        channelConfig.targetToMediumMap[targetKey]
            ?.contains(mediumValue) == true

    if (!isValidMapping) {
        throwValidationException(
            "Invalid channel mapping for target: $target and medium: $medium",
            HOF_VALIDATION_FAILED,
            HOF,
        )
    }
}
```

**Assumption for this example:**  
`validateChannelRequest` is defined at lines 94–101 and `validateChannelMapping` at lines 103–120 of the source file.

### A.1.2. Detected validation rules (conceptual extraction)

#### Rule 1 – When channel mapping validation applies

- **Location:**
  
  - File: `RequestValidator_sample.kt`
  
  - Lines: `94–101` (function `validateChannelRequest`)
  
  - Lines: `103–105` (function `shouldValidateChannelMapping`)

- **Logic:**
  
  - The site region is derived as:
    
    - `region = SiteID.valueOf(channel.siteID.uppercase()).getRegion()`
  
  - Channel mapping validation is performed only if:
    
    - `region == "wr"` **AND** `channelConfig.beneAdminFeesFeatureFlag == true`.

- **Resulting business rule (description):**
  
  - *If the site region resolved from `channel.siteID` equals `'wr'` and the `beneAdminFeesFeatureFlag` is enabled, then the request’s `(target, medium)` pair must be validated against the configured channel mapping.*

#### Rule 2 – Channel mapping validity

- **Location:**
  
  - File: `RequestValidator_sample.kt`
  
  - Lines: `103–120` (function `validateChannelMapping`)

- **Logic:**
  
  - The target key and medium value are normalised as:
    
    - `targetKey = target.lowercase()`
    
    - `mediumValue = medium.uppercase()`
  
  - A mapping is considered valid if:
    
    - `channelConfig.targetToMediumMap[targetKey]?.contains(mediumValue) == true`
  
  - Otherwise, a validation exception is thrown with message:
    
    - `"Invalid channel mapping for target: $target and medium: $medium"`.

- **Resulting business rule (description):**
  
  - *For region `'wr'` with `beneAdminFeesFeatureFlag = true`, the pair `(target.lowercase(), medium.uppercase())` must exist in `channelConfig.targetToMediumMap`; otherwise, the request is rejected with an “Invalid channel mapping…” validation error.*

#### Dependency

- `validateChannelMapping` is only called inside `validateChannelRequest` when `shouldValidateChannelMapping(region)` is `true`.

- Therefore **Rule 2 depends on Rule 1** and SHOULD reference it in the `Depends on` column.

### A.1.3. Example CSV output

For this file, the application MUST produce a CSV(UTF-8) file with at least the following rows (header taken from “**The output file**” subsection   of **4.1 BA – Generate Rules from Source code/schema description**):

```csv
Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on
RULE-001,"If the site region resolved from 'channel.siteID' equals 'wr' AND 'beneAdminFeesFeatureFlag' is true, then the request's (target, medium) must be validated against the configured channel mapping.","RequestValidator_sample.kt","94-105",,, 
RULE-002,"For region 'wr' with 'beneAdminFeesFeatureFlag' = true, the pair (target.lowercase(), medium.uppercase()) must exist in 'channelConfig.targetToMediumMap'; otherwise the request is rejected with 'Invalid channel mapping for target: <target> and medium: <medium>'.","RequestValidator_sample.kt","103-120",,,"RULE-001"
```

Notes for this example:

- **Rule ID** values (`RULE-001`, `RULE-002`) follow the pattern described in the SRS and MUST be unique within a single run.

- **Description** MUST be a human-readable, self-contained statement of the rule derived from the code.

- **Source file** MUST contain the actual file name (or relative path) of the analysed source file.

- **Lines** MUST represent the line range where the rule is implemented. Overlapping ranges are allowed if a rule spans multiple functions.

- **Endpoint** and **Endpoint entity** are left empty for Kotlin code, as they apply only to OpenAPI/YAML input in the current version.

- **Depends on** for `RULE-002` MUST reference `RULE-001`, indicating that the mapping validity rule is only applicable when the condition from Rule 1 is satisfied.

### A.1.4. Implementation guidance derived from the example

From this example, the following behaviour is REQUIRED for Kotlin parsing:

1. **Rule identification**
   
   - The tool MUST identify validation rules originating from:
     
     - Conditional checks that guard a validation call (e.g. `if (shouldValidateChannelMapping(region))`).
     
     - Functions that throw validation exceptions or otherwise reject requests (e.g. `throwValidationException(...)`).

2. **Description generation**
   
   - The tool MUST generate a concise, human-friendly rule description that:
     
     - Reflects the main condition(s) (e.g. `region == "wr"` and feature flag).
     
     - Reflects the validation effect (e.g. “must exist in mapping”, “otherwise request is rejected”).

3. **Line ranges**
   
   - The tool SHOULD compute line ranges so that:
     
     - Guard conditions and the called validation function may be merged into a single rule (as in Rule 1) if they conceptually define a single validation rule.
     
     - The actual validation logic (e.g. mapping lookup + exception) is captured in a separate rule where appropriate (as in Rule 2).

4. **Dependencies**
   
   - If a rule is only applicable when another rule’s condition holds (e.g., a validator is only invoked under certain conditions), the tool MUST express this via the `Depends on` column using the corresponding `Rule ID`.

## A.2. Worked Example for OpenAPI 3.0.2 Specification

### A.2.1. Input file

Example input file: `openapi-spec - sample.yml`

Relevant fragments:

```yaml
openapi: 3.0.2
info:
  version: 1.0.0-oas3
  title: xyz NGS Product and Price Search API for Package Holidays

paths:
  /v3/package/search/results:
    post:
      description: |
        Retrieve list of Package items and facets with cheapest price offer.
        Follows the standards for parameters from the
        Note - filters are yet to be defined
      requestBody:
        content:
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/PackageSearchRequestParams"
            }
          }
        required: true
      parameters:
        # (omitted for brevity)
        ...

components:
  schemas:
    PackageSearchRequestParams:
      description: Product price search Abstract request V3.
      type: object
      required:
        - from
      properties:
        from:
          type: array
          items:
            $ref: '#/components/schemas/From'

    PackageSearchResponse:
      title: SearchResultResponseV3
      required:
        - holidays
      type: object
      properties:
        holidays:
          $ref: '#/components/schemas/Holidays'

    From:
      type: "object"
      required:
        - code
      properties:
        code:
          type: string
          description: Departure Code
          example: BRU
        type:
          type: string
          enum: [ "AIRPORT" ]

    Holidays:
      title: Holidays
      required:
        - offers
      type: object
      properties:
        offers:
          type: array
          items:
            allOf:
              - $ref: '#/components/schemas/Offer'

    Offer:
      title: Offer
      required:
        - productID
      type: object
      properties:
        productID:
          type: string
          example: 748f6b96-a99a-4a3e-bd50-1b4b9c9fa7ac
```

**Assumption for this example:**  
Line ranges are based on the current sample spec (e.g. `paths` block around lines 13–26, `PackageSearchRequestParams` around 49–58, `From` around 67–76, `Holidays` around 76–88, `Offer` around 91–99). If the spec changes, line numbers will change accordingly.

### A.2.2. Detected validation rules (conceptual extraction)

For this OpenAPI spec, the application SHOULD detect at least the following validation rules.

#### Rule 3 – Request body is required for the search endpoint

- **Location:**
  
  - File: `openapi-spec - sample.yml`
  
  - Lines: `13–26` (`paths./v3/package/search/results.post.requestBody`)

- **Logic (OpenAPI):**
  
  - The POST `/v3/package/search/results` operation defines a `requestBody` with:
    
    - `required: true`
    
    - Schema: `$ref: '#/components/schemas/PackageSearchRequestParams'`

- **Resulting business rule (description):**
  
  - *For the POST `/v3/package/search/results` endpoint, a JSON request body conforming to `PackageSearchRequestParams` MUST be provided; requests without a body are invalid.*

#### Rule 4 – Request must include the `from` array

- **Location:**
  
  - File: `openapi-spec - sample.yml`
  
  - Lines: `49–58` (`components.schemas.PackageSearchRequestParams`)

- **Logic (OpenAPI):**
  
  - `PackageSearchRequestParams`:
    
    - `type: object`
    
    - `required: [ from ]`
    
    - `properties.from`:
      
      - `type: array`
      
      - `items: $ref: '#/components/schemas/From'`

- **Resulting business rule (description):**
  
  - *The `PackageSearchRequestParams` request body MUST contain a `from` property. `from` MUST be an array of `From` objects representing departure points.*

- **Dependency:**
  
  - This rule refines the required request body for the same endpoint.
  
  - **Depends on:** Rule 3 (request body required).

#### Rule 5 – Each `From` object must include a departure code and a valid type

- **Location:**
  
  - File: `openapi-spec - sample.yml`
  
  - Lines: `67–76` (`components.schemas.From`)

- **Logic (OpenAPI):**
  
  - `From`:
    
    - `type: object`
    
    - `required: [ code ]`
    
    - `properties.code`:
      
      - `type: string`
      
      - `description: Departure Code`
      
      - `example: BRU`
    
    - `properties.type`:
      
      - `type: string`
      
      - `enum: [ "AIRPORT" ]`

- **Resulting business rule (description):**
  
  - *Each element of the `from` array MUST contain a `code` field, which is a string representing the departure code (e.g. `BRU`). If the optional `type` field is provided, its value MUST be `"AIRPORT"`; any other value is invalid.*

- **Dependency:**
  
  - This rule refines the structure of the `from` array.
  
  - **Depends on:** Rule 4 (the `from` array is required).

#### Rule 6 – Response must include `holidays`

- **Location:**
  
  - File: `openapi-spec - sample.yml`
  
  - Lines: `60–66` (`components.schemas.PackageSearchResponse`)

- **Logic (OpenAPI):**
  
  - `PackageSearchResponse`:
    
    - `required: [ holidays ]`
    
    - `properties.holidays`:
      
      - `$ref: '#/components/schemas/Holidays'`

- **Resulting business rule (description):**
  
  - *The `PackageSearchResponse` object MUST include a `holidays` property containing holiday offers.*

- **Dependency (optional design choice):**
  
  - If you link responses back to endpoints, this rule can be associated with the response of `/v3/package/search/results`.

#### Rule 7 – Each holiday collection must contain offers, and each offer must have a product ID

- **Location:**
  
  - File: `openapi-spec - sample.yml`
  
  - Lines: `76–88` (`Holidays`) and `91–99` (`Offer`)

- **Logic (OpenAPI):**
  
  - `Holidays`:
    
    - `required: [ offers ]`
    
    - `properties.offers`:
      
      - `type: array`
      
      - `items` referencing `Offer`
  
  - `Offer`:
    
    - `required: [ productID ]`
    
    - `properties.productID`:
      
      - `type: string`

- **Resulting business rule (description):**
  
  - *The `Holidays` structure MUST contain an `offers` array. Each `Offer` in this array MUST include a `productID` field of type string; offers without a `productID` are invalid.*

- **Dependencies:**
  
  - The offers rule refines the `holidays` structure.
  
  - **Depends on:** Rule 6.

### A.2.3. Example CSV output

Using the same CSV header as in the Kotlin example:

```
Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on
```

An example CSV output for these OpenAPI-derived rules:

```csv
Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on
RULE-003,"For the POST '/v3/package/search/results' endpoint, a JSON request body conforming to 'PackageSearchRequestParams' MUST be provided; requests without a body are invalid.","openapi-spec - sample.yml","13-26","/v3/package/search/results [POST]","PackageSearchRequestParams",
RULE-004,"The 'PackageSearchRequestParams' request body MUST contain a 'from' property. 'from' MUST be an array of 'From' objects representing departure points.","openapi-spec - sample.yml","49-58","/v3/package/search/results [POST]","PackageSearchRequestParams.from[]","RULE-003"
RULE-005,"Each element of the 'from' array MUST contain a 'code' field (string) representing the departure code (for example 'BRU'). If the optional 'type' field is provided, its value MUST be 'AIRPORT'; any other value is invalid.","openapi-spec - sample.yml","67-76","/v3/package/search/results [POST]","From","RULE-004"
RULE-006,"The 'PackageSearchResponse' object MUST include a 'holidays' property containing holiday offers.","openapi-spec - sample.yml","60-66","/v3/package/search/results [POST]","PackageSearchResponse.holidays",
RULE-007,"The 'Holidays' structure MUST contain an 'offers' array, and each 'Offer' in this array MUST include a 'productID' field of type string; offers without a 'productID' are invalid.","openapi-spec - sample.yml","76-99","/v3/package/search/results [POST]","Holidays.offers[].Offer.productID","RULE-006"
```

Notes:

- **Rule ID** numbering (starting from `RULE-003`) continues from the Kotlin example (`RULE-001`, `RULE-002`), but in practice IDs only need to be unique within a given run.

- **Endpoint** uses a consistent pattern such as `"/v3/package/search/results [POST]"`.

- **Endpoint entity** helps pinpoint the schema location:
  
  - `PackageSearchRequestParams.from[]`
  
  - `From`
  
  - `PackageSearchResponse.holidays`
  
  - `Holidays.offers[].Offer.productID`

- **Depends on** models structural dependencies:
  
  - Request body → its required field → element structure.
  
  - Response object → nested collections and items.

### A.2.4. Implementation guidance derived from the OpenAPI example

From this example, the following behaviour is REQUIRED for OpenAPI parsing:

1. **Schema-based rule extraction**
   
   - The tool MUST treat the following OpenAPI constructs as potential validation rules:
     
     - `required` arrays (e.g. `required: [ from ]`, `required: [ holidays ]`, `required: [ productID ]`).
     
     - Property-level constraints such as:
       
       - `type` (e.g. `string`, `array`, `object`).
       
       - `enum` values (e.g. `"AIRPORT"`).
     
     - Required request bodies (`requestBody.required: true`).

2. **Endpoint association**
   
   - For request-related rules, the tool SHOULD:
     
     - Associate schema refs (`$ref`) under `requestBody` with the corresponding endpoint and HTTP method.
     
     - Populate `Endpoint` with the path + method.
     
     - Populate `Endpoint entity` with a dotted path to the relevant schema fragment (e.g. `PackageSearchRequestParams.from[]`).

3. **Response-related rules**
   
   - For response-related rules (like `PackageSearchResponse.holidays` → `Holidays.offers` → `Offer.productID`), the tool SHOULD:
     
     - Associate them with the corresponding endpoint if they are used as that endpoint’s response schema.
     
     - Use the same `Endpoint` and appropriate `Endpoint entity` value.

4. **Dependencies**
   
   - The tool MUST use the `Depends on` column to model hierarchical relationships:
     
     - Child rules (e.g. properties of `From`) depend on their parent object being required.
     
     - Deeper nested rules (e.g. `Offer.productID`) depend on intermediate containers (e.g. `Holidays.offers`) being required.

5. **Consistency with code-based rules**
   
   - OpenAPI-derived rules MUST be expressed in the same human-friendly style as code-derived rules, so that the resulting CSV can mix rules extracted from:
     
     - Kotlin/Java code, and
     
     - OpenAPI schemas  
       in one coherent catalogue.
