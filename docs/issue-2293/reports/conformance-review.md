---
issue: 2293
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: roles/specs/conformance-review.spec.json
    sha: same-commit
subject: PR #2306 (tokenmaxxxer/on-the-record) — admission-time refusal of
  degenerate/issue-number-shaped tasks + watchdog adhoc-visibility, branch
  issue-2293/implementation, head 760390cceaa1b4aeac018460a08a39d1076f614b
test: issue #2293 body (`## Ask` items 1-3, `## Acceptance`) plus the
  consumer scope-addition comment
  (https://github.com/tokenmaxxxer/on-the-record/issues/2293#issuecomment-5404799228),
  decomposed into REQ-A..REQ-M3 below
result: failed
assertedBy: issue-2293/conformance-review session (builder-blind), 2026-08-25
---

# issue-2293 — conformance-review record

## What was done

Builder-blind conformance review of PR #2306 against issue #2293's frozen
`## Ask` / `## Acceptance` text plus the consumer's follow-up "scope
addition" comment, independent of PR #2306's own
`760390cceaa1b4aeac018460a08a39d1076f614b:docs/issue-2293/reports/implementation.md`
self-assessment (untracked on this `conformance-review` branch, PR-only
path, hence the sha pin). `CORE_BUILD_NOW=1` was set on this session
(delivery-only bypass, contract v3 s19a) — this record is delivered
directly, no phase-1 proposal round.

canonical: `gh issue view 2293`, `gh pr view 2306`, then `git fetch origin
pull/2306/head:pr-2306` + `git worktree add /tmp/pr2306-check pr-2306`
(PR #2306 head `760390cceaa1b4aeac018460a08a39d1076f614b`), and a second
worktree `git worktree add /tmp/main-check main` (`main`
`aa1f5069ba90e6d3cf4adf0c16d4c1db7eb31d3a`) to isolate regressions from
pre-existing failures — all commands run live this session; both
worktrees removed after use.

Requirement extraction (conformance-review-requirement-extraction): `##
Ask` item 1 bundles refusal + message + override ("and" — rule 1) → split
into REQ-A/REQ-B/REQ-C. Item 2 bundles the ADHOC tag + task-first-words
naming → REQ-D/REQ-E. Item 3 (frozen constraint) has three clauses →
REQ-F/REQ-G/REQ-H. The scope-addition comment names two independent
fixes (isolation, log path) joined by "and" → REQ-I/REQ-J (the comment's
own "or refuse without one" alternative folded into REQ-I as one item —
one obligation with two acceptable satisfying shapes, not two
obligations). `## Acceptance` has `gate` (REQ-K), `empty state` (REQ-L),
and `provenance` (three independently executable live-run clauses joined
by "and" — REQ-M1/M2/M3). No summary line met the rule-3 drop threshold.

Requirement list below (derived: one `---`-delimited block per entry in
`## Open findings`, REQ-A through REQ-M3 = 15 blocks total; counted
directly off the issue/comment text quoted in `gh issue view 2293`'s
output this session — full enumeration, no sampling needed):
- **REQ-A** (functional) — refuse admission, before any session starts,
  when the positional `task` is bare-numeric / `#`-prefixed-numeric /
  `-`-prefixed-numeric and `--issue` was not given.
- **REQ-B** (error-handling) — the refusal message names the
  almost-certain intent with a did-you-mean `--issue` suggestion.
- **REQ-C** (edge-case, conditional on REQ-A) — an explicit override flag
  bypasses REQ-A for the rare legitimate numeric-task case.
- **REQ-D** (functional) — every watchdog/poll diagnosis line for a
  no-`--issue` (adhoc) entry says "adhoc" prominently, HEALTHY included.
- **REQ-E** (functional, paired with REQ-D) — that diagnosis also names
  the task's first words.
- **REQ-F** (scope-boundary) — the fix is systemic for all consumer
  sessions, not consumer-specific.
- **REQ-G** (scope-boundary) — no added overhead/conflict/stall surfaces.
- **REQ-H** (scope-boundary) — nothing in the consumer tree.
- **REQ-I** (edge-case, scope-addition) — adhoc/no-`--issue` spawns get
  an isolated workspace instead of running in the caller's cwd, or refuse
  without one.
- **REQ-J** (error-handling, scope-addition) — adhoc/no-`--issue` spawns
  get a timestamped+PID log path (`pipeline.py` `_session_log_path`
  precedent), not the shared `runs/last-session.log`.
- **REQ-K** (functional/evidence) — gate: `tests/test_spawn_pipeline.py`.
- **REQ-L** (edge-case) — empty state: a normal spawn with a real task
  and `--issue` is byte-identical, no new prompts.
- **REQ-M1** (evidence) — provenance: run `spawn.py implementation 538`
  verbatim post-fix, paste the refusal with its suggestion.
- **REQ-M2** (evidence) — provenance: run the override path, show the
  adhoc-labeled watchdog line.
- **REQ-M3** (evidence) — provenance: run a normal spawn showing no
  change.

## Why

Builder-blind re-derivation per this role's mandate: every verdict below
came from this session's own reading of PR #2306's actual diff and two
isolated worktrees (PR head, clean `main`), not from PR #2306's own
implementation record's account — per verdict-assignment rule 6
(re-check an Absent/Incorrect-leaning verdict against the artifact before
finalizing). Two findings below (REQ-I, REQ-J) trace directly to the
consumer's own incident report — the scope-addition comment names the
exact mechanism (`작업 디렉터리 .`, shared `runs/last-session.log`) that
caused the original pollution and log-overwrite damage, so those two
clauses got the closest scrutiny of any item in this review.

## Upstream basis

- `roles/specs/conformance-review.spec.json` (`sha: same-commit`, this
  record's own EARL field/vocabulary source, no local diff this session).
- PR #2306 (`tokenmaxxxer/on-the-record`, branch `issue-2293/implementation`,
  head `760390cceaa1b4aeac018460a08a39d1076f614b`) — `pipeline.py`,
  `spawn.py`, `watchdog.py`, `tests/test_admission_checklist.py`,
  `tests/test_spawn_gate_wiring.py`, `tests/test_spawn_pipeline.py`,
  `pytest.ini` — all read via `git diff main...pr-2306` and a local
  worktree checkout of `pr-2306`, this session.
- `main` at `aa1f5069ba90e6d3cf4adf0c16d4c1db7eb31d3a` — used as the
  pre-change baseline for every "is this pre-existing?" check below
  (REQ-D/REQ-K's cited pre-existing failure, REQ-I/REQ-J's untouched
  code paths).
- Issue #2293 comment `issuecomment-5404799228` (the "scope addition"
  from the consumer's full incident report) — source of REQ-I/REQ-J.

## Open findings

Full requirement ledger below (REQ-A through REQ-M3 = 15 `---`-delimited
blocks, derived: one block per requirement); the non-`Present` entries
(REQ-B, REQ-I, REQ-J, REQ-K) are this record's substantive open findings
and are named again with resolution paths at the end of this section.

---
requirement: refuse admission, before any session starts, when `task` is
  bare-numeric/`#`/`-`-prefixed-numeric and `--issue` is absent (REQ-A)
canonical: this session's own independent pytest re-run plus a live CLI
repro, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 1 (refusal clause)
verdict: Present
evidence: `760390cc:pipeline.py:1462` (`_DEGENERATE_TASK_RE =
re.compile(r"^[#-]?\d+$")`) and `pipeline.py:1465-1496`
(`_admission_check_degenerate_task`); `spawn.py:2293-2294`
(`ADMISSION_CHECKS` row `("degenerate-task",
_admission_check_degenerate_task)`); `spawn.py:2329-2336`
(`admission_gate({..., "task": task, ...})`)
rationale: independent live CLI run, PR head worktree:
```
$ python3 spawn.py implementation 538 -C .
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538
(pass --force-adhoc-task to spawn a genuinely numeric-task adhoc session)
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind.
```
canonical: pasted live run above — executed-live, this session; refusal
fires before any session/workspace exists, matching the clause exactly.
Independent unit-test re-run, PR head worktree:
```
$ python3 -m pytest tests/test_admission_checklist.py -q
30 passed in 18.17s
```
canonical: pasted pytest run above — executed-live, this session.

---
requirement: the refusal message names the almost-certain intent with a
  did-you-mean `--issue` suggestion (REQ-B)
canonical: this session's own live CLI run and direct inspection of the
print statement, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 1 (message clause: `did you
  mean: spawn.py <role> "<task>" --issue 538`)
verdict: Incorrect
evidence: `760390cc:pipeline.py:1491-1495`
```
print(f"[admission] degenerate-task: task {task!r} looks like an issue "
      f"number; did you mean: spawn.py {ctx.get('role')} \"<task>\" "
      f"--issue {number}\n"
      f"(pass --force-adhoc-task to spawn a genuinely numeric-task "
      f"adhoc session)", file=sys.stderr)
```
rationale: `{ctx.get('role')}` is correctly interpolated (prints
`implementation`) but `\"<task>\"` is a literal string, not
`{task!r}` — re-checked live twice (rule 6), both via direct function
call and the full CLI:
```
$ python3 -c "
import pipeline
ctx = {'role': 'implementation', 'task': '538', 'issue': None, 'force_adhoc_task': False}
pipeline._admission_check_degenerate_task(ctx)
"
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538
```
canonical: pasted run above, plus the identical CLI-level run pasted in
REQ-A's finding — both executed-live, this session.
`tests/test_admission_checklist.py` asserts only the boolean return and
the ledger's `item` field
(`test_bare_numeric_task_without_issue_refuses_named`,
`test_hash_prefixed_numeric_task_also_refuses`, etc., all within the
`30 passed` run pasted in REQ-A) — no test asserts on the printed
message's content, so this bug is untested and would ship.
spec_vs_built: issue #2293 asked for a suggestion naming the actual
almost-certain intent — a command a caller could act on. The built
message correctly substitutes the role and the derived issue number
(538) but prints the literal four-character placeholder `<task>` where
the actual task text belongs, so the suggested command
(`spawn.py implementation "<task>" --issue 538`) is not the corrected
command a caller typed — copy-pasting it verbatim passes the literal
string `<task>` as the new task, not `538` or whatever the original task
text was.

---
requirement: an explicit override flag bypasses REQ-A for the rare
  legitimate numeric-task case (REQ-C)
canonical: this session's own live CLI run (`--dry-run`) plus unit-test
re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 1 (override clause)
verdict: Present
evidence: `760390cc:spawn.py:1200-1207` (`--force-adhoc-task` argparse
flag); `pipeline.py:1487` (`if ctx.get("force_adhoc_task") or
ctx.get("issue") is not None: return True`)
rationale: independent live run, PR head worktree:
```
$ python3 spawn.py implementation 538 --force-adhoc-task -C . --dry-run
... (dry-run hook/model JSON, no admission refusal) ...
--model sonnet
```
canonical: pasted run above — executed-live, this session; admission is
not refused with the override present.
`test_force_adhoc_task_override_admits` is independently re-run as part
of the `30 passed` `test_admission_checklist.py` run pasted in REQ-A.

---
requirement: every watchdog/poll diagnosis for a no-`--issue` entry says
  "adhoc" prominently, HEALTHY included (REQ-D)
canonical: this session's own live `diagnose_health()` call plus
unit-test re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 2 (ADHOC-tag clause)
verdict: Present
evidence: `760390cc:watchdog.py:271-282` (`adhoc_prefix` computed when
`entry.get("issue") is None`, prepended to `d["detail"]` inside
`_diagnosis()`)
rationale: independent live call, PR head worktree, reproducing the exact
incident scenario (a HEALTHY adhoc entry):
```
$ python3 -c "
import spawn, tempfile, os, time
from pathlib import Path
with tempfile.TemporaryDirectory() as td:
    log = Path(td) / 's.log'; log.write_text('{\"type\":\"text\"}\n')
    entry = {'log': str(log), 'work': None, 'ts': time.time(), 'pid': os.getpid(),
             'issue': None, 'role': 'implementation', 'task': '538'}
    out = spawn.diagnose_health('k', entry, state={})
    print(out['state'], '|', out['detail'])
"
HEALTHY | ADHOC task="538" — k: 최근 로그 성장, RUNNING
```
canonical: pasted run above — executed-live, this session; a HEALTHY line
for this entry can no longer be misread as "your issue-N spawn is fine",
which is the exact live-incident failure mode. Independent unit-test
re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py -q
1 failed, 69 passed in 53.13s
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
```
canonical: pasted pytest run above — executed-live, this session; the one
failure reproduces identically on clean `main`
(`aa1f5069ba90e6d3cf4adf0c16d4c1db7eb31d3a`):
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace -q -n0
1 failed in 9.96s
```
canonical: pasted `main`-worktree run above — executed-live, this
session, confirming the failure predates this diff.

---
requirement: the same diagnosis names the task's first words (REQ-E)
canonical: same live call as REQ-D, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 2 (task-naming clause)
verdict: Present
evidence: `760390cc:watchdog.py:276-277` (`task_preview = "
".join((entry.get("task") or "").split()[:8])`)
rationale: the live call pasted in REQ-D's finding above prints
`ADHOC task="538" — ...` — `task="538"` is exactly this clause's naming
requirement, produced by the same one call cited there. canonical: same
pasted output as REQ-D above.

---
requirement: the fix is systemic for all consumer sessions, not
  consumer-specific (REQ-F)
canonical: this session's own inspection of the call sites, PR head
worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 1)
verdict: Present
evidence: `760390cc:spawn.py:2293-2294` (`ADMISSION_CHECKS` row, run
unconditionally for every `spawn.py <role> <task>` invocation);
`760390cc:watchdog.py:271-282` (`_diagnosis()` applied unconditionally
inside `diagnose_health()`, the single code path used for every roster
entry regardless of target repo)
rationale: neither new code path is gated behind a consumer identity,
repo slug, or config flag — both run for every admission/diagnosis call
in the shared orchestrator, not scoped to the repo the #2293 incident
happened in. canonical: static inspection of the two cited files' full
bodies this session, no conditional branch on repo/consumer identity
found in either.

---
requirement: no added overhead/conflict/stall surfaces (REQ-G)
canonical: this session's own inspection of the new code's I/O profile,
PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 2)
verdict: Present
evidence: `760390cc:pipeline.py:1465-1496` (`_admission_check_degenerate_task`
— one regex match against an already-in-memory `ctx` dict, no
subprocess/network call); `760390cc:watchdog.py:271-282` (string-prefix
operation on an already-computed `detail` value)
rationale: both additions are synchronous, in-process, and O(1) on
already-available data — no new subprocess, network call, lock, or wait
introduced; the function's own docstring states this explicitly
("Deterministic and purely local (no gh/network call)"). canonical:
static inspection of both function bodies this session, no I/O call
found in either beyond the pre-existing `print(..., file=sys.stderr)`.

