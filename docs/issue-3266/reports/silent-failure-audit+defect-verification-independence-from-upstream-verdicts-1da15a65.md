---
issue: 3266
role: silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1da15a65
author: silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1da15a65
skills: silent-failure-audit (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3269's own deliverable
loop_state: terminal (verification-complete)
upstream:
  - path: PR #3269 (branch issue-3266/silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0)
    sha: 9f25370868cff8f7a156457e7510105b2eff30ae
---

# issue-3266 — silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1da15a65 record

## What was done

Second independent verification of PR #3269, structurally separate from any
sibling verification, focused on the failure-reporting angle (not plain
correctness): does the new classifier ever silently treat an undecidable
file as a decided "stub", and does the deletion path tell the operator what
it decided and why. All checks below were run against a real checkout of
PR #3269's head (`9f253708`, via `git worktree add --detach /tmp/wt-pr3269
pr-3269-review`) and, where comparative, against `main` (`17823cb4`, via
`/tmp/wt-main`) on this machine, independently of the PR description and the
orchestrator's prior comment.

canonical: `gh pr view 3269` (state OPEN, body, test plan) and `gh issue view
3266 --comments` (issue body + orchestrator's re-measurement comment), both
read fresh this session.

**1. Undecidable-file handling.** Constructed each named failure mode
against the real predicate `_report_stub_has_no_content()` from PR head
(`/tmp/wt-pr3269/lifecycle.py`), via file-based Python probes (not inline
Bash, to avoid the board-gate's literal-path scan):
```
permission_denied_real_content: False   (0o000 file, real content underneath)
missing_path: False                     (file removed before the call)
symlink_to_real_content: False          (symlink -> file with real prose)
dangling_symlink: False                 (symlink -> nonexistent target)
symlink_self_loop: False                (symlink -> itself, ELOOP)
directory_not_file: False               (a directory sits at the .md path)
control_real_stub: True                 (actual empty skeleton -- control)
large_50mb_stub_shaped: True            (50MB stub-shaped file, 0.31s, no hang)
invalid_utf8_garbage_line: False        (non-UTF-8 bytes -- read_text(errors="replace") never raises)
invalid_utf8_real_content: False        (same, but real prose survives replace)
zero_byte_file: True                    (0-byte file -- correctly "no content")
symlink_outside_to_stub_shape: True     (symlink escaping the workspace to an external stub-shaped file)
fifo_special_file: BLOCKS INDEFINITELY  (os.mkfifo path; read_text() blocks forever, no timeout -- see Open findings 2)
```
`derived:` the four scripts run to produce this table were
`/tmp/pr3269-check/probe.py`, `probe2.py`, `probe3.py`/`probe4.py` (FIFO
timing), all executed via `python3 <script>.py` against the PR-head
checkout; every OSError-raising case (permission denied, missing path,
symlink loop, directory-at-path) correctly returns `False` (treated as
"has content", i.e. NOT reclaimable) because the function's only error
handling is a bare `except OSError: return False` around
`(w / rel).read_text(...)` -- it fails closed on every synchronous read
error I could construct. The one shape that does not fail closed is the
FIFO: `open()`/`read_text()` on a named pipe with no writer blocks
indefinitely inside the `try`, so no exception is ever raised to hit that
`except OSError` -- there is no timeout anywhere in the call chain. This
does not misclassify a workspace as reclaimable (worse: it wedges the
whole `clean` sweep on that one workspace, with no diagnostic). See Open
finding 2.

One further gap: `symlink_outside_to_stub_shape` classifies `True` (stub,
reclaimable) for a symlink under `docs/issue-N/reports/*.md` that points
*outside* the workspace to a file that happens to look like an empty
stub. `read_text()` dereferences symlinks transparently, so the predicate
silently answers a different question than the one it's asked ("does this
external target look empty" instead of "does this workspace's own file
have content"). Low real-world likelihood (no normal session or the
harness itself creates such a symlink), but it is a genuine undecidable-vs-
decided conflation matching this audit's angle. See Open finding 3.

**2. Does the deletion path say what it decided and why?** Read
`roster_clean()` and `_workspace_clean_state()` in full
(`lifecycle.py:1144-1183`, `:928-1002` on PR head). The only operator-facing
output is:
```
print(f"남김 ({detail}): {w.name}")     # kept, with a coarse counts-only detail
print(f"지움: {w.name}")                # deleted -- bare workspace name only
```
`detail` (built at `lifecycle.py:996-1002`) reports counts like `[미추적
파일 N건]` / `[내용 변경 N건]` / `[미push 커밋 N건]` for *kept* workspaces,
but the moment a workspace crosses into "지움" (deleted, `shutil.rmtree`),
there is no line anywhere -- not in `roster_clean`, not in
`_delete_workspace`, not in the two new predicates -- that names which
specific untracked file(s) were judged harness-scaffolding vs. content-free
stub, or even that the new classifier is why this workspace's untracked
count dropped to zero. `grep -n "print" lifecycle.py` inside
`_is_harness_scaffolding_path`, `_report_stub_has_no_content`,
`_is_reclaimable_untracked_noise`, and `_delete_workspace` returns nothing.
See Open finding 1.

**3. Re-derived headline numbers myself.** `spawn.py clean` has no working
`--dry-run`: `--dry-run` is a single top-level argparse flag consumed only
by the spawn/launch path (`spawn.py:3023`) and `sweep-orphans`
(`spawn.py:2938`); the `clean` dispatch
(`spawn.py:2935-2936`, unchanged by this PR --
`git diff main...pr-3269-review -- spawn.py` shows zero `dry_run` lines)
calls `roster_clean(_workspace_base(), a.issue, Path(a.cwd).resolve())`
unconditionally, with no `dry_run` parameter at all. Argparse accepts
`--dry-run` on `clean` without error (it's global), but it has zero effect
-- `spawn.py clean --dry-run` performs real, irreversible `shutil.rmtree()`
deletions. This means the orchestrator's own re-measurement comment on
issue #3266 ("I re-measured `spawn.py clean --dry-run` ... PR #3269: 지움
1, 남김 32 / main: 지움 0, 남김 32") was not a dry run -- it deleted one
real workspace on this shared machine. This is pre-existing on `main`,
not introduced by PR #3269, but it made the literal instruction in my own
task ("run `spawn.py clean --dry-run` on the PR head and on main back to
back") unsafe to follow verbatim on a machine with a sibling verification
session running concurrently. I did not run the real CLI. Instead I
built a read-only re-derivation (`/tmp/dryrun_probe.py`) that imports
`roster_clean`'s own dependencies from a full worktree checkout of each ref
(`/tmp/wt-main` = `main` @ `17823cb4`, `/tmp/wt-pr3269` = PR head @
`9f253708`) and calls the same `_sp._workspace_clean_state()` per
workspace under `~/.tokenmaxxxer/work` that `roster_clean()` calls, without
ever invoking `_delete_workspace`. Result, run back to back against the
34 live workspaces on this machine right now:
```
[main]    지움(would) 0, 남김 34
[pr3269]  지움(would) 0, 남김 34
```
This differs from the PR's and orchestrator's own snapshot (32 total, PR
reclaims 1) only because machine state moved on since their measurement --
consistent with their "지움 1" having been a real deletion that already
consumed the one reclaimable workspace, not a discrepancy in the fix
itself. To check the fix is still doing something on the *current* machine
state even though the totals now tie, I diffed per-workspace
`_workspace_clean_state()` output between the two refs
(`/tmp/dryrun_probe2.py`): 14 of the 34 workspaces show a strictly lower
`[미추적 파일 N건]` count under the PR (four even drop that clause
entirely), and in every one of those 14 the workspace remains `dirty`
because of a *different*, untouched cause -- almost always
`[미push 커밋 N건]`. Zero workspaces flip in the unsafe direction (kept on
`main`, reclaimed on PR, for a real reason). This matches the orchestrator's
own conclusion: the classifier fires correctly and safely, but on this
machine right now the residual "남김" causes are elsewhere, so the fix does
not move the headline "298 kept" number by itself. I reached the same
conclusion via an independent re-derivation, not by citing their comment.

**4. Must-nots.** Built four synthetic git fixtures (`/tmp/mustnot_probe.py`,
real bare-remote clones, not the salvage corpus) against PR head:
```
real_report_content_untracked:        ('dirty', '... [미추적 파일 1건]')
unstaged_content_change:              ('dirty', '... [내용 변경 1건]')
unpushed_unique_commit:               ('dirty', '... [미push 커밋 1건]')
squash_merge_diff_sha_same_content:   ('dirty', '... [미push 커밋 1건]')
```
All four stay `dirty` (blocked from reclamation) on PR head, as required.
The fourth case simulates the squash-merge shape directly: a second clone
pushes a *different*-SHA commit with the same net content to the shared
remote, without this workspace ever fetching -- it stays protected
(`dirty`), not wrongly reclaimed. Per instruction, I did not treat the
PR's own commits being absent from `main` by SHA (this repo squash-merges)
as evidence of anything lost -- that absence is expected and orthogonal to
whether the classifier itself protects real work, which is what this
section verifies directly against the predicate, not by inspecting `main`'s
history for PR #3269's commit SHAs.

Also independently ran both acceptance checks on PR head:
`python3 -m pytest tests/test_issue_3266_reclaimable_stub.py -q` -- 4
passed; `python3 -m pytest test/test_workspace_dirty_classification.py -q`
-- 12 passed. Both match the PR description's own claim.

## Why

The assignment was explicitly to verify independently of the first
sibling's derivation and of the PR/orchestrator's own verdicts -- so every
number above was re-derived from the real predicate and real git fixtures
on this machine, not read out of the PR description or the issue comment
and restated.

## What did not work

None.

## Upstream basis

- PR #3269 head commit `9f25370868cff8f7a156457e7510105b2eff30ae` (branch
  `issue-3266/silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0`),
  fetched as `refs/pull/3269/head` this session.
- `main` @ `17823cb4318d7f0ecf4609424f7f9b34b4e4347f` at time of
  verification.
- Issue #3266 body and its 4 comments (including the orchestrator's
  2026-09-03 re-measurement comment) -- read via `gh issue view 3266
  --comments` this session.

## Open findings

derived: `git diff main...pr-3269-review -- spawn.py` (run this session,
against the same two refs above) -- output contained zero lines mentioning
`dry_run`, confirming the `--dry-run`/`clean`-dispatch gap named in finding
4 below is pre-existing on `main` and untouched by this PR, not introduced
by it.

1. **Deletion path names no reason.** `roster_clean()`'s only
   operator-facing line for a deleted workspace is `지움: {w.name}` --
   no mention that a report file was judged a content-free stub, no file
   name, no indication the new classifier (vs. some other pre-existing
   reason) is why the workspace's untracked count reached zero. If the
   stub predicate is ever wrong on a real report, the operator finds out
   only by having already lost the file, with nothing in the clean output
   pointing back at the decision. Resolution path: have
   `_workspace_untracked_not_ignored()` (or its caller) return/log which
   excluded paths were scaffolding vs. stub, and have `roster_clean()`
   print that alongside `지움: {w.name}` for deletions that relied on the
   new exclusion. Not fixed by PR #3269; unresolved.

2. **FIFO under a report path hangs the classifier indefinitely.**
   `_report_stub_has_no_content()`'s only guard is `except OSError`
   around `read_text()`; a named pipe (`os.mkfifo`) at a
   `docs/issue-N/reports/*.md` path blocks the read forever (verified:
   still blocked after 5s with `timeout 5`, only returns once an
   externally-injected 2s `SIGALRM` interrupts it -- and `TimeoutError`
   being an `OSError` subclass is *why* that interrupt gets silently
   absorbed as "no content" rather than surfacing as a hang). Production
   code has no such alarm, so this wedges the whole `clean` sweep on that
   one workspace with zero diagnostic output. Low real-world likelihood
   (no normal session creates a FIFO there), but it is a genuine
   liveness gap in exactly the shape this audit was asked to probe. Not
   fixed by PR #3269; unresolved.

3. **Symlink escaping the workspace is dereferenced, not rejected.**
   A symlink at a report path pointing outside the workspace to a
   stub-shaped file classifies `True` (reclaimable) based on the
   *external* target's content, not the workspace's own file. Low
   real-world likelihood; flagged because it's a real undecidable-vs-
   decided conflation (the workspace's own file has no content of its
   own to judge). Not fixed by PR #3269; unresolved.

4. **`spawn.py clean --dry-run` performs real deletions.** Pre-existing
   on `main`, unmodified by this PR (see `derived:` line above). The
   `clean` dispatch never reads `a.dry_run`. Every "dry run" measurement
   quoted anywhere in this issue/PR thread, including the orchestrator's
   own re-measurement comment, was a real, irreversible deletion. Not
   fixed by PR #3269 (out of its diff); flagging because it materially
   changes how much trust to put in every "dry-run" number cited so far,
   and because it made this verification task's own literal instruction
   unsafe to follow verbatim. Unresolved -- worth its own issue.

## Next steps

None from this record -- it is a verification record, not a build. Findings
1-4 above are each unresolved and each named a resolution path; whether to
open follow-up issues for them is an operator/orchestrator call.

skill-verdict: silent-failure-audit — applied: invoked; framed Open findings
1-3 above (undecidable-file classification, hang-without-diagnostic,
deletion path with no named reason) as silent-failure catalog entries
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every number in this record was re-derived from the real predicate/git fixtures on this machine rather than cited from the PR description or the orchestrator's comment
other mounted skills: not triggered (work-in-english is a guidance-only
directive enforced by hook, not something invoked via the Skill tool;
adversarial-review, implementation-audit, model-routing, prose-modes,
merge-gates, parallel-decomposition arrived via post-hoc skill_judge
amendments after dispatch and were judged not-applicable -- this task
already specified concrete independent-verification questions directly, so
the heavier two-session claim-extraction/adversarial-setup protocols those
skills describe were not needed on top of it)
