---
status: proposed
files:
  - gates/patrol_queue.py
  - on-the-record/hooks/test_patrol_queue.py
  - gates/patrol_trigger.py
  - on-the-record/hooks/test_patrol_trigger.py
  - docs/issue-1582/reports/patrol-measurement-2026-08-15.md
---

## Request

Build the tier-1 (mechanical-scanner-only) slice of a role-patrol
pilot: a fingerprinted findings queue that scans a target repo with
existing gate scripts run in scan mode, dedups/absence-closes findings
across runs, separates a diff lane (merge-triggered, promotable) from a
sweep lane (whole-repo, never promotable), enforces per-scanner and
per-repo budgets that drop rather than backlog on overflow, verifies
each finding's excerpt still exists before enqueue, and remembers
dismissals by fingerprint. No LLM call anywhere in this slice, and no
code path that turns a queue entry into an issue — that step stays
human-triggered, out of scope here.

## Constraints

- No LLM invocation anywhere in the diff (issue's own grep-checkable
  acceptance criterion: no spawn.py consult/agent calls from patrol
  code).
- No auto-promotion code path — queue-to-issue only via a human-
  confirmed orchestrator step, not built in this pilot (issue design
  req 9, explicit non-goal).
- Sweep-lane findings must be structurally unable to be marked
  promotable — this is a lane-separation invariant, not just a default
  (issue design req 3, "promotion logic must hard-check it").
- Fingerprint identity excludes line numbers (context-region hash of
  surrounding lines instead), so a finding survives an unrelated
  line-shift elsewhere in the file (issue design req 1; SARIF/GitHub
  Code Scanning precedent cited in the issue).
- Post-merge trigger must not be a git-native `.git/hooks/post-merge`
  file — this repo's own precedent (docs/issue-392's post-merge
  reconciliation proposal) rejected a standalone hook file for the
  reason that hooks don't propagate via clone/fork and are invisible to
  the harness; the same reasoning applies here.
- Trigger-identity gate: patrol's own commits/artifacts (queue writes,
  measurement records) must never satisfy the condition that re-arms
  the trigger — this is the #1360-class regression this pilot must not
  reintroduce (spawn-on-PR's own historical failure, gates/spawn_on_pr.py
  lines 14-22, was recursive self-triggering with no originator check).
- Budgets are hard caps with drop-not-queue semantics, matching
  gates/spawn_on_pr.py's SPAWN_CAP shape: overflow becomes one
  meta-finding stating the drop count, never a growing backlog (issue
  design req 5; Renovate/Dependabot precedent cited in the issue).

## Rationale

**Chosen approach**: one new module, `gates/patrol_queue.py`, owns the
queue lifecycle (fingerprint, enqueue/dedup, absence-close, lane,
budget, verifiability, dismissal) as pure functions over a JSONL file,
callable both from a CLI entry point and from tests without any git or
network dependency. A second, small module, `gates/patrol_trigger.py`,
owns only "was this event a genuine post-merge event, and is the
committer/artifact set eligible to fire" — kept separate from
`patrol_queue.py` because the trigger-identity guard (#1360-class) is a
different failure axis (recursive self-triggering) from the queue's own
correctness (fingerprint stability, dedup, budgets), and issue design
req 4 asks for the regression test to prove specifically that
patrol-produced artifacts don't re-trigger — a clean module boundary
makes that test exercise exactly one function's contract instead of the
whole queue.

**Alternative considered and rejected — one combined module
(`patrol.py`) for both queue and trigger logic**: the issue explicitly
requires a dedicated #1360-class regression test (design req 4,
acceptance list) proving trigger non-reentrance. Folding trigger-arming
logic into the same module as fingerprinting/budgets would make that
regression test depend on the whole queue's behavior being correct
first, coupling a narrow identity-guard test to a much larger surface.
spawn_on_pr.py's own #1360 fix (docstring, gates/spawn_on_pr.py:14-22)
was itself a scope-narrowing fix (PR-creation-only, not board-wide) —
narrow, single-purpose modules are the pattern this repo already
converged on for exactly this failure class.

