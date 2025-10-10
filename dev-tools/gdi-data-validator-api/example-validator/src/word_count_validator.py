#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# --- Constants for GDI Specification ---
INPUT_JSON_PATH = Path("/mnt/input/input.json")
OUTPUT_JSON_PATH = Path("/mnt/output/result.json")

# Validator metadata file path, determined by the Apptainer definition
METADATA_PATH = Path("/usr/local/share/metadata.json")

def create_message(level, message):
    """Create a standardized message dictionary."""
    return {
        "level": level,
        "time": datetime.now().isoformat() + "Z",
        "message": message,
    }


def create_result(overall_result, files_results=None, top_messages=None):
    """Create the standardized output JSON structure."""
    return {
        "result": overall_result,
        "files": files_results or [],
        "messages": top_messages or [],
    }


def describe_validator():
    """Print validator metadata to stdout."""
    if not METADATA_PATH.exists():
        sys.exit(f"Error: Metadata file not found at expected location ({METADATA_PATH}).")
    print(METADATA_PATH.read_text(encoding="utf-8"))


def validate_words(file_path):
    """Count words in a file and check if the count is between 500 and 1000."""
    MIN_WORDS = 500
    MAX_WORDS = 1000

    try:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Path is not a file or does not exist: {file_path}")

        content = path.read_text(encoding="utf-8")
        word_count = len(content.split())

        if MIN_WORDS <= word_count <= MAX_WORDS:
            result = "passed"
            messages = [
                create_message("info", f"Word count is {word_count}. Criteria ({MIN_WORDS}-{MAX_WORDS}) met.")
            ]
        else:
            result = "failed"
            messages = [
                create_message("error", f"Word count is {word_count}. Expected between {MIN_WORDS} and {MAX_WORDS}.")
            ]

    except FileNotFoundError:
        result = "failed"
        messages = [create_message("error", f"File not found or inaccessible: {file_path}")]
        word_count = -1
    except Exception as e:
        result = "failed"
        messages = [create_message("error", f"Unexpected error during validation: {e}")]
        word_count = -1

    return result, messages, word_count


def run_validation():
    """Perform validation according to the GDI input specification."""
    top_messages = [create_message("info", "Word Count Validator started.")]
    overall_result = "passed"
    files_results = []

    try:
        # Step 1: Read and parse input.json
        if not INPUT_JSON_PATH.exists():
            raise FileNotFoundError(f"Input file not found at {INPUT_JSON_PATH}")

        input_data = json.loads(INPUT_JSON_PATH.read_text(encoding="utf-8"))
        files_to_validate = input_data.get("files", [])

        if not files_to_validate:
            raise ValueError("Input JSON must contain a non-empty 'files' array for file mode.")

        # Step 2: Validate each file
        for file_info in files_to_validate:
            file_path = file_info.get("path")
            if not file_path:
                continue

            file_result, file_messages, _ = validate_words(file_path)
            if file_result == "failed":
                overall_result = "failed"

            files_results.append({
                "path": file_path,
                "result": file_result,
                "messages": file_messages,
            })

    except Exception as e:
        overall_result = "failed"
        top_messages.append(create_message("error", f"Validator crashed before completing: {e}"))
        files_results = []

    # Step 3: Write output.json
    output_data = create_result(overall_result, files_results, top_messages)
    try:
        OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON_PATH.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    except Exception as e:
        sys.exit(f"Critical Error: Failed to write output JSON to {OUTPUT_JSON_PATH}: {e}")


def main():
    """CLI entrypoint for the validator."""
    parser = argparse.ArgumentParser(description="GDI Word Count Validator")
    parser.add_argument("--describe", action="store_true", help="Print validator metadata.")
    args = parser.parse_args()

    if args.describe:
        describe_validator()
    else:
        run_validation()


if __name__ == "__main__":
    main()
