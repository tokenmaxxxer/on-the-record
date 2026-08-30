---
issue: 2803
role: technical-writing-style-guide-compliance-632a1d33
author: technical-writing-style-guide-compliance-632a1d33
skills: technical-writing-style-guide-compliance (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: 2d53e0fe:test/test_spawn_attempt_staleness.py
    sha: 2d53e0fe1e18c40f24a2fd6767e5ffc9c26a19ac
---

# issue-2803 — technical-writing-style-guide-compliance-632a1d33 record

derived: `grep -m1 "^description:" /home/jwjung/skill-registry/skills/technical-writing-style-guide-compliance/SKILL.md` — result:
```
description: >-
```
(full trigger text read this turn from that file: mood/voice/person/tone/word-choice compliance review for documentation prose — matched against this task, a terminology rename in test comments, below.)

skill-verdict: technical-writing-style-guide-compliance — not-applicable: task is a terminology-consistency rename in test docstrings/comments (retired "role" noun -> the code's actual `spawn._skill_family()`/`skill` wording), not a Google Dev Doc Style Guide mood/voice/person/tone pass over user-facing documentation.

derived: `grep -m1 "^description:" /home/jwjung/skill-registry/skills/work-in-english/SKILL.md` — result:
```
description: >-
```
(full trigger text read this turn: triggers when the user communicates in Korean; the user's request this turn was in English, confirmed by re-reading the task prompt this turn.)

skill-verdict: work-in-english — not-applicable: the user's request this turn was written in English; commit messages, the PR, and this record are in English per existing repo convention regardless.

derived: `grep -m1 "^description:" /home/jwjung/skill-registry/skills/prose-modes/SKILL.md` — result:
```
description: >-
```
(full trigger text read this turn: document-type x reader-knowledge style tuning for explanatory/teaching prose; this record is a short factual technical record for an expert reader following the established record-shape skeleton, not that kind of composition.)

skill-verdict: prose-modes — not-applicable: this record is a short factual technical record following the project's established record-shape skeleton for an expert reader, not novel explanatory/teaching prose needing document-type x reader-knowledge style tuning.
other mounted skills: technical-writing-style-guide-compliance, work-in-english, prose-modes all evaluated not-applicable (see lines above); none invoked.

## What was done

Followed up on PR #2804 (fixture-literal rename) and PR #2806 (its independent
verification) per the issue's latest comment: brought the six remaining prose
occurrences of the retired noun "role" in `test/test_spawn_attempt_staleness.py`
to the wording the code itself uses.

canonical: `spawn.py:1399-1438` (`_skill_family()`, `_attempt_superseded()`), read this turn — `_skill_family(skill)` takes a parameter named `skill`, strips an 8-hex-char lease-disambiguator suffix, and is exercised in this test file exclusively via `attempt["skill"]` / `spawn._skill_family(...)` calls — the code's own vocabulary is "skill family", never "role family".

Six comment/docstring sites were changed accordingly (no assertions,
identifiers, or `docs/` records touched):

- line 214: "appends to every role string" -> "appends to every skill string"
- line 291: `test_success_on_a_different_issue_does_not_supersede` docstring,
  "same role family, different issue" -> "same skill family, different issue"
- line 303: `test_success_on_a_different_skill_family_does_not_supersede`
  docstring, "same issue, different role family" -> "same issue, different
  skill family" (this is the exact test PR #2806 flagged: a test literally
  named `different_skill_family` whose own docstring called the same thing
  "role family")
- line 423: `SpawnAttemptSweepSupersessionTest` docstring, "(issue,
  role-family)" -> "(issue, skill-family)"
- line 479: inline comment, "the same (issue, role-family)" -> "the same
  (issue, skill-family)"
- line 507: `test_unrelated_halt_on_a_never_tagged_issue_keeps_reporting_unchanged`
  docstring, "issue+role-family" -> "issue+skill-family"

