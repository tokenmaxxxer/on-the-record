---
issue: 3129
role: adversarial-review+silent-failure-audit+test-depth-audit-0be2218f
author: adversarial-review+silent-failure-audit+test-depth-audit-0be2218f
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's repair round 2 (commits 7957bda7, bf28bf93)
code_under_review: bf28bf93fe5491adbd17a4a54ea0297ebb12a78e
type: defect-verification-record
breaking: false
loop_state: landed
verdict: Worked example (cd into an absolute other-repo path) Present — acceptance: `python3
  /tmp/writer2_test/harness.py` (against bf28bf93) — result: marker keyed to
  `issue-42__tokenmaxxxer_study-companion.marker.json`, none written for on-the-record.
  `--repo`/`-R` flag placed after `gh issue edit <n>` Present — acceptance: same harness — result: marker
  keyed to the --repo target. Plain command, no cd, no --repo Present (baseline preserved) — acceptance: same
  harness — result: marker keyed to the session cwd's own repo. All three confirmed actually failing
  (keyed to the wrong, session-cwd repo) pre-repair — acceptance: `python3
  /tmp/writer2_test/harness_prefix.py` (against bedd1c72, the commit before 7957bda7) — result: all three
  keyed to `issue-42__tokenmaxxxer_on-the-record.marker.json`, wrong for the first two cases.
  Parser robustness against the orchestrator's actual command shapes — Incorrect: `cd /a && gh issue edit
  ... --body-file - <<'EOF' ... EOF` (heredoc), `cd /a; gh issue edit ...` (semicolon separator), and
  `(cd /a && gh issue edit ...)` (subshell) all silently mis-key the marker to the session cwd — acceptance:
  `python3 /tmp/writer2_test/attack.py` plus a re-run through the real `amendment-channel.sh` wrapper via
  `subprocess.run(cwd=<session cwd>)` — result: all three wrote `issue-42__tokenmaxxxer_on-the-record.marker.json`
  instead of the study-companion target, empty stderr on both the direct-call and wrapper runs.
  `gh -R owner/repo issue edit 42` (repo flag before the subcommand) Incorrect — acceptance: same wrapper
  re-run — result: empty stdout AND empty stderr, zero markers written, the command is never even recognized
  as a `gh issue edit`. `gh issue edit 42 -R owner/repo` and a relative `cd ../x && ...` (re-tested through
  the real hook wrapper with matching process cwd) both Present — acceptance: same wrapper re-run — result:
  correct target-repo marker both times. A `cd` inside a quoted, non-directory-change string Present —
  acceptance: same harness — result: correctly ignored, keyed to session cwd.
  Failure mode — unresolvable derived path -> no marker + stderr Present, re-confirmed — acceptance: two
  unresolvable roots (no origin remote; unparseable origin URL) against bf28bf93 — result: zero markers,
  the same "could not identify the repo" stderr line for both. Failure mode — never silently falls back to
  cwd — Incorrect, directly contradicted by the heredoc/semicolon/subshell cases above, which is exactly
  what the new code's own docstring at bf28bf93:on-the-record/hooks/amendment_channel.py:63-64 claims does
  not happen ("never a fallback to the session cwd").
  Cross-repo isolation Present — acceptance: two independently git-init'd repos, different origins, shared
  branch issue-42/some-role, against bf28bf93 — result: repo-b's worker got None, only repo-a's marker
  exists. Unresolvable-slug isolation Present — acceptance: as above — result: zero markers for either
  unresolvable root. Fire-once/stop-after-absorption Present — acceptance: `python3
  gates/probe_running_session_sees_amendment.py` and `python3 gates/probe_amendment_notice_fires_once.py`
  (from /tmp/pr3137-verify4) — result: `ok`, exit 0 both.
  Full suite Present — acceptance: `python3 -m pytest tests/ -q` (from /tmp/pr3137-verify4) — result: 304
  passed, 0 failed, derived: 304 - 301 = 3 new writer-side tests over PR #3159's own 301-passed baseline.
  acceptance: `python3 -m pytest test/ -q` — result: 15 failed, 548 passed, 3 xfailed, derived: `python3 -m
  pytest test/ -q 2>&1 | grep -c FAILED` — result: 15, same 5 files PR #3147/#3159 already derived as owned
  by #3091 (not re-derived against the merge-base again this round).
upstream:
  - path: PR #3137 (branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019)
    sha: bf28bf93fe5491adbd17a4a54ea0297ebb12a78e
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md (PR #3159)
    sha: 46998cf871ab1c1e94e1f6e5c8f4b6b7e5b1e5e5
---

# issue-3129 — adversarial-review+silent-failure-audit+test-depth-audit-0be2218f record

## What was done

canonical: `gh pr view 3137` output (head `bf28bf93fe5491adbd17a4a54ea0297ebb12a78e`)
and PR #3159's record
(`docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md`,
read first per the spawning prompt) — this session's assignment: grade
repair round 2 (commits `7957bda7` "derive gh issue edit's target repo,
not the raw session cwd" and `bf28bf93` "add cd-target and --repo test
coverage for the writer-side fix") against PR #3159's one confirmed
Incorrect finding — canonical: PR #3159 record's "Open findings" §1
("the marker path is derived from the raw `PostToolUse` payload `cwd`,
not the repo a `cd <other-repo> && gh issue edit ...` command actually
targets") — by running the real `run_hook` entrypoint (and the real
`amendment-channel.sh` wrapper for cases where process-vs-session cwd
matters), not by reading either record's numbers.

derived: `git fetch origin pull/3137/head:pr-3137-verify4 && git
worktree add /tmp/pr3137-verify4 pr-3137-verify4` — result: worktree at
head `bf28bf93`. A second worktree, `git worktree add /tmp/pr3137-prefix
bedd1c72`, was added to re-confirm the pre-repair failure mode. Neither
worktree was merged into or edited, per the spawning prompt's explicit
instruction not to edit or merge PR #3137.

### 1. The three cases the repair was told to add

canonical: `bf28bf93:on-the-record/hooks/amendment_channel.py:378-397`
(`target_repo_for_command`) checks an explicit `--repo`/`-R` flag first
(`_explicit_repo_flag`, `:354-375`), else resolves the command's `cd`
target via `hook_input.resolved_cwd` (`hook_input.py:243-256`) before
calling `repo_slug_for_cwd`.

derived: script at `/tmp/writer2_test/harness.py`, three cases via the
real `run_hook`, run against `bf28bf93` — acceptance: `python3
/tmp/writer2_test/harness.py` — result:

```
worked-example-cd-abs -> None markers: ['issue-42__tokenmaxxxer_study-companion.marker.json']
explicit---repo-flag -> None markers: ['issue-42__tokenmaxxxer_study-companion.marker.json']
no-cd-no-repo -> [amendment] ... markers: ['issue-42__tokenmaxxxer_on-the-record.marker.json']
```

All three key correctly (the cd-target repo, the --repo-flag repo, and
the session cwd respectively when neither applies). **Present** for all
three. The third case notifying immediately is expected: the write and
the read happen in the same `run_hook` call, and the session writing the
marker also owns the repo it just wrote to.

acceptance: `python3 /tmp/writer2_test/harness_prefix.py` (same three
cases, same script, run against `bedd1c72` — the commit immediately
before `7957bda7`) — result: all three keyed to
`issue-42__tokenmaxxxer_on-the-record.marker.json` (the SESSION cwd,
wrong for the first two cases), confirming each was actually failing
before this repair round, not already passing.

canonical: `bf28bf93:tests/test_amendment_channel.py:504-583`
(`WriterSideTargetsCommandNotSessionCwd`, added by `bf28bf93`) covers
this same shape inside the suite with both positive (marker exists,
right content) and negative (wrong-key marker absent) assertions —
derived: `sed -n '504,583p' bf28bf93:tests/test_amendment_channel.py |
grep -c '    def test_'` — result: 3
(`test_cd_into_another_checkout_keys_the_marker_to_that_checkout`,
`test_explicit_repo_flag_overrides_cwd`,
`test_no_cd_no_repo_flag_still_keys_to_session_cwd`) —
`test-depth-audit`: Genuine Assertion, not Execution-Only.

### 2. Attacking the parser with the orchestrator's actual command shapes

The task named five concrete shapes the orchestrator issues today, plus
a relative cd and a quoted-non-cd decoy. derived: two harnesses —
`/tmp/writer2_test/attack.py` (direct `run_hook` calls) and a second
pass through the real `amendment-channel.sh` wrapper via `subprocess.run`
with `cwd=<session cwd>` and the payload on stdin (the accurate
production invocation shape, since `hook_input.resolved_cwd`'s relative-path
branch and `repo_slug_for_cwd`'s `os.path.isdir` call resolve relative to
the *process's actual* OS cwd, not the payload's declared `cwd` field —
direct `ac.run_hook()` calls from an unrelated launch directory would
misreport a relative-cd case as broken when it is not, see "What did not
work" below).

acceptance: `python3 /tmp/writer2_test/attack.py` — result:

```
cd /a && gh issue edit 42 --body-file - <<'EOF' ... EOF   -> WRONG marker (on-the-record), no stderr
cd /a; gh issue edit 42 ...                                -> WRONG marker (on-the-record), no stderr
(cd /a && gh issue edit 42 ...)                             -> WRONG marker (on-the-record), no stderr
  (also leaks the closing ")" into the note text -- cosmetic, secondary)
