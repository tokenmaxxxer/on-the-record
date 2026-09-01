---
issue: 2974
role: independent-verification-1
author: independent-verification-1
skills: work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2994's own deliverable, author differs from subject's author
loop_state: landed
upstream:
  - path: gates/check_runner.py, gates/merge_gate.py, gates/risk_report.py, on-the-record/hooks/impact-guard.sh, docs/specs/requirements.md, docs/specs/requirement-digest.md
    sha: 36b61cf339dce5651f8c94016d4da3c6233e7259
---

# issue-2974 — independent-verification-1 record

## What was done

Independently verified PR #2994 (`issue-2974/merge-gates+test-derivation-98d98713`,
head `36b61cf339dce5651f8c94016d4da3c6233e7259` — canonical: `gh pr view 2994
--json headRefName,baseRefName,files,commits` output this turn), which fixes
issue #2974's three lettered findings (empty R-ID canon, batch-merge risk
inherited from an unrelated proposal, record-only branches scored as
implementations). The PR's own claimed results were not trusted at face
value: its head was fetched into an isolated `git worktree`
(`git fetch origin issue-2974/merge-gates+test-derivation-98d98713 && git
worktree add /tmp/verify-2994 origin/issue-2974/merge-gates+test-derivation-98d98713`)
and every acceptance check was re-run there, and the diff of each changed
file was read in full against the issue's must-not list and the PR's own
stated rationale.

Acceptance checks, re-run in the isolated worktree:

acceptance: `python3 -m pytest gates/ -k record_only_pr_not_scored -q` — result:
```
2 passed in 0.88s
```

acceptance: `python3 -m pytest gates/ -k record_signal_disagreement -q` — result:
```
2 passed in 0.97s
```

acceptance: `python3 -m pytest gates/ -k batch_merge_unrelated_proposal -q` — result:
```
4 passed in 0.91s
```

acceptance: `python3 -m pytest gates/ -q` (full suite, regression check;
includes the new `gates/test_check_runner.py` and `gates/test_risk_report.py`
files this PR adds — untracked in this session's own worktree, present
only on PR #2994's branch head, confirmed present via `ls` inside
`/tmp/verify-2994` this session) — result:
```
42 passed in 0.89s
```

acceptance: `grep -c "^R[0-9]" docs/specs/requirement-digest.md` — result:
```
0
```
This literal check returns `0`, matching the PR's own disclosed deviation
— every digest entry is rendered `- R001: ...` with a bullet prefix, so
the anchored `^R[0-9]` pattern never matches any line regardless of how
many R-IDs the digest carries.

derived: `grep -c "R[0-9]" docs/specs/requirement-digest.md` (unanchored, counts the real entries) — result:
```
6
```

canonical: `git ls-files | grep -x "watchdog.py"` — result: `watchdog.py`
(repo root, tracked). derived: `grep -n "_DIGEST_LIVE_ENTRY_RE"
watchdog.py` — result:
```
820:_DIGEST_LIVE_ENTRY_RE = re.compile(
821:    r"^- (R\d+): (.+?) \[(\S+)\] \(source: (.+)\)$", re.M)
```
This confirms the regex does require the bullet-prefixed render format the
digest currently uses, so the PR's stated reason for not changing the
format (it would break this real consumer) names something that actually
exists in this checkout, not a rationalized excuse for a failing literal
check.

Diff audit, each changed file read in full against `origin/main` (`git diff
origin/main...HEAD -- <path>`, run in the isolated worktree this session):

- `gates/check_runner.py`: adds `pr_diff_paths()` (`gh pr diff <pr>
  --name-only`), `touches_implementation_paths()` (any path outside
  `docs/` counts as implementation; empty/unreadable diff fails closed to
  `True`, i.e. scored), and `frontmatter_record_only_signal()` (reads
  `kind:` off the diff's own `docs/issue-<n>/reports/*.md` files via
  `gates.record_frontmatter()`, matched against closed
  `_RECORD_ONLY_KINDS`/`_IMPLEMENTATION_KINDS` sets — confirmed these are
  literal strings, not derived from any role/skill/filename). `main()`
  computes both signals before running mechanical checks; the diff signal
  alone decides record-only/scored, disagreement between the two signals
  is appended as a note rather than resolved silently, in both directions
  (record-only-but-frontmatter-says-implementation, and the reverse) —
  confirmed both branches exist in `main()`.
- `gates/merge_gate.py`: `_RESULT_HEADER` and
  `parse_check_runner_result()` recognize the new `RECORD_ONLY_MARKER`
  ahead of the numeric-header parse, returning `{"record_only": True}`;
  `evaluate()` treats that as satisfied (no reason appended), distinct
  from the pre-existing `no_checks` fail-closed branch which still adds a
  refusal reason. Confirmed the two branches are structurally separate,
  not a shared code path that could collapse `record_only` into
  `no_checks` or vice versa.