acceptance: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` — result:
```
(no output, exit 1 — zero remaining "role" occurrences)
```

acceptance: `python3 -m pytest test/test_spawn_attempt_staleness.py -v` before and after, compared as a set of test names — result:
```
before: 41 names captured to /tmp/before_names.txt
after:  41 names captured to /tmp/after_names.txt
diff /tmp/before_names.txt /tmp/after_names.txt: no output (identical sets)
both runs: "41 passed"
```

Also ran a background warrant-hunter probe before landing, stance "this
comment/docstring-only rename could break a docstring/comment-introspecting
or grep-based consumer" — verdict NO FINDING. Its hunt record sits at
docs/issue-2803/reports/technical-writing-style-guide-compliance-632a1d33/2026-08-30-hunt-role-to-skill-rename-comment-only.md
(committed alongside this record in the same commit as this file).

## Why

The issue's latest comment establishes this is determinable, not a judgment
call: `spawn._skill_family()` is the live mechanism, its parameter and the
ledger field it reads are both named `skill`, and one test in this file is
named `different_skill_family` while its own docstring two lines away called
the identical mechanism "role family". Editing the prose to match the code's
own identifier removes that self-contradiction without touching behavior —
scope is explicitly comments/docstrings only, per the task and per this
issue's history of "role" as a retired axis (issues #1955/#2507/#2592/#2798).

## What did not work

None.

## Upstream basis

canonical: `gh pr view 2806 --repo tokenmaxxxer/on-the-record --json state,title` — result:
```
{"state":"MERGED","title":"issue-2803: independent verification of PR #2804 (retired-noun skill-slot rename)"}
```

- `2d53e0fe` (PR #2806, merged, confirmed above) — independent verification
  that established the six prose sites are stale wording, not a distinct
  legitimate concept, and is the basis for this follow-up's scope.
- Issue #2803, latest comment (author JiwonJung94, read via `gh issue view
  2803 --repo tokenmaxxxer/on-the-record --comments` this turn) — defines
  this follow-up's scope (prose-only rename to the code's existing wording)
  and requests the cross-file sweep below.
- `spawn.py:1399-1438` — read directly to confirm the code's current wording
  before choosing replacement text (cited above under "What was done").

Search population for "does the same stale wording sit elsewhere describing
the same mechanism":

1. `test/test_spawn_attempt_staleness.py` itself, all 6 "role"-shaped
   occurrences — fixed (see above); confirmed zero remaining via the
   `grep -inE '\brole\b'` acceptance check above.
2. All other on-the-record test files. acceptance: `git ls-files 'test/*.py' | wc -l` — result:
   ```
   40
   ```
   (every tracked test file besides the one just edited.)
   acceptance: `grep -rniE '\brole[ _-]family\b' test/` — result:
   ```
   (no output — zero matches across all 40 files)
   ```
   acceptance: `grep -rlnE '_skill_family|_attempt_superseded' test/` — result:
   ```
   test/test_spawn_attempt_staleness.py
   ```
   (the mechanism is exercised only in the file already fixed — no other
   file describes it, so there is nothing else in this population to check.)
3. A related-but-distinct function, `resolve_skill_family_source` (skill
   *source-directory* resolution, issue #2561/#2507 — not the lease-suffix
   stripping this issue is about), carries the same stale-noun shape in
   `test/test_consult_no_rulebook_identity_regression.py`.
   derived: `grep -n "resolve_skill_family_source\|resolve_role_family_source" test/test_consult_no_rulebook_identity_regression.py` — result:
   ```
   10:   `resolve_role_family_source()` — 고정 role->skill 표
   54:    접두어로 무엇을 유도하든(있음/없음 모두) 언제나 `resolve_role_family_source()`
   66:    def test_mapped_skill_reaches_resolve_skill_family_source(self):
   68:        real = spawn.resolve_skill_family_source
   74:        spawn.resolve_skill_family_source = spy
   78:            spawn.resolve_skill_family_source = real
   81:    def test_unmapped_skill_still_reaches_resolve_skill_family_source(self):
   86:        real = spawn.resolve_skill_family_source
   92:        spawn.resolve_skill_family_source = spy
   96:            spawn.resolve_skill_family_source = real
   ```
   Lines 10 and 54 cite a literal, nonexistent function name
   `resolve_role_family_source()` in backticks; the only identifier that
   actually exists and is used (lines 66-96) is `resolve_skill_family_source`.
   This is a *different* mechanism than `spawn._skill_family()`, so it is out
   of this follow-up's stated scope ("the same mechanism") and was left
   untouched — reported here as a candidate for a separate, explicitly-scoped
   follow-up rather than folded into this one.
4. tokenmaxxxer-core repo (`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core`,
   the other repo named in the original acceptance criteria).
   acceptance: `git ls-files '*.py' | wc -l` — result:
   ```
   12
   ```
   acceptance: `git grep -l "_skill_family\|_attempt_superseded" -- '*.py'` — result:
   ```
   (no output — this mechanism does not exist in that repo's 12 tracked .py files)
   ```
   acceptance: `git grep -niE '\brole[ _-]family\b'` (all tracked files, not just `*.py`) — result:
   ```
   15 hits, all under docs/issue-{254,257,260,263}/** citing the literal
   filename docs/reports/keep-role-family-classification.md — a real
   proper-noun filename unrelated to this mechanism, and under docs/ in
   that repo besides (out of scope to edit regardless).
   ```

## Open findings

- `resolve_role_family_source()` stale-name reference in
  `test/test_consult_no_rulebook_identity_regression.py` (lines 10, 54) —
  see item 3 above. Resolution path: a separate, explicitly-scoped follow-up
  issue, since it is a different mechanism than the one this issue named.

## Next steps

None — delivered via the build-now bypass (`CORE_BUILD_NOW=1`, contract v3
s19a) as a single-PR follow-up.
