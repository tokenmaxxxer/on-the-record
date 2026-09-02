---
issue: 3231
role: adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed
author: adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3235's deliverable (author implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6)
code_under_review:
  - skills.py
  - spawn.py
  - scripts/preflight/consumer_preconditions.py
  - on-the-record/hooks/skill-corpus-bootstrap.sh
  - on-the-record/hooks/install-precondition-notices.sh
  - on-the-record/hooks/hooks.json
  - tests/test_issue_3231_install_removals.py (untracked here -- lives on PR #3235's branch, not on this repo's default branch)
  - docs/handbooks/install-sufficiency.md
  - docs/handbooks/setup.md
  - README.md
type: verification
breaking: false
verdict: The 5-to-7 satisfied-count claim reproduces independently on a genuinely fresh isolated HOME (not the author's persistent sandbox) with a real network clone. The interrupted-fetch must-not clause holds under four real black-box attacks beyond the PR's own mocked tests -- SIGKILL mid-transfer, a real 2MB tmpfs filling up, an unwritable scratch parent, and a forced os.replace() failure -- in every case the real managed-clone path never existed and the preflight correctly reported unsatisfied. Concurrency (two real simultaneous ensure-skills processes) is genuinely serialized by the pre-existing fcntl lock: exactly one clone ran. All three existing-corpus tiers (MUSTER_SKILL_REPO, sibling clone, ~/.claude/skills) are left untouched when already populated. install-precondition-notices.sh is read-only, confirmed by strace. Two real defects found: (1) INCORRECT -- ensure_skill_corpus_cli()'s own docstring and inline comment claim it is best-effort and never sys.exits, but plumbing._run_net() converts a real subprocess timeout into sys.exit(), which is not caught by _skill_repo_managed_root()'s `except OSError`, so a slow-but-alive network (not a fast refusal, not fully offline) crashes the whole `ensure-skills` process after CLONE_TIMEOUT -- masked only by the SessionStart hook's own `|| true` + trap, not by the function itself; none of the PR's tests catch this because they all mock `_run_net` directly. (2) INCORRECT -- the PR's own claimed full-suite result ("1251 passed, 3 xfailed, 0 failed") does not reproduce on the PR's actual final commit: `tests/test_issue_3182_citation_line_accuracy.py` fails twice, deterministically, because commit b2f089ec added 9 lines to skills.py after commit 101a9095 had already fixed the citation line_anchors, re-drifting them by exactly 9 lines, and the suite was never rerun after that. The three official acceptance checks do pass as claimed. A lower-severity, pre-existing (not introduced by this PR) gap: consumer_preconditions.py's "never mutates the machine" claim is contradicted by `gh auth status` itself writing a device-id file into a fresh $HOME as a side effect of the `gh` binary, not of this script's own code.
loop_state: done
upstream:
  - path: docs/issue-3231/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6.md (untracked here -- lives on PR #3235's branch, not on this repo's default branch)
    sha: same-commit
  - path: docs/issue-3182/reports/adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2.md
    sha: 3580b146f2fca4207b586a0d74340c5b3b639add
  - path: docs/issue-3182/reports/adversarial-review+test-depth-audit+conformance-review-traceability-and-evidence-1839fd7b.md
    sha: 68578b5a2fb26565975e6991b44399e4c488c24f
  - path: docs/issue-3182/reports/silent-failure-audit+adversarial-review+conformance-review-verification-method-selection-73b06823.md
    sha: 2b992a791b1a5dea9f3567f4c802f84d43b0378c
  - path: docs/issue-3182/reports/silent-failure-audit+adversarial-review+test-depth-audit-f6d7707f.md
    sha: b7426d475bb79d0f4bdce37ae073714a5c6e340a
  - path: docs/issue-3182/reports/test-depth-audit+adversarial-review+silent-failure-audit-67e78be7.md
    sha: f86de107105a793a7a1b1c976c4fce2058516b41
---

# issue-3231 — adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed record

## What was done

Independent verification of PR #3235 (`tokenmaxxxer/on-the-record#3235`, "automatic skill-repository fetch, hardened against interrupted-fetch corruption"), issue #3231's delivery.

canonical: `gh pr view 3235 --repo tokenmaxxxer/on-the-record` (this session) — `state: OPEN`, `additions: 890`, `deletions: 136`, `Closes #3231`.
derived: `git fetch origin pull/3235/head:pr-3235-review && git log -1 pr-3235-review` — result: `a0e30dcfba8308693754294e9a72541f839364db` — "issue-3231: fix skill-verdict invoked marker for implementation-blueprint". All verification below ran against this exact commit, in a separate git worktree (`git worktree add /tmp/pr3235-worktree pr-3235-review`), never against my own subject-role branch.

### 1. The satisfied-count claim (5 → 7) — Present, independently reproduced

Ran the preflight myself, from a genuinely fresh isolated `$HOME` I created (`mktemp -d`, not the builder's own sandbox), with `MUSTER_SKILL_REPO` unset and `TOKENMAXXXER_RULEBOOKS` pointed at a nonexistent path — the same shape as the record's own claim, but measured independently.

derived: `env -i PATH="$PATH" HOME=<my own fresh tmpdir> TOKENMAXXXER_RULEBOOKS=<nonexistent> python3 scripts/preflight/consumer_preconditions.py` (before `ensure-skills`, run from `/tmp/pr3235-worktree`) — result:
```
5/10 preconditions satisfied.
5 missing: gh_cli_authenticated, git_identity_configured, skill_repository_resolvable, home_claude_skills_dir_present, remote_push_access
```
derived: `env -i PATH="$PATH" HOME=<same tmpdir> TOKENMAXXXER_RULEBOOKS=<nonexistent> python3 spawn.py ensure-skills` — result: prints `[ensure-skills] ... 를 만들었다`, `[skill-repo] skill-repository 를 받는 중`, then `[ensure-skills] skill-repository corpus 는 /tmp/pr3235-worktree/runs/rulebooks/skill-repository/skills 에서 쓸 수 있다` — a real `git clone` against the live GitHub `skill-repository`, not a mock.
derived: same preflight command, after `ensure-skills` — result:
```
7/10 preconditions satisfied.
3 missing: gh_cli_authenticated, git_identity_configured, remote_push_access
```
Exactly matches the record's claim: 5→7, and the two moved bits are exactly `skill_repository_resolvable` and `home_claude_skills_dir_present`.

Caveat worth stating explicitly, since the task asked whether this is genuinely a plugin-only condition: this measurement's cwd is the on-the-record checkout itself, so `target_repo_board_file_present` reads satisfied because this repo already has its own `docs/specs/approvers.md` — that is the same methodology issue #3182's original baseline used (not something this PR changed or inflated), so the 5→7 delta is apples-to-apples, but a truly separate target repo that has never run `spawn.py init` would show 4→6, not 5→7. `claude`/`git`/`gh` being on PATH is also inherited from this sandbox already having them installed, which is the documented "irreducible" assumption the whole handbook is built on (these four are explicitly out of scope for removal) — not something this PR could or should change.

### 2. Attacking the bootstrap (the part that writes to disk) — Present, verified beyond the PR's own tests

derived: `python3 -m pytest tests/test_issue_3231_install_removals.py -q` (this session, commit `a0e30dcf`, path untracked here — lives on PR #3235's branch) — result: `12 passed`. Every one of those 12 tests mocks `spawn._run_net` wholesale (`_fake_clone_full`/`_fake_clone_interrupted`, defined in that same file) rather than exercising a real filesystem permission, a real disk-full condition, or a real subprocess timeout. canonical: that test file's own module-level helpers (read this session, path untracked here — lives on PR #3235's branch) confirm every "interruption" case is a Python-level substitution of the network call, not an OS-level fault. This is a **Mock-Dominated** pattern (test-depth-audit): it is real code (`_skill_repo_managed_root()`, `ensure_skill_corpus_cli()`) exercising real Python-level branches, but the one thing genuinely dangerous about this feature — what happens when the OS itself fails mid-write — is never reached by these tests. I attacked the four specific real-world interruption points the task named, against the actual `git` binary and the actual filesystem:

**a) Kill mid-fetch (real SIGKILL, not a mock).** Replaced `git` on PATH with a wrapper that creates partial content in the scratch dir then sleeps; started `spawn.py ensure-skills` as a real background process; SIGKILLed the whole process group ~1.5s in, while `git clone` was verifiably still running (confirmed via `ps --forest` showing the live `git clone ... skill-repository.tmp-<pid>-<ts>` child).
derived: `find /tmp/pr3235-worktree/runs/rulebooks -maxdepth 3` right after the kill — result:
```
runs/rulebooks/skill-repository.lock
runs/rulebooks/skill-repository.tmp-3594856-1788392654759614
runs/rulebooks/skill-repository.tmp-3594856-1788392654759614/skills/only-one-partial-skill
```
The real path (`runs/rulebooks/skill-repository`, no `.tmp-` suffix) never existed.
derived: `env -i ... python3 scripts/preflight/consumer_preconditions.py --json` right after — result: `skill_repository_resolvable False`. Retrying `ensure-skills` afterward (real fake-git success this time) cleaned the stale `.tmp-*` scratch automatically and completed normally — confirmed no wedge from the killed attempt.

**b) Fill the destination (real disk-full, not simulated).** Used an unprivileged mount namespace (`unshare --map-root-user --mount`) to mount a genuine 2MB tmpfs at `runs/rulebooks`, then ran `ensure-skills` against the **real** GitHub `skill-repository` (no fake git this time) inside that namespace.
derived: `ensure-skills` output (this session) ended with `skill-repository corpus 를 아직 못 받았다`, rc=0; `df -h runs/rulebooks` showed `0% 사용` (git's own clone/unpack failed before writing meaningfully); `find runs/rulebooks -maxdepth 3` showed only the lock file, no `skill-repository` dir, no leftover scratch. Preflight (same mount namespace) reported `skill_repository_resolvable False`.

**c) Make the scratch directory unwritable.** `chmod 555 runs/rulebooks` before calling `ensure-skills` (real git). derived: `git clone` failed to create the `.tmp-*` directory under the read-only parent (nonzero exit); `_run_net` returned a `CompletedProcess` rather than raising, since this is the child process's own failure, not a Python-level OSError; the `result.returncode == 0` gate correctly skipped promotion. rc=0, no leftover (`find runs/rulebooks` after restoring permissions showed nothing but the lock file).

**d) Make the final rename fail.** Wrote a fake `git` that completes the clone successfully into the scratch dir, then `chmod 555` on the scratch's parent directory just before returning — reproducing a permission change racing the rename.
derived: `env -i ... python3 spawn.py ensure-skills` (this session) — result:
```
[skill-repo] fetch failed: PermissionError: [Errno 13] Permission denied: '/tmp/pr3235-worktree/runs/rulebooks/skill-repository.tmp-3597388-1788392695813920' -> '/tmp/pr3235-worktree/runs/rulebooks/skill-repository'
[ensure-skills] skill-repository corpus 를 아직 못 받았다 -- 네트워크가 없거나 관리 클론이 실패했다; 다음 --skills 스폰 때 다시 시도한다
```
Caught by `except OSError as exc` (skills.py:113), printed, not silently absorbed. `find` after restoring permissions showed the `.tmp-*` scratch left behind (harmless, cleaned by the next attempt's stale-glob sweep) and no `skill-repository` dir at all. Preflight afterward: `skill_repository_resolvable False`.

All four real interruption mechanisms hold the must-not clause. This is a stronger result than the PR's own test file demonstrates, because none of (b), (c), or (d) are reachable through a mocked `_run_net`.

### 3. Atomic rename / cross-device question — Present (by construction, not by handling)

canonical: `skills.py:95` (read this session) — `tmp_dir = d.parent / f"{d.name}.tmp-{os.getpid()}-{int(time.time() * 1e6)}"`. The scratch directory is always a sibling of the destination (same parent), so `os.replace()` (skills.py:111) is always a same-directory, same-filesystem rename — POSIX guarantees this is atomic. The "different devices" failure mode the task asked about cannot occur through this code path at all, because the scratch is never created anywhere but next to `d`; there is no configuration or environment variable that could put scratch and destination on different mounts. This is a design strength worth noting explicitly, not a gap silently avoided.

### 4. Concurrency (two sessions starting at once) — Present, verified with real concurrent processes

Started two real `spawn.py ensure-skills` background processes simultaneously (same fresh isolated `$HOME`, same fake slow-`git`), and waited on both.
derived: `/tmp/clone_calls.log` (the fake git's own append-log, timestamped, this session) — result: exactly one `clone start` / `clone done` pair — only one of the two processes actually ran `git clone`; the other's stdout log (`session_b.log`, this session) shows it printed `skill-repository corpus 는 ... 에서 쓸 수 있다` without ever invoking `git clone` itself.
canonical: `pipeline.py:128-148` (`_locked_rulebook_dir`, read this session) — `fcntl.flock(f, fcntl.LOCK_EX)` around the whole clone-or-reuse body, kernel-released if the holder dies (issue #773, referenced in the code's own docstring). This is the mechanism that produced the observed serialization: the second process blocked on the lock until the first finished, then found `_skill_repo_valid()` already true and reused it.
derived: `find /tmp/pr3235-worktree/runs/rulebooks -maxdepth 3` after both processes exited — result: `runs/rulebooks/skill-repository/skills/example-skill` — single clean corpus, no partial state, no corruption from the race.

### 5. Degrades safely when network is gone / remote refuses / headless — Surface (one real defect found)

- **Remote refuses** (fake git exits 128 immediately, no hang): derived: `ensure-skills` (this session) prints `skill-repository corpus 를 아직 못 받았다`, rc=0, `find runs/rulebooks -maxdepth 2` shows only the lock file. Clean.
- **Genuinely offline / disk-full** (see 2b above): clean, rc=0.
- **Network present but pathologically slow (a real subprocess timeout, not a fast refusal)**: **found a real defect.** canonical: `plumbing.py:41-52` (read this session) — `_run_net()`, which `_skill_repo_managed_root()` calls to run `git clone`:
  ```python
  def _run_net(args: list[str], label: str, timeout: float = NETWORK_TIMEOUT,
               **kwargs) -> subprocess.CompletedProcess:
      try:
          return subprocess.run(args, timeout=timeout, **kwargs)
      except subprocess.TimeoutExpired:
          sys.exit(f"{label}: 시간초과({int(timeout)}s) — 네트워크를 확인하라")
  ```
  `sys.exit()` raises `SystemExit`, which is **not** a subclass of `OSError`. `_skill_repo_managed_root()`'s handler at skills.py:113 is `except OSError as exc:` — it does not catch this. derived: reproduced the real path (not by mocking the exception, but by setting `spawn.CLONE_TIMEOUT = 2` and using a real slow fake `git` so a genuine `subprocess.TimeoutExpired` fires) — result:
  ```
  [skill-repo] skill-repository 를 받는 중
  CAUGHT SystemExit AT TOP LEVEL, code= [skill-repo] clone: 시간초과(2s) — 네트워크를 확인하라
  process exit code: 1
  ```
  canonical: skills.py:278-280 (read this session), the code's own comment inside `ensure_skill_corpus_cli()`:
  ```python
  # `_skill_repo_root()` 자체는 sys.exit 하지 않는다(그건 `resolved_skill_dirs()`
  # 가 실제 스킬 이름을 요청받았을 때만 하는 fail-closed) -- 못 받으면 그냥
  # None 을 돌려주고, 다음 실제 --skills 스폰이 다시 시도한다.
  ```
  and the docstring at skills.py:255-256: "각각 실패해도 나머지를 막지 않는다(best-effort, 항상 0 을 돌려준다 — SessionStart 훅은 세션을 막으면 안 된다)" — "best-effort, always returns 0." The reproduction above shows it does not always return 0; on a real network timeout it raises uncaught and the whole `spawn.py ensure-skills` process dies with exit code 1.
  In practice this is **masked, not fixed**, by the SessionStart hook wrapper: canonical: `on-the-record/hooks/skill-corpus-bootstrap.sh` (read this session) calls `python3 "$CHECKOUT/spawn.py" ensure-skills 2>&1 || true` inside a script that also has `trap 'exit 0' EXIT` — so the hook itself still exits 0 and a session still starts. But (i) the function's own contract is false, confirmed by its own comment being wrong about its own behavior, and (ii) the manner of "safe" here is a hard process kill after `CLONE_TIMEOUT` (180s) elapses, which is a real multi-minute stall for anything that calls `ensure_skill_corpus_cli()` directly (or, unchanged from pre-#3231 behavior, anything that calls `_skill_repo_root()` from inside a real `--skills` spawn) rather than the "print a notice and move on immediately" story the docs tell. This same timeout-to-`sys.exit()` shape predates this PR (`_run_net` itself) — what's new in #3231 is the false "always returns 0" claim layered on top of it, and no test in `tests/test_issue_3231_install_removals.py` (untracked here — lives on PR #3235's branch) exercises this because all of them mock `_run_net` and therefore never let a real `TimeoutExpired` occur.
  scope note: this defect does not affect any of the three official acceptance checks, which do not exercise this path.

### 6. Does not overwrite a user-managed corpus — Present, all three tiers verified live

- `MUSTER_SKILL_REPO` set to a user's own directory with real content: derived: `env -i ... MUSTER_SKILL_REPO=<user dir> python3 spawn.py ensure-skills` (this session) — result: resolved to it directly, printed `skill-repository corpus 는 <user dir> 에서 쓸 수 있다`; the fake git's own call-log (`/tmp/clone_calls.log`) stayed empty for this run, and `find <user dir> -maxdepth 2` afterward showed the same `my-own-skill/SKILL.md` unchanged.
- Sibling clone (`$TOKENMAXXXER_RULEBOOKS/skill-repository/skills`) pre-populated: same result — derived: resolved directly (`skill-repository corpus 는 <sibling>/skill-repository 에서 쓸 수 있다`), no clone attempted, `find` showed the pre-placed `sibling-skill/SKILL.md` unchanged.
- `~/.claude/skills` pre-populated with a user-created subdirectory: derived: `ensure-skills` output (this session) did not print the "created" notice (correctly detected the dir already existed), and `find $HOME/.claude/skills -maxdepth 2` afterward showed the pre-placed `user-managed-skill/note.md` untouched.

### 7. Read-only claims — Present for the notices hook, Surface for the preflight script

- `install-precondition-notices.sh`: ran it under `strace -f -e trace=openat` against a target repo with `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` pointed at an empty file. derived: `grep -E "O_WRONLY|O_RDWR|O_CREAT" strace.log | grep -iE "gitconfig|approvers"` (this session) — result: no matches; `stat -c%s` on the gitconfig file showed it remained 0 bytes after the run. Confirmed read-only.
- `scripts/preflight/consumer_preconditions.py`: strace'd the same way. derived: one write-mode `openat` did occur (this session) — `openat(AT_FDCWD, ".../.local/state/gh/device-id.tmp.<pid>", O_RDWR|O_CREAT|O_EXCL|O_CLOEXEC, 0600)`. canonical: `check_gh_cli_authenticated()` (consumer_preconditions.py:115-120, read this session) calls `gh auth status` — an explicitly-allowed "read-only form" per this script's own docstring (`_run_readonly`'s comment, line 26), but `gh`'s own binary writes a device-id file into a fresh `$HOME/.local/state/gh/` the first time it is ever invoked, as its own internal housekeeping. This contradicts the doc's and script's own "It never mutates the machine — it only observes and reports" / "Zero side effects: no file writes outside stdout" claims on a genuinely first-run machine. This behavior is inherited unchanged from issue #3182 (not introduced by #3231's diff — `git diff main pr-3235-review -- scripts/preflight/consumer_preconditions.py` this session shows no lines touching `check_gh_cli_authenticated` beyond the unrelated line-number comment updates), and #3235 does not touch `check_gh_cli_authenticated()` or its surrounding claim — it only re-carries the pre-existing text forward. Graded Surface rather than Incorrect because the script's own code writes nothing; the side effect is the `gh` binary's, one layer down, and untouched by this PR's own diff.

### 8. Doc-vs-code match (README.md / setup.md / install-sufficiency.md) — Present

canonical: `gh pr diff 3235` (this session, full diff read) cross-checked against `on-the-record/hooks/hooks.json`, `on-the-record/hooks/hook_classification.json`, and the two new hook scripts' actual content (all read this session): the resolution order described (`MUSTER_SKILL_REPO` > sibling > managed, managed clone fetched proactively by a `SessionStart` hook, printed notice before fetching, interrupted fetch never reads as present) matches what I independently observed running the code in sections 1-6 above. The Korean and English versions of `setup.md` say the same thing. No doc-vs-code mismatch found in this PR's own new text (in contrast to the mismatch issue #3182 found in the *pre-existing* text, which this PR correctly identifies and fixes).

### 9. Full test suite — three official acceptance checks Present; the PR's own broader claim Incorrect

derived: `python3 -m pytest tests/test_issue_3231_install_removals.py -q` (this session, on commit `a0e30dcf`, path untracked here — lives on PR #3235's branch) — result: `12 passed`.
derived: `python3 -m pytest tests/test_issue_3182_preflight.py tests/test_issue_3182_install_sufficiency_doc.py -q` (this session) — result: `16 passed` (12 + 4).
Both match the PR's claims exactly; the three official acceptance checks are genuinely satisfied.

The PR body and the builder's own record (untracked here — lives on PR #3235's branch) additionally claim: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` → "1251 passed, 3 xfailed, 0 failed". derived: ran the identical command twice, this session, on commit `a0e30dcf` — result both times:
```
FAILED tests/test_issue_3182_citation_line_accuracy.py::CitationLineAccuracyTest::test_every_cited_line_contains_the_call_it_claims
FAILED tests/test_issue_3182_citation_line_accuracy.py::CitationCommentAndStringDiscriminationTest::test_all_sixteen_real_anchors_still_pass
2 failed, 1249 passed, 3 xfailed, 2 warnings in 35.37s
```
Not a flake: identical result both runs. Root cause: derived: `git log --oneline main..pr-3235-review` (this session) shows commit `101a9095` ("fix citation line numbers shifted by the skills.py/spawn.py edits") landed *before* commit `b2f089ec` ("silent-failure-audit fix ... on skills.py") — and `b2f089ec` adds 9 lines to `skills.py`'s `except OSError:` block (the very `except OSError as exc: print(...)` fix discussed in section 5 above), shifting every line after it down by 9, without re-running the citation-line fix a second time.
derived: `git show b2f089ec --stat -- skills.py` (this session) — result: `skills.py | 13 ++++++++--` (net +9 lines).
derived: `grep -n "def _skill_repo_root" skills.py` on commit `a0e30dcf` (this session) — result: `131:def _skill_repo_root() -> Path | None:`, but `scripts/preflight/consumer_preconditions.py`'s `line_anchors` for `skill_repository_resolvable` (consumer_preconditions.py:309-312, read this session) still say `("skills.py", 122, "def _skill_repo_root")` — off by exactly the 9 lines `b2f089ec` added. Same shape for `home_claude_skills_dir_present`: anchor says `("skills.py", 408, ...)`, real line is `417` (`grep -n '_local_skill_dirs(home' skills.py` this session).
This is reproducible on the PR's actual, final, currently-open-for-review commit. It does not affect the three official acceptance checks (which don't include this test file), but it does mean the PR's/record's own "full suite: 0 failed" claim is false as written on that same commit.

## Why

The task explicitly asked me to verify the count myself rather than trust a number measured only in the author's own sandbox, and to attack the disk-writing bootstrap path specifically because that is where an automatic fetch can do real damage (overwrite/shadow a user's own corpus, or leave a corrupted-but-trusted cache). I therefore prioritized real subprocesses, real filesystems (including a real tmpfs and real permission bits), and real concurrent processes over reading the PR's own mocked tests and taking their word for the must-not clause — the PR's tests mock exactly the layer (`_run_net`) where the real risk lives, so independently reproducing the failure modes through the real `git`/filesystem/OS was the only way to find out whether the claims hold outside the author's own sandbox. That approach is what surfaced both real defects (the `SystemExit` escape, and the stale citation-line drift) — neither is visible from reading the diff or trusting the PR's own passing test run.

## What did not work

None — every attack scenario the task specified was reproducible in this environment (unprivileged mount namespaces were available for the disk-full case; `strace` was available for the read-only verification). No planned check had to be abandoned or downgraded to a code-reading-only judgment.

## Upstream basis

- PR #3235 (`tokenmaxxxer/on-the-record`), commit `a0e30dcfba8308693754294e9a72541f839364db` — the subject under review, fetched into a separate worktree (`git worktree add /tmp/pr3235-worktree pr-3235-review`) and never merged, edited, or pushed to by this session.
- `docs/issue-3231/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6.md` (untracked here — lives on PR #3235's branch, not on this repo's default branch) — this same PR's own builder record, read for the claims under test, not treated as ground truth.
- Issue #3182's five verification-round records (`docs/issue-3182/reports/adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2.md`, `.../adversarial-review+test-depth-audit+conformance-review-traceability-and-evidence-1839fd7b.md`, `.../silent-failure-audit+adversarial-review+conformance-review-verification-method-selection-73b06823.md`, `.../silent-failure-audit+adversarial-review+test-depth-audit-f6d7707f.md`, `.../test-depth-audit+adversarial-review+silent-failure-audit-67e78be7.md`) — read for the ten-precondition baseline and the original "one satisfied" measurement methodology this PR's 5→7 claim needs to stay consistent with.
- `docs/handbooks/install-sufficiency.md` and `docs/handbooks/observer-verification.md` — read, not modified.

## Open findings

1. **Incorrect** — canonical: skills.py:113, skills.py:248, skills.py:278-280, plumbing.py:41-52 (all read this session, quoted with codefences in section 5 above). `ensure_skill_corpus_cli()` (skills.py:248) does not honor its own "best-effort, always returns 0" contract: a real network timeout during the managed-clone fetch raises an uncaught `SystemExit` from `plumbing._run_net()` (plumbing.py:52), which `_skill_repo_managed_root()`'s `except OSError` (skills.py:113) does not catch — reproduced live in section 5 (`CAUGHT SystemExit AT TOP LEVEL`, process exit code 1). Masked at the SessionStart-hook layer by `skill-corpus-bootstrap.sh`'s `... || true` + `trap 'exit 0' EXIT`, so no session actually fails to start over this — but the function's own code comment (skills.py:278-280) asserting "`_skill_repo_root()` 자체는 sys.exit 하지 않는다" is factually wrong, confirmed by the direct reproduction in section 5. Resolution path: either wrap the `_sp._skill_repo_root()` call inside `ensure_skill_corpus_cli()` in a `try/except SystemExit`, or have `_skill_repo_managed_root()` catch `(OSError, SystemExit)` around the `_run_net` clone call specifically. Not required by any of the three official acceptance checks; open for a follow-up round on this same issue or a fast-follow PR.
2. **Incorrect** — derived: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (this session, commit `a0e30dcf`, reproduced twice) — result: `2 failed, 1249 passed, 3 xfailed` (full transcript in section 9 above). The PR's/record's "full suite: 1251 passed, 3 xfailed, 0 failed" claim does not reproduce on the PR's final commit; `tests/test_issue_3182_citation_line_accuracy.py` fails twice, deterministically, because commit `b2f089ec`'s +9-line change to `skills.py` re-drifted the `line_anchors` that an earlier commit (`101a9095`) had just fixed. Resolution path: re-run `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` after any further edit to `skills.py`'s line count and correct the two stale anchors (`skills.py:122` → `131`, `skills.py:408` → `417`) in `scripts/preflight/consumer_preconditions.py`'s `CHECKS` list, then re-verify the full suite before re-claiming "0 failed". Does not affect the three official acceptance checks.
3. **Surface**, lower severity, pre-existing (not introduced by #3231) — canonical: consumer_preconditions.py:115-120 and the strace transcript in section 7 above (this session). `consumer_preconditions.py`'s and `install-sufficiency.md`'s "never mutates the machine" / "zero side effects" claim is contradicted by `gh auth status` itself writing `~/.local/state/gh/device-id...` on a machine's first-ever `gh` invocation. This is `gh`'s own binary behavior, not code this script or this PR wrote, and #3235 does not touch this check or claim. Noted because the task explicitly asked to confirm the read-only claims; not blocking, and arguably out of this PR's own scope to fix.

## Next steps

acceptance: `git status` / `git diff --stat` (this session, run in `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-3231-adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed`) — result: only `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md` is new/modified in this checkout; PR #3235 itself was never edited, merged, or pushed to from this session (all mutation happened in the disposable `/tmp/pr3235-worktree` worktree and disposable `/tmp` scratch directories). loop_state: done for this record. A follow-up round (on this issue or a fast-follow PR) should fix open finding 1 (the `SystemExit` escape) and open finding 2 (re-sync the citation-line anchors and re-verify the full-suite claim) before the PR's test-plan claims are treated as accurate.

skill-verdict: adversarial-review — applied: invoked; treated PR #3235 as a black-box deliverable and actively tried to break its central safety claims (interrupted-fetch atomicity, concurrency, read-only guarantees, no-overwrite) with real OS-level attacks rather than re-reading its own tests and prose as evidence, which is what surfaced both open findings.
skill-verdict: silent-failure-audit — applied: invoked; canonical: skills.py:113 vs. plumbing.py:41-52 (read this session) — catalogued `_skill_repo_managed_root()`'s and `_run_net()`'s exception paths and found the `except OSError` vs. `sys.exit()`/`SystemExit` mismatch reported as open finding 1, a failure-mode-not-actually-caught defect of exactly the kind this audit exists to find.
skill-verdict: test-depth-audit — applied: invoked; classified `tests/test_issue_3231_install_removals.py`'s interrupted-fetch tests (untracked here — lives on PR #3235's branch) as Mock-Dominated (section 2 above) — they replace `spawn._run_net` wholesale rather than exercising a real subprocess/filesystem, which is exactly why none of the PR's 12 passing tests catch either open finding.
other mounted skills: not triggered (work-in-english was applied implicitly by writing this record in English per session convention; implementation-audit was not separately invoked as this task's own adversarial-review/silent-failure-audit/test-depth-audit combination already covers the same present/surface/absent/incorrect/unverifiable grading this task asked for).
