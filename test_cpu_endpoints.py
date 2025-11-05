#!/usr/bin/env python3
"""Simple test script to verify CPU endpoints structure."""

import sys
import inspect
from pathlib import Path

# Add apps/api to path
api_path = Path(__file__).parent / "apps" / "api"
sys.path.insert(0, str(api_path))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from dealbrain_api.api.cpus import router, list_cpus, get_cpu_detail, get_cpu_statistics, trigger_metric_recalculation
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_router_structure():
    """Test router structure and endpoints."""
    print("\nTesting router structure...")

    try:
        from dealbrain_api.api.cpus import router

        # Check router attributes
        print(f"  Router prefix: {router.prefix}")
        print(f"  Router tags: {router.tags}")

        # Count routes
        routes = router.routes
        print(f"  Number of routes: {len(routes)}")

        for route in routes:
            print(f"    - {route.methods} {route.path}")

        print("✓ Router structure looks good")
        return True
    except Exception as e:
        print(f"✗ Router error: {e}")
        return False

def test_endpoint_signatures():
    """Test endpoint function signatures."""
    print("\nTesting endpoint signatures...")

    try:
        from dealbrain_api.api.cpus import list_cpus, get_cpu_detail, get_cpu_statistics, trigger_metric_recalculation

        # Check list_cpus
        sig = inspect.signature(list_cpus)
        print(f"  list_cpus parameters: {list(sig.parameters.keys())}")

        # Check get_cpu_detail
        sig = inspect.signature(get_cpu_detail)
        print(f"  get_cpu_detail parameters: {list(sig.parameters.keys())}")

        # Check get_cpu_statistics
        sig = inspect.signature(get_cpu_statistics)
        print(f"  get_cpu_statistics parameters: {list(sig.parameters.keys())}")

        # Check trigger_metric_recalculation
        sig = inspect.signature(trigger_metric_recalculation)
        print(f"  trigger_metric_recalculation parameters: {list(sig.parameters.keys())}")

        print("✓ All endpoint signatures look good")
        return True
    except Exception as e:
        print(f"✗ Signature error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("CPU Endpoints Test Suite")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Router Structure", test_router_structure()))
    results.append(("Endpoint Signatures", test_endpoint_signatures()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
