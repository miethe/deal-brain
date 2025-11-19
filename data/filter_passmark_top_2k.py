#!/usr/bin/env python3
"""
Filter PassMark CPU data to top 2500 ranked CPUs.

This script reads the full PassMark dataset and filters entries where
the rank is <= 2500, writing the results to a new JSON file.

Usage:
    python data/filter_passmark_top_2k.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_passmark_data(input_path: Path) -> Dict[str, Any]:
    """
    Load PassMark data from JSON file.

    Args:
        input_path: Path to the input JSON file

    Returns:
        Dictionary containing the PassMark data structure

    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If input file contains invalid JSON
    """
    try:
        with input_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        raise


def filter_by_rank(data: List[Dict[str, Any]], max_rank: int = 2500) -> List[Dict[str, Any]]:
    """
    Filter CPU entries by rank threshold.

    Args:
        data: List of CPU data dictionaries
        max_rank: Maximum rank to include (inclusive)

    Returns:
        Filtered list of CPU entries with rank <= max_rank
    """
    return [
        entry for entry in data if isinstance(entry.get("rank"), int) and entry["rank"] <= max_rank
    ]


def save_filtered_data(output_path: Path, filtered_data: Dict[str, Any]) -> None:
    """
    Save filtered data to JSON file with proper formatting.

    Args:
        output_path: Path to the output JSON file
        filtered_data: Dictionary containing filtered PassMark data

    Raises:
        IOError: If unable to write to output file
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error: Unable to write output file: {e}", file=sys.stderr)
        raise


def print_summary(original_count: int, filtered_count: int, max_rank: int) -> None:
    """
    Print a summary of the filtering operation.

    Args:
        original_count: Number of entries in original dataset
        filtered_count: Number of entries after filtering
        max_rank: Maximum rank threshold used
    """
    removed_count = original_count - filtered_count
    percentage = (filtered_count / original_count * 100) if original_count > 0 else 0

    print("=" * 60)
    print("PassMark Data Filtering Summary")
    print("=" * 60)
    print(f"Original entries:     {original_count:,}")
    print(f"Filtered entries:     {filtered_count:,} (rank <= {max_rank})")
    print(f"Removed entries:      {removed_count:,}")
    print(f"Retention rate:       {percentage:.1f}%")
    print("=" * 60)


def main() -> int:
    """
    Main execution function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Define file paths relative to script location
    script_dir = Path(__file__).parent
    input_path = script_dir / "passmark_data.json"
    output_path = script_dir / "top-2k-passmark.json"

    # Configuration
    MAX_RANK = 2500

    try:
        # Load input data
        print(f"Loading data from: {input_path}")
        passmark_data = load_passmark_data(input_path)

        # Extract and validate data array
        if "data" not in passmark_data or not isinstance(passmark_data["data"], list):
            print("Error: Invalid data structure - expected 'data' array", file=sys.stderr)
            return 1

        original_entries = passmark_data["data"]
        original_count = len(original_entries)

        # Filter data
        print(f"Filtering entries with rank <= {MAX_RANK}...")
        filtered_entries = filter_by_rank(original_entries, max_rank=MAX_RANK)
        filtered_count = len(filtered_entries)

        # Prepare output structure (preserve original structure)
        filtered_data = {"data": filtered_entries}

        # Save results
        print(f"Saving filtered data to: {output_path}")
        save_filtered_data(output_path, filtered_data)

        # Print summary
        print_summary(original_count, filtered_count, MAX_RANK)

        print(f"\n✓ Successfully created: {output_path}")
        return 0

    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        print(f"\n✗ Operation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
