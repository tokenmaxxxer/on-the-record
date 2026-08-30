"""issue-1588 — patrol board C1: one living GitHub issue per active role,
edited in place from `.on-the-record/findings/queue.jsonl` (issue #1582
schema). Renovate dependencyDashboard pattern: create once, edit
thereafter, never re-create.

Rendering is pure functions over in-memory queue/board state; the
`gh`-calling shell (ETag-conditional reads, serialized batched writes,
daily write budget) is a thin imperative layer around them, mirroring
`gates/closure_sweep.py`'s `_conditional_issue_list` pattern and
`spawn._split_gh_api_i_output`.

NO issue creation for individual findings, NO spawn, NO checkbox
interpretation — that is issue #1589 (C2).

  python3 gates/patrol_board.py run <repo-root> <role> [--dry-run] [--queue PATH]
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import patrol_queue  # noqa: E402

LABEL_BOARD = "patrol-board"
DEFAULT_DAILY_WRITE_BUDGET = 20

PENDING_HEADING = "## Pending Approval"
APPROVED_HEADING = "## Approved / In Progress"
CLOSED_HEADING = "## Recently Closed"
SECTION_HEADINGS = (PENDING_HEADING, APPROVED_HEADING, CLOSED_HEADING)

_CHECKBOX_LINE = re.compile(r"^- \[( |x)\] `([0-9a-f]+)` (.*)$")
_SEEN_SUFFIX = re.compile(r" \(seen (\d+)x\)$")


# ---------------------------------------------------------------------------
# Pure rendering / selection functions
# ---------------------------------------------------------------------------

def select_board_entries(queue: list[dict], skill: str) -> list[dict]:
    """Diff-lane, status=open, validated entries scoped to `role`. A queue
    entry belongs to a role's board when the judge transport authored it for
    that role — `scanner_id == "judge:<role>"` (spawn.py judge_cmd's enqueue
    shape) — or, for mechanical scanners with no authoring role, when its
    `path` starts with `roles/<role>/` or `<role>/` (issue #1582's
    subject-path convention). `role == ""` selects everything (whole-repo
    board)."""
    out = []
    for entry in queue:
        if entry.get("lane") != "diff" or entry.get("status") != "open":
            continue
        if skill:
            by_scanner = entry.get("scanner_id") == f"judge:{skill}"
            by_path = (entry["path"].startswith(f"skills/{skill}/")
                       or entry["path"].startswith(f"{skill}/"))
            if not (by_scanner or by_path):
                continue
        out.append(entry)
    return out


def _finding_line(entry: dict, checked: bool = False) -> str:
    fp_prefix = entry["fingerprint"][:12]
    mark = "x" if checked else " "
    sev = entry.get("severity", "unspecified")
    loc = f"{entry['path']}@{entry.get('last_seen', '')}"
    excerpt = entry["excerpt"].strip().replace("\n", " ")
    if len(excerpt) > 160:
        excerpt = excerpt[:157] + "..."
    return (f"- [{mark}] `{fp_prefix}` {entry['finding_class']} "
            f"{loc} ({sev}): {excerpt}")


def render_board_body(pending: list[dict], approved_lines: list[str],
                       closed_lines: list[str]) -> str:
    """Render the three-section board body. `pending` is a list of queue
    entries (rendered fresh each run); `approved_lines`/`closed_lines`
    are already-rendered lines carried over from the prior board body
    (dedup/absence-close already applied by the caller)."""
    lines = [PENDING_HEADING, ""]
    if pending:
        lines.extend(_finding_line(e) for e in pending)
    else:
        lines.append("_none_")
    lines += ["", APPROVED_HEADING, ""]
    lines.extend(approved_lines if approved_lines else ["_none_"])
    lines += ["", CLOSED_HEADING, ""]
    lines.extend(closed_lines if closed_lines else ["_none_"])
    return "\n".join(lines) + "\n"


def parse_board_body(body: str) -> dict[str, list[str]]:
    """Split a rendered board body back into {heading: [content lines]},
    tolerant of a body with no recognized headings (empty board)."""
    sections: dict[str, list[str]] = {h: [] for h in SECTION_HEADINGS}
    current = None
    for line in body.splitlines():
        if line.strip() in SECTION_HEADINGS:
            current = line.strip()
            continue
        if current is not None:
            if line.strip() and line.strip() != "_none_":
                sections[current].append(line)
    return sections


def _line_fingerprint(line: str) -> str | None:
    m = _CHECKBOX_LINE.match(line)
    return m.group(2) if m else None


def dedup_fingerprints(existing_lines: list[str], new_entries: list[dict]
                        ) -> tuple[list[str], list[dict]]:
    """A fingerprint already present anywhere in `existing_lines` is never
    re-added as a new line. Its existing line's `(seen Nx)` counter is
    bumped only when the fresh render for that fingerprint actually
    differs from the stored line (a genuine re-detection — e.g. the
    queue's `last_seen` moved) — an unchanged queue between two runs
    must reproduce byte-identical output, so a same-content re-render
    never bumps. Returns (updated existing_lines, entries that are
    genuinely new). Order of `existing_lines` is preserved; bumped lines
    are updated in place."""
    existing_fps = {fp: i for i, line in enumerate(existing_lines)
                     if (fp := _line_fingerprint(line))}
    fresh = []
    updated = list(existing_lines)
    for entry in new_entries:
        fp = entry["fingerprint"][:12]
        if fp in existing_fps:
            idx = existing_fps[fp]
            line = updated[idx]
            m = _SEEN_SUFFIX.search(line)
            stored_base = line[:m.start()] if m else line
            candidate = _finding_line(entry)
            if candidate == stored_base:
                continue
            count = int(m.group(1)) + 1 if m else 2
            updated[idx] = f"{candidate} (seen {count}x)"
        else:
            fresh.append(entry)
    return updated, fresh


def diff_board(prior_pending_lines: list[str], new_pending_fingerprints: set[str]
               ) -> tuple[list[str], list[str]]:
    """Absence-close: any prior Pending-section line whose fingerprint is
    not in `new_pending_fingerprints` this run moves to Recently Closed.
    Returns (still_pending_lines, newly_closed_lines)."""
    still_pending, newly_closed = [], []
    for line in prior_pending_lines:
        fp = _line_fingerprint(line)
        if fp is not None and fp not in new_pending_fingerprints:
            newly_closed.append(line.replace("[ ]", "[x]", 1)
                                 if line.startswith("- [ ]") else line)
        else:
            still_pending.append(line)
    return still_pending, newly_closed


def build_next_body(prior_body: str | None, skill: str, queue: list[dict]) -> str:
    """End-to-end pure render: prior board body (None on first run) +
    current queue -> next board body. Combines select/dedup/absence-close
    without any I/O."""
    pending_entries = select_board_entries(queue, skill)
    sections = parse_board_body(prior_body) if prior_body else {h: [] for h in SECTION_HEADINGS}

    prior_pending = sections[PENDING_HEADING]
    kept_pending, fresh_entries = dedup_fingerprints(prior_pending, pending_entries)

    new_fps = {e["fingerprint"][:12] for e in pending_entries}
    still_pending, newly_closed = diff_board(kept_pending, new_fps)

    fresh_lines = [_finding_line(e) for e in fresh_entries]
    final_pending_lines = still_pending + fresh_lines

    closed_lines = newly_closed + sections[CLOSED_HEADING]
    approved_lines = sections[APPROVED_HEADING]

    return _render_from_lines(final_pending_lines, approved_lines, closed_lines)


def _render_from_lines(pending_lines: list[str], approved_lines: list[str],
                        closed_lines: list[str]) -> str:
    lines = [PENDING_HEADING, ""]
    lines.extend(pending_lines if pending_lines else ["_none_"])
    lines += ["", APPROVED_HEADING, ""]
    lines.extend(approved_lines if approved_lines else ["_none_"])
    lines += ["", CLOSED_HEADING, ""]
    lines.extend(closed_lines if closed_lines else ["_none_"])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Imperative shell — gh reads (ETag conditional) and writes (budgeted,
# serialized, batched to one edit per role per run)
# ---------------------------------------------------------------------------

def _etag_cache_path(root: Path, skill: str) -> Path:
    return root / ".git" / "gh-read-cache" / f"patrol-board-{skill or 'all'}.json"


def find_board_issue(root: Path, skill: str) -> tuple[dict | None, bool, int]:
    """Locate the existing board issue for `role` via one ETag-conditional
    `gh api` call. Returns (issue_dict_or_None, ok, billed_calls). A 304
    response reuses the cached issue and bills 0 calls."""
    slug = spawn._repo_slug(root)
    if not slug:
        return None, False, 0

    cache_path = _etag_cache_path(root, skill)
    etag = None
    cached_raw = None
    try:
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            etag = cached.get("etag")
            cached_raw = cached.get("raw")
            if not isinstance(etag, str):
                etag, cached_raw = None, None
    except (OSError, ValueError, UnicodeDecodeError):
        etag, cached_raw = None, None

    labels = f"{LABEL_BOARD},skill:{skill}" if skill else LABEL_BOARD
    # -X GET is load-bearing: `gh api` with -f fields and no method defaults
    # to POST, and POST /issues is issue CREATION (observed live: 422 only
    # because the payload lacked a title — PR #1594 review).
    cmd = ["gh", "api", "-X", "GET", f"repos/{slug}/issues",
           "-f", f"labels={labels}", "-f", "state=all", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    status, headers, body = spawn._split_gh_api_i_output(r.stdout)
    # gh api exits NON-ZERO on HTTP 304 (observed live: rc=1, stderr
    # "gh: HTTP 304") — the returncode check must not run before the
    # status parse, or the cached-read path is unreachable and every
    # conditional hit reads as a lookup failure (PR #1594 review).
    if r.returncode != 0 and status != 304:
        return None, False, 1
    if status == 304:
        return (cached_raw[0] if cached_raw else None), True, 0
    try:
        data = json.loads(body)
    except ValueError:
        return None, False, 1
    if not isinstance(data, list):
        return None, False, 1

    new_etag = headers.get("etag")
    if new_etag:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"etag": new_etag, "raw": data}),
                                   encoding="utf-8")
        except OSError:
            pass
    return (data[0] if data else None), True, 1


def _budget_path(root: Path, date: str) -> Path:
    return root / ".git" / "patrol-board" / f"write-budget-{date}.json"


def write_budget_ok(root: Path, date: str, cap: int = DEFAULT_DAILY_WRITE_BUDGET) -> bool:
    path = _budget_path(root, date)
    try:
        count = json.loads(path.read_text(encoding="utf-8")).get("count", 0) if path.exists() else 0
    except (OSError, ValueError):
        count = 0
    return count < cap


def record_write(root: Path, date: str) -> None:
    path = _budget_path(root, date)
    try:
        count = json.loads(path.read_text(encoding="utf-8")).get("count", 0) if path.exists() else 0
    except (OSError, ValueError):
        count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"count": count + 1}), encoding="utf-8")


def record_drop(root: Path, skill: str, date: str) -> None:
    """Drop-and-record: a write skipped for daily budget is never queued
    for later — it is logged once and the run moves on."""
    report = root / "docs" / "issue-1588" / "reports" / "write-budget-drops.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {date} role={skill or '(all)'} write dropped: daily budget exceeded\n"
    with report.open("a", encoding="utf-8") as f:
        f.write(line)


def run_patrol_board(root: Path, skill: str, queue_path: Path, dry_run: bool,
                      date: str) -> dict:
    """Orchestrates one patrol-board run for `role`. Returns a summary
    dict (also what --dry-run prints). Makes 0 subprocess/gh calls when
    dry_run is True."""
    queue = patrol_queue.load_queue(queue_path)

    if dry_run:
        # dry-run never touches gh: prior body is treated as absent so the
        # printed body reflects a from-scratch render of the current queue.
        body = build_next_body(None, skill, queue)
        return {"dry_run": True, "api_calls": 0, "wrote": False, "body": body}

    issue, ok, calls = find_board_issue(root, skill)
    if not ok:
        # A failed lookup must never fall through to create — a transient
        # error would mint a duplicate board (PR #1594 review).
        return {"dry_run": False, "api_calls": calls, "wrote": False,
                "error": "board lookup failed"}
    prior_body = issue.get("body") if issue else None
    next_body = build_next_body(prior_body, skill, queue)

    if issue is not None and prior_body == next_body:
        return {"dry_run": False, "api_calls": calls, "wrote": False, "body": next_body}

    if not write_budget_ok(root, date):
        record_drop(root, skill, date)
        return {"dry_run": False, "api_calls": calls, "wrote": False,
                 "body": next_body, "dropped": True}

    title = f"Patrol board: {skill or 'all skills'}"
    if issue is None:
        # First-ever board for this role: labels must exist or create 422s.
        # `gh label create --force` is idempotent; one-time cost per repo.
        for lbl in (LABEL_BOARD, f"skill:{skill}"):
            subprocess.run(["gh", "label", "create", lbl, "--force"],
                           cwd=root, capture_output=True, text=True)
        w = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", next_body,
             "--label", LABEL_BOARD, "--label", f"skill:{skill}"],
            cwd=root, capture_output=True, text=True)
    else:
        w = subprocess.run(
            ["gh", "issue", "edit", str(issue["number"]), "--body", next_body],
            cwd=root, capture_output=True, text=True)
    wrote = w.returncode == 0
    if wrote:
        record_write(root, date)
    return {"dry_run": False, "api_calls": calls + 1, "wrote": wrote, "body": next_body}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "run":
        print("usage: python3 gates/patrol_board.py run <repo-root> <role> "
              "[--dry-run] [--queue PATH] [--date YYYY-MM-DD]")
        return 2
    rest = argv[1:]
    dry_run = "--dry-run" in rest
    if dry_run:
        rest.remove("--dry-run")
    queue_override = None
    if "--queue" in rest:
        i = rest.index("--queue")
        queue_override = Path(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    date = "unspecified"
    if "--date" in rest:
        i = rest.index("--date")
        date = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]

    root = Path(rest[0]).resolve()
    skill = rest[1] if len(rest) > 1 else ""
    queue_path = queue_override or (root / patrol_queue.QUEUE_REL_PATH)

    summary = run_patrol_board(root, skill, queue_path, dry_run, date)
    print(json.dumps({k: v for k, v in summary.items() if k != "body"}, indent=2))
    if dry_run:
        print(summary["body"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
