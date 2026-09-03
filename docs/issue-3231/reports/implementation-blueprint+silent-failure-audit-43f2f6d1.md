---
issue: 3231
role: implementation-blueprint+silent-failure-audit-43f2f6d1
author: implementation-blueprint+silent-failure-audit-43f2f6d1
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - skills.py (this round's diff lives on PR #3235's branch, untracked in this checkout)
  - spawn.py (this round's diff lives on PR #3235's branch, untracked in this checkout)
  - scripts/preflight/consumer_preconditions.py (this round's diff lives on PR #3235's branch, untracked in this checkout)
  - docs/handbooks/install-sufficiency.md (this round's diff lives on PR #3235's branch, untracked in this checkout)
  - docs/issue-3231/_assets/round3-repro/auth_401_server.py (new this round, untracked in this checkout -- lives on PR #3235's branch)
  - docs/issue-3231/_assets/round3-repro/repro_1_credential_prompt.py (new this round, untracked in this checkout -- lives on PR #3235's branch)
  - docs/issue-3231/_assets/round3-repro/repro_2_tcp_blackhole.py (new this round, untracked in this checkout -- lives on PR #3235's branch)
type: implementation
breaking: false
verdict: Fixed the one remaining gap PR #3247 (round-2 verification) found
  and did not patch -- skills.py's SessionStart clone/pull did not suppress
  git's interactive credential prompt the way this codebase's other
  git-network call sites already do. Reused that exact convention
  (`GIT_TERMINAL_PROMPT=0`, `GIT_ASKPASS=true`) via a new
  `skills._skill_repo_git_env()`, applied unconditionally (unlike
  `_git_env()`, which gates on a resolvable `GH_TOKEN`) because this call
  site is an anonymous read-only clone/pull with no push. Demonstrated live
  with two standalone repro scripts, not just asserted. Neighbour check
  found four other git-network call sites with the same missing-guard
  shape; none fixed this round (three pre-existing/unrelated files, one
  recently-added but belonging to a different issue's gate file) -- all
  four named below with dates and reasons. Full suite: 1253 passed, 3
  xfailed, 0 failed -- identical to round 2's own count.
loop_state: landed
upstream:
  - path: PR #3235 (tokenmaxxxer/on-the-record), commit 25d24ab318aa33eb74a755bf16d5ff4792410dad (round 2's final commit, this round's starting point)
    sha: 25d24ab318aa33eb74a755bf16d5ff4792410dad
  - path: docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f.md (PR #3247, round-2 verification that found and did not patch this gap)
    sha: c1c16d7737ae29008bc6e6f34e1fd3451dc86f7b
---

# issue-3231 — implementation-blueprint+silent-failure-audit-43f2f6d1 record

skill-verdict: silent-failure-audit — applied: invoked; classified the clone-hang as a silent-failure-via-timeout-absence and verified the fix converts it to Handled per the catalog's Handled definition (bounded, actionable error propagation)
skill-verdict: implementation-blueprint — not-applicable: single-file guard addition to an existing hook plus two standalone repro scripts, not new multi-module structure

## What was done

canonical: `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f.md`
(PR #3247, sha `c1c16d7737ae29008bc6e6f34e1fd3451dc86f7b`, present on this
repo's default branch and read this session), Open findings item 1 there.

This is round 3 on PR #3235 (issue #3231). Round 2's independent
verification (PR #3247) confirmed round 2's two fixes hold, and found one
new, real, bounded residual risk that it explicitly did not patch (task
scope there was verify-only): the automatic SessionStart skill-repository
clone (`skills.py::_skill_repo_managed_root()`, invoked by
`on-the-record/hooks/skill-corpus-bootstrap.sh` (untracked in this
checkout -- lives on PR #3235's branch) -> `spawn.py ensure-skills`) does
not suppress git's interactive credential prompt the way this codebase's
other git-network call sites already do. This round closes that gap, on
PR #3235's own branch
(`issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6`),
worked in a separate worktree (`/tmp/pr3235-work`) checked out from
`origin/<that branch>` (HEAD at round 2's `25d24ab3` before this round's
commits).

### 1. Found the established convention first

derived: `grep -rn "_git_env(" --include=*.py .` (run in the PR #3235
worktree, this session) — result:
```
relay.py:220:                        env=_sp._git_env())
pipeline.py:854:                label, env=_sp._git_env())
pipeline.py:897:                env=_sp._git_env())
```
canonical: `plumbing.py:364-390` (`_git_env()`, read in the PR #3235
worktree this session) — the canonical definition, reproduced verbatim:
```python
def _git_env() -> dict[str, str] | None:
    ...
    token = _sp._resolve_gh_token()
    if not token:
        return None
    return {**os.environ, "GH_TOKEN": token,
            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}
```
`GIT_TERMINAL_PROMPT=0` and `GIT_ASKPASS=true` are the exact convention --
confirmed used identically at all three call sites above (`relay.py`'s own
push, `pipeline.py`'s `bootstrap_fetch_and_record_sha()` and
`_fetch_or_halt()`), no variant found. `_git_env()` gates the whole dict on
a resolvable `GH_TOKEN` and returns `None` (parent env unmodified) when one
isn't available -- correct for those three call sites, which are the
orchestrator's own authenticated fetch/push against a repo it may need to
push to. `_skill_repo_managed_root()`'s clone/pull is an anonymous
read-only checkout of a public repo (`skill-repository`, no push) -- if the
fix reused `_git_env()` verbatim, its own `GH_TOKEN` gate would leave
exactly the common, token-less case unguarded, which is the case this fix
exists to close. So the fix reuses the same two keys/values, applied
unconditionally, via a new `skills._skill_repo_git_env()` -- same
convention, not a second one.

### 2. Applied the guard at both `_run_net()` calls inside `_skill_repo_managed_root()`

canonical: PR #3235 worktree (`/tmp/pr3235-work`) `skills.py` and
`spawn.py`, this round's own edit, read back after writing (this session).

`skills.py` (final line numbers in the PR #3235 worktree after this
round's commit):
- `skills.py:53-77` — new `_skill_repo_git_env()`, documented in its own
  docstring with the reasoning in section 1 above.
- `skills.py:111` — the TTL-refresh `pull` call: `env=_sp._skill_repo_git_env()` added.
- `skills.py:137-138` — the first-time `clone` call: `env=_sp._skill_repo_git_env()` added.
- `spawn.py:433` — one re-export line (`_skill_repo_git_env = skills._skill_repo_git_env`), following this file's existing pattern for every other `skills.py` name spawn.py re-exports for `mock.patch.object(spawn, ...)` visibility.

### 3. Collateral: citation-line-accuracy repair

derived: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q`
(run in the PR #3235 worktree, this session, before the anchor fix) —
result:
```
FAILED tests/test_issue_3182_citation_line_accuracy.py::CitationLineAccuracyTest::test_every_cited_line_contains_the_call_it_claims
FAILED tests/test_issue_3182_citation_line_accuracy.py::CitationCommentAndStringDiscriminationTest::test_all_sixteen_real_anchors_still_pass
AssertionError: False is not true : posix_fork_support: spawn.py:4707 does not contain 'os.fork()' as real code
2 failed, 1251 passed, 3 xfailed, 2 warnings in 33.38s
```
Root cause: adding one line to `spawn.py`'s re-export block shifted every
absolute line number after it (and the new function in `skills.py` shifted
everything after it there too), and
`tests/test_issue_3182_citation_line_accuracy.py` checks
`scripts/preflight/consumer_preconditions.py`'s hardcoded `line_anchors`
against the real file content. Updated every shifted anchor in
`scripts/preflight/consumer_preconditions.py` (`posix_fork_support`:
`4707`->`4708`, `2705`->`2706`; `claude_cli_on_path`: `4764`->`4765`;
`skill_repository_resolvable`: `155`->`182`;
`home_claude_skills_dir_present`: `441`->`468`; `workspace_disk_headroom`:
`734`->`735`, `745`->`746`, `750`->`751`, `3297`->`3298`) and the matching
prose line numbers in `docs/handbooks/install-sufficiency.md` (lines 56,
57, 183).

derived: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q`
(run in the PR #3235 worktree, this session, after the anchor fix) —
result:
```
..........                                                               [100%]
10 passed in 0.92s
```
`docs/handbooks/install-sufficiency.md` line 52 already cited
`spawn.py:4761` before this round touched anything -- three lines off from
`consumer_preconditions.py`'s own `4764` at the time. That drift predates
this round (canonical: `git blame` on that line, PR #3235 worktree, this
session, showing a commit before this round's), is not part of the
`line_anchors` this test checks, and this round's edit did not cause it --
left as-is, out of scope.

## Why

canonical: this round's own task instructions, re-read this session
(reuse the codebase's existing convention exactly, do not invent a second
one; the fix's evidence trail is section 1 above's grep + canonical read,
performed in that order before any edit).

The task instructed reusing the codebase's existing convention exactly
rather than inventing a second one, so step 1 above (the grep, then a read
of the canonical definition, then confirming no variant across all three
existing call sites) came before any edit. The one deliberate deviation
from `_git_env()` itself -- not gating on `GH_TOKEN` -- is explained
inline in `_skill_repo_git_env()`'s own docstring and in section 1 above:
gating would silently reproduce the exact hazard being fixed for the
common (token-less) case, so it would not be "the same convention" in the
sense that matters (suppressing the prompt), only in the sense of reusing
the same two literal keys.

## Demonstration 1 — credential-demanding remote fails closed (not hangs)

derived: `python3 docs/issue-3231/_assets/round3-repro/repro_1_credential_prompt.py`
(new this round, untracked in this checkout -- lives on PR #3235's
branch; run in the PR #3235 worktree, this session) — result:
```
=== fix's actual env (from the real function) ===
GIT_TERMINAL_PROMPT = 0
GIT_ASKPASS         = true

=== BEFORE: no guard env, real pty, 5s probe window ===
still blocked (alive) after probe window: True
elapsed: 5.045 s  child terminal read so far: "Username for 'http://127.0.0.1:8934': "

=== AFTER: GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=true (this round's fix), real pty, 5s probe window ===
exited within probe window: True
elapsed: 0.05 s  exit status: 128
child output: 'fatal: http://127.0.0.1:8934/fake.git/에 대한 인증이 실패하였습니다\r\n'
```

`docs/issue-3231/_assets/round3-repro/auth_401_server.py` (new this round,
untracked in this checkout -- lives on PR #3235's branch) is a local HTTP
server that answers every request with `401` + `WWW-Authenticate: Basic`
-- the same challenge shape a private/rate-limited git smart-http remote
sends, and the exact shape PR #3247's own round-2 finding reproduced with.

The repro script above (untracked in this checkout -- lives on PR #3235's
branch): a naive `script(1)`-wrapped repro was tried first and gave a
false pass in this sandbox -- `script(1)` needs a real controlling
terminal on the *outer* process to forward keystrokes into the pty it
creates, and this sandbox's own stdin is not a tty, so git's own
`isatty()` check on inherited stdin already failed fast regardless of the
fix, which would have looked like success even without it (full account
in "What did not work" below). The script instead opens its own kernel
pty pair directly (`pty.openpty()`), forks a child, makes the pty slave
the child's controlling terminal via `TIOCSCTTY`, and execs the exact
`git clone` shape `skills.py::_skill_repo_managed_root()` issues as that
child -- independent of whatever terminal the script itself runs under.
The parent probes the pty master with a bounded 5s `select()` window and
reports whether the child was still alive (blocked reading its
controlling terminal) when the window closed, or had already exited.

BEFORE (no guard, matching PR #3247's finding): the child process is still
alive, still blocked reading `Username for '...': ` from its controlling
terminal, after the entire 5s probe window -- it would sit there until an
external timeout killed it (the real `CLONE_TIMEOUT`, 180s, in
production). AFTER (`spawn._skill_repo_git_env()`, the real fix function
imported from the PR #3235 worktree's own `spawn.py`, not reimplemented):
the child exits in 0.05s with `fatal: ... 인증이 실패하였습니다`
("authentication failed") -- a fast, actionable error, no prompt attempted
at all.

## Demonstration 2 — TCP blackhole still fails within a bounded time, and by what mechanism

derived: `python3 docs/issue-3231/_assets/round3-repro/repro_2_tcp_blackhole.py`
(new this round, untracked in this checkout -- lives on PR #3235's
branch; run in the PR #3235 worktree, this session) — result:
```
demo timeout passed to _run_net: 5s (production skills.py call site uses spawn.CLONE_TIMEOUT=180s)
SystemExit raised after 5.01s (bound requested: 5s)
message: [repro] clone: 시간초과(5s) — 네트워크를 확인하라
bounded (elapsed < timeout + slack): True
```

A credential prompt is not the only way a remote can stall a clone: a
proxy or endpoint can accept the TCP connection and then never respond.
`GIT_TERMINAL_PROMPT`/`GIT_ASKPASS` do not apply here -- the request never
reaches git's credential layer at all. The mechanism that bounds this wait
is `plumbing._run_net()`'s own `timeout=` argument
(`subprocess.run(args, timeout=timeout, **kwargs)`, `plumbing.py:41-49`) --
a real OS-level bound enforced by Python's `subprocess` module (it
terminates the child on expiry), not a cooperative one. `_run_net` catches
the resulting `subprocess.TimeoutExpired` and converts it to
`sys.exit(f"{label}: 시간초과({int(timeout)}s) — 네트워크를 확인하라")` --
a bounded, actionable error. `skills.py`'s real clone call site passes
`timeout=CLONE_TIMEOUT` (180s in production); the repro script above
passes a short override (5s) to keep the demo fast, but exercises the
identical code path (`spawn._run_net`, with this round's
`_skill_repo_git_env()` guard included, imported from the PR #3235
worktree's real `spawn.py`).

The clone attempt against the blackhole server (`socket.accept()`s the
connection, then never reads or writes) is killed and converted to a
bounded, actionable `SystemExit` at 5.01s -- matching the requested
timeout, not an indefinite wait. In production this bound is
`spawn.CLONE_TIMEOUT` (180s) for the first-time clone and
`spawn.NETWORK_TIMEOUT` (60s, `plumbing.py:38`) for the TTL-refresh pull.

## Neighbour check — other git-network call sites missing this guard

derived: `grep -rn '"git", *"clone"\|"git", *"fetch"\|"git", *"pull"\|"git", *"ls-remote"\|git clone\|git fetch\|git pull\|git ls-remote' --include=*.py --include=*.sh .`
(run in the PR #3235 worktree, this session), cross-checked with
`git blame`/`git log -1 --format=%ad -- <file>` for each hit to establish
whether it predates issue-3231's own work. Four sites share this round's
missing-guard shape (a `_run_net`/`subprocess.run` git-network call with a
bounded `timeout=` but no `env=` suppressing the interactive prompt);
**none of the four were fixed this round** -- named individually below,
per the task's instruction not to silently fix or silently skip:

1. **`pipeline.py:433-442`, `core_root()`'s clone/pull of
   `tokenmaxxxer-core`.** Same shape as the fixed site (`_run_net` with
   `timeout=CLONE_TIMEOUT`, no `env=`). derived: `git blame -L 438,443
   pipeline.py` (PR #3235 worktree, this session) — result: commit
   `8d9fadd6e`, `2026-08-23` -- 11 days before this round, predates
   issue-3231's own first commit on this cluster (`677b9d74`,
   `2026-08-23`, same day but a separate, later commit). Not fixed: it is
   a different function serving a different managed clone
   (`tokenmaxxxer-core`, not `skill-repository`), in a file this round
   otherwise does not touch, and predates this issue's own work -- outside
   this round's declared single-site scope and the "do not modify
   unrelated files" instruction.
2. **`on-the-record/hooks/self-update.sh:30` and six sibling
   SessionStart-adjacent hooks** (`poll-rearm.sh:50`,
   `impact-guard.sh:49`, `merge-allow-gate.sh:72`,
   `decision-queue-stopgate.sh:55`, `plan-order-guard.sh:56`,
   `directive.sh:177`) each run
   `git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null`
   as a self-clone fallback with **no `env=` guard and no `timeout`
   wrapper at all** (worse than the fixed site: no bound of any kind, not
   even the accidental 180s one). derived: `git blame -L 30,30
   on-the-record/hooks/self-update.sh` (PR #3235 worktree, this session)
   — result: commit `60e77d5f6`, `2026-07-29` -- 5 weeks before this
   round, well predating issue-3231. Not fixed: pre-existing, shell-level
   (not Python, so `skills.py`'s new `_skill_repo_git_env()` does not
   directly transfer), and shared across seven files this round does not
   otherwise touch.
3. **`on-the-record/hooks/pretooluse_dispatcher.py:150-155`**, a
   self-clone of `on-the-record` with `timeout=120` but no `env=`.
   derived: `git blame -L 153,153
   on-the-record/hooks/pretooluse_dispatcher.py` (PR #3235 worktree, this
   session) — result: commit `128f7640b`, `2026-08-24` -- 10 days before
   this round, predates issue-3231. Not fixed: pre-existing, unrelated
   file.
4. **`gates/amends_landing.py:52-55`**, a clone with `timeout=120` but no
   `env=`, used by the amends-landing-apply feature (issue #3129 per
   `on-the-record/hooks/hook_classification.json`'s own rationale text).
   derived: `git blame -L 53,53 gates/amends_landing.py` (PR #3235
   worktree, this session) — result: commit `6ae02cced`, `2026-09-02` --
   **1 day before this round**, genuinely recently-added, the one finding
   here that most closely matches this task's "recently-added" framing.
   Not fixed this round: it belongs to a different issue's gate file
   (amends-landing-apply, not the SessionStart skill-repository clone
   this round's scope names), and this round's task explicitly scopes the
   fix to "the SessionStart clone call site" with a neighbour-*check*,
   not a blanket sweep -- editing an unrelated feature's file without
   that feature's own test run/instruction risks destabilizing it.
   Flagged here as the strongest follow-up candidate (same shape, same
   repo, one day old).

No other `git clone`/`fetch`/`pull`/`ls-remote` call site was found beyond
the ones enumerated above and the ones already guarded (`plumbing.py`'s
`_fetch_or_halt`/`bootstrap_fetch_and_record_sha`, `relay.py`'s push,
`pipeline.py:897`) or genuinely local (`spawn.py:3350`'s "작업 클론"
clones from a `Path(cwd).resolve()` local filesystem path, never a network
URL, so no credential prompt is possible there; test fixtures under
`test/`/`tests/` clone local bare repos for test setup, not production
network paths).

## Silent-failure-audit classification

canonical: the diff described in sections 1-2 above and demonstrated live
in Demonstration 1/2 above (PR #3235 worktree, this session).

- **Original code** (`skills.py`'s two `_run_net()` calls inside
  `_skill_repo_managed_root()`, pre-round-3): **Unguarded /
  Silently-Absorbed-via-timeout-absence.** The credential-prompt failure
  mode has no bounded, actionable error path of its own -- it manifests
  as an indefinite-looking hang (bounded only by accident, via
  `_run_net`'s generic `timeout=` argument, which exists for slow
  networks, not for suppressing an interactive prompt) rather than a
  fast, named, caught error. A caller/operator sees "session start is
  slow" for up to 180s with no diagnostic pointing at "a remote is asking
  for credentials this process can never answer."
- **Fixed code**: **Handled.** `_skill_repo_git_env()` converts the
  credential-challenge case from an accidentally-bounded hang into an
  immediately bounded, actionable error (`fatal: ... 인증이 실패하였습니다`,
  demonstrated at 0.05s in Demonstration 1) -- propagated the same way
  `_run_net`'s existing `except (OSError, SystemExit)` clause in
  `_skill_repo_managed_root()` already handles a genuine network timeout:
  caught, printed to stderr, function returns `None` (best-effort
  contract; `ensure_skill_corpus_cli()` reports "not fetched yet" and
  never blocks the session). Matches the catalog's Handled definition:
  bounded, actionable error propagation, not a caught-and-discarded or
  indefinitely-absorbed failure.

## Tests

derived: `python3 -m pytest tests/test_issue_3231_install_removals.py -q` (run in the PR #3235 worktree, this session) — result:
```
..............                                                           [100%]
14 passed in 0.94s
```
derived: `python3 -m pytest tests/test_issue_3182_preflight.py -q` (run in the PR #3235 worktree, this session) — result:
```
............                                                             [100%]
12 passed in 13.08s
```
derived: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` (run in the PR #3235 worktree, this session) — result:
```
....                                                                     [100%]
4 passed in 4.79s
```
derived: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` (run in the PR #3235 worktree, this session, re-confirmed post-commit; see "Collateral" above for the before/after pair) — result:
```
..........                                                               [100%]
10 passed in 0.92s
```
derived: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (full sweep, run in the PR #3235 worktree, this session, after both commits landed) — result:
```
1253 passed, 3 xfailed, 2 warnings in 32.78s
```
Identical to round 2's own cited count (`1253 passed, 3 xfailed, 0 failed`,
PR #3247's test plan) -- this round's edits add no new test files and
change no test outcomes, only the fix + its own repro scripts (which are
standalone scripts under `docs/issue-3231/_assets/round3-repro/`
(untracked in this checkout -- lives on PR #3235's branch), not part of
the `test/`/`tests/`/`on-the-record/hooks/` sweep). The two warnings are
the pre-existing `pinned-fixture-divergence` (issue #3019) notices,
unrelated to this round's change (`skills.py`/`spawn.py`/
`consumer_preconditions.py` carry no
`SkillCandidatesPinnedFixtureDivergenceTest` interaction).

## What did not work

canonical: this session's own tool-call history running the abandoned
`script(1)`-based repro attempt, before it was replaced with the
`pty.openpty()`-based `repro_1_credential_prompt.py` (PR #3235 worktree,
this session; the abandoned `.sh` variant was deleted, never committed).

The first attempt at Demonstration 1 used `script -qec "... git clone ..." /dev/null`
under `env -u GIT_ASKPASS -u GIT_TERMINAL_PROMPT`, matching PR #3247's own
described repro shape. It returned instantly (`exit 128`, "could not read
Username ... 성공") instead of blocking -- a false pass, contradicting
Demonstration 1's real result above (still blocked after the full 5s
probe window). Root cause: this sandbox's own stdin is not a tty, and
`script(1)` forwards keystrokes from its *own* stdin into the pty it
creates; with nothing to forward (EOF immediately), the child's read on
its controlling terminal returned EOF rather than blocking, regardless of
whether the fix's env was present. Replaced with the `pty.openpty()`-based
script described in Demonstration 1, which creates its own pty pair
independent of the outer terminal and reproduces the true blocking
behavior -- confirmed by Demonstration 1's own transcript above, not
reasserted here.

## Upstream basis

canonical: `gh pr view 3235 --json headRefName,state` (this session,
before entering the worktree) and `git log --oneline -5` on the fetched
branch (this session) — confirmed branch name
`issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6`,
`state: OPEN`, HEAD `25d24ab3` before this round's own commits.

- PR #3235 (tokenmaxxxer/on-the-record), commit `25d24ab318aa33eb74a755bf16d5ff4792410dad`
  (round 2's final commit; this round's starting point).
- `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f.md`
  (PR #3247, round-2 verification), commit `c1c16d7737ae29008bc6e6f34e1fd3451dc86f7b`
  -- the record that found this round's fixed gap and gave the resolution
  path this round follows (`env={**os.environ, "GIT_TERMINAL_PROMPT": "0",
  "GIT_ASKPASS": "true"}` at both `_run_net` call sites inside
  `_skill_repo_managed_root()`).

## Open findings

canonical: "Neighbour check" section above (this record, this session).

None against this round's own change. The four neighbour-check sites
above are open (not fixed, explicitly named with reasons) but are not
findings *against this round's deliverable* -- they are pre-existing or
differently-scoped gaps surfaced by the check this round's task required,
not regressions this round introduced.

## Next steps

canonical: "Neighbour check" item 4 above (this record, this session).

- Follow-up candidate: `gates/amends_landing.py:53`'s clone (neighbour
  check item 4) -- same missing-guard shape, one day old, closest in
  spirit to this round's fix. A future round scoped to that feature's own
  file/tests could apply the same `env=` pattern there.
- None of this round's own deliverable is open; `loop_state: landed`.
