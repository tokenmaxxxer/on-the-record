#!/usr/bin/env python3
"""Amendment channel (issue #3129): the local-file bridge that lets an
orchestrator's mid-flight issue-body edit reach a spawned worker session
that already read the issue once at spawn and never re-reads it.

Two channels exist today and both fail for a spawned worker: cross-session
messages require the RECIPIENT's user to approve, and a headless worker has
nobody to approve them, so every message expires undelivered; amending the
issue body reaches `check_runner` (which re-reads the body to score) but
not the running process, which never re-reads it either.

The seam this uses instead: `PostToolUse` fires on every tool call in a
worker session and its output lands in that session's context
(`hookSpecificOutput.additionalContext`). This module is invoked from that
hook on every tool call, so it must never call `gh` (a network round trip
on every tool use is the same tick-budget cost that made the watchdog
delta-gated) and must never raise (a PostToolUse hook that crashes fails
open per `fail-open-wrapper.sh`, silently dropping the one channel this
issue exists to add -- every public function here returns a value instead,
same total-function contract as `hook_input.py` next to it).

State (two local JSON files, issue #3129's design choice):

  MARKER  <state_dir>/issue-<n>__<repo>.marker.json      {"version": int, ...}
  SEEN    <state_dir>/seen/<session>__<repo>__issue-<n>.json   {"absorbed_version": int}

Repo-attribution repair (PR #3137 follow-up): the marker was originally
keyed by issue number alone. Two independent repos that both happen to use
branch `issue-42/<role>` for issue #42 then share the identical marker
path, so an orchestrator's edit in repo A lands in a worker's context in
unrelated repo B verbatim -- the third instance of the orchestrator-
shared-state-keyed-without-repo defect shape this board has found (after
#3081's `requirement_drift` cache and #3095's `spawn_on_pr` park state).
Every marker/seen path now carries a repo dimension.

That repo identity is deliberately NOT `plumbing._repo_slug()` (what
#3084 and #3106 both reuse) -- that helper shells out to `gh repo view`,
a network round trip, and this module runs as a brand-new subprocess on
EVERY PostToolUse call (see `amendment-channel.sh`), so calling it here
would reintroduce on the repo-resolution path the exact must-not this
issue's acceptance already forbids on the amendment-check path ("do not
poll gh from PostToolUse"). `repo_slug_for_cwd()` below resolves the same
`owner/repo` shape from `git remote get-url origin` instead -- local
git-config plumbing only, the same no-network technique
`spawn._workspace_target_path()` already uses elsewhere in this repo.

Writer-side repo-targeting repair (PR #3159 follow-up; HISTORICAL -- every
function this section and the next name was deleted by the round-4 seam
redesign below, which stopped parsing command text for a target repo
entirely; kept here for the reasoning trail, not as a description of
current code): the write path
originally called `repo_slug_for_cwd()` on the raw `PostToolUse` payload
`cwd` -- the orchestrator's own session directory -- even though the `gh
issue edit` command it is inspecting can `cd` into a DIFFERENT checkout
first (`cd ../study-companion && gh issue edit 42 --body ...`, run from
an `on-the-record` session cwd, is this issue's own worked example) or
name the target explicitly with `--repo`/`-R`. Keying the marker off the
session cwd in that shape reopens the identical collision class this
module exists to close, just under a different trigger. Two sources are
authoritative for what a `gh issue edit` command actually targets, and
the raw session `cwd` is not one of them: an explicit `--repo`/`-R` flag
on the invocation itself (`_explicit_repo_flag()`), or otherwise
`hook_input.resolved_cwd()`'s leading-`cd`-target resolution (the same
total, no-network `cd <path> &&` parser every other hook in this repo
already shares -- see `hook_input.py`'s own docstring, which names this
exact ad-hoc-`cd`-extraction defect class as the reason it exists).
Neither source resolving falls through to the same unresolvable-repo
handling below -- never a fallback to the session cwd.

Parser-robustness repair (PR #3163 follow-up, repair round 3): the round-2
resolver above was correct in principle but leaned on
`hook_input.resolved_cwd()`, whose own contract is "the `cd` target, else
`default`" for every unresolved case including a structurally opaque
command -- so a heredoc body (`--body-file - <<'EOF' ... EOF`, the shape
the orchestrator uses for EVERY body edit), a `cd /a; gh ...` semicolon,
and a `(cd /a && gh ...)` subshell all fell through to `default=cwd`
silently, with no marker, no stderr. `target_repo_for_command()` now calls
`hook_input.cd_target()` directly and never substitutes `cwd` for an
`OpaqueCommand` result -- see that function's own docstring. `cd_target()`
itself gained: heredoc BODY stripping (the redirect is real syntax, the
data between the delimiter lines is not) rather than blanket opacity,
`;`/`||`/newline as valid separators after a `cd` (not only `&&`),
unwrapping enclosing `( ... )`/`{ ... }` groups, and walking multiple
chained `cd` steps in order. Separately, `_GH_ISSUE_EDIT_RE` gained
tolerance for flags between `gh` and `issue edit` (`gh -R owner/repo issue
edit 42` used to miss the regex entirely -- a silent total miss, not even
an unresolvable-repo stderr line, because the write path never triggered
at all).

Seam redesign (PR #3170 follow-up, repair round 4 -- supersedes the two
sections above for the WRITE side): rounds 2 and 3 both tried to recover
the target repo by parsing the `gh issue edit` command's own text more
carefully -- `--repo`/`-R` flags, `cd` prefixes, heredocs, subshells. PR
#3170's independent verification found round 3 still missed 5 of 9
un-enumerated shapes (`pushd`, a quoted `cd` path with a space, a subshell
wrapping only `gh`, `--repo=` before the issue number, a `GH_REPO=` env
prefix) -- parsing shell text is an open-ended enumeration problem, and
every round closes some shapes while leaving the next one for whoever
finds it next.

This round changes the seam instead of adding shapes: the command text is
no longer consulted for the repo AT ALL (it is still consulted for one
thing only -- deciding whether this Bash call is a `gh issue edit ...
--body|--body-file ...` invocation in the first place, see
`_gh_issue_edit_body_call()` -- that is a shape check, not an attribution
parse, and it fails closed to "not applicable" rather than a guess when
undecidable). Two facts, neither of them shell text, are authoritative:

  1. This session's own REGISTERED repo: `repo_slug_for_cwd()` applied to
     this `PostToolUse` payload's own top-level `cwd` field -- the
     directory `spawn.py` launched this process into
     (`subprocess.Popen(cmd, cwd=<workspace>, ...)`), which every hook
     payload in this session reports unchanged for the session's whole
     life. This is NOT the same value a `cd X && gh ...` inside a single
     Bash command string affects -- that `cd` only changes the cwd of the
     one subprocess that command string spawns, never this payload
     field (round 2's own worked example, and rounds 2/3's whole reason
     to parse the command, both rest on this same distinction). Treating
     THIS field as "what spawn.py registered for this session" needs no
     new cross-process registration file: spawn.py already IS the one
     process that chose it, and no session-controlled text can retroactively
     change what the harness reports here for a later tool call.
  2. The actual edited issue's repo and number: `gh issue edit` prints the
     edited issue's URL on success, shaped
     `https://github.com/<owner>/<repo>/issues/<n>`, and the PostToolUse
     payload's own `tool_response` field carries that stdout
     (`hook_input.tool_response_text()` -- the same string-or-json-dumps
     coercion every other `tool_response` consumer in this directory
     already applies ad hoc). `_issue_url_from_response()` regexes it out.

`record_amendment_from_response()` compares the two: same repo -> write
the marker keyed to that repo+issue (the URL's issue number, never a
number lifted from the command text -- round 2/3's own `_GH_ISSUE_EDIT_RE`
capture group is gone for exactly this reason). Different repo -> this is
now a POLICY VIOLATION, not a parse failure to route around: no marker,
one loud stderr line naming BOTH repos, and (unlike every other failure
mode in this module) `main()` returns nonzero for it -- see `main()`'s own
comment for why that nonzero exit does not contradict this module's
"never blocks a tool call" contract. No URL in `tool_response` at all
(the edit failed, or `gh`'s output shape changed some day) is the same
fail-closed shape: no marker, one stderr line, nonzero exit. Two caveats
this redesign does not resolve, recorded in
`docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7.md`
rather than silently assumed away: a session with more than one
legitimate target repo (`spawn.py`'s roster entry carries exactly one
`work` path per session today, so this is a real, currently-unsupported
case, not a hypothetical), and a session started outside `spawn.py`
entirely (no resolvable registered repo -- `repo_slug_for_cwd(cwd)`
returns `None`, which is the SAME fail-closed "no registered repo" path
caveat 1 above already forces, not a separate skip-silently branch).

Unresolvable repo (issue #3128's shape, applied here pre-emptively): when
`repo_slug_for_cwd()` returns None -- no git repo at `cwd`, no `origin`
remote, an origin URL this module's regex does not parse -- neither the
write path nor the read path substitutes a fallback key (a path hash, a
cwd basename, a literal `"unidentified"` string). Any shared fallback is
itself a bucket two different unresolvable repos would collide into,
which is the identical leak this repair fixes for the resolvable case.
Instead, both paths skip entirely: the write path logs one stderr line
(this session's repo could not be identified, so no marker was written --
observable, not silently dropped) and returns without writing; the read
path just returns None (indistinguishable from "no amendment," which is
already this channel's fail-open shape for every other local I/O
failure). No bucket is ever created for an unresolvable repo, so there is
nothing for a second unresolvable repo to collide with.

`version` is an explicit monotonic counter written into the marker's
*content*, not read off the filesystem's mtime -- mtime granularity differs
between Linux (sub-second) and macOS (historically 1s on some filesystems),
so two writes in the same tick could be indistinguishable by mtime alone.
The state machine that gives the two behaviors the issue calls "the
substance of the work":

  fires once per amendment   -- a notice only fires when marker.version is
                                 STRICTLY GREATER than this session's last
                                 absorbed_version for that issue.
  stops after absorption      -- the moment a notice is about to fire, this
                                 session's SEEN file is updated to
                                 marker.version FIRST, so a second call
                                 with no new amendment (version unchanged)
                                 compares equal and stays quiet. A new
                                 `gh issue edit ... --body` bumps version
                                 again and the cycle repeats.

Never a blocking gate: the caller only ever gets a string to fold into
context, or None. Nothing here can deny a tool call.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from typing import NamedTuple, Optional, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_input  # noqa: E402

STATE_DIR_ENV = "OTR_AMENDMENT_STATE_DIR"

# Matches `gh issue edit ...` anywhere a shell would start a new command
# (start of string; after `;`/`&&`/`||`/`|`; or after `(`/`{` opening a
# subshell/group, e.g. `cd /a && (gh issue edit ...)`) -- a SHAPE check
# only ("is this call relevant at all"), never an attribution parse (see
# the module docstring's redesign section): the issue number and target
# repo both now come from `tool_response`/this session's own registered
# repo, never from this match. An optional run of leading `NAME=value`
# env-var assignments is allowed before `gh` itself (`GH_REPO=o/r gh
# issue edit ...` is valid POSIX simple-command syntax, not a separate
# command). The `(?:(?!issue\s+edit\b)\S+\s+)*` gap lets any number of
# flags (`-R owner/repo`, `--repo=owner/repo`, ...) sit between `gh` and
# the `issue edit` subcommand so those shapes are still detected as
# relevant, even though their flag value is no longer read for anything.
_GH_ISSUE_EDIT_RE = re.compile(
    r"(?:^|[;&|]\s*|[({]\s*)"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r"gh\s+(?:(?!issue\s+edit\b)\S+\s+)*issue\s+edit\b"
)
_BODY_FLAG_RE = re.compile(r"--body(?:-file)?(?:=|\s|$)")
_BRANCH_ISSUE_RE = re.compile(r"^issue-(\d+)\b")
_REPO_URL_RE = re.compile(
    r"^(?:https?://[^/]+/|git@[^:]+:|ssh://(?:[^@/]+@)?[^/]+/)"
    r"(?P<slug>[^/]+/[^/]+?)(?:\.git)?/?$"
)
# `gh issue edit`'s own success output: the edited issue's URL, verbatim.
# This is the ONLY source of truth for which repo+issue an edit actually
# landed on (see module docstring redesign section) -- never the command
# text, never the session cwd alone.
_ISSUE_URL_RE = re.compile(
    r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b"
)
_NOTE_MAX = 2000


def default_state_dir() -> str:
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return override
    return os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-amendment")


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def repo_slug_for_cwd(cwd: str) -> Optional[str]:
    """The `owner/repo` this `cwd` checkout's `origin` remote points at, or
    None when it cannot be determined -- no git repo here, no `origin`
    remote configured, or an origin URL this module's regex does not
    parse (see module docstring for why this does NOT shell out to
    `gh repo view` the way `plumbing._repo_slug()` does: this runs on
    every PostToolUse call, and that helper is a network round trip).

    Callers must treat None as "this repo cannot be attributed" and skip
    the read/write entirely -- never substitute a fallback key here, that
    is the exact shared-bucket leak issue #3128 names.
    """
    if not cwd or not isinstance(cwd, str) or not os.path.isdir(cwd):
        return None
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    origin = r.stdout.strip()
    if not origin:
        return None
    m = _REPO_URL_RE.match(origin)
    return m.group("slug") if m else None


def marker_path(state_dir: str, repo: str, issue: str) -> str:
    return os.path.join(
        state_dir, "issue-%s__%s.marker.json" % (_safe(str(issue)), _safe(repo))
    )


def seen_path(state_dir: str, session_id: str, repo: str, issue: str) -> str:
    return os.path.join(
        state_dir, "seen",
        "%s__%s__issue-%s.json" % (_safe(session_id), _safe(repo), _safe(str(issue))),
    )


def _atomic_write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def read_marker(state_dir: str, repo: str, issue: str) -> Optional[dict]:
    """The current amendment marker for `repo`'s `issue`, or None if
    absent/corrupt.

    Never raises: a missing file, a permission error, or malformed JSON all
    read as "no amendment" (fail open) rather than crashing the caller's
    PostToolUse hook.
    """
    try:
        with open(marker_path(state_dir, repo, issue), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("version"), int):
        return None
    return data


def write_amendment(state_dir: str, repo: str, issue: str, note: str = "") -> Optional[int]:
    """Bump the amendment marker for `repo`'s `issue` and return the new version.

    Called from the orchestrator's own PostToolUse call when it edits an
    issue body. Read-increment-write is not atomic across processes (two
    concurrent orchestrators amending the same issue in the same instant
    could race), but the failure mode of a lost increment here is a missed
    notice tick, not a wrong one -- the next amendment still bumps version
    past whatever a worker last absorbed. Returns None on any local I/O
    failure (never raises): a write that cannot land degrades to "the
    worker keeps its stale brief", the same shape as if this channel did
    not exist -- never a crash of the orchestrator's own hook.
    """
    try:
        existing = read_marker(state_dir, repo, issue)
        version = (existing.get("version") if existing else 0) + 1
        data = {
            "version": version,
            "written_at": datetime.now(timezone.utc).isoformat(),
            "note": note[:_NOTE_MAX],
        }
        _atomic_write_json(marker_path(state_dir, repo, issue), data)
        return version
    except OSError:
        return None


def _read_seen(state_dir: str, session_id: str, repo: str, issue: str) -> int:
    try:
        with open(seen_path(state_dir, session_id, repo, issue), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0
    v = data.get("absorbed_version")
    return v if isinstance(v, int) else 0


def _write_seen(state_dir: str, session_id: str, repo: str, issue: str, version: int) -> None:
    _atomic_write_json(
        seen_path(state_dir, session_id, repo, issue), {"absorbed_version": version}
    )


def format_notice(issue: str, marker: dict) -> str:
    note = marker.get("note") or ""
    written_at = marker.get("written_at", "unknown time")
    base = (
        "[amendment] issue #%s was amended by the orchestrator at %s -- "
        "re-read it before continuing. This is advisory: decide whether "
        "the correction is right, do not halt on it." % (issue, written_at)
    )
    if note:
        base += " Note: %s" % note
    return base


def check_notice(state_dir: str, session_id: str, repo: str, issue: str) -> Optional[str]:
    """Fire the notice for `repo`'s `issue` at most once per amendment for
    `session_id`.

    Returns the notice text the first time this session observes a marker
    version it has not yet absorbed, and None on every subsequent call
    until a NEW amendment bumps the version again. Never raises: any local
    I/O failure here just means this tick stays quiet and the next tool
    call re-checks the same comparison (version still unabsorbed), so a
    transient failure delays a notice by one tick instead of losing it or
    crashing the hook.
    """
    try:
        marker = read_marker(state_dir, repo, issue)
        if marker is None:
            return None
        version = marker["version"]
        seen = _read_seen(state_dir, session_id, repo, issue)
        if version <= seen:
            return None
        # Absorb BEFORE returning: the write below is what makes this
        # amendment stop being announced on the very next call, even if
        # nothing downstream reads the return value.
        _write_seen(state_dir, session_id, repo, issue, version)
        return format_notice(issue, marker)
    except OSError:
        return None


def _extract_note(command: str, cwd: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ""
    for i, tok in enumerate(tokens):
        if tok in ("--body", "--body-file") and i + 1 < len(tokens):
            value = tokens[i + 1]
        elif tok.startswith("--body="):
            value = tok[len("--body="):]
        elif tok.startswith("--body-file="):
            value = tok[len("--body-file="):]
        else:
            continue
        if tok in ("--body-file",) or tok.startswith("--body-file="):
            path = value if os.path.isabs(value) else os.path.join(cwd or ".", value)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(_NOTE_MAX)
            except OSError:
                return ""
        return value[:_NOTE_MAX]
    return ""


def issue_for_cwd(cwd: str) -> Optional[str]:
    """The issue number this session's own branch names, or None.

    A worker session's branch is always `issue-<n>/<role>` (spawn.py's own
    naming convention). Local `git` plumbing only -- no network -- so this
    costs one fast subprocess call per tool use, not a `gh` round trip.
    """
    if not cwd or not isinstance(cwd, str) or not os.path.isdir(cwd):
        return None
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = _BRANCH_ISSUE_RE.match(r.stdout.strip())
    return m.group(1) if m else None


def _gh_issue_edit_body_call(tool_name: str, command: str) -> bool:
    """True when this Bash call is a `gh issue edit ... --body|--body-file
    ...` invocation -- the only shape the write side cares about.

    This is the one place command TEXT is still consulted, and only to
    decide "is this relevant at all" -- never to decide WHICH repo it
    targets (see module docstring, redesign section). `False` here means
    "nothing to do", not a failure; nothing is written and nothing is
    logged.
    """
    return bool(
        tool_name == "Bash" and command
        and _GH_ISSUE_EDIT_RE.search(command)
        and _BODY_FLAG_RE.search(command)
    )


def _issue_url_from_response(tool_response: object) -> Optional["_IssueUrl"]:
    """The `(owner/repo, issue_number)` a `gh issue edit` command's own
    `tool_response` reports it edited, or None when no such URL is
    present (the call failed, `gh`'s output shape changed, or this simply
    is not a `tool_response` that carries one).

    `gh issue edit` prints the edited issue's URL
    (`https://github.com/<owner>/<repo>/issues/<n>`) on success -- this is
    the tool's own report of what it actually did, not a parse of what the
    command asked for. Never raises.
    """
    text = hook_input.tool_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.search(text)
    if not m:
        return None
    owner, repo, issue = m.group(1), m.group(2), m.group(3)
    return _IssueUrl("%s/%s" % (owner, repo), issue)


class _IssueUrl(NamedTuple):
    repo: str
    issue: str


class AmendmentSkipped(NamedTuple):
    """Not a `gh issue edit ... --body...` Bash call -- nothing to do,
    not a failure. `main()` exits 0 for this outcome."""


class NoRegisteredRepo(NamedTuple):
    """(issue #3129 round-4 caveat 2) This session carries no resolvable
    registered repo at all: `cwd` is not a git checkout, has no `origin`
    remote, or the remote is a shape `repo_slug_for_cwd()` cannot parse --
    which is exactly what a session started OUTSIDE `spawn.py` (no
    registration ever made) looks like from here, since there is no
    separate "registered" bit to check apart from this. Fails closed: no
    marker, one stderr line, nonzero exit from `main()`."""

    cwd: str


class NoIssueUrlInResponse(NamedTuple):
    """`gh issue edit` ran but its `tool_response` carries no parseable
    issue URL -- the call may have failed, or `gh`'s output shape changed.
    Fails closed: no marker, one stderr line, nonzero exit from `main()`."""

    registered_repo: str


class RepoMismatch(NamedTuple):
    """POLICY VIOLATION: the edited issue's URL names a different repo
    than this session's own registered repo. Fails closed: no marker, one
    stderr line naming BOTH repos, nonzero exit from `main()`."""

    registered_repo: str
    url_repo: str
    issue: str


class MarkerWriteFailed(NamedTuple):
    """Repo+issue resolved cleanly (registered repo == URL repo) but the
    local marker write itself failed (state dir unwritable, etc).
    write_amendment()'s own OSError catch is correct fail-open for the
    orchestrator's own tool call, but the failure must not vanish with
    zero trace -- one stderr line, nonzero exit from `main()`."""

    repo: str
    issue: str


class AmendmentWritten(NamedTuple):
    """Marker written; `version` is the new monotonic counter value."""

    repo: str
    issue: str
    version: int


WriteResult = Union[
    AmendmentSkipped, NoRegisteredRepo, NoIssueUrlInResponse,
    RepoMismatch, MarkerWriteFailed, AmendmentWritten,
]


def record_amendment_from_response(
    state_dir: str, tool_name: str, command: str, cwd: str,
    tool_response: object,
) -> WriteResult:
    """Detect a `gh issue edit ... --body|--body-file ...` Bash call and,
    if the repo it actually edited (from its own `tool_response`, see
    `_issue_url_from_response()`) matches this session's own registered
    repo (from `cwd`, see `repo_slug_for_cwd()`), bump that repo's issue
    marker. Returns a `WriteResult` describing exactly what happened --
    see each variant's own docstring. Never raises.
    """
    if not _gh_issue_edit_body_call(tool_name, command):
        return AmendmentSkipped()

    registered_repo = repo_slug_for_cwd(cwd)
    if registered_repo is None:
        return NoRegisteredRepo(cwd)

    parsed = _issue_url_from_response(tool_response)
    if parsed is None:
        return NoIssueUrlInResponse(registered_repo)

    if parsed.repo != registered_repo:
        return RepoMismatch(registered_repo, parsed.repo, parsed.issue)

    note = _extract_note(command, cwd)
    version = write_amendment(state_dir, parsed.repo, parsed.issue, note=note)
    if version is None:
        return MarkerWriteFailed(parsed.repo, parsed.issue)
    return AmendmentWritten(parsed.repo, parsed.issue, version)


def _report_write_result(result: WriteResult) -> None:
    """Emit the one stderr line each fail-closed `WriteResult` variant
    promises. Quiet for `AmendmentSkipped` (nothing happened, nothing to
    report) and `AmendmentWritten` (the success path speaks for itself via
    the marker file). Never raises."""
    if isinstance(result, NoRegisteredRepo):
        sys.stderr.write(
            "amendment-channel: could not identify this session's own "
            "registered repo (cwd=%r has no resolvable git origin) -- no "
            "marker written, the running worker will not see this "
            "correction (repo unidentified; not attributed to a shared "
            "bucket another unidentified repo could read)\n" % result.cwd
        )
    elif isinstance(result, NoIssueUrlInResponse):
        sys.stderr.write(
            "amendment-channel: gh issue edit ran but its tool_response "
            "carries no parseable https://github.com/<owner>/<repo>/"
            "issues/<n> URL (the call may have failed, or gh's output "
            "shape changed) -- no marker written; this session's own "
            "registered repo is %s\n" % result.registered_repo
        )
    elif isinstance(result, RepoMismatch):
        sys.stderr.write(
            "amendment-channel: POLICY VIOLATION -- gh issue edit #%s "
            "landed in %s but this session is registered to %s -- no "
            "marker written (an edit outside a session's own registered "
            "repo is refused, never silently attributed)\n"
            % (result.issue, result.url_repo, result.registered_repo)
        )
    elif isinstance(result, MarkerWriteFailed):
        sys.stderr.write(
            "amendment-channel: failed to record an amendment marker for "
            "issue #%s in %s (state dir unwritable) -- the running "
            "worker will not see this correction\n"
            % (result.issue, result.repo)
        )


def run_hook(payload_text: object, state_dir: Optional[str] = None) -> Optional[str]:
    """The full PostToolUse behavior: maybe record an amendment, maybe
    return a notice string for the caller to print.

    Thin wrapper over `_run_hook_full()` that drops the `WriteResult` --
    kept as the stable, notice-only entry point every existing caller
    (the `.sh` wrapper's conceptual contract, and most of this module's
    own tests) already expects. `main()` uses `_run_hook_full()` directly
    when it needs the `WriteResult` too (to decide its own exit code).
    """
    notice, _write_result = _run_hook_full(payload_text, state_dir)
    return notice


def _run_hook_full(
    payload_text: object, state_dir: Optional[str] = None,
) -> "tuple[Optional[str], WriteResult]":
    """`run_hook()`'s full behavior, also returning the `WriteResult` so
    `main()` can set its own exit code from it.

    Every ANTICIPATED failure mode (missing/corrupt marker, unwritable
    state dir, no git repo at `cwd`, malformed payload) is handled inside
    the functions this calls, each documented as never raising for its
    own domain. This function deliberately does NOT add another blanket
    catch on top of those: doing so previously (issue #3129 silent-
    failure-audit) meant a genuine bug in this new module would vanish
    with zero trace anywhere -- not stderr, not the `fail-open-wrapper.sh`
    ledger, nothing -- because that ledger's crash detection greps stderr
    for a traceback regardless of exit code (see fail-open-wrapper.sh),
    and this module's own `.sh` wrapper always exits 0 on its trailing
    line independent of this process's exit code either way. An
    unanticipated exception propagating out of `main()` costs nothing in
    blocking risk and is the only way such a bug becomes observable.
    """
    state_dir = state_dir or default_state_dir()
    payload = hook_input.parse_payload(payload_text)
    if isinstance(payload, hook_input.Unparseable):
        return None, AmendmentSkipped()
    data = payload.data
    cwd = data.get("cwd")
    cwd = cwd if isinstance(cwd, str) else ""
    session_id = data.get("session_id")

    write_result = record_amendment_from_response(
        state_dir, payload.tool_name, hook_input.tool_command(payload),
        cwd, data.get("tool_response"),
    )
    _report_write_result(write_result)

    if not isinstance(session_id, str) or not session_id or not cwd:
        return None, write_result
    issue = issue_for_cwd(cwd)
    if not issue:
        return None, write_result
    repo = repo_slug_for_cwd(cwd)
    if not repo:
        # Unresolvable repo on the read side: stay quiet, same as any other
        # local lookup failure this module already fails open on (missing
        # marker, unwritable state dir). No fallback key is substituted
        # here either, so there is nothing for a second unidentified repo
        # to collide with.
        return None, write_result
    return check_notice(state_dir, session_id, repo, issue), write_result


def main() -> int:
    try:
        payload_text = sys.stdin.read()
    except OSError:
        return 0
    notice, write_result = _run_hook_full(payload_text)
    if notice:
        out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": notice}}
        try:
            sys.stdout.write(json.dumps(out))
        except OSError:
            pass
    # issue #3129 round-4: a fail-closed write outcome (no registered repo,
    # no URL in tool_response, a cross-repo policy violation, or a marker
    # write that itself failed) makes THIS process's own exit code
    # nonzero -- observable to anything that invokes amendment_channel.py
    # directly (tests, the gates probes, a human piping its stderr) even
    # though the shipped `.sh` wrapper (amendment-channel.sh) unconditionally
    # exits 0 on its own trailing line regardless of this exit code, same
    # as it always has: a PostToolUse hook must never block a tool call
    # (see hook_classification.json), so the wrapper's own exit code stays
    # fail-open by design -- the stderr line `_report_write_result()`
    # already wrote is the loud signal for the live hook path, same
    # mechanism the pre-existing unresolvable-repo/unwritable-state-dir
    # cases already used before this round.
    if isinstance(write_result, (NoRegisteredRepo, NoIssueUrlInResponse,
                                  RepoMismatch, MarkerWriteFailed)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
