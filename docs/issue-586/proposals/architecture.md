---
status: proposed
files:
  - roles/conformance-review.json
  - roles/capacity-planning.json
  - roles/performance-engineering.json
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape_batch9.py
  - docs/decisions/2026-08-10-judgment-axis-matrix.md
  - docs/handbooks/architecture-methodology.md
---

# Proposal — issue #586 step 1: complete judgment-axis matrix (architecture)

## Intent
Assign the two remaining unowned methodology axes (per
`docs/issue-586/reports/architecture/survey.md`, `alignment` and
`external_burden` — `performance` gets a clean owner too) to exactly one
role each, close the zero-owner gap in the completeness check, and define
the rulebook axis-evaluation procedure template plus a batch plan so
step 2 (implementation) and step 3 (conformance-review) have a frozen
contract to build against.

## Constraints found
- Axis vocabulary is closed at five (`alignment`, `maintenance_complexity`,
  `external_burden`, `attack_potential`, `performance`) — already fixed by
  `gates/role_spec_shape.py`'s `_JUDGMENT_AXES`; not reopened here.
- `maintenance_complexity` (architecture) and `attack_potential`
  (security-threat-model) are already owned — reassigning them is out of
  scope; only the 3 unowned axes get new owners.
- I (architecture, this session) cannot edit other repos'
  rulebook content (`repo`/`path` in each `roles/*.json` point outside
  this checkout) — the procedure template ships as a shape spec in this
  repo; each owning role's own session writes its rulebook's procedure
  text in its own PR, same division #573 used (architecture proposed the
  shape, each role authors its own rulebook prose).
- Completeness must be machine-checkable (issue text, acceptance
  criteria) — a prose assignment is not sufficient; the gate must fail on
  an unowned or double-owned axis.

## Accumulation
This batch edits 3 of 43 `roles/*.json` files with the same one-line
shape (`"judgment_axes": [...]` added/set). If a future issue needs to
reassign or add axes again, the same 3-line-per-file pattern repeats —
that is expected and bounded: `_JUDGMENT_AXES` is closed at 5 entries
(see "Why no additional axis" below), so at most 5 roles will ever carry
this field, and `check_axis_ownership`'s zero-owner extension (this
proposal) is exactly the mechanical brake that stops a 6th accumulation
round from silently drifting — any future axis add/reassignment fails
the gate until the matrix is complete again, so there is no unbounded
repeat-edit risk here, just a fixed, small, gate-verified set.

## 1. Axis matrix — assignment and rationale

