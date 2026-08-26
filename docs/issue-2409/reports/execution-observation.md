---
issue: 2409
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2409/reports/implementation.md
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: directive_assembly.py
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: spawn.py
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: scripts/related_files.py
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: scripts/session_waste_metrics.py
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
subject: PR #2416 (issue-2409/implementation, three additive mechanisms
  plus an instrumentation artifact for issue #2409's waste classes),
  commit 1b09aca4 (HEAD, CHANGES round — NR1b fix at 980d6db9 plus a
  skill-verdict addendum at 1b09aca4, both on top of 64028704 which this
  record's first pass already verified), checked out into an
  independent git worktree at /tmp/wt-2409-impl2 (untracked in this
  tree, removed after this observation)
test: independent re-execution of the instrumentation artifact and the
  related-files lookup against the same 5 real session logs/issue
  numbers the implementation record names, independent re-read of the
  directive_assembly.py/spawn.py diff and the on-the-record/hooks/
  tree for additive-only and untouched-gate claims, a fresh run of the
  four targeted test files, and (CHANGES round) an independent re-run
  of the committed batch-rollup artifact's own generating command,
  byte-diffed against the file conformance-review PR #2420's NR1b
  finding asked to be committed — all from a fresh worktree, independent
  of the PR's own pasted transcripts
result: passed
assertedBy: execution-observation session for issue-2409, independent
  of PR #2416's authoring (implementation) session
---

# issue-2409 — execution-observation record

## What was done

canonical: `git fetch origin issue-2409/implementation && git worktree
add --detach /tmp/wt-2409-impl origin/issue-2409/implementation` — an
independent checkout of PR #2416's head (`64028704`), never the PR's own
pasted transcripts taken as given. `docs/issue-2409/reports/implementation.md`
(cited throughout this record, path untracked in this tree — it lives
only on branch `issue-2409/implementation`/PR #2416, read this session
in that separate worktree) is the record this round re-verifies.
Re-executed or re-read each of its claims that back issue #2409's six
Acceptance bullets.

### Instrumentation artifact + before/after table (Acceptance items 1, 5)

canonical: `python3 -c "import sys; sys.path.insert(0,'scripts');
import session_waste_metrics as sw; print(sw.batch_summary(paths))"`
against the same 5 real `implementation`-role session logs the record
names (issues 2314/2331/2348/2382/2393 — the largest/most-complete log
per issue where more than one exists on this host, same selection rule
the record states) — result:

```
bash_total: 496, bash_other_share: 0.8629, hook_refusals_total: 35
(7.0/session), spawn.py re-reads: 28, own-record re-reads: 7
per-session bash_total [80,76,100,111,129], hook_refusals [8,10,7,0,10],
wall_clock_ms [1498480,2059740,2232118,null,2325492],
num_turns [108,112,177,null,139]
```

derived: exact match, row for row, to the implementation record's own
rollup table (496 Bash / 86.3% other-share / 35 refusals (7.0/session) /
25.0, 34.3, 37.2, n/a, 38.8 min / 108, 112, 177, n/a, 139 turns / 28
`spawn.py` + 7 own-record re-reads) and to its per-session gate
breakdown (2314: record-claim-guard=5, heredoc=2, board-gate=1; 2331:
board-gate=5, record-claim-guard=3, heredoc=1, pr-preflight=1; 2348:
heredoc=3, record-claim-guard=2, acceptance-real-run=1, pr-preflight=1;
2382: none; 2393: board-gate=4, record-claim-guard=4, heredoc=2) —
independently reproduced this session, not merely re-read.

### Exploratory-Bash lookup (Acceptance item 2)

canonical: `python3 scripts/related_files.py <issue> --json` run live
for issues 2314, 2331, 2348, 2382, 2393 — result: `docs_tree`/
`issue_mentions` counts 2314=6/**7**, 2331=6/7, 2348=4/19, 2382=3/0,
2393=4/3. Four of five match the implementation record's own pasted
counts (2314=6/6, 2331=6/7, 2348=4/19, 2382=3/0, 2393=4/3) exactly;
2314's `issue_mentions` is one higher than pasted (6 vs 7 — derived:
diffed directly against the record's own table, one entry off). See
Open findings — this is explained, not a tool defect.

### Wiring / additive-only claims (Acceptance items 2-4, and "no removal")

canonical: `git diff f9f8041f^ f9f8041f -- directive_assembly.py` (PR
worktree) — result: the diff adds `_TASK_LOOKUP_PROSE` and
`_HOOK_CONTRACT_PROSE` as new constants, appends one paragraph to the
existing `_TURN_BUDGET_PROSE` value, and extends
`directive_section_files()` with two new dict entries
(`task-lookup.md` gated on the same `code_scoped` flag `known-paths.md`
already uses; `hook-contract.md` added to the always-materialized set
alongside `completion-and-landing.md`/`repo-discovery.md`/
`turn-budget.md`) — no existing constant body is replaced or removed.
canonical: `git diff f9f8041f^ f9f8041f -- spawn.py` — result: two new
one-line re-export statements (`_TASK_LOOKUP_PROSE`,
`_HOOK_CONTRACT_PROSE`), matching the existing re-export pattern
exactly, nothing else changed. canonical: `git diff
origin/main...HEAD --stat -- on-the-record/hooks/ hooks.json` (PR
worktree, base = this repo's own `main`) — result: empty output, no
changes to any gate script or `hooks.json` between `main` and PR
#2416's head. canonical: `git diff origin/main...HEAD --numstat` —
result: 11 files changed, 1266 insertions(+), 7 deletions(-); the 7
deletions (derived: `git diff origin/main...HEAD --numstat` per-file
breakdown) are two updated assertion lines inside
`tests/test_directive_diet_2135.py` (1 line) and `directive_assembly.py`
(6 lines, the docstring/dict-entry lines replaced by the wider
always-materialized description quoted above) — no file is deleted, no
gate/test/record mechanism removed.

### Targeted test suite (verification of items 1-4 together)

canonical: `env -u CORE_BUILD_NOW python3 -m pytest
tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py
tests/test_related_files.py tests/test_session_waste_metrics.py -q -m ""
-p xdist -n0` (fresh worktree) — result:

```
79 passed, 1 skipped in 2.15s
```

derived: exact match to the implementation record's own pasted summary
(79 passed, 1 skipped).

### CHANGES round — NR1b fix re-verification (commits 980d6db9, 1b09aca4)

canonical: `git fetch origin issue-2409/implementation && git worktree
add --detach /tmp/wt-2409-impl2 origin/issue-2409/implementation` —
head moved from 64028704 (this record's first pass) to `1b09aca4`,
two commits on top: `980d6db9` ("commit generated per-turn-breakdown
artifact (NR1b fix)") and `1b09aca4` ("skill-verdict addendum for
CHANGES round"). canonical: `git diff 64028704..1b09aca4 --numstat`
(fresh worktree) — result: 2 files changed, both docs-only
(`docs/issue-2409/reports/implementation.md` (untracked in this tree —
lives only on branch issue-2409/implementation/PR #2416), 22
insertions; the new artifact file, 96 insertions), 0 deletions;
canonical: `git diff 64028704..1b09aca4 --stat -- on-the-record/hooks/
hooks.json directive_assembly.py spawn.py scripts/related_files.py
scripts/session_waste_metrics.py` — empty output, confirming none of
the four mechanism files this record already verified changed in the
CHANGES round, so the wiring/additive-only findings above still hold
without re-reading those diffs a second time.

canonical: independently re-ran, in the fresh worktree, the exact
`python3 -c` driver `docs/issue-2409/reports/implementation.md`
(untracked in this tree — lives only on branch
issue-2409/implementation/PR #2416) now cites for the artifact
(`sw.batch_summary(paths)` plus one
`sw.analyze(path)['hook_refusals']['by_gate']` per path, same 5 session
logs as the before-table) and piped its stdout to a scratch file —
result: `diff` against the committed
`docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
(untracked in this tree — lives only on branch
issue-2409/implementation/PR #2416) is empty — byte-for-byte identical,
independently reproduced (not merely re-read from the PR's own pasted
diff-check). derived: the issue thread's own "CHANGES requested on PR
#2416" comment (read this session via `gh issue view 2409 --comments`)
names this gap NR1b and states the amended re-review found it as the
sole remaining item; it is now committed at that path and this round
confirms it is genuinely regeneratable, not hand-typed. canonical: `git
ls-files docs/issue-2409/reports/implementation/artifacts/` (fresh
worktree) — result: the file is tracked at `1b09aca4`, not merely
present in a working tree.

canonical: `env -u CORE_BUILD_NOW python3 -m pytest
tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py
tests/test_related_files.py tests/test_session_waste_metrics.py -q -m ""
-p xdist -n0` re-run in the same fresh worktree at `1b09aca4` — result:
`79 passed, 1 skipped in 3.31s`, same counts as this record's first
pass at `64028704`, consistent with the CHANGES round touching no test
or mechanism file.

derived: overall verdict recomputed per this role's spec (worst case
across all cited test entries) — every entry above is `passed`, so the
record's own `result` field stays `passed`; this CHANGES-round section
extends rather than replaces the first pass's evidence.

## Why

derived: this role's own spec
(`roles/specs/execution-observation.spec.json`) fixes the verdict method
(worst case across cited test entries) and states the reason two
independent observers should converge: the check is mechanical
aggregation over already-run claims, not an investigative finding.
Per the approved phase-1 proposal's Rationale, independently
re-executing every reproducible claim (the instrumentation artifact,
the related-files lookup, the targeted test suite) and independently
re-reading the diff/wiring claims — rather than trusting the
implementation record's own pasted transcripts — is what makes this
role's verdict a genuine second observation instead of a restatement,
following the same method `docs/issue-2393/reports/execution-observation.md`
already established for this lineage.

## Upstream basis

`docs/issue-2409/reports/implementation.md` (untracked in this tree —
lives only on branch `issue-2409/implementation`/PR #2416; read at
commit `64028704` and again at commit `1b09aca4`) supplied every claim
re-verified above: the instrumentation artifact and its regenerate
command, the related-files lookup and its per-issue counts, the
`directive_assembly.py`/`spawn.py` diff description, and the targeted
test list.
`docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
(untracked in this tree — lives only on branch
`issue-2409/implementation`/PR #2416; committed there at `980d6db9`)
supplied the generated artifact byte-diffed above.

`roles/specs/execution-observation.spec.json` (read this session, this
tree) fixed this record's own field shape (EARL 1.0
subject/test/result/assertedBy), the worst-case recomputation rule, and
the terminal `loop_state` value (`handed-off`).

GitHub issue #2409 (`gh issue view 2409`, read this session) supplied
the six Acceptance bullets this round checks against, and the operator's
frozen no-side-effects constraint quoted in the phase-1 proposal.

`docs/issue-2393/reports/execution-observation.md` (committed, this
tree) supplied the independent-worktree-plus-fresh-reproduction method
this round reused.

## Open findings

- **This record's own first pass (at `64028704`) matched the
  instrumentation artifact's live CLI output against the implementation
  record's pasted table but did not independently check whether a
  generated artifact file was actually committed to the repo — the same
  gap conformance-review PR #2420's amended re-review later named NR1b.
  Resolved, not open: derived: the "CHANGES round — NR1b fix
  re-verification" section above (`git ls-files
  docs/issue-2409/reports/implementation/artifacts/` plus the
  byte-for-byte `diff` against a fresh independent re-run, both run
  this session) confirms the gap is closed at `1b09aca4`, so this
  round's own record no longer carries that blind spot for the current
  commit.** No resolution path needed beyond noting it — a future round
  of this role should check for a committed generated instance, not
  just a working regenerate command, whenever an Acceptance bullet asks
  for an artifact to be "published"/"in the record."
- **`related_files.py`'s issue-2314 `issue_mentions` count drifted by
  one (6 pasted -> 7 reproduced), and it is explained, not a defect.**
  canonical: `grep -n "2314" docs/issue-2409/reports/implementation.md`
  (PR worktree) — result: 5 matches, all in prose naming issue 2314 as
  one of the 5 sampled issues. That record file (untracked in this
  tree — lives only on branch `issue-2409/implementation`/PR #2416)
  is itself outside `docs/issue-2314/` and now mentions the literal
  string "2314", so `related_files.py`'s `issue_mentions` scan (a
  `git grep` over tracked files outside the target issue's own docs
  tree) now matches it. That file did not yet carry this text, or had
  not yet been committed, at the moment the implementation session
  computed its own pasted count. This confirms the lookup is correctly
  sensitive to the live git tree, not that it undercounts or overcounts
  — but it means the "before/after" table in any record that cites this
  tool is only reproducible byte-for-byte at the exact commit it was
  run against, a property worth stating for any future reader who tries
  to re-run this table later. No resolution path needed beyond this
  note — not a defect.
- **`board-gate` refusals remain uncovered by `hook-contract.md`
  (the implementation record's own finding, independently reproduced
  here).** canonical: the per-session gate breakdown reproduced above
  — derived: board-gate=10 of 35 total refusals across the 5 sampled
  sessions, matching the implementation record's own count exactly.
  Resolution path (unchanged from the implementation record): a
  companion issue against the separate `tokenmaxxxer-core` plugin that
  emits `board-gate`, outside this repo's write set.
  canonical: the same per-session gate breakdown — derived:
  `pr-preflight`=2 and `acceptance-command-real-run-guard`=1 of the
  same 35 total, also matching the implementation record's own count
  exactly; same resolution path the implementation record already gave
  (expand `hook-contract.md` if a future measurement shows these
  categories staying high).
  canonical: `on-the-record/hooks/pretooluse_dispatcher.py`'s `GATES`
  list (read this session, PR worktree) — result:
  `spec-index-preflight.sh`'s trigger is a staged `docs/specs/*` path;
  this round's own commit touches no such path, so
  `python3 gates/spec_index.py --update` does not apply here.
- **This round did not re-measure the corpus-scale "after" number
  (Acceptance item 5's median wall-clock/turns across a comparable
  batch) — the implementation record already states this as NOT
  measured, and this round's own phase-1 proposal placed spawning 5+
  new real role sessions explicitly out of scope for the same
  shared-repo-side-effect reason.** No independent resolution path from
  this role beyond what the implementation record already gives:
  issues are user-authored (contract v3), so a follow-up
  corpus-scale re-measurement is the operator's call, not this role's
  or the implementation role's to file.

## Next steps

None — `loop_state: handed-off`. Every open finding above carries its
own resolution path (or an explicit statement that none is owed by this
role); none is a blocking defect against PR #2416.
