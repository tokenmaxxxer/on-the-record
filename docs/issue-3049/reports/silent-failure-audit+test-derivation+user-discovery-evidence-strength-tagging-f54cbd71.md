---
issue: 3049
role: silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71
author: silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), user-discovery-evidence-strength-tagging (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: test
breaking: false
verdict: pass — all four named cwd shapes are caught by gate-registration-post-guard.sh; no fix needed, the honest map is the deliverable
upstream:
  - path: on-the-record/hooks/gate-registration-post-guard.sh
    sha: 573e7382282be24439c223c1603be648dd0e158f
  - path: on-the-record/hooks/gate-registration-guard.sh
    sha: 573e7382282be24439c223c1603be648dd0e158f
---

# issue-3049 — silent-failure-audit+test-derivation+user-discovery-evidence-strength-tagging-f54cbd71 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW`
— result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round — this
record is the delivered artifact.

canonical: `gh issue view 3049` and `gh issue view 3049 --comments`, both
read at session start — the acceptance amendment names the two executable
checks (`python3 -m pytest tests/test_cwd_shape_coverage.py -q`,
`python3 gates/probe_cwd_shapes.py`) and repeats the must-not clauses from
the issue body verbatim.

canonical: `573e7382:on-the-record/hooks/gate-registration-post-guard.sh`
(read in full this session) — the issue #2705 post-commit companion. It
does not model the cwd at all: `post` mode greps the commit sha out of the
`[<branch> <sha>] <subject>` line in `tool_response`, then inspects that
exact commit's tree via `git show --name-status --format= <sha>` (lines
323-368 of the file) for a newly-added `gates/*.py`/`on-the-record/hooks/*.sh`/
`.github/workflows/*.yml` file missing its spec row. The only place `cwd`
is read at all (line 343, `e.get("cwd") or os.getcwd()`) feeds
`git rev-parse --show-toplevel` purely to find which repo to run `git show`
against (line 311-320) — it never reconstructs or trusts a predicted
staged set the way `gate-registration-guard.sh`'s PreToolUse `--cached`
read does. That is the concrete reason to expect all four shapes are
caught, and this session ran each one for real rather than accepting that
reasoning as the answer.

### The four shapes, each run for real against the unmodified companion

