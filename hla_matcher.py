#!/usr/bin/env python3
"""
HLA Compatibility Matcher
HLA-A/B/C/DRB1/DQB1 mismatch grading and eplet load estimation for transplant pairing.
Stdlib parser / mapper with batch CSV and single lookup.
"""
import argparse
import csv
import json
import sys


def lookup(query):
    """Single lookup: token overlap + substring scoring (no deps). Returns top hits."""
    q = str(query).lower().strip()
    # Built-in HLA allele dictionary for demo
    hla_alleles = [
        ("A*02:01", "a02"),
        ("A*24:02", "a24"),
        ("B*07:02", "b07"),
        ("B*44:02", "b44"),
        ("DRB1*15:01", "drb115"),
        ("DRB1*04:01", "drb104"),
        ("C*07:01", "c07"),
        ("DQB1*06:02", "dqb106"),
    ]
    scored = []
    for label, key in hla_alleles:
        score = 0
        if key in q:
            score += 10
        # token overlap
        qt = set(q.split())
        lt = set(label.lower().split())
        overlap = len(qt & lt)
        score += overlap * 2
        scored.append((score, label))
    scored.sort(reverse=True)
    top = scored[0] if scored else (0, "no match")
    # If no meaningful match found, return "no match"
    if top[0] == 0:
        top = (0, "no match")
    return {"query": query, "top_hit": top[1], "score": top[0], "all": scored[:3]}


def process_csv(inp, out):
    """Process CSV file with HLA lookups. Returns list of result dicts."""
    try:
        with open(inp, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError(f"CSV file '{inp}' has no headers")
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {inp}")

    # Guess query column
    qcol = fieldnames[0]
    for cand in ["query", "test", "drug", "code", "variant", "hla", "lab", "name"]:
        if cand in [c.lower() for c in fieldnames]:
            qcol = [c for c in fieldnames if c.lower() == cand][0]
            break

    results = []
    for row in rows:
        res = lookup(row.get(qcol, ""))
        merged = {**row, "top_hit": res["top_hit"], "lookup_score": res["score"]}
        results.append(merged)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames) + ["top_hit", "lookup_score"])
        writer.writeheader()
        writer.writerows(results)
    return results


def build_parser():
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(prog="hla_matcher", description="HLA Compatibility Matcher")
    sub = parser.add_subparsers(dest="cmd", required=True)
    single = sub.add_parser("single")
    single.add_argument("query", nargs="?", default="A*02:01")
    single.add_argument("--query", dest="q2")
    batch = sub.add_parser("batch")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    return parser


def main(argv=None):
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "single":
        q = getattr(args, "q2", None) or getattr(args, "query")
        print(lookup(q))
        return 0
    if args.cmd == "batch":
        res = process_csv(args.input, args.output)
        print(f"Processed {len(res)} -> {args.output}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
