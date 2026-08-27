---
issue: 2587
role: technical-writing-structure-comprehension-e650e2e5
author: technical-writing-structure-comprehension-e650e2e5
loop_state: landed
upstream:
  - path: on-the-record/directive/spawn-and-board.md
    sha: same-commit
---

# issue-2587 — technical-writing-structure-comprehension-e650e2e5 record

## What was done

Replaced the three `-C <repo>` placeholders in
`on-the-record/directive/spawn-and-board.md` (lines 4, 8, 70) with
`-C <path>`, and added one clarifying note at the first occurrence: the
flag is `-C`/`--cwd`, a filesystem path (not a repo slug), defaulting to
`.`, so it can be omitted when the target repo is already the current
directory.

canonical: `spawn.py:1603` — read before drafting the replacement text
```
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
```

acceptance: `grep -c -- '-C <repo>' on-the-record/directive/spawn-and-board.md` — result:
```
0
```

acceptance: `grep -n '"-C", "--cwd"' spawn.py` — result:
```
1603:    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
```

`spawn.py` itself was not edited this session, so the line quoted above
is its unedited state.

derived: `git diff --stat` (this session's only changed file)
```
 on-the-record/directive/spawn-and-board.md | 12 +++++++-----
 1 file changed, 7 insertions(+), 5 deletions(-)
```

Scanned the rest of the document for other placeholders that misname
what their underlying flag accepts.

derived: `grep -n '<[a-zA-Z_]*>' on-the-record/directive/spawn-and-board.md`
```
4:  `python3 ${CHECKOUT}/spawn.py --skills <skill>[,<skill>...] "<task>" --issue <n> -C <path>`
8:  typed); read the board first with `python3 ${CHECKOUT}/spawn.py -C <path>`.
10:  from reading the board (records under docs/issue-<n>/, each one's
20:  own isolated workspace. PROGRESS CHECKS: `spawn.py --skills <skill>
21:  "<task>" --issue <n>` and `spawn.py watch --issue <n>` both return early, at
26:  (including `stall`), re-arm by calling `spawn.py watch --issue <n>`
33:  running. `spawn.py watch --issue <n> --follow` streams the same
55:  `spawn.py watch --issue <n> --role <r>` call — never a standing loop of
72:  "<task>" --issue <n> -C <path>` covers conformance-review — the seven
```

None of the remaining placeholders (`<skill>`, `<task>`, `<n>`, `<r>`)
misname what they hold — each names what it actually is (a skill name,
a task string, an issue number, a role name). No second site fit the
"fix only if it's the identical defect on the identical flag" bar, so
nothing else in this file was changed, matching the issue's non-goal
of not auditing unrelated placeholders.

## Why

The issue's acceptance criteria pin the fix to a literal grep count of
zero remaining `-C <repo>` occurrences and a working `spawn.py` flag
match. A direct text substitution meets both without any design
choice. The one added sentence exists because the acceptance criteria
also require the flag's real default to be stated, not just the
placeholder renamed. Folding that into the existing parenthetical
(rather than a new paragraph) keeps the diff local to the three defect
sites.

Skip statement (scout-directive / survey-order-directive): this is a
pure bugfix — a placeholder correction with no design decision open,
since the target flag's name, type, and default are already fixed by
`spawn.py`. Scouting and the current-state survey were both skipped
under that mandatory skip condition; this line is the required skip
record.

Build-now bypass: this session's environment carried `CORE_BUILD_NOW=1`
(set by the spawner), authorizing contract v3 s19a's delivery-only
path, so the phase-1 proposal round was skipped and this session
delivered directly: fix, commit, record, one PR.

## What did not work

None.

## Upstream basis

`on-the-record/directive/spawn-and-board.md` — this record's own
commit (`sha: same-commit`), the file edited to close out the issue's
two acceptance checks.

canonical: `spawn.py:1603`, read (not edited) to confirm the flag's
real name and default before drafting the replacement text
```
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
```

## Open findings

None.

acceptance: `grep -c -- '-C <repo>' on-the-record/directive/spawn-and-board.md` — result:
```
0
```

acceptance: `grep -n '"-C", "--cwd"' spawn.py` — result:
```
1603:    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
```

The `must not:` constraint (no change to `spawn.py`'s flag, name, or
default) holds — the line above is `spawn.py`'s current, unedited
state.

## Next steps

None; loop_state is terminal (`landed`).

skill-verdict: technical-writing-structure-comprehension — applied: invoked; used rules 1-2 (15-20 word sentence target, split multi-clause sentences) to revise the inserted clarifying note in spawn-and-board.md into two shorter sentences instead of one long em-dash/so-clause sentence.
skill-verdict: work-in-english — not-applicable: this record and all repository-bound work this session were already authored in English.
