---
issue: 3182
role: silent-failure-audit+implementation-blueprint+test-derivation-b63078f1
author: silent-failure-audit+implementation-blueprint+test-derivation-b63078f1
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - scripts/preflight/consumer_preconditions.py
  - tests/test_issue_3182_preflight.py
  - tests/test_issue_3182_citation_line_accuracy.py
type: repair
breaking: false
verdict: Both defects the third independent verification found on PR #3184's round 3 are fixed. check_workspace_disk_headroom()'s os.statvfs() branch now reports unsatisfied (naming the inode headroom as unobservable) instead of satisfied=True when the observation itself fails; every other precondition check was swept for the same shape and none had it. The citation-accuracy test now tokenizes .py citations and quote-aware-strips shell comments before matching, so it rejects a comment or docstring mentioning the target text instead of passing on raw substring containment; the discrimination is proved both ways with synthetic fixtures, and all 16 real line_anchors still pass. Nothing the prior round's verifications graded Present was touched.
loop_state: done
upstream:
  - path: docs/issue-3182/reports/implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf.md
    sha: 25176d39b6ea54154064fe00f1d9059d912371fc
  - path: scripts/preflight/consumer_preconditions.py
    sha: 25176d39b6ea54154064fe00f1d9059d912371fc
  - path: tests/test_issue_3182_citation_line_accuracy.py
    sha: 25176d39b6ea54154064fe00f1d9059d912371fc
  - path: tests/test_issue_3182_preflight.py
    sha: 25176d39b6ea54154064fe00f1d9059d912371fc
---

# issue-3182 — silent-failure-audit+implementation-blueprint+test-derivation-b63078f1 record

## What was done

canonical: `gh pr view 3184` — `headRefName`
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
`state: OPEN`. This is round 4 on that PR. The spawning brief named two
defects the round-3 verification found and asked for a sweep alongside
the named fix.

### Defect 1 — `os.statvfs()` observation failure silently reported `satisfied: true`

derived: `git show 25176d39:scripts/preflight/consumer_preconditions.py | sed -n '208,215p'`
(pre-fix state) showed:

```python
    try:
        st = os.statvfs(probe)
        free_inodes = st.f_favail
    except (OSError, AttributeError):
        return True, f"{usage.free // (1024 * 1024)}MB free at {probe} (inode count unavailable)"
```

`check_workspace_disk_headroom()` had already run `shutil.disk_usage()`
successfully (bytes headroom confirmed), then called `os.statvfs()` for
the inode half. If that second call raised, the function returned
`True` — the inode check never ran, but the whole precondition still
reported satisfied. This inverts the module's own stated contract
(`scripts/preflight/consumer_preconditions.py:9-13`, derived: `sed -n
'9,13p' scripts/preflight/consumer_preconditions.py`):

```
It never asserts
a precondition it did not actually check: if a check cannot run (binary
missing, subprocess failure, permission error, or a precondition whose
outcome would require a mutating action to observe), the precondition is
reported `satisfied: false`, never guessed `true`.
```

Silent-failure-audit trace (Silently Absorbed → now Handled): site
`scripts/preflight/consumer_preconditions.py:213` (`except (OSError,
AttributeError):`) → returned `(True, "...inode count unavailable")` →
caller (`run_checks()`) recorded `satisfied: true` for
`workspace_disk_headroom` → downstream consequence: an operator reading
the preflight's report (or its exit code) sees the precondition met and
proceeds, with no indication the inode headroom was never actually
checked. Fixed at `scripts/preflight/consumer_preconditions.py:210-220`:
the except branch now returns `(False, "...but inode headroom could not
be observed: <ExceptionType>: <message>")`, naming exactly what could
not be observed. `shutil.disk_usage()`'s sibling except branch
(`:200-203`) was already correct (returns `False` on `OSError`) and is
now locked in by a regression test too.

### Sweep — every other precondition check, for the same shape

derived: `git grep -n "except" scripts/preflight/consumer_preconditions.py`
→

```
scripts/preflight/consumer_preconditions.py:68:    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any
scripts/preflight/consumer_preconditions.py:157:        except OSError:
scripts/preflight/consumer_preconditions.py:202:    except OSError as exc:
scripts/preflight/consumer_preconditions.py:213:    except (OSError, AttributeError) as exc:
scripts/preflight/consumer_preconditions.py:389:        except Exception as exc:  # noqa: BLE001 -- a check must never
```

Exactly 5 `except` sites in the module (the fifth, `:213`, is the fix
above, already re-verified post-fix). Classified each (silent-failure-audit
enumerate-then-classify procedure):

