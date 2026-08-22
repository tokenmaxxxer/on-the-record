---
code_under_review:
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/test_directive_content.py
loop_state: landed
type: directive-content
breaking: false
verdict: pass
---

# issue-2043 implementation record

## What was done
Added a `RESPONSE ORDERING` section to the injected `[orchestrate]` directive
(`on-the-record/hooks/directive.sh`), between the existing `REPLY STRUCTURE`
bullet and the `You never write board records...` bullet. The section states:
when the user's latest message carries an ask or direction, the reply opens
with the direct response to it (what was heard, what the actions taken or
planned are), clearly separated from any status/progress narration that
follows; a pure-status turn (no user ask pending) is unaffected and keeps
`REPLY STRUCTURE`'s existing flow-first shape.

Added `t_response_ordering_obligation_present` to
`on-the-record/hooks/test_directive_content.py`, asserting the section
header, the opening rule, the narration-separation rule, and the
pure-status carve-out are all present in the directive text.

No other directive section was altered (Acceptance requirement).

## Why
Per the issue-2043 body: the orchestrator's replies buried the direct
response to the user's ask under status/progress narration, per the
issue's own empty-state description. The fix makes response-first ordering
a default, mechanically testable property of the injected directive rather
than a one-off behavioral ask.

## Upstream basis
Issue #2043 (frozen `## Acceptance`): the injected orchestrate directive must
carry a RESPONSE ORDERING section stating the rule, verified by a
directive-content test, with no other directive section altered. Delivered
under the build-now bypass (contract v3 s19a) — this session's environment
carried `CORE_BUILD_NOW=1`.

## Acceptance verification
Requirement 1 (RESPONSE ORDERING section present, states the rule) and
requirement 2 (directive-content test asserts its presence) are both
exercised by the same run:

canonical: python3 -m pytest on-the-record/hooks/test_directive_content.py -q — result: PASS
```
10 passed in 0.96s
```
(includes `t_response_ordering_obligation_present`; no SKIPPED lines)

Requirement 3 (no other directive section altered):

canonical: git show cb81a22f -- on-the-record/hooks/directive.sh — result: PASS
(diff is a single inserted bullet block; no other hunk touched)

## Test-tiering gap note
Diff touches `on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py`,
both named in `.on-the-record/test-tiers.json`'s slow-tier
`trigger_change_classes`.

canonical: timeout 280 python3 -m pytest -q -m slow — result: UNMEASURED
(background task hit the 280s bound and was terminated, exit code 143; the
slow suite's full wall-clock cost exceeds that bound in this environment)

canonical: python3 -m pytest -q -m "not slow" — result: PASS
(fast tier ran clean; separately, the diff-scoped run cited under
Acceptance verification above independently exercises both touched files)

Surfacing the slow-tier gap rather than absorbing it silently, per the
test-tier directive's observe-only stage.

## What did not work
None.

## Open findings
None.

## Next steps
None — record is terminal (`landed`).
