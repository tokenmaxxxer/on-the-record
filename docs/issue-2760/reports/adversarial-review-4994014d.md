---
issue: 2760
role: adversarial-review-4994014d
author: adversarial-review-4994014d
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2764, the subject's own deliverable for issue-2760
loop_state: terminal
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 4aa78f31d660782f520cc66a35b4459c970febd4
  - path: docs/issue-2760/reports/secure-coding-authorization-access-control+adversarial-review-f66c1db8.md
    sha: 4aa78f31d660782f520cc66a35b4459c970febd4
---

# issue-2760 — adversarial-review-4994014d record

## What was done

Independent adversarial review of PR #2764 (`issue-2760/secure-coding-authorization-access-control+adversarial-review-f66c1db8` → main), which introduces a `_GIT_UNKNOWN` sentinel to `deliverable-guard.sh`'s `_git_root_from()` so that "git confirmed no repo" (real `None`) and "git could not answer" (unresolved) no longer collapse to the same value, and gates the exemption match off when the answer is unknown.

canonical: `gh pr view 2764 --json title,body,files` (headRefName `issue-2760/secure-coding-authorization-access-control+adversarial-review-f66c1db8`, base `main`, files: `on-the-record/hooks/deliverable-guard.sh` +52/-6, `docs/issue-2760/reports/secure-coding-authorization-access-control+adversarial-review-f66c1db8.md` +249/0 — that record path is untracked in this worktree, present only on branch `pr-2764`, referenced here by that branch, not read from this working tree)

Rebuilt the fix's own probe from scratch (not reused from the PR body) against three script versions pulled directly from git:
- `pr-2764` head (`4aa78f31`) → `/tmp/dg_pr.sh`
- `main` (`1d6e746c`) → `/tmp/dg_main.sh`
- PR #2752's merge-base (`e1b35a53`, verified via `gh api repos/tokenmaxxxer/on-the-record/pulls/2752 --jq '.base.sha'` then `git cat-file -t` to confirm it resolves to a real commit) → `/tmp/dg_mergebase.sh`

derived: harness at `/tmp/dg_probe.py`, `/tmp/dg_extra_probe.py`, `/tmp/dg_sanity_probe.py` — each spawns a real `bash on-the-record/hooks/deliverable-guard.sh` subprocess with a controlled `PATH` (a per-condition fake or real `git`), a real board repo (`git init`'d temp dir under `/var/tmp`, chosen over `/tmp` after discovering `/tmp/.git` already exists in this sandbox and pollutes any "no repo" test rooted there — verified live: `ls -la /tmp | grep -i git` showed a stray `.git`, and a first `no_repo` run under `/tmp` falsely DENIED before the relocation), and a JSON stdin payload matching the hook's real `PreToolUse` shape (`session_id`, `cwd`, `tool_name: Write`, `tool_input.file_path`).

### The six issue-named conditions, relative exempt payload (`docs/specs/approvers.md`), before/after/merge-base

```
$ python3 /tmp/dg_probe.py mergebase
  a_missing    rc=0 ALLOW time=0.045s     b_errors     rc=0 ALLOW time=0.047s
  c1_garbage   rc=0 ALLOW time=0.045s     c2_empty     rc=0 ALLOW time=0.042s
  d_hang15s    rc=0 ALLOW time=0.042s     e_norepo     rc=0 ALLOW time=0.042s

$ python3 /tmp/dg_probe.py main
  a_missing    rc=0 ALLOW time=0.051s     b_errors     rc=0 ALLOW time=0.052s
  c1_garbage   rc=0 ALLOW time=0.047s     c2_empty     rc=0 ALLOW time=0.049s
  d_hang15s    rc=0 ALLOW time=10.055s    e_norepo     rc=0 ALLOW time=0.078s

$ python3 /tmp/dg_probe.py pr
  a_missing    rc=2 DENY  time=0.046s     b_errors     rc=2 DENY  time=0.050s
  c1_garbage   rc=2 DENY  time=0.052s     c2_empty     rc=2 DENY  time=0.055s
  d_hang15s    rc=2 DENY  time=20.068s    e_norepo     rc=0 ALLOW time=0.057s
```

derived: `python3 /tmp/dg_probe.py {mergebase,main,pr}` (transcript above, this session).

Re-derived, not restated: `main` reproduces the issue's reported 6/6-allow exactly (rc=0 on all six, hang at ~10.05s matching the issue's `real 0m10.054s`). `pr-2764` turns this into 5/6-deny with `no repo` still allowed by design (`e_norepo` rc=0) — matching the PR's own claim, independently re-run rather than trusted. `mergebase` (PR #2752's merge-base, pre-#2659) is also 6/6-allow, but for the claimed different reason:

