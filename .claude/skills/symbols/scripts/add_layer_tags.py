#!/usr/bin/env python3
"""
Add architectural layer tags to all symbols based on file path.

Usage:
    python3 add_layer_tags.py --input symbols-api.json --output symbols-api-tagged.json
    python3 add_layer_tags.py --all  # Process all symbol files
"""

import json
import argparse
import sys
from pathlib import Path

# Path pattern to layer mapping
LAYER_MAPPING = {
    # Routers - HTTP entry points
    'app/api/': 'router',
    'app/api/endpoints/': 'router',

    # Services - Business logic
    'app/services/': 'service',

    # Repositories - Data access
    'app/repositories/': 'repository',

    # Schemas - DTOs and serialization
    'app/schemas/': 'schema',

    # Models - ORM definitions
    'app/models/': 'model',
    'db/models/': 'model',

    # Core - Configuration and utilities
    'app/core/': 'core',
    'app/db/': 'core',
    'app/utils/': 'core',
    'auth/': 'auth',

    # Middleware - Request processing
    'app/middleware/': 'middleware',

    # Observability
    'app/observability/': 'observability',
    'app/monitoring/': 'observability',

    # Frontend
    'components/': 'component',
    'hooks/': 'hook',
    'pages/': 'page',
    'lib/': 'util',
    'utils/': 'util',

    # Tests
    'test': 'test',
    '__test': 'test',
    'tests/': 'test',
    '.test.': 'test',
    '.spec.': 'test',
}

def get_layer(path: str) -> str:
    """Determine layer from file path."""
    path_lower = path.lower()

    # Check test patterns first (highest priority)
    for pattern in ['__test', '.test.', '.spec.', 'tests/', 'test/']:
        if pattern in path_lower:
            return 'test'

    # Check other patterns
    for pattern, layer in LAYER_MAPPING.items():
        if pattern.lower() in path_lower:
            return layer

    # Default based on directory
    if 'services' in path_lower:
        return 'service'
    if 'api' in path_lower:
        return 'router'
    if 'models' in path_lower:
        return 'model'

    return 'other'

def add_layer_to_symbols(data: dict) -> dict:
    """Add layer field to all symbols in the structure."""
    if 'modules' in data:
        # Structure: modules with nested symbols
        for module in data.get('modules', []):
            path = module.get('path', '')
            layer = get_layer(path)
            for symbol in module.get('symbols', []):
                if 'layer' not in symbol:
                    symbol['layer'] = layer
    elif 'symbols' in data:
        # Structure: flat symbols array
        for symbol in data.get('symbols', []):
            path = symbol.get('path', '')
            layer = get_layer(path)
            if 'layer' not in symbol:
                symbol['layer'] = layer

    return data

def process_file(input_path: str, output_path: str = None) -> tuple[int, int]:
    """
    Process a single symbol file and add layer tags.

    Returns: (total_symbols, symbols_with_new_tags)
    """
    if output_path is None:
        output_path = input_path.replace('.json', '-tagged.json')

    print(f"Processing: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Count before
    if 'modules' in data:
        total = sum(len(m.get('symbols', [])) for m in data.get('modules', []))
    else:
        total = len(data.get('symbols', []))

    # Add layer tags
    data = add_layer_to_symbols(data)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  ✓ Processed {total} symbols")
    print(f"  ✓ Written to: {output_path}")

    return total, total  # Simplified for Phase 1

def main():
    parser = argparse.ArgumentParser(description='Add architectural layer tags to symbols')
    parser.add_argument('--input', help='Input symbol file')
    parser.add_argument('--output', help='Output symbol file (default: input-tagged.json)')
    parser.add_argument('--all', action='store_true', help='Process all symbol files')
    parser.add_argument('--inplace', action='store_true', help='Overwrite input file')

    args = parser.parse_args()

    symbol_files = [
        'ai/symbols-api.json',
        'ai/symbols-api-tests.json',
        'ai/symbols-ui.json',
        'ai/symbols-ui-tests.json',
        'ai/symbols-web.json',
    ]

    if args.all:
        print("Processing all symbol files...\n")
        total_count = 0
        for file in symbol_files:
            file_path = Path(file)
            if file_path.exists():
                count, _ = process_file(
                    str(file_path),
                    str(file_path) if args.inplace else None
                )
                total_count += count
                print()
        print(f"Total symbols processed: {total_count}")
    elif args.input:
        process_file(args.input, args.output)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
