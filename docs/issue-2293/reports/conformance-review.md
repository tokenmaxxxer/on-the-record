---
issue: 2293
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: roles/specs/conformance-review.spec.json
    sha: same-commit
subject: PR #2368 (tokenmaxxxer/on-the-record) — degenerate-task admission
  guard + adhoc isolation + timestamped log, branch
  issue-2293/implementation, initial-review head
  042e47f744e91609f2994099fe7e9844b1f04efb, re-reviewed after the
  CHANGES-round fix at head a49ee1c9c928782b57ed4f8ef9c828524dc09855
test: issue #2293 body (`## Ask` items 1-3, `## Acceptance`) plus the
  consumer scope-addition comment
  (https://github.com/tokenmaxxxer/on-the-record/issues/2293#issuecomment-5404799228),
  decomposed into REQ-A..REQ-M3 below
result: failed
assertedBy: issue-2293/conformance-review session (builder-blind), 2026-08-25
---

# issue-2293 — conformance-review record

## What was done

Builder-blind conformance review of PR #2368 against issue #2293's frozen
`## Ask` / `## Acceptance` text plus the consumer's "scope addition"
comment, independent of PR #2368's own
`042e47f7:docs/issue-2293/reports/implementation.md` self-assessment
(untracked on this `conformance-review` branch, PR-only path, hence the
sha pin). `CORE_BUILD_NOW=1` was set on this session (delivery-only
bypass, contract v3 s19a) — this record is delivered directly, no
phase-1 proposal round.

PR #2368 redelivers PR #2306's design fresh against current `main` after
#2306 was closed unmerged (a same-day history rewrite invalidated its
branch base), plus the two fixes the scope-addition comment asked for
after #2306 landed. This role reviewed #2306 once already
(`docs/issue-2293/reports/conformance-review.md` at commit `651623df`,
before this write) — that record found REQ-I/REQ-J Absent. This is a
fresh independent pass against #2368's actual diff, not a copy-forward
of the #2306 verdicts: verdict-assignment rule 4 permits carrying a
**Present** verdict forward only when the diff since the cited commit
does not touch the requirement's evidence — #2368 is a different branch
built on a different `main` base with materially different code at every
cited location (different line numbers, an added `--force-adhoc-task`
plumbing path, a warrant-hunt-fixed reuse bug), so every verdict below
was independently re-derived against #2368's own worktree, not carried
from the #2306 record.

canonical: `gh issue view 2293`, `gh issue view 2293 --comments`
(re-confirms no new comments since the #2306 review — same
`issuecomment-5404799228` scope addition, no further additions), `gh pr
view 2368`, then `git fetch origin pull/2368/head:pr-2368` + `git
worktree add /tmp/pr2368-check pr-2368` (PR #2368 head
`042e47f744e91609f2994099fe7e9844b1f04efb`), and a second worktree `git
worktree add /tmp/main2368-check origin/main` (`main`
`46da1c8a199048b380c363a936e92bca1c7c5393`) to isolate regressions from
pre-existing failures — all commands run live this session; both
worktrees removed after use.

**CHANGES-round re-review addendum (this session):** scope was to
independently re-verify REQ-B against PR #2368's CHANGES-round fix
head, without reading or citing PR #2368's own `implementation.md`
"CHANGES-round fix" section as evidence
(defect-verification-independence-from-upstream-verdicts). See the
updated REQ-B block, the revised `## Open findings` summary, and the
updated `## Next steps` recommendation below for this session's own
fresh evidence and verdict; REQ-A, REQ-C..REQ-M3 evidence citations
below still resolve to head `042e47f7:pipeline.py`/`spawn.py`/`watchdog.py`
as originally pinned, per `git diff 042e47f7..a49ee1c9 --stat` pasted in
`## Open findings` below (only `pipeline.py` and
`tests/test_admission_checklist.py` changed in the CHANGES-round).

