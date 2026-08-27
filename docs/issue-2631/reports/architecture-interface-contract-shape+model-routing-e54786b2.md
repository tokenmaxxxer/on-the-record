---
issue: 2631
role: architecture-interface-contract-shape+model-routing-e54786b2
author: architecture-interface-contract-shape+model-routing-e54786b2
skills: architecture-interface-contract-shape (skill-repository(297e350)), model-routing (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: gates/model_routing.py
    sha: same-commit
  - path: on-the-record/hooks/quality-bar-gate.sh
    sha: same-commit
---

# issue-2631 — architecture-interface-contract-shape+model-routing-e54786b2 record

## What was done

Removed both surviving role-name lists per the operator ruling in issue
#2631: neither was renamed, relocated, sharded, or moved into config —
each capability that depended on a fixed identity list either lost that
capability outright (model routing) or turned out to have never actually
needed the list it was iterating (quality-bar gate).

**1. `gates/model_routing.py`** — removed the `_role_tier()` function and
the `"roles": [...]` key from every tier in `DEFAULT_POLICY` and in the
live `.on-the-record/model-routing.json` policy file. `route_model()` no
longer takes a `role` parameter at all — role identity is not a routing
signal anymore. The capability that stops working: the four names
`ux-engineering`, `brand-design`, `content-design`, `architecture` are no
longer forced onto the `judgment` tier by name. Those four roles now route
through the same three remaining rungs as every other role:
`design_bearing_override` (if the verdict is true) → `single_phase_tier`
(if single-phase) → `default_tier`.

`pipeline.py`'s `resolved_role_model()` was updated to match — it still
takes `role` (used only to decide whether to return a `(model, rule)`
tuple vs. a bare string, per issue #2070's byte-identical-when-omitted
contract) but no longer forwards it into `model_routing.route_model()`.

acceptance: `grep -n 'if role in' gates/model_routing.py` — result:
```
(no output, exit 1)
```

**2. `on-the-record/hooks/quality-bar-gate.sh`** — removed the `BAR_ROLES`
literal and the `role_patterns = {role: _TRIGGER_PATH_PATTERNS.get(role)
or [] for role in BAR_ROLES}` comprehension it drove; `bar_scoped_roles()`
is now called with `_TRIGGER_PATH_PATTERNS` directly.

acceptance: `grep -n 'BAR_ROLES' on-the-record/hooks/quality-bar-gate.sh`
— result:
```
(no output, exit 1)
```

derived: `python3` comparison of `{role: _TRIGGER_PATH_PATTERNS.get(role)
or [] for role in BAR_ROLES}` (the removed comprehension, reconstructed
against the pre-edit `BAR_ROLES` list and the still-present
`_TRIGGER_PATH_PATTERNS` dict) against `_TRIGGER_PATH_PATTERNS` itself —
result:
```
before == after: True
```
`BAR_ROLES` was a 7-name literal that exactly matched
`_TRIGGER_PATH_PATTERNS`'s own key set — the comprehension it fed was the
identity transform on a dict that already had exactly those keys, so this
edit changes nothing about which domains this gate classifies or which
files trigger which domain (full transcript, same command, in the
"Quality-bar gate: before vs. after" section below).

## Why

Two different situations under one ruling. `model_routing.py`'s list was
load-bearing — it really did decide which tier a role landed in via
membership test — so removing it removes real behavior (see "routing
change" below).

derived: same dict-equality command as "What was done" above — result:
```
before == after: True
```
`quality-bar-gate.sh`'s `BAR_ROLES` was inert per that result —
`_TRIGGER_PATH_PATTERNS` already held the complete key set, so the
comprehension gated by `BAR_ROLES` never differed from
`_TRIGGER_PATH_PATTERNS` itself. Keeping `_TRIGGER_PATH_PATTERNS` (a
domain → path-pattern dict, not an identity/permission list) is not
"renaming, relocating, sharding, or reading the same names from config" —
it's the pattern data the classification capability needs regardless of
`BAR_ROLES`'s presence, and it predates this issue unchanged. The
Acceptance's own check for this bullet is the literal grep for
`BAR_ROLES`, not a demand to remove `_TRIGGER_PATH_PATTERNS` — that dict
was never named in the ask.

`route_model()`'s `role` parameter was dropped rather than left unused,
per architecture-interface-contract-shape rule 11b (a public interface
carrying a parameter with zero live callers of its purpose after a
refactor should have that parameter deleted, not kept "just in case").

## Model routing: before vs. after (route_model out of gates/model_routing.py)

Ran the same subjects through the pre-change (HEAD) module and the
post-change (working-tree) module, both against their respective real
policy shape.

acceptance: `git show HEAD:gates/model_routing.py` +
`git show HEAD:.on-the-record/model-routing.json` (HEAD =
`49c4854b8d699130fe88e6f6db6e4287feb313c0`, `git rev-parse HEAD`), then
`route_model(role, single_phase, verdict, policy)` per subject — result:
```
role='ux-engineering'   single_phase=False design_bearing_verdict=None -> ('sonnet', 'role-tier:judgment')
role='brand-design'     single_phase=False design_bearing_verdict=None -> ('sonnet', 'role-tier:judgment')
role='content-design'   single_phase=True  design_bearing_verdict=None -> ('sonnet', 'role-tier:judgment')
role='architecture'     single_phase=False design_bearing_verdict=True -> ('sonnet', 'design-bearing-override')
role='api-design'       single_phase=False design_bearing_verdict=None -> ('sonnet', 'default-tier:mid-design')
role='random-role'      single_phase=True  design_bearing_verdict=None -> ('sonnet', 'single-phase-tier:mechanical')
```

acceptance: `gates/model_routing.py` working tree (this commit), same
subjects, `route_model(single_phase, verdict, policy)` (no `role` arg
anymore) — result:
```
role='ux-engineering'   single_phase=False design_bearing_verdict=None -> ('sonnet', 'default-tier:mid-design')
role='brand-design'     single_phase=False design_bearing_verdict=None -> ('sonnet', 'default-tier:mid-design')
role='content-design'   single_phase=True  design_bearing_verdict=None -> ('sonnet', 'single-phase-tier:mechanical')
role='architecture'     single_phase=False design_bearing_verdict=True -> ('sonnet', 'design-bearing-override')
role='api-design'       single_phase=False design_bearing_verdict=None -> ('sonnet', 'default-tier:mid-design')
role='random-role'      single_phase=True  design_bearing_verdict=None -> ('sonnet', 'single-phase-tier:mechanical')
```

**Stated routing change** (required by Acceptance, not to be discovered
later), read off the two result blocks above: the **model** selected is
identical before and after for every subject tested — still `"sonnet"` in
all six cases — because issue #2148 already pinned every tier's `model`
value to `"sonnet"`, independent of which tier gets picked. What **does**
change is the `rule` attribution for the three named roles
(`ux-engineering`, `brand-design`, `content-design`) that used to hit
`role-tier:judgment`: they now fall through to `default-tier:mid-design`
(or `single-phase-tier:mechanical` when single-phase). `architecture`,
`api-design`, and `random-role` are unaffected in both model and rule —
`architecture` was already reachable via `design_bearing_override` before
the role-list check ever ran, and the other two were never in the removed
list. If the #2148 pin is ever lifted and `judgment`/`mid-design` diverge
in model again, these three roles would then also see a real model change
(previously judgment-tier's model, now mid-design/mechanical's) as a
direct consequence of this removal — that is the real, stated behavior
change this issue authorizes.

## Quality-bar gate: before vs. after (classify pass/refuse payloads)

`bar_scoped_roles()`/`classify()` (`gates/quality_bar.py`) are the actual
classification logic the gate's `role_patterns` feeds; the `gh pr
merge`-parsing and record-resolution code around them is unchanged by
this issue, so the test isolates the part that changed. The file lists
below (a synthetic "clean docs edit" vs. a synthetic "touches auth code"
PR) are illustrative payload shapes for this harness, not paths read from
this repo.

acceptance: `python3` script feeding `before_role_patterns` (the removed
`{role: _TRIGGER_PATH_PATTERNS.get(role) or [] for role in BAR_ROLES}`
comprehension) and `after_role_patterns` (`_TRIGGER_PATH_PATTERNS`, what
the edited gate passes) through `gates/quality_bar.py`'s unmodified
`bar_scoped_roles`/`classify` — result:
```
before == after: True
should_pass (no scoped files) [example: a README/docs-only PR]:
  before= frozenset() after= frozenset() equal= True
  classify before= NO_BAR_SCOPED None
  classify after = NO_BAR_SCOPED None
should_refuse (scoped: secure-coding-pattern path) [example: a PR touching a file under an auth/ directory]:
  before= frozenset({'secure-coding', 'test-authoring'}) after= frozenset({'secure-coding', 'test-authoring'}) equal= True
  classify before= BAR_NOT_MET no bar-met record
  classify after = BAR_NOT_MET no bar-met record
```
acceptance: `bash -n on-the-record/hooks/quality-bar-gate.sh` — result:
```
(exit 0, no output)
```

## `scripts/audit_removal_claim.py` output and per-hit classification

Ran against two claims: the `model_routing` role-tier membership test
(`removed_names: ["_role_tier"]`, `member_samples: ["ux-engineering",
"brand-design", "content-design", "architecture"]`, `min_coloc: 2`) and
the `quality-bar-gate` `BAR_ROLES` literal (`removed_names: ["BAR_ROLES"]`,
`member_samples:` the 7 domain names, `min_coloc: 2`).

derived: `python3 scripts/audit_removal_claim.py <claims.json> --root .`
— result:
```
=== model_routing role-tier membership test ===
verdict: RESHAPE_DETECTED
q1 (name gone): live_hits=[] gone=true
q3 (still branches): branch_hits=[] still_branches=false
colocated_files: [
  ('./.git/index', 4),
  ('./gates/__pycache__/human_comprehensibility.cpython-310.pyc', 2),
  ('./gates/__pycache__/model_routing.cpython-310.pyc', 4),
  ('./gates/__pycache__/quality_bar.cpython-310.pyc', 2),
  ('./gates/model_routing.py', 4),
  ('./pipeline.py', 2)
]

=== quality-bar-gate BAR_ROLES literal ===
verdict: RESHAPE_DETECTED
q1 (name gone): live_hits=[] gone=true
q3 (still branches): branch_hits=[] still_branches=false
colocated_files: [
  ('./.git/index', 7),
  ('./.git/objects/pack/pack-973b1715eeac2aa357b3debb05b3bd012d731f95.pack', 3),
  ('./on-the-record/hooks/quality-bar-gate.sh', 7)
]
```

Per-hit classification (Q1/Q3 are clean on both claims per the result
block above — `_role_tier` and `BAR_ROLES` are gone, and grep found no
`in (...)`/`==`/dispatch shape touching any member_sample outside
docs/tests; every hit below is Q2's colocation heuristic, classified
individually):

- `./.git/index`, `./.git/objects/pack/*.pack` (both claims) — **false
  positive**: git's own internal object/index storage, not source; every
  tracked file's content is byte-present in these by construction.
- `./gates/__pycache__/*.pyc` (claim 1) — **false positive**: compiled
  bytecode cache of `model_routing.py`'s new docstring (and an unrelated
  neighboring module's cache picking up a substring), a build artifact
  mirroring the next hit below, not independent evidence.
- `./gates/model_routing.py` (claim 1) — **false positive**: this
  session's own new module docstring narrates the four removed role
  names in prose, explaining what the removal changed (see "What was
  done" above). This is documentation of the removal, not a live data
  structure — Q3's `branch_hits=[]` for this same claim already confirms
  zero branch hits in this file.
- `./pipeline.py` (claim 1) — **false positive**: two incidental,
  unrelated substring matches — `"ux-engineering-color-visibility"` (a
  naming-example string, pre-existing and unrelated to model routing) and
  the substring `"architecture"` inside the unrelated phrase "issue-2548
  architecture record". Neither is part of a role-tier list.
- `./on-the-record/hooks/quality-bar-gate.sh` (claim 2) — **false
  positive, flagged rather than silently dismissed**: this is
  `_TRIGGER_PATH_PATTERNS`, the domain→path-pattern dict the gate has
  always used to decide which changed files implicate which quality
  domain. All 7 domain names are its keys, unchanged by this edit (it
  existed, identical, before `BAR_ROLES`'s removal too — the dict-equality
  result in "What was done" above shows the old `BAR_ROLES`-gated
  comprehension and this dict were already equal). This is a true
  colocation hit in the literal sense the tool measures (7 names in one
  non-doc, non-test file), but it is not a reconstruction of the removed
  `BAR_ROLES` membership test: nothing tests whether an incoming name is
  *permitted* by this dict the way `BAR_ROLES` gated its comprehension;
  it's data the pattern-matching capability inherently needs to tell
  domains apart, out of this issue's scope (the Acceptance's own check
  for this bullet is the literal `BAR_ROLES` grep, not a demand to remove
  `_TRIGGER_PATH_PATTERNS`), and Q3's `branch_hits=[]` for this claim
  confirms no membership test remains anywhere touching these names.

## What did not work

None.

## Upstream basis

acceptance: `gh issue view 2631 --repo tokenmaxxxer/on-the-record`, then
`git rev-parse HEAD` — result: base commit
`49c4854b8d699130fe88e6f6db6e4287feb313c0`, issue body quoting these
lines of that commit's state of both files edited in this delivery:
```
gates/model_routing.py:30   "roles": ["ux-engineering", "brand-design", "content-design", "architecture"],
gates/model_routing.py:55   if role in (tier.get("roles") or []):
on-the-record/hooks/quality-bar-gate.sh:124  BAR_ROLES = [
on-the-record/hooks/quality-bar-gate.sh:247  role_patterns = {role: _TRIGGER_PATH_PATTERNS.get(role) or [] for role in BAR_ROLES}
```
Both files land in this same commit (same-commit per frontmatter).

## Open findings

None.

## Next steps

acceptance: `printenv CORE_BUILD_NOW` — result:
```
1
```
Build-now single-phase delivery per contract v3 s19a: PR carries `Closes
#2631` directly rather than a two-phase proposal/approval split; no
further work is queued on this record.

skill-verdict: model-routing — applied: invoked; used its "When NOT to
delegate" rule to route this task's edits to myself rather than an
executor subagent — small, tightly coupled, judgment-heavy edits where
each step (a handful of lines, requiring continuous judgment about
routing/classification semantics) cost less than writing a delegation
brief would have.
skill-verdict: architecture-interface-contract-shape — applied: invoked;
rule 11b (delete an interface parameter with zero live callers after a
refactor, rather than leaving it unused) drove dropping `route_model()`'s
`role` parameter entirely once its only use (`_role_tier` membership
test) was removed.
other mounted skills: not triggered.
