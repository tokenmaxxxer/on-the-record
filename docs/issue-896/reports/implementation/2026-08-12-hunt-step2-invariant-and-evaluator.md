---
proposal: docs/issue-896/proposals/2026-08-12-step2-invariant-and-evaluator.md
---

# Hunt record — step2-invariant-and-evaluator

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the proposal's frontmatter `files:` list never names `docs/specs/enforcement-boundary.md` or `docs/specs/generated-paths.md`, yet landing the new hook (`test-authoring-invariant-guard.sh`) and new module (`gates/roles_due.py`) without touching them is exactly what this repo's own `gate-registration-guard.sh` denies at commit time.
Kind: design-error
Seed: docs/issue-896/proposals/2026-08-12-step2-invariant-and-evaluator.md frontmatter `files:` block vs `git show --stat HEAD`
cap_seconds: 120
tier: default
diff_stat_lines: 867 insertions(+), 5 deletions(-) across 14 files
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:20:00Z

### Reproduce
```
git worktree add /tmp/repro HEAD~1 -q
cd /tmp/repro
# stage exactly the proposal's frontmatter files: list (14 paths), taken
# from HEAD (1242f05), deliberately omitting docs/specs/enforcement-boundary.md
# and docs/specs/generated-paths.md since neither is in that list:
for f in on-the-record/hooks/test-authoring-invariant-guard.sh \
         on-the-record/hooks/test_test_authoring_invariant_guard.py \
         on-the-record/hooks/hooks.json gates/roles_due.py gates/test_roles_due.py \
         roles/specs/security-threat-model.spec.json roles/specs/accessibility.spec.json \
         roles/specs/interaction-design.spec.json roles/specs/execution-observation.spec.json \
         roles/specs/conformance-review.spec.json spawn.py \
         docs/issue-896/reports/implementation.md; do
  git show 1242f05:"$f" > "$f" && git add "$f"
done
payload='{"tool_name":"Bash","tool_input":{"command":"git commit -m \"add invariant guard\""}}'
echo "$payload" | on-the-record/hooks/gate-registration-guard.sh
```

### Observed
```
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/roles_due.py: no row in docs/specs/enforcement-boundary.md
on-the-record/hooks/test-authoring-invariant-guard.sh: no row in docs/specs/enforcement-boundary.md
on-the-record/hooks/test-authoring-invariant-guard.sh: no row in docs/specs/generated-paths.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
```
exit=2 — the commit the proposal's own write set describes cannot land as written; the actual HEAD commit only succeeds because it silently also touched two files the frozen proposal never listed as in scope.

### Expected
The proposal's `files:` frontmatter (the write set an approver/reviewer checks against) should have named `docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md` up front, since adding any new `gates/*.py` module or `on-the-record/hooks/*.sh` file structurally requires touching both (enforced by this same repo's `gate-registration-guard.sh`) — this is a repeatable, mechanically-derivable omission, not a one-off oversight.
