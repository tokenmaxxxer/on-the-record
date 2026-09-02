"""Standing delegation as machine-visible state (issue #3061).

The operator delegated end-to-end authority repeatedly in one session
("쭈우우욱 해", "네가 알아서 해") and the orchestrator kept stopping anyway to
re-ask for it, because the only record of that grant was conversational
memory — nothing the orchestrator re-read on the next turn. This module
gives that grant a durable, local, cheaply-re-readable record: a single
current-delegation file at `.on-the-record/delegation-state.json` (repo-root
runtime state, same directory `gates/auto_approval_class.py`'s circuit-
breaker state already lives in) that `spawn.py delegation-state` reads back.

This is deliberately a DIFFERENT mechanism from issue #707's standing
delegation (`on-the-record/hooks/approval-gate.sh`'s `DELEGATE <scope> UNTIL
<expiry>` GitHub-comment grammar): #707 answers "may this PR self-cite a
prior operator judgment as APPROVE provenance," checked live against GitHub
comments on every citation, because an APPROVE is consequential enough to
warrant a live re-check. #3061 answers a cheaper, more frequent question —
"is the orchestrator still authorized to keep going without asking again" —
that needs to be re-checked many times per turn, without a GitHub round
trip each time. A local recorded file is the right shape for that; #707's
live-checked comment grammar is not reused here.

Two things this module does NOT attempt, on purpose:

- It never suppresses or auto-answers anything. `audit()` only reports,
  after the fact, turns that plausibly asked for authority a delegation
  already covered — it is diagnostic, not a filter a live turn consults to
  decide whether to keep asking. A program cannot always tell "genuine fork
  the operator must decide" apart from "redundant ask" from text alone (the
  issue's own framing: both surface as a question) — `audit()` is
  deliberately high-precision/low-recall about it (see the extended comment
  above `_REDUNDANT_ASK_RES` below) rather than guessing on ambiguous cases,
  because a false positive here (mislabeling a real escalation as
  redundant) is the worse failure per the issue's own must-not clause. As
  of this module's issue #3061 repair round, this is enforced structurally,
  not just aspirationally: the pattern list matches only the closed set of
  phrasings actually quoted in the issue's own transcript, after two
  independent verifications (PR #3097, PR #3102) reproduced six genuine
  escalations misclassified as redundant by an earlier, more generalized
  pattern list. `test/test_delegation_state.py`'s
  `RedundantAskDirectionOfErrorEvalTest` measures the resulting
  false-redundant/false-genuine trade-off on a held-out set.
- It never grants indefinite authority. Issue #707's own proposal
  (docs/issue-707/proposals/product-discovery.md) already rejected "blanket
  standing delegation with no scope/expiry field" as unsafe; `grant()`
  carries that same principle here — every grant has an `expires_at`,
  defaulting to `DEFAULT_GRANT_HOURS` when the caller does not name one.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import trajectory_analyzer  # sibling top-level module in this checkout, not optional

STATE_REL_PATH = ".on-the-record/delegation-state.json"
DEFAULT_GRANT_HOURS = 24
DEFAULT_WORK_DIR = Path(os.path.expanduser("~/.tokenmaxxxer/work/"))
SESSION_LOG_GLOB = "*.session*.log"


class SkillBoundGrantError(RuntimeError):
    """Raised when a CLAUDE_SKILL-bound session tries to grant its own
    standing delegation — the same self-authorization ban issue #707's
    DELEGATION-CITING APPROVE already applies to APPROVE citations."""


def _state_path(repo: str) -> Path:
    return Path(repo) / STATE_REL_PATH


def _now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_state(repo: str) -> dict | None:
    """The raw recorded record, or None if nothing was ever granted (or the
    file is unreadable/corrupt — fail-closed to "no delegation" rather than
    raising, since a caller asking "am I still authorized" must never crash
    a session that was mid-flight)."""
    path = _state_path(repo)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _state_file_unreadable(repo: str) -> bool:
    """True iff the state file exists but load_state() couldn't parse it —
    distinguishes "genuinely no delegation" from "corrupted record" so
    describe() doesn't silently present the latter as the former."""
    path = _state_path(repo)
    return path.exists() and load_state(repo) is None


