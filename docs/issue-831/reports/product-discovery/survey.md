---
subject: issue-831
kind: current-state-survey
---

# Current-state survey — issue #831

code_under_review:
- spawn.py
- docs/handbooks/setup.md
- docs/specs/northpole.md
- docs/issue-776/reports/execution-observation.md

## Background / context

canonical: `docs/issue-776/reports/execution-observation.md` rows #1, #5 and "Outcome verdict" (read this session)
PR #830 (merged) ran the #776 harness's representative-requirement scenario against a freshly instantiated fixture-target copy with no GitHub remote. The session correctly diagnosed the seeded defect and made two genuine `spawn.py implementation` delegation calls (the #823 spawn-allow hook worked, confirmed at that record's "What was done" step 4), but the second spawn hit `spawn.py`'s hard remote precondition and the session stopped, asking the human operator to either create a private GitHub repo or point it at an existing remote. That is a directly-observed, non-artifactual req#5 FAIL (`check_problems_not_pushed_back`) and a req#4 block (autonomous completion), scored on the actual transcript, not a simulated scenario.

canonical: `spawn.py:4314-4330` (read this session)
The enforcement point is `spawn.py::issue_workspace`, called once per role spawn to build an isolated clone. It reads the calling repo's `origin` URL via `git remote get-url origin`; if that returns empty, it calls `sys.exit(...)` with a Korean message citing "계약 v3 s10" ("target repo has no origin remote — the issue/PR model presupposes a GitHub remote"). There is no branch, flag, or fallback path in this function (or anywhere else in `spawn.py` searched this session) that lets a spawned role session continue without a remote — the hard-exit is unconditional. `_origin_pr_prefix` (`spawn.py:3001-3026`) separately tolerates a missing/erroring `origin` by returning `None` (used only for PR title prefixing), but that tolerance does not reach `issue_workspace`, which is the actual spawn-blocking gate.

canonical: `docs/handbooks/setup.md` (section "Once, per target repo," read this session)
The handbook already documents an intended resolution shape for exactly this gap: "Once, per target repo — and the orchestrator offers to do all of it in conversation when it finds a piece missing: 1. A GitHub remote (`gh repo create --private --source . --push` if local-only). 2. `docs/specs/approvers.md` ... 3. (Recommended) branch protection on main." This describes the orchestrator's own top-level conversation noticing the gap and offering to fix it, confirmed by the human, before any role spawn happens. What #830 observed is different in kind: the stall happened *inside a spawned role session* (the `implementation` role, mid-delegation), which has no human "in conversation" to offer anything to — by design (northpole req #4/#7), a spawned role session runs unattended. `setup.md`'s documented flow and `spawn.py`'s actual enforcement point are not wired to the same actor.

canonical: `docs/specs/northpole.md` sections 4, 5 (read this session)
Two requirements bound the fix directly: req #4 ("role sessions reach the goal with no human intervention") and req #5 ("a mid-course problem is solved by spawning the role-appropriate agent(s) ... not pushed back to the human"). Both are stated as behaviors of the *installed target session*, not the on-the-record maintainers' own repo.

canonical: `docs/handbooks/operations.md` (lines ~330-360, ~975-990, read this session)
The two-account safety model: approval is a GitHub act, gated by `docs/specs/approvers.md`. Single-account mode requires an exact-string issue comment (`APPROVE issue-<n>/<role>`) because a PR review Approve from the PR's own author is not possible on GitHub; two-account mode (a separate agent identity) allows a PR review Approve from a different approvers.md login. `docs/specs/northpole.md` and `docs/handbooks/setup.md` both describe this as optional hardening layered on top of a single-account default — the safety model does not itself require a second GitHub identity, only a second *account* if the operator opts in.

## Problem stated without any solution attached (JTBD tuple)

- **Job performer**: an operator who has installed the on-the-record plugin into a target repository and asked it, in conversation, to get a requirement done autonomously.
- **Job**: get from "I stated what I want" to "it's done, and I can see what happened and why" without being interrupted mid-flight by infrastructure setup questions that have nothing to do with the requirement itself.
- **Circumstance**: the target repository the operator pointed the plugin at has no GitHub remote configured yet (a fresh local repo, a just-`git init`'d project, or a repo whose remote was never set up) — a state the harness's own fixture-target instantiation reproduces and #830 shows a real spawned session hits mid-delegation, not just hypothetically.
- **Desired outcome**: the requirement gets delivered (or the session states plainly and without stopping that it degraded gracefully and why), with zero unresolved requests sitting in the operator's inbox waiting on a decision the session could have made safely on its own — while nothing invasive (an account-scoped, hard-to-reverse GitHub action) happens without the operator's prior, explicit consent.

canonical: `gh issue view 831` output, this session's first tool call ("Candidate directions to evaluate" list)
Gap: issue #831's own text already names three candidate *solutions* (self-provision, local-only mode, confirmed install-time setup) before restating the problem this way. The underlying customer-facing problem is narrower than any of the three: the operator does not want to be asked a question mid-delegation that could have been settled once, up front, at a moment the operator was already present for.

## Opportunity-solution tree placement

- **Outcome**: northpole req #4 + req #5 both hold for a target session in a no-remote repo (an installed-plugin session completes or gracefully degrades, with zero human-input stalls mid-run).
- **Opportunity**: "a target session with no GitHub remote currently has no way to proceed except stopping and asking a human mid-delegation" — the opportunity this survey substantiates with the #830 transcript and the `spawn.py:4328-4330` hard-exit.
- **Candidate solutions** (named in the issue, not yet chosen; canonical: `gh issue view 831` output, this session's first tool call): (a) self-provision via `gh repo create`, (b) local-only degraded mode on plain git, (c) one-time confirmed install-time setup. A fourth latent candidate this survey surfaces from `docs/handbooks/setup.md` (section "Once, per target repo," read this session): wiring that handbook's already-documented install-time-offer pattern to the actual `spawn.py:4328-4330` enforcement point, since (c) and that existing pattern largely coincide.
- **Discriminating assumption to test**: does a one-time, install-time, human-present consent gate (candidate c / the latent wiring candidate) fully retire the req#5 stall, or does the harness still find some no-remote configuration where a spawned role session reaches `issue_workspace` with no prior consent on record? The proposal below argues yes-fully-retires for the steady case and specifies the harness scenario that would falsify that.

## Scouting

Scout brief: `docs/issue-831/reports/product-discovery/scout-brief.md`. Ran (not skipped) — this is a live 3-candidate design decision with real tradeoffs (issue body itself asks for "candidate directions to evaluate, with tradeoffs and safety"), so neither skip condition (pure bugfix / spec leaves no design decision open) applies.