- `:68`, `_run_readonly()`: `except Exception` → returns `(-1, "",
  "<type>: <msg>")`. Every caller treats `rc != 0` (including `-1`) as
  failure. **Handled.**
- `:157`, `check_skill_repository_resolvable()`: `except OSError:
  continue` inside a candidate loop — skips one candidate, falls through
  to the next; if every candidate raises or fails to match, the loop
  exits and the function's own final `return False, ...` fires.
  **Handled** — the `continue` never masks a final unsatisfied verdict.
- `:202`, `check_workspace_disk_headroom()`'s `shutil.disk_usage()`
  branch: `except OSError` → `False`. **Handled**, already correct
  pre-fix.
- `:213`, the same function's `os.statvfs()` branch: **was Silently
  Absorbed** (defect 1 above) — now **Handled**.
- `:389`, `run_checks()`: `except Exception` around each check's `fn()`
  call → `ok, detail = False, f"check raised {type}: {exc}"`.
  **Handled** — the module's own outer safety net.

Sweep result, derived from the `git grep` output and classification
above: every `except` site in the file other than the one named defect
was already Handled — no second Silently-Absorbed site exists.

Regression coverage added to `tests/test_issue_3182_preflight.py`
(`WorkspaceDiskHeadroomObservationFailureTest`, imports the module
directly via `importlib.util` so `os.statvfs`/`shutil.disk_usage` can be
monkeypatched, which the existing subprocess-driven tests in that file
cannot do):

- `test_statvfs_failure_reports_unsatisfied_naming_what_failed`: fakes
  `shutil.disk_usage` to succeed and `os.statvfs` to raise `OSError`;
  asserts `satisfied is False` and the detail names "inode". Verified
  this test fails against the pre-fix code — `derived: git stash push --
  scripts/preflight/consumer_preconditions.py && python3 -m pytest
  tests/test_issue_3182_preflight.py -q -k statvfs_failure ; git stash
  pop`:

  ```
  E       AssertionError: True is not false : os.statvfs() raising must report unsatisfied, got detail='10240MB free at ... (inode count unavailable)'
  1 failed in 0.80s
  ```

  — then confirmed it passes again after `git stash pop` restored the
  fix.
- `test_disk_usage_failure_still_reports_unsatisfied`: locks in the
  sibling branch (`:202` above) that was already correct, so a future
  edit can't regress it while touching the statvfs branch.
- `test_statvfs_success_with_ample_headroom_reports_satisfied`: fakes
  both calls to succeed with ample headroom; asserts `satisfied is
  True` — the positive case, so a fix that over-corrects to
  always-unsatisfied is also caught.

### Defect 2 — citation test matched by raw substring containment

derived: `git show 25176d39:tests/test_issue_3182_citation_line_accuracy.py | sed -n '53,69p'`
(pre-fix) — line 64: `if expected not in actual:` where `actual =
_line(cited_path, lineno)` was the cited line's raw text, unfiltered. An
anchor whose `lineno` pointed at a comment, or at a string literal that
merely mentions the call in prose, would still satisfy `expected in
actual` and pass — including this very script's own docstrings, which
quote `os.statvfs()`/`shutil.disk_usage()`/`sys.exit()` verbatim
(canonical: `scripts/preflight/consumer_preconditions.py:9-37` module
docstring and `:187-194` `check_workspace_disk_headroom` docstring, both
of which contain those exact call texts in prose). The test is the only
mechanical guard against citation drift — canonical: round 3's commit
message (`git log --format=%B -1 ca03582c`) states "5 of the 9 source
citations pointed a few lines away from the call they named" — so a hole
in the guard itself matters more than an ordinary test gap.

Fixed in `tests/test_issue_3182_citation_line_accuracy.py`:
`_line_is_code_match(path, lineno, expected)` now checks containment
against `_code_only_line()`, not the raw line:

- `.py` files: `tokenize.tokenize()` (stdlib, not text heuristics) masks
  out every `COMMENT` token, plus every `STRING` token that forms a bare
  statement by itself (the token immediately before and after it, in the
  significant-token stream, is a `NEWLINE` or start/end of file) — the
  exact shape of a module/class/function docstring or any standalone
  string-literal statement. A `STRING` token that participates in a real
  expression (a list element, a call argument — e.g. `cmd = ["claude",
  ...]`, the actual citation at `pipeline.py:661`) is left untouched,
  since that string is genuinely part of the cited code, not prose about
  it.
- The one non-`.py` citation (`on-the-record/hooks/git-push-guard.sh`)
  gets a quote-aware `#`-strip: a `#` inside a single- or double-quoted
  string is not treated as a comment start.

