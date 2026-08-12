# issue-992 current-state survey (product-discovery, phase 1)

## Background / context

Issue #807 (steps 1-2) built and piloted a Gate A (valid judgment) /
Gate B (valid deliverable) / Gate C (lens-based finding) rubric against
6 load-bearing roles (execution-observation, defect-verification,
architecture, product-discovery, security-threat-model, test-authoring).
canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md
and docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md
(both read this session). Issue #992's own text names "#807/#926/#935"
as the precedent that landed the strengthening edits for that 6-role
set; this survey does not independently re-verify #926/#935's diffs
(out of this issue's scope), only #807's own proposal text.

Issue #992 asks to extend that same depth to the remaining 37 roles,
formalized as a 5-part "expertise template": (a) methodologies with
when-to-use routing, (b) decision frameworks composing with
`judgment_axes` (#586), (c) failure/anti-pattern catalogs, (d)
senior-practitioner checklists, (e) canonical sources with no fabricated
citations. canonical: `gh issue view 992` (read this session).

**Scope constraint found during this survey**: role rulebooks are
external repos, not files in this working tree — `roles/*.json`'s
`repo`/`path` fields point at `$TOKENMAXXXER_RULEBOOKS/<role>-rulebook`
(e.g. `repo: tokenmaxxxer/product-discovery-rulebook`), checked out only
at role spawn time. canonical: roles/product-discovery.json (read this
session, `repo`/`path` fields).

```
derived: echo "TOKENMAXXXER_RULEBOOKS=$TOKENMAXXXER_RULEBOOKS"; ls "$TOKENMAXXXER_RULEBOOKS"
TOKENMAXXXER_RULEBOOKS=
ls: ''에 접근할 수 없음: 그런 파일이나 디렉터리가 없습니다
```

This session has no filesystem access to the 43 rulebook repos
themselves. #807's own audits (canonical:
docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md
§1, which reads `roles/*.json`+`roles/specs/*.spec.json`, never a
rulebook-repo path) hit the same boundary and worked instead from
`roles/specs/*.spec.json` — the machine-checked artifact
(`gates/role_spec_shape.py`) that mirrors each rulebook's operationalized
methodology (`source_standard`, `required_fields`, `recomputation`,
Gate-A/B/C text where present). This survey follows the same
substitution and states it plainly rather than fabricating
rulebook-repo evidence, per this role's evidence-citation obligation.

## Problem stated without any solution attached (JTBD tuple)

The issue text embeds a solution ("raise all 43 rulebooks... land
deepening PRs per cluster"). Restated in the customer's terms, stripped
of that solution:

- **Job performer**: any role session spawned mid-repo-lifecycle
  (an agent acting under a role like `security-threat-model` or
  `pricing`) — and, one level up, the operator who trusts that session's
  output without re-deriving the domain call themselves.
- **Job**: reach a domain-competent verdict (a judgment, a deliverable, a
  finding) that a real ~20-year practitioner in that domain would also
  reach, given the same repo/system state — not a schema-conformant but
  domain-empty stand-in for one.
- **Circumstance**: the role's only domain-knowledge carrier at spawn
  time is its rulebook (+ spec); there is no human domain expert in the
  loop to catch a plausible-sounding-but-wrong call before it lands on
  main.
- **Desired outcome**: the operator can trust a role's verdict on its own
  lens without independently re-verifying the domain reasoning behind
  it — i.e., rulebook thinness never becomes the reason a mistaken
  verdict is trusted as if it were a sound one.

Gap: the issue jumps straight to "which rulebooks are thin, deepen
them" — a solution — without first confirming that thinness (rather
than e.g. missing invocation, or a downstream role never reading the
rulebook it's given) is where the JTBD currently fails. The evidence
below is offered as that confirmation, not assumed.

## Opportunity-solution tree branch (OST)

- **Outcome**: fewer role verdicts that are schema-conformant but
  domain-empty reaching `main` undetected (northpole reqs #1/#3/#5).
  canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md
  §2 (read this session, maps these reqs to load-bearing roles).
- **Opportunity**: the ~37 non-piloted rulebooks lack the same
  methodology depth #807 already exercised on 6 piloted roles — an
  opportunity already exercised on a subset, not a fresh hypothesis.
- **Candidate solutions** (this proposal ranks and phases these, does
  not yet build any): (1) apply #807's Gate A/B/C rewrite pattern
  role-by-role across the remaining 37; (2) add #992's extra template
  parts (anti-pattern catalog, senior checklist) on top of Gate A-C
  where #807 stopped short; (3) do nothing further and rely on
  downstream adversarial review (signal #8, specified but not built —
  canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md
  §3) to catch hollow verdicts post-hoc.
- **Discriminating assumption test**: this proposal's live-fire design
  is the test — a seeded domain task where the deepened rulebook
  demonstrably changes the role's judgment/output vs. the
  pre-deepening baseline, on the first phased cluster, before
  committing the same treatment to the remaining clusters.

## Evidence read this session

canonical: ad-hoc `python3` read of all 43 `roles/specs/*.spec.json`
files this session (script below), not a prior record.

```
derived: python3 -c "
import json, glob
n = sum(1 for f in sorted(glob.glob('roles/specs/*.spec.json')) if json.load(open(f)).get('source_standard'))
print(n, 'of', len(glob.glob('roles/specs/*.spec.json')))
"
43 of 43
```
Every role spec carries a non-empty `source_standard` citation (Gate A
citation present repo-wide).

```
derived: python3 -c "
import glob
hits = []
for f in sorted(glob.glob('roles/specs/*.spec.json')):
    txt = open(f).read().lower()
    if 'hollow' in txt or 'finding_method' in txt or 'anti_pattern' in txt or 'failure_catalog' in txt:
        hits.append(f)
print(len(hits))
for h in hits: print(h)
"
6
roles/specs/architecture.spec.json
roles/specs/defect-verification.spec.json
roles/specs/execution-observation.spec.json
roles/specs/product-discovery.spec.json
roles/specs/security-threat-model.spec.json
roles/specs/test-authoring.spec.json
```
This is exactly the #807 step-2 pilot set (canonical:
docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md
§1, same 6 role names). None of the 6 carry an `anti_pattern`/
`failure_catalog` field even now — #992's part (c) is new ground for
all 43, including the 6 already piloted on Gate A/B/C.

The remaining 37 specs carry `source_standard` (Gate A citation) but
none carry hollow-instance, finding-method, or anti-pattern content —
consistent with #807 step-1's own finding (canonical:
docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md
§1 Gate B, "the CURRENT state for effectively all 43 roles") that Gate B
fails uniformly repo-wide.

## What this survey does not claim

- It does not re-grade the 6 already-piloted roles' Gate A/B/C verdicts
  (that's #807's own record) — #992 explicitly scopes to "the remaining
  ~37."
- It does not claim to have read the external rulebook repos' actual
  prose (inaccessible this session, stated above) — the spec-file proxy
  is the same substitution #807 used, not a stronger claim.
