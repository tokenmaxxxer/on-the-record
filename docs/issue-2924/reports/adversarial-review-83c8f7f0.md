---
issue: 2924
role: adversarial-review-83c8f7f0
author: adversarial-review-83c8f7f0
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: terminal
upstream:
  - path: PR #2955 (branch issue-2924/silent-failure-audit+refactoring-legacy-seam-selection-140f0858, kept alive locally as branch review-pr-2955-cite so cited paths stay git-history-reachable)
    sha: 68f26fe6b25ff0a42a499d989a0f1491f1451cef
---

# issue-2924 — adversarial-review-83c8f7f0 record

## What was done

Independent adversarial verification of PR #2955 (`68f26fe6`, targeting
issue #2924). Every claim below was re-derived from primary sources —
diff, isolated worktree checkouts, and live execution, including a real
`bash:3.2` Docker container — never taken from PR #2955's own record.
Five attack points were dispatched to independent sub-agents, each
working in its own `git worktree` off `review-pr-2955-cite`; the
container corroboration and final synthesis were carried out directly in
this session.

canonical: `gh pr view 2955 --json headRefOid,headRefName` -- result:
`headRefOid: 68f26fe6b25ff0a42a499d989a0f1491f1451cef`,
`headRefName: issue-2924/silent-failure-audit+refactoring-legacy-seam-selection-140f0858`
-- this is the exact commit every finding below is checked against.