---
requirement: nothing in the consumer tree (REQ-H)
canonical: this session's own `git diff --stat` re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 3)
verdict: Present
evidence: `git diff main...pr-2306 --stat`
```
$ git diff main...pr-2306 --stat
.orchestrate-hook-fires.log                        |  12 +
docs/issue-2293/reports/implementation.md          | 353 +++++++++++++++++++++
.../2026-08-25-hunt-degenerate-task-admission-refusal.md |  45 +++
.../reports/implementation/deviation-log.md        |   4 +
pipeline.py                                        |  37 +++
pytest.ini                                         |   2 +-
spawn.py                                           |  23 +-
tests/test_admission_checklist.py                  |  58 ++++
tests/test_spawn_gate_wiring.py                    |  23 ++
tests/test_spawn_pipeline.py                       |  29 ++
watchdog.py                                        |  11 +-
```
canonical: pasted diff-stat above — executed-live, this session; every
path is inside `on-the-record` itself, none under any consumer repo.
Caveat, not scored against this narrow clause: this Present verdict
covers only the lines this PR added — it does not mean the underlying
consumer-tree-pollution mechanism from the original incident is fixed;
see REQ-I below (Absent) for that.

---
requirement: adhoc/no-`--issue` spawns get an isolated workspace instead
  of running in the caller's cwd, or refuse without one (REQ-I)