```
$ grep -n "def _run_git\|subprocess.run\|timeout" /tmp/dg_mergebase.sh
(no output)
```
`_git_root_from` in the merge-base script never invokes `git` at all — confirmed by the absence of any `subprocess`/`_run_git` reference in that file version, and independently by the merge-base's own timing (all six conditions ~0.04s, including `d_hang15s` — a hanging fake `git` binary cannot slow down code that never execs `git`). It is a pure `os.path.isdir(<probe>/".git")` filesystem walk (confirmed by reading `/tmp/dg_mergebase.sh:159-166,273`, sourced from commit `e1b35a53626da83b163e6fcd70455b32db897f92`). This settles by execution — not inference — that the bug predates PR #2752, for the reason the PR names.

### Legitimate-write and scope invariants (acceptance criteria 2, 3's must-not)

```
$ python3 /tmp/dg_sanity_probe.py
--- A) healthy git, exempt relative payload (should ALLOW both) ---
main   ALLOW  dt=0.049s
pr     ALLOW  dt=0.050s
--- B) healthy git, non-exempt deliverable payload (should DENY both) ---
main   DENY   dt=0.049s
pr     DENY   dt=0.048s
--- C) absolute-path exempt payload, git MISSING (scoped-not-universal check) ---
main   DENY   dt=0.045s
pr     DENY   dt=0.051s
--- D) healthy-git timing, 10 runs each (overhead check) ---
main   mean=0.0573s median=0.0501s min=0.0454s max=0.1206s
pr     mean=0.0487s median=0.0474s min=0.0465s max=0.0524s
```
derived: `python3 /tmp/dg_sanity_probe.py` (transcript above, this session; case B's payload `src/foo.py` is a synthetic path written under the probe's own throwaway `git init`'d board repo at `/var/tmp/dg_sanity_env/board_repo`, untracked — not a path in this repository).

(A) the legitimate exempt write (`docs/specs/approvers.md`, healthy git) still passes unchanged before and after — the raw-path fallback was not deleted, and it still does its job on the one case it's supposed to. (B) an ordinary deliverable-shaped write (`src/foo.py`, untracked synthetic probe path, see derived note above), healthy git, is still denied both before and after — the fix did not accidentally widen or narrow the unrelated deny path. (C) the issue's own "scoped, not universal" claim (an absolute exempt-suffix payload does not textually match `EXEMPT_SUFFIXES` and so falls through to the activation check regardless of git health) holds unchanged before and after — already denied on `main`, still denied on `pr`. (D) no overhead: both versions land at ~0.045-0.057s on the healthy-git path; the PR's own reported "~0.04-0.05s unchanged" claim holds under an independently-run 10-iteration sample, not just the PR's own single-shot number.

### Attacking the `_GIT_UNKNOWN` distinction directly — 8 probes beyond the issue's six

```
$ python3 /tmp/dg_extra_probe.py
nonexistent_root_path     main   ALLOW  dt=0.052s
nonexistent_root_path     pr     ALLOW  dt=0.043s
multiline_stdout          main   ALLOW  dt=0.047s
multiline_stdout          pr     ALLOW  dt=0.047s
relative_stdout           main   ALLOW  dt=0.044s
relative_stdout           pr     DENY   dt=0.046s  err='...is-inside-work-tree exited 0: '
nonzero_exit_with_stdout  main   ALLOW  dt=0.048s
nonzero_exit_with_stdout  pr     DENY   dt=0.048s  err='...is-inside-work-tree exited 1: s...'
bare_repo_real_git        main   ALLOW  dt=0.054s
bare_repo_real_git        pr     ALLOW  dt=0.051s
```

derived: `python3 /tmp/dg_extra_probe.py` (transcript above, this session).

Per-condition verdicts on `_git_root_from` (pr-2764, `on-the-record/hooks/deliverable-guard.sh:205-237` at `4aa78f31`):

1. **git exits nonzero with output on stdout** (`nonzero_exit_with_stdout`: exit 1, stdout `/looks/like/a/root`, stderr `some error`): stdout is never inspected on a nonzero exit; falls to the `"not a git repository" in stderr` check, fails, returns `_GIT_UNKNOWN`. Exemption gated off; activation check's own `_run_git` call also gets the same fake nonzero answer and denies via its `else: deny(...)` branch (confirmed by the captured stderr above). **Correctly denied**, no path to a real `None`.
2. **git exits zero with empty stdout**: covered by the issue's own `c2_empty` condition above — `_GIT_UNKNOWN`, denied.
3. **git prints a path that does not exist** (`nonexistent_root_path`: exit 0, stdout `/this/path/does/not/exist/anywhere`): passes `top and posixpath.isabs(top)` (existence is never checked), so it is accepted as a real root. `posixpath.relpath(file, fake_root)` then produces a `..`-prefixed result (no common prefix), which fails the `_rel != "." and not _rel.startswith("..")` guard, so `root_relative_n` silently falls back to the *raw* `n` — which equals the exempt suffix — and the write is **allowed on both `main` and `pr`, unchanged** (see transcript above). This is a real residual gap in the sentinel's coverage (`isabs()` is necessary but not sufficient — the fix never verifies the returned root actually exists or is an ancestor of the file), but it is not reachable by any of the issue's "git cannot answer" conditions: real git's `rev-parse --show-toplevel` never exits 0 with a fabricated, non-existent absolute path — it either resolves the real toplevel or fails. Reaching this requires a `git` on `PATH` that lies while still exiting 0, which is a PATH-hijack/malicious-binary threat model already sufficient to defeat the whole hook by other means (e.g., a hijacked `git` can equally make `is-inside-work-tree` print `false` and bypass the activation check directly). Not a regression (identical on `main`) and out of the six-condition scope this issue defines, but worth naming as an open finding on the `_GIT_UNKNOWN` distinction's actual boundary.
4. **git prints a relative path** (`relative_stdout`, echoes `relative/not/absolute`, exit 0): `posixpath.isabs()` correctly rejects it → `_GIT_UNKNOWN` → exemption gated off. The *same* fake git also answers the activation check's `is-inside-work-tree` call with the same string, which is neither `"true"` nor `"false"`, so the activation check's own `else: deny(...)` fires (transcript above). **Correctly denied**, and this incidentally demonstrates the two checks compose correctly under a uniformly-lying git.
5. **git prints multiple lines** (`multiline_stdout`: `/some/fake/root\nextra_line_of_output\n`, exit 0): `str.strip()` only trims leading/trailing whitespace, not the embedded `\n`; `posixpath.isabs()` only checks the string starts with `/`, so a multi-line string starting with `/` still passes. This collapses into the same failure shape as probe 3 (bogus-but-"absolute" root, `relpath` produces a `..`-prefixed result, falls back to raw-path match) — **allowed on both `main` and `pr`, unchanged** (transcript above). Same scope caveat as probe 3: real `git rev-parse --show-toplevel` never emits more than one line on success.
6. **git is a shell function, not a binary**: not separately probed — `subprocess.run(["git", ...])` execs directly (no shell involved), so a shell function named `git` is invisible to it exactly like a missing binary; this degrades to the `a_missing` condition already covered above (`_GIT_UNKNOWN`, denied).
7. **the call times out at exactly the 10s boundary**: not separately probed beyond `d_hang15s` (which exceeds it, transcript in "The six issue-named conditions" above) — `subprocess.TimeoutExpired` fires once the child has run for >= the timeout, so a hang of any duration >= 10s degrades to the same `r is None` → `_GIT_UNKNOWN` path already confirmed by that transcript.
8. **git succeeds but the repo is bare** (`bare_repo_real_git`, real `git`, cwd = a real `git init --bare` repo): `rev-parse --show-toplevel` in a bare repo fails — exit 128, `fatal: this operation must be run in a work tree`:
   ```
   $ LC_ALL=C git -C bare_repo.git rev-parse --show-toplevel; echo "exit=$?"
   fatal: this operation must be run in a work tree
   exit=128
   $ LC_ALL=C git -C bare_repo.git rev-parse --is-inside-work-tree; echo "exit=$?"
   false
   exit=0
   ```
   canonical: the two `git -C bare_repo.git ...` commands and their output above, run live in this session against a real `git init --bare` repo at `/var/tmp/dg_probe_env/bare_repo.git`.
   The `show-toplevel` failure does not match `"not a git repository"`, so `_git_root_from` correctly returns `_GIT_UNKNOWN`, gating the exemption off. The write is still **allowed on `pr`** (matching `main`, transcript above), but via the *separate*, correctly-designed activation check: `git rev-parse --is-inside-work-tree` in a bare repo returns a clean `false` (exit 0, confirmed live above), a real recognized answer under this hook's own semantics ("only guard writes inside a git repo reachable from cwd" — a bare repo has no work tree, so it is legitimately out of this guard's scope). **Not a hole**: the allow here comes from the activation check's intended non-repo path, independently reached, not from the exemption's raw-path fallback trusting an unresolved answer.

