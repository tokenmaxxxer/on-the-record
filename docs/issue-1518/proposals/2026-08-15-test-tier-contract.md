---
status: proposed
files:
  - gates/test_tier_contract.py
  - tests/test_test_tier_contract.py
  - on-the-record/hooks/test-tier-directive.sh
  - on-the-record/hooks/test_test_tier_directive.py
  - on-the-record/hooks/hooks.json
  - docs/handbooks/operations.md
  - docs/specs/reconciled-index.md
---

## Request

Generalize #1490's test wall-clock discipline (fast tier by default,
budget-bounded, slow tier opt-in) from this one repo into a file
convention (`.on-the-record/test-tiers.json`) any target repo can
declare, so verification roles read it instead of re-deriving the
discipline per repo; when a target repo has none, measure and record the
gap instead of running a silent full suite.

## Constraints

- Schema mirrors #1490's landed shape: `fast` (command + `budget_seconds`,
  default 300) and optional `slow` (command + trigger change-classes).
- File convention, not a `roles/*.json` field (issue #1518 req 1 is
  explicit about this).
- No-contract path must never silently run a full suite (req 3).
- Enforcement stays observe-only at this stage — a directive line, not a
  gate that refuses an over-budget run (req 4; gating waits for >=1 real
  target-repo adoption).
- Same reinstall batch as the current drive — no plugin manifest version
  bump beyond what `hooks.json`'s existing entries already need.
- The design must name its merge point with #1493's future check-run
  artifact (req 5) — done in the current-state survey's "#1493 merge
  point" section; not repeated here since it's a survey finding, not a
  build decision.

## Rationale

Considered keeping the contract as a `roles/*.json` field (e.g. a
`test_tier` key on `execution-observation.json`) instead of a target-repo
file. Rejected: `roles/*.json` lives in *this* plugin repo and is shared
across every target repo a role clones into — a per-repo tier contract
cannot live in a repo-shared config without keying it by target-repo
identity, which is exactly what a file dropped into the target repo's
own checkout does for free (the file's mere presence in that checkout
*is* the key). The issue text itself already forecloses this
("file-convention based ... NOT a roles/*.json field"), and the survey's
`gates/repo_scope.py` precedent confirms "target repo" is already this
plugin's established unit of scope — a file-per-target-repo is the
existing pattern, not a new one.

Also considered YAML for the contract file (matches
`docs/handbooks/operations.md`'s prose-table style more closely).
Rejected: the issue text names the exact path with a `.json` extension
(`.on-the-record/test-tiers.json`), and JSON needs no new dependency in
target repos that may not carry a YAML parser — `json` is stdlib on both
sides (this plugin's Python and any target repo it clones).

## What will be done

- `gates/test_tier_contract.py`: `load_contract(repo_root)` reads
  `.on-the-record/test-tiers.json` from a target repo's root; returns
  `None` when absent OR malformed (fail-closed — a broken contract file
  is treated identically to no contract, never crashes verification).
  `parse_contract(raw_dict)` validates: `fast.command` (non-empty str,
  required), `fast.budget_seconds` (positive number, default 300),
  optional `slow.command` + `slow.trigger_change_classes` (list of
  path-glob strings). `select_tier(contract, changed_paths)` returns
  `"slow"` when any changed path matches a declared trigger glob, else
  `"fast"`. `no_contract_gap(repo_root, measured_seconds)` returns the
  gap record (repo, measured full-run cost, gap note) a verification
  role writes into its own record when no contract exists — this is the
  req-3 no-silent-full-run path.
- `tests/test_test_tier_contract.py`: the three acceptance tests named
  in the issue, verbatim function names.
- `on-the-record/hooks/test-tier-directive.sh` +
  `on-the-record/hooks/test_test_tier_directive.py`: a `UserPromptSubmit`
  directive mirroring `role-deviation-directive.sh`'s shape — states the
  tier-contract policy and the no-silent-full-run rule, observe-only
  (never refuses a tool call). Registered in `hooks.json`'s
  `UserPromptSubmit` array. Existence-checked by the paired test (req 4's
  acceptance bullet).
- `docs/handbooks/operations.md`: a new subsection next to the existing
  #1490 pre-merge tier table, pointing at the new file convention for
  target repos other than this one, and naming the no-contract gap path.
- `docs/specs/reconciled-index.md`: regenerated (`gates/spec_index.py
  --update`) since `operations.md` under `docs/handbooks/` changed.

## Out of scope

- Actually wiring `roles/execution-observation.json` /
  `roles/conformance-review.json` role prompts to call
  `load_contract()`/`select_tier()` at spawn time — req 2 asks for
  "verification-role consumption" at the phase-1 design level (this
  proposal's `## What will be done` gives them the module to consume);
  wiring the role JSON specs themselves is a role-spec change this
  proposal's write set does not cover and would need its own review
  under `role_spec_shape.py`'s gate.
- Gating (refusing an over-budget silent run) — explicitly deferred by
  req 4 until the convention has real adoption.
- #1493's own check-run artifact implementation — only the merge point is
  named, per req 5; #1493 is a separate issue's build.
- Any actual target repo (tokenmaxxxer or otherwise) adopting
  `.on-the-record/test-tiers.json` in its own checkout — this proposal
  ships the convention and its consumer-side module, not a specific
  target repo's opt-in.

## How you'll know it worked

`python3 -m pytest tests/test_test_tier_contract.py
on-the-record/hooks/test_test_tier_directive.py -v` passes all cases,
including the malformed-contract and no-contract fixtures; `hooks.json`
lists the new hook; `docs/specs/reconciled-index.md`'s `operations.md`
hash entry matches the updated file.
