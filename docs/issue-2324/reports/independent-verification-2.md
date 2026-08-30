---
issue: 2324
role: independent-verification-2
author: independent-verification-2
skills: work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2852's own deliverable (subject: diagnose-first-3c31bf9d)
code_under_review: docs/issue-2324/_assets/measure_batching_headroom.py (untracked here), tests/test_directive_diet_2135.py (untracked here), docs/issue-2324/reports/diagnose-first-3c31bf9d.md (untracked here) -- all three live only on PR #2852's branch issue-2324/diagnose-first-3c31bf9d, not on this branch
type: verification
breaking: false
verdict: confirmed — every reproducible claim in PR #2852 reproduces independently (diff scope, 7/7 new tests, full-suite pass/fail counts with identical failing-test names, role-axis/directive/watchdog acceptance checks, and the headroom arithmetic); one disclosed reproducibility caveat found by this audit (Open findings #1) does not change the STOP-AND-REPORT conclusion
loop_state: landed
upstream:
  - path: docs/issue-2324/reports/diagnose-first-3c31bf9d.md  # untracked on this branch
    sha: b5ad704a712b6c4e68c72e19311f2bc8baf409d9
  - path: docs/issue-2324/_assets/measure_batching_headroom.py  # untracked on this branch
    sha: b5ad704a712b6c4e68c72e19311f2bc8baf409d9
  - path: tests/test_directive_diet_2135.py  # untracked on this branch
    sha: b5ad704a712b6c4e68c72e19311f2bc8baf409d9
  - path: docs/handbooks/observer-verification.md
    sha: 0dc01bc3a1054f4546119dc225602bcc9086a9a6
---

# issue-2324 — independent-verification-2 record

## What was done

Independently audited PR #2852 (branch `issue-2324/diagnose-first-3c31bf9d`,
untracked on this branch — checked out separately into its own
worktree for this audit) — issue #2324's subject deliverable — against
its own claims, from a fresh `git worktree` at the PR head (`321af046`),
not by trusting the PR's citations verbatim:

- derived: `git worktree add /tmp/pr2852-verify origin/issue-2324/diagnose-first-3c31bf9d && git merge-base origin/main HEAD && git diff <merge-base> --stat`
  — result: exactly the 4 files the PR claims — `docs/issue-2324/_assets/measure_batching_headroom.py`
  (untracked on this branch), `docs/issue-2324/reports/diagnose-first-3c31bf9d.md`
  (untracked on this branch), its deviation-log entry (untracked on
  this branch), `tests/test_directive_diet_2135.py` (untracked on this
  branch) — `859 insertions(+), 0 deletions`. (A first diff against the
  live tip of `origin/main` showed spurious deletions because `main`
  had advanced past the PR's merge-base since branching; re-diffing
  against the actual merge-base cleared that up and matches
  `gh pr view 2852 --json files`'s own file list.)
- acceptance: `python3 -m pytest tests/test_directive_diet_2135.py -v`
  (untracked on this branch; run inside the PR worktree) — result: `7
  passed`. Read every test body: the `message.id`-grouping fixture, the
  independent-adjacent-pair fixture, and the empty-state
  serial-dependency fixture (Grep-finds-a-path → Read-that-exact-path
  must NOT count as batchable) all exercise real behavior of the
  measurement module, not tautologies.
- acceptance: `python3 -m pytest test/ tests/ -q` on the PR worktree —
  result: `462 passed, 15 failed, 3 xfailed`, and the 15 failing test
  names are byte-identical to the PR body's own pasted list — confirms
  the PR's claim that the branch introduces no new failures (the +7 is
  exactly the new gate test file, untracked on this branch).
- acceptance: `grep -n -iE "\brole\b" docs/issue-2324/_assets/measure_batching_headroom.py tests/test_directive_diet_2135.py`
  (both untracked on this branch; run inside the PR worktree) — result:
  no match (exit 1) — confirms the PR's claim (a).
- acceptance: `git diff <merge-base> --stat -- directive_assembly.py on-the-record/directive/ .on-the-record/directive/`
  — result: empty — confirms the PR's claim (c), no directive file
  touched.
- acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q`
  — result: `36 passed` — confirms the PR's claim (d).
- derived: re-ran the record's own pasted per-transcript rows through
  its own summation script,
  `python3 -c "rows=[(18,2,10,5),(67,0,16,3),(50,15,15,4),(36,1,8,2),(53,5,14,5),(77,6,19,7),(123,0,34,7),(70,0,20,4),(101,3,25,5),(118,5,51,15)]; total=sum(r[0] for r in rows); pairs=sum(r[3] for r in rows); print(total, pairs, f'{100*pairs/total:.2f}%')"`
  — result: `713 57 7.99%` — matches the record's headline number
  exactly; the sum-row arithmetic is not miscopied.
- derived: checked which of the 10 originally-cited session-log paths
  still exist under `$MUSTER_WORKSPACE_ROOT`:
```
for f in <the 10 paths in the record's own command block>; do
  [ -f "$MUSTER_WORKSPACE_ROOT/$f" ] && echo FOUND || echo MISSING
