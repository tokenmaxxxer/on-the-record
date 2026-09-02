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
  decide whether to keep asking.

  Four successive rounds (PR #3097, #3102, #3107, then a repair round
  verified by PR #3122) tried to answer "was this ask redundant" by
  pattern-matching the *words* of the question, each round narrowing the
  pattern list after adversarial input broke it, and each round broken
  again the same way: a genuine escalation and a redundant ask routinely
  share a verb ("이대로 갈까요?" and a life-or-death rollback question
  both ask "shall I go ahead"), so no lexical pattern list — however
  narrow — separates them. See `docs/issue-3061/reports/` for the four
  records; the last one (PR #3122) measured a 50% false-positive rate on
  genuine escalations that merely reused a retained idiom.

  This module now classifies the orchestrator's next intended *action*
  instead — a `{tool, resource}` pair, structurally read off the tool_use
  event that actually followed the ask, not the prose of the ask itself —
  against `grant()`'s recorded `manifest`: an enumerable, structured list
  of covered actions (see the "scope manifest" section below
  `is_covered()`). Set membership replaces text inference: an action
  either matches an enumerated manifest entry or it does not, and
  anything that does not match defaults to "genuine escalation, not
  flagged" — the same err-toward-asking direction the four lexical
  rounds tried and failed to hold, now a structural property of "not
  found in the set" rather than a measured rate on whichever adversarial
  inputs happened to get tried.
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
          skill_env: str | None = "unset", manifest: list[dict] | None = None) -> dict:
    """Record a new standing delegation, replacing any prior one — the
    delegation is state, singular, not an appended log. `skill_env` is the
    `CLAUDE_SKILL` value of the granting session; pass the literal string
    "unset" (the default) to read the real environment, or "" / a skill
    name directly in tests. A skill-bound session can never grant its own
    standing delegation.

    `scope` stays a free-text human label (unchanged from before this
    module's manifest repair) — it is what `describe()` prints for a
    person to read, and it is intentionally NOT what `audit()` classifies
    against anymore. `manifest` is the new, separate, structured field:
    a list of `{"tool", "resource", "repo"}` entries (see `is_covered()`'s
    docstring for the exact matching rule) naming the actions this grant
    actually covers. Omitting it (the default) stores an EMPTY manifest,
    not a permissive one — a grant with no `manifest` entries covers
    nothing, and every action still escalates until entries are added.
    This is a deliberate, stated boundary, not an oversight: bridging an
    operator's free-text "쭉 해" into a manifest that covers something
    without inventing an unrequested guess at what they meant is an open
    question this module does not resolve on its own (see the module
    docstring's manifest section and this module's own issue #3061 record
    for the reasoning); `spawn.py delegation-state --grant --allow
    TOOL:RESOURCE-GLOB[:REPO-GLOB]` (`parse_allow_spec()` below) is the
    non-JSON authoring surface for populating it explicitly."""
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
        "manifest": list(manifest) if manifest else [],
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


def _describe_manifest(manifest: list[dict] | None) -> str:
    entries = manifest or []
    if not entries:
        return "manifest: 0 action(s) — every action still escalates until entries are added"
    parts = ", ".join(
        f"{e.get('tool')}:{e.get('resource')!r}(repo:{e.get('repo', '*')})"
        for e in entries)
    return f"manifest: {len(entries)} action(s) — {parts}"


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
                f"expires_at: {record.get('expires_at')}; "
                f"{_describe_manifest(record.get('manifest'))}")
    reason = ("revoked_at: " + str(record.get("revoked_at"))
              if record.get("revoked_at") else
              "expired at: " + str(record.get("expires_at")))
    return (f"standing delegation recorded but NOT in force ({reason}) — "
            f"scope was: {record.get('scope')!r}, granted_by: "
            f"{record.get('granted_by')}, granted_at: {record.get('granted_at')}")