| Axis | Owning role | Rationale |
|---|---|---|
| `alignment` | `conformance-review` | `decides: 산출물 vs 명세 일치` — conformance-review's entire domain is checking an artifact against recorded specs/decisions without reading builder intent (`use_when`: "빌더 의도는 안 읽는다"). That is definitionally "alignment with recorded judgments" — no other role's `decides` field is about comparing output against a record. |
| `maintenance_complexity` | `architecture` | Already owned (#573) — `decides: 컴포넌트 경계·의존 방향`, this role's whole job is judging what a change costs to maintain going forward. Unchanged by this proposal. |
| `external_burden` | `capacity-planning` | `decides: 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가` — of all 43 roles, capacity-planning is the only one whose domain is resource/demand budgeting; external burden (e.g. crawling load placed on a third party) is a demand-on-a-finite-resource question at heart, same shape as internal capacity, just pointed outward. No role names external-facing load explicitly, so this is the nearest existing domain fit rather than a literal match — recorded as a judgment call, not a certainty. |
| `attack_potential` | `security-threat-model` | Already owned (#573) — `decides: 신뢰 경계의 위협 표면`. Unchanged by this proposal. |
| `performance` | `performance-engineering` | `decides: 부하/지연 목표를 만족하는가` — direct 1:1 match, no ambiguity. |

Every one of the 43 roles was checked against the 5 axes (see survey);
only these 5 have a `decides` field that names the axis's concern. No
axis is left to a role whose domain only touches it tangentially (e.g.
`risk-management`'s "전사 리스크 노출" is broader than any single axis and
was rejected as an owner for that reason — assigning a broad-scope role
would blur the "exactly one owning role" contract at evaluation time, not
just at schema time).

### Why no additional axis
The issue text offers "plus any you justify." I considered and rejected:
- A `cost` / `unit-economics` axis — `finance-unit-economics` exists as a
  full role already; folding it into the fixed judgment-axis set would
  duplicate machinery that role already has (its own record file, own
  `decides`) for no gain the #573 gate needs.
- A `legal` / `compliance` axis — same reasoning against
  `legal-compliance`; the delegated-judgment panel (#573) is scoped to
  the five methodology axes the operator named for exactly this reason
  (per issue #586's own framing: "the methodology axes the operator
  named"). Adding axes outside that closed set is a scope decision for
  the operator, not something this proposal should assume.
No sixth axis is proposed.

## 2. Rulebook axis-evaluation procedure template

Ships as a new section in `docs/handbooks/architecture-methodology.md`
(this repo, in scope) that every axis-owning role's rulebook must match.
Shape (mirrors the `axis_evaluation` record shape
`gates/role_spec_shape.py::check_axis_evaluation_entry` already
validates):

```markdown
## Axis evaluation procedure — <axis-name>

READ: <the specific record/spec paths this role reads to judge this
  axis — e.g. conformance-review reads the spec cited by the
  implementation record's `Upstream / basis` line>

EXECUTE:
1. <mechanical step producing evidence — e.g. "diff the landed artifact
   against the cited spec section", not "consider whether it feels
   aligned">
2. <mechanical step>
3. ...

CRITERIA FOR supports: <closed, checkable condition>
CRITERIA FOR contradicts: <closed, checkable condition — must be able to
  produce a `finding.target_path` that resolves against some role's
  `write_scope` and a `finding.required_fix`, per the existing shape
  check>
CRITERIA FOR no-opinion: <when the axis is out of scope for the artifact
  under review — e.g. no trust boundary present for attack_potential>

CITATION: <what `axis_evaluation.citation` must point to — a record path
  or commit sha, never a paraphrase>
```

This is a shape contract, not prose per role — each owning role's
rulebook session fills the four blanks (READ/EXECUTE/CRITERIA/CITATION)
for its own axis using its own domain knowledge. `EXECUTE` steps must be
mechanical (read a file, run a diff, check a field) so the verdict is
"expertise exercised," per the issue's own #476 line, not a self-report;
a step is rejected on review here if it reduces to "consider whether X"
with no checkable output.

## 3. Batch plan (per #521-#525 precedent)

Program-style, one shippable batch per PR, each batch = one axis
assignment + that role's own rulebook procedure PR (in that role's own
rulebook repo, out of this repo's reach — tracked as a follow-up issue
each, not authored here):

| Batch | Scope | This repo's part |
|---|---|---|
| Batch 1 (this PR, issue #586 step 1) | Schema: assign `alignment` -> conformance-review, `external_burden` -> capacity-planning, `performance` -> performance-engineering on `roles/*.json`; extend `check_axis_ownership` to flag zero-owner axes; add the procedure-template section to the handbook | `roles/conformance-review.json`, `roles/capacity-planning.json`, `roles/performance-engineering.json`, `gates/role_spec_shape.py`, `gates/test_role_spec_shape_batch9.py`, `docs/handbooks/architecture-methodology.md`, `docs/decisions/2026-08-10-judgment-axis-matrix.md` |
| Batch 2 | conformance-review rulebook gains its `alignment` procedure section, filled per the template | Not this repo (rulebook repo) — architecture files the follow-up issue with the frozen template attached |
| Batch 3 | capacity-planning rulebook gains its `external_burden` procedure section | Same as above |
| Batch 4 | performance-engineering rulebook gains its `performance` procedure section | Same as above |
| Batch 5 (issue #586 step 3, conformance-review's own step) | Multi-role panel fixture: extend `test_delegated_judgment_gate.py` with a decision touching 3+ axis-owning roles' write scopes | Not this repo unless the gate test lives here — verify at step-2/3 handoff |

Batches 2-4 are independent of each other once batch 1 lands (no
same-line mutable state, no sequential dependency between the three
rulebooks) — they can run as three separate role sessions in parallel.
Batch 5 depends on batches 1-4 all being landed (the panel fixture needs
all 5 axes actually owned and evaluable).

## Out of scope
- Writing the actual procedure prose inside
  `architecture-rulebook`/`conformance-review-rulebook`/
  `capacity-planning-rulebook`/`performance-engineering-rulebook` — those
  are separate repos; batches 2-4 file as follow-up issues, not done in
  this PR.
- Reopening the 5-axis vocabulary or the 2 already-owned axes.
- The multi-role panel gate-test fixture (issue #586 step 3, owned by
  conformance-review per the issue's own step split) — batch 5 above is
  a placeholder pointer, not this PR's work.

## How I'll know it worked
- `gates/test_role_spec_shape_batch9.py` (extended) shows all 5 axes with
  exactly one owner each, and a new zero-owner-axis test fails before the
  `roles/*.json` edits and passes after.
- `python3 gates/role_spec_shape.py roles/specs/<name>.spec.json` still
  exits 0 for all 43 roles (batch 1 touches `roles/*.json`, not
  `roles/specs/*.spec.json`, so this is a regression check, not a new
  requirement).
- The full repo test suite (`pytest`) passes.

## What did not work
(appended during build, if anything breaks)
