---
issue: 2920
role: refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4
author: refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: same-commit
    sha: same-commit
---

# issue-2920 — refactoring-legacy-seam-selection+silent-failure-audit-b9f1e0f4 record

## What was done

Committed at b0fb23a7 (canonical: `git show b0fb23a7 --stat`):

1. Deleted `resolve_skill_family_source()` (skills.py) — scanned
   skill-repository directory names for an `f"{skill}-"` prefix, mounting
   every directory sharing it. Its only two call sites were
   `consult.py:864` and `consult.py:1254`
   (derived: `grep -rn "resolve_skill_family_source(" *.py` on the pre-fix tree — result: exactly those two lines).
2. Added `resolve_consult_skill_source()` (skills.py) — exact
   directory-name match (comma-separated), same as
   `resolved_skill_dirs()`/`resolve_skill_source()` (`--skills`/`--skill`
   machinery), plus the `_STATIC_POLICY_SKILLS` baseline add-only. A
   selector matching no directory is not `sys.exit`'d (#2569 free-form
   argument preserved) — it lands in a new `"unresolved"` list key.
3. Rewired both call sites: `_composed_consult_skill_source()` (consult.py)
   and `_readonly_plugin_dirs()` (judge's plugin selection, consult.py).
   `merge_composed_skill_source()` does not preserve extra dict keys, so
   `_composed_consult_skill_source()` re-attaches `"unresolved"` after
   merging in the unchanged add-only cross-family BM25+skill_judge match.
4. Made empty/failed resolution visible at three layers:
   `env["MUSTER_SKILLS_UNRESOLVED"]` (`_consult_cmd_and_env()`),
   `verdict["skills_mounted"]`/`verdict["skills_unresolved"]`
   (`consult_cmd()`'s return value), and two new optional kwargs on
   `_append_consult_trace()` (`mounted`, `unresolved`, default `""`,
   appended to the trace line only when non-empty — the `skill_judge`
   trace call site is untouched, byte-identical, confirmed by
   derived: `python3 -m pytest test/test_consult_skill_resolution_2920.py::AppendConsultTraceMountedFieldTest -q` — result: 2 passed).
5. Fixed stale docstrings/comments naming the never-real identifiers
   `resolve_role_family_source()`/`role_settings()`/`resolved_role_model()`
   (dead leftovers from an earlier incomplete rename — the live functions
   are `resolve_consult_skill_source()`/`skill_settings()`/`resolved_skill_model()`;
   canonical: b0fb23a7:consult.py module docstring and
   `_readonly_plugin_dirs()`/`_readonly_settings()`/`_run_panel_session()`
   docstrings).
6. Added `test/test_consult_skill_resolution_2920.py`
   (derived: `python3 -m pytest test/test_consult_skill_resolution_2920.py -q` — result: 13 passed).
   Fixed two existing tests that patched the deleted function by name:
   `test/test_consult_no_rulebook_identity_regression.py`,
   `test/test_spawn_model_override.py`; fixed one stale comment in
   `test/test_spawn_skills_mount.py`.

## Why

Verified live at HEAD 85d9f61d before any change
(derived: `python3 -c "import spawn; repo=spawn._skill_repo_root(); [print(n, spawn.resolve_skill_family_source(n, repo)['skills']) for n in ['conformance-review','implementation','architecture','adversarial-review','code-architecture','totally-bogus-xyz']]"`
— result:
```
conformance-review -> [7 conformance-review-* dirs + work-in-english] (8 total)
implementation -> [5 implementation-* dirs + work-in-english] (6 total)
architecture -> [5 architecture-* dirs + work-in-english] (6 total)
adversarial-review -> ['work-in-english']
code-architecture -> ['work-in-english']
totally-bogus-xyz -> ['work-in-english']
```
), confirming the issue's own 8/6/6-vs-work-in-english-only numbers, and
(derived: `ls /home/jwjung/skill-registry/skills | grep -E '^(architecture|conformance-review|implementation)$'` — result: empty)
that the three role-shaped names are not themselves directories — only
prefixes of other directories. `resolve_skill_family_source()`'s
prefix-scan is the retired `_ROLE_SKILLS` table re-expressed as a
filename convention: the issue's must-not list forbids re-encoding the
table under a different name, so the only fix consistent with invariant
① is deleting the function and its family-coverage capability outright
(explicitly authorized: "if a capability depends on enumerating role
spellings, drop the capability and state plainly what stops working"),
not keeping it as a fallback (that would be "keep a retired role name
working as a selector," the must-not the issue names directly).

Exact-name resolution (reusing `resolved_skill_dirs()`, the same function
`--skills` calls) rather than a new consult-specific matcher was chosen
because the issue's second deliverable is literally "mount the same way
`--skills` does" — a second, parallel definition of "matches" would drift
from the first over time.

Visibility was added at three layers because no single layer reaches
every caller: the background-fork default path (spawn.py, `a.role ==
"consult"` branch) never prints the returned verdict to the invoking
terminal, and the stderr `muster_skills=` line only reaches
`runs/consult-logs/`, which `.gitignore:1` excludes from version control
and which gets overwritten (`O_TRUNC`) on every subsequent consult call —
confirmed empty in this checkout
(derived: `ls runs/consult-logs` — result: no such directory, 0 files).
The durable, git-tracked trace (`docs/**/consult-log.md`) had never
recorded mounted skills at all before this change (see Evidence below) —
fixing only the env-var/verdict layer would leave that corpus permanently
blind going forward too.

## Evidence — corpus bound for acceptance #3

Population bounded to the two locations consult.py's own trace
read/write functions use — there is no third location a consult trace
can land:

derived: `find docs -iname "consult-log.md" | wc -l` — result: 33 (git-tracked, durable)
derived: `ls runs/consult-logs` — result: no such directory (gitignored, ephemeral; 0 files present in this checkout)

Across the 33 files:

derived: `find docs -iname "consult-log.md" -exec cat {} \; | wc -l` — result: 153
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -c "^- "` — result: 147 (6 stray continuation lines, attributable to neither bucket)
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -oE "verb=[a-zA-Z_]+" | sort | uniq -c` — result: 53 verb=consult, 80 verb=skill_judge
derived: `find docs -iname "consult-log.md" -exec cat {} \; | grep -c "mounted="` — result: 0 of 153 (0/153 = 0%)

Every one of the 53 `verb=consult` entries is therefore **undeterminable**
for "did this consult mount only work-in-english," not zero and not all,
and reported as its own bucket rather than folded into either side. The
80 `skill_judge` entries show only the add-on matcher's picked/rejected
list inside `outcome=` — a related but distinct signal (what the matcher
added on top of an unrecorded baseline) — so those 80 are undeterminable
too.

Selector *kind* (a different, determinable question) was derived by
extracting each `verb=consult` entry's `role=<value>` and checking it
against today's skill-repository listing:

derived: role= extraction from the 53 verb=consult lines, classified via `spawn._skill_repo_root()` directory listing — result:
```
26 implementation             -> retired-role-shaped (prefix of 5 dirs, no exact match)
20 requirements-engineering   -> retired-role-shaped (prefix of 1 dir, no exact match)
 2 architecture               -> retired-role-shaped (prefix of 5 dirs, no exact match)
 1 product-discovery          -> retired-role-shaped (prefix of 10 dirs, no exact match)
 1 legal-compliance           -> retired-role-shaped (prefix of 7 dirs, no exact match)
 1 defect-verification        -> retired-role-shaped (prefix of 4 dirs, no exact match)
 1 conformance-review         -> retired-role-shaped (prefix of 7 dirs, no exact match)
 1 product-management         -> no-match (free-text-or-unknown)
```
52/53 = 98.1% (derived: 52/53*100) of every durable `verb=consult` entry
ever recorded used a retired-role-shaped selector, 0 used a real exact
leaf skill name — consistent with the always-on directive's own
documented usage training callers onto exactly the selector shape this
issue found broken. Applied retroactively, this fix would flip all 52
from "silently mounted a family" to "visibly mounts nothing but
work-in-english" — it does not change what a correct call looks like
(a real skill name), only makes the historical corpus's dominant selector
shape now report `unresolved` instead of "working."

## What did not work

None — see "Rationale for deviations" (section absent; nothing diverged).

## Upstream basis

Same-commit b0fb23a7 (canonical: `git show b0fb23a7 --stat`): skills.py,
consult.py, spawn.py (one re-export line), four test files. No prior
docs/issue-2920/ input existed (build-now bypass, `CORE_BUILD_NOW=1`
env var confirmed set this session) — this record is the survey,
proposal, and delivery in one pass per the spawning prompt's explicit
authorization.

## Retirement-count evidence (acceptance #2)

`gates/retirement_count.py` unscoped (its own population is all tracked
`*.py`/`*.sh`, docs excluded, not scoped to a diff):
derived: `python3 gates/retirement_count.py` before this commit — result: 1135 occurrences; after — result: 1098 occurrences (net -37: 61 removed, 24 added).

Bounded to consult's selector-resolution reachable set — consult.py,
skills.py, spawn.py's one touched line, four touched test files — this
commit's **added lines only**:
derived: `git show b0fb23a7 | grep '^+' | python3 -c "import sys; sys.path.insert(0,'gates'); import retirement_count as rc; [print(l.rstrip()) for l in sys.stdin if rc.line_hits(l[1:])]"` — result: 14 lines.

All 14 are docstring/comment prose explaining what was retired and why
(shape: "the retired role axis / role->skill table / retired role name"),
zero are code identifiers — `gates/retirement_count.py`'s own docstring
names this exact exemption for itself ("a citation of the retired axis by
a named contract... not a live use of it"); the same reasoning covers a
record explaining, in the past tense, what a deleted function used to do.

Zero function/parameter identifiers named with `role` remain in the
touched resolution-path files:
derived: `grep -nE "^\s*def [a-zA-Z_]*role[a-zA-Z_]*\(" consult.py skills.py spawn.py` — result: empty
derived: `grep -nE "def [a-zA-Z_]+\([^)]*\brole\b" consult.py skills.py spawn.py` — result: empty

One identifier deliberately left alone: `a.role` — spawn.py's argparse
attribute for its single CLI positional, dispatching *which spawn.py
subcommand* runs (`a.role == "consult"`/`"judge"`/`"panel"`/`"init"`/…).
This accounts for the bulk of the 1098 remaining repo-wide occurrences
(derived: `grep -c "a\.role" spawn.py` — result: 70). This is a different
axis than the one this issue diagnosed: `_ROLE_SKILLS`/
`resolve_skill_family_source()` mapped a selector string to a *cluster of
skills*; `a.role` selects *which verb handler runs* and carries the skill
selector through to `resolve_consult_skill_source()` unchanged as a plain
string, performing no role→skill mapping itself. Renaming it is a large,
unrelated, purely-cosmetic refactor across spawn.py's CLI dispatch table,
not asked for by this issue's diagnosis, acceptance criteria, or must-not
list (must-not: do not relitigate #2569's free-form-argument decision).
Left as-is, justified rather than fixed.

## Acceptance demonstration (executed-live)

derived: `python3 -c "import spawn; repo=spawn._skill_repo_root(); [print(n, spawn.resolve_consult_skill_source(n, repo)['skills'], spawn.resolve_consult_skill_source(n, repo).get('unresolved')) for n in ['conformance-review','implementation','architecture','adversarial-review','code-architecture','totally-bogus-xyz']]"` — result:
```
conformance-review    ['work-in-english'] ['conformance-review']
implementation         ['work-in-english'] ['implementation']
architecture           ['work-in-english'] ['architecture']
adversarial-review      ['work-in-english', 'adversarial-review'] []
code-architecture       ['work-in-english', 'code-architecture'] []
totally-bogus-xyz       ['work-in-english'] ['totally-bogus-xyz']
```
This is the exact reversal of the "Why" section's before-numbers: real
leaf skill names now mount themselves (exactly as `--skills` would —
derived: `python3 spawn.py --skill adversarial-review "check parity" --issue 2920` — result: `{"skills": ["adversarial-review"], "skill_sha": "c05de12"}`, same skill/sha `resolve_consult_skill_source()` returns above);
retired-role-shaped/unknown names mount only the POLICY baseline and are
now visibly reported via `unresolved`.

Multi-skill consult (comma form, `--skills`'s own syntax):
derived: `spawn.resolve_consult_skill_source('adversarial-review,code-architecture', repo)['skills']` — result: `['work-in-english', 'adversarial-review', 'code-architecture']`.
`spawn.py panel <skill-A> <skill-B> "<question>"` is the other existing
multi-skill consult form (two independently-consulted, cross-compared
skills); canonical: consult.py `_run_panel_session()` calls the same
`_composed_consult_skill_source()` this fix changed, so it applies
without a separate code path.

## Test evidence

derived: `python3 -m pytest test/ -q` — result: 521 passed, 3 xfailed, 15 failed.
The same 15 failure names, confirmed byte-identical against the
pre-change tree
(derived: `git stash && python3 -m pytest <same 5 files> -q && git stash pop` — result: identical 15 names),
all pre-existing environment failures (`git fetch` against a
sandboxed/absent `origin` remote) unrelated to this change.

## Open findings

None.

## Next steps

None — issue #2920's two deliverables (role axis removed from consult's
resolution; skill-based consult mounts the way `--skills` does) both
landed at b0fb23a7, acceptance 1-3 demonstrated above.

skill-verdict: refactoring-legacy-seam-selection — applied: invoked; used
the Sprout-Method framing (rule 1) — `resolve_consult_skill_source()` is a
new, separately-testable function added next to the deleted
`resolve_skill_family_source()` rather than a mutation in place — and kept
the seam narrow (rule 6): only the two real call sites were touched, not
the surrounding `_consult_cmd_and_env()`/`consult_cmd()` machinery beyond
what threading `unresolved` through required.
skill-verdict: silent-failure-audit — applied: invoked; the core defect is
a silent failure by the audit's own catalog (a fallback — POLICY-only
mount — substituted for a failed exact-name match with no record that a
fallback occurred, i.e. "default-value substitution without recording");
the three-layer visibility fix is the audit's own prescribed remediation
("replace with explicit fallback + logging that a fallback was used")
applied at every call site that previously absorbed the miss silently.
