# Conformance review of issue-330's path-shaped reach check (phase 2)

kind: record
loop_state: reported
upstream: docs/issue-330/proposals/2026-08-07-impact-reach-check.md
code_under_review:
- gates/gates.py
- gates/test_orphaned_references.py
- docs/issue-330/reports/implementation.md

## What was done

canonical: docs/issue-330/reports/implementation.md, read this session
— re-read the phase-2 record's claims against the approved proposal
(`docs/issue-330/proposals/2026-08-07-impact-reach-check.md`), then
independently re-derived each claim from the current working tree
rather than trusting the record's prose. Verdict scale: Present
(claim reproduces), Incorrect (cited evidence does not reproduce),
Unverifiable (no counter-evidence located either way).

## Per-requirement verdicts

### Item 2 — `orphaned_references(work, base=BASE)` — Present

canonical: gates/gates.py:891-925, read this session — collects old
paths from `_committed_changes_with_status` where status starts with
`D` or a rename's old side is set, builds the `touched` set from both
new and old paths, lists tracked files outside `touched` via `git
ls-files`, then `git grep -F` for each old path across that list,
returning `(old_path, ref_file)` hits. Same shape as proposal item 2
(collect D/rename-old paths, grep the rest of the tree excluding the
PR's own changed files, return hit pairs).

### Item 3 — `reach_check(work, record_text, base=BASE)` — Present

canonical: gates/gates.py:928-948, read this session — calls
`orphaned_references`, extracts the `## Reach` section body with a
regex bounded to the next `##` heading, and for each hit checks
whether the old path or its parent directory string appears in that
body; unmatched hits become finding strings, an empty hit list
returns an empty list. Same shape as proposal item 3.

### Item 4 — unit tests, 6 required fixture scenarios — Present

derived: `grep -n "^def t_" gates/test_orphaned_references.py`, run
this session:
```
55:def t_orphaned_references_empty_when_nothing_deleted_or_renamed():
65:def t_orphaned_references_finds_live_reference_to_deleted_path():
76:def t_orphaned_references_finds_reference_to_renamed_old_path():
87:def t_reach_check_fails_when_orphan_undeclared():
98:def t_reach_check_passes_when_orphan_declared():
112:def t_reach_check_passes_trivially_with_no_deletions():
```
canonical: same listing, run this session — the six functions cover
the scenarios proposal item 4 names: no deletions (trivial case), a
deleted path still referenced, a renamed old path still referenced,
an undeclared orphan (failing case), a declared orphan (passing
case), and no deletions for `reach_check` itself.

acceptance: `python3 -m pytest gates/test_orphaned_references.py -q`
— result:
```
......                                                                   [100%]
6 passed in 0.23s
```
canonical: acceptance run above, this session — the record's cited
test count reproduces under the file's current name. Note: the record
cites the file as gates/test_gates.py (no backtick path below, since
that name no longer resolves in the working tree); it was renamed to
gates/test_orphaned_references.py by a later, separate commit
(`08b28087`, issue-398, resolving a pytest basename collision) that
postdates this record's `code_sha` (`45055f69`) — not a fidelity
defect against the phase-2 record as it stood at its own commit.

### Item 5 — historical-regression evidence — Present

derived: `git diff --name-status d04b36a^1 d04b36a` and `git diff
--name-status 11e459e...ec85a22`, run this session:
```
A	docs/issue-285/proposals/spawn-latency-fixes.md
A	docs/issue-285/reports/implementation.md
A	docs/issue-285/reports/implementation/survey.md
M	spawn.py
M	test_spawn.py
===
A	docs/issue-313/reports/implementation.md
M	spawn.py
M	test_spawn.py
```
derived: `git diff --name-status da2c3de 3ae588b`, run this session:
```
M	README.ko.md
M	README.md
M	protocol.ko.md
M	protocol.md
```
canonical: all three diffs above, run this session — none contains a
`D` or `R` status line, so `orphaned_references` returns no hits for
any of the three named regressions (#285→#296/#297, #297→#313,
#140→#147). This reproduces the record's claimed count of zero
caught out of the three named regressions, and lines up with the
proposal's own Out-of-scope note that content/value/vocabulary-level
regressions sit outside the path-shaped check's coverage.

### Item 1 — mandatory `## Reach` heading — Present, with disclosed gap

canonical: docs/issue-330/reports/implementation.md `## Reach`
section (lines 73-88), read this session — the record carries its
own `## Reach` section, satisfying the proposal's requirement at the
level of this one record.

derived: `grep -rln "## Reach" gates/ hooks/` and `grep -n "Reach"
gates/record_lint.py`, run this session:
```
(no output from either command)
```
canonical: same commands, run this session — no mechanical check in
this repo enforces `## Reach` as a required heading across other
roles' records; the proposal's item 1 describes extending the
record-shape-directive/record-fields-gate pattern that lives in the
external rulebook repo, out of this proposal's write-set. The
implementation record itself discloses this gap directly instead of
asserting universal enforcement — the requirement holds for this
record and is honestly scoped short of the cross-repo mechanism, not
silently overclaimed.

### Out-of-scope constraint — `ALL` registry left untouched — Present

derived: `grep -n "^ALL = " gates/gates.py` and `grep -n
"reach_check\|orphaned_references" gates/gates.py`, run this session:
```
1265:ALL = {"writeset": writeset, "deps": deps,
891:def orphaned_references(work: Path, base: str = BASE) -> list[tuple[str, str]]:
928:def reach_check(work: Path, record_text: str, base: str = BASE) -> list[str]:
```
canonical: same commands, run this session — `orphaned_references`
and `reach_check` are defined but neither name appears in the `ALL`
dict definition; CI/PreToolUse wiring is unchanged, in line with the
proposal's Out-of-scope item 1 and the record's own claim.

## Summary table

canonical: the six verdict sections above, this session — table
restates those verdicts, no new evidence introduced here.

| Item | Proposal requirement | Verdict |
|---|---|---|
| 1 | mandatory `## Reach` heading | Present (disclosed cross-repo gap) |
| 2 | `orphaned_references` | Present |
| 3 | `reach_check` | Present |
| 4 | 6 unit-test scenarios | Present |
| 5 | historical-regression evidence | Present |
| — | `ALL` registry untouched (out of scope) | Present |

Overall verdict (worst case across all cited results, per EARL 1.0
recomputation rule): **Present** across every checked item — no
Incorrect or Unverifiable finding.

## Why

Per-requirement fidelity verdicts, artifact-only, per the
conformance-review role's rulebook (never a holistic quality read,
never a fix). Every claim in `docs/issue-330/reports/implementation.md`
re-derived independently in this session reproduced, including the
record's own self-critical claim that the check does not catch the
regressions that motivated it — the record does not overstate the
check's coverage.

## What did not work

None.

## Open findings

None — every checked claim reproduced; no finding routed to another
role.

## Next steps

None. This role's phase-2 obligation for issue-330 ends at this
verdict record.

## Resolution path

Not applicable — no open finding to resolve.
