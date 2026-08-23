# docs/decisions — machine-readable decision registry (issue #2104)

Decision records in this directory carry YAML front-matter that
`gates/frozen_decisions.py` parses into a registry. The lint
(`gates/test_frozen_decisions.py`, or `python3 -m gates.frozen_decisions`)
asserts every file parses and every frozen decision has a non-empty scope.

## Front-matter format

```yaml
---
id: single-skill-axis        # stable slug; defaults to the filename stem
status: frozen               # frozen | active | superseded
scope:                       # REQUIRED non-empty when status: frozen
  globs:                     # path globs the decision governs
    - "roles/**"
  keywords:                  # case-insensitive substrings of a recommendation
    - "role manifest"
---
```

Other keys (`kind`, `date`, `subject`, `origin`, `legacy-status`, ...)
pass through untouched. Parsing is dependency-free restricted YAML:
scalar `key: value` lines, plus one nested-mapping level whose values
may be `- item` lists — keep authored front-matter to that shape.

- `frozen` — an operator-level principle. Changing it requires an
  operator decision that supersedes the record; a consult cannot.
- `active` — a normal landed decision; informational for the gates.
- `superseded` — kept for history; point to the successor in the body.

## Constitution check + disposition contract

`gates/constitution_check.py` is the mechanical layer that blocks
silent adoption of consult output:

1. `check_recommendation(text, touched_paths)` — computes scope
   intersection (keywords against the recommendation text, globs
   against paths the adoption would touch). No intersection => `skip`
   with a logged reason. Intersection => `needs-disposition`, naming
   the frozen decision(s).
2. The semantic judgment — does the recommendation actually contradict
   the principle? — stays with the orchestrator (fresh-context
   principle-check pass). This gate only enforces that a disposition
   EXISTS.
3. `check_disposition(issue_text, decision_ids)` — an issue that cites
   a consult-trace whose scope intersects a frozen decision must
   contain, for each intersecting decision, either

   - `reaffirms <decision-id>` (the orchestrator judged no conflict /
     the recommendation upholds the principle), or
   - `escalated-to-operator: <link or quote>` (a named conflict; one
     escalation record covers all intersecting decisions).

   Missing disposition is a named-conflict failure — the check names
   the decision id, never a bare refusal.

## Evidence-pointer contract (consults)

Each factual claim in a consult answer may carry, on its line,
`evidence: <path>[:<line>]` or `evidence-cmd: <read-only command>`.
`gates/evidence_check.py` stamps every claim `verified` / `failed` /
`unverified-cmd` (commands outside the grep/test/git-log-shape
allowlist are never executed) / `no-evidence` (advisory, weight-zero
by contract, not an error). The consult path in `spawn.py` appends a
compact stamp summary to the consult trace line — env
`OTR_EVIDENCE_CHECK=0` disables it; a verifier crash fails open with a
`runs/ledger.jsonl` event so consults never stall.