def in_force(record: dict | None, now: datetime | None = None) -> bool:
    """True iff `record` is a granted, non-revoked, non-expired delegation.
    Fail-closed on a malformed `expires_at`: `grant()` always writes a real
    one, so a record whose `expires_at` is present but unparseable is
    corruption, not "no expiry" — treating it as never-expiring would grant
    indefinite authority by default, exactly what this module's module
    docstring says it never does. Only a record with NO `expires_at` field
    at all (a hand-authored/legacy record `grant()` itself never produces)
    reads as unbounded."""
    if not record:
        return False
    if record.get("revoked_at"):
        return False
    raw_expires_at = record.get("expires_at")
    if raw_expires_at is None:
        return True
    expires_at = _parse_iso(raw_expires_at)
    if expires_at is None:
        return False  # present but unparseable -- fail closed, not "no expiry"
    now = now or datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now < expires_at


def grant(repo: str, scope: str, granted_by: str, expires_at: str | None = None,
          hours: float = DEFAULT_GRANT_HOURS, now: datetime | None = None,
          skill_env: str | None = "unset") -> dict:
    """Record a new standing delegation, replacing any prior one — the
    delegation is state, singular, not an appended log. `skill_env` is the
    `CLAUDE_SKILL` value of the granting session; pass the literal string
    "unset" (the default) to read the real environment, or "" / a skill
    name directly in tests. A skill-bound session can never grant its own
    standing delegation."""
    resolved_skill = os.environ.get("CLAUDE_SKILL") if skill_env == "unset" else skill_env
    if resolved_skill:
        raise SkillBoundGrantError(
            f"skill-bound session (CLAUDE_SKILL={resolved_skill!r}) may not "
            f"grant its own standing delegation — only an orchestrator "
            f"session may record one (issue #3061, mirrors issue #707's "
            f"DELEGATION-CITING APPROVE self-approval ban)")
    if not scope or not scope.strip():
        raise ValueError("delegation scope must not be empty")
    now = now or datetime.now(timezone.utc)
    if expires_at is None:
        expires_at = _now_iso(now + timedelta(hours=hours))
    record = {
        "scope": scope.strip(),
        "granted_by": granted_by,
        "granted_at": _now_iso(now),
        "expires_at": expires_at,
        "revoked_at": None,
        "revoked_by": None,
    }
    path = _state_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def revoke(repo: str, revoked_by: str, now: datetime | None = None) -> dict | None:
    """Mark the current record revoked; returns the updated record, or None
    if nothing was ever granted (revoking a delegation that doesn't exist is
    a clean no-op, not an error)."""
    record = load_state(repo)
    if record is None:
        return None
    record["revoked_at"] = _now_iso(now)
    record["revoked_by"] = revoked_by
    path = _state_path(repo)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def describe(repo: str, now: datetime | None = None) -> str:
    """Human-readable read-back — this is what `spawn.py delegation-state`
    prints with no --grant/--revoke/--audit flag. Reports cleanly when
    nothing is granted (issue #3061 acceptance's empty-state requirement)."""
    record = load_state(repo)
    if record is None:
        if _state_file_unreadable(repo):
            return (f"delegation state file exists but is unreadable/corrupt "
                     f"at {_state_path(repo)} — treating as no standing "
                     f"delegation (fail-closed, not silently equated)")
        return "no standing delegation recorded"
    if in_force(record, now):
        return (f"standing delegation IN FORCE — scope: {record.get('scope')!r}; "
                f"granted_by: {record.get('granted_by')}; "
                f"granted_at: {record.get('granted_at')}; "
                f"expires_at: {record.get('expires_at')}")
    reason = ("revoked_at: " + str(record.get("revoked_at"))
              if record.get("revoked_at") else
              "expired at: " + str(record.get("expires_at")))
    return (f"standing delegation recorded but NOT in force ({reason}) — "
            f"scope was: {record.get('scope')!r}, granted_by: "
            f"{record.get('granted_by')}, granted_at: {record.get('granted_at')}")


