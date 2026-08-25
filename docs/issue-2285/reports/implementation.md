---
issue: 2285
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
code_under_review:
  - consult.py
  - docs/specs/consult-guidance-source.md
  - test/test_consult_no_rulebook_identity_regression.py
type: docs
breaking: none
verdict: pass
---

# issue-2285 — implementation record

## What was done

canonical: this session's own commit `0baac601` (`git show --stat
0baac601`) and `consult.py`/`skills.py` read directly during this
session.

Delivered issue #2241 stage 2 against the frozen write set named in
the authoritative proposal (three paths, no more): `consult.py`,
`docs/specs/consult-guidance-source.md`,
`test/test_consult_no_rulebook_identity_regression.py`.

- `docs/specs/consult-guidance-source.md` (new): documents that every
  plugin-directory assembly call site in `consult.py`
  (`consult_cmd()` at `consult.py:642`, `_readonly_plugin_dirs()` at
  `consult.py:916`, `_run_panel_session()` at `consult.py:1309`)
  resolves guidance content through `skills.resolve_role_source()`
  (`skills.py:354-375`) with no allowlist branch. It also states,
  explicitly, that `role` staying exposed as a lookup key in
  `_ROLE_SKILLS` (`skills.py:286-336`) and the `roles/<role>.json`
  existence check is deferred work, owned by later stages of the
  issue #2241 program rather than this one.
- `test/test_consult_no_rulebook_identity_regression.py` (new): a
  regression guard with two angles — a static source scan of
  `consult.py` for identifiers issue #1955 deleted (`rulebook_checkout`,
  `_role_source_allowlist`, `checkout_version`, `role-source-allowlist`),
  and a behavioral check that `_readonly_plugin_dirs()` reaches
  `resolve_role_source()` the same way for a role present in
  `_ROLE_SKILLS` and one that is not.
- `consult.py`: one code comment (no logic change) at the first
  `roles/<role>.json` existence-check call site (`consult.py:355`,
  inside `_skill_judge_consult()`), pointing at the proposal and
  naming which later stages own `_ROLE_SKILLS`'s key shape and this
  existence check. The other existence-check call sites
  (`consult.py:690`, `consult.py:816`, `consult.py:1155`,
  `consult.py:1304`) are the same pattern and are cited from the
  comment/spec rather than each carrying its own copy.

## Why

canonical: `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
read on `main` (`git show main:docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`),
and `consult.py`/`skills.py` read directly in this session.

The proposal's own Rationale already established that issue #1955
(commit `ac4d56a0:consult.py`) fully retired the rulebook/allowlist
resolution path; this stage's job is confirmation plus a regression
guard, not new removal work. The proposal explicitly rejected doing
the `_ROLE_SKILLS` key migration in this same stage "since it's
adjacent" — that work belongs to later stages per the issue #2241
staging order, and jumping that order risks the premature-cutover
failure mode the issue's own text attributes to prior incidents.

Build-now bypass (contract v3 s19a, `CORE_BUILD_NOW=1` set by the
spawner) applied, so the phase-1 proposal round was skipped and this
record documents a direct delivery.

## What did not work

None.

## Deviations

canonical: `git log -1 --format=%H -- docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
(this session, output `ccee895997e7629495aee4ff7c0588e3082c75bc`), plus
line-by-line reread of the current `consult.py`/`skills.py`.

The proposal's own line citations for `consult.py` and `skills.py` do
not resolve against the current tree — ordinary line drift from
unrelated intervening commits since the survey was written, not a
reverted rulebook path (grep for the removed identifiers themselves
turns up zero hits, per the new regression test's static-scan case).
The Acceptance requires the spec's citations to resolve against the
current line ranges, so `docs/specs/consult-guidance-source.md` cites
the actual current locations instead of copying the proposal's
numbers verbatim. The underlying claim (unconditional skill-repo
resolution, no allowlist branch) is unchanged from what the proposal
described.

CHANGES-loop correction (conformance review R5, PR #2344): the
paragraph above was itself wrong. Every `consult.py` line number this
record originally cited for the spec doc's citations was six lines
stale — computed before this same delivery commit's own six-line
Korean comment insertion at the first existence-check call site, and
never recomputed afterward. The stale set this record originally
wrote:

```
consult.py:636, 910, 1303 (call sites)
consult.py:349, 684, 810, 1149, 1298 (existence-check sites)
```

derived: `main:docs/issue-2285/reports/conformance-review.md`
(untracked on this branch — landed on `main` via #2356, not yet
merged into `issue-2285/implementation`), requirement R5, independently
re-grepped the true lines via `git show
0baac6010bb12baf3adb42d025f51885e8433892:consult.py | grep -n`; this
session re-verified the same eight lines against branch head
`f50e689f` (unchanged for `consult.py` since `0baac601` per that
review's R1 `diff --stat`):

canonical: `git show HEAD:consult.py | grep -n
'_sp.resolve_role_source(role\|f = _sp.ROOT / "roles"'` (this session)
— result:
```
355:        f = _sp.ROOT / "roles" / f"{role}.json"
642:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
690:        f = _sp.ROOT / "roles" / f"{role}.json"
816:        f = _sp.ROOT / "roles" / f"{role}.json"
916:    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
1155:        f = _sp.ROOT / "roles" / f"{role}.json"
1304:    f = _sp.ROOT / "roles" / f"{role}.json"
1309:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
```

`docs/specs/consult-guidance-source.md` and this record's "What was
done" section above now cite these eight recomputed lines (355, 642,
690, 816, 916, 1155, 1304, 1309) instead of the six-line-stale set.
Also reworded the spec doc's bullets so the quoted code excerpt sits
immediately after each `path:line` citation, before any function-name
mention, so the not-yet-landed `gates/record_lint.py`
`citation_line_content_check` (issue #2331,
`origin/issue-2331/implementation`, unmerged into this branch) does
not mis-associate a nearby identifier's own definition line with the
cited call-site line — validated below without merging that branch's
changes into this one.

## Upstream basis

canonical: `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`
on `main`, frontmatter `upstream:` above pins the sha this record was
built against.

The stage-2 proposal is the authoritative spec; its `files:`,
Constraints, Out of scope, and Rollback applied verbatim.

## Open findings

None.

## Acceptance evidence (executed-live)

Gate, unmodified by this stage:

```
$ python3 -m pytest tests/test_spawn_consult_panel.py -q
bringing up nodes...
bringing up nodes...