Proved the discrimination both ways in
`CitationCommentAndStringDiscriminationTest` (synthetic fixtures, not
the real cited files, so the proof doesn't depend on the repo's actual
line numbers) — derived: `python3 -m pytest
tests/test_issue_3182_citation_line_accuracy.py -q`:

```
..........                                                               [100%]
10 passed in 0.93s
```

- `test_python_comment_line_is_rejected`: a full-line `#` comment
  mentioning `os.fork()` → rejected; the real call two lines later →
  still matches.
- `test_python_trailing_comment_is_rejected`: `y = 2  # os.fork()
  mentioned here, not called` → rejected.
- `test_python_docstring_mention_is_rejected`: a module docstring and a
  function docstring, each mentioning `os.fork()` in prose → both
  rejected; the real call → still matches.
- `test_python_string_literal_that_is_real_code_still_matches`: guards
  against an over-broad fix that excludes every string —
  `cmd = ["claude", "-p", ...]` (mirrors the real `pipeline.py:661`
  citation) → still matches, since it's real code, not prose.
- `test_shell_comment_line_is_rejected` /
  `test_shell_hash_inside_quotes_is_not_treated_as_comment`: same
  comment-vs-code proof, and the inverse guard (a `#` inside a quoted
  shell string is not mistaken for a comment start), for the `.sh`
  citation path.
- `test_all_sixteen_real_anchors_still_pass` and
  `test_every_cited_line_contains_the_call_it_claims` (existing test,
  now routed through the same discriminating matcher): both assert
  `anchor_count == 16` derived by summing `len(check["line_anchors"])`
  across all `CHECKS` entries at runtime (2+2+1+1+1+1+1+1+2+4 = 16 by
  the `CHECKS` list authored in this same file), not a hardcoded belief
  — a silently-dropped anchor would fail the count assertion instead of
  the loop simply iterating fewer times unnoticed.

## Why

The build-now bypass (`CORE_BUILD_NOW=1`, spawner-set,
`checked: printenv CORE_BUILD_NOW — result: 1`) authorizes delivering
straight to PR #3184's branch without a proposal round; both fixes are
narrow, targeted at the exact defects the brief named plus the sweep it
explicitly asked for, with no unrelated refactor. Kept the existing
module structure (one `except` branch per fix site) rather than
introducing a shared "observation failure" helper across the two
distinct call sites (`shutil.disk_usage` vs `os.statvfs`) — the two
branches have different messages and different exception types worth
keeping separately readable, and there are only two of them.

For defect 2, considered excluding *all* string literals from matching
(simpler to implement) instead of only bare-statement strings, but
rejected it: two of the 16 real anchors (`pipeline.py:661` — `cmd =
["claude"`, and `on-the-record/hooks/git-push-guard.sh:341` — the
`deny(...)` remedy string) cite text that lives inside a string literal
that *is* the actual code being pointed at, not prose mentioning it.
Excluding all strings would have broken those two real citations while
fixing the defect — acceptance: `python3 -m pytest
tests/test_issue_3182_citation_line_accuracy.py -q -k
test_python_string_literal_that_is_real_code_still_matches` — result:

```
.                                                                        [100%]
1 passed in 0.82s
```

## Upstream basis

- `docs/issue-3182/reports/implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf.md`
  (sha `25176d39b6ea54154064fe00f1d9059d912371fc`) — round 3's own
  record, read for the pre-existing `CHECKS`/citation structure this
  round builds on.
- The spawning brief's defect descriptions (the round-3 verification's
  findings, quoted in the brief, including the `os.statvfs` monkeypatch
  reproduction detail) — this round did not re-fetch that verification's
  PR from GitHub; the brief already carried the reproduction detail and
  the exact failure shape needed to locate and fix both defects.
- `scripts/preflight/consumer_preconditions.py`,
  `tests/test_issue_3182_citation_line_accuracy.py`,
  `tests/test_issue_3182_preflight.py` — derived: `git log -1 --format=%H
  25176d39` → `25176d39b6ea54154064fe00f1d9059d912371fc`, the round-3 tip
  this round's `git diff 25176d39 HEAD` (below) is against.

## Open findings

None with a resolution path required this round — canonical:
`docs/issue-3182/reports/implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf.md`
already logged three `sys.exit` gates found beyond round 3's authorized
scope (`core_root`/`core_plugin_dirs`, `require_doctor`,
`ensure_target_remote`) as its own open follow-up, not added to
`CHECKS`. That item is unchanged by this round — carried forward as-is,
not newly discovered here, and out of this round's scope (fixing the two
named defects plus a same-shape sweep of the existing `except` sites).
The sweep this round ran (derived: `git grep -n "except"
scripts/preflight/consumer_preconditions.py`, classified above) found no
new open item.

