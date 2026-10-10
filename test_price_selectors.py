"""Compatibility entry point for the standalone price selector diagnostic."""

if __name__ == "__main__":
    import runpy

    runpy.run_path("debug_price_selectors.py", run_name="__main__")
