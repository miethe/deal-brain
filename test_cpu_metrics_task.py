"""Test script for CPU metrics recalculation task."""

import asyncio
import sys
from pathlib import Path

# Add the apps/api directory to the path
api_path = Path(__file__).parent / "apps" / "api"
sys.path.insert(0, str(api_path))

from dealbrain_api.tasks.cpu_metrics import recalculate_all_cpu_metrics

if __name__ == "__main__":
    print("Testing CPU metrics recalculation task...")
    print("=" * 60)

    try:
        result = recalculate_all_cpu_metrics()
        print("\nTask completed successfully!")
        print(f"Results: {result}")
    except Exception as e:
        print(f"\nTask failed with error: {e}")
        import traceback

        traceback.print_exc()