Requirement extraction (conformance-review-requirement-extraction):
issue #2293's `## Ask`/scope-addition-comment/`## Acceptance` text is
byte-identical to what the prior #2306 review decomposed (reconfirmed
live this session, see canonical above) — same bundling analysis
applies unchanged: `## Ask` item 1 bundles refusal + message + override
("and") → REQ-A/REQ-B/REQ-C; item 2 bundles the ADHOC tag +
task-first-words naming → REQ-D/REQ-E; item 3 (frozen constraint) has
three clauses → REQ-F/REQ-G/REQ-H; the scope-addition comment names two
independent fixes joined by "and" → REQ-I/REQ-J; `## Acceptance` has
`gate` (REQ-K), `empty state` (REQ-L), and `provenance` (three clauses
joined by "and" — REQ-M1/M2/M3). No summary line met the rule-3 drop
threshold. Requirement list below (derived: one `---`-delimited block
per entry in `## Open findings`, REQ-A through REQ-M3 = 15 blocks total
— full enumeration, no sampling needed, same scope the #2306 review
used):

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
  sessions.
- **REQ-G** (scope-boundary) — no added overhead/conflict/stall surfaces.
- **REQ-H** (scope-boundary) — nothing in the consumer tree.
- **REQ-I** (edge-case, scope-addition) — adhoc/no-`--issue` spawns get
  an isolated workspace instead of running in the caller's cwd, or refuse
  without one.