- `gates/risk_report.py`: `batch_blocked()` gained an optional
  `batch_files: list[list[str]] | None = None` parameter. Confirmed the
  default (`None`) preserves every existing caller's behavior unchanged
  (no filtering applied), and that when `batch_files` is given, an
  individually-required proposal is dropped from the blocked list only
  when none of its own `files:` overlap (`_paths_overlap`, pre-existing
  glob-aware helper, reused not reimplemented) with any PR's write-set —
  a proposal the batch does implicate is never dropped by this filter,
  confirmed by reading the `if not axes["requires_individual_approval"]:
  continue` / overlap-check / `continue` control flow directly (the
  dominant-axis requirement itself is untouched; only which proposals
  apply to a given batch changed).
- `on-the-record/hooks/impact-guard.sh`: `_merge_pr_numbers()` resolves
  only the plain `gh pr merge <n>` shape (bare numeric token immediately
  after `merge`); any other shape returns `None` for the whole command.
  The call site resolves `batch_files` via `gh pr diff <n> --name-only`
  per PR; any resolution failure (unparseable command, `gh` failure) sets
  `batch_files = None`, which per the confirmed `risk_report.py` default
  above reproduces exactly the pre-#2974 behavior — no partial or guessed
  batch_files list is ever passed on failure. `bash -n
  on-the-record/hooks/impact-guard.sh` (re-run this session in the
  isolated worktree, exit 0) confirms no syntax break.
- `docs/specs/requirements.md` / `requirement-digest.md`: R005 and R006
  quotes checked verbatim against their cited source issues —
  `gh issue view 1664 --json body` contains the R005 quote
  ("a PR is refused when merging it would delete or overwrite content
  that exists at the base branch HEAD but was added by a commit the PR's
  merge-base does NOT contain...") word-for-word, and `gh issue view 511
  --json body` contains the R006 quote ("Dominant-axis rule: no
  summing/averaging across axes; worst reversibility grade alone forces
  individual human approval.") word-for-word — neither quote is
  fabricated or paraphrased. Both source issues are open and not tagged
  `infrastructure/no-direct-requirement`, matching the record's claim
  that they were deliberately chosen over the six watchdog-flagged issues
  (#2774/#2864/#2872/#2883/#2890/#2956) because those six's common parent
  issues legitimately carry the infra-exemption tag.

No must-not violation found: the requirement-ID gate was not loosened,
special-cased, or given a new escape tag; record-only status is decided
from the diff (primary) with frontmatter as corroboration only, never from
filename/branch/skill name; no PR that touches implementation paths is
skipped from scoring (the fail-closed default on unreadable diffs
confirms this); the batch-merge approval requirement for a proposal a
batch genuinely implicates is unchanged (the overlap check only narrows
which unrelated proposals apply, never weakens the dominant-axis rule
itself for an implicated one).

## Why

canonical: this record's own `## What was done` section above, which
holds the re-run acceptance output and the file-by-file diff audit this
paragraph explains the intent behind.

The task instruction was to read and audit PR #2994 rather than trust its
self-reported results, then flip `verifies_subject` to `true` only if this
record is an independent check of that PR's own deliverable — not a
second implementation attempt. Re-running the acceptance checks from an
isolated worktree (rather than reusing the PR author's own reported
numbers) and reading every changed-file diff against both the issue's
must-not list and the PR's own stated rationale is the concrete form that
independence takes here: it catches a claim that doesn't match the code,
not just a claim that doesn't match itself.

The literal `grep -c "^R[0-9]"` returning `0` was checked directly rather
than accepted from the PR's own text, since this task's instruction was
not to trust the PR's claimed results — the reproduced `0` and unanchored
`6`, and the `watchdog.py` regex confirmation, are recorded above rather
than accepted on the PR's word alone.

## What did not work

None.

## Upstream basis

canonical: `gh pr view 2994 --json headRefName,files` output this turn,
cross-checked against `ls` inside `/tmp/verify-2994` this session.

PR #2994, branch `issue-2974/merge-gates+test-derivation-98d98713`, head
commit `36b61cf339dce5651f8c94016d4da3c6233e7259` (fetched into an isolated
worktree at `/tmp/verify-2994` this session, distinct from this record's
own branch `issue-2974/independent-verification-1`). Changed files
verified: `gates/check_runner.py`, `gates/merge_gate.py`,
`gates/risk_report.py`, `on-the-record/hooks/impact-guard.sh`,
`docs/specs/requirements.md`, `docs/specs/requirement-digest.md`,
`gates/test_check_runner.py`, `gates/test_risk_report.py` (the last two
untracked on this session's own branch — present only on PR #2994's
branch, per the worktree confirmation above). Source issues read in full
for the R-ID quote check: #1664, #511.

## Open findings

None.

## Next steps

None — loop_state: landed.

skill-verdict: work-in-english — applied: invoked; followed the skill's
routing for this task (English record body, commit messages, and PR text;
Korean reserved for the final summary sent to the user).
other mounted skills: not triggered.
