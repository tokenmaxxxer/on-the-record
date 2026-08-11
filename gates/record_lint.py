"""issue-517 — aggregate, single-pass record lint.

Authoring a role record today costs one model turn per gate refusal:
`record_enums`/`record_wellformed`/... in `gates.py` and the four checks
mirrored inline in `on-the-record/hooks/record-claim-guard.sh` each
report only their own first failure, and there is no single command an
author can run before writing to see every violation at once (a
7-refusal loop was observed on issue-512 phase 2).

`lint_record(path)` is a thin aggregator: it calls the existing
`gates.py` check functions (unchanged — this module adds no new rule
logic for anything they already cover) plus four checks lifted here
from `record-claim-guard.sh`'s inline regexes, and unions every
violation into one list. `record-claim-guard.sh` and `gates/ci.py` call
back into this module's functions instead of carrying their own copies,
so each rule's logic lives in exactly one place.

  python3 -m gates.record_lint <record-path>
  python3 -m gates.record_lint            # scans the whole repo
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates

RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md

# Re-exported, not reimplemented: `gates/ci.py` and `record-claim-guard.sh`
# call these names on this module instead of holding their own copies —
# single source of truth means the same function object, not a mirror.
record_enums = gates.record_enums
record_wellformed_in = gates.record_wellformed_in
record_no_tool_residue_in = gates.record_no_tool_residue_in
record_checked_claims = gates.record_checked_claims


def _repo_root(start: Path) -> Path:
    """Walk up from `start` to the nearest `.git` — the target repo's
    root, not this plugin's own checkout (`gates.ON_THE_RECORD_ROOT`)."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    for cand in (p, *p.parents):
        if (cand / ".git").exists():
            return cand
    return start.resolve() if start.is_dir() else start.resolve().parent


# ---------------------------------------------------------------------------
# Checks lifted from record-claim-guard.sh's inline mirror (issue #457 Group
# A/B) — the hook used to carry these as a write-time-fragment approximation.
# Here they run against a record's full text, the shape issue #517 requires.
# ---------------------------------------------------------------------------

_UNVERIFIABLE_LINE = re.compile(r"(?im)^\s*[-*]?\s*unverifiable\s*:\s*(.*)$")
_CHECKED_CLAIM_LINE = re.compile(
    r"^\s*[-*]\s*.+—\s*checked:\s*(\S+)\s*—\s*"
    r"result:\s*(pass|fail|unverifiable)(?::\s*(.+))?\s*$")
_COUNT_RATIO = re.compile(r"\d+\s*(?:of|/)\s*\d+")
_COUNT_NOUN = re.compile(
    r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?|tests?)\b")
_CLAIM_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
_PATH_REF = re.compile(
    r"`((?:src|test|tests|docs|gates|on-the-record)/[^`\s]+)`")

# issue #793 — verify-before-claim: a state/defect-claim marker vocabulary,
# deliberately narrow (known bypassable by synonym choice, same tradeoff
# `_COUNT_RATIO`/`_COUNT_NOUN` already accept — widen from real record
# corpus usage in a later pass, not a closed set assumed complete here).
_STATE_CLAIM_MARKER = re.compile(
    r"(?i)\b(halted|merged|closed|found|confirms?|confirmed|"
    r"is\s+running|is\s+gone|is\s+stale)\b")
_CANONICAL_TAG = re.compile(r"`?canonical:\s*(\S.*?)`?\s*$", re.MULTILINE)

# issue #870 — generalized fake-success detection, candidate (a): an
# OUTCOME claim ("requirement met", "done", "PASS", "complete") needs a
# citation that is itself an EXECUTED-LIVE reference, not just any
# `canonical:` tag — #793's own check only requires the tag be non-empty,
# never inspects what kind of source it names (a prior transcript read
# passes identically to a command actually run this turn). Deliberately
# narrow, same known-bypassable-by-synonym tradeoff `_STATE_CLAIM_MARKER`
# already accepts — widen from real record-corpus usage later, not a
# closed set assumed complete here.
_OUTCOME_CLAIM_MARKER = re.compile(
    r"(?i)\b(requirement(?:s)?\s+met|done|PASS(?:es|ed)?|complete[ds]?)\b")
_EXECUTED_LIVE_CANONICAL = re.compile(
    r"(?i)^(?:gh\s|git\s|pytest\b|python3?\s|npm\s|npx\s|bash\s|sh\s|\./|"
    r"acceptance:\s*\S.*\bresult:\s*(?:PASS|FAIL|UNMEASURED)\b)")