# --- scope manifest ---------------------------------------------------
#
# Four successive rounds tried to answer "was this ask redundant" by
# pattern-matching the WORDS of the question the orchestrator asked (PR
# #3087's first cut, then narrowings verified by PR #3097, #3102, #3107,
# then a repair round verified by PR #3122). All four were graded
# Incorrect against the issue's own must-not clause, each time the same
# way: a genuine escalation and a redundant ask routinely use the exact
# same verb — "이대로 갈까요?" and "이 마이그레이션은 롤백이 불가능합니다.
# 계속 진행할까요?" share a verb, not a meaning — so no lexical pattern
# list, however narrow, separates them; PR #3122's independent
# verification measured a 50% false-positive rate on genuine escalations
# built to reuse a retained idiom, after the surface area had already
# been narrowed from 10 patterns to 4. Full history in
# docs/issue-3061/reports/ (four records) plus the consult that
# recommended this redesign, logged in the issue's own comment thread.
#
# The redesign: stop classifying the SENTENCE and start classifying the
# ACTION. `is_covered()` below is a set-membership lookup — a `{tool,
# resource}` action either matches an entry in the operator's recorded
# `manifest` or it does not; there is no inference step to get wrong.
# "Not enumerated" defaults to "genuine escalation" structurally, not as
# a measured rate on whichever adversarial inputs happened to get tried
# — which is exactly the property four lexical rounds tried and failed
# to hold as a property of a pattern list.
#
# `audit()` still scans historical session transcripts for a turn that
# stopped to ask (assistant text, no tool_use in that same event — the
# one part of the old design that was always structural fact, not
# lexical inference, and stays unchanged). What changed is what it
# checks that stop against: not the text of the question, but the
# {tool, resource} of the tool_use event that actually followed it in
# the same transcript — i.e. what the orchestrator went on to do next,
# whether because the operator answered or because nothing blocked it.
# If that next action is in the recorded manifest, the delegation
# already covered it and the stop was avoidable (flagged). If it is not
# — including when there is no next tool_use event to look at at all —
# `audit()` cannot establish that the stop was avoidable, and the safe
# default (issue #3061's own err-toward-asking direction) is to not
# flag it, the same direction the four retired lexical rounds were
# aiming for and structurally missing.
#
# Manifest entry shape: `{"tool": <tool_use event's "name">, "resource":
# <fnmatch glob against the extracted resource string>, "repo": <fnmatch
# glob against the repo name, default "*">}`. `tool` is an exact match
# (a tool name is already a small closed set — "Bash", "Edit", "Write",
# ... — glob-matching it would only reintroduce the same
# unanchored-substring risk the lexical classifier had); `resource` and
# `repo` are globs because the values they match (shell commands, file
# paths, repo directory names) are open-ended strings a human names
# approximately, e.g. "git *" or "gh pr *".
#
# Threshold dimensions: `repo` is the one this delivery actually wires
# (every action already happens inside a `--repo` context, matching
# `grant()`/`audit()`'s own `repo` parameter). "spend" (a metered cost
# limit) and "blast radius" (e.g. a max file/target count per action)
# would follow the identical mechanism — one more glob-or-bound key on
# a manifest entry, checked the same way — but neither has a signal to
# check against today: a `tool_use` event carries no cost figure, and no
# other module in this repo computes a blast-radius number this one
# could read. Adding either now would be an unused threshold type with
# nothing to validate it against — the anti-pattern this repo's own
# `implementation-blueprint` skill calls speculative-generality — so
# this delivery leaves them named here as the documented extension
# point, not built.
#
# Authoring without hand-written JSON: `spawn.py delegation-state
# --grant SCOPE --allow TOOL:RESOURCE-GLOB[:REPO-GLOB]` (repeatable)
# builds the manifest for you via `parse_allow_spec()` below. Omitting
# `--allow` entirely grants a delegation with an EMPTY manifest — not a
# permissive one. This is the fix's stated cost, not an oversight: it
# pushes the structuring burden onto whoever authors the grant. An
# operator who says "쭉 해" with no `--allow` flags gets a delegation
# that is machine-visible and revocable (R1) but covers zero actions
# (R2) until entries are added — bridging free-text delegation into a
# manifest that covers something, without this module guessing at an
# unstated intent, is named as open work in this delivery's record
# rather than solved by inventing a default allowlist here.


_ACTION_RESOURCE_FIELDS = ("command", "file_path", "path", "url", "description")


def is_covered(action: dict, manifest: list[dict] | None, repo: str | None = None) -> bool:
    """True iff `action` (`{"tool": str, "resource": str}`) matches at
    least one entry of `manifest`. Set membership, not inference: `tool`
    must match an entry's `tool` exactly; `resource` must match that
    entry's `resource` glob (`fnmatch`); when both `repo` and the entry's
    `repo` (default `"*"`) are given, `repo` must also match that glob.
    An action matching no entry returns False — the manifest enumerates
    what is delegated, and anything outside that enumeration is a
    genuine escalation by construction, never a guess."""
    for entry in manifest or []:
        if entry.get("tool") != action.get("tool"):
            continue
        if not fnmatch.fnmatch(action.get("resource") or "", entry.get("resource") or "*"):
            continue
        entry_repo = entry.get("repo") or "*"
        if repo is not None and not fnmatch.fnmatch(repo, entry_repo):
            continue
        return True
    return False


