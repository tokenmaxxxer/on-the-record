#!/usr/bin/env python3
"""Agent-behavior efficiency metrics (issue #1504).

Computes four behavioral waste metrics over existing git-tracked ledgers:

  (a) re-check count per (role, issue, unchanged-subject-hash)
  (b) sessions ending with 0 commits vs. their role's expected deliverable
  (c) round-trip count (consults + phases + re-verifications + respawns)
      per landed change
  (d) wait/poll time attributable to sessions blocking on external state

Each metric has a pure "core" function operating on already-parsed ledger
entries (unit-testable without a git checkout) and an "extract_*" function
that builds those entries from this repo's git history / `gh` CLI for a
given date range.

  python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16 [--json]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Roles whose phase-2 delivery is expected to produce at least one commit.
# Consult/observation-only roles routinely end a turn with 0 commits by
# design (e.g. a validity consult that only advises), so they are not
# flagged by metric (b).
EXPECTED_COMMIT_SKILLS = {"implementation", "coding"}

RECHECK_RE = re.compile(r"(\d+)(?:st|nd|rd|th)\s+re-check|재확인", re.I)
SKILL_DIR_RE = re.compile(r"reports/([a-z][a-z0-9_-]*)/deviation-log\.md$")
ISSUE_RE = re.compile(r"docs/issue-(\d+)/")


# ---------------------------------------------------------------------------
# (a) re-check count per (role, issue, unchanged-subject-hash)
# ---------------------------------------------------------------------------

def recheck_counts(entries: list[dict]) -> dict[tuple, int]:
    """entries: [{"skill":..., "issue":..., "subject_hash":...}, ...],
    one entry per re-check event. Returns a count per (role, issue,
    subject_hash) key — the number of times that unchanged subject was
    re-checked."""
    counts: Counter = Counter()
    for e in entries:
        counts[(e["skill"], e["issue"], e["subject_hash"])] += 1
    return dict(counts)


def _subject_hash(line: str) -> str:
    """Collapse a re-check line to its blocker identity by stripping the
    leading ISO timestamp and the re-check ordinal, so consecutive
    re-checks of the *same* unresolved blocker hash identically."""
    stripped = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:]+Z?\s*[|]?\s*", "", line)
    stripped = re.sub(r"\(\d+(?:st|nd|rd|th)\s+re-check\)", "", stripped, flags=re.I)
    # Drop volatile per-turn detail (commit shas, dates, bare numbers) so
    # repeated re-checks of the *same* blocker collapse to one hash even
    # when each turn cites a different sha/timestamp for its evidence.
    stripped = re.sub(r"\b[0-9a-f]{7,40}\b", "", stripped)
    stripped = re.sub(r"\d{4}-\d{2}-\d{2}T[\d:]+Z?", "", stripped)
    stripped = re.sub(r"\d+", "", stripped)
    return hashlib.sha256(stripped.strip().encode()).hexdigest()[:12]


def extract_recheck_entries(repo: Path = REPO) -> list[dict]:
    entries = []
    for path in sorted(repo.glob("docs/issue-*/reports/**/deviation-log.md")):
        rel = str(path.relative_to(repo))
        issue_m = ISSUE_RE.search(rel)
        if not issue_m:
            continue
        issue = issue_m.group(1)
        skill_m = SKILL_DIR_RE.search(rel)
        skill = skill_m.group(1) if skill_m else "unknown"
        text = path.read_text(errors="replace")
        for line in text.splitlines():
            if RECHECK_RE.search(line) and "re-check" in line.lower() or "재확인" in line:
                entries.append({
                    "skill": skill, "issue": issue,
                    "subject_hash": _subject_hash(line),
                    "source": rel, "line": line.strip(),
                })
    return entries


# ---------------------------------------------------------------------------
# (b) sessions ending with 0 commits vs. role's expected deliverable
# ---------------------------------------------------------------------------

def zero_commit_sessions(sessions: list[dict]) -> list[dict]:
    """sessions: [{"skill":..., "issue":..., "commits": int, ...}, ...].
    Flags a session iff commits == 0 AND its role is expected to deliver a
    commit (EXPECTED_COMMIT_ROLES). Non-implementation (e.g. consult)
    sessions with 0 commits are not flagged."""
    return [s for s in sessions
            if s.get("commits", 0) == 0 and s.get("skill") in EXPECTED_COMMIT_SKILLS]


SUBJECT_TRAILER_RE = re.compile(r"^Subject:\s*issue-(\d+)\s*$", re.M)


def extract_sessions(repo: Path, since: str, until: str) -> list[dict]:
    """One session per (issue, role) that landed an implementation.md
    record in the window. `commits` counts non-doc (code/config) files
    changed across that issue's `Subject: issue-<n>` trailer-carrying
    commits in the window — the 0-commit-deliverable proxy, since no
    runs/roster session history is git-tracked in this checkout (survey
    finding). A record-only commit (record landed, no code changed) is
    exactly the pattern metric (b) is meant to flag for an implementation
    role."""
    log = subprocess.run(
        ["git", "-C", str(repo), "log", f"--since={since}", f"--until={until}",
         "--format=COMMIT|%H", "--name-only"],
        capture_output=True, text=True, check=True).stdout
    commits = []
    cur_sha = None
    cur_files: list[str] = []
    for line in log.splitlines():
        if line.startswith("COMMIT|"):
            if cur_sha:
                commits.append((cur_sha, cur_files))
            cur_sha = line.split("|", 1)[1]
            cur_files = []
        elif line.strip():
            cur_files.append(line)
    if cur_sha:
        commits.append((cur_sha, cur_files))

    sessions: dict = defaultdict(lambda: {"commits": 0, "has_implementation_record": False})
    for sha, files in commits:
        msg = subprocess.run(
            ["git", "-C", str(repo), "show", "-s", "--format=%B", sha],
            capture_output=True, text=True, check=True).stdout
        m = SUBJECT_TRAILER_RE.search(msg)
        if not m:
            continue
        issue = m.group(1)
        key = (issue, "implementation")
        sessions[key]["skill"] = "implementation"
        sessions[key]["issue"] = issue
        for f in files:
            if f.startswith(f"docs/issue-{issue}/reports/implementation.md"):
                sessions[key]["has_implementation_record"] = True
            elif not f.startswith("docs/"):
                sessions[key]["commits"] += 1
    return [dict(v, key=k) for k, v in sessions.items()
            if v.get("has_implementation_record")]


# ---------------------------------------------------------------------------
# (c) round-trip count per landed change
# ---------------------------------------------------------------------------

def round_trip_counts(artifact_paths: list[str]) -> dict[str, int]:
    """artifact_paths: repo-relative paths under docs/issue-<n>/{proposals,
    reports}/. Returns {issue: count} — one round-trip unit per artifact
    file (a proposal, a phase report, a re-verification record each count
    as one round-trip)."""
    counts: Counter = Counter()
    for p in artifact_paths:
        m = ISSUE_RE.search(p)
        if m:
            counts[m.group(1)] += 1
    return dict(counts)


def extract_round_trip_artifacts(repo: Path) -> list[str]:
    paths = []
    for sub in ("proposals", "reports"):
        for p in repo.glob(f"docs/issue-*/{sub}/**/*.md"):
            paths.append(str(p.relative_to(repo)))
    return paths


def extract_landed_issues(since: str, until: str) -> list[str]:
    """Issue numbers referenced by PR titles/bodies for PRs merged in the
    window, via `gh pr list`. Best-effort: returns [] if `gh` is
    unavailable (e.g. offline test environment)."""
    try:
        out = subprocess.run(
            ["gh", "pr", "list", "--state", "merged", "--search",
             f"merged:{since}..{until}", "--limit", "200",
             "--json", "number,title,body"],
            capture_output=True, text=True, check=True).stdout
        prs = json.loads(out)
    except Exception:
        return []
    issues = set()
    for pr in prs:
        for m in re.finditer(r"issue-(\d+)|#(\d+)", pr.get("title", "") + " " + (pr.get("body") or "")):
            issues.add(m.group(1) or m.group(2))
    return sorted(issues)


# ---------------------------------------------------------------------------
# (d) wait/poll time attributable to sessions blocking on external state
# ---------------------------------------------------------------------------

def wait_poll_time(entries: list[dict]) -> dict[str, float]:
    """entries: [{"issue":..., "seconds": float}, ...] — pre-extracted wait
    durations. Returns total seconds per issue. Kept as a pure aggregator;
    see extract note below on why no repo extraction is implemented."""
    totals: defaultdict = defaultdict(float)
    for e in entries:
        totals[e["issue"]] += e.get("seconds", 0.0)
    return dict(totals)


def extract_wait_poll_entries(repo: Path = REPO) -> list[dict]:
    """No runs/ or roster heartbeat history is git-tracked in this
    checkout (survey finding) — wait/poll durations are runtime-only and
    not derivable from committed records. Always returns []; callers
    should report metric (d) as not derivable rather than 0."""
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def compute(repo: Path, since: str, until: str) -> dict:
    recheck_entries = extract_recheck_entries(repo)
    a = recheck_counts(recheck_entries)

    sessions = extract_sessions(repo, since, until)
    b = zero_commit_sessions(sessions)

    artifacts = extract_round_trip_artifacts(repo)
    c_all = round_trip_counts(artifacts)
    landed = extract_landed_issues(since, until)
    c = {issue: c_all.get(issue, 0) for issue in landed} if landed else c_all

    wait_entries = extract_wait_poll_entries(repo)
    d = wait_poll_time(wait_entries)
    d_derivable = bool(wait_entries) or bool(list(repo.glob("runs/**/*")))

    return {
        "since": since, "until": until,
        "a_recheck_counts": {"|".join(k): v for k, v in a.items()},
        "b_zero_commit_sessions": b,
        "c_round_trips_per_landed_issue": c,
        "d_wait_poll_seconds": d if d_derivable else None,
        "d_note": None if d_derivable else
            "not derivable: no runs/ or roster heartbeat history is git-tracked in this checkout",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--since", default="2026-08-13")
    ap.add_argument("--until", default="2026-08-16")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = compute(Path(args.repo), args.since, args.until)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"(a) re-check keys with count>1: "
              f"{sum(1 for v in result['a_recheck_counts'].values() if v > 1)}")
        print(f"(b) zero-commit implementation sessions: {len(result['b_zero_commit_sessions'])}")
        print(f"(c) issues with round-trip artifacts: {len(result['c_round_trips_per_landed_issue'])}")
        print(f"(d) wait/poll seconds: {result['d_wait_poll_seconds']} "
              f"({result['d_note'] or 'derived from git-tracked records'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