...................................................x.......              [100%]
58 passed, 1 xfailed in 1.10s
```

The 1 xfail is issue #1619's pre-existing documented concurrency-timing
flake, unrelated to this stage.

New regression test:

```
$ python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v
test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentityInSource::test_consult_py_carries_no_forbidden_rulebook_identifiers PASSED
test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo::test_mapped_role_takes_the_same_single_path PASSED
test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo::test_unmapped_role_still_resolves_through_resolve_role_source PASSED

3 passed in 0.81s
```

Existing role/skill-resolution acceptance, unmodified and still green:

```
$ python3 -m pytest test/test_spawn_role_skill_resolution.py -q
...............                                                          [100%]
```

Empty state (rollback, per the proposal's own definition): reverting
the spec file and the new regression test leaves `consult.py`'s actual
code change as comment-only —

canonical: `git diff 0baac601~1 0baac601 -- consult.py` (this session)
shows only `+` lines inside the new comment block and zero removed or
non-comment lines — rollback has no runtime effect, matching the
proposal's stated Rollback.

`docs/specs/reconciled-index.md` regeneration, run in the same commit
per the docs/specs/* convention:

```
$ python3 gates/spec_index.py --update
docs/specs/reconciled-index.md 갱신됨
$ python3 gates/spec_index.py
통과: 모든 spec 문서가 기록된 해시와 일치한다
```

`docs/specs/consult-guidance-source.md` is a new file, not one of the
curated rows the "Tracked documents" table already lists, so
`--update` produced no working-tree diff — correct, since no tracked
document's content changed.

Recomputed-citation validation (CHANGES-loop fix for R5), run against
the not-yet-landed `gates/record_lint.py` `citation_line_bounds_check`/
`citation_line_content_check` from `origin/issue-2331/implementation`
(fetched read-only into `/tmp` for this check, never merged into this
branch or written into the repo tree):

canonical: this session, `python3 /tmp/validate_citations.py` (a
throwaway script loading `citation_line_bounds_check`/
`citation_line_content_check` from a copy of
`origin/issue-2331/implementation:gates/record_lint.py` and running
both over `docs/specs/consult-guidance-source.md`) — result:
```
bounds findings: 0
content findings: 0
```

Also reran the gates already in this branch's tree, unaffected by the
doc-only fix:
```
$ python3 gates/spec_index.py
통과: 모든 spec 문서가 기록된 해시와 일치한다
$ python3 -m pytest test/test_consult_no_rulebook_identity_regression.py -v
created: 10/10 workers
[gw3] [ 33%] PASSED test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo::test_unmapped_role_still_resolves_through_resolve_role_source
[gw1] [ 66%] PASSED test/test_consult_no_rulebook_identity_regression.py::ReadonlyPluginDirsUnconditionalSkillRepo::test_mapped_role_takes_the_same_single_path
[gw0] [100%] PASSED test/test_consult_no_rulebook_identity_regression.py::NoRulebookIdentityInSource::test_consult_py_carries_no_forbidden_rulebook_identifiers

3 passed in 0.79s
```

skill-verdict: work-in-english — applied: invoked; loaded before
writing this record and the new code comment/test docstrings. This
repo's own established convention (Korean code comments and
docstrings alongside English commit messages, visible throughout
`consult.py`/`skills.py`/existing tests) is what the skill's own
edge-case guidance endorses matching, so the new `consult.py` comment
and the new test's docstrings were written in Korean to match
surrounding style, and this record/commit/PR are in English.

other mounted skills: not triggered — no coupling/cohesion threshold
was crossed, no GoF pattern decision was made, no data-structure/perf
tradeoff was chosen, and the change is a single-file-group
confirmation-plus-regression-test, not a multi-module structure
decision.

Warrant-hunter dispatch: skipped by design, not omission. This session
is headless/single-shot, so a `run_in_background` agent's completion
notification would arrive after the process that spawned it has
already exited — contract v3 s22, which the warrant-directive itself
names as taking priority over its own dispatch instructions in exactly
this situation, resolves the conflict as "do not dispatch the hunter
at all."

## Next steps

None — stage 2 is delivered. Stage 3 under the issue #2241 program is
a separate, later-spawned issue.