## What did not work

Initially wrote `_python_masked_spans()`'s multi-line-string span end
column as `len(toks[0].line) + len(t.string)`, reasoning from the
tokenizer's own `.line` attribute — wrong on inspection (`toks[0]` is
the `ENCODING` token, whose `.line` is empty, so the arithmetic was
nonsense) before it was ever run. Caught in review before executing;
replaced with a large sentinel column (`1_000_000`) and relied on Python
slicing being a no-op past a string's length, which needs no per-line
length lookup at all. No test run ever exercised the broken version.

The first version of `test_statvfs_failure_reports_unsatisfied_naming_what_failed`
patched only `os.statvfs` and asserted on the result — it failed with
`'inode' not found`, detail `'cannot read disk usage at ...'`. Root
cause: CPython's `shutil.disk_usage()` is itself implemented on top of
`os.statvfs()` on POSIX, so patching `os.statvfs` alone also breaks the
`shutil.disk_usage()` call earlier in the same function, tripping its
*own* except-OSError branch first and never reaching the inode check
this test targets. Fixed by also faking `shutil.disk_usage` to succeed
independently, decoupling it from the patched `os.statvfs`.

## Next steps

Code fixes are committed on this branch — acceptance: `git log --oneline
-3` — result:

```
2e418e66 issue-3182: round 4 -- citation test now distinguishes real code from a comment or docstring
bbf7e708 issue-3182: round 4 -- fix os.statvfs() observation failure silently reporting satisfied
25176d39 issue-3182: round 3 addendum -- discriminating exit-code test, bidirectional doc-drift test, platform-invariant git check
```

Remaining, outside this record write: commit this record file itself,
then `git push` to
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`
(PR #3184, already OPEN — no new PR to open), do not merge, per the
brief.

## Acceptance checks (executed, this round, from repo root, not /tmp)

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` — result:

```
...........                                                              [100%]
11 passed in 12.98s
```

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` — result:

```
....                                                                      [100%]
4 passed in 8.94s
```

acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` — result:

```
....                                                                      [100%]
4 passed in 4.84s
```

derived: `python3 -m pytest tests/ -q` — result:

```
399 passed, 2 warnings in 34.00s
```

The two warnings are a pre-existing, unrelated pinned-fixture-divergence
notice (issue #3019, `tests/test_skill_candidates_floor.py`) — canonical:
the warning text itself names `captured 2026-09-01T03:40:29Z`, before
this round's changes, and neither file it names
(`test_skill_candidates_floor.py`, the `_bm25_cross_family_scores()`
scorer) is in this round's `code_under_review`.

derived: `git diff --stat 25176d39 HEAD` — result:

```
 scripts/preflight/consumer_preconditions.py     |  13 +-
 tests/test_issue_3182_citation_line_accuracy.py | 271 +++++++++++++++++++++++-
 tests/test_issue_3182_preflight.py              |  49 +++++
 3 files changed, 325 insertions(+), 8 deletions(-)
```

## skill-verdict

skill-verdict: silent-failure-audit — applied: invoked; used the
enumerate-classify-trace procedure on
`scripts/preflight/consumer_preconditions.py`'s `except` sites (derived:
`git grep -n "except" scripts/preflight/consumer_preconditions.py`, 5
matches) to justify the sweep result under "Sweep — every other
precondition check, for the same shape" above, rather than asserting it
from a skim.
skill-verdict: test-derivation — applied: invoked; used the
route-by-problem-shape step at lightweight depth matching the size of
this repair (not the full high-risk procedure) — each defect's fix
routes to a 2-condition decision table (observation succeeds/fails for
defect 1; comment-or-docstring vs. real-code for defect 2), and both new
test classes cover both branches of their respective tables
(`test_statvfs_failure_...` / `test_statvfs_success_...`; the six
`CitationCommentAndStringDiscriminationTest` cases pairing a
rejected-prose case with a still-matches-code case).
skill-verdict: implementation-blueprint — not-applicable: two
function-local bug fixes plus matching regression tests in already-
existing files, no new module boundary or multi-file structure decision
to freeze.
other mounted skills: not triggered (work-in-english's obligations were
followed as house style throughout — English commits/tests/comments,
Korean reserved for the final chat summary — but it was not invoked via
the Skill tool this session).