def outcome_claim_citation_check(text: str) -> list[str]:
    """issue #870 mirror: an OUTCOME claim ("requirement(s) met", "done",
    "PASS(es/ed)", "complete(d)") needs a `canonical:` tag within 3 lines
    above it whose cited source is itself an executed-live reference (a
    command string, or an `acceptance: <command> — result: ...` line) —
    not a bare file-read/summary citation, which satisfies #793's own
    state-claim check but does not prove the claimed outcome was actually
    re-run against the current state. Fail-closed: no qualifying citation
    -> refused."""
    bad = []
    lines = text.splitlines()
    in_fence = [False] * len(lines)
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
    for i, line in enumerate(lines):
        if in_fence[i]:
            continue
        # A markdown heading ("## What was done") names a section, it
        # does not itself assert an outcome — skip, same shape reasoning
        # `bare_count_claim_check` uses to skip fenced code.
        if line.lstrip().startswith("#"):
            continue
        if not _OUTCOME_CLAIM_MARKER.search(line):
            continue
        window = "\n".join(lines[max(0, i - 3):i + 1])
        m = _CANONICAL_TAG.search(window)
        cited = m.group(1).strip().strip("`") if m and m.group(1).strip() else ""
        has_executed_live = bool(cited) and bool(
            _EXECUTED_LIVE_CANONICAL.search(cited))
        # A `derived: <command>` tag (#333's own citation for a count
        # claim) is itself a command reference — accept it as a sibling
        # executed-live source, same "don't double-demand a citation for
        # what's already cited" treatment `canonical_source_claim_check`
        # gives count claims.
        has_derived = bool(_CLAIM_DERIVED_TAG.search(window))
        if not has_executed_live and not has_derived:
            bad.append(
                "레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): "
                f"{line.strip()!r} — 'requirement met/done/PASS/complete' "
                "류의 결과 주장을 하면서 3줄 이내에 실행-라이브 인용"
                "(`gh ...`/`pytest ...`/`python3 ...`/"
                "`acceptance: <command> — result: ...` 등으로 시작하는 "
                "`canonical:` 태그)이 없다 — 파일을 읽었다는 인용만으로는 "
                "부족하다.")
    return bad


def unverifiable_reason_check(text: str) -> list[str]:
    """#310/#331 mirror: an `unverifiable:` escape line needs a reason."""
    bad = []
    for m in _UNVERIFIABLE_LINE.finditer(text):
        if not m.group(1).strip():
            bad.append(
                "`unverifiable:` 줄에 이유가 없다 (issue #310) — "
                "`unverifiable: <이유>` 형태로 왜 기계 검사가 불가능한지 "
                "적어야 한다.")
    return bad


def checked_claim_reason_check(text: str) -> list[str]:
    """#331 mirror: an Acceptance-verification `unverifiable` result needs
    a reason."""
    bad = []
    for ln in text.splitlines():
        cm = _CHECKED_CLAIM_LINE.match(ln)
        if not cm:
            continue
        result, reason = cm.group(2), cm.group(3)
        if result == "unverifiable" and not (reason and reason.strip()):
            bad.append(
                "Acceptance verification 의 `unverifiable` 항목에 이유가 "
                f"없다 (issue #331): {ln.strip()!r}")
    return bad


def bare_count_claim_check(text: str) -> list[str]:
    """#333 mirror: a bare "N of M"/"N items" count needs `derived:` or a
    code-fence reproduction — fences are excluded."""
    bad = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for pat in (_COUNT_RATIO, _COUNT_NOUN):
            for cm in pat.finditer(line):
                tail = line[cm.end():]
                if _CLAIM_DERIVED_TAG.match(tail.lstrip()):
                    continue
                bad.append(
                    "레코드에 근거 없는 개수 주장 (issue #333): "
                    f"{line.strip()!r} — 숫자가 코드펜스 재현이나 "
                    "`derived: ...` 인용 없이 그냥 타이핑되어 있다.")
                break
    return bad


def orphaned_path_reference_check(root: Path, text: str) -> list[str]:
    """#330 mirror: a backtick-quoted relative path that resolves nowhere
    in the working tree."""
    bad = []
    for m in _PATH_REF.finditer(text):
        ref = m.group(1)
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if not (root / ref).exists():
            bad.append(
                "레코드가 존재하지 않는 경로를 참조한다 (issue #330): "
                f"`{ref}` — 리치(reach)가 끊긴 참조다.")
    return bad