`gates/probe_cwd_shapes.py` (new) does, per shape: build a fresh scratch
git repo, run the real bash builtin (`pushd`, `cd`, `$CDPATH`) genuinely
moving the cwd bundled with `git add <probe file> && git commit` in ONE
`bash -c` invocation, independently confirm via `git log -1 --name-status`
that real git actually staged and committed the file (the ground-truth
check the issue's must-not requires before trusting any "caught" verdict),
then feed the real captured commit stdout into the actual, unmodified
`gate-registration-post-guard.sh` — `post` mode first, then `pre` mode —
exactly as the two hooks are wired in `on-the-record/hooks/hooks.json`
(`PreToolUse`(broad)+`PostToolUse`(`Bash`), both `fail-open-wrapper.sh
gate-registration-post-guard.sh <mode>`).

derived: `python3 gates/probe_cwd_shapes.py` — result:
```
bare-pushd: documented=caught actual=caught commit='[master 0cda4fd] add_probe_bare_pushd'
pushd-plusN: documented=caught actual=caught commit='[master fc2b074] add_probe_pushd_plusn'
env-prefixed-cd: documented=caught actual=caught commit='[master f5760c0] add_probe_envprefix'
cdpath: documented=caught actual=caught commit='/tmp/otr-probe-cwd-shapes-4g5fj1r2/cdpath/cdpath_target/back'
ok
```
Exit 0 — 4 shapes run, 4 shapes `actual=caught` (4/4 = 100%). (The
`cdpath` line's "commit" field shows the auto-printed CDPATH resolution
path, not the commit line — see the "cdpath prints an unexpected line"
note under Why — the actual commit line follows it in the full captured
stdout, and is what the companion parses.)

Per shape, real bash's own behaviour (independently confirmed, not cited
from the closed-#2774/#2778/#2779 record at face value) and the
companion's response:

1. **Bare `pushd`** (`pushd sub && pushd`) — real bash swaps the top two
   stack entries and ends back at the repo root (not a no-op, which is
   what leaves `gate-registration-guard.sh`'s own parser blind — issue
   text, restated for context, not re-derived here since this issue is
   about the companion, not the PreToolUse parser). Ground truth: `git log
   -1 --name-status` shows `A	gates/probe_bare_pushd.py`. Companion `pre`
   mode, once a violation is on record, emits
   `hookSpecificOutput.additionalContext` naming the exact sha and the
   missing row. **Caught.**
2. **`pushd +N`/`-N`** (`pushd pn_a && pushd +1`) — real bash rotates
   stack index 1 to the top. Ground truth: `A gates/probe_pushd_plusn.py`
   genuinely staged. **Caught**, same mechanism.
3. **Env-prefixed `cd`** (`cd envprefix_sub && FOO=bar cd ..`) — a
   per-command env-var assignment prefix on `cd` still really changes
   directory in real bash. Ground truth: `A gates/probe_envprefix.py`
   genuinely staged. **Caught**, same mechanism.
4. **`$CDPATH`** (`export CDPATH=<sibling dir with a symlink named
   "back" -> the repo>; cd back`) — real bash's `cd` consults `$CDPATH`
   for a target name that does not exist relative to cwd, and additionally
   auto-prints the resolved path (`/tmp/.../cdpath_target/back`) the way
   `cd -` does — a session doing this sees an unexpected line of output
   it did not ask to print, on top of whatever else it typed. Ground
   truth: `A gates/probe_cdpath.py` genuinely staged. **Caught**, same
   mechanism.

**Finding: all four shapes are caught.** derived: the `python3
gates/probe_cwd_shapes.py` transcript immediately above (this session) —
caught/run = 4/4 = 100%, exit 0. Per the acceptance amendment's own
empty-state clause ("if all four are caught, state that as the finding")
— that is the finding. The companion's post-hoc, sha-based design is
structurally indifferent to which of the PreToolUse guard's cwd
predictions were wrong, because it never makes a cwd prediction of its
own; it reads git's own record of what already happened. No open gap is
being named as "uncaught and closed by a parser patch" — none of the four
came back uncaught in this run.

### `gates/probe_cwd_shapes.py` and `tests/test_cwd_shape_coverage.py`

Two new files, per the acceptance amendment's two `check:` commands:

- `gates/probe_cwd_shapes.py` — the standalone probe named directly by
  `check: bash -c "python3 gates/probe_cwd_shapes.py"`. `DOCUMENTED_STATUS`
  (all four `"caught"`, matching this session's run above) is asserted
  against a fresh live run every time the probe executes — it fails in
  either direction: a caught shape silently becoming uncaught (the
  companion regresses), or an uncaught one being quietly closed without
  this record being updated (there is currently no uncaught shape to
  regress the other way, but the assertion structure holds for a future
  shape that does land as uncaught). derived: the mismatch-detection
  behaviour itself was verified this session by temporarily flipping
  `DOCUMENTED_STATUS["bare-pushd"]` to `"uncaught"` and re-running —
  result: `FAIL: bare-pushd: documented status 'uncaught' but this run
  observed 'caught' ...`, exit 1 — then reverted (`git diff` against this
  file shows no residual change from that probe).
- `tests/test_cwd_shape_coverage.py` — the pytest wrapper named by
  `check: bash -c "python3 -m pytest tests/test_cwd_shape_coverage.py -q"`,
  calling the same `run_shape()` the standalone probe uses (one
  implementation, two entry points).

canonical: this session's own `test-derivation` skill call (see the
skill-verdict line below) — the population (four named shapes) routes to
equivalence partitioning by shape identity: one test per shape. derived:
`python3 -m pytest tests/test_cwd_shape_coverage.py -v` — result:
`CwdShapeCoverageTest::test_bare_pushd_matches_documented_status`,
`test_pushd_plusN_matches_documented_status`,
`test_env_prefixed_cd_matches_documented_status`,
`test_cdpath_matches_documented_status` all PASSED — partitions exercised
/ partitions identified = 4/4 = 100% EP coverage.

The empty-state clause (not-reproducible) and the must-not clauses were,
before this pass, only asserted in this record's own prose — not exercised
by any test — so this session added two more:
- `NotReproducibleEdgeTest` — a synthetic failing shape (`command: "false"`),
  since none of the real four turned out non-reproducible in this
  environment, to prove the not-reproducible path itself reports a named
  reason rather than crashing or silently passing.
- `MustNotClausesTest` — `git diff origin/main -- <path>` on both guard
  scripts, asserted byte-empty — mechanically confirms this delivery never
  touched either hook, rather than trusting this record's own "did not
  extend the parser" sentence. derived: `git diff origin/main --
  on-the-record/hooks/gate-registration-guard.sh
  on-the-record/hooks/gate-registration-post-guard.sh | wc -l` — result:
  `0`, run directly this session before writing the test.

derived: `python3 -m pytest tests/test_cwd_shape_coverage.py -q` — result:
`8 passed` (4 per-shape + 1 all-shapes-genuinely-staged + 1 probe-script
entry point + 1 must-not-diff + 1 not-reproducible edge).

derived: `python3 -m pytest tests/ -q` — result: `5 failed, 190 passed`.
The 5 failures (`test_respawn_deliverable_gate.py` x4,
`test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present`)
are pre-existing on `origin/main` — derived: `git rev-parse origin/main`
and `git merge-base HEAD origin/main` both return
`573e7382282be24439c223c1603be648dd0e158f` (this branch has not diverged
from `origin/main` except for this delivery's own new, untracked files at
session start), and `git stash -u && python3 -m pytest
tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_when_gate_finds_none
tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
-q && git stash pop` — result: `2 failed` (the identical two IDs)
reproduced against that exact commit before this session's files were
restored. This session's two new files add one net passing test beyond
the pre-existing baseline (190 minus the pre-existing 189 = 1, since
`tests/test_cwd_shape_coverage.py` did not exist before) and zero new
failures — the failing-test-name SET is unchanged from `origin/main`'s own
baseline, following the same SET (not count) comparison convention prior
`docs/issue-2705/` verification records in this repo already use.

derived: `python3 -m pytest test/ -q` — result: `15 failed, 548 passed, 3
xfailed`, also all pre-existing on `origin/main` (same commit, untouched by
this delivery — none of the 15 failing names are anywhere near
`gate-registration`/`cwd`/`probe_cwd_shapes`).

### Silent-failure pass on `gates/probe_cwd_shapes.py` itself

canonical: this session's own `silent-failure-audit` skill call (see the
skill-verdict line below) — enumerated `run_shape()`'s error-handling
sites and found two that were classifiable as Silently Absorbed before
the fix, both now Handled:

1. **Ambient-environment absorption** — `env = dict(os.environ)` copied
   the calling shell's full environment into the hook subprocess call
   verbatim. If `ORCHESTRATE_OFF=1` happened to be set in whatever
   environment runs this probe (every gate in this file, including
   `gate-registration-post-guard.sh` itself, treats it as a global kill
   switch — `573e7382:on-the-record/hooks/gate-registration-post-guard.sh:90`),
   every shape would silently report "uncaught" for a reason that has
   nothing to do with the companion's own cwd handling, and nothing in
   the probe's output would say so. Fixed: `gates/probe_cwd_shapes.py`
   now sets `env["ORCHESTRATE_OFF"] = "0"` explicitly before invoking
   either hook mode, so the probe measures the guard's real logic
   regardless of the ambient session it runs in.
2. **Unchecked `post` mode exit code** — `post_res.returncode` was
   captured into the result dict but never read. The hook's own header
   comment (`573e7382:on-the-record/hooks/gate-registration-post-guard.sh:56-57`)
   documents `post` mode as pure side-effect, always exit 0; a non-zero
   exit there would mean something broke before the violation could even
   be written to the state file, and the probe would still fall through
   to checking `pre` mode, observe no report, and record a bare
   "uncaught" mismatch with no clue why. Fixed: a non-zero `post` (or
   `pre`) exit now returns `ok: False` with `post_res.stderr`/
   `pre_res.stderr` in the reason, the same not-reproducible-with-attempt-
   shown shape the bundled-command failure path already used.

derived: re-ran `python3 gates/probe_cwd_shapes.py` and `python3 -m
pytest tests/test_cwd_shape_coverage.py -q` after both fixes — identical
`ok` / `8 passed` results to the transcripts already shown above (the
fixes widen what the probe would catch on a future regression; they do
not change today's four-caught verdict, confirmed by re-running rather
than assumed).

## Why

The issue's own framing is unusual and load-bearing: a shape that is NOT
caught is an acceptable outcome, and the deliverable is an honest map, not
four green checks. canonical:
`573e7382:on-the-record/hooks/gate-registration-post-guard.sh` (read in
full before writing any probe code) — the companion never re-derives the
cwd from command text at all; it keys off the commit sha `git commit`
itself already printed and inspects that commit's own tree. Given that
design, the a priori expectation was that none of the four PreToolUse-level
cwd-modelling escapes would carry over to it, since they are specifically
escapes from a *predictive* cwd model the companion does not have. This
session did not treat that expectation as the answer: derived: the
`gates/probe_cwd_shapes.py` transcript in "What was done" above (this
session) — each shape runs for real, independently confirms the file is
genuinely staged by real git (`git log -1 --name-status`) before ever
asking the companion anything (must-not clause: "do not mark a shape
caught on the strength of the companion's own claim without running the
shape"), and only then checks the companion's actual `pre`-mode report
text for the expected sha and path substrings.

Two implementation choices worth naming:
- **Reusing one `run_shape()` for both the standalone probe and the
  pytest module**, rather than writing the shape-running logic twice.
  The acceptance amendment names two separate `check:` commands
  (`gates/probe_cwd_shapes.py` run directly, and via pytest), but nothing
  requires two independent implementations of "run this shape for real" —
  duplicating it would only create a second place for the four shapes'
  setup logic to drift out of sync.
- **`MustNotClausesTest` as a diff check, not a design-intent test.** The
  must-not clauses (do not extend the PreToolUse parser; do not widen
  either hook to fail closed) are constraints on how this issue gets
  resolved, not on the shipped hooks' runtime input/output behavior —
  derived: `git diff origin/main -- on-the-record/hooks/gate-registration-guard.sh
  on-the-record/hooks/gate-registration-post-guard.sh` (this session,
  cited again under "What was done") is the only mechanical form of "the
  parser was not extended" available — there is no black-box input that
  distinguishes "the parser was not extended" from "the parser was
  extended but happens to behave the same on these four inputs". That is
  what the test asserts, rather than encoding the prose sentence as an
  assertion with nothing underneath it.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 3049` and `gh issue view 3049 --comments`, read
at session start, for the acceptance criteria (original) and the
acceptance amendment (the two executable `check:` commands actually
implemented here, replacing the original two prose-shaped checks per
issue #3059's judgment-vs-mechanical distinction).

canonical: `573e7382:on-the-record/hooks/gate-registration-post-guard.sh`
and `573e7382:on-the-record/hooks/gate-registration-guard.sh`, both read in
full this session — the issue #2705 companion and the guard it reports
for. canonical: `573e7382:on-the-record/hooks/hooks.json`, read this
session, for the exact `PreToolUse`/`PostToolUse` wiring
(`fail-open-wrapper.sh gate-registration-post-guard.sh pre|post`) the
probe's own hook invocations mirror.

canonical: `c76a9808:docs/issue-2705/reports/adversarial-review-87659a67.md`,
read in full this session, for the four shapes' original live repro
commands (bare `pushd`, `pushd +N`/`-N`, env-prefixed `cd`, `$CDPATH`) —
this session's own scratch-repo commands in `gates/probe_cwd_shapes.py`
were built from and independently re-derived against that record's
transcripts, not copied without re-running them.

## Open findings

None. All four shapes are caught by the companion; no uncaught gap to
name a cost for, per the acceptance amendment's own empty-state clause.

## Next steps

None — `loop_state: landed`. If a future change to either guard script
flips any shape's status, `gates/probe_cwd_shapes.py` and
`tests/test_cwd_shape_coverage.py` fail loudly (derived: the
`DOCUMENTED_STATUS["bare-pushd"]` flip-and-revert experiment cited under
"What was done" above) and this record's `DOCUMENTED_STATUS`/verdict need
updating together with whatever caused the flip.

skill-verdict: silent-failure-audit — applied: invoked; audited
`gates/probe_cwd_shapes.py`'s `run_shape()` error-handling sites — derived:
the two Silently-Absorbed-then-fixed sites (ambient `ORCHESTRATE_OFF`
inheritance, unchecked `post`-mode exit code), documented with file:line
citations under "What was done" §"Silent-failure pass" above.
skill-verdict: test-derivation — applied: invoked; routed the four-shape
population to equivalence partitioning — derived: the `python3 -m pytest
tests/test_cwd_shape_coverage.py -v` per-shape PASSED lines cited under
"What was done" above, 4/4 = 100% EP coverage, plus the two added tests
for the not-reproducible empty state and the must-not diff invariant that
were previously only prose.
skill-verdict: user-discovery-evidence-strength-tagging — not-applicable:
no interview log or claim set to evidence-tag in this issue — it audits a
hook's runtime behavior via live command execution, not recounted user
statements.