acceptance: `python3 -m pytest -q` on PR HEAD in worktree
`/tmp/wt-pr2955-angle5` — result: `17 failed, 732 passed, 3 xfailed in
33.70s`; acceptance: `python3 -m pytest -q` on merge-base `8c60562c` in a
second worktree — result: `17 failed, 722 passed, 3 xfailed in 33.50s`;
failed-test-name sets diffed identical between the two runs, and the
10-test delta (732-722) is exactly the new tests this PR adds. Overall
verdict: PASS, no blocking defects, based on all five attack-point
transcripts below. Two non-blocking gaps are recorded as open findings:
(1) four confirmed false-positive shapes in the check's pattern-matching
rules, currently latent; (2) one live GNU-only construct
(`68f26fe6:on-the-record/hooks/stop-poll-rearm.sh:129`'s bare `timeout`)
that both the issue body's own enumeration and this PR's coverage miss,
though it degrades gracefully.

### Attack 1 — is the check real, or fitted to its own two test-case bugs?

`68f26fe6:on-the-record/checks/macos_bash32_compat.py` (a new file this
PR adds — it exists on PR branch `68f26fe6`/`review-pr-2955-cite`, not
on this record's own branch) implements 4 rule families: flock-without-
guard, array-expansion-without-guard, `stat -c`-without-`stat -f`-
fallback, and a `/proc`-dependency allowlist for `.py` files.

canonical: sub-agent (id `a901155e500cc3135`), in worktree
`/tmp/wt-pr2955-angle1` off `review-pr-2955-cite`, ran `git show
29d00cb553aec34cd7c87e950cd4b4153ead24de:on-the-record/monitors/poll-heartbeat.sh`
piped into `check_sh_file()` -- result: 2 violations (flock line 163,
array line 303, both matching #2919's shape); same agent ran
`check_sh_file()` against current-HEAD `poll-heartbeat.sh` -- result: 0
violations; ran `python3 -m pytest
on-the-record/checks/test_macos_bash32_compat.py -v` -- result: `4
passed`. This confirms fail-then-pass on the exact #2919 bugs the check
was built from.

derived: same sub-agent wrote one NEW synthetic violation per rule
(fresh unguarded `flock`, fresh unguarded array expansion, fresh `stat
-c` with no fallback, fresh `/proc` read in a `.py` file not on the
allowlist) and ran the check against each, including the full `run()`
pipeline (not just the low-level detector) for the `/proc` case --
result: all four caught, no false negatives on any rule in isolation.
This is the evidence that the check generalizes past the two bugs it was
written from, not merely fitted to them.

Independently reproduced the array-bug corroboration myself, in this
session, against a real `bash 3.2.57` container:
canonical: `docker run --rm bash:3.2 bash --version` -- result: `GNU
bash, version 3.2.57(1)-release (x86_64-pc-linux-musl)`; `docker run
--rm -v "$WD":/work bash:3.2 bash /work/pre_array.sh` where
`pre_array.sh` is `set -uo pipefail; IFS=' ' read -r -a ARR <<<""; for x
in "${ARR[@]}"; do echo "$x"; done; echo done` -- result: `line 3:
ARR[@]: unbound variable`, exit=1; `docker run --rm -v "$WD":/work
bash:3.2 bash /work/head_array.sh` (same script, loop replaced with
`${ARR[@]+"${ARR[@]}"}` guard) -- result: `done`, exit=0. This matches
PR #2955's own record claim
(`68f26fe6:docs/issue-2924/reports/silent-failure-audit+refactoring-legacy-seam-selection-140f0858.md:150-175`)
— independently re-derived here, not copied from it.

derived: same sub-agent's transcript confirms pytest wiring is plain
`test_*.py` discovery (`grep -r conftest` over the repo -- result: no
`conftest.py` anywhere, no plugin/entry-point registration) -- so the
check protects a bare `pytest` run from repo root (matching this repo's
actual convention) but is not enforced against a narrower, path-scoped
invocation. Non-blocking.

### Attack 2 — false positives (matters more than true positives, since this runs on every pytest invocation)

canonical: sub-agent (id `aa42c18dda124c63e`) ran `python3
on-the-record/checks/macos_bash32_compat.py --verbose` against the full
live corpus at HEAD -- result: population 53 live `.sh`, 132 live `.py`;
`PASS`, exit 0 -- zero violations today.

derived: same sub-agent adversarially probed each of the 4 rules and
confirmed a false-positive shape for all 4, each demonstrated with a
working snippet and pasted check output -- result: (1) flock guard —
`command -v "flock"` (quoted), `type -p flock` (POSIX alternative), and
a bare comment mentioning "flock" with zero real invocations are all
misflagged; (2) `stat -c` fallback — a heredoc/usage-text body
containing the string `stat -c %Y file` is flagged as executable code;
(3) array guard — a function using `set +u` ... expand ... `set -u` (a
standard, version-independent safe idiom) is still flagged, because the
only recognized safe marker is the literal `[@]+` substring on the same
line; (4) `/proc` allowlist — a docstring sentence merely mentioning
`'/proc/self/status'` in prose, with zero live `/proc` access, is
flagged as a new dependency.

derived: same sub-agent's separate corpus sweep, cross-confirmed by
attack 4's independent 232-file enumeration below -- result: none of
these four false-positive shapes exist in the live corpus today, so
today's `PASS` is trustworthy — but the rules are narrow single-shape
pattern matches, and the check's own design goal explicitly names noise
as an existential risk (source-quoted in its own docstring per the
sub-agent's report), so this is a genuine, currently-dormant risk to the
check's longevity, not a blocking defect today.

### Attack 3 — Linux path genuinely unchanged, and does the new visibility reach a reader?

canonical: sub-agent (id `a8497a0915503b028`), worktree `angle3`, ran
`git diff $(git merge-base main HEAD) HEAD -- roster.py watchdog.py` --
result: +33 lines in `roster.py` (module-level `_PROC_AVAILABLE =
os.path.isdir("/proc")`, a `_note_proc_identity_degraded()` print-once
helper, and one `if not _PROC_AVAILABLE:` branch each inside
`_watcher_looks_real` / `_session_looks_real`), +19 in `watchdog.py` (a
`degraded_note` string appended to `watchdog_lock_acquire`'s refusal
message only when `other_start is None`); ran `pytest
test/test_proc_identity_degradation_visibility.py -q` -- result: `6
passed`, including `test_watcher_looks_real_silent_when_proc_available`
and `test_refusal_message_unchanged_when_start_time_is_real`, both
asserting byte-identical Linux behaviour.

derived: on Linux `_PROC_AVAILABLE` is always `True` (procfs always
mounted) per the diffed source above, so every new conditional is
provably dead code on that branch and the prior statements execute in
the same order with the same result -- CONFIRMED genuinely unchanged,
not merely intended to be, corroborated by the diff itself, not just the
PR's own tests. Caveat (non-blocking): `_PROC_AVAILABLE` is a snapshot
taken once at module import, not re-checked per call — if `/proc`
vanished mid-process (pathological on Linux) the degrade would still be
silent for that call, a real-but-negligible gap on the platform where it
matters.

derived: same sub-agent's transcript, `grep -rn 'while True\|time.sleep'
watchdog.py spawn.py` -- result: no matches — confirms
`roster_watchdog()` is not a daemon loop. Cross-referenced against
`68f26fe6:on-the-record/monitors/poll-heartbeat.sh:426`'s bash loop
(`sleep 120`) invoking `python3 spawn.py watchdog --auto-respawn` as a
brand-new subprocess each tick, with combined stdout+stderr appended to
`~/.claude/tokenmaxxxer/poll-watchdog.log` -- result: a fresh process
each tick means the print-once flag resets every cycle, so the note
recurs for as long as the degraded condition persists and lands in a
persistent, greppable log file — an operator attaching late (`tail -f`)
sees it again within one cycle. The task's hypothesized worst case (a
long-lived process where a late-attaching operator never learns the
guard is off) does not match this codebase's actual invocation pattern;
it would only apply to a hypothetical caller that imports `roster.py`
once and keeps calling these functions repeatedly inside one long-lived
process, which does not currently exist in this codebase.

### Attack 4 — independent re-derivation of the GNU-only-construct enumeration; is claim (d) right that the issue body was wrong?

canonical: sub-agent (id `a9e73061952700d24`) ran `git ls-files '*.sh'
'*.py' | grep -v '^docs/'` -- result: 232 files (deliberately broader
than the check's own 185-file population — it also swept `test/` paths,
and a wider construct list: `stat -f`, `readlink -f`, `sed -i`, `date
-d`, `ls --color`, `grep -P`, `md5sum`, `timeout`, `find -printf`,
`xargs -r`, `realpath`, `nproc`, `base64 -w`, `mapfile`, `declare -A`,
GNU `getopt`).

canonical: same sub-agent ran `git diff $(git merge-base main HEAD) HEAD
-- on-the-record/hooks/decision-queue-stopgate.sh` -- result: empty,
exit 0 (PR #2955 made zero changes to this file); ran `git log -p
--follow -- on-the-record/hooks/decision-queue-stopgate.sh` -- result:
the `stat -c ... || stat -f ... || echo 0` line was added (not modified)
in commit `aa207739`, "issue-2016 phase 2: cut PreToolUse/Stop hook
wall-clock via short-circuit + TTL cache (#2027)"; ran `git merge-base
--is-ancestor aa207739 <PR-2955-merge-base>` -- result: yes. Claim (d)
CONFIRMED: the `stat -c || stat -f` fallback predates PR #2955 by an
unrelated issue-2016 commit; the PR correctly made no changes there.
This also means the issue-2924 body's premise — that this `stat -c` site
was the population's only live GNU-only construct — was already stale
when written, and PR #2955's claim (d) correctly identifies that.

canonical: independently confirmed myself, in this session: `git log -1
--format=%cI -- on-the-record/hooks/stop-poll-rearm.sh` -- result:
`2026-08-28`; `git show
85d9f61d:on-the-record/hooks/stop-poll-rearm.sh | grep -n timeout` --
result: line 129 present, `timeout 20 python3
"${checkout}/spawn.py" deadman-check 2>/dev/null || true`; `git
merge-base --is-ancestor 85d9f61d HEAD` -- result: yes. The issue body
states its population was "enumerated at `85d9f61d`" — this bare
`timeout` line was present in that exact file at that exact commit, so
this is a live miss in the issue's own enumeration, not a
later-introduced gap: neither the issue-2924 body nor PR #2955's
coverage names it, and `68f26fe6:on-the-record/checks/macos_bash32_compat.py`'s
`_GNU_ONLY_BARE` rule set (derived: read directly in Attack 1 and Attack
2 above) does not check for `timeout` at all. Severity is low — the
function's own comment says "Any failure mode (timeout, missing python,
import error) is swallowed," and `|| true` catches the shell's exit-127
("command not found") from a missing `timeout` binary, so on macOS
without coreutils this advisory deadman-check silently never fires
rather than crashing. Out of this PR's stated scope (the `#2919`/`#2924`
population plus `decision-queue-stopgate.sh`, already covered), so not a
blocker for this PR, but it directly falsifies the "no other live
GNU-only site" framing.

### Attack 5 — fail-open risk, standing invariants, numeric claims

canonical: sub-agent (id `a22637d15497052a5`) `chmod 000`'d a tracked
file post-`git add` to force a read exception in `run()` -- result:
`PermissionError` propagates as a genuine pytest FAILURE (no
try/except around `read_text()` in
`68f26fe6:on-the-record/checks/macos_bash32_compat.py:165-170`); moved
`macos_bash32_compat.py` aside -- result: `ModuleNotFoundError` at
collection time, `Interrupted: 1 error during collection`, the entire
suite refuses to run rather than silently skipping the file's own tests;
added a new `.py` file with unguarded `/proc` access, not on
`KNOWN_PROC_SITES` -- result: check reports `FAIL`, exit 1, offending
test fails. Fail-open risk REFUTED for all three probed shapes — parse
errors, a missing module, and a stale allowlist all fail loud/closed,
not silent/open.

derived: same sub-agent found two genuine (currently latent)
false-*negative* gaps instead, worth recording though non-blocking (no
live file exploits them) -- result: `_GNU_ONLY_BARE` regexes require the
GNU-only flag immediately after the command token (`grep --color=auto
-P` or `sed -e ... -i` would slip past, confirmed absent from the live
population via `grep`), and the array-guard check is line-granular, not
per-occurrence (`echo "${good[@]+"${good[@]}"}" "${bad[@]}"` on one line
returns zero violations despite the second array being genuinely
unguarded — exactly #2919's defect class, reintroduced by co-location).

canonical: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py
-v` -- result: `4 passed`; `python3 -m pytest
test/test_proc_identity_degradation_visibility.py -v` -- result: `6
passed`. "4 + 6 tests pass" CONFIRMED exactly.

canonical: `python3 -m pytest -q` on PR HEAD -- result: `17 failed, 732
passed, 3 xfailed in 33.70s`; `python3 -m pytest -q` on merge-base
`8c60562c` in a second worktree -- result: `17 failed, 722 passed, 3
xfailed in 33.50s` — failed-test-name sets diffed identical between the
two runs; the 10-test delta (732-722) is exactly the new 4+6 tests. "17
pre-existing failures, same set with and without the change" CONFIRMED
exactly, full summary lines pasted verbatim, not rounded.

derived: `git diff <base> HEAD -- roster.py watchdog.py <new files> |
grep -in 'role\b'` -- result: empty — no role-axis revival found. `time
python3 -c "...check.run(verbose=True)..."` -- result: `73ms` against
the full 53+132-file corpus — negligible overhead, well under a
"sub-second to couple seconds" bar. `pytest
test/test_bootstrap_signal_guard.py
test/test_proc_identity_degradation_visibility.py
test/test_reconcile_crash_verdict_race.py
test/test_session_completion_heartbeat.py
test/test_spawn_attempt_staleness.py
test/test_unrecovered_commit_count.py
test/test_watchdog_heartbeat_noise.py
test/test_workspace_progress_tracking.py -q` -- result: `113 passed` —
no monitor/watchdog breakage. The two latent false-negative gaps noted
above are the only new-bug candidates found reading the diff closely;
neither is exploited by any live file today.

canonical: independently ran myself, in this session: `git diff
--diff-filter=M $(git merge-base main review-pr-2955-cite)
review-pr-2955-cite -- docs/` -- result: empty (only additions under
`docs/`, no modifications) -- the historical-records-never-modified
invariant holds.

## Why

Adversarial review requires re-deriving claims from primary sources, not
trusting the builder's own record — so every command in this record was
re-run independently (four via isolated `git worktree` checkouts per
sub-agent, one — the bash:3.2 container corroboration — directly in this
session) rather than copied from PR #2955's own record. Five attack
points were dispatched to independent sub-agents because each required
its own checkout/container/full-suite-run with no shared mutable state
between them (fan-out per the freelunch research exception); the
container corroboration and final synthesis were carried out directly in
this session since they either needed a single quick verification or
required judgment across all five reports that isn't delegable.

canonical: this synthesis is grounded in the `canonical:`/`derived:`
transcripts pasted under Attacks 1-5 above, plus the two commands run
directly in this session (`docker run --rm bash:3.2 ...` for the array
corroboration, `git diff --diff-filter=M ... -- docs/` for the
historical-records invariant) — not in PR #2955's own record.

## What did not work

None — all five attack points and the container corroboration produced
usable evidence per the `canonical:`/`derived:` transcripts above; no
dead ends or discarded approaches.

## Upstream basis

- PR #2955, branch `issue-2924/silent-failure-audit+refactoring-legacy-seam-selection-140f0858`,
  head `68f26fe6b25ff0a42a499d989a0f1491f1451cef` (sha: real). canonical:
  `gh pr view 2955 --json headRefOid` -- result: matches.
- `68f26fe6:docs/issue-2924/reports/silent-failure-audit+refactoring-legacy-seam-selection-140f0858.md`
  — read for context only, never taken as ground truth; every claim it
  makes that this record relies on was independently re-derived above,
  not copied.
- Issue #2924 body. canonical: `gh issue view 2924` -- result: read
  directly for acceptance criteria and the original enumeration claim
  ("Population enumerated at `85d9f61d`... excluding `docs/`... and test
  files").
- Commit `a826a010` (issue-2919 fix) and its parent `29d00cb5` — used as
  the pre-fix/post-fix pair for the fail-then-pass proof (see Attack 1).

## Open findings

1. Four confirmed false-positive shapes in
   `68f26fe6:on-the-record/checks/macos_bash32_compat.py`'s
   pattern-matching rules (see Attack 2 above for the full `derived:`
   evidence) — currently latent, no live file exploits them, but a real
   risk to the check's longevity per its own stated design goal (noise →
   disabled). No resolution path assigned; follow-up hardening, not a
   blocker.
2. Two confirmed false-negative gaps (GNU-flag-position regex, line-
   granular array-guard check — see Attack 5 above for the full
   `derived:` evidence) — currently latent, exactly #2919's defect class
   if ever reintroduced by co-location. No resolution path assigned;
   follow-up hardening, not a blocker.
3. `68f26fe6:on-the-record/hooks/stop-poll-rearm.sh:129`'s bare
   `timeout` (no `gtimeout`/`command -v timeout` guard — see Attack 4
   above for the full `canonical:` evidence, verified present at commit
   `85d9f61d`, the issue's own enumeration point) is a live GNU-only
   construct missed by both the issue-2924 body's own enumeration and PR
   #2955's coverage; degrades gracefully (silent no-op, not a crash) but
   is exactly the "nothing prevents the next divergence" shape the issue
   names. Out of this PR's stated scope; flagged for the orchestrator to
   file as follow-up, not fixed here per this skill's evaluate-don't-fix
   mandate.

## Next steps

None — this record is terminal. `loop_state: terminal` per the
frontmatter above.

skill-verdict: adversarial-review — applied: invoked; this entire record
is the adversarial-review skill applied to PR #2955, structurally
independent verification via isolated worktrees and a live container
reproduction rather than trusting the builder's record.
other mounted skills: not triggered (work-in-english guidance was
followed throughout — record, commits, and PR are English-only — without
a separate Skill-tool invocation since no Korean-language input needed
translating; implementation-audit is a guidance-only task-text match per
the task header, not independently invoked this session).
