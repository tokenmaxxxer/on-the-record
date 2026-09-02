---
issue: 3059
role: silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316
author: silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316
skills: silent-failure-audit (skill-repository(c05de12)), technical-writing-structure-comprehension (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: da8b3b0e53cc1f3287e131edc32e1a2112df0cc1
type: implementation-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: gh issue view 3059 --repo tokenmaxxxer/on-the-record (issue body + follow-up comment)
    sha: same-commit
---

# issue-3059 — silent-failure-audit+technical-writing-structure-comprehension+test-derivation+adversarial-review-95e5c316 record

## What was done

`gates/check_runner.py:238-241`'s `parse_checks()` classified any backtick
`check:`/`gate:` command whose first token was not on `INTERPRETERS`
(`bash`, `bun`, `deno`, `node`, `npx`, `pytest`, `python`, `python3`,
`sh`) as `judgment`, identically to a check that was genuinely prose —
the follow-up comment's cause 1 (`grep -n foo bar.md`, a real mechanical
command missing a wrapper) and cause 2 (a description with no backtick
command at all) both produced the same "판단이 필요한 기준" message.

Changes, all in `gates/check_runner.py`:

- `_COMMON_NON_INTERPRETER_TOOLS` (new, line ~106): a diagnostic-only
  curated set — `grep`, `jq`, `cat`, `test`, `diff`, `git` — the six
  tools the issue names as observed live. Never added to `INTERPRETERS`
  and never consulted by `run_checks`; it exists only to pick a message.
- `parse_checks()`: a bullet whose backtick content is a real command
  (survives the `_STATING_VERB_PREFIX`/`_FOREIGN_OWNER`/
  `_MEASUREMENT_LANGUAGE`/`_looks_like_path` exclusions already in that
  function) but whose first token is in the curated set now carries
  `reason: "unmapped-interpreter"`, `command`, and `tool` alongside the
  existing `type: "judgment"` — still never executed (must-not honoured:
  `INTERPRETERS` itself is untouched, and nothing auto-wraps the command).
- `_judgment_line()` (new): renders one judgment item; an
  `unmapped-interpreter` item names the missing token and the sanctioned
  fix as `bash -c {shlex.quote(command)}` (`shlex.quote`, not a literal
  `"..."` wrap — see Open findings, quote-escaping bug).
- `format_no_checks_comment()` / `format_comment()`: both now route their
  judgment-item rendering through `_judgment_line()`, and
  `format_no_checks_comment()`'s header splits into three cases —
  all-unmapped, all-genuine (byte-identical to the prior text), and
  mixed (states both counts).

