---
issue: 3044
role: independent-verification-2
author: independent-verification-2
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), verify-finding-record (skill-repository(c05de12))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
type: verification-record
breaking: false
verdict: correct-with-open-finding
upstream:
  - path: gates/record_lint.py (skill_verdict_reason_check, invoked-mismatch loop)
    sha: bc557df536ea5a44ab2059a002644bb2fbdf8946
  - path: on-the-record/hooks/skill-verdict-guard.sh (hard/soft split, decision:block path)
    sha: bc557df536ea5a44ab2059a002644bb2fbdf8946
---

# issue-3044 — independent-verification-2 record

## What was done

Independently audited and re-derived PR #3068 (`issue-3044: reject and
block false skill-verdict invoked claims`,
`bc557df536ea5a44ab2059a002644bb2fbdf8946`, closes #3044) against issue
#3044's three acceptance checks and its `must not` list, without citing
the PR's own claimed output. Checked out the PR head into an isolated
`git worktree` (`/tmp/pr3068-verify`, removed after use — no leftover
state) and ran all three acceptance commands myself.

canonical: `python3 -m pytest on-the-record/hooks/ -q -k invoked` (run
in `/tmp/pr3068-verify` on `bc557df5`) — result:
```
9 passed in 0.88s
```

canonical: `grep -rn 'invoked' gates/record_lint.py | head -1` (run in
`/tmp/pr3068-verify`) — result:
```
gates/record_lint.py:545:_SKILL_VERDICT_INVOKED_MARKER = re.compile(r"(?i)^invoked\s*;")
```

canonical: `python3 -m pytest on-the-record/hooks/ -q` (run in
`/tmp/pr3068-verify`) — result:
```
2 failed, 40 passed in 1.11s
```
Both failures are `test_hook_classification.py::HookClassificationTest`
(`test_every_hooks_json_registration_has_a_classification_entry`,
`test_registration_count_matches_the_issues_own_count`). Re-derived the
"pre-existing, unrelated" claim myself rather than citing the PR body:

canonical: `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q`
(run on this repo's own working copy, unmodified, at `24bc12b4`/main —
no PR diff applied) — result:
```
2 failed, 4 passed in 0.81s
```
Same two failures, same test names, confirming they predate and are
unaffected by this PR's diff (`hooks.json`/`hook_classification.json`
for `gate-registration-post-guard.sh`, neither file this PR touches).

Read `gates/record_lint.py`'s `skill_verdict_reason_check`
(`bc557df5:gates/record_lint.py:548-626`) and
`bc557df5:on-the-record/hooks/skill-verdict-guard.sh` in full (355
lines) rather than only the PR's diff hunks, to check the `must not`
list independently:

- `not-applicable:` lines never match `_SKILL_VERDICT_APPLIED` (which
  requires the content to start with `applied:`), so the new converse
  loop (`bc557df5:gates/record_lint.py:613-625`) can never fire on one —
  checked by a direct call in this session, not by trusting the PR's
  own unit test — derived: `python3 -c` invoking
  `record_lint.skill_verdict_reason_check("skill-verdict: bar — not-applicable: no sink here\n", ["foo"])`
  in `/tmp/pr3068-verify` — result: `[]`. Confirmed correct: matches the
  must-not clause.
- An unreadable/absent transcript never reaches
  `skill_verdict_reason_check` at all: `skill-verdict-guard.sh` exits 0
  before computing `mounted`/`invoked` whenever `transcript_path` is
  missing or not a file (`bc557df5:on-the-record/hooks/skill-verdict-guard.sh:91-95`),
  and `invoked_skill_names`'s `except OSError: return []`
  (`bc557df5:on-the-record/hooks/skill-verdict-guard.sh:151-152`) routes
  a mid-read failure into the zero-invocation advisory branch (line
  299), never the blocking branch. Re-ran the PR's own
  `test_hook_reports_not_blocks_when_transcript_missing` myself (part
  of the full-suite `canonical:` run above, 40 passed) rather than
  citing its presence in the diff.
- The pre-existing missing-line/missing-marker (#2039/#2062) shape
  checks are byte-unaffected on their own: the old per-`mounted`-name
  loop (`bc557df5:gates/record_lint.py:591-612`) is untouched, and —
  derived: `diff gates/record_lint.py on-the-record/gates/record_lint.py`
  run in `/tmp/pr3068-verify` — result: empty, confirming the two
  mirror files stay identical as claimed.

## Why

Per [[defect-verification-independence-from-upstream-verdicts]], a
review requirement/PR claim is a claim to independently test, not a
settled fact — so I re-derived all three acceptance commands from a
freshly checked-out worktree rather than trusting the PR body's pasted
output, and deliberately looked for a negative/edge path the PR's own
tests might have skipped (rule 2) instead of stopping once the
happy-path acceptance checks came back green.

That search found one. The PR's three subprocess tests
(`bc557df5:on-the-record/hooks/test_skill_verdict_reason_check.py`,
Part 2) each exercise a record with exactly one violation category —
hard-only (`test_hook_blocks_on_invoked_mismatch_record`, where the
mismatched name `bar` is never invoked in the transcript, so no soft
violation for it is even possible) or none. No test constructs a
record where an invoked skill both (a) triggers a hard
`invoked-mismatch` for one name and (b) is separately missing a
`skill-verdict` line (a soft, pre-#3044 violation) for a *different*
genuinely-invoked name in the same Stop turn. I built that case myself
in an isolated fixture (`/tmp/svg-indep-test`, a throwaway `git init`
repo unrelated to and cleaned up independently of this repo's own
`docs/issue-*` tree) and ran the real shipped hook against it directly
— piping a Stop-event JSON payload into
`bash on-the-record/hooks/skill-verdict-guard.sh`, not `pytest`.

canonical: hook run (in `/tmp/svg-indep-test`, `bc557df5`'s copy of
`skill-verdict-guard.sh`) against a fixture record with `skill-verdict:
foo — applied: invoked; ...` (invoked, matches), `skill-verdict: bar —
applied: invoked; ...` **absent entirely** (`bar` genuinely invoked per
the fixture transcript, but has no line — a #2039 soft violation), and
`skill-verdict: ghost — applied: invoked; ...` (`ghost` never invoked —
a #3044 hard violation) — result:
```
{"decision": "block", "reason": "skill-verdict-guard: docs/issue-999999/reports/implementation.md -- invoked-mismatch (issue #3044): 'ghost' 의 `skill-verdict` 줄이 `applied: invoked; ...`라고 주장하지만, 이 세션의 transcript 는 그 스킬이 Skill 도구로 호출된 적이 없다는 것을 보여준다 — not-applicable 로 정정하거나, 실제로 Skill 도구를 호출한 뒤 다시 기록하라. -- 자세한 형태는 docs/handbooks/skill-verdict-obligation.md 참고."}
```
The `reason` string names only `ghost`; it never mentions `bar`, even
though `bar` is genuinely invoked and genuinely missing its required
`skill-verdict` line. Confirmed independently at the function level
too — derived: `python3 -c` calling
`record_lint.skill_verdict_reason_check(text, ["foo", "bar"])` directly
(`text` carrying only the `foo`/`ghost` lines) — result: returns *both*
the `bar`-missing-line violation and the `ghost` `invoked-mismatch`
violation. So `skill_verdict_reason_check` itself still computes the
soft violation correctly; it is
`bc557df5:on-the-record/hooks/skill-verdict-guard.sh`'s reporting layer
(the `hard`/`soft` split at
`bc557df5:on-the-record/hooks/skill-verdict-guard.sh:323-335`) that
drops `soft` — and the once-per-session `reminder` — entirely whenever
`hard` is non-empty, returning before either is ever assembled into
output.

This is a genuine, reproduced gap against the issue's own `must not`
clause ("must not weaken the existing detection of a missing verdict
line"): in a session whose record carries both violation kinds at once,
the pre-existing #2039 missing-line signal for the *other* skill is
silently absent from this Stop turn's output — not corrected, not
mentioned, not deferred visibly, just missing that turn. It is not a
permanent loss (fixing `ghost` and triggering Stop again will
re-surface `bar`, since `bar` is still missing then and `hard` will be
empty), and it does not affect any of the three acceptance commands,
which all still pass exactly as the PR claims (re-derived above,
`canonical:` acceptance runs under "## What was done"). I judge
`verdict: correct-with-open-finding` rather than `Incorrect`: the
acceptance criteria as literally stated are met and re-derived by my
own execution, but the `must not` clause is violated in this one
co-occurrence case, which the PR's own test matrix
(equivalence-partitioned by line type x name membership, never by
"violation count per turn") does not cover.

## What did not work

None — derived: every acceptance command and edge-case probe above
(three `canonical:` acceptance runs, the not-applicable direct call,
the missing-transcript subprocess test, the `diff` mirror-file check,
and the hard+soft fixture reproduction) produced a definite pass or a
definite, reproduced gap; nothing was attempted and abandoned
half-way.

## Upstream basis

- PR #3068 (`bc557df536ea5a44ab2059a002644bb2fbdf8946`), branch
  `issue-3044/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3`
  — canonical: `gh pr view 3068` — result: state OPEN; canonical:
  `gh pr diff 3068` — result: the diff re-read and traced above.
- Subject deliverable record (PR branch only, not on this branch —
  cited commit-pinned):
  `bc557df536ea5a44ab2059a002644bb2fbdf8946:docs/issue-3044/reports/silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3.md`,
  `author: silent-failure-audit+secure-coding-input-validation-injection-defense+test-derivation+adversarial-review-0f4af9e3`
  (differs from this record's `author: independent-verification-2` —
  self-verification guard satisfied).
- Issue #3044 body — canonical: `gh issue view 3044` — the three
  acceptance checks and the `must not` list re-derived above.
- `docs/handbooks/observer-verification.md` (this branch,
  `same-commit`-adjacent, unmodified) — the `verifies_subject`/count
  mechanism this record's frontmatter participates in.

## Open findings

canonical: the hard+soft fixture reproduction under "## Why" above
(hook run in `/tmp/svg-indep-test` against `bc557df5`'s
`skill-verdict-guard.sh`, `reason` naming only `ghost` and omitting
`bar`) plus the three `canonical:` acceptance-command re-runs under
"## What was done" (all passing exactly as the PR claims).

1. `bc557df5:on-the-record/hooks/skill-verdict-guard.sh`'s hard/soft
   split (lines 323-335, added by this PR) discards `soft` violations
   and the `reminder` entirely whenever `hard` is non-empty, instead of
   including both in the block `reason` (or emitting `soft`/`reminder`
   via a follow-up mechanism, if the JSON payload only supports one
   top-level shape per Stop response). Concretely, reproduced above: a
   record with one hard `invoked-mismatch` and one soft
   missing-verdict-line violation in the same turn surfaces only the
   hard one; the soft one is silently absent from that turn's output,
   reappearing only on a subsequent Stop attempt once the hard
   violation is cleared. This does not fail any of the three literal
   acceptance commands (re-run and confirmed above, see the
   `canonical:` tag directly above) but is a real, reproduced instance
   of the issue's own must-not clause ("must not weaken the existing
   detection of a missing verdict line") in the co-occurrence case the
   PR's test matrix does not cover. Resolution path: either fold `soft`
   into the same `reason` string when `hard` fires, or file a small
   follow-up issue scoped to "co-occurring hard+soft skill-verdict
   violations in one Stop turn" — left to the maintainer/coding skill
   to pick, not fixed here (this record only verifies, per
   [[verify-finding-record]] and this session's own
   independent-verification scope).

## Next steps

None — this record is terminal (`loop_state: landed`). The open
finding above is a report, not a blocking defect against the PR's
literal acceptance criteria; it is left for a human or a future
coding-skill session to decide whether it warrants a follow-up PR.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; used to re-derive all three acceptance commands from a freshly checked-out worktree instead of citing the PR body's pasted output, and to deliberately construct a hard+soft co-occurrence edge case the PR's own equivalence-partitioned test matrix does not cover, rather than stopping once the three happy-path acceptance checks came back green
skill-verdict: verify-finding-record — not-applicable: this skill's procedure and file target (`docs/issue-<n>/reports/defect-verification.md`, a `reproduced`/`not-reproduced`/`blocked` outcome block) belong to a different record kind than this session's actual deliverable, `docs/issue-3044/reports/independent-verification-2.md` under the `verifies_subject` counted-verification mechanism (`docs/handbooks/observer-verification.md`) — no `defect-verification.md` file was in scope for this subject; the skill's rigor-independence spirit (record a not-reproduced/gap outcome with the same evidentiary weight as a reproduced one) was carried over into this record's own Open findings section instead