# --- audit mode -------------------------------------------------------
#
# High-precision, low-recall on purpose (see module docstring) — and, as of
# this repair round (issue #3061 repair, PR #3097 + PR #3102), deliberately
# narrower than the first cut shipped in PR #3087.
#
# Both independent verifications of PR #3087 found the SAME failure mode
# from different angles: a "redundant ask" pattern list built from generic
# verb constructions ("shall i", "should i proceed", bare "진행할까요") does
# not distinguish a redundant ask from a genuine escalation, because real
# escalations routinely use the exact same verbs — "Shall I roll this out
# to prod now, or hold for the nightly build?" and "이대로 갈까요?" share a
# verb, not a meaning. Six independently constructed genuine-escalation
# phrasings (irreversible actions, explicit authority language, English and
# Korean, one explicit fork) were all misclassified as redundant by that
# first cut. This is not six bugs to patch one at a time — the underlying
# claim (a keyword/verb-pattern regex can separate "redundant ask" from
# "genuine escalation" in open-ended natural language) does not hold, and
# no amount of adding negative filters for THESE six phrasings would catch
# an unseen seventh; it would only make the pattern list fit the six
# counterexamples on hand.
#
# The direction chosen instead: since the two classes are not reliably
# separable by a program under this design, `_is_redundant_ask()` now only
# matches the closed set of phrasings actually quoted (or a fixed-anchor
# bug fix of one actually quoted) in issue #3061's own transcript — never a
# generalized verb pattern invented beyond that literal set. This is a
# narrowing, not a widening: `계속 진행할까요` (the issue's literal quote)
# stays; the bare `진행할까요` stem the first cut generalized it to is
# removed, because that stem alone is exactly what flagged the adversarial
# Korean escalation case ("...진행할까요? 되돌릴 수 없는 작업이라 운영자
# 판단이 필요합니다.") as redundant. `해도 될까요` (never quoted in the
# issue) and all four English modal-verb patterns (never quoted in the
# issue — the issue's own examples are Korean) are removed for the same
# reason: they are generalizations with no grounding in an observed
# redundant ask, and every one of the six false positives came from
# exactly this kind of generalized verb match.
#
# The error direction this chooses is explicit: a redundant ask that goes
# undetected costs nothing but an uncounted audit entry; a genuine
# escalation mislabeled as redundant, in a report an operator might use to
# judge "is my orchestrator over-asking," costs the operator's trust in
# the one channel meant to say "an irreversible action was proposed and
# correctly stopped for you." Recall on redundant-ask detection is
# intentionally sacrificed for that. See
# docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c.md's
# repair-round section for the measured false-redundant / false-genuine
# rates on a held-out set built after this narrowing, not used to tune it.
#
# A turn is flagged only when it (a) ended with assistant text and no
# tool_use in the same event — the same "agent monologue" shape
# trajectory_analyzer.agent_monologue_runs() already uses for "narration
# with no observation between" — (b) that text matches one of the closed
# literal phrasings below, and (c) that text does NOT also carry a fork
# marker (named alternatives, a real either/or) — presence of a fork
# marker disqualifies the turn from being flagged even if it also matches
# (b).

_REDUNDANT_ASK_RES = [re.compile(p, re.IGNORECASE) for p in (
    r"이대로\s*갈까요",
    r"계속\s*진행할까요",
    r"이\s*순서로\s*갈까요",
    # issue #3061 repair (PR #3102 finding): the trailing `\s*$` anchor
    # required the string to end immediately after 하겠습니다 -- a plain
    # trailing period, which ordinary Korean sentences carry, broke the
    # match for the issue's own third named stopping pattern. Widened only
    # to tolerate the sentence-final punctuation that pattern's own quoted
    # example implies, not to catch new phrasings.
    r"다음은[^\n]*하겠습니다[.!?]?\s*$",
)]

