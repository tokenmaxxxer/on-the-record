files: on-the-record/hooks/record-claim-shape-directive.sh, on-the-record/hooks/hooks.json, on-the-record/hooks/test_record_claim_guard.py

## Request

Issue #730: `record-claim-guard.sh`'s citation shape (bare counts need a
code fence or `derived:` tag; `unverifiable:`/`checked:` lines need a
reason; backtick paths must resolve — all delegated to
`gates/record_lint.py`) is stated in no proactive directive text, so a
role session learns it only from refusal — per the #726 audit catalog
row 9, the single most frequent gate-refusal on 2026-08-11. Add a
proactive directive that states the same shape before the gate fires,
mirroring what `record_lint.py` checks with no drifting second copy.

## Constraints

- Mirror `record_lint.py`'s checks exactly, in the same order they run —
  no restating them in looser prose that could drift from the code.
- No change to `record_lint.py`'s or `record-claim-guard.sh`'s actual
  rule logic — this is a proactive-statement addition, not a rule change.
- Stays inside on-the-record's own repo (survey's conclusion): the gate
  only fires in on-the-record-hosted sessions, so the fix does not touch
  `tokenmaxxxer-core` or any per-role rulebook.
- Follow the existing sibling pattern (`record-shape`, `proposal-shape`,
  `survey-order` sub-plugins in implementation-rulebook): directive text
  and its enforcing gate travel together and are phrased to match.

## Rationale

**A new dedicated hook file, over folding the text into the existing
`hooks/directive.sh`.** `hooks/directive.sh` deliberately exits early
whenever `CLAUDE_ROLE` is set (line 12) — it is the orchestrator's own
directive (spawn/consult mechanics, board-reading, delegation rules),
none of which applies to a spawned role session, and role sessions are
exactly the audience that needs the citation shape. Repurposing it to
also serve role sessions would mean branching its entire body on
`CLAUDE_ROLE`, mixing two audiences' unrelated content in one file. A
new file scoped to role sessions (mirroring how `record-shape-gate.sh`/
`proposal-shape-gate.sh`/`survey-order-gate.sh` each pair with their own
UserPromptSubmit directive rather than being crammed into one shared
file) keeps each directive's audience and lifetime clear and matches
established precedent in this same codebase.

**Generate the directive text from record_lint.py's own check functions
and docstrings at hook-run time, over hand-typing a parallel prose
copy.** The issue explicitly warns against "authoring a second drifting
copy." record_lint.py's four checks already carry Korean explanatory
strings inline (e.g. `bare_count_claim_check`'s "issue #333" message
text) that describe the rule in prose. The alternative of hand-writing
new English/Korean directive prose independently was considered and
rejected: any wording change to a check's rule (e.g. widening
`_COUNT_NOUN`'s noun list, or changing what counts as a valid `derived:`
tag) would need to be manually re-applied to the directive text too, with
no mechanical link between the two — precisely the drift the issue names
as the failure mode to avoid. Instead, the new hook imports
`record_lint` (same `sys.path` resolution `record-claim-guard.sh` already
uses) and builds its printed text from the functions' own docstrings/
regex-derived examples, so a future change to the check logic changes
what the check *rejects* and what the directive *states* from the same
source.

**One-way generation (hook reads from record_lint.py), not a shared
external spec file both sides consult.** A third option — factor the
rule descriptions into a standalone data file (e.g. YAML) that both
`record_lint.py` and the new directive load — was considered and
rejected as unnecessary indirection: `record_lint.py` is already the
issue's own named "single source of truth," it does not need to stop
being that source to also feed a directive; adding a third file the two
existing ones would need to stay in sync with only reintroduces the
drift risk one layer out.

## What will be done

- `on-the-record/hooks/record-claim-shape-directive.sh`: a new
  UserPromptSubmit hook, following `record-claim-guard.sh`'s own
  self-hosted-detection and kill-switch conventions (`ORCHESTRATE_OFF`,
  fail-open on missing `gates/record_lint.py` rather than blocking the
  turn). Fires only when `CLAUDE_ROLE` is set (a spawned role session,
  the audience that hits the gate) and `gates/record_lint.py` is
  importable from the resolved gates directory (the same resolution
  `record-claim-guard.sh` already does) — silently no-ops otherwise
  (non-self-hosted sessions never had this gate active either, so no
  directive is owed). Emits one `<record-claim-citation-directive>`
  block naming, in `record_lint.py`'s own check order: (1) a bare count
  claim needs a code fence or a `derived: ...` tag; (2) an
  `unverifiable:` line needs a reason; (3) a `checked: ... — result:
  unverifiable` Acceptance line needs a reason; (4) a backtick-quoted
  src/test/docs/gates/on-the-record path must resolve in the working
  tree. Each rule's stated text is built from that check function's own
  docstring/message strings, not re-authored from scratch.
- `on-the-record/hooks/hooks.json`: register the new hook under
  `UserPromptSubmit`, alongside the existing entry.
- `on-the-record/hooks/test_record_claim_guard.py`: add a test that
  invokes the new hook (or imports and calls its text-building function
  directly, whichever the implementation lands as) with `CLAUDE_ROLE`
  set, and asserts the rendered text names all four rule shapes — this
  is the check the issue's Acceptance criterion asks for.

## Out of scope

- Any change to `record_lint.py`'s or `record-claim-guard.sh`'s
  enforcement logic.
- Any change to `tokenmaxxxer-core`'s or any per-role rulebook's
  directive text — the survey found the gate does not fire there, so
  there is nothing for those repos to proactively state.
- Retrofitting the same generated-from-source pattern onto
  `record-shape`/`proposal-shape`/`survey-order`'s existing hand-written
  directives — those already ship working, gate-paired text; revisiting
  their authoring method is a separate decision, not this issue's scope.

## How you'll know it worked

The new unit test in `on-the-record/hooks/test_record_claim_guard.py`
passes: it renders the deployed directive and asserts the text names the
count-needs-citation, unverifiable-needs-reason, and path-must-resolve
rules (the issue's own Acceptance wording), and fails if that text is
removed or the directive is deleted — matching the issue's stated "empty
state" requirement.
