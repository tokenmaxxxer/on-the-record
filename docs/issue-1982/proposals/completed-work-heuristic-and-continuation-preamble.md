---
status: proposed
files:
  - spawn.py
  - tests/test_respawn_continuation_preamble.py
  - docs/issue-1982/reports/implementation.md
---

## Request

When reconcile's dead-worker path resolves to `RESPAWN_IDENTICAL` (no
prior commit observed) and the actual respawn hits a workspace with
uncommitted changes, `_respawn_or_cap()` today forwards `.task.txt`'s
original text unmodified (survey: spawn.py:4050-4066). The new session
then has no signal that a previous session already left work in the
tree, and may redo it or re-strand it (observed: #1959 needed 3 rounds,
#1978 respawned identically). Add a continuation preamble — "workspace
contains uncommitted work from the previous session — verify briefly,
then commit/push/PR; do not redo" — prepended to the respawn task text,
gated by a minimal completed-work heuristic that classifies the dirty
workspace as finished or unfinished. This proposal's deliverable is that
heuristic and its misclassification failure modes; wiring it into
`_respawn_or_cap()` is phase-2.

## Constraints

- Heuristic must run at respawn time, using only signals already cheap
  and local at that point: `git status --porcelain`, git diff content,
  and the repo's own doc-placement/record conventions (survey:
  spawn.py:8446-8448 already computes `git status --porcelain` on this
  exact workspace in a sibling code path).
- Never push obviously unfinished work (issue's consult condition) — the
  heuristic must be conservative: default to "unfinished" (no preamble,
  byte-identical task) whenever signals are ambiguous or thin, since an
  unwarranted "verify briefly, then commit/push/PR" nudge risks landing
  broken output, while a missed continuation preamble only costs a redo
  (the existing, already-tolerated failure mode).
- Acceptance requires the unfinished branch produce a byte-identical
  respawn task versus today — the heuristic must be a pure, additive gate
  in front of the existing `task = task_path.read_text(...)` line, not a
  rewrite of it.
- No new `gh`/network calls — reconcile's existing purity contract
  (survey: spawn.py:1665-1673) extends to this heuristic; it must work
  from local git state only.

## Rationale

Considered and rejected: **reuse `_respawn_fingerprint()`'s board-hash
delta** (survey: spawn.py:3973-3981) as the finished/unfinished signal —
i.e., treat "board_snapshot() changed since last respawn" as "finished."
Rejected because `board_snapshot()` tracks issue/PR-board state, which by
definition hasn't changed yet for exactly the case this issue targets
(work sits uncommitted, never reached a PR) — the signal is structurally
blind to the one state transition this heuristic needs to detect. Using
it would mean the heuristic keys off a value that's guaranteed constant
across every dirty-uncommitted respawn, i.e. no discrimination at all.

Considered and rejected: **ask the dying session to self-report
finished/unfinished in a marker file** before exit (e.g. a `.finished`
sentinel the session writes as its last act). Rejected because the
failure modes this issue exists to catch are exactly the ones where the
session dies mid-work, crashes, or is killed (survey: `_auto_respawn_check`
fires on watchdog `crashed`, spawn.py:4069-4104) — a self-report requires
the session to reach a clean exit path, which is the case that's already
fine today (`session_end_verdict` already handles orderly completion). A
self-report heuristic would be unreachable in precisely the crash/kill
scenarios that produce the RESPAWN_IDENTICAL dirty-workspace case.

Chosen approach: a **local, git-only structural heuristic** — classify
"finished" only when uncommitted changes are (a) non-empty, (b) contain
at least one file under the record-shape-required paths for the current
role's kind (e.g. `docs/issue-<n>/reports/<role>.md` or its phase-1
survey/proposal siblings, per the role-handoff contract's own
placement rules already enforced by `record-shape-gate.sh`/
`survey-order-gate.sh`), and (c) the diff for that record file is
non-trivial (more than a frontmatter-only stub — reuse the same
non-empty-body check `record_lint.py` gates already apply to these
files). All other dirty states — code-only changes with no
record file, a record file that's frontmatter-only, or a `git status`
with no tracked changes at all (only stray untracked scratch files) —
classify as "unfinished." This keys off the same shape gates already
mechanically enforced at commit time (record-shape-gate.sh,
proposal-shape-gate.sh), so "looks finished" tracks "would actually pass
this repo's own definition of a landable unit" rather than a generic
LOC/diff-size proxy, which has no relationship to whether the work is
safe to hand off.

## What will be done

Phase 2 (this proposal is phase 1 only) will:
1. Add `_classify_workspace_completion(work: str, role: str) -> str`
   (returns `"finished"` or `"unfinished"`) to `spawn.py`, implementing
   the git-only structural check above.
