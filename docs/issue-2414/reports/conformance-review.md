---
issue: 2414
role: conformance-review
author: conformance-review
loop_state: terminal
upstream:
  - path: docs/issue-2414/reports/implementation.md
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
  - path: gates/acceptance_gate.py
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
  - path: gates/requirement_met.py
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
  - path: on-the-record/directive/acceptance-format.md
    sha: 2019bf3be0f0404e6b05e753eba5f1991bb54c34
subject: PR #2422 (branch issue-2414/implementation, head 2019bf3b)
test: builder-blind conformance review against issue #2414's own six `## Acceptance` checks, plus independent re-derivation of the PR's 12.5% frequency figure and 76%/31% backlog-impact figures
result: failed
assertedBy: conformance-review
---

# issue-2414 — conformance-review record

canonical: `docs/issue-2414/reports/implementation.md` (untracked on `main`
— PR #2422's own branch, not yet landed) is not readable from this
checkout. It was read this session from PR #2422's branch instead: `git
fetch origin pull/2422/head:pr-2422-review && git worktree add
/tmp/pr2422-wt pr-2422-review` (HEAD `2019bf3be0f0404e6b05e753eba5f1991bb54c34`),
and from `gh pr diff 2422`. Every reference to that record below refers to
the PR #2422 branch, not to this checkout's `main`.

## What was done

Builder-blind review of PR #2422 against issue #2414's own six `## Acceptance`
checks (not the PR's self-description). For each check: located the evidence
the builder cited, then independently re-executed it against the live
repository rather than trusting the citation — re-read #2291/#2383/#2393's
live issue bodies, checked out the PR branch into a worktree, ran both
shipped test suites, and re-ran the frequency and backlog-impact
measurements against current repository state (open issues, merged-PR list)
using the PR's own shipped `gates/acceptance_gate.py`/`gates/requirement_met.py`
code, imported and called directly (not re-typed).

## Why

canonical: this session's own live re-execution, cited per-requirement
below. Verify-at-landing (issue #2137) requires the review to re-execute
evidence, not read the builder's transcription of it — this PR's own
central claim is "measured, not asserted," so re-measuring rather than
re-reading was the only way to actually check that claim. The open-issue
backlog is small enough to enumerate in full rather than sample (exact
counts and the sweep re-run are in the check-5/Incorrect-finding blocks
below), so both backlog-impact percentages were fully re-derived rather
than spot-checked. The frequency measurement's PR-classification step is a
judgment call the builder's own record discloses as such over a corpus too
large to re-read PR-by-PR inside this review's scope; that piece is checked
by an exact-count reproduction plus a plausibility check against a wider
mechanical superset (see the check-2 finding below), with the residual gap
stated in Open findings rather than treated as independently re-derived.

## Upstream basis

- The builder's implementation record (PR #2422 branch, sha `2019bf3b`,
  untracked on `main`) — canonical: read via `gh pr diff 2422` and the
  worktree checkout named above.
- `gates/acceptance_gate.py`, `gates/requirement_met.py`,
  `on-the-record/directive/acceptance-format.md` (same sha) — the shipped
  code and doc, read and executed directly out of the PR #2422 worktree
  (`/tmp/pr2422-wt`), not trusted from the PR's prose description.
- Issue #2414 (this issue), #2415, #2291, #2383, #2389, #2393, #2400, #2411,
  #2413 — read live this session via `gh issue view <n>` / `gh pr view <n>`.

## Requirement findings

---
requirement: "read #2291, #2389 and #2400's original `## Acceptance` sections and confirm (or refute, with citations) that A and B are the two distinct shapes — the record states the verdict either way"
spec_ref: "issue #2414 body, `## Acceptance` check 1"
verdict: Present
evidence: "the builder's implementation record `## Measurements` section 1 (PR #2422 branch); independently re-run this session: `gh issue view 2291 --json body -q .body`, `gh issue view 2383 --json body -q .body`, `gh issue view 2393 --json body -q .body`, `gh pr view 2389 --json body -q .body`, `gh pr view 2400 --json body -q .body`"
rationale: "canonical: `gh pr view 2389`/`gh pr view 2400` output read this session shows both carry `## Summary`/`## Test plan`, no `## Acceptance` section — #2389 and #2400 are PR numbers, not issue numbers. The PR under review substitutes the issues those two PRs actually closed (#2383, #2393, per `gh pr view 2389 --json body -q .body` containing 'Closes #2383' and `gh pr view 2400 --json body -q .body` containing 'Closes #2393'), each of which does carry a real `## Acceptance` section — this resolves issue #2414's own citation error rather than compounding it. Read live this session: #2291's Acceptance names only what the trace must record, never what it must not (matches #2393's own finding, canonical: `gh issue view 2393 --json body -q .body`); #2383's Acceptance names only pruning by age, never what must survive (matches #2411's bug, canonical: `gh issue view 2411 --json body -q .body`); #2393's Acceptance requires only the one-time cleanup, never the ongoing policy's reach (matches #2413, canonical: `gh issue view 2413 --json body -q .body`). The builder record states the A/B verdict explicitly with citations, satisfying the check."
---

---
requirement: "measure how often landed mechanism-adding work produced a same-shape follow-up defect, across a stated window of closed issues — the number and window are in the record, and the record states whether it justifies a new gate"
spec_ref: "issue #2414 body, `## Acceptance` check 2"
verdict: Present
evidence: "the builder's implementation record `## Measurements` section 2 (PR #2422 branch); independently re-run this session"
rationale: |
  Re-ran the window+total count live this session:
  ```
  $ gh pr list --state merged --limit 300 --json number,title,mergedAt > /tmp/merged_prs.json
  $ python3 -c "
  import json
  d = json.load(open('/tmp/merged_prs.json'))
  w = [p for p in d if p['mergedAt'] and '2026-08-25T00:00:00Z' <= p['mergedAt'] <= '2026-08-25T11:51:03Z']
  print(len(w))
  "
  116
  ```
  derived: matches the record's stated window count exactly.

  Numerator cross-checked live: canonical: `gh issue view 2393 --json body -q .body` cites PR #2366 (#2291's mechanism) as the trace it flags; canonical: `gh issue view 2411 --json body -q .body` states "Follow-up to #2383 / PR #2389 (already merged as `cea0f583`)"; canonical: `gh issue view 2413 --json body -q .body` states "landed by PR #2400 for #2393" — all three defect-to-mechanism-PR chains real and correctly attributed.

  Denominator ("mechanism-adding delivery PRs") rests on a judgment call
  the record itself discloses ("provenance: read, a judgment call ... not a
  mechanical regex"). This review does not have budget to re-read all 116
  PR bodies to reproduce that count to the exact digit. A mechanical
  title-only filter this session (excluding conformance-review/
  execution-observation/re-review/CHANGES-round titles) gives:
  ```
  $ python3 -c "
  import json, re
  d = json.load(open('/tmp/merged_prs.json'))
  w = [p for p in d if p['mergedAt'] and '2026-08-25T00:00:00Z' <= p['mergedAt'] <= '2026-08-25T11:51:03Z']
  pat = re.compile(r'conformance.review|execution-observation|re-review|CHANGES-round', re.I)
  print(len([p for p in w if not pat.search(p['title'])]))
  "
  38
  ```
  derived: 38 is a superset consistent with the record's stated 24 after
  excluding further non-mechanism deliveries the record's own worked
  example already demonstrates it does (e.g. PR #2273 "remove
  poll-heartbeat.sh's bash 3.2 heredoc landmine" is named in the record as
  explicitly excluded for adding no write/delete/refuse/report surface;
  several of the 38 — #2369 a pure Extract-Class refactor, #2323/#2307/
  #2246/#2243 pure bugfixes, #2252 a staged proposal with no shipped code —
  are plausibly excluded on the identical basis). The record's own 3/24 =
  12.5% arithmetic is correct given its stated 24; the 24 itself is
  plausible but not exactly re-derived digit-for-digit by this review.

  Verdict: the record states the frequency (12.5%, ~12h window) and its
  own justification explicitly — canonical: the builder's implementation
  record `## Measurements` section 2 (PR #2422 branch), "12.5% in one
  dense session justifies a bounded, low-cost intervention ... not a
  heavyweight new process" — satisfying the check's letter; the
  denominator's exact precision is the one open caveat, noted in Open
  findings below rather than silently accepted.
---

---
requirement: "if A is judged worth addressing — a mechanism-adding issue is refused at authoring time unless it names what the mechanism must not do; enforced at the same point as `empty state:`/`provenance:`; demonstrated live: an issue missing it is refused, one with it spawns normally"
spec_ref: "issue #2414 body, `## Acceptance` check 3"
verdict: Present
evidence: "gates/acceptance_gate.py:82-96 (`_MECHANISM_TRIGGER`/`_MUST_NOT`), :149-166 (wiring into `check_issue_body`, same function as the existing empty-state/provenance checks) — PR #2422 branch sha `2019bf3b`"
rationale: |
  canonical: re-ran both shipped regression tests this session against the
  PR #2422 worktree:
  ```
  $ python3 gates/test_acceptance_gate.py 2>&1 | grep issue_2414
  ok - t_issue_2414_mechanism_adding_missing_must_not_blocks
  ok - t_issue_2414_mechanism_adding_with_must_not_spawns_normally
  ok - t_issue_2414_mechanism_trigger_catches_past_tense_and_passive_voice
  ok - t_issue_2414_non_mechanism_issue_escapes_with_not_applicable
  27/27 passed
  ```
  Independently reproduced the live-demonstration claim directly against
  the three real, unmodified original issue bodies, fetched fresh this
  session (not the record's pasted output):
  ```
  $ python3 -c "
  import sys, json, subprocess
  sys.path.insert(0, 'gates')
  import acceptance_gate as ag
  for n in [2291, 2383, 2393]:
      body = json.loads(subprocess.run(['gh','issue','view',str(n),'--json','body'],capture_output=True,text=True).stdout)['body']
      bad = ag.check_issue_body(n, body)
      print(n, 'violations=', len(bad), 'trigger=', ag._MECHANISM_TRIGGER.findall(body)[:3])
  "
  2291 violations= 1 trigger= ['append', 'append']
  2383 violations= 1 trigger= ['pruned', 'prune', 'pruned']
  2393 violations= 1 trigger= ['pruned', 'rotated', 'pruning']
  ```
  derived: all three real unmodified issue bodies are refused (1 violation
  each), matching the builder's own `verify_real_cases.py` output verbatim.
  The field is existence-only and gated inside `check_issue_body`, the
  identical function `empty state:`/`provenance:` are checked in (same
  enforcement point, confirmed by reading gates/acceptance_gate.py:149-166
  directly). Both the refuse-when-missing and spawn-when-present
  demonstrations exist as regression tests above and both are green.
---

---
requirement: "if B is judged worth addressing — the landing path requires executed evidence the mechanism reached its target population (before/after counts), not merely that it ran; demonstrated against a real case"
spec_ref: "issue #2414 body, `## Acceptance` check 4"
verdict: Present
evidence: "gates/requirement_met.py:91-111 (`_POPULATION_LINE`/`_BEFORE_AFTER_EVIDENCE`), :146-155 (`_population_map`), :212-228 (`_convergence_evidence_missing`), :388-471 (wiring into `grade()`) — PR #2422 branch sha `2019bf3b`"
rationale: |
  canonical: re-ran the shipped regression suite this session against the
  PR #2422 worktree:
  ```
  $ python3 gates/test_requirement_met.py 2>&1 | grep issue_2414
  ok  t_issue_2414_population_declared_with_before_after_passes
  ok  t_issue_2414_population_declared_without_before_after_blocks
  ok  t_issue_2414_population_not_declared_is_unaffected
  ok  t_issue_2414_real_case_2413_gap_would_have_blocked
  35/35 passed
  ```
  Opt-in (`population:` metadata line), existence-only (a before/after
  numeric pair somewhere in the PR diff's added lines, not verified for
  truth), and blocks specifically when `provenance: executed-live` is also
  claimed — confirmed by reading requirement_met.py:212-228 directly. The
  "demonstrated against a real case" clause is satisfied twice as green
  regression tests above, not prose narration alone: against PR #2400's
  real merged diff (`t_issue_2414_real_case_2413_gap_would_have_blocked`
  uses the exact criterion #2413 says #2393 should have had) and against a
  correctly-accepted declared-with-evidence case.
---

---
requirement: "whatever is added does not lengthen the normal authoring or landing path for issues that add no mechanism — measured, not asserted"
spec_ref: "issue #2414 body, `## Acceptance` check 5"
verdict: Present
evidence: "gates/acceptance_gate.py:149 (`if _MECHANISM_TRIGGER.search(body) and ...`), gates/requirement_met.py:216 (`if not population or provenance != \"executed-live\": return False`) — PR #2422 branch sha `2019bf3b`"
rationale: |
  Both new fields are gated by an explicit conditional checked before any
  new requirement is imposed (confirmed by direct inspection: the new
  `if`-branch's body never evaluates unless the trigger/opt-in condition is
  true, so an issue/check that doesn't trip it produces byte-identical
  output with or without the new code present). Independently re-ran the
  conditional's actual firing rate against the live open backlog this
  session:
  ```
  $ gh issue list --state open --limit 200 --json number,body > /tmp/open_issues.json
  $ python3 -c "..." # sweep narrow-trigger marginal count against gates/acceptance_gate.py
  total=44 baseline_blocked=11 narrow_blocked=24 narrow_marginal_new=13
  ```
  derived: 13/44 = 30% of the live open backlog trip the new
  authoring-time requirement; the remaining fraction of the backlog sees no
  new required line at authoring time, and every check not opting into
  `population:` sees no new behavior at landing time. This is a structural
  guarantee (verified by inspection), independently re-measured against the
  live backlog by this review rather than merely asserted.
---

---
requirement: "the shipped narrow-trigger design's migration cost is accurately reported, since 'measured, not asserted' is the standard issue #2414 itself sets for any addition — verifying the 76%/31% backlog-impact figures this task asked for"
spec_ref: "issue #2414 body, `## Acceptance` check 5 (accuracy of the stated measurement); PR #2422 description's headline figure '14/45 (31%)'"
verdict: Incorrect
evidence: "gates/acceptance_gate.py:75-76 and on-the-record/directive/acceptance-format.md:28 — PR #2422 branch sha `2019bf3b`"
rationale: |
  canonical: `grep -n "8 of 45\|18%\|blocks 8" gates/acceptance_gate.py
  on-the-record/directive/acceptance-format.md` against the PR #2422
  worktree this session:
  ```
  on-the-record/directive/acceptance-format.md:28:  one blocks 8).
  gates/acceptance_gate.py:75:# backlog, this bounds the one-time migration cost to 8 of 45 open
  gates/acceptance_gate.py:76:# issues (18%) while still catching all three real incidents (#2291,
  ```
  This contradicts the builder's implementation record's `## Measurements`
  section 3 ("narrow-trigger (shipped) design = 14/45 = 31% newly blocked")
  and the PR #2422 description's own headline figure. Independently
  re-executed both the narrow-trigger and universal-design backlog sweeps
  against the live repository this session (44 currently-open issues, one
  fewer than the record's 45 because #2413 has since closed — #2413 is
  itself one of the marginally-blocked issues in both designs):
  ```
  $ python3 -c "..." # narrow-trigger sweep, PR #2422 worktree's own acceptance_gate module
  total=44 baseline_blocked=11 narrow_blocked=24 narrow_marginal_new=13
  issues=[1633, 1656, 2136, 2138, 2139, 2297, 2334, 2357, 2360, 2409, 2412, 2415, 2417]
  $ python3 -c "..." # universal-design sweep (trigger unconditional), same module
  total=44 baseline_blocked=11 universal_blocked=44 universal_marginal_new=33
  ```
  derived: 13/44 (narrow) and 33/44 (universal) — each exactly one fewer
  than the record's 14/45 and 34/45 (accounted for by #2413's closure since
  the PR's own measurement was taken), and neither consistent with the code
  comment's "8 of 45". The two figures this task asked to verify — 76%
  (34/45 universal) and 31% (14/45 narrow) — are BOTH independently
  reproduced and accurate; the "8 of 45 (18%)" figure shipped in the code
  comment and the directive doc is the inaccurate one.
spec_vs_built: "Spec (issue #2414 check 5, and this PR's own stated discipline): the migration cost of any addition must be measured and accurately stated, not asserted. Built: the correct, re-derivable number (14/45, 31%) exists in the builder's implementation record and the PR description, but a stale, lower, unfixed number (8/45, 18%) ships live in both the enforcing code's own comment (gates/acceptance_gate.py:75-76) and the directive doc future authors read (on-the-record/directive/acceptance-format.md:28). canonical: the builder's own `## What did not work` section (PR #2422 branch) states `_MECHANISM_TRIGGER` was missing past-tense/passive verb forms until a background warrant-hunter caught it before landing, and that Measurement 3 was re-run against the fixed regex afterward ('all fenced outputs above are post-fix') — the fixed, broader regex trips on more of the backlog, which is why the true count moved from roughly 8 to 14, but the code comment and directive doc committed in that same fix commit were never updated to match."
---

---
requirement: "no existing verification, record, or observer step is removed — state explicitly what was not touched"
spec_ref: "issue #2414 body, `## Acceptance` check 6"
verdict: Present
evidence: "the builder's implementation record `## What was not touched (issue-2414 acceptance criterion 6)` (PR #2422 branch)"
rationale: |
  canonical: `gh pr diff 2422 --name-only` this session:
  ```
  docs/issue-2414/reports/implementation.md
  docs/issue-2414/reports/implementation/2026-08-25-hunt-mechanism-trigger-and-convergence-evidence.md
  docs/issue-2414/reports/implementation/deviation-log/20260825T123700808526-fd3ea243eab5cfcd.md
  docs/reports/product/priorities.md
  gates/acceptance_gate.py
  gates/requirement_met.py
  gates/test_acceptance_gate.py
  gates/test_requirement_met.py
  on-the-record/directive/acceptance-format.md
  tests/test_acceptance_gate_tests_dir.py
  ```
  derived: 10 files touched total. `gates/gates.py`, `board.py`, `spawn.py`
  — the existing call-site wiring the record claims is untouched — do not
  appear anywhere in this list, corroborating the record's explicit claim
  by omission. The record names specifically what was not touched
  (`_ARTIFACT_REF`/`_EMPTY_STATE`/`_PROVENANCE`/`_UNVERIFIABLE`, the
  existing `requirement_met.py` sub-checks, the observer roles) rather than
  a bare assertion.
---

## What did not work

None on this review's own part — the verification approach (checking out
the PR into a worktree and re-executing its measurements rather than
reading its prose) worked as intended and is what surfaced the Incorrect
finding above.

## Open findings

- The stale "8 of 45 (18%)" figure in `gates/acceptance_gate.py:75-76` and
  `on-the-record/directive/acceptance-format.md:28` (Incorrect finding
  above, canonical: grep output pasted in that finding's evidence) —
  resolution path: not this review's to fix (conformance-review writes only
  its own record); since PR #2422 explicitly does not land as permanent
  (its own "Amendment reconciliation" section states it is offered as
  candidate input to #2415, not landed), whichever session next decides
  `must not:`'s fate — a #2415 keep/merge/drop review round, or a direct
  edit to PR #2422 before any merge — should correct both citations to the
  record's own 14/45 (31%) figure or re-measure fresh against the backlog
  at that time.
- The PR-classification judgment call behind the frequency figure could not
  be fully re-derived at PR-by-PR granularity within this review (see the
  check-2 finding above, canonical: the 38-item mechanical superset pasted
  there) — flagged as a residual verification gap, not asserted as wrong;
  the builder's own record discloses the same limitation.

## Skill verdicts

- skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2414's six `## Acceptance` bullets into the discrete requirement blocks above, and to pull the migration-cost-accuracy check out as its own item (implied by check 5's "measured, not asserted" clause and this task's explicit ask to verify 76%/31%) rather than folding it silently into check 5's Present verdict.
- skill-verdict: conformance-review-sampling-derivation — applied: invoked; the open backlog was enumerated fully rather than sampled (small enough — see the check-5/Incorrect-finding blocks above for the exact re-run), while the merged-PR-window classification was checked by an exact-count reproduction plus a mechanical superset plausibility check rather than full re-classification, with that limitation stated in Open findings rather than treated as exact.
- skill-verdict: conformance-review-verification-method-selection — applied: invoked; Test for the two shipped regression suites (rerun live against the PR worktree), Analysis for re-executing the frequency/backlog-impact measurements against current repository state, Inspection for the diff/comment/doc consistency check that surfaced the Incorrect finding.
- skill-verdict: conformance-review-verdict-assignment — applied: invoked; six Present verdicts and one Incorrect verdict, the Incorrect one naming its failing clause and citing spec_vs_built; re-checked its evidence twice (grep against both code and doc, plus a fresh live backlog re-run) before finalizing.
- skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence field cites file:line plus the PR head sha (`2019bf3be0f0404e6b05e753eba5f1991bb54c34`) or a live, re-runnable command with pasted output.
- skill-verdict: conformance-review-finding-record — applied: invoked; this file is the only file this review wrote to, using the five-value verdict set, and evidence was locatable for all seven requirement blocks (no refusal needed).
- skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope is ordinary fidelity-checking against issue #2414's own six checks, not an explicit extension into risk-banding a finding.
- skill-verdict: adversarial-review — not-applicable: this session already holds the full spec (issue #2414), the builder's own record, and PR history — the structurally-blind separate-evaluator setup that skill sets up is not what this review does; the conformance-review role itself already serves that function per contract v3.

## Next steps

None further from this session — `loop_state: terminal`. Whichever session
next touches `must not:`/`population:` (a #2415 keep/merge/drop review
round, or a direct edit to PR #2422) should correct the stale citations
named in Open findings above.
