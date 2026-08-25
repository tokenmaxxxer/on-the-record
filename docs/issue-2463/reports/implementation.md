---
issue: 2463
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
type: fix
breaking: "none — the exclusion only narrows classification from file-existence to judgment for backtick tokens containing a `<...>` angle-bracket placeholder; every other classification path (test/grep/artifact-smoke/measurement-language/bare-path/dotfile/compound-command) is untouched, pinned by the full existing test suite staying green"
verdict: pass
---

# issue-2463 — implementation record

## What was done

Hardened `gates/check_runner.py`'s `_looks_like_path()` (called from
`parse_checks()`'s classifier) to exclude backticked tokens that contain an
angle-bracket placeholder (`<n>`, `<role>`, `<...>`) from `file-existence`
classification, regardless of whether the token also contains `/`. A new
module-level `_ANGLE_PLACEHOLDER = re.compile(r"<[^\s<>]+>")` regex is
checked first inside `_looks_like_path()`; a match short-circuits to
`False`, which routes the caller through the existing `judgment` default
already present in `parse_checks()` — no new branch needed there.

This delivers recommendation (1) from the issue's requirements-engineering
consult only. Recommendation (2) (verb-based imperative-vs-descriptive
branching) is out of scope: the issue's "What" section names only the
angle-bracket exclusion. Recommendation (3) (a WARN tier for ambiguous
cases) is addressed by an explicit deferral statement below, per
Acceptance bullet 4.

Added regression tests to `gates/test_check_runner.py` (the module already
holds the `_looks_like_path` classifier's test suite for the #2278/#2313/
#2233 hardening this extends):
- `t_angle_bracket_placeholder_path_classifies_as_judgment_not_file_existence`
  — pins the exact issue #2402 Acceptance bullet text that produced two of
  this session's 9 misclassifications.
- `t_angle_bracket_placeholder_variants_all_classify_as_judgment` — three
  more placeholder shapes (`issue-<n>`, `issue-<n>/<role>/notes`,
  `<role>/<n>`).
- `t_genuinely_missing_literal_path_without_placeholder_still_fails` —
  regression fixture: a real `/`-shaped path with no placeholder still
  classifies `file-existence`, and `run_checks()` still reports its
  outcome as a genuine miss against an empty tempdir.
- pre-existing `t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails`
  and `t_bare_conventional_filename_and_dotfile_still_classify_as_file_existence_and_fail`
  continue to pin the non-placeholder classification outcomes unchanged.

**WARN-tier statement (Acceptance bullet 4):** explicitly deferred, not
implemented, for this delivery. The issue's own "What" section scopes this
fix to the single exclusion rule described above; the WARN tier is the
consult's third recommendation, aimed at a separate genuinely-ambiguous
middle case that this issue's 9 observed misclassifications don't
exhibit — every one of them was an unambiguous placeholder mention, not a
borderline case needing human judgment to disambiguate. Introducing a
third check-result vocabulary entry alongside the two that exist today
would reach into `run_checks()`'s result shape, `format_comment()`'s
summary-count arithmetic, and `merge_gate.py`'s evaluation logic — a
materially larger, cross-cutting change with open design questions of its
own (how a third status interacts with merge-gate evaluation and the
summary count) that the issue's own `design-research-skip: mechanical`
framing does not cover. Deferring it keeps this delivery the same shape as
the #2278/#2313/#2233 precedents it extends: one narrow exclusion rule, no
new check-result vocabulary.

## Why

The defect is the same class as #2278 (bare non-path identifiers wrongly
defaulted to file-existence), #2313 (compound commands classified by the
whole string instead of the executed final segment), and #2233 (bare `.py`
gate paths executed instead of run through pytest): a classifier heuristic
in `_looks_like_path()` fires on text that merely *resembles* a path.
Here, a backticked token like `` `issue-<n>/<role>` `` contains a literal
`/`, so the pre-fix `_looks_like_path()` returned `True` unconditionally —
but the token is a naming-convention description, not an assertion that a
file at that literal path exists. A literal path segment `issue-<n>`
(containing the byte string `<n>`) can never exist on disk, so this
misclassification isn't a rare edge case — it mechanically misfires every
single time it's reached. It hit 9 times this session, twice on issue
#2402's own genuine Acceptance text (behind PRs #2446, #2456) — text the
orchestrator did not author, which is why this is a gate defect and not an
authoring-quality issue.

