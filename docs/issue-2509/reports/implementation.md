---
issue: 2509
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gates/check_runner.py
    sha: fcf0b5b9d9394fd832aea7a8ebb121214ae89ca1
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
type: fix
breaking: false
verdict: pass
---

# issue-2509 — implementation record

## What was done

Fixed the residual `check_runner.py::_looks_like_path`/`parse_checks`
defect: a backticked token with a `/` was still read as "this path must
exist in the repo under review" even when the bullet's own text says the
token belongs somewhere else (an installed plugin's own directory, a
target/consumer repo's local layout). Before this fix, at
`fcf0b5b9d9394fd832aea7a8ebb121214ae89ca1:gates/check_runner.py:140-151`:
```python
def _looks_like_path(token: str) -> bool:
    if _ANGLE_PLACEHOLDER.search(token):
        return False
    if "/" in token:
        return True
    if token in _BARE_PATH_NAMES:
        return True
```
— any token containing `/` returns `True` unconditionally once the
angle-bracket-placeholder check (#2463) doesn't match, with no way to
tell "this path exists in the repo under review" apart from "this
bullet is describing a path that lives somewhere else."

Two additions to `gates/check_runner.py`:

1. `_FOREIGN_OWNER` — a regex for an explicit foreign-owner possessive
   ("installed plugin's", "target repo's", "another repo's", …)
   immediately (within a 60-char window) before the backtick. When
   present, the token classifies `judgment` instead of `file-existence`,
   regardless of its `/`-shape. The window is deliberately short so a
   foreign-owner phrase describing something else earlier in a long
   bullet can't leak forward onto an unrelated, later, genuinely-local
   path — pinned by
   `t_foreign_owner_phrase_far_from_the_backtick_does_not_leak_forward`.
   The noun list is narrow (`plugin`/`repo(sitory)` only, not
   `module`/`tool`/`project`/`package`) after a before-landing
   warrant-hunter pass found the wider list ambiguous; see "What did not
   work" for the reproduction and fix.
2. `_STATING_VERB_PREFIX` — a regex matching a bullet that opens with
   "state explicitly", "demonstrate live", or "document". When matched,
   `looks_like_command` is forced `False` so the bullet is never
   classified `test`, even when its backtick has command-token shape
   (e.g. `.claude/skills` reads the same as a `/`+`.`-shaped relative
   command path to the existing classifier).

A third, smaller fix rides along: the `file-existence` fallback now
requires `len(tokens) == 1`. Without it, a stating-verb bullet whose
backtick is a real multi-word command (e.g. `gates/check_runner.py
--skills`) would fall through to `_looks_like_path` on the *whole*
multi-word string and get "checked" for existence as one bogus literal
path — the token-count guard routes that shape to `judgment` instead.
canonical: gates/check_runner.py:227-266 (this session's diff)

Added 7 regression tests to `gates/test_check_runner.py` pinning: the
two live #2488 examples (installed-plugin `skills/`, target-repo
`.claude/skills`) each classify `judgment`; the foreign-owner window
doesn't leak across an unrelated later path in the same bullet; a
generic `module`/`tool`/`project`/`package` possessive does NOT
downgrade a real in-repo path (the narrowed-noun-list regression); a
`demonstrate live`/`document`-prefixed bullet never becomes `test`; and
a stating-verb bullet whose backtick genuinely is a real command is
unaffected.
canonical: gates/test_check_runner.py (new
`t_installed_plugin_owned_directory_classifies_as_judgment_not_file_existence`,
`t_target_repo_owned_path_classifies_as_judgment_not_file_existence`,
`t_foreign_owner_phrase_far_from_the_backtick_does_not_leak_forward`,
`t_generic_module_or_tool_possessive_does_not_downgrade_a_real_in_repo_path`,
`t_demonstrate_live_prefixed_bullet_never_classifies_as_test`,
`t_document_prefixed_bullet_never_classifies_as_test`,
`t_stating_verb_prefix_does_not_suppress_test_for_a_non_stating_bullet`)

## Why

Checking actual existence-on-disk to decide the classification type was
considered and rejected: it would make the classifier self-referential
and defeat the issue's own non-goal.
canonical: gh issue view 2509 (`## Non-goals`: "Do not make the
classifier permissive... an unrecognized shape must still fail closed
rather than pass silently"; Acceptance `must not:` line: "an
unrecognized shape must still land in judgment (refused), never in
'passed'"; and "must not: reclassify a bullet that does assert a real
in-repo path into judgment")
The only signal available at classification time that isn't
existence-based is textual: an explicit possessive naming a different
owner right next to the backtick. That is narrow by construction (a
fixed adjective+noun list, a short 60-char proximity window) so it only
fires on the shape #2488 actually hit, not on any bullet that merely
mentions a plugin or another repo somewhere in its prose.

## What did not work

The `_FOREIGN_OWNER` noun list first shipped (in this same session,
before this commit) as `plugin|repo(sitory)|project|package|tool|module`
— broader than #2488's live bullets ("installed plugin's", "target
repo's") actually needed. A before-landing warrant-hunter pass caught
that `module`/`tool`/`project`/`package` are ambiguous: a bullet phrased
"unlike another module's `x`, this repo's own `y`" can describe two
things both local to this repo, and the wider list would silently
downgrade a genuinely-missing in-repo path assertion to unenforced
`judgment` — exactly the non-goal violation cited above. Reproduced
live and fixed before ever landing: narrowed the noun list to
`plugin|repo(sitory)` only (the two nouns #2488's real bullets actually
used), and added
`t_generic_module_or_tool_possessive_does_not_downgrade_a_real_in_repo_path`
to pin the corrected boundary.
```
$ python3 -m pytest gates/test_check_runner.py -k t_generic_module_or_tool_possessive_does_not_downgrade_a_real_in_repo_path -q
1 passed in 2.74s
```
derived: `python3 -m pytest gates/test_check_runner.py -k t_generic_module_or_tool_possessive_does_not_downgrade_a_real_in_repo_path -q`

## Upstream basis

- `gates/check_runner.py` (sha `fcf0b5b9d9394fd832aea7a8ebb121214ae89ca1`,
  issue #2463's landed fix) — the angle-bracket-placeholder exclusion
  this issue's fix sits directly next to and follows the same shape for
  (a narrow, textually-scoped exclusion, not an existence check).
- Issue #2488 (PRs #2497/#2499/#2500) — source of the two live
  misclassified bullets fixed here, and of the "before" reproduction
  quoted under "Acceptance evidence" below.
  derived: gh pr view 2497 --json number,title,state,headRefName; gh pr
  view 2499 --json number,title,state,headRefName; gh pr view 2500
  --json number,title,state,headRefName
  ```
  {"headRefName":"issue-2488/implementation","number":2497,"state":"OPEN", ...}
  {"headRefName":"issue-2488/execution-observation","number":2499,"state":"OPEN", ...}
  {"headRefName":"issue-2488/conformance-review","number":2500,"state":"OPEN", ...}
  ```

## Acceptance evidence

Classification of the two live #2488 bullets, before vs. after this fix
— both re-derived directly from `gates.check_runner.parse_checks()`
against issue #2488's real Acceptance section text this session:

Before (original code, reproduced by `git stash` of this fix and
re-running the same probe):
```
[file-existence] "a skill name that exists only in an installed plugin's `skills/` (not in the skill-repository checko"
[test] 'state explicitly what trust distinction (if any) is applied between the curated skill-repository and'
```
After (this fix):
```
[judgment] "a skill name that exists only in an installed plugin's `skills/` (not in the skill-repository checko"
[judgment] 'state explicitly what trust distinction (if any) is applied between the curated skill-repository and'
```
derived: python3 /tmp/scratch_probe.py (script body: `check_runner.parse_checks()` called on issue #2488's Acceptance section, printing each check's classified `type`)

A genuine in-repo path (no foreign-owner possessive, no stating-verb
prefix) is unaffected:
```
$ python3 -m pytest gates/test_check_runner.py -k t_genuinely_missing_literal_path_without_placeholder_still_fails -q
1 passed in 0.79s
```
derived: python3 -m pytest gates/test_check_runner.py -k t_genuinely_missing_literal_path_without_placeholder_still_fails -q

**PRs #2497/#2499/#2500 (issue #2488) re-run under the fix**, calling
`gates/check_runner.py`'s own `parse_checks`/`run_checks` directly
against each PR's real head commit (via `checkout_pr_worktree`), without
calling `post_comment` — no comment was posted to any of the three live
PRs, since re-measuring their classification doesn't require writing to
them, and posting to PRs outside this issue's own delivery would be an
external side effect beyond this issue's scope.

Before (original code — stashed this fix, re-ran the identical
worktree-checkout script against all three live PR head commits):
```
=== PR #2497 (issue #2488) ===
## Acceptance check-runner result: 0/2 passed
- [FAIL] (file-existence) a skill name that exists only in an installed plugin's `skills/` ...
- [FAIL] (test) state explicitly what trust distinction (if any) is applied between the curated skill-repository and a target repo's local `.claude/skills` ...
```
(byte-identical `0/2 passed` output for PR #2499 and PR #2500 — same
issue #2488 body classified the same way against each PR's own head
commit.)
derived: python3 /tmp/rerun_check_runner.py (against gates/check_runner.py before this session's fix, via `git stash`)

After (this fix, same script, same three PR head commits):
```
=== PR #2497 (issue #2488) ===
classified: 0 mechanical, 5 judgment
## Acceptance check-runner result: no checks declared
```
(identical `no checks declared` output for PR #2499 and PR #2500.)
derived: python3 /tmp/rerun_check_runner.py (against gates/check_runner.py after this session's fix)

This is consistent with #2488's conformance-review's independent
five-Present finding (all five of #2488's Acceptance bullets are
live-demonstration/judgment criteria, none mechanically checkable): the
gate no longer manufactures a mechanical FAIL on requirements it cannot
evaluate — it reports the honest "no checks declared" result quoted
directly above, in place of the FAIL result quoted in the "Before"
block above it.

Full gates test suite, run after the fix (including the narrowed
`_FOREIGN_OWNER` noun list and its new regression test):
```
$ python3 -m pytest gates/ -q
1015 passed, 8 xfailed in 5.76s
```
derived: python3 -m pytest gates/ -q

`gates/test_check_runner.py` alone, both entry points:
```
$ python3 -m pytest gates/test_check_runner.py -q
45 passed in 1s
$ python3 gates/test_check_runner.py
38/38 passed
```
derived: python3 -m pytest gates/test_check_runner.py -q; python3 gates/test_check_runner.py

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; this record, all
commit messages, and the PR title/body are in English. The two new
regex comments added to `gates/check_runner.py` were written in Korean,
not English, as an explicit exception per the skill's own "match
surrounding style when editing next to existing Korean" guard — that
file's existing comments are close to 100% Korean prose, and adding
English comments next to them would have left it half-and-half, which
the skill explicitly warns against. Flagging per the skill's
project-convention-conflict rule.
other mounted skills: not triggered — implementation-blueprint (a
single-file classifier fix, no multi-module structure decision),
implementation-complexity-coupling-management,
implementation-design-pattern-selection, and
implementation-performance-data-structure-choice (no coupling/cohesion,
GoF-pattern, or data-structure/algorithm decision anywhere in this
delivery's scope).
