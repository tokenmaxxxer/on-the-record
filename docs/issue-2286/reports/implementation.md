---
issue: 2286
role: implementation
author: implementation
kind: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
code_under_review:
  - tokenmaxxxer-core:core/hooks/board-gate.sh
  - tokenmaxxxer-core:core/hooks/test_board_gate.py
  - docs/issue-2286/reports/implementation/board-gate-r5-migration.md
type: feat
breaking: none — additive; every author:-less (pre-stage-1) record keeps the original role-filename-only R5 behavior unchanged
verdict: pass
---

# issue-2286 — implementation record

## What was done

Delivered issue #2241 stage 3 exactly per
`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`'s
files: write set, cross-repo (`tokenmaxxxer-core:core/hooks/board-gate.sh`,
`tokenmaxxxer-core:core/hooks/test_board_gate.py`, both edited in place at
`$CLAUDE_PLUGIN_ROOT_CORE`), plus the migration doc (relocated — see
Deviations):

- `board-gate.sh` R5 (reports/ ownership) rewritten to read a record's
  own `author:` frontmatter field (`_record_author`, reading `_record_text`
  of the target path) instead of matching the writing session's role
  against the record's filename. Matching author writes freely
  (`continue`); a differing author may still write when the call is
  provably append-only (`_write_is_append_only`: for Write/Edit/MultiEdit,
  `gate_lib.gate_reconstruct_write(tool, ti, existing_text)` then
  `new_text.startswith(existing_text)`; for Bash, `_bash_append_only`
  requires every failing segment naming the target to reach it via a bare
  `>>` redirect or `tee -a`/`--append`, never a truncating `>`, an
  in-place sed/awk edit, `dd`, or a `tee` with no `-a`); anything else
  denies with an "authored by ... not ..." message. A record carrying no
  `author:` field (file absent, or present without the field) falls
  through unchanged to the original role-filename check.
- `EXTRA_SUBTREE` corrected from the stale `{"feasibility": "spikes",
  "ops": "postmortems"}` to `{"technical-feasibility": "spikes",
  "release-engineering": "postmortems"}`, matching `board.py`'s own
  already-correct equivalent ownership check.
- `test_board_gate.py` test count after this change: 13 total (derived:
  `python3 -m pytest hooks/test_board_gate.py -q` from
  `$CLAUDE_PLUGIN_ROOT_CORE` — see the fenced run in ## Evidence below;
  8 pre-existing cases kept unmodified + 5 new), the 5 new covering:
  own-author append accepted, foreign-author truncating overwrite
  refused, foreign-author `>>` append accepted, an author-less on-disk
  record still enforcing the role-filename fallback, and
  `EXTRA_SUBTREE`'s keys checked against the corrected pair by parsing
  the gate's own source.
- The migration doc for this stage (relocated — see Deviations) states
  the fallback rule, the stage-1 cutover date, and the `EXTRA_SUBTREE`
  correction, per the proposal's "What will be done" spec for that doc.
- Cross-repo delivery stops at a pushed branch in `tokenmaxxxer-core`
  (commit `a4bb55f`, branch `issue-2286-board-gate-r5-author-identity`)
  — this role session cannot open the PR itself there. canonical: `gh pr
  create`/`gh issue create` refusal messages produced live this turn by
  this session's own `upstream-defect-scope-guard`/`gh-guard` hooks (see
  Open findings for the exact text).

## Why

Chosen (matches the proposal's own Rationale, re-verified against the
actual code rather than taken on faith): a lease (`roster.py`'s
issue-scoped lease, stage 1) answers "who currently holds the right to
work this issue right now"; `author:` answers "who actually wrote the
content already sitting in this file." Those can disagree mid-flight —
one session's lease expires, a second acquires it — so R5's
foreign-write check must key off authorship of existing content, not
whoever currently holds the lease. Rejected alternative (the proposal's
own, not a new one this session considered): keying R5 off the lease's
issue-scope alone, dropping `author:` as a separate field — rejected
because that re-collapses concurrency (job (a)) and write-isolation (job
(b)) into one key, the exact overloading issue #2241 retires.

