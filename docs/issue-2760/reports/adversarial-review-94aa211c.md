---
issue: 2760
role: adversarial-review-94aa211c
author: adversarial-review-94aa211c
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 4aa78f31d660782f520cc66a35b4459c970febd4
loop_state: landed
type: review
breaking: false
verdict: pass — the six broken-git conditions re-derive exactly as PR #2764 claims (6/6-allow before, 5/6-deny+1-allow after), the merge-base execution claim holds once an environmental fixture artifact is controlled for, healthy-git and the untouched exemption channel are unregressed, and all four standing invariants hold; adversarial probing of the _GIT_UNKNOWN/None split found no bypass reachable without already controlling the git binary itself (a stronger threat model than this issue's scope) — one informational note, no blocking findings
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: 4aa78f31d660782f520cc66a35b4459c970febd4
---

# issue-2760 — adversarial-review-94aa211c record

## What was done

Independent verification of PR #2764 (`4aa78f31`, base `on-the-record/hooks/deliverable-guard.sh`), which fixes issue #2760: `_git_root_from` used to collapse "git said no repo" and "git could not answer" into a single `None`, letting a relative `EXEMPT_SUFFIXES`-matching payload win the exemption under every broken-git condition. The fix adds a `_GIT_UNKNOWN` sentinel distinct from a real `None`, and gates the raw-path fallback on it.

