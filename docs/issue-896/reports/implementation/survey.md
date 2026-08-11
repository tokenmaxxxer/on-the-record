# Survey — issue-896 implementation (step 2, invariant-first reframe)

## Scope
Implements the operator's REFRAME comment on #896 (invariant-first, not
spawn-when): (1) a standing, always-on test-authoring invariant gate, and
(2) the roles-due evaluator for judgment residue only.
canonical: gh issue view 896 --comments (REFRAME comment body, read this session)

## Existing always-on gate pattern to mirror
canonical: on-the-record/hooks/pr-preflight.sh:1-27, on-the-record/hooks/deliverable-guard.sh:1-30
- PreToolUse Bash matcher, regex on tool_input.command, deny-only,
  fail-open on parse ambiguity, positive exit 2 only on a proven match.
- Registered in on-the-record/hooks/hooks.json under PreToolUse.

## Checkpoint for the invariant
canonical: gates/gates.py:168-175 (changed_files), spawn.py:1416-1426 (_base)
Per-edit PreToolUse is too early (code and its test often land in separate
tool calls within one commit). git commit is already the interception
point pr-preflight.sh and contract-guard.sh use for the same Bash matcher.
A new hook intercepts git commit, reads the staged diff
(git diff --cached --name-only --diff-filter=ACM), classifies paths as
code/test/doc/config, and denies when a code path changed with no test
path changed in the same staged set, unless the commit message carries an
explicit N/A trailer.

## roles-due evaluator inputs
canonical: spawn.py:1351-1372 (board), roles/security-threat-model.json:16, roles/accessibility.json:16, roles/product-discovery.json:16, roles/interaction-design.json:15, roles/defect-verification.json:16, roles/execution-observation.json:16, roles/conformance-review.json:17
board(root) already maps subject -> role -> frontmatter for "does a record
exist". Seven roles already carry a parenthetical board_condition in their
Korean use_when text, precise enough to decompose into a structured
trigger without inventing new categories: security-threat-model,
accessibility, product-discovery, interaction-design,
defect-verification, execution-observation, conformance-review.
test-authoring is excluded from this evaluator's roster on purpose — its
bar is now the standing invariant above, not judgment residue.
Full 43-role trigger coverage stays out of scope (matches the phase-1
proposal's own Out of scope); a role spec with no trigger key is never
reported due.

## Write set
on-the-record/hooks/test-authoring-invariant-guard.sh (new),
on-the-record/hooks/test_test_authoring_invariant_guard.py (new),
on-the-record/hooks/hooks.json (register), gates/roles_due.py (new),
gates/test_roles_due.py (new), roles/specs/*.spec.json for the seven roles
above (add trigger), spawn.py (add roles-due subcommand),
docs/issue-896/proposals/2026-08-12-step2-invariant-and-evaluator.md
(this phase's proposal), docs/issue-896/reports/implementation.md (this
record).