def canonical_source_claim_check(text: str) -> list[str]:
    """issue #793 mirror: a state/defect-claim line (role output "found",
    session/PR/board state "halted|merged|closed|is running|is gone|is
    stale", or a bare count claim) needs a `canonical: <what was read>`
    tag within 3 lines above it, citing the actual role record/diff, raw
    ground-truth command output, or file:line-context read — not a
    summary/grep/watcher signal with nothing named."""
    bad = []
    lines = text.splitlines()
    in_fence = [False] * len(lines)
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
    for i, line in enumerate(lines):
        if in_fence[i]:
            continue
        marker_claim = bool(_STATE_CLAIM_MARKER.search(line))
        count_claim = not marker_claim and bool(
            _COUNT_RATIO.search(line) or _COUNT_NOUN.search(line))
        if not (marker_claim or count_claim):
            continue
        window = "\n".join(lines[max(0, i - 3):i + 1])
        m = _CANONICAL_TAG.search(window)
        has_canonical = bool(m and m.group(1).strip())
        # A count claim already satisfying #333's `derived:` requirement
        # names its source too — `canonical:` is a sibling tag, not a
        # second mandatory citation for the same already-cited count.
        has_derived = count_claim and bool(_CLAIM_DERIVED_TAG.search(window))
        if not has_canonical and not has_derived:
            bad.append(
                "레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): "
                f"{line.strip()!r} — role output / session·PR·board 상태 / "
                "결함을 주장하면서 3줄 이내에 `canonical: <읽은 소스>` 태그가 "
                "없다 — 요약이나 grep/watcher 신호가 아니라 실제 레코드/diff, "
                "raw ground truth, 또는 file:line 컨텍스트를 인용해야 한다.")
    return bad


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def lint_record(path: Path) -> list[str]:
    """Run every record rule against one record file's full text and
    return the complete violation list — no first-failure abort.

    Delegates to `gates.py`'s existing diff-scoped check functions (they
    already accept a repo root and internally scan `changed_files()`,
    which covers uncommitted worktree edits — the common authoring case
    of a record just written/scaffolded), filtered down to violations
    naming this specific file, plus the four full-text checks above.
    """
    path = Path(path).resolve()
    root = _repo_root(path)
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    text = path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""

    bad: list[str] = []
    if not RECORD_PATH.match(rel):
        bad.append(
            f"레코드 경로 형태가 아니다: {rel} — "
            "docs/issue-<n>/reports/<role>.md 형태여야 한다.")
        return bad
    if not path.exists():
        bad.append(f"레코드 파일이 없다: {rel}")
        return bad

    diff_scoped = []
    try:
        diff_scoped += gates.record_enums(root, {})
        diff_scoped += gates.record_refusal_reasoned(root, {})
        diff_scoped += gates.record_wellformed_in(root)
        diff_scoped += gates.record_no_tool_residue_in(root)
        diff_scoped += gates.record_derived_counts_in(root)
        diff_scoped += gates.record_checked_claims(root, {})
        diff_scoped += gates.reach_check(root, text)
        diff_scoped += gates.sibling_mention_check(root, text)
    except RuntimeError as e:
        bad.append(str(e))
    # These functions report against every changed record, not just this
    # one — keep only violations that name this file.
    bad += [b for b in diff_scoped if rel in b]

    bad += unverifiable_reason_check(text)
    bad += checked_claim_reason_check(text)
    bad += bare_count_claim_check(text)
    bad += orphaned_path_reference_check(root, text)
    bad += canonical_source_claim_check(text)
    bad += outcome_claim_citation_check(text)
    return bad


def find_records(root: Path) -> list[Path]:
    """All `docs/issue-*/reports/*.md` record files tracked or present
    under `root` — used by the whole-repo scan mode."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            full = Path(dirpath) / fn
            rel = full.relative_to(root).as_posix()
            if RECORD_PATH.match(rel):
                out.append(full)
    return out


def main(argv: list[str]) -> int:
    target = Path(argv[0]) if argv else Path(".")
    if target.is_dir():
        records = find_records(target)
        if not records:
            print("record_lint: no records found under "
                  f"{target.resolve()} — 검사할 레코드가 없다.")
            return 0
        exit_code = 0
        for rec in sorted(records):
            violations = lint_record(rec)
            if violations:
                exit_code = 1
                print(f"== {rec} ==")
                for v in violations:
                    print(f"- {v}")
        return exit_code

    violations = lint_record(target)
    if not violations:
        print(f"record_lint: {target} — 위반 없음.")
        return 0
    for v in violations:
        print(f"- {v}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
