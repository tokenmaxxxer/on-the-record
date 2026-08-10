# Issue #587 — implementation proposal (phase 1, step 2)

status: proposed
files:
  - gates/remediation_spawn.py
  - gates/test_remediation_spawn.py
  - on-the-record/commands/run.md

## Request

Build step 2 of #587: turn the approved architecture (`docs/issue-587/proposals/architecture.md`,
PR #589) into working code — the finding-to-spawn-task generator, its unit tests, and the
`run.md` contract step that consumes it. The e2e fixture-target-repo scenario is step 3's job,
not this proposal's.

## Constraints

- Write set is exactly the three files above — no `spawn.py` edit (architecture's own `files:`
  list excludes it; its section 2 wiring discussion is explicitly deferred, and this issue's
  step-2 instructions name only the generator, its test, and the run.md step).
- Task text must be derived from the remediation record's own fields via a fixed template —
  never free-authored (acceptance criterion, architecture Decision §1).
- Round counter and escalation stay driven solely by existing `remediation-*.md` records — no
  new state store (survey.md confirms nothing new is needed).
- Idempotency check reuses `git`/`gh` lookups (branch or PR carrying a `Remediation:
  <remediation_path>` trailer), not a new marker file.

## Rationale

Architecture's Decision §1 already fixed the function signature, template string, and
idempotency approach; implementation's job is realizing that exactly, not re-deciding it. The
one open call is *how* the generator's output reaches `spawn.py` from `run.md`, since the
architecture proposal deferred spawn.py's own call-site signature to implementation but then
excluded spawn.py from the write set. Two shapes were considered:

- **Add a new `spawn.py --issue <n> -C <repo>` no-positional-args mode** that internally calls
  the generator and launches pending tasks itself (architecture §2's literal wording). Rejected
  for this proposal: it requires editing `spawn.py`, which is outside the frozen write set both
  proposals share, and issue #587's own step-2 instructions list only the generator, its test,
  and "the run.md contract step" — not a spawn.py change. Widening the write set to include
  `spawn.py` here would be scope-exceeded relative to what step 2 actually asks for.
- **Have `run.md`'s orchestrator step call the generator directly (e.g. via a one-line `python3
  gates/remediation_spawn.py --issue <n> -C <repo>` CLI invocation described in the doc) and
  pass its printed `role`/`task` straight into the existing, unmodified `spawn.py <role>
  "<task>" --issue <n> -C <repo>` invocation** — chosen. This satisfies the acceptance
  criterion ("when a remediation spawn task exists, launch it and report — never re-derive
  routing") without touching `spawn.py`, keeps this proposal's write set aligned with what
  step 2 actually names, and leaves the `spawn.py` wiring architecture sketched in §2 as a
  natural follow-up if a future step wants it built into `spawn.py` itself rather than surfaced
  through the contract doc.

## What will be done

1. `gates/remediation_spawn.py`: `pending_remediation_tasks(root: Path, issue: int) ->
   list[dict]` — reads `docs/issue-<n>/decisions/remediation-*.md`, parses each record's
   frontmatter, filters to `status: open`, builds `task` via the fixed template from
   architecture Decision §1 (`Remediation round {round}: fix \`{target_path}\` —
   {required_fix} (routed from \`{remediation_path}\`, finding: \`{finding_source}\`)`),
   returns `{role, task, remediation_path, round}` per pending record. Idempotency: for each
   candidate, shell out to `git branch --list "issue-<n>/<role>"` (local) and `gh pr list
   --json headRefName,body` (remote), excluding a candidate whose branch exists or whose PR
   body contains `Remediation: <remediation_path>`. A thin `if __name__ == "__main__":` CLI
   (`--repo`, `--issue`) prints each pending task as one line (`<role>\t<task>`) for `run.md`'s
   orchestrator step to consume, matching `gates/closure_sweep.py`'s injectable-function +
   thin-CLI shape.
2. `gates/test_remediation_spawn.py`: unit tests against `tmp_path`-constructed fixture repos —
   (a) one fixture `remediation-1.md` (`status: open`) → exactly one task, exact template
   string asserted; (b) a 3-round chain of remediation records escalating per the gate's own
   round/repeat-contradiction rules → the `status: escalated` record is excluded from
   `pending_remediation_tasks`'s output (escalated is the operator's, never auto-spawned); (c)
   zero `remediation-*.md` files → `[]`, asserted explicitly as the empty-state case the
   acceptance criterion names; (d) a record whose branch/PR already exists (idempotency) →
   excluded even though `status: open`.
3. `on-the-record/commands/run.md`: insert a new step between the existing board-read step and
   the free-judgment "누구를 깨울지" paragraph (current step 3, lines 77-82): before proposing
   who to wake next, run `python3 $ON_THE_RECORD/gates/remediation_spawn.py --issue <n> -C
   <레포>`; if it prints any pending task, launch that task's `role`/`task` verbatim via the
   existing `spawn.py <role> "<task>" --issue <n> -C <레포>` step 4 invocation and report — skip
   the free-judgment routing paragraph entirely for that issue, since the routing decision is
   already made. This is the literal "launch it and report — never re-derive routing" contract
   step #587 asks for.

## Out of scope

- `spawn.py` itself (no new flag, no internal call to the generator) — deferred per Rationale.
- The e2e fixture-target-repo scenario and its record at
  `docs/issue-587/reports/execution-observation/` — step 3's job per the issue body.
- Any change to `on-the-record/hooks/delegated-judgment-gate.sh`'s existing round/escalation
  logic — this proposal only reads what it already writes.

## How you'll know it worked

- `python3 -m pytest gates/test_remediation_spawn.py` (or the repo's plain-assert runner
  convention) passes, covering: fixture finding → one task with exact template string; a
  3-round chain reaching `status: escalated` correctly excluded; zero findings → `[]` asserted
  explicitly; idempotency exclusion when a branch/PR already exists.
- `on-the-record/commands/run.md` diff shows the new step ordered between board-read and the
  existing free-judgment paragraph, referencing the generator's CLI form and the unmodified
  `spawn.py` launch step — reviewable by reading the diff.
