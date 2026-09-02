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
import sys
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


class MalformedManifestError(ValueError):
    """Raised internally when a `manifest` value is not shaped as
    `list[dict]` with string-typed `tool`/`resource`/`repo` fields —
    never surfaces past this module's read-path boundary as a raw
    exception. `is_covered()`, `_describe_manifest()`, and `audit()`
    each catch it and fail closed to "covers nothing" (the same
    direction an absent or empty manifest already takes), printing a
    diagnostic to stderr so the malformed state is visible rather than
    silently swallowed. `grant()` is the one place this is allowed to
    propagate: a malformed `manifest=` argument is an authoring-time
    bug and must fail loudly, the same standard `parse_allow_spec()`
    already holds itself to for a malformed `--allow` spec — never
    silently degrade to storing a broken record that every later read
    then has to fail closed against."""


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
    # Validated, not just coerced: `list(manifest)` on a bare string used
    # to silently explode it into one entry per character (issue #3061
    # round-4 verification, PR #3192 Q4) and write that to disk, where
    # every later read would then have to fail closed against it. A
    # malformed `manifest=` argument is an authoring-time bug and fails
    # loudly here, the same standard `parse_allow_spec()` already holds
    # itself to for a malformed `--allow` spec.
    validated_manifest = _validate_manifest(manifest)
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
        "manifest": validated_manifest,
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


