#!/usr/bin/env python3
"""
Analyze performance test results and generate recommendations.

Usage:
    poetry run python scripts/performance/analyze_results.py performance-results.json
"""

import argparse
import json
import sys
from pathlib import Path


def load_results(file_path: str) -> dict:
    """Load performance test results from JSON."""
    with open(file_path, "r") as f:
        return json.load(f)


def analyze_results(results: dict) -> dict:
    """Analyze results and generate insights."""
    analysis = {
        "summary": results.get("summary", {}),
        "critical_issues": [],
        "warnings": [],
        "optimizations": [],
        "passed_tests": [],
    }

    for result in results.get("results", []):
        if not result["passed"]:
            # Failed test - critical issue
            p95 = result["p95_ms"]
            target = result["target_ms"]
            overage_pct = ((p95 - target) / target) * 100

            analysis["critical_issues"].append(
                {
                    "scenario": result["scenario"],
                    "operation": result["operation"],
                    "entity_type": result["entity_type"],
                    "p95_ms": p95,
                    "target_ms": target,
                    "overage_pct": overage_pct,
                    "recommendation": get_recommendation(result),
                }
            )
        elif result["p95_ms"] > result["target_ms"] * 0.75:
            # Within target but getting close - warning
            analysis["warnings"].append(
                {
                    "scenario": result["scenario"],
                    "p95_ms": result["p95_ms"],
                    "target_ms": result["target_ms"],
                    "margin_pct": ((result["target_ms"] - result["p95_ms"]) / result["target_ms"])
                    * 100,
                }
            )
        else:
            # Passed with good margin
            analysis["passed_tests"].append(
                {
                    "scenario": result["scenario"],
                    "p95_ms": result["p95_ms"],
                    "target_ms": result["target_ms"],
                }
            )

        # Check for high variability
        if result["stddev_ms"] > result["mean_ms"] * 0.3:
            analysis["optimizations"].append(
                {
                    "scenario": result["scenario"],
                    "type": "high_variability",
                    "stddev_ms": result["stddev_ms"],
                    "mean_ms": result["mean_ms"],
                    "recommendation": "High response time variability detected. Consider connection pooling, caching, or reducing external dependencies.",
                }
            )

    return analysis


def get_recommendation(result: dict) -> str:
    """Generate optimization recommendation based on result."""
    operation = result["operation"]
    entity_type = result["entity_type"]

    recommendations = {
        "PATCH": f"Optimize {entity_type} PATCH: Add database index, reduce validation overhead, or cache frequently accessed data.",
        "PUT": f"Optimize {entity_type} PUT: Review transaction size, add indexes, or implement optimistic locking.",
        "DELETE": f"Optimize {entity_type} DELETE: Add index on foreign keys, use COUNT(*) with LIMIT 1 for existence check.",
        "LIST": f"Optimize {entity_type} LIST: Add pagination, implement query result caching, or use materialized views.",
        "DETAIL": f"Optimize {entity_type} DETAIL: Use eager loading (selectinload), implement caching, or denormalize data.",
    }

    return recommendations.get(operation, "Review database queries and add appropriate indexes.")


def print_analysis(analysis: dict):
    """Print analysis results."""
    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)

    # Summary
    summary = analysis["summary"]
    print(f"\nSummary:")
    print(f"  Total Tests: {summary.get('total_tests', 0)}")
    print(f"  Passed: {summary.get('passed', 0)}")
    print(f"  Failed: {summary.get('failed', 0)}")

    # Critical Issues
    if analysis["critical_issues"]:
        print("\n" + "=" * 80)
        print("❌ CRITICAL ISSUES (Tests Failed)")
        print("=" * 80)

        for issue in analysis["critical_issues"]:
            print(f"\n{issue['scenario']}")
            print(f"  Operation: {issue['operation']} {issue['entity_type']}")
            print(f"  P95: {issue['p95_ms']:.1f}ms (target: {issue['target_ms']:.0f}ms)")
            print(f"  Overage: {issue['overage_pct']:.1f}%")
            print(f"  ➜ {issue['recommendation']}")

    # Warnings
    if analysis["warnings"]:
        print("\n" + "=" * 80)
        print("⚠️  WARNINGS (Approaching Limits)")
        print("=" * 80)

        for warning in analysis["warnings"]:
            print(f"\n{warning['scenario']}")
            print(f"  P95: {warning['p95_ms']:.1f}ms (target: {warning['target_ms']:.0f}ms)")
            print(f"  Safety margin: {warning['margin_pct']:.1f}%")
            print(f"  ➜ Monitor this test - approaching threshold")

    # Optimization Opportunities
    if analysis["optimizations"]:
        print("\n" + "=" * 80)
        print("💡 OPTIMIZATION OPPORTUNITIES")
        print("=" * 80)

        for opt in analysis["optimizations"]:
            print(f"\n{opt['scenario']}")
            if opt["type"] == "high_variability":
                print(f"  Issue: High response time variability")
                print(f"  StdDev: {opt['stddev_ms']:.1f}ms (Mean: {opt['mean_ms']:.1f}ms)")
            print(f"  ➜ {opt['recommendation']}")

    # Passed Tests
    if analysis["passed_tests"]:
        print("\n" + "=" * 80)
        print("✅ PASSED TESTS")
        print("=" * 80)

        for test in analysis["passed_tests"]:
            margin = test["target_ms"] - test["p95_ms"]
            margin_pct = (margin / test["target_ms"]) * 100
            print(
                f"  {test['scenario']:50s} P95: {test['p95_ms']:7.1f}ms (margin: {margin_pct:5.1f}%)"
            )

    print("\n" + "=" * 80)


def generate_recommendations_summary(analysis: dict):
    """Generate high-level recommendations."""
    print("\n" + "=" * 80)
    print("RECOMMENDED ACTIONS")
    print("=" * 80)

    if analysis["critical_issues"]:
        print("\n🔴 HIGH PRIORITY:")
        for i, issue in enumerate(analysis["critical_issues"], 1):
            print(f"  {i}. Fix {issue['scenario']}: {issue['recommendation']}")

    if analysis["warnings"]:
        print("\n🟡 MEDIUM PRIORITY:")
        for i, warning in enumerate(analysis["warnings"], 1):
            print(f"  {i}. Monitor {warning['scenario']}: Approaching performance limits")

    if analysis["optimizations"]:
        print("\n🟢 LOW PRIORITY (Optimizations):")
        for i, opt in enumerate(analysis["optimizations"], 1):
            print(f"  {i}. {opt['scenario']}: {opt['recommendation']}")

    if not analysis["critical_issues"] and not analysis["warnings"]:
        print("\n✅ No critical issues or warnings detected!")
        print("   All performance targets are met with healthy margins.")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze performance test results and generate recommendations"
    )
    parser.add_argument(
        "results_file",
        help="Path to performance results JSON file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output analysis as JSON",
    )

    args = parser.parse_args()

    # Load results
    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Error: Results file not found: {results_path}")
        sys.exit(1)

    results = load_results(args.results_file)

    # Analyze
    analysis = analyze_results(results)

    # Output
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print_analysis(analysis)
        generate_recommendations_summary(analysis)


if __name__ == "__main__":
    main()