done
```
  result: 7 `FOUND`, 3 `MISSING` (`2827-diagnose-first-6c16a19d`,
  `2749-adversarial-review-71d5dd92`, `2749-silent-failure-audit-e9b54ddf`
  — cleaned up from the environment since the record's measurement).
  Re-ran `measure_batching_headroom.py` (untracked on this branch)
  against the 7 `FOUND` paths and diffed against the record's own
  table:
```
row (issue-role)                          record        re-measured
2749-adversarial-review-28904fd2          67,0,16,3     67,0,16,3    match
2847-diagnose-first-50e013fd              50,15,15,4    80,15,28,8   MISMATCH (see Open findings #1)
2830-diagnose-first-7c274fa6              36,1,8,2      36,1,8,2     match
2814-test-authoring                       53,5,14,5     53,5,14,5    match
2811-technical-writing-style-guide        123,0,34,7    123,0,34,7   match
2798-adversarial-review                   70,0,20,4     70,0,20,4    match
2135-diagnose-first+minimalism-scoping    101,3,25,5    101,3,25,5   match
```
  6 of 7 re-checked rows match exactly (shown in the code fence above);
  the one mismatch is analyzed in Open findings #1.

## Why

Per `docs/handbooks/observer-verification.md`'s counted, self-declared
`verifies_subject: true` mechanism, and the warrant protocol's
instruction to re-derive rather than restate, every checkable claim in
the PR was independently re-run rather than read and trusted: a fresh
worktree diffed against the exact merge-base (not the PR's own stated
file list) for the diff-scope claim, the actual pytest invocations for
every acceptance line, and the committed measurement script re-run
against the transcripts it cites rather than accepting the record's
table at face value. This is the same "re-derive from scratch" posture
`docs/issue-2749/reports/adversarial-review-71d5dd92.md` (a prior
independent-verification round in this same repo) used, applied here to
a measurement-only delivery instead of a code-behavior one.

## What did not work

None.

## Upstream basis

- `docs/issue-2324/reports/diagnose-first-3c31bf9d.md` (untracked on
  this branch, lives on PR #2852's branch, sha
  `b5ad704a712b6c4e68c72e19311f2bc8baf409d9`) — the subject deliverable
  record this audit verifies; read in full.
- `docs/issue-2324/_assets/measure_batching_headroom.py` (untracked on
  this branch, lives on PR #2852's branch, same sha) — read in full;
  derived: `python3 docs/issue-2324/_assets/measure_batching_headroom.py <7 available transcript paths>`
  — result: 6 of the 7 rows matched the subject record's own table
  exactly, one diverged (shown in the comparison code fence above and
  analyzed in Open findings #1).
- `tests/test_directive_diet_2135.py` (untracked on this branch, lives
  on PR #2852's branch, same sha) — read in full; acceptance:
  `python3 -m pytest tests/test_directive_diet_2135.py -v` — result:
  `7 passed`.
- `docs/handbooks/observer-verification.md` (sha
  `0dc01bc3a1054f4546119dc225602bcc9086a9a6`) — read for the
  `verifies_subject` semantics and self-verification guard (this
  record's `author: independent-verification-2` differs from the
  subject's own `author: diagnose-first-3c31bf9d`, satisfying the
  guard).

## Open findings

1. One of the 7 re-checkable transcripts diverged from the record's
   table: `on-the-record-issue-2847-diagnose-first-50e013fd.session.*.log`
   measured `(50, 15, 15, 4)` (total/multi/single/pairs) in the PR's
   record but measures `(80, 15, 28, 8)` here (derived and shown in the
   comparison table above) — the underlying log file is append-only and
   grew after the record's own snapshot was taken — derived:
   `stat -c '%y %n' "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2847-diagnose-first-50e013fd.session.20260830T134944.497939.log"`
   vs `date -u` — result: mtime was only ~14.5 minutes stale at audit
   time, close to the record's own >15-minute "not concurrently
   in-flight" selection threshold, consistent with the session that log
   belongs to having resumed or continued writing after being judged
   stale. This is a limitation of using live, growing per-session log
   files as a measurement source, not an arithmetic error in the PR:
   derived — recomputing the 10-row total with `(80,15,28,8)` in place
   of `(50,15,15,4)`:
```
python3 -c "
total=713-50+80; pairs=57-4+8
print(total, pairs, f'{100*pairs/total:.2f}%')
"
```
   result: `743 61 8.21%` — still below the 10-15% action threshold the
   PR's record set in advance, so the STOP-AND-REPORT conclusion is
   unaffected. Resolution path: none needed for this delivery's
   conclusion; a future measurement wanting bit-for-bit reproducibility
   should snapshot/copy transcripts before analysis rather than reading
   live per-session log files in place.
2. 3 of the 10 cited transcripts no longer exist under
   `$MUSTER_WORKSPACE_ROOT` at audit time (listed and derived above) —
   expected environment drift/cleanup, not something the subject record
   could have prevented, but it means this audit could independently
   re-check only 7 of the record's 10 rows rather than all 10.
3. The subject record's own disclosed limitations (missing
   MultiEdit-over-serial-Edit directive guidance, no true pre-#2262
   baseline available in this environment, and a crude
   >=15-character-token dependency heuristic) were read — canonical:
   `docs/issue-2324/reports/diagnose-first-3c31bf9d.md` (untracked on
   this branch, lives on PR #2852's branch), its own "Open findings"
   section — and judged reasonable, not independently re-derived, since
   they are explicitly-scoped limitations the subject record already
   discloses rather than claims presented as settled fact.

## Next steps

None — `loop_state: landed`. This record satisfies one of the two
required independent-verification slots for issue #2324's subject
(`diagnose-first-3c31bf9d`); the human-maintainer closure decision the
subject record leaves open (close on the basis #2262 substantially
covers Ask #1, or file a narrower MultiEdit-guidance follow-up) is
unaffected by this audit and is not decided here.

skill-verdict: work-in-english — applied: invoked; this record, the
commit, and the PR are written in English (the spawning task text was
in Korean).
