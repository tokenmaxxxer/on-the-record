---
Subject: issue-1118
---

## Scout skip record

Skip condition: spec leaves no design decision open. The requirement set
under review is fixed by docs/specs/requirements.md (single cited
requirement R001, mechanically defined by the requirement_registry
function in gates/gates.py); there is no product-shaped surface to scout
comparable prior art against — canonical: docs/specs/requirements.md:22-27,
read this session.

## Board condition

canonical: `git log origin/main --oneline -i --grep="1118"`, read this
session.
```
930d4153 Merge pull request #1128 from tokenmaxxxer/issue-1118/implementation
f526e42b issue-1118: phase-2 board record for stopgate scan and dedup fixes
12c7cbb1 Merge pull request #1125 from tokenmaxxxer/issue-1118/implementation
41e5623b issue-1118 phase-2: exclude injected directive text from stopgate scan, dedup undischargeable flags
c5bc2052 Merge pull request #1121 from tokenmaxxxer/issue-1118/architecture
407800ca issue-1118 phase-1: survey hook-pair contradiction, propose scan/dedup fix
```

Implementation commit 41e5623b landed on main (merge 12c7cbb1), with its
own phase-2 board record added by f526e42b (merge 930d4153). No
conformance-review record for this subject exists at HEAD yet —
canonical: `find docs/issue-1118 -name conformance-review.md`, read this
session (empty result). Board condition satisfied.

## What issue #1118 asked for

canonical: `gh issue view 1118`, read this session.

Issue #1118 is a hook-pair contradiction fix (product-capture-stopgate.sh
vs deliverable-guard.sh), self-labeled `infrastructure/no-direct-requirement`.
Its own text states plainly: "the only digest requirement (R001,
record-growth dilution) is not this issue's target." This session was
invoked citing R001 as the requirement basis to check regardless — R001
is being checked as the standing digest requirement against this issue's
delivered artifact, not because the issue claims to implement it.

## R001 itself

canonical: docs/specs/requirements.md:22-27, read this session.
```
## R001
quote: 기록이 많아짐으로써 사용자가 핵심으로 제시하는 요구사항들이 희석되는 문제
source_issue: 321
check: gates/gates.py::requirement_registry
status: enforced
```
R001's enforcement mechanism is the requirement_registry function in
gates/gates.py, which fails when any docs/specs/requirements.md entry's
`check` path no longer resolves at HEAD — i.e., it guards against a
requirement's enforcement quietly disappearing as the record grows.

## Code under review

canonical: `git show --stat 41e5623b` and `git show --stat f526e42b`, read
this session.
- on-the-record/hooks/product-capture-stopgate.sh
- gates/test_product_capture_vs_deliverable_guard.py
- docs/issue-1118/decisions/generator-choice.md
- docs/issue-1118/reports/implementation.md

None of these touch docs/specs/requirements.md or gates/gates.py.
R001 has no direct implementation surface in this delivery; the only
relevant question for phase 2 is whether the delivery incidentally
degrades R001's enforcement mechanism (e.g. by adding a stale requirement
entry, or breaking the registry gate).

## Gap

No conformance-review record for this subject exists yet — canonical:
`find docs/issue-1118 -name conformance-review.md`, read this session
(empty result), same finding cited under Board condition above. Phase 2
plan: render a per-requirement verdict for R001 by re-running the
requirement_registry gate at current HEAD and checking whether the
delivered files list above touches docs/specs/requirements.md.