`on-the-record/directive/acceptance-format.md` gained two bullets:
INTERPRETER ALLOWLIST (names the allowlist, the wrapping convention, and
that the fix is still the author's to apply) and PROSE COSTS THE
RECORD-ONLY PATH (documents that an all-prose Acceptance section is
refused at `NO_CHECKS_MARKER` before the diff ever reaches the
record-only exemption check in `main()`, per the follow-up comment).

`gates/test_check_runner.py` gained new tests covering: unmapped-
interpreter classification and its `reason`/`tool`/`command` fields;
that the classification never becomes an execution path; that
genuinely-prose and stating-verb-prefixed bullets keep no `reason`; that
`INTERPRETERS` was not widened; all three `format_no_checks_comment()`
header branches; `format_comment()`'s skipped section; survival across a
compound `cd X && CMD` command; and that all six curated tool names
reach the branch — derived: `python3 -m pytest gates/test_check_runner.py -q`
— result: 22 passed (11 pre-existing, 11 new).

skill-verdict: silent-failure-audit — applied: invoked; audited the
existing `judgment`/`JudgmentCheckError` fail-closed paths this change
touches (`run_checks`'s refusal, `main()`'s empty-state fail-closed
return) before extending them, to check the new `reason` field could not
itself become a second silent-failure surface — derived: `python3 -m
pytest gates/test_check_runner.py -k
test_unmapped_interpreter_never_executes_even_if_fed_to_run_checks -q`
— result: 1 passed (the item still raises `JudgmentCheckError` and is
never executed, `reason` is inert to every execution path).
skill-verdict: technical-writing-structure-comprehension — applied: invoked;
used for the two new acceptance-format.md bullets and the PR-comment
message text — short sentences, one idea per sentence, explicit
consequence stated up front rather than buried in a subordinate clause.
skill-verdict: test-derivation — applied: invoked; routed the issue's 3
acceptance criteria as Given-When-Then scenarios at Low/Medium depth
(non-safety-critical bugfix, no combinatorial parameter space) — see
Upstream basis below for the mapping. No EP/BVA/decision-table/state-
transition routing applied; none of the 3 criteria matched those shapes.
skill-verdict: adversarial-review — applied: invoked; spawned a fresh-
context `general-purpose` agent (agent id `a9ae2d950209f0b57`) with only
the diff (`git diff` output, no issue text, no rationale) and the
standard "find everything wrong" evaluator prompt. Findings and their
disposition are in Open findings below.
other mounted skills: not triggered (work-in-english, prose-modes —
followed as ambient convention: commit/PR/doc/record text in English,
terse prose — without a separate Skill-tool invocation).

## Why

The issue traces two distinct causes landing on one message and asks the
runner to separate them without widening what it executes. The fix is
therefore additive-only to the `judgment` bucket: same classification,
same refusal to run, richer reason. This avoids the two must-nots
directly — `INTERPRETERS` is untouched, and nothing auto-wraps a command
in `bash -c` (the wrap only ever appears as suggested text in a PR
comment) — derived: `python3 -m pytest gates/test_check_runner.py -k
"test_interpreters_allowlist_is_not_widened or
test_unmapped_interpreter_never_executes_even_if_fed_to_run_checks" -q`
— result: 2 passed.

The curated `_COMMON_NON_INTERPRETER_TOOLS` set is deliberately narrow
and named directly from the issue body ("grep, jq, cat, test, diff, git
... fails both arms") rather than inferred from a broader heuristic
(e.g., "any bare identifier followed by a flag-shaped token") — a
broader heuristic risks reclassifying bullets that #2278/#2313/#2463/
#2509 already fixed for good reasons (bare skill-name identifiers,
foreign-owned paths, stating-verb prose), and this repo's own history
shows that classifier heuristics widened without a measured live case
have produced regressions each time.

## What did not work

None.

## Upstream basis

- canonical: `gh issue view 3059 --repo tokenmaxxxer/on-the-record`
  (issue body) — supplies the defect description,
  `gates/check_runner.py:238-241` cite, the two follow-on effects, and
  the 3 Acceptance criteria (sha: same-commit — read live, not a repo
  path).
- canonical: `gh issue view 3059 --repo tokenmaxxxer/on-the-record
  --comments` (follow-up comment) — supplies cause 1 vs. cause 2, the
  study-companion PR #1/#2/#3 live observations, and the record-only-path
  consequence (sha: same-commit — read live, not a repo path).

Acceptance-criteria to test-case mapping (test-derivation, Low/Medium
depth — a scoped bugfix, no combinatorial/state-machine shape):

| # | Criterion | Given-When-Then | Depth | Test(s) |
|---|---|---|---|---|
| 1 | unmapped-token check reports distinct reason; empty state: genuine prose unchanged | Given a `check:` bullet with a real command whose first token isn't on `INTERPRETERS`, When `parse_checks` runs, Then the item carries `reason: "unmapped-interpreter"`. Given a bullet with no backtick command at all, When parsed, Then it carries no `reason`. | Medium (user-facing classification branch, not safety-critical) | `test_unmapped_interpreter_command_is_still_judgment_but_carries_a_reason`, `test_genuinely_prose_check_has_no_backtick_and_no_reason`, `test_stating_verb_prefixed_command_shape_stays_plain_judgment`, `test_unmapped_interpreter_recognizes_every_curated_tool_name`, `test_unmapped_interpreter_classification_survives_compound_command` |
| 2 | message names the sanctioned `bash -c` form, not only the refusal | Given an unmapped-interpreter judgment item, When rendered, Then the line names the missing token and a `bash -c` wrap of the exact command. | Medium | `test_format_no_checks_comment_unmapped_only_names_interpreter_and_bash_c`, `test_format_comment_skipped_section_uses_the_distinct_reason_line` |
| 3 | allowlist + wrapping convention documented where an author will meet it | Given `on-the-record/directive/acceptance-format.md`, When grepped for `INTERPRETERS`/`bash -c`, Then both terms are present. | Low (a documentation existence check, not a logic branch) | derived below |
| must-not-1 | do not widen `INTERPRETERS` | Given the change, When `INTERPRETERS` is inspected, Then it is byte-identical to before and disjoint from the new curated set. | High (a must-not is always high-risk by definition) | `test_interpreters_allowlist_is_not_widened` |
| must-not-2 | do not auto-wrap in `bash -c` | Given an unmapped-interpreter item, When fed to `run_checks`, Then it still raises `JudgmentCheckError` (never executes). | High | `test_unmapped_interpreter_never_executes_even_if_fed_to_run_checks` |

Residual: this technique set does not establish that the curated 6-tool
list is exhaustive, does not cover non-functional concerns (there are
none here), and does not substitute for the adversarial review that
caught the real defects listed under Open findings below — those were
found by an independent evaluator, not by the derived test cases
themselves (the tests were written to encode the fix, then updated once
the escaping bug and doc wording were corrected).

Acceptance requirement met — checked: `python3 -c "import sys;
sys.path.insert(0,'gates'); import check_runner as cr;
print(cr.parse_checks(open('/dev/stdin').read()))" <<< '## Acceptance\n-
x\n  - check: \`grep -n foo bar.md\`'` — result: `[{'type': 'judgment',
'raw': '\`grep -n foo bar.md\`', 'reason': 'unmapped-interpreter',
'command': 'grep -n foo bar.md', 'tool': 'grep'}]`

derived: `grep -rn 'INTERPRETERS\|bash -c'
on-the-record/directive/acceptance-format.md` — result: 2 matches (lines
119, 125) — satisfies criterion 3.

derived: `python3 -m pytest gates/ -q` — result: 57 passed, 0 failed
(full gates suite, not just this file).

unverifiable: the issue's second Acceptance check (`python3
gates/check_runner.py 2 1 --repo /home/jwjung/study-companion | grep -i
-e 'bash -c' -e interpreter`) names an external `study-companion` repo
checkout not present in this session — checked the equivalent mechanism
directly instead, same result string produced by the same code path
(see the "Acceptance requirement met" citation above, which contains
both `bash -c` and the tool name driving the `interpreter` allowlist
message).

## Open findings

Adversarial-review findings and their disposition (agent id
`a9ae2d950209f0b57`, spawned via the Agent tool with only this diff and
the standard evaluator prompt — canonical: the agent's returned report,
reproduced/re-derived below):

- Quote-escaping bug in the suggested `bash -c "..."` wrap for commands
  containing double quotes (e.g. `grep -n "foo bar" file.md`) — derived:
  `bash -c "grep -n \"foo bar\" file.md"; echo exit:$?` against a file
  containing `foo bar test` — result: exit 1 (wrong; the un-wrapped
  command exits 0) versus `bash -c 'grep -n "foo bar" file.md'` (the
  `shlex.quote`-produced form) — result: exit 0 (correct, matches the
  un-wrapped command). Resolution: fixed — `_judgment_line()` now emits
  `bash -c {shlex.quote(command)}`.
- New doc bullet described the path-detection arm as "a file extension"
  when the code only requires a `.` anywhere in the first token —
  canonical: `gates/check_runner.py` lines 264-267 (`looks_like_command
  = bool(tokens) and ("/" in tokens[0] and tokens[0].count(".") >= 1 or
  tokens[0] in INTERPRETERS)`) — no extension check exists. Resolution:
  fixed — doc now says "the first token contains both `/` and `.`".
- Doc/code comment attributed `INTERPRETERS` narrowing to issue #2509 —
  derived: `git log --oneline --all | grep -i 2509` and `git log -p
  --all -- gates/check_runner.py | grep -n 2509` — result: PR #2513
  ("fix check_runner false FAIL on foreign-owned paths and stating-verb
  bullets") added `_FOREIGN_OWNER`/`_STATING_VERB_PREFIX`; no hunk
  touches `INTERPRETERS`. Resolution: fixed — citation now credits #2073
  for establishing the allowlist and #2509 for hardening the same
  classifier against a different false-positive class, without claiming
  #2509 touched `INTERPRETERS` itself.
- Curated set recognizes only 6 tools; `curl`/`awk`/etc. still fall to
  the old undifferentiated message. Resolution: not fixed, judged out of
  scope — the issue's must-not forbids a general command allowlist, and
  the issue body itself scopes the curated set to "the ones observed
  live" (these 6). A 7th tool observed live is a follow-up issue, not
  something to guess at now.
- "PROSE COSTS THE RECORD-ONLY PATH" documents a real ordering gap in
  `main()` (the empty-state check runs before the record-only check) but
  doesn't reorder it. Resolution: not fixed, judged out of scope — the
  issue's 3 Acceptance criteria ask for documentation of this
  consequence, not a reordering of `main()`; reordering was never in the
  approved scope.
- Unescaped backtick in `_judgment_line()`'s Markdown rendering if a
  command itself contains a backtick. Resolution: not fixed, judged out
  of scope — matches the existing risk level of every other line in
  `format_comment()`/`format_no_checks_comment()`, none of which escape
  Markdown specials in check text; a repo-wide fix is a separate, larger
  change.
- Weak test coverage of the curated tool set and no compound-command
  case at review time — canonical: the agent's own report, quoted
  verbatim — "Every new test that exercises classification uses `` `grep
  -n foo bar.md` ``. `jq`, `cat`, `test`, `diff`, `git` — 5 of the 6
  entries ... are asserted only to be *members of the set* ..., never
  actually run through `parse_checks`" and "there is zero test for it
  [the compound-command interaction]". This was true of the working
  tree at review time (before this commit existed — the review ran
  against the diff, not against a committed snapshot). Resolution:
  fixed before committing — added
  `test_unmapped_interpreter_recognizes_every_curated_tool_name` (all 6
  tools) and `test_unmapped_interpreter_classification_survives_
  compound_command`; both are present in `code_under_review:` above —
  derived: `git show da8b3b0e:gates/test_check_runner.py | grep -c
  "^def test_unmapped_interpreter_"` — result: 4 (all 4
  unmapped-interpreter test functions, including the 2 added in
  response to this finding, are in the committed snapshot).

## Next steps

None — delivered. Next action is push + PR (Closes #3059, since the 3
Acceptance criteria and both must-nots are satisfied per the checks
above).
