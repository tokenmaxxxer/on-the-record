# Scout brief — issue-896 (role-activation evaluator + enforcement)

Stages used: 1 sweep (4 parallel WebSearch angles) + 0 deepening (saturation reached at judge point 1 — the four angles converged on the same must-be pattern; no build decision would change with another round). Mode: parallel (4 WebSearch calls, one turn).

## Category must-bes (Kano)
- **Condition evaluated against artifact state, not remembered by an operator.** OPA/Rego PR-check pattern and CODEOWNERS both compute "who/what is required" from the diff's file paths at review time, never from a human recalling a rule.
- **Gate is scoped to the paths/conditions actually touched**, not global — the Dependabot thread explicitly warns against blocking all merges on any outstanding alert; gates must fire only on the PRs whose diff matches the condition.
- **Escape is a controlled, reasoned exception, not a silent bypass.** Risk-acceptance/waiver practice frames exceptions as an explicit, attributable record (who accepted, why, scope) — never an unlogged skip.

## Performance axes the field competes on
1. **Precision of the trigger** (path/content match vs whole-repo blanket) — CODEOWNERS/required-reviewer-rule and OPA PR-checks both key off changed file paths, not issue/PR labels alone.
2. **Hard-block vs surfaced-only, chosen per severity/criticality** — risk-based deployment gating explicitly grades by exploitability/criticality rather than one blanket threshold; not every finding blocks.
3. **Exception durability** — waivers are treated as expiring, re-reviewed, not permanent; a stale N/A is itself a finding.

## One pattern to adopt, one to skip
- **Adopt**: path/content-keyed required-check, computed automatically per PR (CODEOWNERS/OPA pattern) — mirror this by keying board_condition evaluation off the branch's landed-file diff, not off issue text.
- **Skip**: forcing CI as the enforcement surface (branch-protection required status checks) — issue #896 explicitly requires plugin-only, no forced CI (req#7); the pattern's shape (compute-then-require) is adopted, its transport (GitHub required check) is not.

## Segment fit
This is dev-tooling/internal governance, not a consumer product — the comparison set is CI/policy-gate systems (OPA, CODEOWNERS, vulnerability-gating), not end-user apps. Fit is direct: same problem shape (trigger condition leads to required action leads to escape hatch), different transport (plugin/hook, not GitHub branch protection).

## Gap line
canonical: roles/specs/*.spec.json (43 files, use_when.board_condition field) and gates/role_spec_shape.py, read this session
The repo already has the machine-readable half of the must-be — `roles/specs/*.spec.json` carries `use_when.board_condition` on all 43 roles, and `gates/role_spec_shape.py` validates the field is a non-empty string — but has neither of the other two must-bes: nothing evaluates the condition against the diff (no "compute what's required" step), and nothing frames a skip as a controlled exception (no N/A/waiver record). Both gaps are what this proposal must fill.

## Sources
- [Pull Request Check Policies | Open Policy Agent](https://www.openpolicyagent.org/docs/cicd/pr-checks)
- [Required reviewer rule is now generally available - GitHub Changelog](https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/)
- [About code owners - GitHub Docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [How to Use DAST Results for Risk-Based Deployment Gating](https://www.invicti.com/blog/web-security/risk-based-deployment-gating-dast)
- [Dependabot auto-merge discussion, GitHub community #112234](https://github.com/orgs/community/discussions/112234)
