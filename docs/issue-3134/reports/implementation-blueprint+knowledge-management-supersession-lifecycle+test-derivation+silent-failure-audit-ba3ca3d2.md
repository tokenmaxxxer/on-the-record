---
issue: 3134
role: implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2
author: implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2
skills: implementation-blueprint (skill-repository(c05de12)), knowledge-management-supersession-lifecycle (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: a3d9b886af78073b857f847b5313bd6d234e0b2f
type: implementation-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: gh issue view 3134 --repo tokenmaxxxer/on-the-record (issue body)
    sha: same-commit
  - path: supersession.py
    sha: same-commit
  - path: docs/handbooks/record-contract.md
    sha: same-commit
---

# issue-3134 — implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2 record

## What was done

Added `amends: <path>#<section>` — a section-scoped correction primitive
alongside the existing whole-artifact `supersedes:` (issue #3050,
`supersession.py`) — with the discoverability enforcement the issue
names as the actual requirement, not the field. All four acceptance
checks pass:

canonical: `a3d9b886af78073b857f847b5313bd6d234e0b2f` (this commit, this
session's own work) — `amends.py`, `gates/amends_index.py`,
`gates/probe_amends_is_discoverable.py`,
`gates/probe_amends_fails_closed.py`, `tests/test_amends_resolution.py`,
`docs/specs/amends-index.md` added; `docs/handbooks/record-contract.md`
and `docs/handbooks/record-authoring.md` updated.

- `python3 -m pytest tests/test_amends_resolution.py -q` — derived:
  ran this command against `a3d9b886` — result: 19 passed (0 failed).
- `python3 gates/probe_amends_is_discoverable.py` — derived: ran this
  command against `a3d9b886` — result: exit 0, `ok`.
- `python3 gates/probe_amends_fails_closed.py` — derived: ran this
  command against `a3d9b886` — result: exit 0, `ok`, all four named
  cases (dangling target, missing section anchor, conflicting
  correctors, cycle) passed.
- `python3 -m pytest tests/ -q` — derived: ran this command against
  `a3d9b886` — result: 273 passed (254 pre-existing + 19 new), 2
  pre-existing unrelated warnings.

**`amends.py`** (repo root, domain layer, no filesystem/git access,
mirrors `supersession.py`'s own contract) —
`a3d9b886:amends.py:1-38` (module docstring, the discoverability
decision) and `a3d9b886:amends.py:76-147` (`resolve_amendments()`):
provides `render_amends_field()`, `parse_amends()`, `section_anchor()`
(heading-text normalizer), `extract_section_anchors()`, and
`resolve_amendments(records)` — the tree-content-only resolver
returning `amended` / `broken` / `missing_section` / `conflicts` /
`cycles`, each of the last four failing closed rather than picking a
winner.

**`gates/amends_index.py`** (infrastructure/interface layer) —
`a3d9b886:gates/amends_index.py:1-18` (module docstring) and
`a3d9b886:gates/amends_index.py:119-140` (`check()`): generates and
drift-checks `docs/specs/amends-index.md`, a cross-cutting index in the
`specs/` bucket (same shape as the existing
`docs/specs/reconciled-index.md` + `gates/spec_index.py` pair, outside
any single `docs/issue-<n>/` tree). `check()` fails closed on a missing
index (even with zero edges), a missing index with live edges present,
and a stale index that disagrees with what the tree's `amends:` edges
resolve to — derived: `python3 gates/amends_index.py` — result: `ok:
docs/specs/amends-index.md matches the tree's amends: edges`, exit 0.

**`gates/probe_amends_is_discoverable.py`** — builds the study-companion
PR #11 shape (target record's own Limitation section wrong, corrector
record amends it), confirms the target's raw content carries zero
signal in isolation, then confirms `docs/specs/amends-index.md` surfaces
the amendment and that `check()` refuses when it is missing/stale and
passes once regenerated — derived: `python3
gates/probe_amends_is_discoverable.py` — result: exit 0, `ok` (full
stdout includes `-- confirmed: A's own raw content has zero signal of
the amendment --`, `-- confirmed: check() refuses an unlinked amendment
--`, `-- confirmed: check() passes once the index is regenerated --`).
It fails against current main: `amends.py` does not exist there —
canonical: `git show main:amends.py` output — `fatal: path 'amends.py'
exists on disk, but not in 'main'` — so the probe's own `import amends`
raises `ModuleNotFoundError` before any assertion runs, an honest
failure not a staged one.

**`gates/probe_amends_fails_closed.py`** — the four degenerate cases the
issue names: dangling target, section anchor absent from the target's
own headings, two correctors conflicting on the same target#section,
and a cycle (A amends B, B amends A) — derived: `python3
gates/probe_amends_fails_closed.py` — result: exit 0, `ok`, each of the
four `case_*()` functions printed its own `ok:` line and none raised.

**`tests/test_amends_resolution.py`** — 19 cases derived: `python3 -m
pytest tests/test_amends_resolution.py -q` — result: `19 passed in
0.84s` (parse round-trip, anchor normalization, and
`resolve_amendments()` equivalence-partitioned over relationship-shape:
none / single / two-sections-same-target / dangling / missing-section /
conflict / cycle / `./`-path-variant), derived per the test-derivation
skill (see "Why").

**`docs/handbooks/record-contract.md`** — `a3d9b886:docs/handbooks/
record-contract.md` new "Amends" section (mirrors "Supersession",
cross-referenced both directions) stating the field, the resolver
contract, and the discoverability decision.

**`docs/handbooks/record-authoring.md`** — `a3d9b886:docs/handbooks/
record-authoring.md` "Correcting a prior session's record" now points
to `amends:` for section-scoped corrections instead of only naming the
gap.

**`docs/specs/amends-index.md`** — the generated index itself, checked
in — canonical: this session's own `python3 gates/amends_index.py
--update` run, then `git show a3d9b886:docs/specs/amends-index.md` —
currently empty (zero live `amends:` edges in this tree), per the
issue's own must-not against retrofitting the study-companion records.

## Why

**Discoverability decision.** The issue's own consult was explicit the
frontmatter field is not the fix — canonical: `gh issue view 3134
--repo tokenmaxxxer/on-the-record` body, the "Recommended shape" and
"Why the reader invariant is the crux" sections — `amends.py`'s module
docstring (`a3d9b886:amends.py:1-38`) carries the full reasoning,
summarized here. Three shapes were considered:

1. *Required backlink in the target record.* Rejected outright, not as
   a design trade-off: `board-gate.sh`'s write-set isolation pins a
   session to its own `docs/issue-<n>/` tree, and an `amends:` edge is
   by definition cross-issue — no write shape reaches the target,
   confirmed live in this same session (see "What did not work" below
   for the exact refusal text) — the same class of hard, mechanical
   refusal `supersession.py`'s own root-cause comment (issue #3050)
   documents for a peer session's record path. The `knowledge-
   management-supersession-lifecycle` skill's rule 4 ("the entry
   itself, not just the index, must carry the status") is the standard
   piece of general advice this violates — but it is advice for a
   system where editing the entry is *possible*; here it is not, so
   the skill's own rule 6 framing (file the disagreement explicitly
   rather than silently picking one) is the closer fit: state the
   rejection and why, rather than pretend the ADR-literature default
   applies unchanged.
2. *Generated cross-cutting index.* Adopted — `docs/specs/amends-
   index.md` / `gates/amends_index.py`, precedented by this repo's own
   `docs/specs/reconciled-index.md` / `gates/spec_index.py` pair
   (`a3d9b886:gates/spec_index.py`, read this session): a checked-in
   artifact outside any single issue's tree, so any session may
   regenerate it regardless of which issue it is scoped to.
3. *Gate refusal on an unlinked amendment.* Adopted on top of (2), not
   instead of it: an index nobody is required to keep synchronized is
   the "extra layer, same problem" failure the issue names. derived:
   `python3 gates/amends_index.py` on a tree with a live edge and no
   committed index — result (via
   `gates/probe_amends_is_discoverable.py`'s own temp-repo check,
   `a3d9b886:gates/probe_amends_is_discoverable.py:150-159`): refused
   with "an unlinked amendment", exactly matching `spec_index.py`'s own
   drift-refusal shape (`a3d9b886:gates/spec_index.py:39-58`).

Rejected explicitly, not by omission: a plain per-target note *inside*
the corrector's own record only (no index at all) — this is what
`supersedes:` already gives a reader for a superseded record (the
corrector's `supersedes:` line is enough because nothing should trust
the original anymore). It is insufficient for `amends:` specifically
*because* the target stays authoritative: a reader who never opens the
corrector's record has no path to the correction at all, which is
exactly the "target stays authoritative, so nothing makes a reader look
elsewhere" crux the issue names as the reason this primitive is harder
than `supersedes:`.

**Fails-closed design (`resolve_amendments`).** Ordering matters:
broken/missing_section are resolved before conflict detection (an edge
that cannot even resolve to a real target+section is not eligible to
conflict), and conflicts are excluded before cycle detection (two
correctors already fighting over one section is reported as a conflict,
not folded into a cycle report even if one of them also closes a loop)
— `a3d9b886:amends.py:76-147`. Cycle detection is plain DFS
colour-marking (white/gray/black) over the corrector→target graph,
independent of section anchor — `a3d9b886:amends.py:186-208`
(`_find_cyclic_paths`) — a cycle is a property of which records amend
which other records, not of which sections. All four fail-closed shapes
are exercised and confirmed: derived: `python3
gates/probe_amends_fails_closed.py` — result: exit 0, `ok`.

**`amends:` without a `#section` parses as no field, not a smaller
`amends:`.** `parse_amends()` returns `None` for a bare-path `amends:`
value rather than treating it as target-only
(`a3d9b886:amends.py:105-119`). A whole-record correction belongs to
`supersedes:`'s resolver; silently accepting it here would let it hide
from `supersession.resolve_authoritative()` entirely — derived: `python3
-m pytest tests/test_amends_resolution.py -q -k
test_field_without_section_returns_none` — result: 1 passed.

**Section anchors, not line ranges or hashes.** A GitHub-style heading
slug (lowercase, punctuation stripped, whitespace collapsed to `-`) is
the section identity, matching how a human names "the Limitation
section" and how the study-companion case is actually phrased in the
issue — canonical: `gh issue view 3134` body, "Both verifications graded
its record's Limitation section misleading". This does not solve
heading-rename drift (issue #3050's own "Partial supersession" section
named this as the reason it deferred section-level markers — canonical:
`docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-6eac66c0.md`,
lines 142-186, read this session) — a rename after the `amends:` edge is
written lands as `missing_section`, fails closed, and is surfaced in the
index's "Unresolved edges" table rather than silently resolving to the
wrong heading or silently vanishing — derived: `python3 -m pytest
tests/test_amends_resolution.py -q -k
test_missing_section_anchor_reported_not_amended` — result: 1 passed.

**Skill verdicts.**

skill-verdict: implementation-blueprint — applied: invoked; ran
`python3 <skill-dir>/scripts/prep.py classify --surface backend
--external no --logic rich --asynchronous no` (routed `domain-rich`),
then `recommend domain-rich --team 1` — derived: both commands run this
session, output captured in this session's own transcript. Domain-rich's
default module layout (domain/application/infrastructure/interface) was
collapsed per its own CONWAY line ("one owner — collapse elaborate
module boundaries") down to the two layers this task actually has:
`amends.py` (domain, pure) and `gates/amends_index.py`
(infrastructure+interface, the only layer with file I/O) — matching
`supersession.py`'s own already-established shape rather than inventing
new boundaries for a single-owner task.

skill-verdict: knowledge-management-supersession-lifecycle — applied:
invoked; consulted on whether `amends` is a distinct lifecycle state
from `superseded`/`deprecated` and what discoverability rule 4 implies.
Its rule 4 informed the rejection of a bare unlinked index (see
"Discoverability decision" above) and its rule 6 framing (file
disagreement explicitly) informed how the record states the
target-backlink rejection rather than eliding it.

skill-verdict: test-derivation — applied: invoked; confirmed the
equivalence-partitioning route over relationship-shape (same shape as
`test_supersession_shape.py`'s own prior derivation — canonical:
`a3d9b886:tests/test_supersession_shape.py:1-29` docstring, read this
session — one grain finer: target *and* section) and confirmed the
fails-closed/discoverability probes' case lists match the acceptance
section's own enumeration verbatim — canonical: `gh issue view 3134`
body, the `probe_amends_fails_closed.py` and
`probe_amends_is_discoverable.py` paragraphs.

skill-verdict: silent-failure-audit — applied: invoked; checked
`amends.py` (pure, no I/O, nothing to silently absorb) and
`gates/amends_index.py`'s three fallible paths (missing index, stale
index, file reads in `_load_records`) — none wrapped in try/except, all
propagate or explicitly fail closed. derived: `grep -n "except\|try:"
amends.py gates/amends_index.py` — result: no matches (empty output),
confirmed this session.

## What did not work

The generated index was first written to a top-level path, renamed
from that path to its final location before any commit: renamed from
`docs/amends-index.md` to `docs/specs/amends-index.md` (the `specs/`
bucket, matching `docs/specs/reconciled-index.md`'s own precedent) —
canonical: this session's own tool-result output — attempting to stage
the top-level path was refused by the `board-gate.sh` PreToolUse hook:
"docs/amends-index.md is neither docs/README.md, one of the six
standing buckets (_assets, decisions, handbooks, proposals, reports,
specs), nor an issue tree (docs/issue-<n>/)." The top-level path was
never committed at any point. Re-verified all four acceptance checks
after the rename — derived: `python3 -m pytest
tests/test_amends_resolution.py -q && python3
gates/probe_amends_is_discoverable.py && python3
gates/probe_amends_fails_closed.py && python3 -m pytest tests/ -q` —
result: all four passed after the rename, same as before it.

The first record write attempt (this file, before the code commit
existed) was refused by `record-claim-guard.sh` for uncited bare-count
and status claims, and for citing paths not yet in git history —
canonical: this session's own tool-result output naming issue #333,
#793, #870, and #1085. Resolved per `record-order.md`'s own guidance:
committed the code first (`a3d9b886`), then rewrote this record with
`derived:`/`canonical:` tags anchored to that commit.

## Upstream basis

canonical: `gh issue view 3134 --repo tokenmaxxxer/on-the-record` (this
session's own read, full body) — the acceptance section, the
must-nots, and the study-companion PR #11 repro this record's
discoverability probe models.

canonical: `a3d9b886:supersession.py` (this repo, landed issue #3050,
read this session) — the precedent this module mirrors:
`resolve_authoritative()`'s tree-content-only contract, `./`-path-
normalization handling, and the "two artifacts, not one" decision this
record extends one grain down.

canonical: `a3d9b886:gates/spec_index.py` +
`a3d9b886:docs/specs/reconciled-index.md` (this repo, landed issue
#336, read this session) — the precedent for a generated, cross-cutting,
drift-checked index living outside any single issue's write-set,
adopted as the discoverability mechanism.

derived: `python3 -m pytest tests/test_amends_resolution.py -q` —
result: 19 passed.

derived: `python3 gates/probe_amends_is_discoverable.py` — result: exit
0, `ok`.

derived: `python3 gates/probe_amends_fails_closed.py` — result: exit 0,
`ok`, all four cases pass.

derived: `python3 -m pytest tests/ -q` — result: 273 passed (254
pre-existing + 19 new), 2 pre-existing unrelated warnings
(`test_skill_candidates_floor.py` pinned-fixture-divergence, issue
#3019).

derived: `python3 -m pytest test/ -q` — result: 548 passed, 15 failed,
3 xfailed. All 15 failures are pre-existing and unrelated to this
change (`test_convention_equivalence.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_local_dependency_env.py`) — owned by issue #3091, reported
separately from `tests/`'s clean run per the spawning task's own
framing.

## Open findings

None.

## Next steps

`loop_state: landed`. Two items explicitly out of scope by the issue's
own must-nots, left for a future decision rather than attempted here:
retrofitting the two existing study-companion verification records into
live `amends:` edges (they predate the mechanism), and relaxing
`board-gate.sh`'s write-set isolation (it is correct and is the reason
this primitive exists).
