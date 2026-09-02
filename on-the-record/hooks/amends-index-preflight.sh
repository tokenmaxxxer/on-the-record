#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on `amends:` discoverability
# drift -- issue #3134 repair round.
#
# The #3134 repair round's independent verification (docs/issue-3134/
# reports/, PR #3146) graded the first delivery's must-not 1 Surface:
# `gates/amends_index.py::check()` was correct but unwired -- no
# PreToolUse hook invoked it, following its own stated precedent
# (spec-index-preflight.sh, path:on-the-record/hooks/
# spec-index-preflight.sh). This hook is that wiring.
#
# Unlike spec-index-preflight.sh's single self-contained hash comparison
# (one registry file -> one derived index, ported inline so no `gates/`
# checkout is required in a consumer repo), `amends_index.py::check()`
# composes THREE modules (`amends.py`'s resolver, `amends_backlink.py`'s
# marker logic, `amends_index.py`'s own render/glob) over an unbounded
# `docs/issue-*/reports/**/*.md` glob. Hand-porting that inline and
# keeping it byte-for-byte in sync with three separate source files by
# hand is the same trap `requirement-digest-preflight.sh`'s own comment
# warns about for a single file, worse for three. This hook instead
# follows `quality-bar-gate.sh`/`merge-allow-gate.sh`'s alternate,
# equally-established precedent: resolve a checkout that carries
# `gates/`, import the real modules, run the real function. `amends:` is
# repo-local in the same sense `spec_index.py` is ("checks this repo's
# own docs/issue-*/reports/ set, not a consumer's" --
# docs/specs/enforcement-boundary.md) -- a consumer checkout with no
# `gates/amends_index.py` at all fails open below, same as
# spec-index-preflight.sh's own missing-index fail-open path.
#
# Trigger: narrowed to a `git commit` whose staged set touches a
# `docs/issue-*/reports/**/*.md` record or `docs/specs/amends-index.md`
# itself (gate-registration-guard.sh precedent for narrow-by-design
# triggers) -- an unrelated commit never pays the glob-scan cost.
#
# Repair round 3 (issue #3134 reopen, findings 1+2): this hook used to
# call `amends_index.check()` -- the FULL check, blocking on a still-
# missing backlink or a stale index just as readily as on a genuinely
# malformed edge. That denied a correcting session's own first commit of
# its own record (by construction always pre-landing, so always
# "unlinked" in `check()`'s sense) and let one unresolved edge anywhere
# in the tree deny every future report-touching commit, repo-wide, by any
# session -- reproduced live in docs/issue-3134/reports/adversarial-
# review+knowledge-management-supersession-lifecycle+silent-failure-
# audit-48484397.md. This hook now calls `amends_index.check_staged()`
# instead: scoped to this commit's own staged paths, and never blocking
# on a missing backlink or index staleness at all -- those are landing-
# step concerns, checked by `check_landing()` and resolved automatically
# by `gates/amends_landing.py::land()` (see
# `on-the-record/hooks/amends-landing-apply.sh`). Only a dangling target,
# a missing section anchor, a conflict, or a cycle this commit's own
# staged paths participate in is ever denied here.
#
# Known limitation (documented, not silently absorbed): `check_staged()`
# reads the WORKING TREE via `Path.read_text`, not staged git blobs
# (unlike spec-index-preflight.sh's `git show :<path>`) -- a discrepancy
# between staged content and the working tree (e.g. `git commit` without
# a prior `git add` of a just-edited record) is a known gap, matching
# `amends_index.py`'s own existing contract rather than introducing a new
# one; the working tree is what every session's own Edit/Write tool calls
# actually write to before staging, so this holds in the harness's normal
# write-then-add-then-commit sequence.
#
# Fail-open by design: any environment gap (no python3/git, no `gates/`
# checkout here, unresolvable payload) exits 0. What must never happen is
# silently allowing a commit this hook positively determined would land
# an unlinked `amends:` edge (missing index update, missing backlink, or
# both); that path exits 2.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
# issue #2016 phase 2: cheap bash-level short-circuit before the python3 spawn below --
# skip the interpreter launch entirely when the raw payload plainly can't match this
# gate's own command-shape condition (checked again, authoritatively, in python).
{ grep -qF 'git' <<<"$payload" && grep -qF 'commit' <<<"$payload"; } || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, subprocess, sys
from pathlib import Path

def deny(msg):
    sys.stderr.write("amends-index-preflight: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("AIP_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

# issue #2210: strip heredoc bodies before tokenizing, same reason
# spec-index-preflight.sh does -- data inside a heredoc is not shell
# syntax and must not false-trigger the "git"/"commit" token check.
sys.path.insert(0, os.environ.get("OTR_HOOKS_DIR", ""))
from heredoc_scope import strip_heredoc_bodies  # noqa: E402
cmd_skeleton = strip_heredoc_bodies(cmd)

try:
    _lexer = shlex.shlex(cmd_skeleton, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)
if "git" not in tokens or "commit" not in tokens:
    sys.exit(0)

cwd = os.getcwd()
if not os.path.isfile(os.path.join(cwd, "gates", "amends_index.py")):
    sys.exit(0)  # fail open: no gates/ checkout here to check against

try:
    r = subprocess.run(["git", "diff", "--cached", "--name-only"],
                       capture_output=True, text=True, timeout=20, cwd=cwd)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
staged = set(line.strip() for line in r.stdout.splitlines() if line.strip())

_RECORD_RE = re.compile(r"^docs/issue-[^/]+/reports/.*\.md$")
relevant = (
    any(_RECORD_RE.match(p) for p in staged)
    or "docs/specs/amends-index.md" in staged
)
if not relevant:
    sys.exit(0)

sys.path.insert(0, cwd)
sys.path.insert(0, os.path.join(cwd, "gates"))
try:
    import amends_index  # noqa: E402
except ImportError:
    sys.exit(0)  # fail open: this checkout's gates/ can't actually run the check

bad = amends_index.check_staged(Path(cwd), staged)
if bad:
    deny("this commit's own amends: edge is malformed:\n  - " + "\n  - ".join(bad))
PY

OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)" AIP_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
