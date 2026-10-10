"""Compatibility entry point for the standalone performance diagnostic."""

if __name__ == "__main__":
    import runpy

    runpy.run_path("scripts/performance_optimizations.py", run_name="__main__")
