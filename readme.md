# Valid Builder

Valid Builder is a command-line tool that extracts validation rules from a single Kotlin source file or OpenAPI 3.0.x YAML file and writes them to an RFC4180-compliant CSV. The output lists each rule with a unique ID, description, source file and lines, endpoint context, and dependencies so business analysts can review implemented validations quickly.

## Requirements

- Python 3.10 or later
- Runtime dependencies are declared in `pyproject.toml` and include:
  - [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/) for parsing OpenAPI documents while preserving line numbers.
  - [`python-dotenv`](https://pypi.org/project/python-dotenv/) for reading `.env` configuration files.

## Installation

Install the package in editable mode from the repository root:

```bash
python -m pip install -e .
```

This installs the `valid-builder` console script.

## Usage

Run the CLI by providing a single input file and an optional output path:

```bash
valid-builder path/to/input.kt --output rules.csv
valid-builder "path/to/openapi.yml" --output rules.csv
```

Additional options:

- `--lang` – override language detection (`kotlin` or `openapi`).
- `--config` – path to a `.env` file that customizes defaults such as the starting rule ID or log destination.

If `--output` is omitted, the CSV defaults to `output.csv` in the current working directory.

## Configuration

The tool reads defaults from an `.env` file (path configurable via `--config`). Key variables include:

- `DEFAULT_RULE_ID` – starting rule ID template (e.g., `RULE-001`).
- `OPENAPI_ENDPOINT_ENTITIES` – comma-separated endpoint entity labels.
- `LLM_METHOD`, `LLM_MODEL`, `LLM_URL`, `LLM_API_KEY` – reserved for future LLM-based extraction.
- `LOG_FILE`, `LOG_LEVEL` – optional log destination and verbosity.

Command-line arguments take precedence over `.env` values.

## Running Tests

From the repository root, execute:

```bash
pytest
```

The test suite includes unit, integration, and end-to-end coverage across Kotlin, OpenAPI, configuration, orchestration, logging, and packaging behaviors.