canonical: this session's own inspection of `-C`/`--cwd` resolution and
`_spawn_one()`'s call site, PR head worktree, cross-checked against the
scope-addition comment's incident description.
spec_ref: issue #2293 comment `issuecomment-5404799228` ("adhoc/no-issue
  spawns still get an isolated workspace (or refuse without one)")
verdict: Absent
evidence: `760390cc:spawn.py:1105`
(`ap.add_argument("-C", "--cwd", default=".", ...)`) — unconditional
default, no branch on `a.issue`; `760390cc:spawn.py:1535-1545`
(`_spawn_one(a.cwd, a.role, a.task, ..., a.issue, ...)`) passes the
caller's cwd through unchanged whether or not `--issue` was given
rationale: `git diff main...pr-2306 -- spawn.py pipeline.py watchdog.py`
(pasted in REQ-H's finding above, no `-C`/`--cwd`/workspace-isolation
hunk present) touches zero lines in either cited location or anywhere
else related to workspace resolution/isolation; no admission check in
the new `ADMISSION_CHECKS` row (or any existing row) inspects `issue is
None` to require or create an isolated workspace, and none refuses an
adhoc spawn for lacking one. canonical: `git diff main...pr-2306 -- spawn.py |
grep -n '"-C"'` returns only the pre-existing argparse definition line
(`1105`), no new hunk — executed-live, this session. The exact incident
mechanism the comment describes ("작업 디렉터리 .") is unchanged.
spec_vs_built: the comment asked for adhoc/no-`--issue` spawns to either
get an isolated workspace or be refused without one — a direct fix for
the incident where a degenerate-task adhoc spawn ran in the caller's cwd
and created 40 untracked files under a consumer repo's `frontend/src`,
later breaking an unrelated PR's build. PR #2306 built the REQ-A/B/C/D/E
admission-and-visibility fixes only; it does not touch `-C`/`--cwd`
resolution at all, so a *non*-degenerate-task adhoc spawn (or one passed
with `--force-adhoc-task`) still runs directly in the caller's cwd with
no isolation and no refusal added.

