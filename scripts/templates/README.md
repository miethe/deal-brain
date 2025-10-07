# Import Templates

These sample files pair with `scripts/import_entities.py` and outline the expected
schema for each supported entity. Copy one of the JSON or CSV variants to start a
new dataset and adjust the values as needed before running the importer.

Run the script from the repository root, using project-relative paths:

```bash
python scripts/import_entities.py cpu data/cpus.json
python scripts/import_entities.py listing scripts/templates/listing.csv --dry-run
```

Use `--dry-run` to validate a payload without touching the database. All files
are relative to the repository root; the script will reject inputs outside this
workspace.
