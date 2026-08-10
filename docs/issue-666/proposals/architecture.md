# ADR: own the record-format contract inside on-the-record's shared gate chain (issue #666)

## Context
Five phase-2 sessions (#641, #650, #653/PR #665, and today's pattern) landed
code+tests+PR successfully and then stranded on the last, purely mechanical
record write: bare commit sha in `code_under_review` (should be a file
list), an unsourced `N/N passed` count, an unfilled `## Accumulation`
section. See [survey.md](../reports/architecture/survey.md): the correct
shape already exists as code/docs in this repo
(`record-scaffold.sh`, `record_lint.py`, `record-claim-guard.sh`,
`accumulation-claim-guard.sh`, `docs/handbooks/record-authoring.md`), but
none of it is reachable from the text a session reads before it starts
authoring — that text (`SessionStart` directive) is generated in each
role's own **external** rulebook repo, outside this checkout's write scope,
and today says only where the record goes and which field *names* are
required, never how to shape them.

## Decision
Do not chase the fix into ~13+ external rulebook repos. Move the contract
enforcement entirely into the two places this repo already owns and that
already fire for every role regardless of which external rulebook spawned
the session — the shared `PreToolUse` hook chain — and make those hooks'
refusal messages carry the full shape contract inline, so a single
refusal is self-sufficient to correct the record without a docs lookup or
an orchestrator re-injecting instructions per task.

1. **New shared hook: `on-the-record/hooks/record-shape-guard.sh`**
   (PreToolUse, `Write|Edit|MultiEdit`, scoped to `docs/issue-*/reports/**`
   like its two siblings). Fires the one live check that currently does not
   exist anywhere in this repo: on a write to a role's own record, parse
   the YAML frontmatter and require `code_under_review` to be a list
   (`- path/...` items), denying with the exact corrected shape inline if
   it is a bare scalar (sha or otherwise) — e.g. "`code_under_review` must
   be a list of file paths under review, not a single value. Example:\n
   `code_under_review:\n  - src/foo.py\n  - test/test_foo.py`". Reuses
   `record_lint.py`'s existing frontmatter-parsing helper (no new YAML
   dependency) the same way `record-claim-guard.sh` already imports
   `gates/record_lint`.
2. **Harden `record-claim-guard.sh` and `accumulation-claim-guard.sh`'s
   existing deny messages to be self-sufficient.** Today's messages name
   the violation; add the corrected-shape example inline (a `derived:
   <path/to/evidence>` tag example next to a bare-count denial; the exact
   `## Accumulation\n<non-empty body>` shape next to an accumulation
   denial) so the session that receives the refusal has everything needed
   to fix it in the same turn, matching what `record-shape-guard.sh` does
   for `code_under_review`. This is the substitute for "reaching the
   authorship point": since this repo cannot edit the external
   `SessionStart` text, the next-earliest point it *does* own is the first
   write attempt, and a refusal that is a complete worked example closes
   the same gap a pre-emptive instruction would have — the session still
   authors the record correctly without a second external round-trip
   (re-reading a handbook, asking the orchestrator), which is what today's
   stranding pattern actually costs.
3. **Point `record-scaffold.sh`'s and the new guard's messages at each
   other.** `record-shape-guard.sh`'s deny text on a *first* write (no
   existing record file, malformed from scratch) suggests running
   `record-scaffold.sh <role> <issue-n>` first; this closes the loop
   between the already-correct generator (issue #517) and the point of
   failure, without requiring the generator itself become a hook (already
   ruled out on #517 — no lifecycle event to hang it off).
4. **Do not attempt to edit the external per-role `directive.sh` files
   from this repo.** They are out of write scope for any role session
   working inside this on-the-record checkout, per role-handoff contract
   v3's own layout rule (a role writes only its own record area inside the
   repo it was spawned in). Recorded as an open finding below, not
   silently absorbed.

## Consequences
- All three record-format checks (list-typed `code_under_review`,
  sourced counts, filled Accumulation) become enforceable from exactly one
  repo (on-the-record) and one lifecycle event (`PreToolUse` on the
  record-write tools), regardless of which of the ~13+ external rulebooks
  spawned the session — the judged criterion ("역할이 형식을 소유해 1회
  통과") is met at the hook layer: the format is owned by code that runs
  unconditionally, not by prose an orchestrator must remember to restate
  per task.
- `record-fields-gate.sh`'s placeholder-quality substring check, currently
  duplicated per-role inside each external rulebook, is superseded for the
  `code_under_review` shape specifically (still not touched by this repo —
  each external rulebook keeps its own copy for its role-specific required
  *field names*, which `record-shape-guard.sh` does not attempt to own).
- A session can still hit one refusal round-trip before landing a correct
  record — this proposal does not claim zero refusals, only that the
  refusal it does hit is a complete, worked correction rather than a bare
  "wrong" that sends the session hunting for the right shape (today's
  actual failure: #641/#650/#653 stranded not because the gate fired, but
  because nothing at the point of firing told the session the fix).
- New file, no new install/CI dependency: `record-shape-guard.sh` imports
  the same `gates/record_lint` module `record-claim-guard.sh` already
  imports; same zero-install, `python3`-only posture.

## Alternatives considered
- **Edit each external per-role rulebook's `directive.sh` to add a
  record-authoring pointer** (the pattern already used once for
  `architecture-methodology.md`). Rejected as this issue's primary
  mechanism: out of this repo's write scope entirely (~13+ separate repos,
  none checked out here), and even where reachable it only reduces
  *first*-attempt failures for sessions that read and retain a long
  directive — it doesn't help a session that skims past it, whereas a
  hook fires unconditionally. Left as a follow-up (below), not abandoned.
- **Make `record-scaffold.sh` a PreToolUse hook that auto-fires before the
  first record write.** Already ruled out on #517 (warrant-hunter finding):
  no lifecycle event corresponds to "author is about to start a record" —
  `PreToolUse` only sees the write already in flight, at which point a
  *deny-with-example* (this proposal) does the same corrective job without
  inventing a new trigger.
- **Leave the contract in `docs/handbooks/record-authoring.md` only,
  relying on sessions to read it.** Rejected: this is the status quo and
  is exactly what produced #641/#650/#653 — a document nothing points to
  at the moment of authoring is not part of the authorship point.

## Open findings
- **Cross-repo propagation is out of scope here and still unowned.** The
  true fix for the `SessionStart` text itself (13+ external rulebook
  repos) has no owner or mechanism in this repo — `docs/issue-170/_assets/
  rulebook-skeleton/` is a frozen template snapshot with no live sync to
  the repos it templates. Recommend a follow-up issue scoped to whichever
  role/process owns those external repos, once this proposal's hook-layer
  fix is landed and its effect on recurrence is observed.
- `record-fields-gate.sh`'s "placeholder — harden before treating as
  load-bearing" self-assessment (issue #170) is still true post-#666; this
  proposal does not harden it, only supersedes its one weakest check
  (`code_under_review` shape) at a layer it cannot skip.

## Hand-off
No `api-design` hand-off — no interface shape beyond a hook's own
deny-message text. No `performance-engineering` hand-off — one more
`PreToolUse` hook firing only on `docs/issue-*/reports/**` writes, same
cost class as the two siblings it joins. Implementation (phase 2, after
approval) stays within this same architecture role's branch per contract
v3 s19.
