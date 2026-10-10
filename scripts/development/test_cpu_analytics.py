"""Compatibility entry point for the standalone CPU analytics diagnostic."""

if __name__ == "__main__":
    import runpy

    runpy.run_path("scripts/development/cpu_analytics_diagnostic.py", run_name="__main__")
