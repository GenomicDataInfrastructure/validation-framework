# Implementation Specifications for GDI Data Validators

## Overview

This document specifies the contract for data validation services within the GDI project. These services perform sanity checks to ensure data integrity.

The validators are designed to be pluggable and containerized, ensuring consistency and a predictable I/O interface. They operate with the principle of least privilege and should be delivered as containers, with **Apptainer** as the recommended choice due to its suitability for secure, multi-user environments.

The validation process includes checks for both:

- File content: Validating file formats (e.g., BAM, CRAM, VCF, XML), their embedded metadata, and paired files where applicable (e.g., BAM and its corresponding BAI index).
- File structure: Verifying folder layouts, file naming conventions, and file-level metadata.


By adhering to a unified I/O contract, all validators are guaranteed to be interoperable.

## General requirements

- Each validator runs as an isolated process (in a container).
- Input consists of a JSON request file and a data directory containing the files to be validated.
- Output must be written as a JSON response file to a designated mounted location.
- No external state or network calls are allowed (except if explicitly permitted).
- Validators must expose a metadata description of their capabilities.
- Validators must be deterministic: same input -> same output.

## Input Specification

**Input contains:**

- A single JSON object mounted at `/mnt/input/input.json`.
- A data path containing files to be validated mounted at `/mnt/input/data`.
- `/mnt/input` mounted as read-only.

**Properties for the JSON object:**

```json
{
  "files": [
    {
      "path": "/mnt/input/data/dataset_dummy/sample.bam"
    }
  ],
  "paths": [
    "/mnt/input/data/dataset_dummy/sample1.bam",
    "/mnt/input/data/dataset_dummy/sample2.bam"
  ],
  "config": {
    // optional, validation-specific config
  }
}
```

**Field descriptions:**

- `files`: array of files for file content validation.
  - `path`: file path inside the container.
- `paths`: array of file paths for file structure validation.
- Exactly one of `files` and `paths` must be present.
- `config`: optional configuration for the validator.

**Example (file content validation with a single file):**

```json
{
  "files": [
    {
      "path": "/mnt/input/data/dataset_dummy/dataset.xml"
    }
  ]
}
```

**Example (file structure validation):**

```json
{
  "paths": [
    "/mnt/input/data/dataset_dummy/dataset.xml",
    "/mnt/input/data/dataset_dummy/sample1.bam",
    "/mnt/input/data/dataset_dummy/sample1.bai",
    "/mnt/input/data/dataset_dummy/sample2.bam",
    "/mnt/input/data/dataset_dummy/sample2.bai"
  ]
}
```

## Output specification

**Output contains:**

- A single JSON object mounted at `/mnt/output/result.json`.
  - Has two layers of output:
    - Overall result (single job-level outcome).
    - Detailed results (per-file, optional for file structure validation).

**Properties for the JSON object:**

```json
{
  "result": "passed" | "failed", // overall result
  "files": [ // detailed per-file results
    {
      "path": "/mnt/input/data/dataset_dummy/sample.bam",
      "result": "failed",
      "messages": [
        {
          "level": "error",
          "time": "2025-09-16T10:00:00Z",
          "message": "Invalid BAM header: missing @SQ"
        }
      ]
    }
  ],
  "messages": [
    {
      "level": "warning",
      "time": "2025-09-16T10:05:00Z",
      "message": "Validator ran with default config"
    }
  ]
}
```

**Field descriptions:**

- `result` — one of: `passed`, `failed` (overall aggregation).
  - `passed` = all files passed (possibly with warnings).
  - `failed` = at least one file failed validation, or the validator crashed.
- `files`— per-file detail (optional for file structure validation).
  - `path` — the validated file path.
  - `result` — `passed` or `failed`.
  - `messages` — structured messages:
    - `level`: `info`, `warning`, `error`
    - `time`: ISO 8601 timestamp
    - `message`: human-readable description
- `messages` (top-level) — optional job-level messages (e.g., config issues, execution warnings).

**Example (file content validation with multiple files):**

```json
{
  "result": "failed",
  "files": [
    {
      "path": "/mnt/input/data/dataset_dummy/sample1.bam",
      "result": "passed",
      "messages": []
    },
    {
      "path": "/mnt/input/data/dataset_dummy/sample2.bam",
      "result": "failed",
      "messages": [
        {
          "level": "error",
          "time": "2025-08-26T12:30:00Z",
          "message": "Invalid BAM header: missing @SQ"
        }
      ]
    }
  ]
}
```

## Error handling

- All errors must be reported in the messages section.
- If the validator fails before producing per-file results, it should return something like this:

```json
{
  "result": "failed",
  "files": [],
  "messages": [
    {
      "level": "error",
      "time": "2025-08-26T12:45:00Z",
      "message": "Validator crashed due to invalid input format"
    }
  ]
}
```

## Validator Metadata (Capabilities Declaration)

Every validator must ship with a metadata JSON to describe what it can do, when called by the `--describe` flag.

**Required fields:**

```json
{
  "validatorId": "xml-schema-validator",
  "name": "XML Schema Validator",
  "description": "Validates XML metadata files against the GDI XSD schema.",
  "version": "1.2.0",
  "mode": "file" | "file-structure" | "file-pair",
  "pathSpecification": ["METADATA/*.xml"]
}
```

**Field descriptions:**

- `validatorId` — unique identifier for the validator.
- `name` — human-readable name.
- `description` — short description of what it checks.
- `version` — semantic version.
- `mode` — validation mode.
  - `file` - validates the content of individual files.
  - `file-structure` - validates the overall file structure (e.g., directory layout, required files present).
  - `file-pair` - validates related files together (e.g., BAM and BAI pairs).
- `pathSpecification` — list of path patterns used to select files to validate (e.g., METADATA/*.xml).

## Communication Summary

- What validator receives:
  - A single JSON object with file paths mounted at `/mnt/input/input.json`.
  - A data path containing files to be validated mounted at `/mnt/input/data`.
- What validator produces:
  - A single JSON object with overall and/or per-file results mounted at `/mnt/output/result.json`.
- How validator declares itself:
  - Metadata JSON describing supported capabilities, version, etc.
