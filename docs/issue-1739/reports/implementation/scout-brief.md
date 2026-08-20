# issue-1739 scout brief (phase 1)

Mode: batched-sequential fallback (two WebSearch calls issued in one
message, i.e. actually concurrent dispatch — not a serialized loop).
One sweep stage only; the two angles converged on the same must-bes at
judge point 1, so no deepening round was run.

Angles swept: (1) Renovate/Dependabot automerge scoping by update-risk
class, (2) Mergify/Kodiak policy-engine auto-merge conditions.

## Category must-bes (Kano)

- Auto-merge/auto-approve is gated on an explicit allow-list of
  low-risk classes (update type, package pattern), never a blanket
  "everything green" rule.
- All required checks/conditions are required to succeed before the
  automated path fires — the automation composes existing CI/status
  gates, it does not replace them.
- A visible audit signal (label, PR comment, log) marks what was
  auto-handled, distinct from human-approved work.

## Performance axes the strong exemplars compete on

1. **Scoping granularity** — Renovate's packageRules let automerge be
   scoped by update type x package pattern x release-age delay, not
   just a single on/off switch.
2. **Staged rollout / friction knobs** — both tools default to some
   friction (minimum release age, reviewer requirement) rather than
   immediate automerge, and expect operators to tighten before trusting
   the default.
3. **Composability with existing gates** — Mergify's auto_merge setting
   only fires when a merge-protection ruleset's success conditions are
   already satisfied; it carries no independent logic of its own for
   judging code correctness.

## Adopt / skip

- Adopt: risk-class allow-list plus composition over already-existing
  deterministic gates (axis 3) — this matches Requirement 1's whitelist
  approach and Requirement 3's "fires only when deterministic gates
  succeed" directly.
- Adopt: staged-rollout friction (axis 2) — Requirement 6's shadow-mode
  window before bypass activation is the same pattern as
  minimumReleaseAge / reviewer-requirement defaults: don't trust the
  automation immediately, observe first.
- Skip: per-package-pattern scoping granularity (axis 1) — this issue's
  class definition is diff-shape-based (docs-only, test-only), not
  dependency-package-based, so Renovate's packageRules concept doesn't
  transfer; noted only so the classifier design doesn't overfit to a
  package-manager mental model.

## Segment fit

on-the-record's PRs are role-authored code/doc changes on a private
mono-branch-per-issue workflow, not third-party dependency bumps on a
public OSS repo — the exemplars' trust model (bot-authored PR from a
known, narrow diff generator) matches this issue's target (a role
session's own mechanical, narrow-scope PR) more closely than it matches
a general "any contributor's PR" automerge policy. That similarity is
why the "risk-class allow-list + composability" must-bes were adopted
and the "package-pattern scoping" axis was skipped.

## Gap line

Present in current state: three deterministic gates already exist
(scope_adherence.py, stale_revert_guard.py, requirement_met.py) that
the classifier can compose over, matching axis 3 (composability)
without new gate logic.
derived:
```
$ ls gates | grep -iE "scope_adherence|stale_revert|requirement_met"
requirement_met.py
scope_adherence.py
stale_revert_guard.py
test_requirement_met.py
test_scope_adherence.py
```
Missing from current state: no risk-class allow-list classifier exists
yet (axis 1's transferable half — diff-shape classing, not package
classing), no audit-log/label distinguishing auto-handled work (the
category must-be), and no staged-rollout/shadow mechanism (axis 2) —
all three are what Requirements 1, 5, and 6 ask this issue to build.

Sources:
- [Renovate and Dependabot Security Configuration: Auto-Merge Boundaries and Scope Rules](https://www.systemshardening.com/articles/cicd/renovate-dependabot-security/)
- [Dependabot vs Renovate 2026: Pick One for Your Stack](https://appsecsanta.com/sca-tools/dependabot-vs-renovate)
- [GitHub Auto-Merge: When the Native Button Is Enough, and When You Outgrow It | Mergify](https://mergify.com/blog/github-auto-merge-when-native-is-enough)
- [The Origin Story of Merge Queues | Mergify](https://mergify.com/blog/the-origin-story-of-merge-queues)
