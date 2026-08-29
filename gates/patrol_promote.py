"""issue-1589 — patrol board C2: checkbox tick = work-start approval.

Promotes a ticked Pending-Approval board line to a real, structured
per-finding GitHub issue exactly once (fingerprint search before
create), moves the board line to "Approved / In Progress", enforces
rate caps (2 promotions/hour/role, 10 open patrol issues/role) with a
"queued: rate cap" board annotation instead of a silent drop, and never
lets patrol's own promoted issues re-trigger patrol.

Reuses gates/patrol_board.py's select_board_entries for role scoping
(scanner_id first, path-prefix second — binding integration note, PR
#1592 review) and gates/patrol_trigger.py's own file-path anti-loop
guard rather than re-deriving either. This module's own anti-loop axis
(never re-promote the same tick) is handled here via a body marker +
label, not by editing patrol_trigger.py.

Scope ends at creating the promoted issue and moving the board line —
it does NOT spawn role sessions or run any classification/approval-token
flow (that is the normal orchestration path, per issue #1589's own
stated scope).

  python3 gates/patrol_promote.py run <repo-root> <role> [--dry-run]
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
import patrol_board  # noqa: E402
import patrol_queue  # noqa: E402

LABEL_PROMOTED = "patrol-promoted"
RATE_CAP_HOURLY_PER_SKILL = 2
RATE_CAP_OPEN_PER_SKILL = 10
_MARKER_RE = re.compile(r"<!-- patrol:promoted fp=([0-9a-f]+) -->")


def _marker(fingerprint: str) -> str:
    return f"<!-- patrol:promoted fp={fingerprint} -->"


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------

def _resolve_prefix(fp_prefix: str, queue: list[dict]) -> dict | None:
    for entry in queue:
        if entry["fingerprint"][:12] == fp_prefix:
            return entry
    return None


def detect_ticks(prior_body: str | None, new_body: str, queue: list[dict]
                  ) -> list[dict]:
    """Compare the Pending-Approval section of `prior_body` (the board
    body this module itself last processed; None on first run) against
    `new_body`. A line whose fingerprint prefix was unchecked (or absent)
    in `prior_body` and is checked in `new_body` is a fresh tick — the
    only kind of tick this issue's PCC-2 scope may act on. Returns the
    matching full queue entries, in board order."""
    prior_checked: set[str] = set()
    if prior_body:
        for line in patrol_board.parse_board_body(prior_body)[patrol_board.PENDING_HEADING]:
            m = patrol_board._CHECKBOX_LINE.match(line)
            if m and m.group(1) == "x":
                prior_checked.add(m.group(2))

    ticks = []
    for line in patrol_board.parse_board_body(new_body)[patrol_board.PENDING_HEADING]:
        m = patrol_board._CHECKBOX_LINE.match(line)
        if not m or m.group(1) != "x":
            continue
        fp_prefix = m.group(2)
        if fp_prefix in prior_checked:
            continue
        entry = _resolve_prefix(fp_prefix, queue)
        if entry is not None:
            ticks.append(entry)
    return ticks


def build_finding_issue_body(entry: dict) -> str:
    """Structured per-finding issue body: fingerprint, rule/baseline ID
    (scanner_id), file:line@SHA, severity, evidence, proposed direction,
    plus the anti-loop marker. `entry["path"]` carries no line number
    (patrol_queue fingerprints deliberately exclude line numbers), so
    the location line renders as `path@last_seen` — the same shape
    patrol_board._finding_line already uses for the board's own line."""
    sev = entry.get("severity", "unspecified")
    loc = f"{entry['path']}@{entry.get('last_seen', '')}"
    return (
        f"**Fingerprint:** `{entry['fingerprint']}`\n"
        f"**Rule / baseline ID:** `{entry['scanner_id']}` / `{entry['finding_class']}`\n"
        f"**Location:** `{loc}`\n"
        f"**Severity:** {sev}\n\n"
        f"**Evidence:**\n```\n{entry['excerpt']}\n```\n\n"
        f"**Proposed direction:** address the `{entry['finding_class']}` "
        f"finding at `{loc}` per the `{entry['scanner_id']}` rule that "
        "flagged it.\n\n"
        f"{_marker(entry['fingerprint'])}\n"
    )