The fix sits inside `_looks_like_path()` itself (checked first, before the
`/` check) rather than as a separate branch in `parse_checks()`, because
`_looks_like_path()` has exactly one caller (line 201) and every other
classification path (`looks_like_command`, `_MEASUREMENT_LANGUAGE`,
`_artifact_touched`) runs before it or independently of it — narrowing the
function's own contract ("does this token look like a real path") is the
minimal-surface-area change, and matches this repo's established pattern
of hardening the classifier function itself rather than adding call-site
special cases (see the #2278/#2313 comments in the same file).

## What did not work

None.

## Upstream basis

None — self-contained bugfix, no upstream proposal or design doc. The
issue's own `design-research-skip: mechanical` note states it extends the
existing classifier-hardening pattern (#2278/#2313/#2233) with one more
exclusion rule, and delivery ran under the build-now bypass
(`CORE_BUILD_NOW=1`), which skips the proposal round for this session.

## Acceptance evidence (executed live, this session, 2026-08-26)

**Bullet 1 — synthetic fixture, before/after, reproducing the 9-case pattern:**

canonical:
```
$ python3 gates/test_check_runner.py
...
ok - t_angle_bracket_placeholder_path_classifies_as_judgment_not_file_existence
ok - t_angle_bracket_placeholder_variants_all_classify_as_judgment
...
31/31 passed
```

Before/after comparison, run against the exact issue #2402 Acceptance
bullet text that produced 2 of the 9 real misclassifications (loaded the
pre-fix `gates/check_runner.py` via `git show HEAD:gates/check_runner.py`
into a separate module, classified the identical section string through
both the pre-fix and post-fix module):

canonical:
```
BEFORE fix: ['file-existence']
AFTER  fix: ['judgment']
BEFORE fix run_checks() output: status=fail, "issue-<n>/<role> missing"
```

**Bullet 2 — regression fixture, genuinely nonexistent literal path:**

canonical:
```
$ python3 gates/test_check_runner.py
...
ok - t_genuinely_missing_literal_path_without_placeholder_still_fails
ok - t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails
ok - t_bare_conventional_filename_and_dotfile_still_classify_as_file_existence_and_fail
...
31/31 passed
```

`section = "the report lands at \`reports/genuinely-missing-report\`"`
classifies as `file-existence`; `run_checks()` against an empty tempdir
reports `status: "fail"` — confirming the placeholder exclusion did not
disable the check for tokens without a placeholder.

**Bullet 3 — live re-classification against issue #2402's real Acceptance
section** (the issue whose text produced the misclassifications behind
PRs #2446 and #2456; `check_runner` classifies at issue-body granularity
via `_acceptance_section()` — the same section text is what actually ran
against PRs #2446/#2456/#2461, since there is no per-PR variant of the
issue's Acceptance text):

canonical:
```
$ gh issue view 2402 --repo tokenmaxxxer/on-the-record --json body -q .body \
    > /tmp/issue_2402_body.txt

=== BEFORE fix (HEAD) — issue #2402 Acceptance classification ===
file-existence | there is a supported way to recut a corrupted branch's content that remains mapped to its `issue-<n>/<role>` subject...
judgment       | `board-sweep`'s subject-mapping recognizes branches produced by that path...
judgment       | a role whose delivery landed via a recut branch is NOT re-spawned...
judgment       | if the chosen approach leaves any unmapped-branch case...

=== AFTER fix (current tree) — issue #2402 Acceptance classification ===
judgment | there is a supported way to recut a corrupted branch's content that remains mapped to its `issue-<n>/<role>` subject...
judgment | `board-sweep`'s subject-mapping recognizes branches produced by that path...
judgment | a role whose delivery landed via a recut branch is NOT re-spawned...
judgment | if the chosen approach leaves any unmapped-branch case...
```

The previously-misclassified bullet (`file-existence`, which mechanically
FAILed since `issue-<n>/<role>` never exists on disk) now reads `judgment`
— outside check_runner's mechanical scope, matching the other three
descriptive bullets in the same Acceptance section, instead of a false
FAIL.

**Bullet 4 — WARN-tier statement:** deferred; reasoning is stated in full
under "What was done" above.

**Full regression sweep — confirming no other classification path shifted:**

canonical:
```
$ python3 -m pytest gates/test_check_runner.py -q
38 passed in 1.56s

$ python3 -m pytest gates/ -q
1006 passed, 8 xfailed in 5.06s
```

## Open findings

None.

## Next steps

None — terminal (`loop_state: landed`).

skill-verdict: work-in-english — applied: invoked; code comments adjacent
to existing Korean file style kept Korean per the skill's own
project-convention-conflict guard, while new test names/docstrings, the
commit message, PR title/body, and this record's prose are written in
English; this chat's final summary is written in Korean per the skill's
routing rule.
skill-verdict: implementation-blueprint — not-applicable: single-function
classifier hardening inside one existing module, no multi-module structure
decision — the skill's own scope note excludes a one-line mechanical
extension of an established pattern.
skill-verdict: implementation-complexity-coupling-management — not-applicable:
no coupling/cohesion metric, accessor chain, cross-module import direction,
or check-pipeline ordering decision — a single regex exclusion inside an
existing classifier function.
skill-verdict: implementation-design-pattern-selection — not-applicable: no
GoF-pattern introduction/removal decision — a regex guard, not an
abstraction.
skill-verdict: implementation-performance-data-structure-choice — not-applicable:
no data-structure/algorithm/communication-scheme choice — a single
`re.search` call on an already-tokenized string, same cost class as the
checks it sits beside.
