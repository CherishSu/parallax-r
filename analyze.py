"""Analyze saved results without contacting a model or modifying the source run."""
import argparse
import hashlib
import json
from pathlib import Path
from parallax.stats import analyze_run


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('results', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--draws', type=int, default=10000)
    p.add_argument('--seed', type=int, default=20261004)
    args = p.parse_args()
    if args.out.resolve() == args.results.resolve() or args.out.exists():
        p.error('Choose a new output file; existing files are not overwritten.')
    raw = args.results.read_bytes()
    result = analyze_run(json.loads(raw), args.draws, args.seed)
    result['source_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Saved {args.out}; no model calls made.')


if __name__ == '__main__':
    main()
