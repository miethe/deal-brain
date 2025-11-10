#!/usr/bin/env python3
"""
update_cpus_from_passmark.py

Update Deal Brain's cpu.json using PassMark CSV dumps (licensed or sample).
- Input cpu.json schema: array of CPU objects (see example in repo).
- Input PassMark CSV: CPUModelSummary.csv (preferred) or DetailedBenchmarks_sample.csv-like.
- Output: updated cpu.json (in-place by default) and optional filtered cpu_top.json.

USAGE:
  python update_cpus_from_passmark.py --cpu-json cpu.json --passmark-csv CPUModelSummary.csv \
      --out cpu.updated.json --top-out cpu_top.json --min-rating 15000 --min-samples 50 \
      --rank-top-n 0

Notes:
- We do *not* scrape cpubenchmark.net. Use licensed CSV dumps from PassMark or other legally
  obtained datasets.
- Fuzzy matching is done with difflib; you can improve with rapidfuzz if available.

"""
import argparse
import csv
import io
import json
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from difflib import get_close_matches, SequenceMatcher

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'\(.*?\)', '', s)  # drop bracketed
    s = s.replace('cpu @', '').replace('@', '')
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    # normalize common vendor prefixes
    s = s.replace('intel(r) ', 'intel ').replace('amd ryzen(tm) ', 'amd ryzen ')
    s = s.replace(' with radeon graphics', '')
    return s

