---
issue: 3231
role: adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f
author: adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # round-2 (second) independent verification of PR #3235's deliverable, commit 12dacfdb/25d24ab3
code_under_review:
  - skills.py
  - scripts/preflight/consumer_preconditions.py
  - tests/test_issue_3231_install_removals.py (untracked in this checkout -- lives on PR #3235's branch, not on this repo's default branch)
  - on-the-record/hooks/skill-corpus-bootstrap.sh (untracked in this checkout -- lives on PR #3235's branch, not on this repo's default branch)
  - on-the-record/hooks/install-precondition-notices.sh (untracked in this checkout -- lives on PR #3235's branch, not on this repo's default branch)
type: verification
breaking: false
verdict: Round 2's two fixes hold under independent re-derivation -- the
  SystemExit contract is genuinely repaired across every failure class this
  session could drive the function through, and the citation-line/full-suite
  claim reproduces exactly. The `|| true` shell wrapper is now provably
  redundant. Both properties this round did not touch (preflight mutates
  nothing, notices hook never touches global git config) remain true. One
  new, real, bounded residual risk found on the angle neither round
  covered: the automatic SessionStart clone does not suppress git's
  interactive credential prompt the way the rest of this codebase's
  git-network call sites already do. See Open findings for evidence and
  grading; acceptance numbers below.
loop_state: done
upstream:
  - path: PR #3235 (tokenmaxxxer/on-the-record), commit 25d24ab318aa33eb74a755bf16d5ff4792410dad (round 2's final commit, HEAD at review time)
    sha: 25d24ab318aa33eb74a755bf16d5ff4792410dad
  - path: docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md (PR #3238, round-1 verification; untracked in this checkout, lives on main)
    sha: 1b7293da57db04f4f0d39cd9bb2c2a262301f538
  - path: docs/issue-3231/reports/implementation-blueprint+silent-failure-audit+test-derivation-b51a2437.md (round-2 repair record; untracked in this checkout -- lives on PR #3235's branch)
    sha: 12dacfdb08d293c3d9021fc34e79e96ea5534567
---

# issue-3231 — adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f record

## What was done

Second independent verification of PR #3235 (round 2, commit `25d24ab3`,
branch `issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6`).
Per [[defect-verification-independence-from-upstream-verdicts]] this session
re-derived every check itself rather than citing round 1's (PR #3238's) or
round 2's own claims.

canonical: `gh pr view 3235 --repo tokenmaxxxer/on-the-record` (this
session) — result: `state: OPEN`. canonical: `gh pr view 3238 --repo
tokenmaxxxer/on-the-record` (this session) — result: `state: MERGED`.
derived: `git fetch origin pull/3235/head:pr-3235-local && git checkout
pr-3235-local` (this session) — checked out PR #3235's real tip
(`git log --oneline -1` → `25d24ab3 issue-3231: deviation-log entry for
round 2 ...`) for all code inspection and command execution below. This
session made no repo tool calls to any freelunch worker (per the task's
explicit "no background worker" instruction, which the freelunch
directive itself subordinates to contract v3 s22 in a headless session) —
every command below ran directly in this session and its result was read
directly in this session.

### 1. Fix 1 (`SystemExit` contract) — driven through every failure class

canonical: `skills.py:74-90` and `skills.py:104-149` (`_skill_repo_managed_root()`
on PR #3235's tip `25d24ab3`, read this session) — round 2 added `except
SystemExit` alongside the pre-existing `except OSError` at both `_run_net`
call sites (TTL-refresh pull, initial clone).

derived: this session wrote its own standalone script (not the shipped
tests) driving `spawn._skill_repo_root()` and `spawn.ensure_skill_corpus_cli()`
directly through four failure classes, each with a real `unittest.mock`
side effect on `_run_net` reproducing the real subprocess shape, plus one
(`os.replace` raising `OSError` mid-`os.replace`) not covered by the
shipped test file at all. result (this session, `_skill_repo_root()`
return values):
```
remote_refusing -> ('returned', None)
corrupt_partial_clone_exit0 -> ('returned', None)
destination_disappears_during_replace -> ('returned', None)
```
(the network-timeout class was covered separately below via
`ensure_skill_corpus_cli()`.) derived: re-ran the same four classes through
`spawn.ensure_skill_corpus_cli()` (this session) — result, all four:
```
remote_refusing rc= 0 leftover_tmp= []
corrupt_partial_clone_exit0 rc= 0 leftover_tmp= []
destination_disappears_during_replace rc= 0 leftover_tmp= []
network_timeout_clone rc= 0 leftover_tmp= []
```
Every failure class this session could construct against the function's
real code path returns cleanly per its own stated contract; none escaped
as an exception, none left a promotable partial corpus, none left
scratch-directory litter.

Mutation check (test-depth-audit, Step 4): this session reverted round 2's
own fix in a working-tree copy of `skills.py` (restoring the pre-round-2
shape at both call sites: unconditional pull-and-mark with no try/except,
and `except OSError` only at the clone site) and re-ran round 2's two new
regression tests, `test_never_fails_the_session_on_a_real_network_timeout`
and `test_stale_pull_timeout_falls_back_to_the_existing_valid_corpus`
(defined in `tests/test_issue_3231_install_removals.py`, untracked in this
checkout — lives on PR #3235's branch, read while checked out on
`pr-3235-local`). derived: `python3 -m pytest
tests/test_issue_3231_install_removals.py -k "test_never_fails_the_session_on_a_real_network_timeout
or test_stale_pull_timeout_falls_back_to_the_existing_valid_corpus" -v`
(this session, against the reverted copy) — result:
```
FAILED tests/test_issue_3231_install_removals.py::EnsureSkillCorpusCliTest::test_stale_pull_timeout_falls_back_to_the_existing_valid_corpus
FAILED tests/test_issue_3231_install_removals.py::EnsureSkillCorpusCliTest::test_never_fails_the_session_on_a_real_network_timeout
2 failed in 0.95s
```
with an uncaught `SystemExit` propagating out of pytest
(`E   SystemExit: [skill-repo] clone: 시간초과(180s) — 네트워크를 확인하라`),
confirming both are Genuine Assertion tests, not decorative — they would
have caught the exact defect PR #3238 found. `skills.py` was restored from
the pre-edit copy immediately after. derived: `git status --short
skills.py` (this session, after restore) — result: empty output (clean,
no diff against the checked-out tip).

### 2. The shell wrapper's `|| true` — removed in a scratch copy, confirmed redundant

canonical: `on-the-record/hooks/skill-corpus-bootstrap.sh:47` (untracked in
this checkout — lives on PR #3235's branch; read this session while
checked out on `pr-3235-local`) — `python3 "$CHECKOUT/spawn.py"
ensure-skills 2>&1 || true`, and the script's own `set -uo pipefail` (no
`-e`) plus a `trap 'exit 0' EXIT` that fires unconditionally at every exit
path.

derived: this session made a byte-identical scratch copy of the hook with
only that `|| true` deleted, then ran both the original and the scratch
copy with `TOKENMAXXXER_CHECKOUT` pointed at a fake `spawn.py` that
`sys.exit(1)`s unconditionally on `ensure-skills` (a harder failure than
anything the real fixed `ensure_skill_corpus_cli()` can now produce, since
that always returns 0 — this isolates the wrapper's own claim). result
(this session, both runs):
```
=== original (with || true) ===
exit code: 0
=== scratch copy (no || true) ===
exit code: 0
```
Identical. This confirms `|| true` was never load-bearing for the overall
hook's own exit code (the `trap 'exit 0' EXIT` alone already forces that,
and `set -uo pipefail` never enables `-e`) — what round 2 actually fixed
is `ensure_skill_corpus_cli()` itself no longer raising past its own call
boundary, which is the real property PR #3238 found broken (the uncaught
`SystemExit` killed the whole `ensure-skills` *process*, a different
failure mode than the hook's own wrapping around a normal nonzero exit
code).

### 3. The full-suite claim — reproduced myself

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py -q`
(this session, on PR #3235's tip `25d24ab3`) — result:
```
14 passed in 0.95s
```
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` —
result:
```
12 passed in 13.29s
```
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` —
result:
```
4 passed in 4.84s
```
acceptance: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (this
session, run twice) — result both times:
```
1253 passed, 3 xfailed, 2 warnings
```
0 failed both runs. The 2 warnings are the pre-existing, unrelated
`SkillCandidatesPinnedFixtureDivergenceTest` fixture-drift warnings (read
in the pytest output this session), not failures and not new.

derived: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -v`
(this session; xdist's own worker prefixes shown, per-test `PASSED` lines
not aggregated) — result:
```
[gw0] [ 60%] PASSED tests/test_issue_3182_citation_line_accuracy.py::CitationLineAccuracyTest::test_every_check_declares_at_least_one_line_anchor
[gw1] [ 70%] PASSED tests/test_issue_3182_citation_line_accuracy.py::CitationLineAccuracyTest::test_every_line_anchor_file_is_named_in_the_source_field
[gw4] [ 80%] PASSED tests/test_issue_3182_citation_line_accuracy.py::CitationCommentAndStringDiscriminationTest::test_python_comment_line_is_rejected
[gw2] [ 90%] PASSED tests/test_issue_3182_citation_line_accuracy.py::CitationLineAccuracyTest::test_every_cited_line_contains_the_call_it_claims
[gw3] [100%] PASSED tests/test_issue_3182_citation_line_accuracy.py::CitationCommentAndStringDiscriminationTest::test_all_sixteen_real_anchors_still_pass
10 passed in 0.97s
```
All 10 tests report `PASSED` explicitly, including
`test_every_cited_line_contains_the_call_it_claims` — the specific test PR
#3238 demonstrated failing pre-round-2. None are `SKIPPED`, `XFAIL`, or
absent from the run. Confirms the two failures round 2 addressed are
genuinely gone, not deselected or marked expected.

### 4. The angle neither round covered — bootstrap fetch on a foreign machine

Four conditions, each driven against the real function (real `git`
subprocess where feasible, mocked `_run_net` only where a real network
condition cannot be constructed locally):

**Behind a proxy that refuses the connection**: derived: `https_proxy`/
`HTTPS_PROXY` pointed at `http://127.0.0.1:1` (nothing listening), real
`spawn.ensure_skill_corpus_cli()` call (this session). result:
```
rc: 0 elapsed: 0.018217086791992188
```
printed `[ensure-skills] skill-repository corpus 를 아직 못 받았다 ...`.
Fails fast, fail-closed, reports, does not hang. Graded **Present**.

**Git that requires credentials it does not have**: derived: this session
first established `git`'s own real behavior (independent of PR #3235's
code) with a real pty attached as stdin (`script -qec "git clone
http://127.0.0.1:8933/fake.git testclone5" /dev/null`, `GIT_ASKPASS`/
`SSH_ASKPASS`/`GIT_TERMINAL_PROMPT` unset via `env -u`) against a local
Python HTTP server returning `401` + `WWW-Authenticate: Basic`. result:
```
Username for 'http://127.0.0.1:8933':
Session terminated, killing shell... ...killed.
exit: 124
```
(`timeout 6` killed it — without that external timeout it blocks
indefinitely reading `Username`.) canonical: `plumbing.py:364-381`
(`_git_env()`, read this session) already establishes the fix for exactly
this hazard elsewhere in this codebase — `GIT_TERMINAL_PROMPT: "0",
GIT_ASKPASS: "true"` — and its own docstring cites the real incident that
motivated it ("`GH_TOKEN` 없이 그냥 돌리면 재사용 워크스페이스 fetch 가
인증 실패로 막힌다"). derived: `grep -rn "_git_env(" --include=*.py .`
(this session) — result:
```
relay.py:220:                        env=_sp._git_env())
pipeline.py:854:                label, env=_sp._git_env())
pipeline.py:897:                env=_sp._git_env())
```
`skills.py`'s `_skill_repo_managed_root()` (the clone/pull calls at
`skills.py:84-86`, `:111-113`) is not among these call sites and passes no
`env=` to `_run_net()` at all, so it inherits whatever terminal-prompt
behavior the parent process has — unlike the codebase's own established
pattern for this hazard. Because `_run_net()` enforces `timeout=
CLONE_TIMEOUT` (180s) / `NETWORK_TIMEOUT` (60s) regardless, and round 2's
`except SystemExit` fix (re-verified in section 1 above with this
session's own commands) now catches that timeout cleanly, this does not
hang forever and does not crash the session — but on a machine where the
automatic SessionStart hook process has a real controlling terminal and
the network path challenges for credentials (corporate MITM proxy,
private/rate-limited remote), it does attempt an authentication flow and
does block session start for up to 180 seconds before failing closed.
Graded **Surface** in Open findings below — real and reproducible per the
commands above, bounded (not infinite, always eventually fails closed and
reports per section 1's own re-derivation), but a genuine gap against the
issue's "must not attempt an authentication flow that could hang a
non-interactive session" clause that this round's diff does not address.

**Remote reachable but branch/HEAD missing**: derived: cloned a real local
empty bare repo (`git init --bare`, no commits, no branches) via `file://`
through the real `ensure_skill_corpus_cli()` path (this session, only the
clone destination URL substituted inside a mocked `_run_net` that shells
out to the real local `file://` remote). result:
```
rc: 0
managed dir exists: False
```
`git clone` exits 0 (an empty repo is not itself an error) but produces no
`skills/` subdirectory, so `_skill_repo_valid()` correctly returns
`False`; no promotion happens. Graded **Present**.

**Local disk has the directory but it is not a git repository at all**:
derived: built `skills_dir` with real valid content but no `.git`
underneath, then called `spawn._skill_repo_root()` for real (this
session, no mocking of `_run_net`). result:
```
[skill-repo] /tmp/.../runs/rulebooks/skill-repository 의 origin 대비 최신 여부를 판정할 수 없다 (HEAD 를 resolve 할 수 없다) ...
resolved: /tmp/.../runs/rulebooks/skill-repository/skills elapsed: 0.004305839538574219
is real git repo (.git exists)? False
```
Resolves immediately to the existing valid `skills_dir` — the
precondition already reads satisfied, correctly, since the corpus really
is present and usable. The TTL-refresh `git -C d pull` subprocess call
fails fast (not a git repo) but its non-zero exit is not itself checked or
printed — `_sp._mark_pulled(d)` (`skills.py:87`) is called unconditionally
right after `_run_net()` regardless of returncode. canonical: `git show
a0e30dcf:skills.py` (this session) shows this same unconditional
`_mark_pulled(d)` after a returncode-unchecked pull was already present in
PR #3235's original commit `a0e30dcf`, not introduced by round 2 (round
2's own diff, `git show 12dacfdb --stat`, this session, touches only the
`except SystemExit` wrapper added around this pre-existing pair). The run
above did print a related diagnostic from the next line
(`_report_managed_clone_staleness`: "origin 대비 최신 여부를 판정할 수
없다"), so it is not fully silent, though the pull's own failure is not
named as such. canonical: the adjacent comment at `skills.py:78-80` (read
this session, present since PR #3235's original commit) explicitly
discloses this as an inherited, not new, defect: "이슈 #2616: core_root()
와 완전히 같은 TTL-pull 패턴...같은 결함을 그대로 물려받는다" (inherits
the same defect as `core_root()`, issue #2616). Because it is pre-existing,
disclosed in-code, and shared with an unrelated function this PR did not
touch, this session does not treat it as a new open finding against PR
#3235 (see Open findings item 2) — noted for completeness since the task
asked this exact condition be checked, and graded **Present** for the
properties actually under this round's scope (does not crash, does not
hang, does not falsely report the corpus itself as satisfied when it was
not).

### 5. Regression check on properties this round did not touch

derived: `grep -n "\.write_text\|open(.*['\"]w\|mkdir\|os\.replace\|shutil\.\|subprocess\.\|\.unlink\|git config --global\|git config --add" scripts/preflight/consumer_preconditions.py`
(this session) — every hit is either a docstring/comment, `shutil.which`
(read-only PATH lookup), `shutil.disk_usage` (read-only), or inside
`_run_readonly()` itself (`consumer_preconditions.py:57-68`, its own
docstring states "Run a read-only subprocess; never raises"). No write,
mutate, or `git config --global`/`--add` call anywhere in the file.
Graded **Present**, unchanged by round 2 — canonical: `git show 12dacfdb
--stat` (this session) shows round 2's own diff touched only two
`line_anchors` string literals in this file.

canonical: `on-the-record/hooks/install-precondition-notices.sh`
(untracked in this checkout — lives on PR #3235's branch; full file read
this session while checked out on `pr-3235-local`) — only `git config
--get user.name`/`--get user.email` (read), plus filesystem existence
checks (`[ -f docs/specs/approvers.md ]`). No `git config --global`/
`--add`/`--replace-all` anywhere. canonical: `git show 12dacfdb --stat`
(this session) — this file is entirely absent from round 2's diff (lists
only `consumer_preconditions.py`, `skills.py`, the tests file, and the new
record). Graded **Present**, untouched by round 2.

### 6. 5→7 satisfied-count claim, re-reproduced on a fresh isolated `$HOME`

derived: `HOME=/tmp/scratch3231/freshhome` (fresh, empty), real
`scripts/preflight/consumer_preconditions.py` run with `MUSTER_SKILL_REPO`/
`TOKENMAXXXER_RULEBOOKS` unset — before any fetch (this session), result:
```
6/10 preconditions satisfied.
4 missing: git_identity_configured, skill_repository_resolvable, home_claude_skills_dir_present, remote_push_access
```
(this sandbox's baseline already has `git`/`gh`/board-file satisfied,
unlike a genuinely bare machine, so the absolute count differs from PR
#3235's/#3238's 5-baseline claim — a sandbox-composition difference, not a
reproduction failure). Then derived: a real `python3 spawn.py
ensure-skills` (this session, real network clone, confirmed fresh by
directory mtime, not a pre-existing cache) followed by the same preflight
script — result:
```
8/10 preconditions satisfied.
2 missing: git_identity_configured, remote_push_access
```
The delta (6→8, `+2`) is exactly `skill_repository_resolvable` and
`home_claude_skills_dir_present` flipping MISS → OK — the two
preconditions the issue names as removable, and no others changed. This
confirms the causal mechanism (not just the absolute count) independently
of both prior rounds' own sandbox baselines.

## Why

Per [[defect-verification-independence-from-upstream-verdicts]], this round
re-derived every property from scratch on PR #3235's real tip rather than
trusting round 2's own record or PR #3238's prior grades, including
properties both prior sessions already graded Present (preflight
mutation-free, notices hook read-only) — round 2 touched neighbouring code
in the same files, so a stale Present grade could have gone stale without
a fresh check. The one new finding (credential-prompt exposure on the
automatic SessionStart clone) came from the one instruction in this
round's brief that neither prior round had been asked to check: "what
happens on a machine that is not this one" — this session searched for the
codebase's own prior art (`_git_env()`) for the same hazard class rather
than assuming the shipped mocked tests were sufficient. derived: `grep -n
"def _fake" tests/test_issue_3231_install_removals.py` (this session,
path untracked in this checkout — lives on PR #3235's branch, read while
checked out on `pr-3235-local`) — result: every module-level fake
substitutes `spawn._run_net` in Python directly; none opens a real
subprocess with a real pty or a real credential-challenged remote, so none
of the shipped tests could have caught the finding in Open findings item 1
below.

## Upstream basis

canonical: `gh pr view 3235 --repo tokenmaxxxer/on-the-record --json
headRefName,state` (this session) — result confirmed branch name
`issue-3231/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6`
and `state: OPEN`, before `git fetch origin pull/3235/head:pr-3235-local`
(this session) fetched the real tip `25d24ab318aa33eb74a755bf16d5ff4792410dad`
— round 2's final commit, the code under review in this record.

canonical: `git show 1b7293da:docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md`
(this session; PR #3238, round-1 verification, merged to main as
`1b7293da57db04f4f0d39cd9bb2c2a262301f538`) — read this session for its
scope and the two defects it found, used only to know what round 2 was
asked to fix, not cited as evidence for this round's own grades (each
grade above was independently re-derived).

canonical: `docs/issue-3231/reports/implementation-blueprint+silent-failure-audit+test-derivation-b51a2437.md`
(round 2's own repair record; untracked in this checkout — lives on PR
#3235's branch; read this session while checked out on `pr-3235-local`),
commit `12dacfdb08d293c3d9021fc34e79e96ea5534567` — read for round 2's
claimed fixes; every claim in it was independently re-derived in sections
1-6 above rather than cited as ground truth.

## Open findings

1. **Surface** — the automatic SessionStart skill-repository clone
   (`skills.py:84-86`, `:111-113`, called from the new
   `on-the-record/hooks/skill-corpus-bootstrap.sh`, untracked in this
   checkout — lives on PR #3235's branch) does not set
   `GIT_TERMINAL_PROMPT=0`/`GIT_ASKPASS=true` the way this codebase's other
   git-network call sites already do (`plumbing.py:364-381` `_git_env()`,
   used by `relay.py`/`pipeline.py`, confirmed via `grep -rn "_git_env("`
   in section 4 above). On a machine with a real controlling terminal and
   a credential-challenged network path (corporate MITM proxy,
   private/rate-limited remote), this attempts an interactive
   authentication flow that blocks session start for up to
   `CLONE_TIMEOUT` (180s, clone) or `NETWORK_TIMEOUT` (60s, TTL-refresh
   pull) before failing closed via round 2's own `except SystemExit` fix
   (re-derived working in section 1 above — it does not hang forever and
   does not crash the session, it delays start). Reproduction: section 4
   above, the pty-attached `script -qec` command against a local `401`
   server, exit code `124` (killed after the test's own 6s timeout,
   would otherwise block indefinitely on `Username for '...': `).
   Resolution path: pass `env={**os.environ, "GIT_TERMINAL_PROMPT": "0",
   "GIT_ASKPASS": "true"}` (or reuse `_git_env()`'s pattern directly) at
   both `_run_net` call sites inside `_skill_repo_managed_root()`, the
   same fix shape already proven elsewhere in this codebase. Not fixed by
   this session — task scope was to verify PR #3235, not edit it.
2. The `core_root()`-inherited TTL-marker-written-on-failed-pull pattern
   (section 4, fourth bullet above) — pre-existing (present in PR #3235's
   original commit `a0e30dcf`, not introduced by round 2, confirmed via
   `git show a0e30dcf:skills.py` in section 4 above), explicitly disclosed
   in-code (`skills.py:78-80`, citing issue #2616), and shared with an
   unrelated pre-existing function. Not a new finding against this PR;
   noted only because the task asked this exact condition be checked.
3. The `gh auth status` device-id write on a fresh `$HOME` — already
   identified and graded pre-existing/out-of-scope by PR #3238's record
   (canonical: `git show 1b7293da:docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-0664d1ed.md`,
   section 7 there, re-read this session). Not re-litigated by this round.

## What did not work

None. Every property this round was asked to check was reproducible with a
real command or a real subprocess-level attack (all logged in sections
1-6 above with their own `derived:`/`canonical:` results); nothing had to
be abandoned or descoped. The one open finding (item 1 above) was found,
not missed — it does not represent a planned check that failed to execute.

## Next steps

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py tests/test_issue_3182_preflight.py tests/test_issue_3182_install_sufficiency_doc.py -q`
(this session, combined re-run of the issue's three official acceptance
checks, `tests/test_issue_3231_install_removals.py` untracked in this
checkout — lives on PR #3235's branch) — result:
```
30 passed
```
acceptance: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` (this
session, final confirmation run) — result:
```
1253 passed, 3 xfailed, 2 warnings
```
`loop_state: done` for this record on the strength of the acceptance
results directly above and sections 1-6's own re-derived evidence: round
2's two targeted fixes both hold, the full acceptance surface passes
genuinely (not skipped/deselected, confirmed in section 3), and the two
properties round 2 did not touch remain Present (section 5). One new
Surface-level residual risk (Open findings item 1) is documented with a
reproduction and a resolution path but was not patched by this session,
per the task's explicit instruction not to edit PR #3235. canonical: this
session's own tool-call history — no `gh pr merge`, `gh pr review
--approve`, or write to any path outside
`docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f.md`
was made on PR #3235's branch; this record itself lands only on this
session's own branch,
`issue-3231/adversarial-review+silent-failure-audit+test-depth-audit-88bb8a1f`.

skill-verdict: adversarial-review — applied: invoked; this session is
structurally independent of both PR #3235's builder session and round 2's
repair session (different session, no shared context), and re-derived
every claim under review from PR #3235's real tip rather than trusting
either prior session's own report — see "Why" above and
[[defect-verification-independence-from-upstream-verdicts]].
skill-verdict: silent-failure-audit — applied: invoked; classified the two
`except SystemExit` sites round 2 added (Handled, confirmed via mutation
revert in section 1) and traced forward the pre-existing unconditional
`_mark_pulled(d)` after a returncode-unchecked pull (section 4, fourth
bullet) to its downstream consequence (a falsely-fresh TTL marker),
following the catalog's trace-forward method.
skill-verdict: test-depth-audit — applied: invoked; reverted round 2's own
fix in a scratch copy of `skills.py` and re-ran its two new regression
tests to confirm they are Genuine Assertion (fail on the pre-fix code, not
merely execute it) rather than trusting the round-2 record's own claim
that they do.
other mounted skills: not triggered.