---
requirement: adhoc/no-`--issue` spawns get a timestamped+PID log path,
  not the shared `runs/last-session.log` (REQ-J)
canonical: this session's own inspection of the log-path branch, PR head
worktree, cross-checked against `main`.
spec_ref: issue #2293 comment `issuecomment-5404799228` ("a
  timestamped+PID log path like issue-scoped spawns (pipeline.py:958
  precedent)")
verdict: Absent
evidence: `760390cc:spawn.py:2835-2836`
```
log_path = (_session_log_path(cwd) if issue is not None
            else ROOT / "runs" / "last-session.log")
```
rationale: byte-identical to `main:spawn.py:2835-2836` —
```
$ git diff main...pr-2306 -- spawn.py | grep -n "last-session"
$ echo "exit: $?"
exit: 1
```
canonical: pasted grep above (no output, exit 1 = no match) — executed
live, this session; `_session_log_path()` (the timestamped+PID helper
the comment cites, `pipeline.py:972` on `main`, unchanged) is only ever
called for the `issue is not None` branch, both before and after this
PR. A second degenerate-task mistake — or any two ordinary adhoc spawns
run back-to-back — still overwrite each other's `runs/last-session.log`
exactly as the incident report describes.
spec_vs_built: the comment named this as one of two required fixes
(isolation, log path) alongside REQ-I, citing `pipeline.py:958` as the
existing precedent mechanism to reuse for adhoc spawns too. PR #2306
does not touch this line or call site; the shared-log-overwrite failure
mode from the incident is unfixed.