def load_passmark_csv(path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load PassMark CSV dump.
    Supported columns (CPUModelSummary.csv typical):
      CPU Name,Rating,Rank,Num Thread Execution units,Avg Speed,Stock Speed,Samples,Single Thread,maxTDP,URL
    Fallback supported (DetailedBenchmarks_sample.csv-like):
      CPU name, CPU Mark, Single Thread, ... (we'll try to infer)
    Returns dict keyed by normalized name slug.
    """
    text = path.read_text(errors='ignore', encoding='utf-8')
    # Attempt to sniff dialect safely
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0] + '\n' + text.splitlines()[1])
    except Exception:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = list(reader)
    norm = {}

    # Map a few possible header aliases
    def get(row, *names):
        for n in names:
            if n in row and row[n] not in (None, ''):
                return row[n]
        return None

    for r in rows:
        name = get(r, 'CPU Name', 'CPU name', 'cpu name', 'Name')
        if not name:
            # skip unknown lines
            continue
        rating = get(r, 'Rating', 'CPU Mark', 'CPUMark', 'CPUmark', 'CPUMARK')
        single = get(r, 'Single Thread', 'SingleThread', 'Single Thread Rating', 'SingleThreadRating')
        samples = get(r, 'Samples', 'Sample Count', 'Num Samples')
        rank = get(r, 'Rank', 'Ranking')
        tdp = get(r, 'maxTDP', 'TDP', 'Max TDP')
        url = get(r, 'URL', 'Link')

        # Coerce numerics
        def to_int(v):
            try:
                return int(float(str(v).replace(',', '').strip()))
            except Exception:
                return None
        rating_i = to_int(rating)
        single_i = to_int(single)
        samples_i = to_int(samples)
        rank_i = to_int(rank)
        tdp_i = to_int(tdp)

        entry = {
            'cpu_name_raw': name.strip(),
            'cpu_mark_multi': rating_i,
            'cpu_mark_single': single_i,
            'samples': samples_i,
            'rank': rank_i,
            'max_tdp_w': tdp_i,
            'source_url': url.strip() if isinstance(url, str) else None,
        }
        norm[slugify(name)] = entry
    return norm

def best_match(name: str, candidates: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], float]:
    """Return best matching key and score [0..1] for a given CPU name."""
    key = slugify(name)
    if key in candidates:
        return key, 1.0
    # try close matches with difflib
    all_keys = list(candidates.keys())
    close = get_close_matches(key, all_keys, n=1, cutoff=0.6)
    if close:
        k = close[0]
        score = SequenceMatcher(None, key, k).ratio()
        return k, score
    return None, 0.0

def update_cpu_json(cpu_json_path: Path, passmark_map: Dict[str, Dict[str, Any]],
                    out_path: Path, min_match: float = 0.72) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, float]]]:
    data = json.loads(cpu_json_path.read_text())
    updated = []
    misses = []
    for cpu in data:
        name = cpu.get('name') or cpu.get('cpu_name') or ''
        if not name:
            updated.append(cpu)
            continue
        key, score = best_match(name, passmark_map)
        if key and score >= min_match:
            p = passmark_map[key]
            # Only overwrite if values are present
            if p.get('cpu_mark_multi') is not None:
                cpu['cpu_mark_multi'] = p['cpu_mark_multi']
            if p.get('cpu_mark_single') is not None:
                cpu['cpu_mark_single'] = p['cpu_mark_single']
            # Populate tdp if missing and available
            if (cpu.get('tdp_w') in (None, 0) or 'tdp_w' not in cpu) and p.get('max_tdp_w') is not None:
                cpu['tdp_w'] = p['max_tdp_w']
            # Add attributes container if missing
            cpu.setdefault('attributes', {})
            if p.get('samples') is not None:
                cpu['attributes']['passmark_samples'] = p['samples']
            if p.get('rank') is not None:
                cpu['attributes']['passmark_rank'] = p['rank']
            if p.get('source_url'):
                cpu['attributes']['passmark_url'] = p['source_url']
        else:
            misses.append((name, key or '', score))
        updated.append(cpu)
    out_path.write_text(json.dumps(updated, indent=2))
    return updated, misses

def build_top_subset(passmark_map: Dict[str, Dict[str, Any]],
                     min_rating: int = 15000, min_samples: int = 20,
                     rank_top_n: int = 0, keep_mobile: bool = True) -> List[Dict[str, Any]]:
    """
    Create a bounded 'top CPUs' list based on rating/samples (and optionally rank).
    Heuristics: filter out obscure ES/engineering samples; keep consumer desktop & mobile.
    """
    def looks_like_mobile(name: str) -> bool:
        # heuristic for Intel mobile parts: U, P, H/HX; AMD: U/HS/H/HX; Apple M*
        n = name.upper()
        return any(tag in n for tag in [' U ', ' P ', ' H ', ' HX ', 'HS ']) or n.startswith('APPLE M')

    items = []
    for k, p in passmark_map.items():
        name = p['cpu_name_raw']
        rating = p.get('cpu_mark_multi') or 0
        samples = p.get('samples') or 0
        rank = p.get('rank') or 10**9

        # Basic filters
        if min_rating and (rating is None or rating < min_rating):
            continue
        if min_samples and (samples is None or samples < min_samples):
            continue
        if not keep_mobile and looks_like_mobile(name):
            continue

        items.append({
            'name': name,
            'manufacturer': 'Intel' if name.lower().startswith('intel') else ('AMD' if name.lower().startswith('amd') else 'Other'),
            'cpu_mark_multi': rating,
            'cpu_mark_single': p.get('cpu_mark_single'),
            'attributes': {
                'passmark_rank': rank,
                'passmark_samples': samples,
                'passmark_url': p.get('source_url'),
            }
        })
    # Apply rank cut if provided
    if rank_top_n and rank_top_n > 0:
        items = [x for x in items if x['attributes']['passmark_rank'] and x['attributes']['passmark_rank'] <= rank_top_n]
    # Sort by rating desc
    items.sort(key=lambda x: (x['cpu_mark_multi'] or 0), reverse=True)
    return items

def main():
    ap = argparse.ArgumentParser(description="Update Deal Brain cpu.json from PassMark CSV dump (no scraping).")
    ap.add_argument('--cpu-json', type=Path, required=True, help='Path to existing cpu.json to update')
    ap.add_argument('--passmark-csv', type=Path, required=True, help='Path to PassMark CSV (licensed dump or sample)')
    ap.add_argument('--out', type=Path, default=None, help='Output path for updated cpu.json (defaults to overwrite input)')
    ap.add_argument('--top-out', type=Path, default=None, help='Optional output for bounded top CPUs subset (cpu_top.json)')
    ap.add_argument('--min-match', type=float, default=0.72, help='Minimum fuzzy match ratio to accept')
    ap.add_argument('--min-rating', type=int, default=15000, help='Min CPU Mark for inclusion in top subset')
    ap.add_argument('--min-samples', type=int, default=20, help='Min sample count for inclusion in top subset')
    ap.add_argument('--rank-top-n', type=int, default=0, help='Keep only CPUs with rank <= N in top subset (0 to ignore)')
    ap.add_argument('--exclude-mobile', action='store_true', help='Exclude mobile parts in top subset')
    args = ap.parse_args()

    if not args.cpu_json.exists():
        print(f"CPU JSON not found: {args.cpu_json}", file=sys.stderr)
        sys.exit(2)
    if not args.passmark_csv.exists():
        print(f"PassMark CSV not found: {args.passmark_csv}", file=sys.stderr)
        sys.exit(2)

    passmap = load_passmark_csv(args.passmark_csv)
    out_path = args.out if args.out else args.cpu_json
    updated, misses = update_cpu_json(args.cpu_json, passmap, out_path, min_match=args.min_match)

    print(f"Updated {len(updated)} CPUs. Misses: {len(misses)}")
    if misses:
        print("Unmatched CPUs (name -> best_match, score):")
        for n, k, s in sorted(misses, key=lambda x: x[2]):
            print(f"  - {n} -> {k} ({s:.2f})")

    if args.top_out:
        top = build_top_subset(passmap,
                               min_rating=args.min_rating,
                               min_samples=args.min_samples,
                               rank_top_n=args.rank_top_n,
                               keep_mobile=not args.exclude_mobile)
        args.top_out.write_text(json.dumps(top, indent=2))
        print(f"Wrote top subset: {args.top_out} ({len(top)} CPUs)")

if __name__ == '__main__':
    main()