### The design decision itself: is "confirmed no repo still allows the raw-path exemption" a seventh hole?

canonical: `on-the-record/hooks/deliverable-guard.sh:272-355` at `4aa78f31` (read directly, both the exemption block and the activation-check block below it), plus the `e_norepo`/`bare_repo_real_git` transcripts above showing the activation check's own `if not inside: sys.exit(0)` firing independently of the exemption's decision.

No. Reaching it requires the file's cwd/absolute path to resolve to a location genuinely outside any git repository (`git rev-parse --show-toplevel` really answers "not a git repository", condition (e) above). But the activation check lower in the same script asks the identical real question again (`git rev-parse --is-inside-work-tree`) before it would ever deny — and for a location truly outside a repo, that also answers `false`, which the activation check *unconditionally* allows on its own (`deliverable-guard.sh:354-355`, `if not inside: sys.exit(0)`), independent of anything the exemption code decided. An attacker or accident that can reach "confirmed no repo" for the exemption check has, by the same real git answer, already reached a location this hook was never going to guard regardless of `EXEMPT_SUFFIXES` — the raw-path fallback here is provably redundant with a rule that predates this fix and this issue (out of scope per the issue's own "Non-goals"), not a new avenue. The only way the two calls could disagree is a repo being created/destroyed in the narrow window between them (a TOCTOU race, not "git cannot answer"), which is a pre-existing, unrelated hypothetical this fix neither introduces nor is asked to close.