I re-derived every acceptance check and every invariant myself, from a fresh, independently-built test harness (not the PR author's `/tmp/dg_probe.py`, which no longer exists on disk), plus ran a set of adversarial probes against the new sentinel's own boundary. Full harness at `/tmp/dg_test/` (probe.py, attack.py, priorities_check.py, issue_re_check.py — scratch, not committed).

## Why

Task instructions required re-deriving rather than restating the PR's own record, attacking the `_GIT_UNKNOWN`/`None` distinction specifically, and settling the pre-#2752 claim by execution rather than trusting the PR's report of it.

## Upstream basis

- `on-the-record/hooks/deliverable-guard.sh` at `4aa78f31d660782f520cc66a35b4459c970febd4` (PR #2764 head) — code under review.
- canonical: `gh pr view 2764` output — PR body links a record at path `docs/issue-2760/reports/secure-coding-authorization-access-control+adversarial-review-f66c1db8.md`, which exists on PR #2764's branch (untracked on this branch since the PR is unmerged) — used only to identify which claims to re-derive, not re-cited as evidence itself.

## Evidence

### Harness construction and one real deviation

My first build of the harness put scratch fixture directories under bare `tempfile.mkdtemp()` (defaults to `/tmp`). Running the merge-base script's six conditions against that fixture gave a result that contradicted the PR's claim: the exempt-suffix payload *denied* under "git missing" instead of allowing.

derived: `test -e /tmp/.git && echo HAS-GIT` — result: `HAS-GIT` (an empty, pre-existing directory literally named `.git` sits directly under `/tmp` on this machine, unrelated to this task — `ls -la /tmp/.git` shows only `.`/`..`, mtime 6월 11, no repo content).

The merge-base script's `_git_root_from` (pre-#2659) is a naive `os.path.isdir(<probe>/".git")` walk with no git subprocess at all — it treated `/tmp` itself as a "repo root" for any fixture path under `/tmp`, the same naive-walk weakness issue #2659 documents. This was a fixture artifact, not a finding about the code under review. Fixed by moving all fixtures to `/dev/shm` and reconfirming its ancestry is clean:

derived: `for d in / /var /var/tmp /dev/shm "$HOME"; do test -e "$d/.git" && echo HAS-GIT || echo no; done` — result: `no` for all five, including `/dev/shm`.

With that fix, the merge-base result flips to match the PR's claim exactly (below).

### Acceptance check 1 — six conditions, relative exempt-suffix payload, before vs after

Harness: independently-built `probe.py`, real `bash` subprocess invocation of the actual hook file, fake `git` executables placed first on `PATH` for the five simulated conditions, real `git` binary against a directory with a verified-clean ancestor chain for "no repo", `TOKENMAXXXER_SPAWNED` explicitly unset (this hook only fires for *orchestrator* sessions, confirmed by reading the hook's own `if spawned: sys.exit(0)` branch before building the harness).

derived: `python3 /tmp/dg_test/probe.py /tmp/dg_test/before.sh BEFORE` (`before.sh` = `git show origin/main:on-the-record/hooks/deliverable-guard.sh`) — result:
```
condition              exempt rc  time     deny rc    time     stderr(exempt)
healthy git            rc=0        0.03s  rc=2        0.03s  ''
a' git missing         rc=0        0.03s  rc=2        0.03s  ''
b' git errors          rc=0        0.04s  rc=2        0.04s  ''
c1' garbage stdout     rc=0        0.03s  rc=2        0.03s  ''
c2' empty stdout       rc=0        0.03s  rc=2        0.04s  ''
d' hangs               rc=0       10.05s  rc=2       20.07s  ''
e' no repo             rc=0        0.03s  rc=0        0.03s  ''
```
6/6 broken-git conditions ALLOW the exempt-suffix payload, including the timing tell (hang: ~10s/one `_run_git` call vs. ~20s/two for the deny-shaped payload) — matches PR #2764's claimed BEFORE table exactly.

derived: `python3 /tmp/dg_test/probe.py /tmp/dg_test/after.sh AFTER` (`after.sh` = PR #2764 head, `4aa78f31`) — result:
```
condition              exempt rc  time     deny rc    time     stderr(exempt)
healthy git            rc=0        0.03s  rc=2        0.04s  ''
a' git missing         rc=2        0.03s  rc=2        0.04s  'orchestrate: could not determine whether ...'
b' git errors          rc=2        0.04s  rc=2        0.03s  'orchestrate: could not determine whether ...'
c1' garbage stdout     rc=2        0.03s  rc=2        0.03s  'orchestrate: could not determine whether ...'
c2' empty stdout       rc=2        0.03s  rc=2        0.03s  'orchestrate: could not determine whether ...'
d' hangs               rc=2       20.06s  rc=2       20.08s  'orchestrate: could not determine whether ...'
e' no repo             rc=0        0.05s  rc=0        0.03s  ''
```
5/6 (missing/errors/garbage/empty/hang) now DENY, matching the deny-shaped payload's rc on every one of those. `no repo` still allows both before and after — matches PR #2764's claimed AFTER table exactly, including 6/6→5/6-deny.

### Acceptance check 2 — healthy git, same payload, before vs after

Same tables above, `healthy git` row: exempt rc=0 both before/after, deny rc=2 both before/after, timing 0.03–0.04s both sides — no regression on the common path, exemption still functions when git is healthy.

### Acceptance check 3 — merge-base of PR #2752, execution not inference

derived: `git show --format="%H %P" -s 67ba464490e8f91c5345fd1cf6f3b4e46dbada04` — result: `67ba464490e8f91c5345fd1cf6f3b4e46dbada04 43f86ce54a3209221461d8547657eaf8051d4a3c` — single parent, confirming `43f86ce5` is the merge-base.

derived: `git show 43f86ce54a3209221461d8547657eaf8051d4a3c:on-the-record/hooks/deliverable-guard.sh > /tmp/dg_test/mergebase.sh` then `grep -n subprocess /tmp/dg_test/mergebase.sh` — result: one hit, inside a comment string (`"git itself manages its own internals over a subprocess"`) — no `import subprocess`, no subprocess call anywhere in the executable code. Confirms the merge-base script's `_git_root_from` never invokes `git` at all.

derived: `python3 /tmp/dg_test/probe.py /tmp/dg_test/mergebase.sh MERGE-BASE-fixed` (fixtures under `/dev/shm`, clean ancestry) — result:
```
condition              exempt rc  time     deny rc    time     stderr(exempt)
healthy git            rc=0        0.04s   rc=2        0.03s  ''
a' git missing         rc=0        0.04s   rc=0        0.05s  ''
b' git errors          rc=0        0.05s   rc=0        0.05s  ''
c1' garbage stdout     rc=0        0.03s   rc=0        0.03s  ''
c2' empty stdout       rc=0        0.03s   rc=0        0.03s  ''
d' hangs               rc=0        0.03s   rc=0        0.03s  ''
e' no repo             rc=0        0.04s   rc=0        0.04s  ''
```
6/6 broken-git conditions ALLOW the exempt-suffix payload at the merge-base too — **independently confirms the bug predates PR #2752**, matching PR #2764's claim by direct execution, not by trusting its record.

### Adversarial probing of the `_GIT_UNKNOWN`/`None` boundary

Built `attack.py`, testing each condition the task specified, against `after.sh` (the fix). derived: `python3 /tmp/dg_test/attack.py /tmp/dg_test/after.sh` — full transcript below, condition by condition:

1. **git exits nonzero but writes a plausible root to stdout**: result `rc=2` (deny), stderr `'orchestrate: could not determine whether docs/specs/approvers.md is inside a git repository (git rev-parse --is-inside-work-tree exited 1: fatal: whatever)...'`. On the nonzero branch, `_git_root_from` only inspects `r.stderr`, never `r.stdout` (`sed -n '183,238p' on-the-record/hooks/deliverable-guard.sh` at `4aa78f31`, the `if r.returncode == 0:`/`if "not a git repository" in r.stderr.lower():` branches) — a nonzero exit's stdout is fully ignored, so this vector is inert.
2. **git exits zero, stdout is a real absolute path but not a git root** (echoed the fixture's own `cwd`): result `rc=0` (allow). `_git_root_from` accepts any non-empty absolute stdout on `rc=0` with no existence or realness check. Because the crafted "root" here is exactly the payload's own ancestor, `posixpath.relpath` computed the correct raw suffix anyway — same outcome the raw-path fallback already gives in the "no repo" case, not a new privilege.
3. **git exits zero, stdout is a genuinely nonexistent, unrelated absolute path** (`echo "/this/path/does/not/exist/anywhere"`): result `rc=0` (allow). `_git_root_from` returns it as a trusted root; `posixpath.relpath` then produces a `../…`-prefixed string (escapes the fabricated root), which the code's own `if _rel != "." and not _rel.startswith(".."):` guard refuses to adopt — so `root_relative_n` stays the raw `n`, which already equals the exempt suffix, and the write is allowed on that basis. Same outcome as "no repo" (raw-path match), not a new bypass — but confirms the code trusts any absolute-looking, non-empty, `rc=0` stdout unconditionally. This trust assumption predates this fix (the pre-#2660 code trusted `r.stdout.strip()` the same way whenever non-empty — `sed -n '155,166p'` of `/tmp/dg_test/mergebase.sh`) and requires control over what the `git` binary itself prints, a strictly stronger prerequisite than "git cannot answer," which is this issue's scope.
4. **git exits zero, stdout is a relative-looking string** (`echo "relative/looking/root"`): result `rc=2` (deny), reached via the activation check — the exemption path itself correctly returned `_GIT_UNKNOWN` (`posixpath.isabs("relative/looking/root")` is `False`).
5. **git exits zero, stdout has multiple lines** (an absolute path plus a garbage second line): result `rc=0` (allow) — `r.stdout.strip()` only strips leading/trailing whitespace, so an embedded `\n` survives into `top`, and `posixpath.isabs` only checks the leading character. Same trust-boundary note as #3.
6. **git is a bash function, not a binary, with no `git` executable on `PATH`**: result `rc=2` (deny), stderr `'orchestrate: could not determine whether docs/specs/approvers.md is inside a git repository (git rev-parse did not run)...'`. Confirmed `subprocess.run(["git", ...])` never resolves shell functions (no shell interprets them); exporting a `BASH_FUNC_git%%` environment variable had no effect. This vector is inert by construction.
7. **timeout at the 10s boundary** (`sleep 9.9`, `sleep 10.0`, `sleep 10.3`, each followed by an echoed absolute path): result `sleep 9.9s -> rc=0, time=9.95s`; `sleep 10.0s -> rc=2, time=20.07s`; `sleep 10.3s -> rc=2, time=20.06s`. The 9.9s case completes inside the internal `timeout=10` and its (fabricated) stdout is trusted per the #3/#5 mechanism above; the 10.0s and 10.3s cases both trigger `subprocess.TimeoutExpired`, denying with `rc=2` at ~20s total (two `_run_git` calls, matching the deny path's timing shape from check 1's `d' hangs` row). `timeout=10` (`sed -n '169,180p' on-the-record/hooks/deliverable-guard.sh`) behaves as a floor, not an exclusive bound — no separate boundary bug found beyond the already-noted stdout-trust behavior.
8. **git succeeds against a bare repo**: result `rc=0` (allow) for the exempt payload. Isolated the mechanism directly: `git -C <bare> rev-parse --show-toplevel` → `rc=128`, stderr `'fatal: this operation must be run in a work tree'` (does not contain "not a git repository") → `_git_root_from` correctly returns `_GIT_UNKNOWN` here, so the exemption path denies internally (confirmed by code read: the nonzero+unrecognized-stderr branch). The observed `rc=0` comes from the activation check further down, independently: `git -C <bare> rev-parse --is-inside-work-tree` → `rc=0`, stdout `false`. Confirmed this is the activation check's own judgment, not exemption leakage, by re-running a deny-shaped payload (file_path `"src/module.py"`) against the same bare-repo `cwd` in a standalone script — also `rc=0` (`derived: python3 /tmp/dg_test/... ad hoc bare-repo deny check` — `deny-shaped in bare repo -> rc= 0`). A bare repo has no working tree to guard writes in, so "not inside a work tree" → "not this gate's business" is the intended design (same category as "no repo"), applied consistently to both payload shapes.

### Is "confirmed no repo still allows" a seventh hole?

derived: standalone script re-running the deny-shaped payload (file_path `"src/module.py"`, not exempt-suffix) against the same genuinely-outside-any-repo fixture used in check 1 — result: `rc=0` (allow), both before and after the fix, identical to the exempt-suffix payload's outcome in that same condition. This is not exemption-specific: the activation check itself (`git rev-parse --is-inside-work-tree` confidently returning "false", or "not a git repository" in stderr — `sed -n '267,309p' on-the-record/hooks/deliverable-guard.sh`) allows every write, regardless of path shape, once git confirms there is no repository at all. The exemption path's parity with "no repo" reaches the identical outcome the activation check would reach on its own — it is not granting a privilege the rest of the hook wouldn't already grant. Reaching this condition requires the write's `cwd` to have no `.git` ancestry anywhere up to the filesystem root, confirmed by git's own authoritative negative answer: derived: `LC_ALL=C git -C /dev/shm/verify_norepo rev-parse --show-toplevel` — result: `rc=128`, stderr `'fatal: not a git repository (or any parent up to mount point /dev)\nStopping at filesystem boundary...'`. At that point the write sits entirely outside this hook's stated protection domain, per the hook's own comment (`sed -n '267,272p' on-the-record/hooks/deliverable-guard.sh`: "A random project the user is hand-editing outside any git repo is still not this gate's business"). Verdict: safe, not a seventh hole.

### Untouched exemption channel and the second gated channel

derived: `python3 /tmp/dg_test/priorities_check.py` (relative file_path `"docs/reports/product/priorities/foo.md"` under simulated "git errors") — result: `before priorities-shard under git-errors -> rc= 0`, `after priorities-shard under git-errors -> rc= 2`. Confirms `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`, the second channel the PR's diff gates on `_git_unknown_for_exemption`, is fixed the same way as `EXEMPT_SUFFIXES`.

derived: `python3 /tmp/dg_test/issue_re_check.py` (relative file_path `"docs/issue-2760/reports/product/requirements.md"`, matching `PRODUCT_CAPTURE_ISSUE_RE`, under simulated "git errors") — result: `before PRODUCT_CAPTURE_ISSUE_RE path under git-errors -> rc= 0`, `after PRODUCT_CAPTURE_ISSUE_RE path under git-errors -> rc= 0` — identical on both sides, confirming this channel (matched against raw `n` directly, never through `_git_root_from`) is genuinely untouched by the fix, not silently over-gated as a side effect.

### Standing invariants

**1. No return of the retired role axis.**
derived: `git grep -wIn "role" -- . ':!docs/'` on PR #2764's head (checked out at `/tmp/otr-pr2764`, `4aa78f31`) — result: `1103`.
derived: same command on `origin/main` — result: `1103`.
Identical.

**2. No new bug — failing-test set as names, not counts.**
acceptance: `python3 -m pytest test/ -q` on PR #2764's worktree — result: `15 failed, 414 passed, 3 xfailed in 2.12s`.
acceptance: `python3 -m pytest test/ -q` on this branch (`= origin/main`, zero commits ahead per `git log --oneline -5`) — result: `15 failed, 414 passed, 3 xfailed in 2.97s`.
derived: `diff /tmp/dg_test/after_failed.txt /tmp/dg_test/main_failed.txt` (both `grep '^FAILED' | sort` of the two runs above) — result: `IDENTICAL SETS`, empty diff, 15 lines each.

**3. No overhead increase.**
From the healthy-git rows in check 1's tables above: exempt-suffix payload 0.03s before / 0.03s after; deny-shaped payload 0.03s before / 0.04s after — within run-to-run noise, matching the PR's claimed ~0.04-0.05s.
acceptance: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py -q` on PR #2764's worktree — result: `24 passed, 1 xfailed in 1.04s`.

**4. Monitor/watch machinery unbroken and not quieter.**
acceptance: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` on PR #2764's worktree — result: `30 passed in 2.34s`.
checked: `test/test_watchdog_heartbeat_noise.py` is present in the 414-passed set above (not in either run's 15-name failing set) per the `pytest test/ -q` runs cited under invariant 2 — passing, unaffected.
checked: `grep -rl "deliverable-guard\|deliverable_guard" on-the-record/monitors/*.py` on PR #2764's worktree — result: no match (grep exit 1) — confirms no coupling exists between the monitors code and this hook.

## Open findings

1. **[Informational, not blocking] The `rc=0` + absolute-stdout branch trusts git's output unconditionally** (no existence check, no single-line check) — see attack items #3, #5, #7 above. Reachable only by a `git` binary that itself lies (rc=0, absolute-looking stdout, but a fabricated or unrelated path) — a threat model strictly outside "git cannot answer," which is what issue #2760 scoped and what this PR fixes. Present symmetrically in the (unmodified) activation check too (trusts a `"true"`/`"false"` string match with no independent corroboration). No resolution path proposed here — flagging for visibility per the adversarial-review skill's incentive to surface everything, not because it blocks this issue's acceptance criteria.

## Next steps

None — `loop_state: landed`. Verification complete; no code changes proposed by this record. The one open finding above is informational and explicitly out of this issue's stated scope (the constraint said "the exemption path fails closed on every condition where git cannot answer," not "where git lies").

## Skill application

- skill-verdict: adversarial-review — applied: invoked; this session is itself the blind, structurally-independent evaluator the skill describes — it received only the issue/PR references (no shared context with PR #2764's authoring session), rebuilt its own test harness from scratch rather than reusing or trusting `/tmp/dg_probe.py`, and was tasked specifically to attack the fix's central claim rather than restate it. Every finding above cites its own re-derivation command and output rather than the PR's record.

## What did not work

- Built the first probe harness with `tempfile.mkdtemp()` defaulting to `/tmp`. Expected the merge-base script's "no repo"/"git missing" conditions to allow the exempt payload (matching the PR's claim); instead got a deny. derived: `test -e /tmp/.git && echo HAS-GIT` — result: `HAS-GIT`, an unrelated pre-existing empty directory literally named `/tmp/.git` on this machine satisfied the merge-base script's naive `os.path.isdir(probe/".git")` walk and made `/tmp` itself look like a repo root. Fixed by moving all fixtures to `/dev/shm` (confirmed clean `.git` ancestry first via the five-path check under "Harness construction" above), after which the merge-base result matched the PR's claim exactly.
