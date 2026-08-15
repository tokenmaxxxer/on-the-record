"""issue-1582 — tier-1 role-patrol findings queue.

Mechanical scanner findings, fingerprinted by scanner + normalized path +
a hash of surrounding context lines (never raw line numbers, so a finding
survives an unrelated line-shift elsewhere in the file — SARIF
partialFingerprints precedent, docs/issue-1582/proposals/
2026-08-15-tier1-role-patrol-pilot.md).

Pure functions over a JSONL queue file; no git or network dependency, no
LLM call anywhere in this module.

  python3 -m gates.patrol_queue scan <repo-root> [--lane diff|sweep]
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import record_lint  # noqa: E402

QUEUE_REL_PATH = ".on-the-record/findings/queue.jsonl"
DISMISSAL_REASONS = ("false-positive", "wont-fix", "test-code")
LANES = ("diff", "sweep")


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _context_hash(context_lines: list[str]) -> str:
    normalized = "\n".join(line.strip() for line in context_lines if line.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def fingerprint(scanner_id: str, path: str, context_lines: list[str]) -> str:
    """sha256(scanner_id + normalized_path + context-region hash) — no
    line numbers in identity, so unrelated line-shifts elsewhere in the
    file don't churn a finding's identity."""
    material = f"{scanner_id}\x00{_normalize_path(path)}\x00{_context_hash(context_lines)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def load_queue(queue_path: Path) -> list[dict]:
    if not queue_path.exists():
        return []
    out = []
    for line in queue_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def save_queue(queue_path: Path, queue: list[dict]) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        "\n".join(json.dumps(e, sort_keys=True) for e in queue) + ("\n" if queue else ""),
        encoding="utf-8",
    )


def enqueue(queue: list[dict], finding: dict) -> list[dict]:
    """Existing fingerprint -> refresh last_seen only. New fingerprint ->
    append a new entry with first_seen == last_seen.

    Lane is set here from the finding's own `lane` field and never
    mutated afterward; `promotable` can only be true when lane == "diff"
    — enforced here, not left to caller discipline."""
    fp = finding["fingerprint"]
    lane = finding.get("lane", "sweep")
    if lane not in LANES:
        raise ValueError(f"unknown lane: {lane!r}")
    promotable = bool(finding.get("promotable", False)) and lane == "diff"

    for entry in queue:
        if entry["fingerprint"] == fp:
            entry["last_seen"] = finding["last_seen"]
            entry["status"] = "open"
            return queue

    new_entry = {
        "fingerprint": fp,
        "scanner_id": finding["scanner_id"],
        "path": _normalize_path(finding["path"]),
        "finding_class": finding["finding_class"],
        "excerpt": finding["excerpt"],
        "first_seen": finding["last_seen"],
        "last_seen": finding["last_seen"],
        "lane": lane,
        "promotable": promotable,
        "status": "open",
    }
    return queue + [new_entry]


def absence_close(queue: list[dict], scope: str, seen_fingerprints: set) -> list[dict]:
    """Any entry whose path falls under `scope` and whose fingerprint did
    not reappear in `seen_fingerprints` this scan is marked status=fixed."""
    out = []
    for entry in queue:
        in_scope = entry["path"].startswith(_normalize_path(scope)) if scope else True
        if in_scope and entry["fingerprint"] not in seen_fingerprints and entry["status"] == "open":
            entry = dict(entry, status="fixed")
        out.append(entry)
    return out


def apply_budget(findings: list[dict], per_scanner_cap: int) -> tuple[list[dict], list[dict]]:
    """Truncate each scanner's findings at `per_scanner_cap`; return
    (kept, meta_findings) — one meta finding per truncated scanner
    stating the drop count. Drop-not-queue: overflow never backlogs."""
    by_scanner: dict[str, list[dict]] = {}
    for f in findings:
        by_scanner.setdefault(f["scanner_id"], []).append(f)

    kept: list[dict] = []
    meta: list[dict] = []
    for scanner_id, items in by_scanner.items():
        keep = items[:per_scanner_cap]
        dropped = items[per_scanner_cap:]
        kept.extend(keep)
        if dropped:
            meta.append({
                "scanner_id": scanner_id,
                "path": "",
                "finding_class": "budget-truncation",
                "excerpt": f"scanner {scanner_id} truncated, {len(dropped)} more",
                "lane": items[0].get("lane", "sweep"),
                "promotable": False,
            })
    return kept, meta


def verify(finding: dict, repo_root: Path) -> bool:
    """Re-read the cited path and confirm the quoted excerpt is still
    present verbatim before enqueue (curl bug-bounty lesson: an
    unverifiable finding is dropped, never queued)."""
    path = repo_root / finding["path"]
    if not path.exists() or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return finding["excerpt"].strip() in text


def record_dismissal(queue: list[dict], fingerprint_: str, reason: str) -> list[dict]:
    if reason not in DISMISSAL_REASONS:
        raise ValueError(f"unknown dismissal reason: {reason!r}")
    out = []
    for entry in queue:
        if entry["fingerprint"] == fingerprint_:
            entry = dict(entry, status="dismissed", dismissal_reason=reason)
        out.append(entry)
    return out


def is_dismissed(queue: list[dict], fingerprint_: str) -> bool:
    for entry in queue:
        if entry["fingerprint"] == fingerprint_ and entry["status"] == "dismissed":
            return True
    return False


def dismissal_counts(queue: list[dict]) -> dict[str, int]:
    """Per-scanner dismissal counters for the eviction contract
    (>=10% probation / >=25% stop-promoting) — counters land now,
    enforcement is explicitly out of scope for this pilot."""
    counts: dict[str, int] = {}
    for entry in queue:
        if entry["status"] == "dismissed":
            counts[entry["scanner_id"]] = counts.get(entry["scanner_id"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# record_lint scanner adapter — the pilot's one tier-1 scanner (design req 8:
# reuse an existing gate script in scan mode; record_lint's whole-repo mode
# already exists and needs no new admission process).
# ---------------------------------------------------------------------------

SCANNER_ID_RECORD_LINT = "record_lint"

_QUOTED_SPAN = re.compile(r"'([^']+)'|`([^`]+)`")


def _quoted_excerpt(message: str) -> str | None:
    """record_lint violation messages carry their evidence as a quoted
    span lifted verbatim from the record (e.g. "...: 'some record text'
    — explanation"), before the final " — " separator. Pull that span out
    so `verify()` checks against text that can actually appear in the
    file — the full violation sentence (rule name + explanation) never
    does."""
    head = message.split(" — ")[0]
    matches = _QUOTED_SPAN.findall(head)
    if not matches:
        return None
    last = matches[-1]
    return last[0] or last[1]


def scan_record_lint(repo_root: Path) -> list[dict]:
    """Run record_lint.find_records/lint_record over `repo_root` and
    translate violations into pilot finding dicts (pre-fingerprint,
    pre-lane — caller sets lane/scan-scope). A violation with no
    verbatim-quoted span (e.g. a reach-check rule naming a path, not
    record text) has no anchor `verify()` can confirm and is dropped at
    scan time rather than churning the verify-drop counter."""
    findings = []
    for rec in record_lint.find_records(repo_root):
        violations = record_lint.lint_record(rec)
        rel = rec.relative_to(repo_root).as_posix()
        for v in violations:
            excerpt = _quoted_excerpt(v)
            if excerpt is None:
                continue
            findings.append({
                "scanner_id": SCANNER_ID_RECORD_LINT,
                "path": rel,
                "finding_class": "record-lint-violation",
                "excerpt": excerpt,
                # The full violation message (rule + quoted span), not the
                # excerpt alone: keeps two different rules that happen to
                # quote overlapping record text from colliding onto one
                # fingerprint, while staying stable under unrelated edits
                # elsewhere in the record (no line numbers involved).
                "context_lines": [v],
            })
    return findings


def run_scan(repo_root: Path, lane: str, per_scanner_cap: int = 200) -> dict:
    """End-to-end: scan -> verify -> budget -> fingerprint -> enqueue ->
    absence-close -> save. Returns a summary dict for measurement
    reporting (no side effects beyond writing the queue file)."""
    if lane not in LANES:
        raise ValueError(f"unknown lane: {lane!r}")

    queue_path = repo_root / QUEUE_REL_PATH
    queue = load_queue(queue_path)

    raw_findings = scan_record_lint(repo_root)

    verified = []
    verify_dropped = 0
    for f in raw_findings:
        probe = {"path": f["path"], "excerpt": f["excerpt"]}
        if verify(probe, repo_root):
            verified.append(f)
        else:
            verify_dropped += 1

    for f in verified:
        f["lane"] = lane

    kept, meta = apply_budget(verified, per_scanner_cap)

    seen_fingerprints = set()
    for f in kept:
        fp = fingerprint(f["scanner_id"], f["path"], f["context_lines"])
        seen_fingerprints.add(fp)
        finding = {
            "fingerprint": fp,
            "scanner_id": f["scanner_id"],
            "path": f["path"],
            "finding_class": f["finding_class"],
            "excerpt": f["excerpt"],
            "last_seen": "scan",
            "lane": lane,
            "promotable": (lane == "diff"),
        }
        if is_dismissed(queue, fp):
            continue
        queue = enqueue(queue, finding)

    for m in meta:
        fp = fingerprint(m["scanner_id"], "", [m["excerpt"]])
        seen_fingerprints.add(fp)
        queue = enqueue(queue, {
            "fingerprint": fp,
            "scanner_id": m["scanner_id"],
            "path": m["path"],
            "finding_class": m["finding_class"],
            "excerpt": m["excerpt"],
            "last_seen": "scan",
            "lane": m["lane"],
            "promotable": False,
        })

    scope = "" if lane == "sweep" else ""
    queue = absence_close(queue, scope, seen_fingerprints)
    save_queue(queue_path, queue)

    return {
        "lane": lane,
        "scanner": SCANNER_ID_RECORD_LINT,
        "raw_findings": len(raw_findings),
        "verified": len(verified),
        "verify_dropped": verify_dropped,
        "enqueued": len(kept),
        "budget_truncated_scanners": len(meta),
        "queue_size": len(queue),
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "scan":
        print("usage: python3 -m gates.patrol_queue scan <repo-root> [--lane diff|sweep]")
        return 2
    rest = argv[1:]
    lane = "sweep"
    if "--lane" in rest:
        i = rest.index("--lane")
        lane = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    root = Path(rest[0]) if rest else Path(".")
    summary = run_scan(root.resolve(), lane)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