def parse_allow_spec(spec: str) -> dict:
    """Parse one `--allow` CLI value into a manifest entry — the
    non-JSON authoring surface `grant()`'s docstring points to. Syntax:
    `TOOL:RESOURCE-GLOB[:REPO-GLOB]`, e.g. `Bash:git *` or
    `Bash:gh pr *:on-the-record` (REPO-GLOB defaults to `"*"`, any
    repo). Raises ValueError on a spec missing its required TOOL or
    RESOURCE part — a malformed `--allow` value fails the grant loudly
    at authoring time; it never silently drops to an emptier manifest
    without saying so. Known limitation: a colon inside RESOURCE itself
    (e.g. a URL glob) is ambiguous with the `:`-delimited grammar and
    will split wrong — author such an entry as JSON directly via
    `grant(..., manifest=[...])` instead of `--allow`."""
    parts = spec.split(":", 2)
    if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(
            f"malformed --allow spec {spec!r} — expected "
            f"'TOOL:RESOURCE-GLOB[:REPO-GLOB]', e.g. 'Bash:git *'")
    tool, resource = parts[0].strip(), parts[1].strip()
    repo_glob = parts[2].strip() if len(parts) == 3 and parts[2].strip() else "*"
    return {"tool": tool, "resource": resource, "repo": repo_glob}


def _extract_action(tool_use: dict) -> dict:
    """Turn one `trajectory_analyzer.tool_use_events()` entry into the
    `{"tool", "resource"}` shape `is_covered()` matches against.
    `resource` is read from the first populated field among
    `_ACTION_RESOURCE_FIELDS` in the tool's `input` (`command` covers
    Bash — the dominant case in practice, since `git`/`gh` calls are
    shell commands; `file_path`/`path` cover Edit/Write/Read; `url` and
    `description` are generic fallbacks for other tools). A tool shape
    this list does not recognize still gets a real (non-empty) resource
    string — the input dict, JSON-serialized — rather than an empty
    one, so it can never accidentally glob-match a wildcard entry meant
    for a different tool's resource."""
    inp = tool_use.get("input") or {}
    resource = None
    for field in _ACTION_RESOURCE_FIELDS:
        value = inp.get(field)
        if isinstance(value, str) and value:
            resource = value
            break
    if resource is None:
        resource = json.dumps(inp, sort_keys=True, ensure_ascii=False) if inp else ""
    return {"tool": tool_use.get("name") or "", "resource": resource}


def _turn_text_and_action(event: dict) -> tuple[str, bool]:
    blocks = (event.get("message", {}) or {}).get("content") or []
    has_tool_use = any(isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks)
    text = "\n".join(
        b.get("text", "") for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    )
    return text, has_tool_use


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
    turns that stopped to ask when the actual next action they took was
    already covered by the recorded delegation's manifest. Returns
    `{"since": since, "scanned_logs": int, "count": int, "flagged": [...]}`.
    Empty-state: no logs found, or no delegation ever recorded, both report
    count 0 — there is nothing to compare a stop-then-continue against
    without a delegation on record.

    A turn is a flaggable candidate when it (a) ended with assistant text
    and no `tool_use` in that same event (the structural "stopped instead
    of acting" shape) and (b) the delegation was in force at that turn's
    own timestamp. It is actually FLAGGED only when the next `tool_use`
    event anywhere later in the same transcript resolves to an action
    `is_covered()` by the recorded manifest — i.e. what the orchestrator
    went on to do next was something the standing delegation already
    authorized, so the stop was avoidable. When there is no later
    `tool_use` event to check at all (the log ends at the ask, or nothing
    the manifest covers followed), this cannot establish that the stop
    was avoidable and it is NOT flagged — the same fail-closed direction
    `in_force()`/`load_state()` already use elsewhere in this module."""
    since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    record = load_state(repo)
    repo_name = Path(repo).resolve().name
    logs = _candidate_session_logs(work_dir, repo_name, since_dt)
    flagged = []
    if record is not None:
        manifest = record.get("manifest") or []
        for log_path in logs:
            events = trajectory_analyzer.parse_session_log(log_path)
            tool_uses = trajectory_analyzer.tool_use_events(events)
            for event_index, event in enumerate(events):
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
                if has_tool_use or not text.strip():
                    continue
                next_tool_use = next(
                    (tu for tu in tool_uses if tu["index"] > event_index), None)
                if next_tool_use is None:
                    continue
                action = _extract_action(next_tool_use)
                if not is_covered(action, manifest, repo=repo_name):
                    continue
                flagged.append({
                    "log": str(log_path),
                    "timestamp": event.get("timestamp"),
                    "text_excerpt": text.strip()[:160],
                    "next_action": action,
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
        action = f.get("next_action") or {}
        lines.append(
            f"  - {f['timestamp']}: {f['log']} — {f['text_excerpt']!r} "
            f"(next action {action.get('tool')}:{action.get('resource')!r} "
            f"already in the manifest)")
    return "\n".join(lines)