---
requirement: gate `tests/test_spawn_pipeline.py` (REQ-K)
canonical: this session's own re-run of the named gate file plus a diff
of its own changes, PR head and `main` worktrees.
spec_ref: issue #2293 body, `## Acceptance`, `gate` line
verdict: Incorrect
evidence: `git diff main...pr-2306 -- tests/test_spawn_pipeline.py`
(29 lines, all `@pytest.mark.xdist_group(name="role_model_config")`
decorators plus save/restore of `ROLE_MODEL_CONFIG` around the
pre-existing role-model tests)
rationale: independent re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_pipeline.py -q
86 passed in 9.31s
```
canonical: pasted run above — executed-live, this session. But:
```
$ grep -ni "degenerate\|adhoc\|force_adhoc" tests/test_spawn_pipeline.py
$ echo "exit: $?"
exit: 1
```
canonical: pasted grep above (no output, exit 1 = no match) — executed
live, this session; none of the 86 passing tests in this file exercises
REQ-A through REQ-E, and the PR's own changes to this file are an
unrelated xdist role-model-config race fix (its commit message reads
"fix test_spawn_pipeline.py role-model xdist race + isolation gap",
consistent with `pytest.ini`'s new `--dist=loadgroup` addopt in the same
diff). The feature's actual tests live in
`tests/test_admission_checklist.py` and `tests/test_spawn_gate_wiring.py`
instead (cited in REQ-A/B/C/D/E above).
spec_vs_built: the Acceptance section names `tests/test_spawn_pipeline.py`
specifically as this issue's gate. The delivered feature is well
tested — but not by the named gate file, which passing in full says
nothing about the degenerate-task/adhoc-visibility behavior this issue
asked for. A CI run scoped to the named gate would not catch a
regression in REQ-A through REQ-E.

---
requirement: a normal spawn with a real task and `--issue` is
  byte-identical, no new prompts (REQ-L)
canonical: this session's own structural diff of the admission-gate call
site plus a targeted unit-test re-run, PR head worktree.
spec_ref: issue #2293 body, `## Acceptance`, `empty state` line
verdict: Present
evidence: `760390cc:spawn.py:2329-2336` (`admission_gate({..., "task":
task, ..., "force_adhoc_task": force_adhoc_task})` — two new keys added
to the ctx dict passed to every admission check)
rationale: none of the pre-existing `ADMISSION_CHECKS` rows
(`approve-token`, `directive-completeness`, `watch-registration`, etc.)
read a `"task"` or `"force_adhoc_task"` key, so their behavior is
unchanged by the new keys' presence, and
`_admission_check_degenerate_task` itself short-circuits whenever
`ctx.get("issue") is not None` (`pipeline.py:1487`, cited in REQ-C).
Targeted independent re-run, PR head worktree:
```
$ python3 -m pytest tests/test_admission_checklist.py -q -k test_issue_given_skips_degenerate_task_check
1 passed in 0.98s
```
canonical: pasted run above — executed-live, this session. A full live
`--issue`-flagged spawn CLI run was attempted this session but confounded
by an unrelated pre-existing acceptance-gate/requirement-linkage check
firing on a nonexistent placeholder issue number — Analysis (structural
diff + this targeted test), not a clean live-CLI Test, is this finding's
actual method.