def rate_cap_ok(state: dict, now_hour_key: str) -> tuple[bool, bool]:
    """(hourly_ok, open_ok) per PCC-5, checked independently. `now_hour_key`
    is an hour-granularity key (e.g. an ISO string truncated to the
    hour) — a promotion timestamp counts toward the hourly cap only when
    its own hour key matches."""
    promotions = state.get("promotions", [])
    hourly_count = sum(1 for ts in promotions if ts.startswith(now_hour_key))
    open_count = len(state.get("open_issue_numbers", []))
    return hourly_count < RATE_CAP_HOURLY_PER_SKILL, open_count < RATE_CAP_OPEN_PER_SKILL


def move_ticked_line(pending_lines: list[str], approved_lines: list[str],
                      fp_prefix: str, issue_number: int | None,
                      annotation: str | None = None) -> tuple[list[str], list[str]]:
    """Moves the ticked Pending line matching `fp_prefix` into Approved /
    In Progress with a link to `issue_number`. When `annotation` is set
    (rate-cap deferral) the line stays in Pending, ticked, with the
    annotation suffix appended instead — "queued", never dropped."""
    remaining, moved = [], None
    for line in pending_lines:
        m = patrol_board._CHECKBOX_LINE.match(line)
        if m and m.group(2) == fp_prefix:
            moved = line
            continue
        remaining.append(line)
    if moved is None:
        return pending_lines, approved_lines

    if annotation:
        remaining_with_note = remaining + [f"{moved} ({annotation})"]
        return remaining_with_note, approved_lines

    rest_text = patrol_board._CHECKBOX_LINE.match(moved).group(3)
    approved_line = f"- `{fp_prefix}` {rest_text} -> #{issue_number}"
    return remaining, approved_lines + [approved_line]


# ---------------------------------------------------------------------------
# Imperative shell
# ---------------------------------------------------------------------------

def _state_path(root: Path, skill: str) -> Path:
    return root / ".git" / "patrol-promote" / f"{skill or 'all'}.json"


def load_state(root: Path, skill: str) -> dict:
    path = _state_path(root, skill)
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("promotions", [])
            data.setdefault("open_issue_numbers", [])
            return data
    except (OSError, ValueError):
        pass
    return {"promotions": [], "open_issue_numbers": []}


def save_state(root: Path, skill: str, state: dict) -> None:
    path = _state_path(root, skill)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def _prior_body_path(root: Path, skill: str) -> Path:
    return root / ".git" / "patrol-promote" / f"prior-body-{skill or 'all'}.txt"


def load_prior_body(root: Path, skill: str) -> str | None:
    path = _prior_body_path(root, skill)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def save_prior_body(root: Path, skill: str, body: str) -> None:
    path = _prior_body_path(root, skill)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def find_existing_promotion(root: Path, fingerprint: str) -> int | None:
    """Idempotence check: same tick never files twice, survives process
    restarts — searches live GitHub state, not just local state."""
    slug = spawn._repo_slug(root)
    if not slug:
        return None
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", slug, "--label", LABEL_PROMOTED,
         "--state", "all", "--search", fingerprint[:12], "--json",
         "number,body", "--limit", "50"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        hits = json.loads(r.stdout)
    except ValueError:
        return None
    for hit in hits:
        m = _MARKER_RE.search(hit.get("body") or "")
        if m and m.group(1) == fingerprint:
            return hit["number"]
    return None


