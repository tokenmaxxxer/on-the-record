---
status: proposed
files:
  - docs/issue-831/reports/product-discovery/survey.md
  - docs/issue-831/reports/product-discovery/scout-brief.md
  - docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md
---

# Proposal — issue #831: no-remote graceful setup, not a mid-run stall

Phase-1 product-discovery deliverable. No code changes in this PR (issue #831 step 1 scope). Depends on: `docs/issue-831/reports/product-discovery/survey.md` (current-state survey, committed alongside this proposal, satisfying the survey-before-proposal order constraint).

## Intent

Decide which of three candidate directions (self-provision, local-only degraded mode, one-time confirmed install-time setup) should replace `spawn.py`'s current unconditional hard-exit on a missing `origin` remote (`spawn.py:4328-4330`), so that a target session never again reaches the #830-observed mid-delegation stall — and specify how the #776 harness should measure both the steady-state (remote present) and no-remote-graceful-degrade scenarios.

## Constraints (from the current-state survey)

- req #4 (autonomous completion, no human intervention mid-run) and req #5 (problems not pushed back to the human) both bind a *spawned role session*, which by design (northpole req #7) runs unattended — it has no human "in conversation" to ask.
  canonical: `docs/specs/northpole.md` sections 4, 5, 7 (read in survey)
- The two-account safety model (`docs/specs/approvers.md`, single- vs two-account approval) is orthogonal to remote *existence* — it governs who can approve a PR once one exists, not whether a remote gets created in the first place.
  canonical: `docs/handbooks/operations.md` (read in survey)
- `docs/handbooks/setup.md` already documents "the orchestrator offers to [create a GitHub remote] in conversation" as one of three per-target-repo setup items, alongside `approvers.md` and branch protection — but this offer is not wired to `spawn.py`'s actual enforcement point (`issue_workspace`), and the offer as documented presumes a human is present in the orchestrator's top-level conversation, which is true at install/setup time but not true inside a spawned role session.
  canonical: `docs/handbooks/setup.md`, `spawn.py:4314-4330` (read in survey)

## Candidate evaluation (RICE)

Reach = fraction of no-remote target-repo instantiations the fix actually covers. Impact = req#4/#5 severity if unaddressed (both currently FAIL/blocked per #830, so headroom is large for any candidate that closes the gap). Confidence = how well-grounded the estimate is in this session's own reading of the code (not user interviews — none available for an internal orchestration contract; scored on code/spec grounding instead, flagged accordingly). Effort = rough build size.

| Candidate | Reach | Impact | Confidence | Effort | RICE (R×I×C/E, 1-5 scale each, E as divisor) | Safety verdict |
|---|---|---|---|---|---|---|
| (a) Self-provision (`gh repo create` inside `issue_workspace`, no prior consent) | 5 (covers every no-remote case automatically) | 5 | 2 (confidence low — this is exactly the shape the scout brief's GitLost citation warns against: an account-scoped, irreversible action taken by an unattended session with no consent boundary) | 2 (small code change, but the safety argument itself is weak) | 12.5 | **Rejected as default-on.** Creating a repo under the operator's GitHub account with no consent is the kind of invasive/irreversible action the issue text itself flags as needing scrutiny; doing it from inside an *unattended* spawned session (no human "in conversation" to stop it) is worse than the self-provision candidates the scout brief's field sweep found acceptable (which all gate on a prior consent step). |
| (b) Local-only degraded mode (plain git, no GitHub) | 3 (covers no-remote cases, but the issue/PR model — approvals, board records, PR merge as human decision — has no local-git equivalent) | 3 (unblocks req#4/#5 for delegation itself, but silently breaks the *approval* half of the safety model, which is GitHub-native: `docs/handbooks/operations.md`'s two-account model has no meaning without a remote to hold PRs and reviews) | 3 | 1 (largest: needs a parallel local-record/approval path, a new architecture, per the issue's own framing as "a larger architectural change") | 9 | **Rejected for now, not ruled out long-term.** It would require redesigning the approval/merge half of the safety model (contract v3 s19's phase-2-on-Approve gate is defined in terms of a GitHub PR review or issue comment) — out of proportion to this issue's scope, and it weakens rather than strengthens the requirement that human approval remains a GitHub act. |
| (c) One-time confirmed install-time setup | 4 (covers the steady-state case fully; does not by itself cover a repo whose remote disappears *between* install and a later spawn — see harness scenario below) | 5 | 4 (grounded directly in `docs/handbooks/setup.md`'s existing documented pattern for the other two setup items, not invented from scratch) | 4 (small: wire the existing documented offer to the actual `spawn.py` gate, plus a recorded consent artifact `issue_workspace` can check before it would otherwise hard-exit) | 5.0 | **Recommended.** See safety argument below. |

ICE fallback not used — reach is estimable from the harness's own fixture-instantiation shape (every no-remote repo hits the same `issue_workspace` code path), not from unavailable user-interview data.

## Recommendation: (c), one-time confirmed install-time setup — wired to the actual enforcement point

**Mechanism** (direction, not implementation — step 2/architecture owns the actual design): at install/setup time, when a human operator IS present in the top-level orchestrator conversation (matching `docs/handbooks/setup.md`'s existing "offers to do all of it in conversation" pattern for `approvers.md` and branch protection), the orchestrator offers to run `gh repo create --private --source . --push` or accept a pointed-at existing remote, exactly as `setup.md` already documents — and, on confirmation, writes a durable, checkable record of that consent (e.g. the resulting `origin` remote itself is the record; no new state file needed beyond what `git remote -v` already shows). `spawn.py::issue_workspace`'s existing check ("does `origin` resolve?") is *already* the right check for whether setup happened — the gap is only that when it does NOT resolve, the current behavior is an unconditional `sys.exit` reached by an unattended role session, instead of that gap being caught and resolved earlier, at the orchestrator's own top-level conversation, before any role spawn is attempted.

**Safety argument (req#4/#5, invasive-action consent):**
- The only account-scoped, hard-to-reverse action (creating a GitHub repository) happens at exactly one moment: install/target-repo setup, in the orchestrator's own top-level conversation — the one moment a human operator is provably present (they just typed the setup command). This matches the scout brief's field finding that responsible 2026 agentic tools ask before anything destructive, and avoids the GitLost-class failure mode of an account-scoped action reachable without a hard consent gate.
  canonical: `docs/issue-831/reports/product-discovery/scout-brief.md` (this session's scout pass)
- After that one confirmation, no later moment — including every subsequent role spawn, and specifically the unattended mid-delegation moment #830 observed — ever needs to ask again, because `spawn.py`'s existing `git remote get-url origin` check already answers "has setup happened" without needing a new consent artifact to go stale or drift from reality.
- req#4/#5 hold because a spawned role session, once setup has happened, never reaches a state where `origin` is empty and it has no path forward — the precondition `spawn.py:4328` currently exits on becomes unreachable in steady state, not papered over with a silent auto-provision the operator never agreed to.
- Nothing invasive happens without consent: candidate (a) is explicitly rejected above for exactly this reason.

## Harness measurement (#776)

Both scenarios below extend `harness.driver` fixture instantiation (currently: no remote ever seeded, per survey's citation of `instantiate_fixture_target`); step 2/3 implement, this proposal specifies the scenario shape only.

1. **Steady-state (remote present) scenario**: `instantiate_fixture_target` seeds a real or mocked GitHub origin (a throwaway `gh repo create` under a harness-controlled test account, or a local bare-repo stand-in served over a URL `spawn.py`'s `git remote get-url origin` treats identically) *before* the representative-requirement session launches — simulating a target repo that already completed the one-time setup this proposal recommends. Assertion: the run reaches the same delegation depth #830 reached (two `spawn.py implementation` calls) and continues past it to a completed `final_report`, with `human_input_stalls` empty (req#1/#4/#5 all measurable, not UNMEASURED, per `harness/signals.py`'s own empty-state branches cited in the #830 record).
2. **No-remote graceful-degrade scenario**: `instantiate_fixture_target` seeds NO remote (today's existing behavior), but the launched session is the *orchestrator's own top-level conversation* (not a bare role spawn) — i.e. the scenario that actually exercises the setup-time offer this proposal specifies, rather than jumping straight to a role spawn the way the #830 fixture did. Assertion: the transcript shows the setup offer being made and (harness-scripted) confirmed, `origin` resolves afterward, and the subsequent delegation proceeds with zero `human_input_stalls` at the `issue_workspace` gate specifically — distinguishing "asked once, at setup, and proceeded" (PASS) from "stalled mid-delegation with no remote" (today's #830 FAIL) and from "silently auto-provisioned with no confirmation event in the transcript" (a new FAIL condition the harness must add, since that would be candidate (a) sneaking back in).

Both scenarios reuse `harness/signals.py`'s existing `check_problems_not_pushed_back` and `check_orchestration_to_completion` unmodified — only `instantiate_fixture_target` and the launch harness (which actor gets the first prompt: orchestrator vs. bare role) need new scenario variants, per the survey's finding that #830's stall happened at the wrong actor's boundary.

## Out of scope

- Actual implementation of the setup-time consent wiring in `spawn.py` (step 2, architecture + implementation).
- Redesigning the approval/merge model for local-only mode (candidate b) — explicitly deferred, not silently dropped.
- Deciding whether a machine agent account (`MUSTER_AGENT_GH_TOKEN`) changes any of this — out of this issue's scope per the survey; the two-account model is orthogonal to remote existence (see Constraints).

## How you'll know it worked

The #776 harness's two new scenarios (above) both reach measurable (non-UNMEASURED) verdicts on req#1/#4/#5, with the steady-state scenario PASSing and the no-remote scenario PASSing via a recorded, confirmed setup event rather than either a stall or a silent auto-provision.