---
requirement: provenance — run `spawn.py implementation 538` verbatim
  post-fix, paste the refusal with its suggestion (REQ-M1)
canonical: this session's own live run, PR head worktree (same run
pasted under REQ-A).
spec_ref: issue #2293 body, `## Acceptance`, `provenance` line, clause 1
verdict: Present
evidence: pasted live run under REQ-A above
rationale: the exact command from the incident, run verbatim, refuses
with a suggestion attached — satisfying this clause's process
requirement. The suggestion's own content accuracy is scored separately
under REQ-B (Incorrect); this clause only asks that the run happen and
produce a refusal-plus-suggestion, which it does. canonical: same pasted
run as REQ-A above.

---
requirement: provenance — run the override path, show the adhoc-labeled
  watchdog line (REQ-M2)
canonical: this session's own live runs, PR head worktree (same runs
pasted under REQ-C and REQ-D).
spec_ref: issue #2293 body, `## Acceptance`, `provenance` line, clause 2
verdict: Present
evidence: pasted live runs under REQ-C (override admits) and REQ-D
(resulting watchdog entry tagged `ADHOC task="538"`) above
rationale: both halves of this clause — the override succeeding, and the
resulting entry's watchdog line carrying the ADHOC tag — were
independently reproduced live this session. canonical: same pasted runs
as REQ-C and REQ-D above.