Append-only-for-foreign-authors implementation choice: the proposal
requires a foreign-authored record stay writable for new content, "not
read-only-foreign," but never with an altered existing line. Rather than
inventing a new diff mechanism, this reuses `gate_lib.gate_reconstruct_write`
(already in `gate-lib.py`, built for exactly this: reconstructing a
Write/Edit/MultiEdit's resulting content against `existing_text`) for
the three JSON-tool cases, and a narrow, conservative, fail-closed regex
scan (`_bash_append_only`) for Bash — mirroring this same gate's own
existing posture toward unanalyzable Bash write shapes (issue-225): when
this gate cannot prove a write is append-only from the command text
alone, it denies rather than guesses.

## What did not work

An early draft of `_bash_append_only` denied a real, provable append
outright: it treated any segment containing a literal `<<` substring as
unprovable, which also caught the visible REDIRECT line of a
`cat <<'EOF' >> target` heredoc (not just its masked body). derived:
`python3 -m pytest hooks/test_board_gate.py -q` first run against that
draft failed `test_author_bearing_record_allows_append_from_a_different_author`
(rc 2, "authored by" refusal on a call that should have been a provable
append); fixed by dropping the blanket `"<<" in stripped` check and
relying only on the segment's actual `FILE_REDIR` operator match, then
re-run clean (see the fenced 13-passed run in ## Evidence). Fixed before
this record's own commit — no unresolved defect remains.

## Upstream basis

`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
(sha `135712e8e4c56195aa0dedab6060db1610f3dc13`) is the authoritative
spec this record follows verbatim for files:, Constraints, Out of scope,
and Rollback. `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md`
and `directive_assembly.py`'s `_stamp_additive_record_fields`
(`author: {role}\n`, one call site) establish what the `author:` field
this stage reads actually contains today.

## Open findings

- **Cross-repo PR could not be opened by this session.** `gh pr create
  --repo tokenmaxxxer/tokenmaxxxer-core ...` was refused by this
  session's own `upstream-defect-scope-guard` ("the upstream defect
  channel files issues only, never PRs"); the suggested fallback, `gh
  issue create --repo tokenmaxxxer/tokenmaxxxer-core ...`, was then
  refused by `gh-guard` ("issues are the user's requirement backlog,
  user-authored only (contract v3 s9) — no role touches them").
  canonical: both refusal messages were produced live by this session's
  own PreToolUse hooks against the actual `gh pr create`/`gh issue
  create` invocations attempted this turn.
  Resolution path: the code is committed and pushed
  (`tokenmaxxxer/tokenmaxxxer-core` branch
  `issue-2286-board-gate-r5-author-identity`, commit `a4bb55f`) — a
  human or a differently-scoped session (not a role session bound by
  these same two gates) opens the actual PR from that branch.
- **Migration doc filed under this issue's own tree, not the path the
  proposal names.** See Deviations for the full citation. canonical:
  the same live `Write`-tool R4 refusal cited there.
- none beyond the two above.

## Next steps

- A human (or non-role session) opens the PR from
  `tokenmaxxxer/tokenmaxxxer-core`'s pushed
  `issue-2286-board-gate-r5-author-identity` branch and merges it —
  this stage's core-repo half is not landed until that PR merges,
  independent of this repo's own PR for this record. canonical: commit
  `a4bb55f` on that branch, pushed live this turn (`git push -u origin
  issue-2286-board-gate-r5-author-identity` succeeded).
- issue #2286 can close once that cross-repo PR merges (or the human
  judges the pushed-branch state sufficient — the proposal's Rollback
  section makes clear reverting it is a single, safe, byte-identical
  operation either way).

## Deviations

- **Migration doc path.** The proposal names
  `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
  (untracked, never created) for this doc. Written instead under this
  session's own docs/issue-2286/reports/implementation/ subtree: a
  live probe (`Write` tool call to the proposal's named path, from
  branch `issue-2286/implementation`) was refused by `board-gate.sh` R4
  itself — canonical: "writing docs/issue-2241/ requires branch
  issue-2241/implementation (current: issue-2286/implementation)",
  produced live this turn — proving R4 is unaffected by this stage's
  R5-only change, and that this session's own write scope under the very
  gate it is rewriting does not reach the proposal's named path. Content
  is otherwise what the proposal's "What will be done" section specifies
  for that doc.
- **Cross-repo delivery stops at a pushed branch, not a merged PR.**
  canonical: the `gh pr create`/`gh issue create` refusal messages
  produced live this turn, quoted in full in Open findings above — a
  role session has no channel to open a PR or file an issue against an
  upstream repo under this session's own gates.

## Operator-frozen constraint reconciliation

amendments-reconciled: issuecomment-5407297176 (and its identical
predecessor issuecomment-5403811225) — "the fix must hold systemically
for every session ... and must land without side effects: no added
per-spawn overhead or steady-state load, no new conflict surfaces, no
stall/deadlock modes, no consumer-tree pollution."

This change is a pure rewrite of one PreToolUse gate's own decision
logic (`board-gate.sh` R5): it adds no background process, no lock file,
no append-log, and no new state of any kind — every consumer repo sees
only the same gate binary making a different, purely local decision per
tool call, exactly as R1-R4 already do. The one added cost per gated
call is a single `open()`+`read()` of the target record's current
on-disk text (already necessary to check `author:`) plus one regex
search — measured directly rather than assumed:

acceptance: `python3 /tmp/bench_board_gate_old.py` (pre-change gate,
`git show HEAD~1:core/hooks/board-gate.sh`, 20 runs, own-author append)
— result:
```
sanity rc=0 err=''
old gate, own-record append x20: min=38.5ms median=44.5ms max=63.7ms
```

acceptance: `python3 /tmp/bench_board_gate.py` (post-change gate, same
payload shape, 20 runs) — result:
```
sanity rc=0 err=''
own-author append x20: min=41.1ms median=45.4ms max=74.0ms
```

Median delta stayed under a millisecond against a baseline dominated by
`python3` interpreter startup (both old and new gate spawn one `python3
-c ...` process per call) — the added read+regex is not measurably
distinguishable from run-to-run noise. No consumer-tree pollution: the
only new file this stage plants anywhere is this repo's own migration
doc, inside this session's own granted write scope; no file is written
into any consumer repo's tree by the gate itself. No new conflict
surface or stall/deadlock mode: the added logic is synchronous,
read-only against the target file, and introduces no waiting, locking,
or retry loop.

## Evidence

acceptance: `python3 -m pytest hooks/test_board_gate.py -q` (run from
`$CLAUDE_PLUGIN_ROOT_CORE`, the live-mounted core checkout this
session's own hooks execute against) — result:
```
.............                                                            [100%]
13 passed in 1.56s
```

Live probe against this session's OWN rewritten gate (not a fixture):
writing this very record succeeded through the rewritten R5's
author-match branch (this record's own `author: implementation`
frontmatter matches this session's `CLAUDE_ROLE`) — this write's own
success, having gone through the live-mounted gate this stage rewrote,
is that proof.

## Acceptance verification

- derived: `python3 -m pytest hooks/test_board_gate.py -q` (from
  `$CLAUDE_PLUGIN_ROOT_CORE`) — checked: `hooks/test_board_gate.py` —
  result: pass, all cases (see the fenced run above)
- derived: `python3 -c "compile(open('/tmp/embedded2.py').read(), '<embedded>', 'exec')"`
  (the gate's embedded Python payload, extracted from
  `core/hooks/board-gate.sh`) — checked: syntax validity — result: pass
- derived: live `Write` tool probe to
  `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
  (untracked path) from branch `issue-2286/implementation` — checked: R4
  still refuses a foreign-issue write after this stage's R5-only change
  — result: pass (refused as expected, R4 message unchanged in shape)

## skill-verdict

skill-verdict: work-in-english — applied: invoked; this record, the
core-repo commit/PR-body drafts, and all code/comments/tests are in
English per the skill; the final user-facing summary in this session's
reply is in Korean.
other mounted skills: not triggered — implementation-blueprint (single
existing file, one already-frozen spec, no multi-module structure
decision), implementation-complexity-coupling-management (no coupling/
cohesion metric crossed a threshold), implementation-design-pattern-selection
(no GoF-pattern introduced or removed), implementation-performance-data-structure-choice
(a dict lookup and two small regex scans, not a data-structure/algorithm
trade-off) all reviewed against this task and judged not applicable.