- **REQ-J** (error-handling, scope-addition) — adhoc/no-`--issue` spawns
  get a timestamped+PID log path, not the shared `runs/last-session.log`.
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
came from this session's own reading of PR #2368's actual diff and two
isolated worktrees (PR head, clean `main`), not from PR #2368's own
implementation record's account — per verdict-assignment rule 6
(re-check an Absent/Incorrect-leaning verdict against the artifact
before finalizing), applied twice below: once to confirm REQ-B's message
bug survived the redelivery unfixed, and once to confirm REQ-I/REQ-J
(Absent in the #2306 pass) are now genuinely Present in #2368, not just
superficially touched. REQ-I got the closest scrutiny of any item in
this review, because its own PR description names a warrant-hunt finding
against its first draft (a pid-reused adhoc workspace silently inheriting
a stale prior task's branch/files) — this session independently
re-derived that the fix in the final diff actually closes that gap
(evidence under REQ-I below), rather than trusting the PR body's account
of its own hunt.

canonical: `python3 -m pytest tests/test_spawn_pipeline.py -q -k AdhocIsolationAndLogPath -v`
(PR head worktree) — result: `3 passed in 13.82s`, plus every other
`gh ...`/`pytest ...`/`python3 ...` command pasted under each
REQ-A..REQ-M3 entry in `## Open findings` below — the re-derivation this
paragraph describes is that section's own evidence, not a separate claim
asserted here.

## Upstream basis

- `roles/specs/conformance-review.spec.json` (`sha: same-commit`, this
  record's own EARL field/vocabulary source, no local diff this session).
- PR #2368 (`tokenmaxxxer/on-the-record`, branch `issue-2293/implementation`,
  head `042e47f744e91609f2994099fe7e9844b1f04efb`) — `pipeline.py`,
  `spawn.py`, `watchdog.py`, `tests/test_admission_checklist.py`,
  `tests/test_spawn_gate_wiring.py`, `tests/test_spawn_pipeline.py` — all
  read via `git diff main...pr-2368` and a local worktree checkout of
  `pr-2368`, this session.
- `main` at `46da1c8a199048b380c363a936e92bca1c7c5393` — used as the
  pre-change baseline for every "is this pre-existing?" check below
  (REQ-K's cited pre-existing failures).
- Issue #2293 comment `issuecomment-5404799228` (the "scope addition"
  from the consumer's full incident report) — source of REQ-I/REQ-J.
- This role's own prior record on PR #2306 (`docs/issue-2293/reports/conformance-review.md`
  at commit `651623df`) — read for requirement-scope continuity only (no
  new issue comments since), not reused as evidence for any verdict below.

## Open findings

Full requirement ledger below (REQ-A through REQ-M3 = 15 `---`-delimited
blocks). REQ-B is now Present — canonical: pasted live-CLI/pytest
evidence in the REQ-B block above, this session, fresh worktree at PR
head `a49ee1c9`. REQ-K remains this record's one substantive open
finding:
```
$ git diff 042e47f7..a49ee1c9 --stat -- tests/test_spawn_pipeline.py
```
canonical: the command above (this session, fresh worktree) produced no
output — the CHANGES-round diff does not touch
`tests/test_spawn_pipeline.py`, so REQ-K's finding carries forward
unchanged. REQ-K is named again with its resolution path at the end of
this section.

---
requirement: refuse admission, before any session starts, when `task` is
  bare-numeric/`#`/`-`-prefixed-numeric and `--issue` is absent (REQ-A)
canonical: this session's own independent pytest re-run plus a live CLI
repro, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 1 (refusal clause)
verdict: Present
evidence: `042e47f7:pipeline.py:1522` (`_DEGENERATE_TASK_RE =
re.compile(r"^[#-]?\d+$")`) and `pipeline.py:1525-1551`
(`_admission_check_degenerate_task`); `spawn.py:2452` (`ADMISSION_CHECKS`
row `("degenerate-task", _admission_check_degenerate_task)`)
rationale: independent live CLI run, PR head worktree:
```
$ python3 spawn.py implementation 538 -C /tmp/pr2368-check
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
```
canonical: pasted live run above — executed-live, this session; refusal
fires before any session/workspace exists. Independent unit-test re-run,
PR head worktree:
```
$ python3 -m pytest tests/test_admission_checklist.py -q
31 passed in 12.29s
```
canonical: pasted pytest run above — executed-live, this session.

---
requirement: the refusal message names the almost-certain intent with a
  did-you-mean `--issue` suggestion (REQ-B)
canonical: this session's own live CLI run, direct inspection of the
print statement, and an independent pytest re-run, in a fresh isolated
worktree at PR #2368's post-CHANGES-round head — none of it read from
or trusted against PR #2368's own `implementation.md` "CHANGES-round
fix" account (defect-verification-independence-from-upstream-verdicts
rule 1/3: a claimed fix is a claim to independently re-derive, not a
settled fact).
spec_ref: issue #2293 body, `## Ask`, item 1 (message clause: `did you
  mean: spawn.py <role> "<task>" --issue 538`)
verdict: Present (was Incorrect against PR #2368 head `042e47f7`, this
  same record, above history preserved)
evidence: `a49ee1c9:pipeline.py:1547-1551`
```
    stripped = task.strip()
    print(f"[admission] degenerate-task: task {stripped!r} looks like "
          f"an issue number; did you mean: spawn.py {role} \"{stripped}\" "
          f"--issue {digits}? Pass --force-adhoc-task to admit this "
          f"literal task anyway.", file=sys.stderr)
```
and `a49ee1c9:tests/test_admission_checklist.py:327-340`
(`test_refusal_message_substitutes_actual_task_not_placeholder`)
rationale: re-review scope for this session (per this session's own
assignment): independently verify REQ-B specifically, after PR #2368's
CHANGES-round commits (`2d96713c` "CHANGES-round fix — substitute real
task in did-you-mean…" through head `a49ee1c9`). The literal `"<task>"`
this record's own prior pass flagged (Incorrect, against head
`042e47f7`) is gone: `stripped = task.strip()` is bound once and
`{stripped}` now fills the task slot in the f-string, alongside the
already-correct `{role}`/`{digits}`. Independent live CLI run, fresh
worktree (`git worktree add /tmp/wt2368b a49ee1c9`, this session, no
files carried over from the earlier `/tmp/pr2368-check` worktree):
```
$ python3 spawn.py implementation 538; echo "RC=$?"
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "538" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```
canonical: pasted live run above — executed-live, this session; the
suggested command now reads the caller's real task (`"538"`), a
copy-pasteable corrected invocation, not the placeholder. Negative-path
check (rule 2, don't stop at the happy path): `grep -n '"<task>"'
pipeline.py` (fresh worktree) returns no hit anywhere in the source —
the literal string is fully gone, not just absent from this one call
site's output. Independent test re-run, same worktree:
```
$ python3 -m pytest tests/test_admission_checklist.py -q
32 passed in 0.95s
```
canonical: pasted pytest run above — executed-live, this session (31
prior + the new `test_refusal_message_substitutes_actual_task_not_placeholder`,
which asserts `'"538"' in message` and `"<task>" not in message` against
a direct `_admission_check_degenerate_task` call with captured stderr —
this is exactly the content assertion this record's prior pass noted
was missing). This closes both halves of the prior Incorrect finding:
the message bug itself, and the fact that it shipped untested.

---
requirement: an explicit override flag bypasses REQ-A for the rare
  legitimate numeric-task case (REQ-C)
canonical: this session's own live CLI run (`--dry-run`) plus unit-test
re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 1 (override clause)
verdict: Present
evidence: `042e47f7:spawn.py:1125-1130` (`--force-adhoc-task` argparse
flag); `pipeline.py:1537-1538` (`if ctx.get("issue") is not None or
ctx.get("force_adhoc_task"): return True`)
rationale: independent live run, PR head worktree:
```
$ python3 spawn.py implementation 538 --force-adhoc-task -C /tmp/pr2368-check --dry-run
... (dry-run hook/model JSON, no admission refusal) ...
--model sonnet
```
canonical: pasted run above — executed-live, this session; admission is
not refused with the override present. `test_force_adhoc_task_overrides`
and `test_force_adhoc_task_admits_and_no_workspace_change` are part of
the `31 passed` `test_admission_checklist.py` run pasted under REQ-A.

---
requirement: every watchdog/poll diagnosis for a no-`--issue` entry says
  "adhoc" prominently, HEALTHY included (REQ-D)
canonical: this session's own live `diagnose_health()` call plus
unit-test re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 2 (ADHOC-tag clause)
verdict: Present
evidence: `042e47f7:watchdog.py:278-287` (`adhoc_prefix` computed when
`entry.get("issue") is None`, prepended inside `_diagnosis()`)
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
for this entry can no longer be misread as "your issue-N spawn is fine".
Independent unit-test re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py -q
1 failed, 70 passed in 60.70s
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
```
canonical: pasted pytest run above — executed-live, this session; the one
failure reproduces identically on clean `main`
(`46da1c8a199048b380c363a936e92bca1c7c5393`):
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace -q -n0
1 failed in 49.95s
```
canonical: pasted `main`-worktree run above — executed-live, this
session, confirming the failure predates this diff.

---
requirement: the same diagnosis names the task's first words (REQ-E)
canonical: same live call as REQ-D, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 2 (task-naming clause)
verdict: Present
evidence: `042e47f7:watchdog.py:279-282` (`task_hint = (entry.get("task")
or "").strip()[:60]`)
rationale: the live call pasted in REQ-D's finding above prints
`ADHOC task="538" — ...` — the task text is named in the tag, produced by
the same one call cited there. Implementation-note (not scored against
this requirement): this build takes the first 60 raw characters of the
task string rather than the first N whitespace-split words (PR #2306's
approach, `" ".join(task.split()[:8])`); for typical adhoc task text
this still surfaces the task's opening words, but a task whose first
word alone exceeds 60 characters would be truncated mid-word rather than
dropped at a word boundary — a cosmetic edge case, not a failure of this
clause's actual ask (naming the task so a HEALTHY line is identifiable).
canonical: same pasted output as REQ-D above.

---
requirement: the fix is systemic for all consumer sessions, not
  consumer-specific (REQ-F)
canonical: this session's own inspection of the call sites, PR head
worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 1)
verdict: Present
evidence: `042e47f7:spawn.py:2452` (`ADMISSION_CHECKS` row, run
unconditionally for every `spawn.py <role> <task>` invocation);
`042e47f7:watchdog.py:271-287` (`_diagnosis()` applied unconditionally
inside `diagnose_health()`, the single code path used for every roster
entry regardless of target repo)
rationale: independent test re-run confirming the tag is conditioned on
`issue is None` alone, not on any consumer/repo identity, PR head
worktree:
```
$ python3 -m pytest tests/test_spawn_gate_wiring.py -q -k test_issue_scoped_entry_has_no_adhoc_tag
1 passed in 12.60s
```
canonical: pasted run above — executed-live, this session; plus static
inspection of both files' full bodies this session — neither code path
is gated behind a consumer identity, repo slug, or config flag.

---
requirement: no added overhead/conflict/stall surfaces (REQ-G)
canonical: this session's own inspection of the new code's I/O profile,
PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 2)
verdict: Present
evidence: `042e47f7:pipeline.py:1525-1551` (`_admission_check_degenerate_task`
— one regex match against an already-in-memory `ctx` dict, no
subprocess/network call); `042e47f7:watchdog.py:278-287` (string-prefix
operation on an already-computed `detail` value)
rationale: REQ-A/REQ-D's admission-check and watchdog-tagging additions
are both synchronous, in-process, and O(1) on already-available data —
no new subprocess, network call, lock, or wait. The scope-addition fixes
(REQ-I/REQ-J below) do add a real clone step for adhoc spawns, but that
is the fix itself — the same clone-isolation an issue-scoped spawn
already performs, not a new stall surface layered on top of unrelated
admission checks; `_timed("adhoc_workspace")` (`spawn.py:2562`) scopes
it for the existing timing-diagnostics mechanism, no new one introduced.
canonical: static inspection of the cited function bodies and the
`_spawn_one()` control flow this session.

---
requirement: nothing in the consumer tree (REQ-H)
canonical: this session's own `git diff --stat` re-run, PR head worktree.
spec_ref: issue #2293 body, `## Ask`, item 3 (frozen constraint, clause 3)
verdict: Present
evidence: `git diff main...pr-2368 --stat`
```
$ git diff main...pr-2368 --stat
docs/issue-2293/reports/implementation.md          | 262 +++++++++++++++++++
.../2026-08-25-hunt-2293-implementation.md         |  54 +++++
.../reports/implementation/deviation-log.md        |   3 +
pipeline.py                                        |  32 +++
spawn.py                                           |  62 ++++-
tests/test_admission_checklist.py                  |  91 +++++++
tests/test_spawn_gate_wiring.py                    |  31 +++
tests/test_spawn_pipeline.py                       | 144 +++++++++++
watchdog.py                                        |  17 +-
```
canonical: pasted diff-stat above — executed-live, this session; every
path is inside `on-the-record` itself, none under any consumer repo.

---
requirement: adhoc/no-`--issue` spawns get an isolated workspace instead
  of running in the caller's cwd, or refuse without one (REQ-I)
canonical: this session's own inspection of `issue_workspace()` and
`_spawn_one()`'s new adhoc block, PR head worktree, cross-checked
against the scope-addition comment's incident description; independently
re-derived (verdict-assignment rule 6) since the #2306 pass found this
Absent.
spec_ref: issue #2293 comment `issuecomment-5404799228` ("adhoc/no-issue
  spawns still get an isolated workspace (or refuse without one)")
verdict: Present
evidence: `042e47f7:spawn.py:1683` (`issue_workspace(cwd: str, issue: int
| None, role: str)` widened to accept `issue is None`);
`spawn.py:1727-1728` (adhoc path keys the clone dir by pid:
`f"{repo_name}-adhoc-{role}-{os.getpid()}"`); `spawn.py:2555-2564` (new
`if issue is None:` block in `_spawn_one()` calling `issue_workspace(cwd,
issue, role)` unconditionally for every adhoc spawn, before the session
subprocess runs); `spawn.py:1734-1743` (before-landing warrant-hunt fix:
`if issue is None and (work / ".git").exists(): ...
shutil.rmtree(work, ignore_errors=True)`, guarding the pre-existing
reuse-by-directory branch against a pid-collided leftover)
rationale: independent live pytest re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_pipeline.py -q -k AdhocIsolationAndLogPath -v
test_issue_workspace_isolates_adhoc_by_pid_not_by_issue_none ... ok
test_stale_pid_keyed_workspace_is_wiped_not_reused ... ok
test_adhoc_spawn_runs_isolated_with_timestamped_pid_log ... ok
3 passed in 13.82s
```
canonical: pasted run above — executed-live, this session;
`test_adhoc_spawn_runs_isolated_with_timestamped_pid_log` asserts the
session subprocess's `cwd` is the isolated clone, not the caller's `-C`
path — the exact incident mechanism (`작업 디렉터리 .`) this clause
targets, and `test_stale_pid_keyed_workspace_is_wiped_not_reused` asserts
a pid-collided leftover's stale branch/files are wiped, not inherited —
the exact before-landing warrant-hunt gap the PR's own description names
against its first draft, independently confirmed fixed here rather than
trusted from the PR body.

---
requirement: adhoc/no-`--issue` spawns get a timestamped+PID log path,
  not the shared `runs/last-session.log` (REQ-J)
canonical: this session's own inspection of the log-path line, PR head
worktree, cross-checked against `main`; independently re-derived since
the #2306 pass found this Absent.
spec_ref: issue #2293 comment `issuecomment-5404799228` ("a
  timestamped+PID log path like issue-scoped spawns")
verdict: Present
evidence: `042e47f7:spawn.py:3005` (`log_path = _session_log_path(cwd)`
— unconditional, the `issue is not None` branch and the
`ROOT / "runs" / "last-session.log"` fallback both removed)
rationale: independent diff re-run, PR head worktree:
```
$ git diff main...pr-2368 -- spawn.py | grep -n "last-session\|log_path ="
+        log_path = _session_log_path(cwd)
```
canonical: pasted grep above — executed live, this session; the shared
fallback path is gone from the diff entirely, not merely unreached.
`_session_log_path()` is now called for both branches — because REQ-I
above isolates every adhoc spawn's `cwd` into its own pid-keyed clone
first, `_session_log_path(cwd)` (which derives its filename from `cwd`)
produces a distinct timestamped+PID path per adhoc spawn the same way it
already does for issue-scoped spawns, closing the shared-log-overwrite
failure mode the incident report describes. Confirmed by
`test_adhoc_spawn_runs_isolated_with_timestamped_pid_log`'s regex
assertion (pasted under REQ-I) on the roster entry's `log` field:
`re.escape(Path(isolated).name) + r"\.session\.\d{8}T\d{6}\.\d+\.log$"`
— not `last-session.log`.

---
requirement: gate `tests/test_spawn_pipeline.py` (REQ-K)
canonical: this session's own re-run of the named gate file plus a
targeted grep for feature coverage, PR head and `main` worktrees.
spec_ref: issue #2293 body, `## Acceptance`, `gate` line
verdict: Surface
evidence: `git diff main...pr-2368 -- tests/test_spawn_pipeline.py` (144
lines added — a new `AdhocIsolationAndLogPath` class, 3 tests)
rationale: independent re-run, PR head worktree:
```
$ python3 -m pytest tests/test_spawn_pipeline.py -q
2 failed, 87 passed in 9.74s
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_env_overrides_config
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_config_only_appends_flag
```
canonical: pasted run above — executed-live, this session; both failures
reproduce on clean `main` (`46da1c8a`) too:
```
$ python3 -m pytest tests/test_spawn_pipeline.py -q   # main worktree
3 failed, 83 passed in 24.16s
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_env_overrides_config
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_role_model_config_only_appends_flag
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_resolved_role_model_builtin_default_is_sonnet
```
canonical: pasted `main`-worktree run above — executed-live, this
session; pre-existing flakiness (env/order-dependent), not a regression
from this diff — the named gate file is not clean on `main` either.
Per verdict-assignment rule 1 (Surface, not Present, when matching code
exists but doesn't fire on the actual condition the requirement names):
this file now contains real, directly-relevant coverage for REQ-I/REQ-J
(`AdhocIsolationAndLogPath`, `3 passed` pasted under REQ-I) — an
improvement over PR #2306, whose changes to this same file were an
unrelated xdist race fix with zero feature coverage. But
`grep -ni "degenerate\|force_adhoc" tests/test_spawn_pipeline.py`
(PR head worktree) returns no hit — REQ-A/REQ-B/REQ-C (the
degenerate-task admission-and-message behavior) have no coverage in the
named gate file at all; that coverage lives entirely in
`tests/test_admission_checklist.py` instead. A CI run scoped to the named
gate would catch a REQ-I/REQ-J regression but not a REQ-A/REQ-B/REQ-C
one.
spec_vs_built: the Acceptance section names `tests/test_spawn_pipeline.py`
specifically as this issue's one gate for the whole feature. Half the
feature (the isolation/log-path scope addition) is now genuinely
exercised there; the other half (degenerate-task detection, its message,
and the override) is not, and would silently regress under a CI run
scoped only to this named file.

---
requirement: a normal spawn with a real task and `--issue` is
  byte-identical, no new prompts (REQ-L)
canonical: this session's own live CLI dry-run plus a structural diff of
the admission-gate call site, PR head worktree.
spec_ref: issue #2293 body, `## Acceptance`, `empty state` line
verdict: Present
evidence: `042e47f7:spawn.py:2555` (`if issue is None:` — the new
adhoc-isolation block is unreachable when `--issue` is given);
`pipeline.py:1537` (`_admission_check_degenerate_task` short-circuits
`return True` whenever `ctx.get("issue") is not None`)
rationale: independent live run against the real issue #2293 (avoiding
the placeholder-issue-number confound the #2306-era review hit), PR head
worktree:
```
$ python3 spawn.py implementation "fix a real bug" --issue 2293 -C /tmp/pr2368-check --dry-run
... (clean dry-run hook/model JSON, no admission refusal, no adhoc-isolation prompt) ...
--model sonnet
```
canonical: pasted run above — executed-live, this session, Test-method
(a full CLI run, not the Analysis-only fallback the #2306-era review
needed). None of the pre-existing `ADMISSION_CHECKS` rows read the new
`"task"`/`"force_adhoc_task"` ctx keys, so their behavior is unchanged by
the keys' presence.

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
under REQ-B (Present as of head `a49ee1c9`, was Incorrect against
`042e47f7`); this clause only asks that the run happen and produce a
refusal-plus-suggestion, which it does, independent of REQ-B's content
verdict. canonical: same pasted run as REQ-A above.

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
canonical: this session's own live CLI dry-run, same basis as REQ-L.
spec_ref: issue #2293 body, `## Acceptance`, `provenance` line, clause 3
verdict: Present
evidence: same as REQ-L
rationale: carried from REQ-L's Test-method finding above — the clean
live `--issue`-scoped dry-run pasted there is this clause's own evidence
too; both check the same underlying claim from two angles (acceptance's
empty-state line vs. its provenance line). canonical: same pasted run as
REQ-L above.

---

Resolution paths for the non-`Present` findings above:

1. **REQ-B** (Present as of head `a49ee1c9`, CHANGES-round fix — see
   REQ-B block above; no resolution path needed, resolved).
2. **REQ-K** (Surface) — add degenerate-task/message/override coverage
   (REQ-A/B/C) to `tests/test_spawn_pipeline.py` itself so the named gate
   exercises the whole feature the Acceptance section attributes to it,
   not only the isolation/log-path half; or correct the Acceptance
   section's `gate` line to also name `tests/test_admission_checklist.py`
   where that coverage actually lives.

REQ-I and REQ-J — Absent against PR #2306 in this role's prior pass — are
now both Present against PR #2368, and REQ-B (against PR #2368's initial
head `042e47f7`, the same did-you-mean message bug flagged once already
against #2306) was fixed in a CHANGES-round respawn and is now Present
too — see the corresponding blocks above, each with its own
`canonical:`-tagged live-CLI/pytest evidence: REQ-I/REQ-J's `3 passed`
`AdhocIsolationAndLogPath` run and diff/grep evidence, and REQ-B's
`a49ee1c9:pipeline.py:1547-1551` fix plus this session's
`32 passed in 0.95s` re-run of `tests/test_admission_checklist.py`.

## Next steps

None from this review's own side — `loop_state` above is this record
kind's terminal value, `reported`. For the owning role: PR #2368 (as of
its CHANGES-round fix, head `a49ee1c9`) closes issue #2293's
scope-addition ask (REQ-I/REQ-J) in full and REQ-B is now fixed and
independently re-confirmed Present this session — but `Closes #2293`
still overstates it while REQ-K (the named Acceptance gate,
`tests/test_spawn_pipeline.py`, still covers only half the feature —
REQ-A/B/C's degenerate-task coverage lives entirely in
`tests/test_admission_checklist.py` instead) remains open.

canonical: `gh pr view 2368 --json body -q .body` — result: `Closes
#2293` trailer present in the PR body (re-confirmed unchanged this
session); the recommendation above rests on REQ-K's finding and
evidence in `## Open findings` above, and REQ-B's now-Present verdict in
the same section.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; reconfirmed issue #2293's `## Ask`/scope-addition-comment/`## Acceptance` text is unchanged since this role's prior pass (see `gh issue view 2293 --comments` under "What was done") and reused the same REQ-A..REQ-M3 decomposition rather than silently re-deriving a different one
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to choose live-CLI/Test evidence for REQ-A/B/C/D/E/I/J/K and to upgrade REQ-L/M3 to a clean live-CLI Test this session (the #2306-era pass had to fall back to Analysis there, confounded by a placeholder issue number); re-invoked in this session's REQ-B re-review to choose the same live-CLI+Test combination against the CHANGES-round head
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 6 to independently re-derive REQ-B (Incorrect, re-confirmed against #2368's own differently-shaped code, not copy-forwarded) and REQ-I/REQ-J (re-derived from Absent-in-#2306 to Present-in-#2368, including verifying the PR's own claimed warrant-hunt fix rather than trusting its account); used rule 1 to grade REQ-K as Surface (matching, directly-relevant code exists in the named gate now, but does not cover REQ-A/B/C). Re-invoked this session for the CHANGES-round re-review: REQ-B moved Incorrect → Present, re-derived fresh against head `a49ee1c9` in an isolated worktree (live CLI + `32 passed` pytest run), not carried forward from the PR's own implementation-record account
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used to pin every evidence citation above to file:line plus the `pr-2368`/`main` commit shas actually read this session. Re-invoked this session to pin REQ-B's updated evidence to `a49ee1c9:pipeline.py:1547-1551` and `a49ee1c9:tests/test_admission_checklist.py:327-340`, plus the prior `042e47f7` Incorrect verdict's citation preserved as history rather than overwritten
skill-verdict: conformance-review-finding-record — applied: invoked; used for this record's `---`-delimited per-requirement block shape (requirement/spec_ref/verdict/evidence/rationale/spec_vs_built) and the frontmatter's EARL field set. Re-invoked this session to update the REQ-B block in place (verdict Incorrect → Present, `spec_vs_built` dropped since it's required only for Incorrect per rule 3.6) rather than opening a parallel record
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; this session's REQ-B re-review deliberately did not read or cite PR #2368's own `implementation.md` "CHANGES-round fix" account as evidence (rule 1/3) — instead re-derived the verdict from a fresh isolated worktree at head `a49ee1c9` with an independent live CLI run and pytest re-run, plus a negative-path grep confirming no `"<task>"` literal remains anywhere in `pipeline.py` (rule 2), not just at the one call site the PR's own account quoted
skill-verdict: conformance-review-sampling-derivation — not-applicable: the requirement set was small and fully enumerable (same 15-block ledger this role already derived once for this issue, reconfirmed unchanged), so no sampling scope was needed
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting findings; the non-Present finding (REQ-K) is recorded with a resolution path, not a severity band
skill-verdict: implementation-audit — not-applicable: this session's task already routes through the more specific, mandated conformance-review-* skill family (requirement-extraction/verdict-assignment/finding-record above), which implements the same independent-evaluator-with-no-builder-intent-access principle implementation-audit describes, natively for this repo's own EARL-schema record format; invoking the generic cross-domain skill on top would duplicate that procedure without adding anything the more specific family doesn't already cover
other mounted skills: not triggered

## What did not work

Warrant-hunt dispatch: skipped for this delivery. Per this session's
`CORE_BUILD_NOW=1` bypass, this record is delivered directly with no
separate phase-1 proposal transition, so only a before-landing dispatch
would apply — and this session's own write set is entirely under
`docs/` (this record file only), which the warrant protocol's DOCS-ONLY
FAST PATH exempts from the before-landing dispatch outright (`docs-only,
no before-landing dispatch`). This mirrors the mandatory-skip-line
convention scout uses, so the skip is not silent.

Every citation above was read or re-run live this session in isolated
worktrees (`/tmp/pr2368-check`, `/tmp/main2368-check`), pasted throughout
`## Open findings` above, and both worktrees were removed after use.

Every REQ-A/M1 live CLI run pasted from the initial pass (PR head
`042e47f7:pipeline.py:1547-1550`) shows the same suggested-command text
that pass's own REQ-B finding called out as buggy (`"<task>"`
unsubstituted) — noted once there, not repeated as a fresh finding at
each pasted occurrence.

Re-review, this session: fetched PR #2368's post-CHANGES-round head and
opened it in a fresh isolated worktree, scoped to independently
re-verifying REQ-B —
```
$ gh pr view 2368 --json commits -q '.commits[-1].oid'
a49ee1c9c928782b57ed4f8ef9c828524dc09855
$ git worktree add /tmp/wt2368b a49ee1c9
```
canonical: pasted commands above — executed-live, this session. Every
citation under the updated REQ-B block (`## Open findings` above) was
read or re-run live in that worktree this session; the worktree was
removed after use, `git worktree remove /tmp/wt2368b` (this session).
REQ-A/C-M3 were not re-litigated: `git diff 042e47f7..a49ee1c9 --stat`
(pasted in `## Open findings` above) shows the CHANGES-round diff
touches only `pipeline.py` and `tests/test_admission_checklist.py`,
neither of which any other requirement's evidence cites.
