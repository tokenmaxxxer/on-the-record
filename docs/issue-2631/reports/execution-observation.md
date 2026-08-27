---
issue: 2631
role: execution-observation
author: execution-observation
verifies_subject: true  # independent re-verification of PR #2633's own deliverable
loop_state: complete
upstream:
  - path: gates/model_routing.py
    sha: cdd7e3a4178139c1cc1c61ca25826937c1a0458f
  - path: on-the-record/hooks/quality-bar-gate.sh
    sha: cdd7e3a4178139c1cc1c61ca25826937c1a0458f
  - path: docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md
    sha: 444b6906f6609e3f9e9b5cce0d8e74c5e4415d2d
---

# issue-2631 — execution-observation record

## What was done

Independently re-verified the two commits already landed on branch
`issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`
(PR #2633, open, `Closes #2631`) against issue #2631's Acceptance list,
using a fresh git worktree checkout of both the after-state
(`444b6906`) and the pre-change base (`origin/main` = `3567f44c`) rather
than trusting the builder's own record — see
`docs/issue-2631/reports/architecture-interface-contract-shape+model-routing-e54786b2.md`
(untracked on this branch; lives on branch
`issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`,
PR #2633, not yet merged to main) for the delivery this record verifies.

acceptance: `grep -n 'if role in' gates/model_routing.py` (after-state
worktree) — result:
```
(no output, exit 1)
```

acceptance: `grep -n 'BAR_ROLES' on-the-record/hooks/quality-bar-gate.sh`
(after-state worktree) — result:
```
(no output, exit 1)
```

acceptance: `diff` of `gates/model_routing.py` and `pipeline.py` between
the pre-change and after-state worktrees — result:
```
< def _role_tier(role: str, tiers: dict) -> str | None:
<     for tier_name, tier in tiers.items():
<         if role in (tier.get("roles") or []):
<             return tier_name
<     return None
< def route_model(role: str, single_phase: bool = False, ...):
---
> def route_model(single_phase: bool = False, ...):
--- pipeline.py ---
<         return model_routing.route_model(role, single_phase, design_bearing_verdict, policy)
---
>         return model_routing.route_model(single_phase, design_bearing_verdict, policy)
```
Confirms `_role_tier()` and the `if role in (tier.get("roles") or [])`
membership test are fully deleted, `route_model()`'s signature drops the
`role` parameter, and `pipeline.py`'s call site no longer forwards `role`
into it — matches the claimed diff.

acceptance: `route_model()` invoked directly on 7 subjects (4 from the
builder's set plus one I added, `security-review`, which was never in the
removed list, to independently probe an unaffected case) — before
(pre-change worktree, `route_model(role, single_phase, verdict, policy)`)
vs. after (after-state worktree, `route_model(single_phase, verdict,
policy)`) — result:
```
BEFORE role='ux-engineering'   single_phase=False verdict=None  -> ('sonnet', 'role-tier:judgment')
BEFORE role='brand-design'     single_phase=False verdict=None  -> ('sonnet', 'role-tier:judgment')
BEFORE role='content-design'   single_phase=True  verdict=None  -> ('sonnet', 'role-tier:judgment')
BEFORE role='architecture'     single_phase=False verdict=True  -> ('sonnet', 'design-bearing-override')
BEFORE role='api-design'       single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')
BEFORE role='random-role'      single_phase=True  verdict=None  -> ('sonnet', 'single-phase-tier:mechanical')
BEFORE role='security-review'  single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')

AFTER  role='ux-engineering'   single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')
AFTER  role='brand-design'     single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')
AFTER  role='content-design'   single_phase=True  verdict=None  -> ('sonnet', 'single-phase-tier:mechanical')
AFTER  role='architecture'     single_phase=False verdict=True  -> ('sonnet', 'design-bearing-override')
AFTER  role='api-design'       single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')
AFTER  role='random-role'      single_phase=True  verdict=None  -> ('sonnet', 'single-phase-tier:mechanical')
AFTER  role='security-review'  single_phase=False verdict=None  -> ('sonnet', 'default-tier:mid-design')
```
The **model** is identical before/after for all 7 subjects (still
`"sonnet"` throughout, per #2148's tier-model pin). The **rule**
attribution changes only for `ux-engineering`/`brand-design`
(`role-tier:judgment` → `default-tier:mid-design`) and `content-design`
(`role-tier:judgment` → `single-phase-tier:mechanical`); `architecture`,
`api-design`, `random-role`, and my added `security-review` are
unaffected in both model and rule. Confirms the builder's stated routing
change and confirms it holds for a subject outside the builder's own set.

acceptance: `bash -n on-the-record/hooks/quality-bar-gate.sh` (after-state
worktree) — result: `syntax OK` (exit 0).

derived: reconstructed the removed `BAR_ROLES` literal from the pre-change
worktree's source (7 names) and diffed the after-state's
`_TRIGGER_PATH_PATTERNS` dict against `{role:
_TRIGGER_PATH_PATTERNS.get(role) or [] for role in BAR_ROLES}` — result:
```
dict equal: True
```

acceptance: independently authored (not copied from the builder's record)
pass/refuse payloads run through `gates/quality_bar.py`'s unmodified
`bar_scoped_roles()`, before-patterns (`BAR_ROLES`-gated comprehension,
reconstructed) vs. after-patterns (`_TRIGGER_PATH_PATTERNS` directly) —
result:
```
PASS payload   ["package-lock.json", "README.md"]        scoped before/after: frozenset() frozenset() equal=True
REFUSE payload ["src/services/auth/login.py"]             scoped before/after: frozenset({'test-authoring','secure-coding'}) frozenset({'secure-coding','test-authoring'}) equal=True
```
Byte-identical scoping for both a payload that should pass (no domains
triggered) and one that should refuse (secure-coding + test-authoring
triggered), confirmed with payload shapes independent of the builder's own
examples.

derived: `python3 scripts/audit_removal_claim.py <claims.json> --root .`
run independently (my own claims JSON, same `removed_names`/
`member_samples`/`min_coloc` the builder used) against the after-state
worktree — result:
```
=== model_routing role-tier membership test ===
verdict: RESHAPE_DETECTED
q1 (name gone): live_hits=[] gone=true
q3 (still branches): branch_hits=[] still_branches=false
colocated_files: [('./gates/__pycache__/model_routing.cpython-310.pyc', 4), ('./gates/model_routing.py', 4), ('./pipeline.py', 2)]

=== quality-bar-gate BAR_ROLES literal ===
verdict: RESHAPE_DETECTED
q1 (name gone): live_hits=[] gone=true
q3 (still branches): branch_hits=[] still_branches=false
colocated_files: [('./on-the-record/hooks/quality-bar-gate.sh', 7)]
```
Matches the builder's reported q1/q3/colocated-files for both claims
(module-level and shell-hook prose narrating the removal, not a live data
structure — same reasoning as the builder's per-hit classification). My
run did not surface `.git/index`/pack-file hits the builder's did — an
environmental difference (a linked worktree's `.git` is a file, not a
directory holding the object store), not a discrepancy in the source
classification.

acceptance: `python3 -m pytest -q -m "not slow"` run independently on
both the pre-change and after-state worktrees — result:
```
pre-change: 16 failed, 475 passed in 5.21s
after:      16 failed, 475 passed in 5.21s
```
Same 16 failing test IDs in both runs (identical set —
`harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace`
and 15 others under `test/test_convention_equivalence.py`,
`test/test_local_dependency_env.py`,
`test/test_spawn_cross_family_skill_selection.py`,
`test/test_spawn_artifact_skill_pairing.py`,
`test/test_spawn_skill_judge_haiku_timeout_overlap.py`). No regression.

derived: `python3 gates/spec_index.py --update` run independently on both
worktrees to check the builder's deviation claim — result: identical
`FileNotFoundError: roles/specs/brand-design.spec.json` on both
pre-change and after-state, confirming the generator's dependency on
issue #2610's retired `roles/specs/*.spec.json` tree pre-dates this
change and is not something this delivery introduced or was obligated to
fix.

canonical: `docs/specs/enforcement-boundary.md` diff between worktrees —
the edited row accurately documents the `route_model()` signature change
(`role` parameter and the fixed-name-list tier-membership test it drove
are gone) without overclaiming a capability loss beyond what the routing
test above shows.

## Why

Contract v3 verify-at-landing requires executed acceptance evidence for a
delivered change. I reconstructed each Acceptance-list check from issue
#2631's own text using fresh git worktrees of the pre-change and
after-state commits, rather than re-running the builder's exact commands,
and where the check allowed it (routing subjects, quality-bar payloads)
chose inputs the builder had not already used, so agreement is
independent confirmation rather than recomputation of the same numbers.

canonical: issue #2631 Acceptance list (`gh issue view 2631`) — five
checks, each executed above under "What was done" with its own
`acceptance:`/`derived:` tag and pasted result.

## What did not work

None.

## Upstream basis

acceptance: `gh pr view 2633 --json body,commits,files`, then `git log
--oneline origin/main..origin/issue-2631/architecture-interface-contract-shape+model-routing-e54786b2`
— result: base `3567f44c` (current `origin/main`), two commits
`cdd7e3a4` (the code change) and `444b6906` (deviation log + priorities.md
capture), PR #2633 open with `Closes #2631` in its body.

## Open findings

None.

## Next steps

None — the five Acceptance-list checks were each independently executed
and matched in "What was done" above; no further verification work is
queued on this record.

acceptance: `printenv CORE_BUILD_NOW` — result:
```
1
```
Build-now single-phase delivery per contract v3 s19a — this record closes
in this same session, `loop_state: complete`.

other mounted skills: not triggered.