gh -R owner/repo issue edit 42                              -> NOTHING: no marker, no notice, no stderr
gh issue edit 42 -R owner/repo                               -> correct marker (study-companion)
cd ../study-companion-checkout && gh issue edit 42 ...       -> correct marker (via real wrapper re-run)
gh issue edit 42 --body 'please cd into the right place'    -> correct marker (cwd), "cd" in body ignored
```

acceptance: re-run of the first four cases through the real
`amendment-channel.sh` wrapper (stdout/stderr captured separately) —
result: heredoc, semicolon, and subshell cases each produced a
`{"hookSpecificOutput": ...}` JSON blob on stdout announcing an
amendment to the WRONG repo, with empty stderr in all three; `gh -R`
before the subcommand produced empty stdout AND empty stderr — the
command is invisible to the channel entirely.

canonical: `bf28bf93:on-the-record/hooks/hook_input.py:160-163`
(`_has_heredoc`) and `:176-207` (`cd_target`) — a heredoc, unbalanced
quotes, or an oversize command all short-circuit to `OpaqueCommand`
*before* the `_CD_RE` match is even attempted; canonical:
`bf28bf93:on-the-record/hooks/hook_input.py:101`
(`_CD_RE = re.compile(r"^\s*cd\s+(\S+)\s*&&")`) is anchored to the start
of the string and requires a literal `&&` — a leading `;` (semicolon
form) or a leading `(` (subshell form) never matches at all, same as
`OpaqueCommand`. canonical: `bf28bf93:on-the-record/hooks/hook_input.py:243-256`
(`resolved_cwd`) returns `default` (the caller's raw `cwd`, i.e. the
session cwd) for BOTH the `OpaqueCommand` and `NoCdTarget` results, with
no distinction between "there genuinely was no cd" and "the cd couldn't
be structurally trusted" — the second case is silently treated the same
as the first, which is exactly the silent-fallback shape.

canonical: `bf28bf93:on-the-record/hooks/amendment_channel.py:63-64`
(module docstring, added by `7957bda7`): "Neither source resolving falls
through to the same unresolvable-repo handling below -- never a fallback
to the session cwd." This claim is contradicted by the heredoc,
semicolon, and subshell reproductions above — each one falls through to
exactly the session cwd, the opposite of the repair's own stated design
guarantee in the same commit that introduces it.

derived: `grep -n "heredoc\|<<\|; gh\|(cd \|-R " bf28bf93:tests/test_amendment_channel.py`
run from `/tmp/pr3137-verify4` — result: the only matches are the two
`--repo`/`-R`-after-subcommand cases already in
`WriterSideTargetsCommandNotSessionCwd` (§1 above); zero coverage
anywhere in the suite for a heredoc body, a `;`-separated `cd`, a
subshell-wrapped `cd`, or a `-R` flag placed before the `gh` subcommand.
**Incorrect** overall for this section: the repair closes the one
literal worked example given to it (`cd <path> && gh issue edit ...
--body '...'`) but not the family of equivalent real-world shapes the
task itself names as what the orchestrator actually issues today — a
parser that handles the worked example and nothing else has moved the
collision rather than closed it, per the task's own framing.

### 3. The two failure modes of getting the target wrong

canonical: `bf28bf93:on-the-record/hooks/amendment_channel.py:415-430`
(`maybe_write_from_command`) — when `target_repo_for_command` returns
`None` (a resolvable-but-unidentifiable target, e.g. no origin remote or
an unparseable origin URL at the derived path), no marker is written and
one stderr line is emitted naming the failure (issue #3128's rule).
Present, re-confirmed — acceptance: unresolvable-slug reproduction in
§4 below — result: same stderr text PR #3159's record quoted for round 1.

Incorrect for "never falls back to the cwd silently": §2 above is
exactly this failure mode under a different name — three of the seven
tested command shapes (heredoc, semicolon, subshell) resolve to
`OpaqueCommand`/no-`&&`-match, and `resolved_cwd`'s `default=cwd`
fallback silently substitutes the session cwd as if it were a
legitimately resolved target, with no stderr distinguishing "couldn't
parse the cd" from "there was no cd to parse." `silent-failure-audit`:
this is a Silently Absorbed failure path, not a Handled one — canonical:
the docstring quote in §2 above asserts the opposite happens.

### 4. Cross-repo isolation, unresolvable-slug isolation, fire-once/absorption -- re-run

acceptance: cross-repo reproduction (two independently `git init`'d
repos, different origins, shared branch `issue-42/some-role`) re-run
against `bf28bf93` — result: repo-a orchestrator's marker written
(`issue-42__orgA_repo-a.marker.json`), repo-b worker got `None`, exactly
one marker file exists. Present.

acceptance: unresolvable-slug reproduction (no-origin-remote root,
unparseable-origin-URL root) re-run against `bf28bf93` — result: both
produced `None` and the same "could not identify the repo" stderr line,
zero marker files written for either. Present.

acceptance: `python3 gates/probe_running_session_sees_amendment.py`
(from `/tmp/pr3137-verify4`) — result: `ok`, exit 0. acceptance:
`python3 gates/probe_amendment_notice_fires_once.py` (from
`/tmp/pr3137-verify4`) — result: `ok`, exit 0. canonical:
`docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md`
§3 (PR #3159, already read both probes' full bodies against `bedd1c72`
and confirmed exact-count/content-bearing, not execution-only) —
derived: `diff <(git -C /tmp/pr3137-prefix show
bedd1c72:gates/probe_amendment_notice_fires_once.py)
/tmp/pr3137-verify4/gates/probe_amendment_notice_fires_once.py` and the
same for `probe_running_session_sees_amendment.py` — result: empty diff
for both files, neither probe changed by commits `7957bda7`/`bf28bf93`;
this session's own exit-0 re-run above confirms they still pass against
the new head, not merely that the source is byte-identical. Present.

### 5. Full suite

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q`
(from `/tmp/pr3137-verify4`) — result:

```
50 passed in 0.90s
```

derived: 50 - 47 = 3, exactly the 3 new
`WriterSideTargetsCommandNotSessionCwd` tests counted in §1 above.
Present.

acceptance: `python3 -m pytest tests/ -q` (from `/tmp/pr3137-verify4`)
— result:

```
304 passed, 2 warnings
```

(the 2 warnings are pre-existing pinned-fixture-divergence notices from
`test_skill_candidates_floor.py`, unrelated to this module) — derived:
304 - 301 = 3, matching the 3 new tests (PR #3159's record cited
`tests/` at 301 passed against `bedd1c72`). Present.

acceptance: `python3 -m pytest test/ -q` (from `/tmp/pr3137-verify4`,
not an owned acceptance check for this issue, run for completeness) —
result:

```
15 failed, 548 passed, 3 xfailed
```

derived: `python3 -m pytest test/ -q 2>&1 | grep -c FAILED` — result:
15; the FAILED lines name the same 5 files
(`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) PR #3147 and PR #3159
already independently confirmed pre-existing and owned by #3091; none of
the 15 names touch anything either repair-round commit changed. Present.

## Why

Every acceptance number above was re-derived against `bf28bf93` directly
rather than cited from PR #3159's record, and the pre-repair failure was
independently re-confirmed against `bedd1c72` rather than assumed from
PR #3159's own finding. Per `adversarial-review`'s blind-evaluator
stance, this session did not stop at the task's one worked example
(`cd <path> && gh issue edit ...`) or at `bf28bf93`'s own suite passing
— acceptance: `python3 -m pytest tests/test_amendment_channel.py -q`
(from `/tmp/pr3137-verify4`) — result:

```
50 passed in 0.90s
```

all green, yet §2's independently constructed heredoc/semicolon/subshell/
`-R`-before-subcommand cases above still reproduce the wrong-repo write
the suite does not cover — the repair's green suite does not certify it
against the family of real command shapes the task named. Per
`silent-failure-audit`, the central question for §2/§3 was not "does the
wrong-repo write crash" but "is it observable" — it is not: no stderr,
no stdout diagnostic, nothing distinguishes a correctly-resolved cd from
a heredoc that silently degraded to the session cwd. Per
`test-depth-audit`, `WriterSideTargetsCommandNotSessionCwd` was read in
full and classified Genuine Assertion (both positive and negative
assertions on marker existence/content, §1 above), not Execution-Only —
derived: same `grep -n "heredoc\|<<\|; gh\|(cd \|-R "
bf28bf93:tests/test_amendment_channel.py` command as §2 above, zero
matches for the four attacked shapes — the audit finding here is a
coverage gap, not a weakness in the tests that do exist.

## What did not work

None of this session's own reproductions failed to run — every script
in `/tmp/writer2_test/` executed on the first attempt. One methodological
correction happened mid-session, not a retry: the initial direct
`ac.run_hook()` call for the relative-cd case
(`cd ../study-companion-checkout && ...`) appeared to fail when run
directly from Python, but that was traced to the harness script's own
process cwd not matching the session's declared `cwd` — canonical:
`bf28bf93:on-the-record/hooks/hook_input.py:243-256` (`resolved_cwd`)
returns the raw, unjoined `cd`-target path, and
`bf28bf93:on-the-record/hooks/amendment_channel.py:163`
(`repo_slug_for_cwd`'s `os.path.isdir(cwd)` check) resolves a relative
path against the actual OS process cwd, not the payload's `cwd` field.
Re-run through the real `amendment-channel.sh` wrapper with
`subprocess.run(..., cwd=<session cwd>)` (the way the hook is genuinely
invoked) showed the relative-cd case resolves correctly — recorded in §2
above as Present, not folded into the Incorrect findings, since it does
not reproduce under the real invocation path.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used the
blind-evaluator stance to go past the task's one worked example and
build four additional real-world command shapes (heredoc, semicolon,
subshell, `-R`-before-subcommand, §2 above) rather than stopping at
`bf28bf93`'s own suite passing — see the "Why" section's acceptance/
result citation for the suite's own green run alongside the independent
reproductions that still break it.

skill-verdict: silent-failure-audit — applied: invoked; the central
finding in this record (§2/§3) is a silent-failure classification: the
heredoc/semicolon/subshell cases are a Silently Absorbed failure path
(wrong-repo write, zero stderr, contradicting the code's own docstring
claim at `bf28bf93:on-the-record/hooks/amendment_channel.py:63-64`), not
a Handled one; the unresolvable-slug path was re-confirmed Handled
(stderr present, no marker, §3/§4 above).

skill-verdict: test-depth-audit — applied: invoked; classified
`bf28bf93`'s new `WriterSideTargetsCommandNotSessionCwd` suite (3
tests — derived: same `grep -c '    def test_'` count as §1 above) as
Genuine Assertion (checks both the correct marker's existence/content
and the wrong marker's absence) — derived: `grep -n
"heredoc\|<<\|; gh\|(cd \|-R " bf28bf93:tests/test_amendment_channel.py`
run from `/tmp/pr3137-verify4` — result: only the two `--repo`/`-R`-
after-subcommand matches already in
`WriterSideTargetsCommandNotSessionCwd`, zero matches for
heredoc/semicolon/subshell/`-R`-before-subcommand — the reason the
suite's own green run does not certify the parser against those shapes.

skill-verdict: work-in-english — applied: invoked; this record, every
scratch script, and all commit messages this session writes are in
English; the end-of-turn summary to the user follows in Korean per
policy.

other mounted skills: not triggered — `implementation-audit`,
`conformance-review-finding-record`, `product-discovery-guardrail-metrics`,
and `upstream-defect-report-convention` (configured by task-text match,
not this role's own mounted set) did not apply: this record already
follows `implementation-audit`'s Present/Surface/Absent/Incorrect/
Unverifiable taxonomy without a separate invocation; derived: `git
ls-files '**/conformance-review*'` — result: no matches, so
`conformance-review-finding-record`'s trigger path does not exist in
this repository; this session is not in a product-discovery
hypothesis-registered phase; and this session is verifying an internal
repair round, not preparing an upstream defect report.

## Upstream basis

- PR #3137, branch
  `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`,
  head `bf28bf93fe5491adbd17a4a54ea0297ebb12a78e` (canonical: `gh pr
  view 3137` output and the fetched worktree at that head; not
  same-commit with this record; this session did not edit or merge this
  PR, per the spawning prompt's explicit instruction). Repair round 2 is
  commits `7957bda7` and `bf28bf93`, applied on top of the round-1 head
  `bedd1c72` PR #3159 already verified.
- PR #3159's record
  (`docs/issue-3129/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac.md`,
  merged via `46998cf8`) — read first per this session's spawning
  instructions, but every number and reproduction in this record was
  independently re-derived against `bf28bf93`, not cited from that
  record.
- Issue #3128 ("The repo-attribution fixes reopen their own leak when
  `_repo_slug()` cannot resolve") — its must-not clauses ("do not
  invent a fallback identifier ... a path hash, a cwd basename, or
  anything else that can collide") remain the acceptance bar for the
  unresolvable-slug path (§3 above, still Present), and its "if two
  roots genuinely cannot be told apart, each must report that it cannot"
  clause is the standard §2/§3's Incorrect finding fails against for the
  heredoc/semicolon/subshell cases (they do not report; they silently
  substitute).

## Open findings

1. Writer-side repo-keying breaks under three real command shapes the
   orchestrator actually issues (Incorrect, confirmed reproduced — full
   repro in §2/§3 above): `cd <other-repo> && gh issue edit ...
   --body-file - <<'EOF' ... EOF`, `cd <other-repo>; gh issue edit ...`,
   and `(cd <other-repo> && gh issue edit ...)` all silently key the
   marker to the orchestrator's own session cwd instead of the `cd`
   target, with zero stderr trace, directly contradicting the repair's
   own new docstring claim (`bf28bf93:on-the-record/hooks/amendment_channel.py:63-64`,
   "never a fallback to the session cwd"). Root cause:
   `hook_input.cd_target()` (`hook_input.py:176-207`) returns
   `OpaqueCommand` for a heredoc/unbalanced-quote command and
   `NoCdTarget` for a non-`&&`-anchored `cd` (semicolon, subshell), and
   `resolved_cwd()` (`hook_input.py:243-256`) treats both identically to
   "genuinely no cd prefix," silently returning `default` (the session
   cwd) in all three cases. Resolution path: `maybe_write_from_command`
   should treat `OpaqueCommand` (and a `cd`-shaped-but-unmatched prefix,
   if detectable) as itself an unresolvable-target case — routed through
   the same "no marker + stderr" branch issue #3128 already established
   for a `None` repo slug, not through the cwd-fallback branch meant only
   for the case where the command genuinely never `cd`s anywhere.
2. `gh -R owner/repo issue edit <n>` (repo flag before the subcommand)
   is a total silent miss, not a wrong-key write (Incorrect, confirmed
   reproduced in §2 above): `_GH_ISSUE_EDIT_RE`
   (`amendment_channel.py:122-124`) requires `gh`, `issue`, and `edit` as
   three literally adjacent tokens (only whitespace between them), so
   this shape never matches at all — no marker, no notice, and (unlike
   the unresolvable-slug case) no stderr line either, since the code
   never reaches the branch that would emit one. Pre-existing regex gap,
   not introduced by this repair round, but squarely inside what the
   task asked this session to try. Resolution path (optional, smaller
   than finding 1): loosen `_GH_ISSUE_EDIT_RE` to tolerate flags between
   `gh` and `issue edit`, or scan for `-R`/`--repo` anywhere before the
   `issue edit <n>` match, not only after it.
3. Cosmetic: the subshell case's trailing `)` leaks into the extracted
   note text (`(cd /a && gh issue edit 42 --body 'x')` produced a note
   of `"x)"`, see §2) — secondary to finding 1, not separately gating.
4. Carried forward, unchanged by this repair round (PR #3147's/#3159's
   minor findings, out of this round's stated scope): silent truncation
   at `_NOTE_MAX` with no truncation marker; `main()`'s stdin/stdout
   `OSError` paths still silently drop; the two-no-origin-remote-only
   unresolvable-slug test-coverage thinness PR #3159 noted. Not
   re-litigated further here.

## Next steps

Finding 1 is the one that should gate before this PR lands — it is the
same collision class this repair round exists to close, reopened by
three command shapes the task's own text names as what the orchestrator
actually issues today, not exotic edge cases. Finding 2 is real but
narrower (a total miss, not a wrong-repo write) and pre-existing to this
specific repair round. Findings 3-4 are minor/carried-forward. This
session does not edit or merge PR #3137, per the spawning prompt's
explicit instruction; these findings are handed to whoever picks the PR
up next.

`loop_state: landed` — derived: this record's §1-§5 above, each with
its own `acceptance:`/`derived:` command and result, cover every check
the spawning prompt assigned (the three named cases, the parser attack
set, both failure modes, cross-repo/unresolvable-slug/fire-once
re-confirmation, and the full suite); no further action is planned from
this session itself.
