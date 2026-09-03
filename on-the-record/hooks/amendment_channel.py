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

  1. (superseded by repair round 5 below) This session's own REGISTERED
     repo -- originally `repo_slug_for_cwd()` applied to the `PostToolUse`
     payload's own top-level `cwd` field, on the claim that field is fixed
     for the session's whole life. That claim was false (see round 5
     section) and this source was replaced; kept here only so the "two
     facts" framing below still reads as history, not as current code.
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
this redesign does not resolve: a session with more than one legitimate
target repo (`spawn.py`'s roster entry carries exactly one `work` path
per session today, so this is a real, currently-unsupported case, not a
hypothetical) -- the FALSE-BLOCK direction, a legitimate multi-repo
session gets wrongly refused; and a session started outside `spawn.py`
entirely (no resolvable registration at all -- fails the SAME closed way,
not a separate skip-silently branch). Round 4's own record framed only
the false-block direction of caveat 1; it did not anticipate that
`repo_slug_for_cwd(cwd)` being a LIVE recomputation (not an actual
registration) also opened a FALSE-ACCEPT direction -- a `cd` could
silently re-register a session to a second repo with no refusal at all.
Round 5 below closes the false-accept direction structurally (the trust
root can no longer move with `cwd`); the false-block direction (no
multi-repo support) is unchanged and still real.

Trust-root repair (PR #3137 repair round 5, issue #3129, following PR
#3191's independent verification of round 4): round 4's own central claim
-- that the payload's `cwd` field is "fixed for the session's whole
life" and "no session-controlled text can retroactively change what the
harness reports here" -- is false. Claude Code's own hooks reference
(`https://code.claude.com/docs/en/hooks`, "cwd follows Claude") states
plainly that `cwd` is live: it is the new directory after Claude runs
`cd`. An ordinary, standalone `cd` in its own Bash call -- not chained
with the `gh issue edit` call, so the round-4 docstring's own "that `cd`
only changes the cwd of the one subprocess" reasoning does not apply to
it at all -- silently re-registers a session's `repo_slug_for_cwd(cwd)`
result to whatever repo it just `cd`'d into, and round 4 had no persisted
record of the ACTUAL launch-time choice to compare against and catch
this (PR #3191's Angle 3, reproduced end-to-end against the real hook
binary, `cwd-drifted-to-other-repo-then-edits-there`: no `RepoMismatch`,
no stderr, a marker written exactly as if that had been the session's own
registered repo all along).

Fact 1 above is now `registered_repo_for_pid()`: this session's own
registered repo comes from `spawn.py`'s own roster (`runs/active.json`,
written by `roster_register()` at dispatch, BEFORE the session's process
exists at all -- see `spawn.py`'s two `roster_register()` call sites),
never from any `PostToolUse` payload field. The correlation from "this
running hook subprocess" to "the roster entry spawn.py wrote for it" is
this OS process's own kernel-tracked ANCESTRY (`/proc/<pid>/stat`'s ppid
field, walked upward): the roster's `pid` field is the actual OS pid
`subprocess.Popen()` assigned the session's `claude` process, an ancestor
of every hook subprocess that session ever spawns, and no Bash command a
session can run -- `cd`, an env re-export, a crafted `--repo=` flag --
changes what pid its own ancestor processes are; that is kernel state, not
session-reported state. A `start_time` pairing (the same pid-reuse guard
`roster.py`'s own `_paired_liveness()` already applies elsewhere in this
codebase) rejects a stale roster entry whose pid number the OS has since
reassigned to an unrelated process. No ancestor pid found registered
within the hop budget -- including a session never launched through
`spawn.py` at all, round-4 caveat 2's case -- fails the same closed way
`NoRegisteredRepo` already did: no marker, one stderr line, nonzero exit.
No `/proc` on this platform (macOS) fails the same way rather than
falling back to `cwd` or anything else the session could influence.

