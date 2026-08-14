---
code_under_review:
  - on-the-record/hooks/record-tiering-directive.sh
  - on-the-record/hooks/record-tiering-guard.sh
  - on-the-record/hooks/test_record_tiering_directive.py
type: revert
breaking: false
verdict: killed-per-measurement
loop_state: landed
---

# issue #745 — phase 2 record: revert Item 2 tiering for `reports/<role>.md`

## Summary of work

Executes the pre-registered revert condition from
`docs/issue-745/reports/product-discovery.md` (this issue's own landed
measurement record, PR #1509, `## Decision rule` section): Item 2
(citation-informed section tiering, candidate 1) is killed for the
`reports/<role>.md` category — primary metric moved +19.1% instead of the
pre-registered ≥-30%, and the `cross_issue_citation_rate` guardrail
breached by -15pp against a 5pp tolerance.

canonical: `on-the-record/hooks/record-tiering-guard.sh` and
`on-the-record/hooks/record-tiering-directive.sh` (both read in this same
turn before editing) — their entire matched scope was
`docs/issue-<n>/reports/implementation.md`'s `## What did not work`
section (derived: `grep -n "reports/implementation" on-the-record/hooks/record-tiering-guard.sh`
→ the guard's only path regex, `(^|/)docs/issue-[^/]+/reports/implementation\.md$`).
That path pattern is exactly the `reports/<role>.md` category the kill
verdict names — there is no narrower subset to carve out, so the revert
removes this pair's entire enforcement rather than narrowing a regex.
`proposals/*.md` and `docs/reports/*.md` were never matched by either
script (canonical: same regex read above), so their behavior is
unchanged, consistent with the verdict record's statement that those
categories carry no verdict from this measurement window.

## What was done

- `on-the-record/hooks/record-tiering-directive.sh`: replaced the
  CLAUDE_ROLE-gated `<record-tiering-directive>` emission with an
  unconditional no-op (`exit 0`, no output), with a header comment
  recording the kill verdict and why the file is kept (not deleted) —
  `hooks.json` still references it, and the history stays traceable.
- `on-the-record/hooks/record-tiering-guard.sh`: replaced the PreToolUse
  payload-parsing/denial logic with the same unconditional no-op, header
  comment updated the same way.
- `on-the-record/hooks/test_record_tiering_directive.py`: narrowed to the
  reverted (inert) scope — tests that used to assert a `returncode == 2`
  deny on a padded "None ..." body now assert `returncode == 0` (no
  longer denied); tests for behavior that no longer exists (the
  split-Edit reconstruction bypass, the fragment-fallback-on-unreadable-
  file path, the non-implementation-report path-ignore case, the
  fragment-without-heading case) were removed since there is no more
  content-inspection logic left to exercise. Tests asserting always-quiet
  behavior (CLAUDE_ROLE unset, ORCHESTRATE_OFF=1, malformed payload) are
  kept as-is since a no-op trivially satisfies them too.

derived:
```
$ python3 -m pytest on-the-record/hooks/test_record_tiering_directive.py -q
.........                                                                [100%]
9 passed in 0.07s
```

`hooks.json` was left unchanged — both entries still point at the same
script paths, which now simply no-op; no registration edit was needed.

## Why (rationale)

The kill verdict is binding per the pre-registered rule in
`docs/issue-745/proposals/product-discovery.md` Item 2 (guardrail breach
on a named category overrides the primary metric and forces immediate
kill, no pivot). This record's job is mechanical execution of that
already-decided revert, not re-litigating the candidate.

## Upstream basis

- `docs/issue-745/reports/product-discovery.md` (PR #1509, this issue's
  own measurement record — `code_under_review:` lists the same two hook
  files, `verdict: kill`, `loop_state: invalidated`)
- `docs/issue-745/proposals/product-discovery.md` (Item 2's pre-registered
  package: primary metric, threshold, guardrail, revert condition)
- issue #760 (original phase-1/phase-2 landing of the now-reverted
  mechanism, PR #783)

## What did not work

None.

## Open findings

canonical: `docs/issue-745/reports/product-discovery.md` `## Open
findings` section (this record does not reopen or re-derive them) — two
items remain out of this record's scope:

- Why real (non-"none") `## What did not work` content grew in the
  post-#783 sample is unexplained; deferred to a follow-up investigation
  per that record's own `## Next steps` item 2. Not actioned here — this
  record's scope is the revert only.
- Items 1 (thinking budget) and 3 (execution-observation conditioning)
  remain held per the operator's 2026-08-11 decision comment on this
  issue; their revisit is out of this record's scope.

## Next steps

- A follow-up session investigates the `## What did not work` content
  growth (per `docs/issue-745/reports/product-discovery.md` Next steps
  item 2) to inform whether a redrawn tiering candidate is worth
  pre-registering.
- Whichever role/issue the operator assigns next re-evaluates Items 1 and
  3, per the operator's 2026-08-11 held-items decision.

## Resolution path

Both open findings above resolve exactly as stated in
`docs/issue-745/reports/product-discovery.md`'s own `## Resolution path`
section — this record adds no new open findings of its own, so it
inherits that resolution path rather than restating a different one.