**Alternative considered and rejected — a git-native
`.git/hooks/post-merge` file as the trigger**: rejected for the same
reason docs/issue-392's post-merge-reconciliation proposal rejected a
new standalone sync step: git hooks are local-only, don't propagate via
clone/fork, and are invisible to the harness driving role sessions.
`patrol_trigger.py` instead exposes a callable entry point meant to be
chained onto the merge command the orchestrator already runs (mirrors
#392's chosen approach), so there is no second mechanism to forget to
invoke.

**Alternative considered and rejected — reproducing the issue's
"proposal frontmatter validity" scanner as this repo's second tier-1
scanner**: the issue cites that scanner's 4-true-positive result from
the *consumer* repo (`/home/jwjung/tokenmaxxxer`), a different
codebase; this repo has no equivalent standalone Python scanner for
that check (docs/issue-1582/reports/implementation/survey.md's survey
confirmed the shape check lives only in a plugin-side shell hook, not
present in this repo's own tree). Design req 8 only requires reusing
*some* existing gate script in scan mode with a >=90% hand-checked
actionable rate; `gates/record_lint.py`'s existing whole-repo scan mode
(`find_records`/`lint_record`) already satisfies that on its own
without inventing a new scanner admission process in this pilot.

## What will be done

1. `gates/patrol_queue.py`:
   - `fingerprint(scanner_id, path, context_lines) -> str`: sha256 over
     scanner_id + normalized path + a hash of the surrounding
     non-blank context lines (not raw line numbers), so a finding's
     identity survives unrelated line-shifts elsewhere in the file.
   - `enqueue(queue, finding) -> queue`: existing fingerprint refreshes
     `last_seen` only; new fingerprint appends a new entry with
     `first_seen == last_seen`.
   - `absence_close(queue, scope, seen_fingerprints) -> queue`: any
     entry whose scope was covered by this scan and whose fingerprint
     did not reappear in `seen_fingerprints` is marked `status=fixed`.
   - Lane field (`diff` | `sweep`) is set at enqueue time from the
     caller's scan mode and is never mutated afterward; a `promotable`
     flag can only be true when `lane == "diff"` — enforced inside the
     same function that would set it, not left to caller discipline.
   - `apply_budget(findings, per_scanner_cap) -> (findings, meta)`:
     truncates each scanner's findings at the cap and returns one meta
     finding per truncated scanner stating the drop count; caller
     applies the same shape at the per-repo-per-day level.
   - `verify(finding, repo_root) -> bool`: re-reads the cited path and
     confirms the quoted excerpt is still present verbatim before
     enqueue; a finding that fails this check is dropped and counted,
     never queued.
   - `record_dismissal(queue, fingerprint, reason) -> queue`: reason is
     one of `false-positive` / `wont-fix` / `test-code`; dismissed
     fingerprints are excluded from future enqueue and a per-scanner
     dismissal counter is maintained for a later eviction contract
     (counters land now, enforcement is explicitly out of scope per
     issue design req 7).
   - A scanner adapter for `gates/record_lint.py`'s scan mode
     (`find_records` + `lint_record`) wired in as the pilot's one
     tier-1 scanner.
2. `on-the-record/hooks/test_patrol_queue.py`: unit tests for
   fingerprint stability under line-shift, dedup refresh, absence-close,
   lane separation (sweep entries can never be `promotable=true`),
   per-scanner cap overflow meta-finding, verifiability drop, dismissal
   suppression — the exact list the issue's acceptance section names.
3. `gates/patrol_trigger.py`: a callable entry point
   (`should_fire(event) -> bool`) that checks the event's origin against
   an originator allowlist excluding patrol's own commit/artifact
   signature (queue-file-only diffs, measurement-record-only diffs),
   plus a small runner that invokes the queue scan when `should_fire`
   is true. Not wired into a git-native hook (per Constraints); exposed
   as a function meant to be called from the merge-command seam.
4. `on-the-record/hooks/test_patrol_trigger.py`: the #1360-class
   regression test — construct an event whose only diff is a
   patrol-produced queue/measurement-record commit and assert
   `should_fire` returns false.
5. A single live run against the target repo named in the issue
   (`/home/jwjung/tokenmaxxxer`), recorded as
   `docs/issue-1582/reports/patrol-measurement-2026-08-15.md`: wall-clock,
   findings enqueued per scanner, verifiability-drop count — the
   tier-2 go/no-go input the issue's acceptance section requires.
6. Confirm by grep that no `spawn.py consult`/agent-invoking call
   exists anywhere in `gates/patrol_queue.py` or `gates/patrol_trigger.py`
   (issue's own stated acceptance check).

## Out of scope

- LLM tier-2 scanning of any kind.
- A read-only consult verb (upstream defect #1581, explicitly deferred
  by the issue).
- Any code path from queue entry to GitHub issue — promotion stays a
  manual, human-confirmed orchestrator action not built here.
- Per-role rotation scheduling.
- Eviction enforcement (>=10% probation / >=25% stop-promoting) beyond
  maintaining the counters the eviction contract will read later.
- Wiring `patrol_trigger.py` into the actual merge-command file
  (`on-the-record/commands/run.md` or equivalent) — the survey found
  that seam's current state unconfirmed; phase 2 reads its live state
  before choosing the exact call site, and if that specific wiring
  needs a file outside this proposal's frozen write set, phase 2 stops
  at the scope-exceeded boundary and reports it rather than expanding
  the write set silently.

## How you'll know it worked

- `pytest on-the-record/hooks/test_patrol_queue.py on-the-record/hooks/test_patrol_trigger.py`
  passes, covering every behavior named in the issue's acceptance list.
- The #1360-class regression test in `test_patrol_trigger.py` fails on
  a reverted `should_fire` origin-check (proving it's load-bearing, not
  vacuous) and passes with the check in place.
- `docs/issue-1582/reports/patrol-measurement-2026-08-15.md` contains a
  real measured run's wall-clock, per-scanner enqueue count, and
  verifiability-drop count against the target repo.
- `grep -rn "consult\|spawn.py" gates/patrol_queue.py gates/patrol_trigger.py`
  shows no LLM-invoking call.