def _is_utf8_safe(value: str) -> bool:
    """True iff `value` round-trips through UTF-8 encoding. A lone
    Unicode surrogate (issue #3061 round-5 verification, PR #3201 hole
    2) passes `isinstance(value, str)` -- it is a normal Python string
    -- but raises `UnicodeEncodeError` the moment anything tries to
    write it as UTF-8 bytes, which is exactly what `grant()`'s
    `path.write_text(..., encoding="utf-8")` does. Checking this at
    validation time turns that late, uncaught crash at the disk-write
    step into an early, loud `MalformedManifestError` here -- the same
    standard this module already holds a wrong-type field to."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


# issue #3061 round-7 verification (PR #3212, 8th independent pass): the
# walk below reached every position round 6 named, but was not robust to
# its OWN input shape rather than the string content it was looking for.
# A self-referential dict/list, or a cycle through two containers, sent
# it into infinite recursion -- an uncaught RecursionError, not a
# reported rejection. Plain deep-but-acyclic nesting past Python's
# default recursion limit did the same, because nothing bounded the
# walk's depth explicitly; it only "worked" by accident when a surrogate
# happened to be found before the stack ran out. And the walk had no
# opinion on any value that was neither a string nor a container -- a
# `bytes` or `set` field passed through silently and reached `grant()`'s
# `json.dumps()` at the disk-write step, an uncaught TypeError there
# rather than an early MalformedManifestError here. All three are the
# same failure class hole 2 already exists to prevent: a validator that
# crashes on its input has not validated anything, it has just moved the
# crash a few frames later. Fixed by making every dimension the walk can
# fail on an explicit, reported check instead of an assumption:
#
# - Cycles: `_MANIFEST_MAX_DEPTH` alone does not catch a cycle through a
#   SHARED sub-container at the same depth on every hop (e.g. two dicts
#   that reference each other) as anything other than "still descending"
#   -- it would eventually trip the depth bound, but only after wasting
#   `_MANIFEST_MAX_DEPTH` frames, and it would misreport a real cycle as
#   "too deep" rather than name it as a cycle. `visiting` tracks the
#   `id()` of every dict/list currently open on the CURRENT recursion
#   path (not every container ever seen -- the same sub-list legitimately
#   appearing twice as sibling values, e.g. a shared default, is not a
#   cycle) and is checked before descending into a container, so a
#   self-reference or a two-container cycle is caught in O(1) the moment
#   it recurs, before depth or the real Python stack are ever at risk.
#   `id()` identity, never `==`, is what avoids re-entering a hostile
#   value's own `__eq__`/`__hash__`.
# - Depth: `_MANIFEST_MAX_DEPTH` bounds the walk's own recursion
#   explicitly, independent of `sys.getrecursionlimit()` (which this
#   walk does not control and must not rely on) -- exceeding it raises
#   `MalformedManifestError` instead of running the walk into
#   `RecursionError` territory. The bound is far above any realistic
#   manifest's nesting (a handful of levels under `tool`/`resource`/
#   `repo`/an optional `meta`-shaped extra field) and far below the
#   interpreter's default recursion limit (1000), leaving headroom for
#   whatever stack depth the caller already has in play.
# - Value types: manifest values are written to disk as JSON and read
#   back with `json.loads()`, so the allowlist is not "everything
#   `json.dumps()` can turn into bytes without raising" -- it is the
#   narrower set of Python types a save-then-load round trip hands back
#   as the SAME type it started as: `str`, `int`, `float`, `bool`,
#   `None`, and the two containers `dict`/`list`. That set is now
#   enumerated POSITIVELY and enforced at validation time -- anything
#   else (`bytes`, `set`, a custom object, anything) is invalid here,
#   not a surprise `TypeError` at `grant()`'s write step.
#
#   `tuple` is the case this distinction exists for (issue #3061 round-8
#   verification, PR #3216, ninth pass). `json.dumps()` accepts a tuple
#   value without complaint -- it serializes as a JSON array, same as a
#   list -- so "can `json.dumps()` write it" alone would admit it. But
#   `json.loads()` never reconstructs a tuple; every array it reads back
#   is a `list`. A manifest entry holding a tuple in memory (e.g. what
#   `grant()` returns before it ever touches disk) would compare unequal
#   (`(1, 2) != [1, 2]`) to the very same entry read back via
#   `load_state()`, even though the two hold identical data -- a value
#   that silently changes Python type across a save and load is exactly
#   the kind of trap this validator exists to catch at authoring time,
#   not leave to surface later as an unexplained equality failure
#   somewhere a caller compares a granted manifest against a reloaded
#   one. So `tuple` is excluded on purpose, not by omission: `dict` and
#   `list` are the containers that round-trip stably, and those are the
#   only two admitted.
#
#   The same round-trip-stability standard applies to dict KEYS: JSON
#   object keys are always strings on read-back regardless of what was
#   written, so a non-string key (which would otherwise reach
#   `json.dumps()` and either silently stringify in ways nothing here
#   validated, or raise for a key type `json.dumps` refuses outright,
#   e.g. a tuple key) is rejected here too.
_MANIFEST_MAX_DEPTH = 64


def _check_no_surrogates(value, path: str, _depth: int = 0,
                          _visiting: frozenset = frozenset()) -> None:
    """Recursively walk `value` -- every dict key, every dict value, every
    list element, at every depth -- and raise `MalformedManifestError` the
    moment it finds: a string that fails `_is_utf8_safe()`; a container
    cycle (direct or through another container); nesting past
    `_MANIFEST_MAX_DEPTH`; or a value/key of any type outside the set
    that round-trips through a `json.dumps()`/`json.loads()` save-and-load
    as the same Python type it started as -- narrower than "everything
    `json.dumps()` can write without raising" (a `tuple` value clears that
    bar but is still rejected; see the module-level comment above this
    function for why). Every one of these is a reported rejection here,
    never a crash later.

    issue #3061 round-6 verification (PR #3207 hole 2): checking only the
    three named fields (`tool`/`resource`/`repo`) left every OTHER string
    a manifest entry can carry unchecked -- an unlisted key's value, a
    surrogate used as a dict key, or a surrogate nested inside a
    structure under a non-named field all still reached `grant()`'s
    `path.write_text(..., encoding="utf-8")` uncaught, and worse, since
    `write_text()` truncates the target file before the encode error
    fires, this destroyed any pre-existing valid delegation state in the
    process. A manifest entry is allowed to carry keys beyond `tool`/
    `resource`/`repo` (this module does not enumerate what a caller may
    attach) and those extra values are allowed to be arbitrary nested
    JSON-shaped structures -- so this walks the WHOLE structure, not just
    the three named fields."""
    if _depth > _MANIFEST_MAX_DEPTH:
        raise MalformedManifestError(
            f"{path} nests deeper than the maximum manifest depth of "
            f"{_MANIFEST_MAX_DEPTH} levels")
    if isinstance(value, (dict, list)):
        vid = id(value)
        if vid in _visiting:
            raise MalformedManifestError(
                f"{path} contains a cycle -- a container that refers "
                f"back to itself, directly or through another container")
        _visiting = _visiting | {vid}
        if isinstance(value, dict):
            for key, sub_value in value.items():
                if not isinstance(key, str):
                    raise MalformedManifestError(
                        f"{path} has a dict key of type "
                        f"{type(key).__name__}, not a string")
                if not _is_utf8_safe(key):
                    raise MalformedManifestError(
                        f"{path} has a dict key that cannot round-trip "
                        f"through UTF-8 encoding (e.g. a lone Unicode "
                        f"surrogate)")
                _check_no_surrogates(sub_value, f"{path}[{key!r}]",
                                     _depth + 1, _visiting)
        else:
            for i, item in enumerate(value):
                _check_no_surrogates(item, f"{path}[{i}]", _depth + 1,
                                     _visiting)
    elif isinstance(value, str):
        if not _is_utf8_safe(value):
            raise MalformedManifestError(
                f"{path} contains a character that cannot round-trip "
                f"through UTF-8 encoding (e.g. a lone Unicode surrogate)")
    elif isinstance(value, (int, float, bool)) or value is None:
        pass  # JSON-representable scalar leaves -- allowed as-is
    else:
        raise MalformedManifestError(
            f"{path} is a {type(value).__name__}, which is not a type a "
            f"manifest value may be (allowed: string, number, boolean, "
            f"null, object, array)")


def _validate_manifest_entry(entry, index: int) -> dict:
    if not isinstance(entry, dict):
        raise MalformedManifestError(
            f"manifest entry {index} is a {type(entry).__name__}, not an object")
    for key in ("tool", "resource", "repo"):
        if key not in entry or entry[key] is None:
            continue
        if not isinstance(entry[key], str):
            raise MalformedManifestError(
                f"manifest entry {index} field {key!r} is a "
                f"{type(entry[key]).__name__}, not a string")
    # Structural checks above cover the three named fields' TYPES; this
    # recursive sweep covers UTF-8 safety, cycle-freedom, depth, and
    # value/key types for everything anywhere in the entry -- named
    # field, unlisted key, dict key, or nested inside a structure under a
    # non-named field (issue #3061 round-6 verification, PR #3207 hole
    # 2; round-7 verification, PR #3212, added the cycle/depth/type
    # checks). `_check_no_surrogates` bounds its own recursion via
    # `_MANIFEST_MAX_DEPTH` and cannot legitimately raise
    # `RecursionError` -- the wrapper below is defense in depth only, so
    # that even an unforeseen pathological shape fails closed as a
    # reported `MalformedManifestError` here rather than an uncaught
    # crash, holding the same "no crash, ever" standard this module
    # holds itself to everywhere else.
    try:
        _check_no_surrogates(entry, f"manifest entry {index}")
    except RecursionError:
        raise MalformedManifestError(
            f"manifest entry {index} is nested too deeply to validate")
    return entry


def _validate_manifest(manifest) -> list[dict]:
    """Returns `manifest` as a validated `list[dict]`, or raises
    `MalformedManifestError`. `None` and `[]` are both valid — "no
    manifest" and "empty manifest" already mean "covers nothing" — only
    a manifest that is present but not shaped as list-of-string-keyed-
    objects is malformed: a non-list value (a bare string, a dict, an
    int), a list containing a non-dict entry (a string, `None`, a
    nested list), or an entry whose `tool`/`resource`/`repo` field holds
    something other than a string (a nested dict or list one level too
    deep) all raise here rather than reaching a `.get()` call on the
    wrong type further down."""
    if manifest is None:
        return []
    if not isinstance(manifest, list):
        raise MalformedManifestError(
            f"manifest is a {type(manifest).__name__}, not a list")
    return [_validate_manifest_entry(e, i) for i, e in enumerate(manifest)]


def _safe_manifest(manifest, context: str) -> list[dict]:
    """Read-path wrapper around `_validate_manifest()`: never raises,
    fails closed to an empty (covers-nothing) manifest, and says so on
    stderr so a malformed on-disk record is visible instead of silently
    read as "nothing was ever granted"."""
    try:
        return _validate_manifest(manifest)
    except MalformedManifestError as exc:
        print(f"delegation_state: malformed manifest ({exc}) in {context} — "
              f"treating as 0 covered actions (fail-closed, same direction "
              f"as no manifest / an empty manifest)", file=sys.stderr)
        return []


def _describe_manifest(manifest: list[dict] | None) -> str:
    entries = _safe_manifest(manifest, "describe()")
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

# issue #3061 round-4 verification (PR #3192, Q2): a trailing-wildcard
# manifest entry -- this module's own recommended authoring idiom, e.g.
# "git *" -- matched as a bare fnmatch glob against the WHOLE resource
# string, with no awareness that a shell reads that string as more than
# one command. "git log --oneline && rm -rf /var/lib/postgres" glob-
# matches "git *" because fnmatch has no concept of "&&"; the wildcard
# entry ends up silently authorizing a second, unrelated, unauthorized
# command chained onto the first.
#
# Two honest fixes were on the table: (a) refuse to match a command
# containing a shell operator against a WILDCARD entry at all, or (b)
# split the command on its operators and require every segment to be
# independently covered. (b) needs a real shell tokenizer to split
# correctly across quoting, nested "$(...)"/backtick substitution, and
# heredocs -- getting that parser slightly wrong reintroduces exactly
# this bug class in a new shape (the same lesson four rounds of lexical
# classifier already taught this issue: a hand-written text heuristic
# is never the fail-closed side to bet on). (a) needs no parser: it
# only needs to recognize that a shell operator is PRESENT, not to
# understand the structure around it, so it fails closed by construction
# rather than by care. This module takes (a).
#
# Cost to an author: a manifest entry using a wildcard glob only ever
# covers a single, non-chained command. An author who legitimately wants
# a specific chained command covered (e.g. "git fetch && git rebase
# origin/main") must enumerate that exact compound string as its own
# manifest entry with no wildcard in it -- a literal, non-glob `resource`
# value still matches via plain equality (see below), because that is an
# explicit, single enumerated action, not a class of actions inferred
# from a prefix. It does not generalize: a slightly different chain needs
# its own entry. That is the fix's stated cost, the same shape as
# `parse_allow_spec()`'s own documented colon-ambiguity limitation.
#
# issue #3061 round-5 verification (PR #3201 hole 1): the token list
# below used to be the WHOLE test -- "does `resource` contain one of
# these known operator substrings" -- and it has now failed by omission
# twice for the identical reason: it named `;`, `|`, `&`, a backtick,
# `$(`, `<<`, but never named `\n` or `\r`, so `"git status\nrm -rf /"`
# glob-matched a bare `"git *"` wildcard entry via `fnmatch`'s DOTALL
# `*` and silently authorized the second, unenumerated command. Adding
# `\n`/`\r` to the tuple would only re-narrow this to the SAME
# omission-by-enumeration failure mode against the next control or
# separator character nobody thought to list (a vertical tab, a form
# feed, a NUL byte, a Unicode line/paragraph separator -- none of which
# are shell operators in the traditional sense, but all of which a
# multi-line-aware consumer downstream of this string could read as a
# second line). A blacklist can only ever be as complete as whoever
# wrote it remembered to be.
#
# The fix flips the direction: `_is_provably_single_command()` below
# stops asking "is a known-bad substring present" and asks "is every
# character in this string one this module can PROVE belongs to a
# single command line" -- `str.isprintable()` is the built-in,
# Unicode-database-driven answer to that for the control/separator
# half (it is False for every C0/C1 control character, every Unicode
# line/paragraph separator, and every non-ASCII space separator, by
# Unicode category, not by enumeration -- a newly assigned separator
# codepoint is caught automatically, the same way an already-known one
# is). The enumerated operator tokens still name the actual multi-
# character shell chaining SYNTAX (`&&`, `||`, `` ` ``, `$(`, `<<`) --
# that half is not "control characters nobody thought to list", it is
# a small, closed, semantically necessary set of shell grammar this
# module deliberately still recognizes by name, same as before. Fail-
# closed direction is unchanged: anything not provably a single
# command still never matches a wildcard entry.
_SHELL_OPERATOR_TOKENS = (";", "|", "&", "`", "$(", "<<")


def _is_provably_single_command(resource: str) -> bool:
    """True iff `resource` can be established as a single, non-chained
    shell command -- i.e. it is safe to match against a WILDCARD
    manifest entry. False (not provably single) whenever `resource`
    contains a known shell-chaining operator token (see
    `_SHELL_OPERATOR_TOKENS`) OR any non-printable character --
    `str.isprintable()` is False for control characters (`\\n`, `\\r`,
    `\\0`, vertical tab, form feed, ...), Unicode line/paragraph
    separators, and non-ASCII space separators, covering that entire
    class by Unicode category rather than by an enumerable, and
    historically incomplete, token list (issue #3061 round-5
    verification, PR #3201 hole 1). Presence-only for the operator
    tokens, not a parse: a resource string that merely contains one of
    these characters inside quoted data (rare, and the false-positive
    direction is "escalate a command that didn't actually need it") is
    treated the same as a real chain -- fail closed, never fail open."""
    if not resource.isprintable():
        return False
    return not any(token in resource for token in _SHELL_OPERATOR_TOKENS)


def _is_glob_pattern(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def is_covered(action: dict, manifest: list[dict] | None, repo: str | None = None) -> bool:
    """True iff `action` (`{"tool": str, "resource": str}`) matches at
    least one entry of `manifest`. Set membership, not inference: `tool`
    must match an entry's `tool` exactly; `resource` must match that
    entry's `resource` glob (`fnmatch`) -- UNLESS `action`'s resource is
    not provably a single, non-chained shell command (see
    `_is_provably_single_command()`) and the entry's `resource` is a
    wildcard glob, in which case the match is refused regardless of
    whether the glob would otherwise hit, so a grant for one command can
    never authorize a second command chained onto it; when both `repo`
    and the entry's `repo` (default `"*"`) are given, `repo` must also
    match that glob. An entry with no `resource` value at all never
    matches anything -- a manifest entry missing its `resource` key is
    incomplete authoring, not an implicit wildcard, and must not
    silently cover everything for its `tool`. A malformed `manifest`
    (wrong shape, not list[dict] with string fields) fails closed to
    "nothing covered" and says so on stderr, the same direction an
    absent or empty manifest already takes. An action matching no entry
    returns False — the manifest enumerates what is delegated, and
    anything outside that enumeration is a genuine escalation by
    construction, never a guess."""
    entries = _safe_manifest(manifest, "is_covered()")
    action_resource = action.get("resource") or ""
    action_is_compound = not _is_provably_single_command(action_resource)
    for entry in entries:
        if entry.get("tool") != action.get("tool"):
            continue
        entry_resource = entry.get("resource")
        if not entry_resource:
            continue  # missing/empty resource is incomplete authoring, never an implicit "*"
        if action_is_compound and _is_glob_pattern(entry_resource):
            continue  # a wildcard entry may not authorize a chained command
        if not fnmatch.fnmatch(action_resource, entry_resource):
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


def _episode_tool_uses(events: list[dict], tool_uses: list[dict], event_index: int) -> list[dict]:
    """Every `tool_use` event between this ask (`event_index`) and either
    the next ask-shaped stop (another assistant event with text and no
    tool_use) or the end of the transcript.

    issue #3061 round-4 verification (PR #3192, Q5): the transcript
    format carries no field correlating a specific `tool_use` event to
    the ask that prompted it -- no parent/reply id, nothing but stream
    order. Picking "the very next tool_use event" (what this function's
    predecessor did) is therefore a proxy for "the action this ask was
    about," not a real binding, and an ordinary intervening action (a
    `git log` sanity check while waiting on guidance) that happens to be
    individually covered can stand in for a later, genuinely uncovered
    action that never gets checked -- a real, irreversible escalation
    misclassified as redundant via temporal misattribution instead of
    lexical matching. No positional heuristic fixes this: restricting to
    "the very next raw event" doesn't help, because the confounding
    action in that failure mode already IS the very next event.

    What IS honestly available from stream order alone is the full
    stretch of what the orchestrator did in this episode -- everything
    up to the next stop or the end of the log. `audit()` uses this
    (`all(...)` over the whole stretch, not just its first entry) rather
    than asserting a single-action binding it cannot actually prove:
    only when EVERY action taken during the stretch was already covered
    can the stop be called avoidable with any confidence; a single
    uncovered action anywhere in the stretch means audit() cannot rule
    out that action being what the ask was actually about, and reports
    uncertain (not flagged) instead of guessing."""
    boundary = _episode_boundary(events, event_index)
    return [tu for tu in tool_uses if event_index < tu["index"] < boundary]


def _episode_boundary(events: list[dict], event_index: int) -> int:
    """Index of the next ask-shaped stop after `event_index`, or
    `len(events)` if none is found before the transcript runs out --
    the same boundary `_episode_tool_uses()` uses, exposed separately
    so `audit()` can tell "this episode ended at a real next ask" from
    "this episode ran off the end of THIS transcript," which by itself
    is ambiguous between "the session genuinely finished here" and "the
    log was truncated mid-episode" (issue #3061 round-5 verification,
    PR #3201 hole 3) -- `audit()` resolves that ambiguity separately,
    against `trajectory_analyzer.final_result_event()`."""
    for i in range(event_index + 1, len(events)):
        ev = events[i]
        if ev.get("type") != "assistant":
            continue
        text, has_tool_use = _turn_text_and_action(ev)
        if not has_tool_use and text.strip():
            return i
    return len(events)


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
    `{"since": since, "scanned_logs": int, "count": int, "flagged": [...],
    "indeterminate": [...]}`. Empty-state: no logs found, or no delegation
    ever recorded, both report count 0 — there is nothing to compare a
    stop-then-continue against without a delegation on record.

    A turn is a flaggable candidate when it (a) ended with assistant text
    and no `tool_use` in that same event (the structural "stopped instead
    of acting" shape) and (b) the delegation was in force at that turn's
    own timestamp. It is actually FLAGGED only when EVERY `tool_use`
    event in this episode -- the whole stretch between this ask and the
    next ask-shaped stop or the end of the transcript, not just the
    first action taken -- resolves to an action `is_covered()` by the
    recorded manifest (see `_episode_tool_uses()`'s docstring for why a
    single-next-action binding is not something this transcript format
    can actually prove). When even one action in the episode is NOT
    covered, this cannot establish that the stop was avoidable and it is
    NOT flagged — the same fail-closed direction `in_force()`/
    `load_state()` already use elsewhere in this module. A malformed
    `manifest` on the loaded record fails closed to "covers nothing"
    (reported on stderr) rather than crashing the scan.

    issue #3061 round-5 verification (PR #3201 hole 3): an episode whose
    stretch runs all the way to the end of the events this log actually
    contains -- no next ask-shaped stop was found before the transcript
    ran out -- is genuinely ambiguous by itself: it is what a normally-
    finished session's LAST episode also looks like. Distinguishing them
    needs a signal beyond "did I find a next ask," so this checks
    whether the log reached `trajectory_analyzer`'s terminal `result`
    event at all (absent on a still-running, crashed, or truncated log,
    per that function's own docstring -- and also absent when the
    would-be terminal event itself was a partial JSON line cut off
    mid-write, since `parse_session_log()` already drops an unparseable
    trailing line rather than raising). When that boundary-reaches-EOF
    episode's log never reached a terminal `result` event, `audit()`
    cannot rule out that more of the episode was cut off before it could
    be recorded -- covered actions seen so far are not the whole
    picture, and an uncovered one that never got logged is exactly as
    plausible as it is for any other unseen action. That episode is
    reported INDETERMINATE, never flagged, regardless of whether the
    visible portion happens to look fully covered -- the same shape of
    silent failure this whole module exists to stop happening to a
    live turn, now caught in audit()'s own retrospective read of a
    truncated log instead of quietly presenting it as an ordinary
    "clean" (flagged-or-not) episode.

    issue #3061 round-6 verification (PR #3207 hole 3): round 5's fix
    above computed "did the log reach completion" ONCE per log file --
    "does a terminal `result` event exist anywhere in this log" -- and
    only consulted that single flag for the one episode whose boundary
    ran off the end of the transcript. A log can genuinely carry more
    than one `result` event (each completed turn/episode gets its own),
    and that per-LOG flag going True because an EARLIER episode
    completed said nothing about whether a LATER episode -- including
    one bounded by a real next ask, not just one running off the end --
    ever reached its own. Two failure shapes followed: a log whose
    earlier episodes completed normally but whose last one was cut off
    still read as globally "reached completion" and the last episode was
    flagged as clean; and a middle episode that was itself cut off (the
    process died mid-episode, before writing that episode's own `result`
    event, then something later re-appended further events to the same
    log path) was never even considered for the ambiguity check at all,
    because only the final, boundary-reaches-EOF episode was ever
    checked.

    The fix: completion is now a per-EPISODE fact, not a per-log one, and
    every episode audit() reports on is checked, not just the last.
    `result_indices` below is every `result` event's index in the whole
    log; an episode (whatever its own boundary) is known-complete only
    if at least one of those indices falls strictly inside ITS OWN
    stretch (`event_index < ri < boundary`). An episode with no `result`
    event in its own stretch is reported INDETERMINATE regardless of
    whether its boundary was a genuinely-found next ask or the end of
    the transcript -- finding a next ask proves the log kept being
    written to, not that THIS episode's own turn ever reached a
    completion marker before that later writing happened."""
    since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    record = load_state(repo)
    repo_name = Path(repo).resolve().name
    logs = _candidate_session_logs(work_dir, repo_name, since_dt)
    flagged = []
    indeterminate = []
    if record is not None:
        manifest = _safe_manifest(record.get("manifest"), "audit()")
        for log_path in logs:
            events = trajectory_analyzer.parse_session_log(log_path)
            tool_uses = trajectory_analyzer.tool_use_events(events)
            result_indices = [i for i, ev in enumerate(events) if ev.get("type") == "result"]
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
                boundary = _episode_boundary(events, event_index)
                episode = [tu for tu in tool_uses if event_index < tu["index"] < boundary]
                episode_actions = [_extract_action(tu) for tu in episode]
                episode_reached_completion = any(
                    event_index < ri < boundary for ri in result_indices)
                if not episode_reached_completion:
                    indeterminate.append({
                        "log": str(log_path),
                        "timestamp": event.get("timestamp"),
                        "text_excerpt": text.strip()[:160],
                        "episode_actions": episode_actions,
                    })
                    continue
                if not episode_actions:
                    continue
                if not all(is_covered(a, manifest, repo=repo_name) for a in episode_actions):
                    continue
                flagged.append({
                    "log": str(log_path),
                    "timestamp": event.get("timestamp"),
                    "text_excerpt": text.strip()[:160],
                    "next_action": episode_actions[0],
                    "episode_actions": episode_actions,
                })
    return {"since": since, "scanned_logs": len(logs), "count": len(flagged),
            "flagged": flagged, "indeterminate": indeterminate}


def format_audit(result: dict) -> str:
    indeterminate = result.get("indeterminate") or []
    header = (f"{result['count']} turn(s) since {result['since']} asked for "
              f"authority a recorded delegation already covered "
              f"(scanned {result['scanned_logs']} session log(s))")
    if result["count"] == 0 and not indeterminate:
        return header + "."
    lines = [header + ":"]
    for f in result["flagged"]:
        action = f.get("next_action") or {}
        lines.append(
            f"  - {f['timestamp']}: {f['log']} — {f['text_excerpt']!r} "
            f"(next action {action.get('tool')}:{action.get('resource')!r} "
            f"already in the manifest)")
    if indeterminate:
        # issue #3061 round-5 verification (PR #3201 hole 3): said
        # plainly, not folded silently into the flagged-or-not count --
        # these episodes were cut off before audit() could see whether
        # every action in them was covered.
        lines.append(
            f"{len(indeterminate)} episode(s) could not be seen to their "
            f"end (session log truncated or still running) — reported "
            f"indeterminate, not a clean verdict:")
        for f in indeterminate:
            lines.append(f"  - {f['timestamp']}: {f['log']} — {f['text_excerpt']!r}")
    return "\n".join(lines)