def promote_tick(root: Path, skill: str, entry: dict, state: dict,
                  now_iso: str) -> dict:
    """Orchestrates one tick's promotion. Idempotence search runs before
    any cap check, so an already-promoted tick is never blocked by its
    own prior promotion's cap consumption."""
    existing = find_existing_promotion(root, entry["fingerprint"])
    if existing is not None:
        return {"promoted": True, "issue": existing, "already_existed": True}

    hourly_ok, open_ok = rate_cap_ok(state, now_iso[:13])
    if not (hourly_ok and open_ok):
        return {"promoted": False, "reason": "rate_cap"}

    sev = entry.get("severity", "unspecified")
    title = f"[patrol:{skill or 'all'}] {entry['finding_class']}: {entry['path']}"
    body = build_finding_issue_body(entry)
    # Labels must exist or the create 422s (same failure class as the board's
    # first create — PR #1594 review). `gh label create --force` is idempotent.
    for lbl in (LABEL_PROMOTED, "finding", f"skill:{skill}", f"severity:{sev}"):
        subprocess.run(["gh", "label", "create", lbl, "--force"],
                       cwd=root, capture_output=True, text=True)
    r = subprocess.run(
        ["gh", "issue", "create", "--title", title, "--body", body,
         "--label", LABEL_PROMOTED, "--label", "finding",
         "--label", f"skill:{skill}", "--label", f"severity:{sev}"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return {"promoted": False, "reason": "gh_error", "stderr": r.stderr[:300]}

    issue_url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    m = re.search(r"/issues/(\d+)", issue_url)
    issue_number = int(m.group(1)) if m else None

    state["promotions"] = state.get("promotions", []) + [now_iso]
    if issue_number is not None:
        state["open_issue_numbers"] = state.get("open_issue_numbers", []) + [issue_number]
    return {"promoted": True, "issue": issue_number}


def _has_checked_pending(body: str) -> bool:
    pending = patrol_board.parse_board_body(body)[patrol_board.PENDING_HEADING]
    return any(line.lstrip().startswith("- [x]") for line in pending)


def run_patrol_promote(root: Path, skill: str, queue_path: Path, dry_run: bool,
                        now_iso: str) -> dict:
    queue = patrol_queue.load_queue(queue_path)

    if dry_run:
        return {"dry_run": True, "api_calls": 0, "promotions": [], "deferred": []}

    issue, ok, calls = patrol_board.find_board_issue(root, skill)
    new_body = issue.get("body") if issue else None
    if new_body is None:
        return {"dry_run": False, "api_calls": calls, "promotions": [], "deferred": []}

    # Correctness note (live E2E, PR #1594 review): the prior-body diff
    # alone CONSUMES a tick even when its promotion fails (gh_error) or is
    # rate-capped — the next run sees no fresh tick and the approval is
    # silently lost. Promotion eligibility is therefore "checked AND still
    # in Pending Approval", with idempotence guaranteed by
    # find_existing_promotion(), not by the body diff. prior_body is kept
    # only as a cheap short-circuit when nothing changed at all.
    prior_body = load_prior_body(root, skill)
    if prior_body == new_body and not _has_checked_pending(new_body):
        return {"dry_run": False, "api_calls": calls, "promotions": [], "deferred": []}
    ticks = detect_ticks(None, new_body, queue)

    if not ticks:
        save_prior_body(root, skill, new_body)
        return {"dry_run": False, "api_calls": calls, "promotions": [], "deferred": []}

    state = load_state(root, skill)
    sections = patrol_board.parse_board_body(new_body)
    pending_lines = sections[patrol_board.PENDING_HEADING]
    approved_lines = sections[patrol_board.APPROVED_HEADING]

    promotions, deferred = [], []
    for entry in ticks:
        fp_prefix = entry["fingerprint"][:12]
        result = promote_tick(root, skill, entry, state, now_iso)
        if result["promoted"]:
            pending_lines, approved_lines = move_ticked_line(
                pending_lines, approved_lines, fp_prefix, result["issue"])
            promotions.append({"fingerprint": entry["fingerprint"], "issue": result["issue"]})
        else:
            annotation = "queued: rate cap" if result.get("reason") == "rate_cap" else None
            if annotation:
                pending_lines, approved_lines = move_ticked_line(
                    pending_lines, approved_lines, fp_prefix, None, annotation=annotation)
            deferred.append({"fingerprint": entry["fingerprint"], "reason": result.get("reason")})

    save_state(root, skill, state)

    next_body = patrol_board._render_from_lines(
        pending_lines, approved_lines, sections[patrol_board.CLOSED_HEADING])

    api_calls = calls
    wrote = False
    if next_body != new_body and issue is not None:
        if patrol_board.write_budget_ok(root, now_iso[:10]):
            w = subprocess.run(
                ["gh", "issue", "edit", str(issue["number"]), "--body", next_body],
                cwd=root, capture_output=True, text=True)
            api_calls += 1
            wrote = w.returncode == 0
            if wrote:
                patrol_board.record_write(root, now_iso[:10])
        else:
            patrol_board.record_drop(root, skill, now_iso[:10])

    save_prior_body(root, skill, next_body if wrote else new_body)

    return {"dry_run": False, "api_calls": api_calls, "wrote": wrote,
            "promotions": promotions, "deferred": deferred}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "run":
        print("usage: python3 gates/patrol_promote.py run <repo-root> <role> "
              "[--dry-run] [--queue PATH] [--date YYYY-MM-DDTHH]")
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
    now_iso = "1970-01-01T00:00:00"
    if "--date" in rest:
        i = rest.index("--date")
        now_iso = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]

    root = Path(rest[0]).resolve()
    skill = rest[1] if len(rest) > 1 else ""
    queue_path = queue_override or (root / patrol_queue.QUEUE_REL_PATH)

    summary = run_patrol_promote(root, skill, queue_path, dry_run, now_iso)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