---
requirement: provenance — run a normal spawn showing no change (REQ-M3)
canonical: this session's own structural check plus targeted unit test,
same basis as REQ-L.
spec_ref: issue #2293 body, `## Acceptance`, `provenance` line, clause 3
verdict: Present
evidence: same as REQ-L
rationale: carried from REQ-L's Analysis-method finding above — the
`1 passed` targeted pytest run pasted there is this clause's own
evidence too; both check the same underlying claim from two angles
(acceptance's empty-state line vs. its provenance line). canonical: same
pasted run as REQ-L above.

---

Resolution paths for the non-`Present` findings above:

1. **REQ-B** (Incorrect) — fix the f-string at `pipeline.py:1492` to
   interpolate the actual task value (e.g. `{task!r}`) instead of the
   literal `"<task>"`, and add an assertion on the printed message's
   content to `tests/test_admission_checklist.py` so this class of bug
   is caught before merge next time.
2. **REQ-I** (Absent) — give adhoc/no-`--issue` spawns an isolated
   workspace (or an admission-time refusal when one can't be provided),
   per the scope-addition comment's own two-option framing.
3. **REQ-J** (Absent) — route adhoc/no-`--issue` spawns through
   `_session_log_path()` (or an equivalent timestamped+PID scheme)
   instead of the shared `ROOT / "runs" / "last-session.log"` fallback at
   `spawn.py:2836`.
4. **REQ-K** (Incorrect) — either add degenerate-task/adhoc-visibility
   coverage to `tests/test_spawn_pipeline.py` itself, or treat the
   Acceptance section's `gate` line as needing correction to name
   `tests/test_admission_checklist.py` / `tests/test_spawn_gate_wiring.py`
   instead, so the named gate and the actual feature coverage line up.

REQ-I and REQ-J are the more consequential pair: they are the two fixes
the consumer explicitly asked for after the admission-guard/watchdog work
already landed, and neither is present in PR #2306 at all — the
incident's actual damage mechanisms (consumer-tree pollution via cwd,
session-log overwrite) remain fully reproducible today.

## Next steps

None from this review's own side — `loop_state` above is this record
kind's terminal value, `reported`. For the owning role: PR #2306 should
not be treated as fully closing issue #2293 as currently scoped — the
issue's frozen Acceptance plus the scope-addition comment together name
findings that split into present-and-correct (REQ-A/C/D/E/F/G/H/L/M1/M2/M3)
and needing-rework (REQ-B/I/J/K), and `Closes #2293` on this PR overstates
what the needing-rework set alone would justify.

canonical: `gh pr view 2306 --json body -q .body` — result: `Closes
#2293` trailer present in the PR body pasted this session (see `## What
was done`); the recommendation above rests on the REQ-I/REQ-J/REQ-K
findings' evidence and rationale in `## Open findings` above.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2293's `## Ask`/scope-addition-comment/`## Acceptance` into REQ-A..REQ-M3 above (see "Requirement extraction" paragraph under `## What was done`)
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to choose live-CLI/Test evidence for REQ-A/B/C/D/E/K and Analysis (structural diff + a targeted existing test, no clean live-CLI run available) for REQ-L/M3, per each finding's `canonical:` line above
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used to grade REQ-B/REQ-K as Incorrect (not Absent — both are addressed-but-wrong, per rule 2) and REQ-I/REQ-J as Absent (no code touches the cited call sites at all), with each Incorrect/Absent finding's `spec_vs_built` naming the failing clause per rule 5
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used to pin every evidence citation above to file:line plus the `pr-2306`/`main` commit shas actually read this session, per rule 1
skill-verdict: conformance-review-finding-record — applied: invoked; used for this record's `---`-delimited per-requirement block shape (requirement/spec_ref/verdict/evidence/rationale/spec_vs_built) and the frontmatter's EARL field set
skill-verdict: conformance-review-sampling-derivation — not-applicable: the requirement set was small and fully enumerable (derived directly from the issue/comment/Acceptance text into the 15-block ledger above), so no sampling scope was needed
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting findings; the non-Present findings are recorded with resolution paths, not severity bands
other mounted skills: not triggered

## What did not work

Before-landing warrant hunt, stance 0:
`docs/issue-2293/reports/conformance-review/2026-08-25-hunt-conformance-review.md`
(committed `1cc65b14`).
```
$ git show 760390cc:spawn.py | sed -n '2290,2296p'
ADMISSION_CHECKS: list[tuple] = [
    ("degenerate-task", _admission_check_degenerate_task),
    ("approve-token", _admission_check_approve_token),
$ git show 760390cc:spawn.py | grep -n "return _spawn_one("
1535:    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
```
canonical: pasted `sed`/`grep -n` output above — executed-live, this
session. REQ-A/REQ-F's `ADMISSION_CHECKS` citation above reads
`spawn.py:2293-2294` (the hunt's target — the first draft had
`pipeline.py:2313`/`spawn.py:2313`, neither resolving to this
construct); REQ-I's `_spawn_one()` call-site range above reads
`1535-1545` (the first draft had `1536-1545`, omitting line 1535
itself); REQ-B's print-statement range above reads `1491-1495` (the
first draft had `1491-1494`, omitting the closing `"adhoc session)"`
line already visible in the code block pasted in REQ-B's own finding).

Every remaining citation was read or re-run live this session in
isolated worktrees, pasted throughout `## Open findings` above, and all
worktrees were removed after use.

Noted as an evidence/coverage gap in the artifact under review, not a
review-process failure: PR #2306's own record cites
`tests/test_spawn_pipeline.py` as passing without noting that file
contains no coverage of the feature it's named as the gate for (REQ-K,
see the `grep` result pasted there), and its did-you-mean message has an
unasserted content bug (REQ-B, see the live runs pasted there) that its
own test suite would not have caught.