Fact 2's own detection also had a gap PR #3191 found (Angle 2): the old
`_ISSUE_URL_RE.search()` scanned `tool_response` for the URL SHAPE
anywhere in the text, with no check that the match was `gh`'s own
success report rather than a URL-shaped substring inside a FAILED edit's
error message (e.g. `HTTP 422: Validation Failed. See
https://github.com/<repo>/issues/7 for the field format example. (edit 42
was NOT applied)`) -- a marker was silently written for an edit that
explicitly did not apply. `gh issue edit` prints ONLY the edited issue's
URL to stdout on success -- nothing before it, nothing after -- so
`_issue_url_from_response()` now requires the URL to `fullmatch` the
ENTIRE (stripped) `tool_response` text, not merely appear inside it. This
is a POSITIVE success check, not a failure-marker denylist (the
`FAILURE_MARKERS` heuristic `post-landing-obligation-gate.sh` uses
elsewhere in this repo): any additional text at all -- an HTTP error
prefix, a trailing parenthetical, a second URL -- fails the `fullmatch`
and this module treats it exactly like "no URL in response", because a
failure message is never JUST a bare URL with nothing else, by
construction of what an error message is. This also closes, as a
structural consequence rather than a separate fix, PR #3191's
lower-severity finding that an unanchored `.search()` picks the FIRST of
multiple URLs in a response and can misattribute a legitimate edit to the
wrong (first-matched) repo -- a response with more than one URL now fails
`fullmatch` the same way a failure message does.

Real-shape repair (PR #3137 repair round 7, following PR #3205's
independent verification of round 6): round 5's own `fullmatch` check
(previous section) is correct in principle but was validated against
hand-built string fixtures only, never a real payload. PR #3205 captured
one live (`claude -p` against an isolated project with its own
`PostToolUse` hook dumping raw stdin) and found a real Claude Code `Bash`
`tool_response` is a STRUCTURED OBJECT --
`{"stdout": ..., "stderr": ..., "interrupted": ..., "isImage": ...,
"noOutputExpected": ...}` -- never the bare string
`hook_input.tool_response_text()`'s own docstring assumed ("usually the
tool's own stdout as a plain string"). That coercion `json.dumps()`s the
whole dict for a non-string `tool_response`, wrapping the URL in
surrounding JSON punctuation (`{"stdout": "https://...", "stderr": ...}`)
that no `fullmatch` on the bare URL shape can ever match -- so the
positive success check never fired for a single real `gh issue edit`
call, success or failure, and the channel this whole issue exists to
build recorded nothing against real traffic. This round reproduced the
same capture independently (two live `claude -p` runs against Claude Code
2.1.258, one isolated project each, one echoing plain text and one
running a failing `gh issue edit`) and confirmed the identical shape
before writing this fix.