### Four standing invariants

canonical: `git diff main...pr-2764 -- on-the-record/hooks/deliverable-guard.sh` (read directly, full diff, this session) — touches only `_git_root_from`, the `_GIT_UNKNOWN` sentinel, and the two `root_relative_n`-gated exemption checks; no `role`/`kind` axis code appears in any changed hunk.

- **No return of the retired role axis in any reshaped form**: confirmed by the diff read above.
- **No new bug — failing-test set vs `main`, compared as sets of names**:
  ```
  $ git worktree add /tmp/wt-pr2764 pr-2764 && git worktree add /tmp/wt-main main
  $ cd /tmp/wt-pr2764 && python3 -m pytest test/ -q   → 15 failed, 414 passed, 3 xfailed
  $ cd /tmp/wt-main   && python3 -m pytest test/ -q   → 15 failed, 414 passed, 3 xfailed
  $ diff <(sort pr_failed_names.txt) <(sort main_failed_names.txt) && echo "IDENTICAL SETS"
  IDENTICAL SETS
  ```
  derived: the four commands above, run live in this session (worktrees removed afterward with `git worktree remove`) — `grep '^FAILED'` sorted and diffed by name (not count), genuinely identical sets, not just equal cardinality.
  Targeted tests named in the PR also pass: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py -q` → `24 passed, 1 xfailed` (pr-2764 worktree, re-run live, matches PR claim).
- **No overhead increase**: see "Legitimate-write and scope invariants" (D) above — independently re-measured at ~0.045-0.057s both sides across 10 runs each, not a single-shot re-check of the PR's own number.
- **Monitor/watchdog machinery unbroken, not quieter**: `python3 -m pytest test/test_watchdog_heartbeat_noise.py on-the-record/monitors/test_poll_heartbeat.py -q` (pr-2764 worktree) → `36 passed` — re-run live this session.
- **Role-axis grep count**: could not reproduce the PR's literal reported count (1103) at any scope tried:
  ```
  $ git grep -wIn "role" main -- on-the-record        | wc -l   → 314
  $ git grep -wIn "role" pr-2764 -- on-the-record      | wc -l   → 314
  $ git grep -wIn "role" main -- on-the-record/hooks   | wc -l   → 232
  $ git grep -wIn "role" pr-2764 -- on-the-record/hooks| wc -l   → 232
  ```
  derived: the four `git grep` commands above, run live this session. unverifiable: the exact directory/ref scope the PR's own session used to reach "1103" is not stated in the PR body and I could not recover it. The load-bearing part of the claim — identical before/after — holds at every scope actually tried, so the invariant itself is confirmed even though the specific number is not reproduced.

## Why

The task asked for independent re-derivation, not restatement of the PR's own probe output — every number and verdict above comes from a probe harness built fresh in this session (not copied from the PR's linked record) against scripts pulled directly from the three named git refs, run against real subprocesses with controlled `PATH`s and real temp git repos.

## Upstream basis

- `on-the-record/hooks/deliverable-guard.sh` @ `4aa78f31d660782f520cc66a35b4459c970febd4` (PR #2764 head) — the code under review.
- `docs/issue-2760/reports/secure-coding-authorization-access-control+adversarial-review-f66c1db8.md` @ `4aa78f31d660782f520cc66a35b4459c970febd4` — the subject's own deliverable record for issue-2760, which this record independently verifies (`verifies_subject: true`); untracked in this worktree, present only on branch `pr-2764`.
- Comparison points pulled directly from git, not from any record: `main` @ `1d6e746c`, PR #2752 merge-base @ `e1b35a53626da83b163e6fcd70455b32db897f92`.
  derived: `gh api repos/tokenmaxxxer/on-the-record/pulls/2752 --jq '.base.sha'` — result: `e1b35a53626da83b163e6fcd70455b32db897f92`; `git cat-file -t e1b35a53626da83b163e6fcd70455b32db897f92` — result: `commit` (both run live, this session).

## Open findings

1. **`_GIT_UNKNOWN`'s coverage boundary**: `_git_root_from` validates that a zero-exit stdout is non-empty and starts with `/` (`posixpath.isabs`), but never validates that the resulting string is a single line or an existing/ancestor directory. A `git` that exits 0 with a fabricated absolute path (single- or multi-line) is accepted as a real root and the exemption falls back to matching the raw `file_path`, exactly as it did before this fix — allowed on both `main` and `pr-2764` (probes 3 and 5 above). Not reachable by any of the issue's six "git cannot answer" conditions (real git never behaves this way on success), only by a hijacked/malicious `git` on `PATH`, a threat model that already defeats this hook by simpler means (e.g. lying on `is-inside-work-tree` directly). Resolution path: none required for this issue's acceptance criteria (out of the six-condition scope as defined); worth a future issue if the PATH-hijack threat model is ever brought in scope for this hook.
2. **Role-axis grep count (1103) not reproduced**: see "Four standing invariants" above — unverifiable at the scope tried, though the identical-before/after invariant it was meant to support does hold. No resolution path needed for this record; flagged for the PR author only if the exact number matters to some other check.

## Next steps

canonical: this session's own probe transcripts above (`/tmp/dg_probe.py`, `/tmp/dg_extra_probe.py`, `/tmp/dg_sanity_probe.py`) and the live `pytest`/`git grep`/`gh` commands in "Four standing invariants".

None — `loop_state: terminal`. All three acceptance-criteria checks (six conditions before/after/merge-base, healthy-git legitimate-write regression, merge-base execution settling the pre-#2752 question) were independently re-run and matched the PR's claims; the design-decision question ("is confirmed-no-repo a seventh hole") was independently reasoned through and found safe; the two open findings above are scope notes, not blockers.

## What did not work

None.

skill-verdict: adversarial-review — applied: invoked; loaded via Skill tool at session start per the spawning task's own trigger match, then followed by building an independent probe harness from scratch (not reusing the subject's own linked evidence) and attacking the fix's central distinction directly across 8 probes beyond the issue's named six, per the skill's "structurally independent evaluator" protocol.
skill-verdict: work-in-english — applied: invoked; this record, all code/harness comments, and all commit/PR text are in English per the skill's policy for a Korean-speaking session.