2. Call it from `_respawn_or_cap()` immediately after
   `task = task_path.read_text(...)`, only when `git status --porcelain`
   on `work` is non-empty (dirty workspace) — clean workspaces are
   unaffected and keep today's byte-identical task.
3. When classified `"finished"`, prepend the continuation preamble to
   `task` before the `_spawn_one()` call; when `"unfinished"`, leave
   `task` untouched.
4. Add `tests/test_respawn_continuation_preamble.py` with a fixture dirty
   workspace for each branch, asserting (a) finished → preamble text
   present in the respawn task, (b) unfinished → task byte-identical to
   `.task.txt`'s original content, run live per the issue's acceptance
   check.
5. Document the heuristic's known misclassification failure modes (below)
   in `docs/issue-1982/reports/implementation.md`.

### Misclassification failure modes (this proposal's core deliverable)

- **False "finished"**: a session writes a syntactically complete-looking
  record file (frontmatter + non-trivial body) but the actual code change
  it describes is broken or incomplete — the heuristic only inspects
  record-file shape, not code correctness. Mitigated, not eliminated, by
  the preamble's own wording ("verify briefly" — it does not say "push
  without checking"); a human/session still gates the actual push.
- **False "unfinished"**: a role whose deliverable legitimately has no
  `docs/issue-<n>/reports/**` record at this point (e.g. mid-phase-2 code
  work before the record is written, or a role kind not covered by
  `record-fields-terminal-states.json`'s default vocabulary) will always
  classify as unfinished even with substantial, real code progress — the
  conservative default (Constraints) accepts this as a known cost: a
  spurious redo, not a spurious push.
- **Boundary flicker on partial writes**: if the dying session was
  interrupted mid-write of its own record file (e.g. `Write` truncated by
  a kill signal), the file may exist with valid frontmatter but a
  truncated body — indistinguishable from a legitimately short-but-real
  body by this heuristic alone. Left as an accepted gap; a stricter check
  (e.g. requiring the record file's `loop_state:` line be present and
  syntactically valid, since a mid-write truncation is more likely to cut
  that off) is deferred to a follow-up issue if this gap proves costly in
  practice, per the same escalate-not-silently-improve norm this repo
  already uses for cap-reached respawns (survey: spawn.py:4038-4043,
  `_post_crash_comment`).
- **Multi-role workspace ambiguity**: if a workspace ever holds
  uncommitted changes attributable to more than one role/session (not
  currently possible under this repo's one-branch-per-issue-role
  convention, but not mechanically prevented), the heuristic has no way to
  attribute the record file to "the previous session" specifically versus
  older stray uncommitted state — it would classify based on whatever is
  present, without provenance. Out of scope to solve here; flagged as a
  standing assumption the heuristic inherits from the branch-ownership
  convention, not something this heuristic newly introduces.

## Accumulation

`_classify_workspace_completion()` adds one `git status --porcelain`
call, reusing the exact invocation pattern already at spawn.py:8446-8448
rather than opening a new inline subprocess call site of its own shape —
it is not a new repeated-call class. If future issues add more
respawn-time classifiers (e.g. a code-correctness check, a lint-pass
check), the right shape is to grow this one function's decision logic
(more checks feeding the same `"finished"`/`"unfinished"` return), not to
add more standalone `subprocess.run(["git", ...])` call sites inside
`_respawn_or_cap()` — N more such checks staying siloed would accumulate
into scattered git-status calls at the same chokepoint; consolidating
them in `_classify_workspace_completion()` keeps that count at one call
site regardless of how many classification rules it grows.

## Out of scope

- Wiring the heuristic into `_respawn_or_cap()` and writing the test file
  (phase 2, pending approval of this proposal).
- Extending the heuristic to the watchdog-`crashed` respawn path's
  non-dirty cases, or to `RESPAWN_WITH_HANDOFF`/`ESCALATE` verdicts —
  those already carry a commit or go to manual review respectively and
  are not this issue's stranding case.
- Consuming the `"handoff"` field reconcile's divergence dict already
  computes but which no caller reads (survey: spawn.py:3376-3377) — a
  separate wiring gap, not this issue's target.
- Solving the multi-role workspace ambiguity or record-file truncation
  gaps named above — flagged as accepted limitations, not addressed by
  this proposal.

## How you'll know it worked

Acceptance check from the issue, executed live in phase 2: with a fixture
dirty workspace classified `"finished"`, the respawn task text contains
the continuation preamble; with a fixture classified `"unfinished"`, the
respawn task is byte-identical to today's — both asserted by
`pytest tests/test_respawn_continuation_preamble.py` run live, not by
inspection.
