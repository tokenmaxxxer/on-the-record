---
subject: issue-1199
role: secure-coding
kind: record
loop_state: landed
---

# Record: secure-coding tool-landscape fold-in (issue-1199)

canonical: `gh issue view 1199 --json comments -q '.comments[] | select(.body=="APPROVE issue-1199/secure-coding")'`
run this session — a comment body exactly `APPROVE issue-1199/secure-coding`
was posted by `JiwonJung94` (listed in `docs/specs/approvers.md`), single-
account mode. Two such comments were found; both are exact-string matches,
no near-miss to flag.

## Verification level

L1. Both delivered rules target ASVS L1-scoped controls (component
vetting before use; input validated against a defined structure) per
`docs/issue-1199/proposals/2026-08-15-secure-coding-plugin-tool-landscape.md`
(commit `3fcf18517993ff0e6b727ada0a04fca8ea210590`, this repo). The two
requirement IDs carry their own verdict token in the ASVS checklist
section below.

## What was done

Executed the phase-2 fold-in unlocked by the APPROVE comment above.

Surveyed the Claude Code plugin/skill ecosystem for the secure-coding
domain (adoption-evidence method — canonical:
`docs/issue-1199/reports/secure-coding/scout-brief-plugins.md`, commit
`3fcf18517993ff0e6b727ada0a04fca8ea210590`, this repo): anthropics/
claude-code-security-review (`stargazers_count: 5861`), trailofbits/
skills (`stargazers_count: 6589`), ghostsecurity/skills
(`stargazers_count: 398`), snyk/claude-plugin-snyk (`stargazers_count:
0`, secondary confirmation only), all read via `curl -s
https://api.github.com/repos/<org>/<repo>` this session.

Delivered two native rule additions to `tokenmaxxxer/secure-coding-
rulebook`, branch `issue-1199/plugin-tool-landscape`, commit
`d35df23469c80e8553270e428f7cd21334afef67` (canonical: `git show
d35df23469c80e8553270e428f7cd21334afef67 --stat`, run this session —
2 files changed, 19 insertions), opened as
https://github.com/tokenmaxxxer/secure-coding-rulebook/pull/26
(canonical: `gh pr create` output this session, returned URL above).

1. **Pre-acceptance dependency health check** — `playbook/
   dependency-supply-chain-security.md` rule 9: before a new dependency
   is added, check its maintenance posture and known-vulnerability
   exploitability, rather than relying solely on the post-acceptance
   scan/patch ladder (rules 1-8). Traces to the scout brief's Snyk
   (pre-add health check) and ghostsecurity/skills (exploitability-
   first SCA triage) entries. Requirement ID: see checklist below.
2. **Diff/trust-boundary-scoped, false-positive-aware review
   discipline** — `playbook/input-validation-injection-defense.md`
   rule 10 (canonical: `git show
   d35df23469c80e8553270e428f7cd21334afef67 -- playbook/input-validation-injection-defense.md`,
   run this session): scope a security review pass to changed lines
   and the trust boundaries they cross, and triage out low-signal/
   non-reachable matches before they reach the finding list. Traces
   to the scout brief's anthropics/claude-code-security-review entry
   (diff-scoped PR review with false-positive filtering). Requirement
   ID: see checklist below.

No tool name, repo URL, or `source:` framing was added to either
rulebook rule body — both are phrased as this role's own native
judgment, matching the issue's 2026-08-13 native-application amendment;
provenance stays only in this record and the scout brief.

## ASVS checklist

Scope covered: the two playbook files targeted by this round
(`dependency-supply-chain-security.md`, `input-validation-injection-
defense.md`); no other playbook file was touched this round.

requirement_id: ASVS V14.2.1, level: L1
canonical: acceptance: git show d35df23469c80e8553270e428f7cd21334afef67 -- playbook/dependency-supply-chain-security.md — result: PASS (rule 9 present in the diff, run this session)
verdict: pass

requirement_id: ASVS V5.1.3, level: L1
canonical: acceptance: git show d35df23469c80e8553270e428f7cd21334afef67 -- playbook/input-validation-injection-defense.md — result: PASS (rule 10 present in the diff, run this session)
verdict: pass

## Findings

canonical: `git show d35df23469c80e8553270e428f7cd21334afef67 --stat`, run this session — diff adds only two playbook rules
N/A — none found (no code artifact was produced or reviewed this round).

## Why

Issue #1199 requires every role's rulebook to fold in learnings from
its domain's most-adopted Claude Code plugins/skills (2026-08-14
amendment), citing requirement northpole req#1 (specialist delegation
at real practitioner completeness). secure-coding had not yet been
surveyed under this issue.

## Upstream / basis

- `docs/issue-1199/reports/secure-coding/scout-brief-plugins.md`
  (commit `3fcf18517993ff0e6b727ada0a04fca8ea210590`, this repo)
- `docs/issue-1199/proposals/2026-08-15-secure-coding-plugin-tool-landscape.md`
  (commit `3fcf18517993ff0e6b727ada0a04fca8ea210590`, this repo)
- `d35df23469c80e8553270e428f7cd21334afef67` (secure-coding-rulebook)

## Open findings

None.

## loop_state

landed
