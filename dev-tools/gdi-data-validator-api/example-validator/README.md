# Example Word Count Validator

This provides an example **GDI Data Validator** that checks whether a text file contains between **500 and 1000 words**.

It demonstrates how to package and run a validator in an **Apptainer** (or **Singularity**) container following the GDI Data Validator specification.

---

## Prerequisites

Before you begin, ensure you have **Apptainer** (or **Singularity**) installed on your system.

For installation instructions, refer to the [Apptainer documentation](https://apptainer.org/docs/).

---

## Build the Container

The validator container is defined in the file `src/Apptainer.def`.

From the project root directory (`example-validator`), build the container using:

```bash
sudo apptainer build word_count_validator.sif src/Apptainer.def
```

This command produces a runnable image file named `word_count_validator.sif`.

## Running the Example Validator

The validator follows the GDI validator specification, which requires:

- An input JSON file describing the validation request.
- A mounted input directory containing the data files to validate.
- A mounted output directory where results will be written.

Test data are provided in the `test_data` subfolder.

### Display the Validator Metadata

To view the validator’s metadata (as defined in `src/metadata.json`):

```bash
apptainer run word_count_validator.sif --describe
```

The output will be a JSON description of the validator:
(see `src/metadata.json` for details)

### Run Validation (Expected to Pass)

```bash
mkdir -p output
apptainer run \
    --bind "$(pwd)/test_data/input.json":/mnt/input/input.json:ro \
    --bind "$(pwd)/test_data/data_pass":/mnt/input/data:ro \
    --bind "$(pwd)/output":/mnt/output \
    word_count_validator.sif
```

**Expected output:**

The validation result is written to `output/result.json`.

```json
{
  "result": "passed",
  "files": [
    {
      "path": "/mnt/input/data/doc.txt",
      "result": "passed",
      "messages": [
        {
          "level": "info",
          "time": "2025-10-10T15:50:35.334312Z",
          "message": "Word count is 600. Criteria (500-1000) met."
        }
      ]
    }
  ],
  "messages": [
    {
      "level": "info",
      "time": "2025-10-10T15:50:35.331879Z",
      "message": "Word Count Validator started."
    }
  ]
}
```

### Run Validation (Expected to Fail)

```bash
mkdir -p output
apptainer run \
    --bind "$(pwd)/test_data/input.json":/mnt/input/input.json:ro \
    --bind "$(pwd)/test_data/data_fail":/mnt/input/data:ro \
    --bind "$(pwd)/output":/mnt/output \
    word_count_validator.sif
```

**Expected output:**

The validation result is written to `output/result.json`.

```json
{
  "result": "failed",
  "files": [
    {
      "path": "/mnt/input/data/doc.txt",
      "result": "failed",
      "messages": [
        {
          "level": "error",
          "time": "2025-10-10T15:53:04.414574Z",
          "message": "Word count is 200. Expected between 500 and 1000."
        }
      ]
    }
  ],
  "messages": [
    {
      "level": "info",
      "time": "2025-10-10T15:53:04.412030Z",
      "message": "Word Count Validator started."
    }
  ]
}
```
