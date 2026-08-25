---
issue: 2286
role: execution-observation
author: execution-observation
kind: execution-observation
type: review
breaking: none — this is a review record; it makes no production code change itself
code_under_review:
  - tokenmaxxxer-core:core/hooks/board-gate.sh (PR #312, tokenmaxxxer-core, branch fix/issue-2286-board-gate-r5-author-identity)
  - docs/issue-2286/reports/implementation.md (PR #2387, on-the-record, branch issue-2286/implementation — untracked in this tree)
loop_state: handed-off
upstream:
  - path: docs/issue-2286/reports/implementation.md
    sha: 117ce2aac0825ac08fd4e29cd22d39af3767eb59
  - path: docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
subject: PR #2387 (on-the-record, "issue-2286: rewrite board-gate.sh R5 write-scope onto author identity (stage 3)") delivering docs/issue-2286/reports/implementation.md, plus its cited cross-repo half tokenmaxxxer-core PR #312 (branch fix/issue-2286-board-gate-r5-author-identity, commit 2914cd52e79ac8927ec5279119cad868ce0b69c1)
test: independent re-derivation of every falsifiable claim in docs/issue-2286/reports/implementation.md against the code PR #312 actually opens for review — git worktrees of PR #312's real head and its base (per `gh pr view 312 --json baseRefOid,headRefOid,files`), a from-scratch pytest re-run, and hand-built board-gate.sh probes this session wrote itself (not the PR's own fixtures) — commands and outputs below
result: failed
verdict: fail
assertedBy: execution-observation session for issue-2286, independent of PR #2387/#312's authoring (implementation) session
---

# issue-2286 — execution-observation record

## What was done

Independently observed and re-verified PR #2387 (on-the-record,
delivering `docs/issue-2286/reports/implementation.md` — untracked in
this tree, lives on branch `issue-2286/implementation` at commit
`117ce2aac0825ac08fd4e29cd22d39af3767eb59`, read via `git fetch origin
pull/2387/head:pr-2387` then `git show pr-2387:docs/issue-2286/reports/implementation.md`)
against `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
(this repo's `main`, sha `135712e8e4c56195aa0dedab6060db1610f3dc13`) and
its cited cross-repo half, tokenmaxxxer-core PR #312. Per this role's
own EARL-style scope (worst-case verdict over cited test/acceptance
entries — same posture this repo's issue-2207 execution-observation
record took, `git show 206b8129:docs/issue-2207/reports/execution-observation.md`),
every falsifiable claim was re-derived independently: this session's
own git worktrees of PR #312's actual head and base, this session's own
`pytest` invocation, and board-gate.sh probes this session built itself
(`/tmp/probe_gate.py`, modeled on but not reusing `test_board_gate.py`'s
own `run_gate` helper, so a gap in that file could not hide behind its
own tests).

### Mechanical claims — confirmed

acceptance: `gh pr view 312 --repo tokenmaxxxer/tokenmaxxxer-core --json baseRefOid,headRefOid` —
result: `headRefOid: 2914cd52e79ac8927ec5279119cad868ce0b69c1`,
`baseRefOid: 509759c9067282807e05e46cd6e32e5fe1a243b0` (current
tokenmaxxxer-core `main` tip at PR-open time). canonical: this GitHub
API response, read live this turn, confirms PR #312's own description's
claim that it was recut onto current main — `git merge-base a4bb55f
origin/main` (this session's own core checkout) → `ba7066c7...`, and
`git log --oneline ba7066c7..origin/main | wc -l` → `452`: the original
`a4bb55f` commit's base was 452 commits stale, matching the "phantom
diff" description.

canonical: `board-gate.sh` at PR #312's actual head, read from this
session's own worktree
(`/tmp/pr312-review/branch/core/hooks/board-gate.sh:93`) —
`EXTRA_SUBTREE = {"technical-feasibility": "spikes",
"release-engineering": "postmortems"}` — matches the record's claimed
correction verbatim.

acceptance: `grep -n 'ROLES = ' spawn.py` (this repo) — result: line
599, the `ROLES` tuple includes both `technical-feasibility` and
`release-engineering` (`spawn.py:599-601`, read directly) — the
corrected `EXTRA_SUBTREE` keys are real role names.

acceptance: `grep -n 'technical-feasibility\|release-engineering' board.py` —
result: lines 768, 770 — confirms board.py's own equivalent ownership
check already used these exact names, matching the record's "matching
board.py's own already-correct equivalent check" claim.

canonical: `directive_assembly.py:366-382` (this repo, read directly) —
`_stamp_additive_record_fields` returns `f"author: {role}\n"`, the
single call site every `author:` line comes from — confirms what the
`author:` field this stage's R5 reads actually contains.

acceptance: `git log -1 --format=%ci 470d5a1a` (this repo) — result:
`2026-08-25 13:28:15 +0900` — matches the migration doc's cited stage-1
cutover date exactly (`docs/issue-2286/reports/implementation/board-gate-r5-migration.md`,
read via `git show pr-2387:...`, untracked in this tree, same branch as
the implementation record above).

### R5 behavior — confirmed live, against PR #312's actual head

This session's own probe harness (`/tmp/probe_gate.py`) ran against a
`git worktree` of PR #312's real head
(`2914cd52e79ac8927ec5279119cad868ce0b69c1`), constructing its own
board/record fixtures independently of `test_board_gate.py`, covering
all four cases the proposal's "How you'll know it worked" describes.

acceptance: `python3 /tmp/probe_gate.py` — result:
```
own_author_append -> (0, '')
foreign_author_truncate -> (2, "board-gate: docs/issue-198/reports/implementation.md is authored by 'implementation', not 'execution-observation'. A session may append new content to a foreign-authored record but never alter another author's existing lines. (contract v3 s11, issue-2241 stage 3)")
foreign_author_append -> (0, '')
legacy_no_author_foreign_role_append -> (2, 'board-gate: docs/issue-198/reports/implementation.md belongs to another role. execution-observation writes only execution-observation.md, execution-observation/** — never a foreign record. (contract v3 s11)')
```
canonical: this session's own live invocation, this turn, against the
actual `board-gate.sh` PR #312 opens — all four results match the
proposal's spec exactly: same-author write allowed (rc 0),
foreign-author truncating overwrite denied (rc 2, "authored by ...
not ..."), foreign-author `>>` append allowed (rc 0), and an
`author:`-less legacy record still enforced under the original
role-filename rule (rc 2, "belongs to another role"). The R5 rewrite
code itself is sound by this session's own live measurement, distinct
from the test-coverage gap in the "NOT confirmed" section below.

derived: independent 20-run timing (`/tmp/bench_probe.py`, this
session's own script and methodology — the record's own
`/tmp/bench_board_gate_old.py`/`/tmp/bench_board_gate.py` no longer
exist to re-run) of the old gate (worktree of PR #312's base,
`origin/main`) vs the new gate (worktree of PR #312's head), same
own-author-append payload — result:
```
old rc set: {0} median: 41.443766094744205 min: 39.11456186324358 max: 47.49630205333233
new rc set: {0} median: 44.91251427680254 min: 40.46512674540281 max: 56.002477183938026
```
canonical: this session's own live 20-run benchmark, this turn — a
~3.5ms median delta, larger than the record's own cited ~1ms, but still
inside the ~8–16ms run-to-run spread dominated by the `python3`
interpreter-startup cost both gates pay per call. This corroborates the
record's "no material added per-spawn overhead" conclusion, though not
its specific number.

### Mechanical claims — NOT confirmed as stated

The record (`docs/issue-2286/reports/implementation.md`, untracked in
this tree, branch `issue-2286/implementation`) states in its own
Evidence section: *"`python3 -m pytest hooks/test_board_gate.py -q` ...
13 passed in 1.56s"* and in its own "What was done": *"5 new [covering]
own-author append accepted, foreign-author truncating overwrite
refused, foreign-author `>>` append accepted, an author-less on-disk
record still enforcing the role-filename fallback, and
`EXTRA_SUBTREE`'s keys checked against the corrected pair."*

acceptance: `gh pr view 312 --repo tokenmaxxxer/tokenmaxxxer-core --json files -q '.files[].path'` —
result: `core/hooks/board-gate.sh` — **exactly one file.**
`test_board_gate.py` is not part of PR #312's diff at all. canonical:
this GitHub API response, read live this turn.

acceptance: `python3 -m pytest core/hooks/test_board_gate.py -q`, run
this turn from this session's own worktree of PR #312's real head
(`2914cd52e79ac8927ec5279119cad868ce0b69c1`) — result:
```
........                                                                 [100%]
8 passed in 15.09s
```
canonical: this session's own live run, this turn — 8, not 13.
`grep -n '^def test_' core/hooks/test_board_gate.py` (same worktree)
lists exactly the 8 pre-existing heredoc/mention-only cases; none of
the 5 named new cases (author-match, foreign-truncate-deny,
foreign-append-allow, legacy-fallback, EXTRA_SUBTREE-key-check) exist
in this file on this branch.

canonical: `git show a4bb55f --stat` (this session's own core checkout
at `$CLAUDE_PLUGIN_ROOT_CORE`, branch
`issue-2286-board-gate-r5-author-identity`, read live this turn) —
result: `core/hooks/test_board_gate.py | 71 +++...` — this original,
unmerged, never-PR'd commit does carry the 5-new-test diff the record
describes. PR #312's own description (quoted verbatim,
`gh pr view 312`, read live this turn): the original branch had "a
stale merge-base (38052e5, ~99 files of unrelated phantom diff)" and
was "recut here onto current main with only the intended file" —
singular. The recut kept `board-gate.sh`'s changes but dropped
`test_board_gate.py`'s. The record's Evidence section is true of the
`a4bb55f` commit tree, which was never opened as a PR; it is false of
`tokenmaxxxer-core` PR #312, the artifact that will actually be
reviewed and merged.

canonical: `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
"How you'll know it worked" (this repo's `main`, read directly) —
requires `test_board_gate.py` to "gain cases" for the four R5 behaviors
and the `EXTRA_SUBTREE` check. PR #312 as opened (per the `gh pr view
--json files` result above) does not meet this. The R5 logic itself is
not defective — this session's own independently built probes (above)
confirm it behaves exactly as specified — but the delivered PR carries
no regression protection for it, and the record's own cited acceptance
command's fenced output (`13 passed in 1.56s`) does not match what
`python3 -m pytest core/hooks/test_board_gate.py -q`, run against PR
#312's actual head this turn, produces (`8 passed`).

## Why

Per this role's EARL-style scope (worst-case verdict over cited
acceptance entries), `result: failed` here despite the R5 rewrite code
itself working correctly, per this session's own live
`/tmp/probe_gate.py` run in the "R5 behavior" section above.

canonical: the test-coverage gap documented in the "NOT confirmed as
stated" section above (this session's own live `gh pr view --json
files` and `pytest` runs, quoted there) is the failing basis — the
implementation record's own Evidence section makes a specific,
falsifiable claim about `test_board_gate.py` that those same live
commands disprove.

Precedent: this repo's issue-2207 execution-observation record (`git
show 206b8129:docs/issue-2207/reports/execution-observation.md`,
canonical, read this turn) took the same posture: `result: failed` on a
citation gap alone, independent of whether the underlying change itself
was sound.

## Upstream basis

`docs/issue-2286/reports/implementation.md` (untracked in this tree —
lives on branch `issue-2286/implementation` at commit
`117ce2aac0825ac08fd4e29cd22d39af3767eb59`, PR #2387) and
`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
(this repo's `main`, sha `135712e8e4c56195aa0dedab6060db1610f3dc13`) are
the two documents every claim in this record was checked against.
tokenmaxxxer-core PR #312 (branch
`fix/issue-2286-board-gate-r5-author-identity`, commit
`2914cd52e79ac8927ec5279119cad868ce0b69c1`) is the actual code artifact
checked, per `gh pr view 312 --repo tokenmaxxxer/tokenmaxxxer-core`,
read live this turn.

## Open findings

- **`test_board_gate.py` carries no coverage for the author-identity R5
  rewrite in the PR that will actually be merged (tokenmaxxxer-core PR
  #312).** canonical: `gh pr view 312 --repo tokenmaxxxer/tokenmaxxxer-core --json files`
  (read live this turn, quoted above) — single-file diff,
  `core/hooks/board-gate.sh` only. Resolution path: a follow-up commit
  on `fix/issue-2286-board-gate-r5-author-identity` (or a fresh commit
  against current `main`) re-adds the 5 cases. derived: `git show
  a4bb55f --stat` (quoted above) shows those 5 cases already exist,
  written, in the original `a4bb55f` commit's own
  `core/hooks/test_board_gate.py` diff (`+71` lines) at
  `$CLAUDE_PLUGIN_ROOT_CORE`, branch
  `issue-2286-board-gate-r5-author-identity` (not pushed as the `fix/`
  branch PR #312 actually opens) — before PR #312 merges.
- none beyond the above — every other claim this session checked
  (EXTRA_SUBTREE correction, `author:` field semantics, R5's four
  behaviors, the migration doc's content and cutover date, the overhead
  measurement's conclusion, and the cross-repo PR-channel gap) held up
  under this session's own independent re-derivation, cited above.

## Next steps

- loop_state: handed-off.

  canonical: every acceptance command cited above was executed live
  this turn — this role's review work here is finished.

  A human or the implementation role decides whether to land PR #312
  with a follow-up test commit first, or accept the gap and land tests
  separately; this role does not merge or re-open PRs itself.

- Issue #2286's own Acceptance section stands unsatisfied for now: this
  session's own live pytest run against PR #312's head (Mechanical
  claims section above) diverges in test count from the implementation
  record's own cited pytest run (same section above). Until
  tokenmaxxxer-core PR #312 gains equivalent test coverage (or an
  operator explicitly waives it), this gap stands.

## What did not work

An early version of this session's own timing/behavior probe script was
written as a `python3 - <<'EOF' ... EOF` Bash heredoc targeting `/tmp` —
refused by this session's own `board-gate.sh` ("a Bash call carries an
un-analyzable write-capable shape ... issue-225") even though the
target was outside `docs/` entirely, because this session's own write
scope is bound by the very gate under review. canonical: the refusal
message, produced live this turn against this session's own attempted
Bash call. Fixed by writing probe scripts through the `Write` tool and
invoking them with a plain `python3 /tmp/....py` (a provably
read-only-shaped Bash invocation) instead. No unresolved defect in this
review itself remains.

## skill-verdict

skill-verdict: work-in-english — applied: invoked; this record and all
cited commands/output are in English per the skill; the final
user-facing summary in this session's reply is in Korean.
