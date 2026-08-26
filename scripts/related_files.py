#!/usr/bin/env python3
"""Single-lookup file map for a task's issue (issue #2409).

The pre-resolved-map mechanism the issue's acceptance section asks for:
one call that returns what a role session currently spends several
ad-hoc `grep`/`find` calls re-deriving — the issue's own docs tree, and
every code/test/spec file that already mentions the issue number, plus
optional keyword hits.

  python3 scripts/related_files.py <issue-number> [--keyword WORD ...] [--json]
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_ISSUE_NUM_RE = re.compile(r"^\d+$")


def _git(args: list[str], repo: Path = REPO) -> list[str]:
    out = subprocess.run(["git", "-C", str(repo)] + args,
                         capture_output=True, text=True, check=False).stdout
    return [l for l in out.splitlines() if l]


def docs_tree(issue: int, repo: Path = REPO) -> list[str]:
    """`git ls-files docs/issue-<n>` — the issue's own proposal/report tree."""
    return sorted(_git(["ls-files", f"docs/issue-{issue}"], repo))


def issue_mentions(issue: int, repo: Path = REPO) -> list[str]:
    """Files outside `docs/issue-<n>/` that already mention this issue —
    `issue-<n>`, `issue #<n>`, or `#<n>` — one `git grep` covering the
    three phrasings a manual search would otherwise run separately.
    `docs/issue-<n>/` itself is excluded in Python (not via a git
    pathspec) since exclude-magic pathspec globbing is a portability
    footgun this doesn't need."""
    prefix = f"docs/issue-{issue}/"
    hits = _git(["grep", "-l", "-I", "--extended-regexp",
                 "-e", rf"issue-{issue}\b",
                 "-e", rf"issue #{issue}\b",
                 "-e", rf"#{issue}\b"], repo)
    return sorted(h for h in hits if not h.startswith(prefix))


def keyword_hits(keywords: list[str], repo: Path = REPO) -> dict[str, list[str]]:
    """One `git grep -l -i` per keyword — still one call per distinct
    keyword the caller actually names, not per-directory/per-extension
    the way ad-hoc exploration usually fans out."""
    return {kw: sorted(_git(["grep", "-l", "-i", "-I", "--", kw], repo))
            for kw in keywords}


def build_manifest(issue: int, keywords: list[str] | None = None,
                   repo: Path = REPO) -> dict:
    return {
        "issue": issue,
        "docs_tree": docs_tree(issue, repo),
        "issue_mentions": issue_mentions(issue, repo),
        "keyword_hits": keyword_hits(keywords, repo) if keywords else {},
    }


def format_manifest(manifest: dict) -> str:
    issue = manifest["issue"]
    lines = [f"docs/issue-{issue}/ ({len(manifest['docs_tree'])} files):"]
    lines += [f"  {p}" for p in manifest["docs_tree"]] or ["  (none)"]
    mentions = manifest["issue_mentions"]
    lines.append(f"files outside docs/issue-{issue}/ mentioning this issue "
                 f"({len(mentions)}):")
    lines += [f"  {p}" for p in mentions] or ["  (none)"]
    for kw, files in manifest["keyword_hits"].items():
        lines.append(f"keyword {kw!r} ({len(files)}):")
        lines += [f"  {p}" for p in files] or ["  (none)"]
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("issue", help="issue number")
    ap.add_argument("--keyword", action="append", default=[],
                    help="additional keyword to grep for (repeatable)")
    ap.add_argument("--json", action="store_true")
    return ap


def main(argv=None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not _ISSUE_NUM_RE.match(args.issue):
        print(f"error: issue must be a bare number, got {args.issue!r}", file=sys.stderr)
        return 1
    manifest = build_manifest(int(args.issue), args.keyword)
    print(json.dumps(manifest, indent=2, ensure_ascii=False) if args.json
          else format_manifest(manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
