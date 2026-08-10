---
proposal: docs/issue-577/proposals/2026-08-10-round-role-scoped-phase2.md
---

# Hunt record — round-role-scoped-phase2

## after-proposal — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — the proposed role-scoped prefix in contract-guard.sh directly contradicts gates/ci.py's `_approved_roles_on_issue`/`_phase_from_approval`, whose docstring (issue #312) explicitly makes phase an issue-level, role-agnostic property specifically to support cross-role handoff (architect proposes, implementation delivers, #304/#307). contract-guard.sh's own header comment claims "Phase is determined the same way gates/ci.py._approved_roles_on_issue does" — a claim the proposal's role-scoping breaks without updating or even mentioning that header sentence.
Kind: composition
Seed: docs/issue-577/proposals/2026-08-10-round-role-scoped-phase2.md (diff: `git diff HEAD~1 -- docs/issue-577/`)
cap_seconds: 120
tier: default
diff_stat_lines: 227
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:05:00Z

### Reproduce
Read gates/ci.py:180-219 (`_approved_roles_on_issue` / `_phase_from_approval`), whose docstring states verbatim (Korean): "phase 는 이슈의 속성이다(issue #312): 이슈에 달린 `APPROVE issue-<n>/<any role>` 코멘트가 하나라도 있으면(승인자 allowlist), 이 PR 이 어느 role 의 브랜치에서 왔든 phase2 — architect 가 제안하고 implementation 이 인도하는 cross-role 인계(#304/#307)가 그 예다." I.e. ci.py deliberately ignores the delivering PR's own role when scanning for `APPROVE issue-<n>/<role>` comments, by design, to support cross-role handoff.

Then run the two algorithms side by side on the same comment set (architect approved the issue, but the delivering PR's branch is `issue-577/implementation`, the documented cross-role-handoff shape) — script run as `python3 /tmp/.../repro.py`:

```python
issue = 577
approvers = {"alice"}
comments = [{"body": "APPROVE issue-577/architect", "author": {"login": "alice"}}]

prefix = "APPROVE issue-%d/" % issue          # gates/ci.py logic (role-agnostic)
roles = set()
for c in comments:
    b = c["body"].strip()
    if b.startswith(prefix) and c["author"]["login"] in approvers:
        role_token = b[len(prefix):]
        if role_token:
            roles.add(role_token)
ci_phase = "phase2" if roles else "phase1"

pr_role = "implementation"                     # proposal's role-scoped prefix, from headRefName
cg_prefix = "APPROVE issue-%d/%s" % (issue, pr_role)
cg_phase2 = any(c["body"].strip().startswith(cg_prefix) for c in comments)
cg_phase = "phase2" if cg_phase2 else "phase1"
print(ci_phase, cg_phase)
```

### Observed
```
phase2 phase1
```
For the exact cross-role-handoff scenario `_phase_from_approval`'s own docstring names as its reason to exist (#304/#307), `gates/ci.py` (the CI-time, authoritative gate) says phase2 — requiring a `Closes #577` in the delivering `implementation` PR's body — while the proposed contract-guard.sh (the pre-merge, zero-install gate) says phase1 and lets `gh pr merge` through with no `Closes` obligation checked at all. The two gates now silently disagree on the same PR: one says "must close", the other says "no requirement". Since contract-guard.sh runs pre-merge, its permissiveness is the one that actually reaches the user, cancelling ci.py's requirement rather than reinforcing it.

### Expected
The proposal should scope by (issue, round) without narrowing to the delivering PR's own role — or should explicitly reconcile with `_phase_from_approval`'s documented cross-role-handoff design and update contract-guard.sh's header claim ("the same way gates/ci.py._approved_roles_on_issue does") to state the two are now intentionally different, with a rationale for why the cross-role case is safe to treat as phase1 pre-merge while ci.py treats it as phase2 at CI time. The current "Rationale"/"Considered and rejected" sections never mention `_approved_roles_on_issue`'s role-agnostic design or the #304/#307 cross-role handoff at all, despite contract-guard.sh's own header sentence promising equivalence with it.
