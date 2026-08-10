---
status: proposed
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_pr_preflight.py
---

## Intent
Close issue #653: `pr-preflight.sh`'s pre-create `Closes #<n>` refusal
already exists but has two gaps that let a phase-2 PR body's missing trailer
slip through uncaught — no round-scoping (the #577 fix, applied to
`contract-guard.sh` only) and a body-file-read-before-write race — so the
omission surfaces later as a merge-time block instead of a pre-create
refusal.

## Constraints
- Zero-install, no GitHub Actions (issue's stated constraint).
- Must reuse #577's round-scoped phase-2 signal, not re-invent it.
- Auto-attach is ruled out: no hook in this deployment rewrites `Bash` tool
  input; see `docs/issue-653/reports/architecture/survey.md` and
  `docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
  for the full architecture rationale.

## Will do (phase 2, after approval)
1. Add round-scoping to `pr-preflight.sh`'s phase2 determination, anchored
   on the current branch's own first commit (no PR exists yet at create
   time, so no `commits` field to read as `contract-guard.sh` does).
2. Statically evaluate a `--body-file` path's same-command producer
   (`printf ... >`, `cat <<EOF >`) when the file does not yet exist at
   check time, instead of failing open.
3. Add/extend a fixture test covering: prior-round approval + new phase-1
   PR -> allow; same-round approval + delivering PR missing Closes via
   `--body-file` written in the same compound command -> deny naming the
   trailer.

## Out of scope
- Auto-attach / command rewriting.
- Any change to `contract-guard.sh`'s existing (already-correct) merge-time
  logic beyond factoring the shared round-scoping computation out.
- CI/Actions-based enforcement.

## How we'll know it worked
Fixture test (per issue's acceptance criteria) drives a phase-2 delivery PR
creation with a missing/absent Closes trailer via both `--body` and
`--body-file` forms and asserts pre-create denial naming the exact trailer;
a phase-1 proposal PR on a multi-round issue with a prior-round approval
asserts allow (no false phase-2).

## What did not work
(none yet — phase 2 not started)