`_issue_url_from_response()` now reads through `_response_stdout_text()`
instead of `hook_input.tool_response_text()`: a dict `tool_response` with
a string `stdout` field yields THAT field alone (never `stderr` -- `gh
issue edit` writes its success URL to stdout only, and mixing in stderr
text would let a warning line coexist with a URL and still `fullmatch`,
exactly the laxness the positive-success design exists to refuse); a bare
string `tool_response` is still accepted as-is unchanged from round 5 (no
real Claude Code build found anywhere in this issue's own investigation
trail -- round 5, round 6, PR #3205, or this round -- ever actually emits
a bare string for `Bash`, so this path is a defensive compatibility
fallback, not a confirmed current or historical production shape; kept
because every pre-round-7 fixture in this suite assumed it and it costs
nothing to keep accepting). Anything else (`tool_response` absent, not a
dict/str, or a dict whose `stdout` is not itself a string) yields `""`,
the same fail-closed "no URL" outcome `_issue_url_from_response()` already
gives for empty text -- `hook_input.tool_response_text()` itself is
UNCHANGED (still shared, correctly, by every `.search()`-based consumer
elsewhere in this repo, which tolerates the json-dumps wrapper because
`.search()` finds the URL anywhere in the blob; only this module's
`fullmatch` needed the tool's own stdout isolated first).

The suite-wide blind spot PR #3205 named (every fixture before this round
built `tool_response` as a bare string, so 79 tests and both gate probes
passed against code that could not match a real payload) is closed
separately: `tests/fixtures/amendment_channel/bash_tool_response.json`
holds the live-captured shape as reviewable data, and
`tests/test_amendment_channel.py`'s `_bash_tool_response()` Creation
Method builds every write-path fixture through it now, including a
dedicated test that failed against the round-6 tip before this fix (see
that file's `RealBashToolResponseShapeIsHandled` class).

Unresolvable repo (issue #3128's shape, applied here pre-emptively): when
`repo_slug_for_cwd()` returns None -- no git repo at the target directory,
no `origin` remote, an origin URL this module's regex does not parse --
neither path substitutes a fallback key (a path hash, a directory
basename, a literal `"unidentified"` string). Any shared fallback is
itself a bucket two different unresolvable repos would collide into,
which is the identical leak this repair fixes for the resolvable case.
Instead, both paths skip entirely: the write path logs one stderr line
(this session's repo could not be identified, so no marker was written --
observable, not silently dropped) and returns without writing; the read
path just returns None (indistinguishable from "no amendment," which is
already this channel's fail-open shape for every other local I/O
failure). No bucket is ever created for an unresolvable repo, so there is
nothing for a second unresolvable repo to collide with. (Round 5 changes
WHICH directory the write path resolves this against -- `spawn.py`'s own
registered `work` directory, via `registered_repo_for_pid()`, rather than
`cwd` -- not this fail-closed shape itself, which is unchanged; the read
path is unchanged by round 5 in both respects.)

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
# issue #3129 round 5: direct test-injection override for the roster path
# `registered_repo_for_pid()` reads, mirroring `STATE_DIR_ENV` above.
ROSTER_PATH_ENV = "OTR_ROSTER_PATH"
# How many `/proc` ancestry hops `registered_repo_for_pid()` walks before
# giving up. Generous headroom over the couple of hops a real hook
# invocation actually needs (this script -> its `.sh` wrapper's shell ->
# the `claude` process spawn.py registered) -- see module docstring,
# round-5 section.
_MAX_ANCESTRY_HOPS = 32

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


def _proc_stat_fields(pid: int) -> Optional[list]:
    """`/proc/<pid>/stat`'s fields from index 2 (state) onward, or None on
    any read failure or platform without `/proc` (macOS). `comm` (field 2
    in the raw file) can itself contain spaces and parentheses, so this
    cuts after the LAST `)` and re-splits from there -- the same
    tokenization `watchdog._proc_start_time()` uses for the same file
    (reimplemented locally rather than imported: this hook keeps its own
    zero-heavy-dependency contract, see module docstring). Never raises.
    """
    try:
        with open("/proc/%d/stat" % pid, "r", encoding="utf-8") as f:
            raw = f.read()
    except (OSError, ValueError):
        return None
    rest = raw[raw.rfind(")") + 2:]
    fields = rest.split()
    return fields or None


def _proc_ppid(pid: int) -> Optional[int]:
    """`pid`'s own parent pid, read straight from the kernel -- never
    anything a session's tool call could report about itself (no `cd`, no
    env re-export, no command text touches this). `None` when the pid is
    gone, unreadable, or this platform has no `/proc` at all."""
    fields = _proc_stat_fields(pid)
    if fields is None or len(fields) < 2:
        return None
    try:
        return int(fields[1])
    except ValueError:
        return None


def _proc_start_time(pid: int) -> Optional[str]:
    """`pid`'s own boot-relative start clock tick (`/proc/<pid>/stat`
    field 22) -- the same pid-reuse guard `spawn.py`'s roster already
    records at registration time and `roster.py`'s own
    `_paired_liveness()` already pairs against elsewhere in this
    codebase. `None` on any read failure or platform without `/proc`."""
    fields = _proc_stat_fields(pid)
    if fields is None or len(fields) < 20:
        return None
    return fields[19]


def _install_root() -> Optional[str]:
    """The checkout root containing `spawn.py`, found by walking up from
    THIS FILE's own on-disk location -- fixed at install time by how the
    interpreter was invoked, never by any `cwd` a session's tool calls
    report. `None` if not found within a few levels (e.g. this hook
    shipped to a bare zero-install consumer checkout that has no
    `spawn.py` at all) -- the caller's fail-closed path handles that."""
    probe = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(probe, "spawn.py")):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return None


def default_roster_path() -> Optional[str]:
    """Where `spawn.py`'s own session roster (`runs/active.json`) lives --
    the registration issue #3129 round 5 trusts INSTEAD OF the
    `PostToolUse` payload's `cwd` field (see module docstring, round-5
    section). `ROSTER_PATH_ENV` is a direct test-injection override
    (mirrors `STATE_DIR_ENV`); `MUSTER_STATE_ROOT` mirrors `spawn.py`'s
    OWN state-root override so a harness that redirects spawn.py's roster
    redirects this lookup the same way; otherwise this walks to the
    installation root via `_install_root()`. `None` when none of the
    three resolves -- the caller's fail-closed path handles that, same as
    every other unresolvable case in this module."""
    override = os.environ.get(ROSTER_PATH_ENV)
    if override:
        return override
    state_root = os.environ.get("MUSTER_STATE_ROOT")
    if state_root:
        return os.path.join(state_root, "active.json")
    root = _install_root()
    if root is None:
        return None
    return os.path.join(root, "runs", "active.json")


def registered_repo_for_pid(pid: int, roster_path: Optional[str] = None) -> Optional[str]:
    """The `owner/repo` `spawn.py` registered for the session this
    process (`pid`) belongs to -- issue #3129 repair round 5's trust
    root, replacing round 4's `repo_slug_for_cwd(cwd)` (see module
    docstring, round-5 section, for why `cwd` is not safe to trust here).

    Walks `pid`'s own kernel-tracked ancestry (via `/proc`, `_proc_ppid`)
    up to `_MAX_ANCESTRY_HOPS` hops looking for an ancestor pid that
    appears as some roster entry's own `pid` field -- the OS pid
    `spawn.py`'s `subprocess.Popen()` chose for this session's `claude`
    process, written to the roster BEFORE that process (and therefore
    every hook subprocess it later spawns) existed at all. A match's
    `start_time` is paired against the live value at that pid (the same
    pid-reuse guard `roster.py`'s own `_paired_liveness()` already
    applies to liveness checks) before it is trusted; the walk continues
    past a reuse mismatch rather than trusting it or stopping short.

    Returns `None` (never a guess, never a fallback to `cwd` or anything
    else the session could influence) when: this platform has no `/proc`
    (macOS today), the roster cannot be read at all, or no ancestor pid
    within the hop budget matches any correctly-paired roster entry --
    covering issue #3129 round-4 caveat 2's "a session started outside
    spawn.py entirely" case, since such a session's own ancestry
    structurally cannot contain a registered pid. Never raises."""
    if not os.path.isdir("/proc"):
        return None
    path = roster_path if roster_path is not None else default_roster_path()
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            roster = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(roster, dict) or not roster:
        return None
    by_pid = {}
    for entry in roster.values():
        if not isinstance(entry, dict):
            continue
        entry_pid = entry.get("pid")
        work = entry.get("work")
        if isinstance(entry_pid, int) and isinstance(work, str) and work:
            by_pid[entry_pid] = (work, entry.get("start_time"))

    current = pid
    for _ in range(_MAX_ANCESTRY_HOPS):
        hit = by_pid.get(current)
        if hit is not None:
            work, recorded_start = hit
            if recorded_start is None or _proc_start_time(current) == recorded_start:
                return repo_slug_for_cwd(work)
            # pid reuse: this number WAS a registered session once, but
            # the live process wearing it now is not that session --
            # keep walking rather than trust the coincidence.
        parent = _proc_ppid(current)
        if parent is None or parent == current or parent <= 1:
            return None
        current = parent
    return None


def has_registered_ancestor(pid: int, roster_path: Optional[str] = None) -> bool:
    """Is this process descended from a session `spawn.py` registered?

    Issue #3283: `registered_repo_for_pid()` answers a different
    question -- "which repo", which additionally requires the recorded
    workspace to resolve to an `origin` slug. A worker whose workspace
    has no resolvable origin gets `None` there, and reading that as "no
    registered ancestor" would let it through the operator-only path and
    assert any repo it liked. The gate has to key on the ancestry itself,
    which is the thing a worker cannot forge, not on whether a slug
    happened to parse.

    Answers False where there is no /proc: the caller then falls back to
    a weaker posture, which is stated at the call site rather than hidden
    here.
    """
    if not os.path.isdir("/proc"):
        return False
    path = roster_path if roster_path is not None else default_roster_path()
    if not path:
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            roster = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(roster, dict):
        return False
    by_pid = {}
    for entry in roster.values():
        if isinstance(entry, dict) and isinstance(entry.get("pid"), int):
            by_pid[entry["pid"]] = entry.get("start_time")
    current = pid
    for _ in range(_MAX_ANCESTRY_HOPS):
        if current in by_pid:
            recorded = by_pid[current]
            if recorded is None or _proc_start_time(current) == recorded:
                return True
        parent = _proc_ppid(current)
        if parent is None or parent == current or parent <= 1:
            return False
        current = parent
    return False


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


def _response_stdout_text(tool_response: object) -> str:
    """The `gh issue edit` command's own stdout text, from a `PostToolUse`
    `tool_response` field -- issue #3129 repair round 7, replacing
    `hook_input.tool_response_text()` for this ONE caller
    (`_issue_url_from_response()`; every other `tool_response` consumer in
    this repo keeps using `hook_input.tool_response_text()` unchanged, see
    module docstring round-7 section for why their `.search()`-based scans
    were never broken by the same gap).

    A real Claude Code `Bash` `tool_response` (Claude Code 2.1.258,
    live-captured this round and independently by PR #3205 against the
    same CLI) is a dict shaped `{"stdout": ..., "stderr": ...,
    "interrupted": ..., "isImage": ..., "noOutputExpected": ...}` -- a
    dict `tool_response` with a string `stdout` field returns THAT field
    alone, never `stderr` (see module docstring for why stderr is
    deliberately excluded here). A bare string `tool_response` is
    returned as-is, a defensive compatibility path for an older/other
    shape this round found no live evidence of (see module docstring).
    Anything else -- absent, not a dict/str, or a dict whose `stdout` is
    not a string -- returns `""`. Never raises.
    """
    if isinstance(tool_response, dict):
        stdout = tool_response.get("stdout")
        return stdout if isinstance(stdout, str) else ""
    if isinstance(tool_response, str):
        return tool_response
    return ""


def _issue_url_from_response(tool_response: object) -> Optional["_IssueUrl"]:
    """The `(owner/repo, issue_number)` a `gh issue edit` command's own
    `tool_response` reports it edited, or None when no such URL is
    present (the call failed, `gh`'s output shape changed, or this simply
    is not a `tool_response` that carries one).

    `gh issue edit` prints the edited issue's URL, and ONLY that URL --
    nothing before it, nothing after -- to stdout on success
    (`https://github.com/<owner>/<repo>/issues/<n>`). This is a POSITIVE
    success check (issue #3129 repair round 5), not a failure-marker
    denylist: the (stripped) text must `fullmatch` the URL shape in full,
    not merely contain it anywhere. A failed edit's error text is never
    JUST a bare URL with nothing else -- by construction of what an error
    message is, it always carries explanatory text around any URL it
    happens to quote -- so this signal structurally cannot appear in a
    failure. `.search()` (matching anywhere in the text) previously let a
    URL-shaped substring inside a FAILED edit's own error message pass as
    if it were `gh`'s own success report; `fullmatch` closes that.

    `text` comes from `_response_stdout_text()` (issue #3129 repair round
    7), not `hook_input.tool_response_text()`: the latter `json.dumps()`s
    a real Bash `tool_response` dict whole, and no `fullmatch` on the bare
    URL shape can ever match text wrapped in surrounding JSON punctuation
    -- see module docstring, round-7 section, for the live capture that
    found this. Never raises.
    """
    text = _response_stdout_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.fullmatch(text.strip())
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


class NoProcOnPlatform(NamedTuple):
    """(issue #3281) This platform has no `/proc` at all (macOS) --
    ancestry-based repo attribution structurally cannot run here, for any
    session, ever, regardless of roster state. Split out from
    `NoRegisteredRepo` (a Linux ancestry MISS: roster unreadable or no
    ancestor pid matched -- a legitimate per-session closed failure the
    module already reported before this split) so the runtime notice can
    say plainly "this platform can't do this" instead of folding a
    platform gap into a message about one session's registration. Fails
    closed: no marker, one stderr line, nonzero exit from `main()` --
    the `macos_bash32_compat.py` check requires exactly this
    runtime-visible signal (not just a docstring) before a `/proc` site
    may join `KNOWN_PROC_SITES`."""


class NoRegisteredRepo(NamedTuple):
    """(issue #3129 round-4 caveat 2, mechanism replaced in round 5) This
    session's own process ancestry carries no roster registration at all
    within the hop budget -- the roster is unreadable, or no ancestor pid
    matches a live, correctly-paired roster entry -- which is exactly what
    a session started OUTSIDE `spawn.py` (no registration ever made) looks
    like from here. (No `/proc` on this platform is `NoProcOnPlatform`
    instead, checked first -- see `record_amendment_from_response()`.)
    Fails closed: no marker, one stderr line, nonzero exit from `main()`.
    Never a fallback to `cwd` or anything else the session's own tool
    calls could influence -- see `registered_repo_for_pid()`."""


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


class WorkerMayNotAssertRepo(NamedTuple):
    """A caller with a registered ancestor tried to name its own repo.

    Issue #3283: the explicit path exists for the operator's session,
    which has no ancestry to attribute. A worker has one, so its repo is
    read from the roster rather than taken from its argv -- otherwise the
    forgery this module was built to prevent walks in the front door.
    """

    registered_repo: str
    asserted_repo: str


WriteResult = Union[
    AmendmentSkipped, NoProcOnPlatform, NoRegisteredRepo, NoIssueUrlInResponse,
    RepoMismatch, MarkerWriteFailed, AmendmentWritten,
    WorkerMayNotAssertRepo,
]


def record_amendment_from_response(
    state_dir: str, tool_name: str, command: str, cwd: str,
    tool_response: object, pid: Optional[int] = None,
    roster_path: Optional[str] = None,
) -> WriteResult:
    """Detect a `gh issue edit ... --body|--body-file ...` Bash call and,
    if the repo it actually edited (from its own `tool_response`, see
    `_issue_url_from_response()`) matches this session's own registered
    repo (from `spawn.py`'s own roster, see `registered_repo_for_pid()`
    -- issue #3129 repair round 5, replacing `repo_slug_for_cwd(cwd)`),
    bump that repo's issue marker. Returns a `WriteResult` describing
    exactly what happened -- see each variant's own docstring.

    `cwd` is used ONLY for `_extract_note()`'s cosmetic note-text
    resolution below (a relative `--body-file` path) -- never for repo
    attribution. `pid` defaults to this process's own pid (`os.getpid()`)
    -- the real production path always resolves the running hook
    process's own registration; `roster_path` is a test-injection
    override (see `registered_repo_for_pid()`). Never raises.
    """
    if not _gh_issue_edit_body_call(tool_name, command):
        return AmendmentSkipped()

    if not os.path.isdir("/proc"):
        return NoProcOnPlatform()

    registered_repo = registered_repo_for_pid(
        pid if pid is not None else os.getpid(), roster_path=roster_path)
    if registered_repo is None:
        return NoRegisteredRepo()

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


def amend_as_orchestrator(state_dir: str, repo: str, issue: str,
                          note: str = "", pid: Optional[int] = None,
                          roster_path: Optional[str] = None) -> WriteResult:
    """Deliver an amendment for an explicitly named repo (issue #3283).

    The ancestry rule this module is built on is right and stays: a worker
    must not be able to say which repo a correction is for, because cwd
    and argv are things its own tool calls can set. But an orchestrator
    was started by the operator, not by `spawn.py`, so it has no
    registered ancestor and the channel refused it -- failing for exactly
    the participant it exists to serve. Three corrections were lost that
    way on 2026-09-03, each one loud at the hook's stderr and invisible
    where it mattered.

    So the two paths are mutually exclusive, and the property that
    identifies a worker is what denies it this one: a caller WITH a
    registered ancestor is refused here and must use the hook path, where
    its repo is attributed rather than asserted. A caller without one is
    the operator's own session and may name the repo.

    The weaker half, stated rather than glossed: "has no registered
    ancestor" is weaker evidence than "has one", since a determined worker
    could orphan itself (setsid, parent exits) and shed its ancestry. That
    is a much stronger attack than the one this rule was written against,
    and a worker doing it has already left its contract far behind -- so
    it is accepted, not defended against, and every use of this path
    records the caller's pid so the choice is auditable.
    """
    caller = pid if pid is not None else os.getpid()
    if has_registered_ancestor(caller, roster_path=roster_path):
        # Keyed on the ancestry, not on whether a repo slug resolved --
        # a worker whose workspace has no parseable origin is still a
        # worker, and reading its unresolvable slug as "no ancestor" was
        # a hole this gate had on its first draft.
        registered = registered_repo_for_pid(caller, roster_path=roster_path)
        return WorkerMayNotAssertRepo(registered or "an unresolvable repo",
                                       repo)
    version = write_amendment(state_dir, repo, issue,
                              note=note or f"operator amendment (pid {caller})")
    if version is None:
        return MarkerWriteFailed(repo, issue)
    return AmendmentWritten(repo, issue, version)


def _report_write_result(result: WriteResult) -> None:
    """Emit the one stderr line each fail-closed `WriteResult` variant
    promises. Quiet for `AmendmentSkipped` (nothing happened, nothing to
    report) and `AmendmentWritten` (the success path speaks for itself via
    the marker file). Never raises."""
    if isinstance(result, WorkerMayNotAssertRepo):
        sys.stderr.write(
            "amendment-channel: this session is registered in spawn.py's "
            f"roster for {result.registered_repo!r}, so it may not assert "
            f"{result.asserted_repo!r} -- a spawned worker's repo is "
            "attributed from its ancestry, never taken from its arguments "
            "(issue #3283) -- no marker written\n")
        return
    if isinstance(result, NoProcOnPlatform):
        sys.stderr.write(
            "amendment-channel: this platform has no /proc (macOS) -- "
            "ancestry-based repo attribution cannot run here at all, for "
            "any session -- no marker written, corrections routed through "
            "this channel will never be delivered on this platform (not a "
            "per-session failure; see amendment_channel.py's module "
            "docstring for the platform gap)\n"
        )
    elif isinstance(result, NoRegisteredRepo):
        sys.stderr.write(
            "amendment-channel: could not find this session's own "
            "registered repo in spawn.py's roster (the roster is "
            "unreadable, or this process's own ancestry carries no "
            "registered pid at all -- e.g. a session not started through "
            "spawn.py) -- no marker written, the running worker will not "
            "see this correction (unregistered; never attributed to cwd "
            "or anything else this session's own tool calls could "
            "influence)\n"
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


def run_hook(payload_text: object, state_dir: Optional[str] = None,
             roster_path: Optional[str] = None) -> Optional[str]:
    """The full PostToolUse behavior: maybe record an amendment, maybe
    return a notice string for the caller to print.

    Thin wrapper over `_run_hook_full()` that drops the `WriteResult` --
    kept as the stable, notice-only entry point every existing caller
    (the `.sh` wrapper's conceptual contract, and most of this module's
    own tests) already expects. `main()` uses `_run_hook_full()` directly
    when it needs the `WriteResult` too (to decide its own exit code).
    `roster_path` is a test-injection override, threaded straight to
    `record_amendment_from_response()` -- production callers leave it
    unset and get `default_roster_path()`'s real resolution.
    """
    notice, _write_result = _run_hook_full(payload_text, state_dir, roster_path)
    return notice


def _run_hook_full(
    payload_text: object, state_dir: Optional[str] = None,
    roster_path: Optional[str] = None,
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
        cwd, data.get("tool_response"), roster_path=roster_path,
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
    if isinstance(write_result, (NoProcOnPlatform, NoRegisteredRepo,
                                  NoIssueUrlInResponse, RepoMismatch,
                                  MarkerWriteFailed)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