_FORK_MARKER_RES = [re.compile(p, re.IGNORECASE) for p in (
    r"옵션\s*[12]|option\s*[12]|choice\s*[12]",
    r"중\s*(하나|어느)",
    r"\bwhich (of|one)\b",
    r"\beither\b.*\bor\b",
    r"trade-?off|장단점",
    r"[ab]\s*안\b|방안\s*[12]",
)]


def _turn_text_and_action(event: dict) -> tuple[str, bool]:
    blocks = (event.get("message", {}) or {}).get("content") or []
    has_tool_use = any(isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks)
    text = "\n".join(
        b.get("text", "") for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    )
    return text, has_tool_use


def _is_redundant_ask(text: str) -> bool:
    if not text:
        return False
    if any(r.search(text) for r in _FORK_MARKER_RES):
        return False
    return any(r.search(text) for r in _REDUNDANT_ASK_RES)


def _candidate_session_logs(work_dir: Path, repo_name: str, since: datetime) -> list[Path]:
    if not work_dir.exists():
        return []
    since_ts = since.timestamp()
    out = []
    for path in work_dir.glob(SESSION_LOG_GLOB):
        try:
            if path.stat().st_mtime < since_ts:
                continue
        except OSError:
            continue
        # Best-effort repo scoping: session log paths are siblings of the
        # session's own workspace directory (spawn.py's _session_log_path),
        # which has no dedicated repo-identity field to filter on — a
        # substring match on the repo's directory name is what's available,
        # not a guaranteed exact correlation. Documented, not hidden: see
        # module docstring and docs/issue-3061 record's open findings.
        if repo_name and not fnmatch.fnmatch(path.name, f"*{repo_name}*"):
            continue
        out.append(path)
    return sorted(out)


def audit(repo: str, since: str, work_dir: Path = DEFAULT_WORK_DIR,
          now: datetime | None = None) -> dict:
    """Scan session transcript logs modified since `since` (YYYY-MM-DD) for
    turns that ended by asking for authority a recorded delegation already
    covered at that turn's own timestamp. Returns
    `{"since": since, "scanned_logs": int, "count": int, "flagged": [...]}`.
    Empty-state: no logs found, or no delegation ever recorded, both report
    count 0 — there is nothing to compare a redundant ask against without a
    delegation on record."""
    since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    record = load_state(repo)
    repo_name = Path(repo).resolve().name
    logs = _candidate_session_logs(work_dir, repo_name, since_dt)
    flagged = []
    if record is not None:
        for log_path in logs:
            events = trajectory_analyzer.parse_session_log(log_path)
            for event in events:
                if event.get("type") != "assistant":
                    continue
                ts = _parse_iso(event.get("timestamp"))
                if ts is None:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < since_dt:
                    continue
                if not in_force(record, ts):
                    continue
                granted_at = _parse_iso(record.get("granted_at"))
                if granted_at is not None:
                    if granted_at.tzinfo is None:
                        granted_at = granted_at.replace(tzinfo=timezone.utc)
                    if ts < granted_at:
                        continue
                text, has_tool_use = _turn_text_and_action(event)
                if has_tool_use or not _is_redundant_ask(text):
                    continue
                flagged.append({
                    "log": str(log_path),
                    "timestamp": event.get("timestamp"),
                    "text_excerpt": text.strip()[:160],
                })
    return {"since": since, "scanned_logs": len(logs), "count": len(flagged),
            "flagged": flagged}


def format_audit(result: dict) -> str:
    header = (f"{result['count']} turn(s) since {result['since']} asked for "
              f"authority a recorded delegation already covered "
              f"(scanned {result['scanned_logs']} session log(s))")
    if result["count"] == 0:
        return header + "."
    lines = [header + ":"]
    for f in result["flagged"]:
        lines.append(f"  - {f['timestamp']}: {f['log']} — {f['text_excerpt']!r}")
    return "\n".join(lines)
