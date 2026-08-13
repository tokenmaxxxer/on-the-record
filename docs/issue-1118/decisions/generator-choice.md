# Generator-level fix, not instance patch (issue #1118)

Context: hook-pair contradiction reports on product-capture-stopgate.sh
recurred under different trigger phrases (priorities.md, then goals.md),
and the same conflict was lost twice on 2026-08-12 when addressed only
at the reported instance.

Decision: fix at the stopgate's two generator points — the transcript
scan that cannot distinguish injected directive text from user-authored
text (Fix 2), and the flag-emission path with no bound on how long an
undischargeable flag persists (Fix 3) — rather than special-casing
#1118's own trigger phrase or category.

Consequences: future trigger phrases appearing inside injected wrapper
blocks, and future undischargeable categories beyond priorities/goals,
are covered without a new patch per phrase or category.

Alternatives considered: patching only the reported phrase ("우선순위는
아래 순서대로") — rejected, since the issue's own evidence shows the same
generator class recurring under a different phrase (goals.md) within the
same day, meaning a phrase-specific patch would not have prevented the
second recurrence.
