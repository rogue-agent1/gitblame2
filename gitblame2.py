#!/usr/bin/env python3
"""gitblame2 - Git blame summary and author heatmap.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import subprocess
import re
from collections import Counter


def cmd_summary(args):
    """Author summary for a file."""
    try:
        out = subprocess.check_output(["git", "blame", "--porcelain", args.file],
                                       text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"  Error: can't blame {args.file}"); return 1
    authors = Counter()
    for line in out.split("\n"):
        if line.startswith("author "):
            authors[line[7:]] += 1
    total = sum(authors.values())
    for author, count in authors.most_common():
        pct = count / total * 100
        bar = "█" * int(pct / 3)
        print(f"  {count:5d} ({pct:4.1f}%)  {bar}  {author}")
    print(f"\n  {total} lines, {len(authors)} authors")


def cmd_hot(args):
    """Find most-changed files (hotspots)."""
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={args.since}", "--pretty=format:", "--name-only"],
            text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("  Error running git log"); return 1
    files = Counter(f for f in out.strip().split("\n") if f.strip())
    for f, count in files.most_common(args.limit):
        bar = "█" * min(count, 20)
        print(f"  {count:5d}  {bar}  {f}")


def cmd_age(args):
    """Show file ages (oldest/newest lines)."""
    try:
        out = subprocess.check_output(["git", "blame", "--porcelain", args.file],
                                       text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"  Error: can't blame {args.file}"); return 1
    timestamps = []
    for line in out.split("\n"):
        if line.startswith("author-time "):
            timestamps.append(int(line.split()[1]))
    if not timestamps:
        print("  No data"); return
    from datetime import datetime
    oldest = datetime.fromtimestamp(min(timestamps))
    newest = datetime.fromtimestamp(max(timestamps))
    print(f"  Oldest line: {oldest.strftime('%Y-%m-%d')}")
    print(f"  Newest line: {newest.strftime('%Y-%m-%d')}")
    print(f"  Span: {(newest - oldest).days} days")
    print(f"  Lines: {len(timestamps)}")


def main():
    p = argparse.ArgumentParser(prog="gitblame2", description="Git blame analytics")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("summary", aliases=["s"], help="Author summary"); s.add_argument("file")
    s = sub.add_parser("hot", help="File hotspots")
    s.add_argument("--since", default="30 days ago"); s.add_argument("-n", "--limit", type=int, default=20)
    s = sub.add_parser("age", help="Line ages"); s.add_argument("file")
    args = p.parse_args()
    if not args.cmd: p.print_help(); return 1
    cmds = {"summary": cmd_summary, "s": cmd_summary, "hot": cmd_hot, "age": cmd_age}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
