---
issue: 3281
role: silent-failure-audit+test-depth-audit-4856384e
author: silent-failure-audit+test-depth-audit-4856384e
skills: silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3282's deliverable, angle: the check itself
loop_state: terminal
code_under_review: on-the-record/checks/macos_bash32_compat.py, on-the-record/checks/test_macos_bash32_compat.py, on-the-record/hooks/amendment_channel.py, scripts/issue-3041/run_pair.sh (PR #3282, head b5a83907)
type: verification
breaking: false
verdict: PR #3282's own numbers reproduce exactly (4 passed on the compat check, 1652 passed/1 pre-existing failure/3 xfailed on the PR branch vs 1650 passed/2 failed/3 xfailed on main -- no new failures). The check itself has real, live-tree-confirmed blind spots -- most notably its own /proc regex misses `os.path.isdir("/proc")` (no trailing slash before the closing quote), the exact line this same PR added at amendment_channel.py:482 -- and its bare "PASS" carries none of the necessary-not-sufficient caveat the issue itself insists on.
upstream:
  - path: docs/issue-3281 (issue body, PR #3282)
    sha: 7d857d5f73096570a6cf385abf83608d3f253dd0
---

# issue-3281 — silent-failure-audit+test-depth-audit-4856384e record

## What was done

Second, structurally independent verification of PR #3282 (issue #3281),
angled at the check itself (`on-the-record/checks/macos_bash32_compat.py`)
rather than the fix.

canonical: this session's own tool-call transcript — no Edit/Write to any
code path, no `git push`/`gh pr merge`, no Agent/background dispatch;
every command cited below (`gh`, `git worktree`, `python3 -m pytest`,
`grep`) ran directly in this session's foreground, per the task's own
scope limits ("Do not edit or merge PR #3282. Do not run a background
worker.").

All commands below ran in this session's own worktree plus two throwaway
`git worktree` checkouts (`/tmp/pr3282-check` at PR #3282's head,
`/tmp/main-check` at `origin/main`), both removed
(`git worktree remove --force`) before this record was written.

### 1. Coverage: what the check does and does not catch

The task's own framing ("it scans live .sh and .py files for two shapes")
undersells the check as shipped.

canonical: `on-the-record/checks/macos_bash32_compat.py`, read directly
this session, lines 100-149 (`check_sh_file`) and 152-158
(`check_py_file`); `git log --oneline -- on-the-record/checks/macos_bash32_compat.py`
shows one commit (`71167c3a`, issue #2924), predating this branch — PR
#3282 does not touch this function's logic.

`check_sh_file()` alone runs seven checks: `flock` without a
`command -v flock` guard, `stat -c` without a same-line `stat -f`
fallback, four bare `_GNU_ONLY_BARE` patterns (`sed -i`, `date -d`,
`readlink -f`, `grep -P`), and the `"${arr[@]}"`-under-`set -u` shape.
`check_py_file()` adds the `KNOWN_PROC_SITES` allowlist check. That is
nine rule shapes total, not two.

**Live-tree count of the task's candidate gaps**, population built via
the check's own `is_live()`/`list_population()` logic re-implemented
verbatim:

derived: `python3 /tmp/list_live.py` (script body: `git ls-files '*.sh'
'*.py'` filtered through the check module's own `is_live()` regex,
`docs/` and `test`/`tests` paths excluded) — result: `62 177`, i.e. 62
live `.sh` files and 177 live `.py` files.

| Candidate | Live sites found | Already caught? |
|---|---|---|
| `sed -i`, `date -d`, `readlink -f`, `grep -P` | 0 | n/a (none exist) |
| `stat -c` | 1 | Yes — same-line `stat -f` fallback, correctly not flagged |
| `flock` | 1 | Yes — guarded with `command -v flock`, correctly not flagged |
| `base64 -w`, `/dev/shm`, `declare -A`, `mapfile`/`readarray`/`${var,,}`/`${var^^}`/`wait -n`/`coproc` | 0 each | n/a |
| **`timeout` (GNU coreutils)** | **3** | **No — zero rule for it** |
| duplicate paths differing only by case | 0 | n/a |

derived (one call per row, live `.sh`/`.py` files from `/tmp/live_sh.txt`
+ `/tmp/live_py.txt` above):
```
$ grep -nE '\bstat\s+-c\b' <62 live .sh files>
on-the-record/hooks/decision-queue-stopgate.sh:73:  mtime="$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)"
$ grep -nE '(^|[^\w#])flock(\s|$)' <62 live .sh files>
on-the-record/monitors/poll-heartbeat.sh:225:if command -v flock >/dev/null 2>&1; then
on-the-record/monitors/poll-heartbeat.sh:284:      flock -x 200
$ grep -nE 'base64\s+-w|declare\s+-[a-zA-Z]*A|mapfile|readarray|/dev/shm' <62 live .sh + 177 live .py>
(no output)
$ git ls-files | tr 'A-Z' 'a-z' | sort | uniq -d
(no output — zero case-collision paths)
$ grep -nE '(^|[^A-Za-z0-9_./-])timeout[[:space:]]+[0-9]' <62 live .sh files>
on-the-record/hooks/stop-poll-rearm.sh:129:  timeout 20 python3 "${checkout}/spawn.py" deadman-check 2>/dev/null || true
scripts/issue-3041/run_pair.sh:96:      timeout 600 env "${UNSET_ARGS[@]}" claude -p "$PROMPT" \
scripts/issue-3041/run_pair.sh:109:      timeout 600 env "${UNSET_ARGS[@]}" claude -p "$PROMPT" \
```
(the `run_pair.sh` hits are this session's own pre-PR worktree; PR #3282
edits these same two lines for the array guard but leaves `timeout`
itself untouched.) `timeout(1)` is GNU coreutils, not installed by
default on macOS — a real, live, currently-uncaught macOS-breaking
construct sitting in the exact file this issue's fix touched, plus one
more site in `stop-poll-rearm.sh` the fix never looked at.

**A second, more consequential gap: the `/proc` regex itself has a blind
spot, and this PR's own fix lands inside it.**
`_PROC_RE = re.compile(r"[\"']/proc/")` requires a quote character
immediately followed by `/proc/` with a trailing slash.

derived: `python3 /tmp/test_proc_regex.py` (script applies `_PROC_RE`,
copied verbatim from the check's own source, to four literal samples) —
result:
```
False os.path.isdir("/proc")
True open("/proc/%d/stat" % pid)
True Path(f"/proc/{pid}/cmdline")
False os.path.isdir('/proc')
```
`os.path.isdir("/proc")` — no trailing slash before the closing quote —
does not match. PR #3282 adds exactly this line,
`if not os.path.isdir("/proc"): return NoProcOnPlatform()`, at
`on-the-record/hooks/amendment_channel.py:482` (`gh pr diff 3282`, hunk
under `record_amendment_from_response`) — invisible to `check_py_file()`.
The file was still routed into `KNOWN_PROC_SITES` only because it
already contains a *different*, matching line
(`open("/proc/%d/stat" % pid, ...)` at line 382, pre-existing —
`grep -n '"/proc/%d/stat"' on-the-record/hooks/amendment_channel.py`
confirms this line exists both before and after PR #3282).
`roster.py:44`'s `_PROC_AVAILABLE = os.path.isdir("/proc")` has the
identical blind spot, masked the same way by a second matching line in
the same file (confirmed via the `/proc` grep sweep cited in Section 1's
opening table). A new file whose only `/proc` dependency was the
`os.path.isdir("/proc")` idiom — which this PR itself just wrote — would
pass `check_py_file()` with zero violations and never reach
`KNOWN_PROC_SITES` review.

### 2. The allowlist as a mechanism

`KNOWN_PROC_SITES` is a closed enumeration.

canonical: `on-the-record/checks/macos_bash32_compat.py:65` (post-PR,
`/tmp/pr3282-check`) — `KNOWN_PROC_SITES = {"roster.py", "watchdog.py",
"amendment_channel.py"}`.

The property the issue actually wants enforced is: every live `/proc`
read must be preceded, on some reachable path, by a runtime-visible
degradation notice for the platform-absent case. That property is not
mechanically decidable by a static, dependency-free, regex-over-text
scan (the check's own module docstring states this design constraint —
"purely static, dependency-free... cheap enough to run on every `pytest`
invocation"). Verifying it needs control-flow analysis to determine
whether a guard reaches the read, *and* whether the guard's
non-availability branch performs an observable side effect versus a
silent `return None` — the second question is a semantic judgment (is
this notice loud enough), not a syntactic pattern. A rule trying to
encode "flag any `/proc` site with no `sys.stderr.write` within N lines"
would false-positive against this PR's own fix (the notice is routed
through the shared `_report_write_result()` helper, not textually
adjacent to the `/proc` read — `gh pr diff 3282`, `_report_write_result`
hunk) and false-negative against a textually-adjacent but unreachable
`sys.stderr.write`. Given that, the enumeration is close to the right
shape for the property being enforced — but only because the allowlist
functions as a human-review gate, not as the coverage mechanism itself.
The real gap, demonstrated concretely in Section 1's `os.path.isdir("/proc")`
finding, is that a file already in `KNOWN_PROC_SITES` (or with one
matching + one non-matching `/proc` line) can add a new `/proc`-reading
line that is never itself seen by `check_py_file()`.

**On the two grandfathered entries.** `roster.py` and `watchdog.py` are
allowlisted by comment reference to a prior audit,
`docs/issue-2924/reports/silent-failure-audit+refactoring-legacy-seam-selection-140f0858.md`
(path confirmed to exist: `git ls-files docs/issue-2924/reports/` lists
this file), not by a mechanically re-checked bar.

canonical: `roster.py:47-61` (`_note_proc_identity_degraded()`, read
directly this session) prints a once-per-process stderr line when `/proc`
identity checks degrade; `watchdog.py:1860-1889`
(`_acquire_single_instance_lock()`, read directly this session) embeds a
degradation clause in the message its caller prints on the failure path.
Both grandfathered entries do carry genuine runtime-visible notices in
practice, so the grandfathering is substantively earned — but the check
has no mechanism that would catch a future edit quietly removing that
notice while leaving the file in `KNOWN_PROC_SITES`; only
`amendment_channel.py`, added by this PR, was held to a live bar (a
session/reviewer actually reading the diff), and that bar is the
non-mechanizable judgment call described above — this repo's own
standing lesson about lists losing to the next omission
(`docs/handbooks/observer-verification.md`, read directly this session:
`gates/merge_gate.py`'s `required_verification_missing()` deliberately
replaced a closed `kind:` vocabulary with a self-declared counted field
for the analogous reason, issue #2609) applies to `KNOWN_PROC_SITES`
itself, not just to the allowlist's contents.

### 3. False confidence

What a green result establishes: none of the nine syntactic rule shapes
in Section 1 are present in the current live population, and no live
`.py` file has an un-reviewed literal `/proc/`-with-slash reference.
Nothing more — no code in this check ever runs on macOS or under bash
3.2, and no execution of any guarded code path happens.

derived: `python3 on-the-record/checks/macos_bash32_compat.py --verbose`
in this session's own pre-fix worktree — result:
```
[macos-bash32-compat] population: 62 live .sh, 177 live .py (git ls-files '*.sh' '*.py' minus docs/ and test/tests paths)
[macos-bash32-compat] /proc dependency sites: 4 occurrence(s) in 3 file(s): on-the-record/hooks/amendment_channel.py, roster.py, watchdog.py
[macos-bash32-compat] FAIL -- 3 violation(s):
  scripts/issue-3041/run_pair.sh:96: "${arr[@]}" expanded under set -u/-o nounset without the ${arr[@]+"${arr[@]}"} bash-3.2-safe guard -- an empty/unset array is unbound under bash 3.2 (issue #2919 shape)
  scripts/issue-3041/run_pair.sh:109: "${arr[@]}" expanded under set -u/-o nounset without the ${arr[@]+"${arr[@]}"} bash-3.2-safe guard -- an empty/unset array is unbound under bash 3.2 (issue #2919 shape)
  on-the-record/hooks/amendment_channel.py: new /proc dependency outside the reviewed set ['roster.py', 'watchdog.py'] -- must be made portable or given a runtime-visible degradation notice, then added to KNOWN_PROC_SITES
```

derived: `python3 on-the-record/checks/macos_bash32_compat.py --verbose`
in `/tmp/pr3282-check` (PR #3282's head) — result:
```
[macos-bash32-compat] population: 62 live .sh, 177 live .py (git ls-files '*.sh' '*.py' minus docs/ and test/tests paths)
[macos-bash32-compat] /proc dependency sites: 4 occurrence(s) in 3 file(s): on-the-record/hooks/amendment_channel.py, roster.py, watchdog.py
[macos-bash32-compat] PASS
```
The bare word `PASS` (and pytest's own `4 passed` on top of it) carries
zero scope qualification, visible only in the two runs quoted directly
above — nothing distinguishes this from any other green check to a
reader who never opens the source. The necessary-not-sufficient caveat
exists in exactly two places: the module's Python-source docstring
(`macos_bash32_compat.py:1-41`, never printed at runtime) and prose the
issue author and PR author each wrote by hand this round (issue #3281's
closing paragraph; PR #3282's description). Nothing enforces that the
caveat travels with the check going forward — a future reader who sees
only `pytest -q` pass, or only `PASS` on stderr, gets the full,
unqualified "macOS support: yes" impression issue #3281 explicitly warns
against ("Do not let a green check read as 'macOS works'" — `gh issue
view 3281`, quoted verbatim in this session's own fetch).

### 4. Re-deriving the numbers

The task brief states "The PR reports 88 passed and a specific failure
count on main."

derived: `gh pr view 3282 --repo tokenmaxxxer/on-the-record --json
body,comments` piped through `grep -n "88\|passed\|failure"` — result:
zero "88" hits; the only pass/fail lines present are `4 passed` (compat
check) and `1652 passed, 1 pre-existing failure ..., 3 xfailed` (full
suite), both in the PR body's own Test-plan section.

Independently reproduced, not cited, in two throwaway worktrees:

acceptance: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -q`
at PR #3282's head (`/tmp/pr3282-check`, commit b5a83907) — result:
```
....                                                                     [100%]
4 passed in 0.87s
```

acceptance: `python3 -m pytest -q` at PR #3282's head — result:
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
1 failed, 1652 passed, 3 xfailed, 2 warnings in 46.13s
```

acceptance: `python3 -m pytest -q` at `origin/main` (`/tmp/main-check`,
commit 7d857d5f) — result:
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
2 failed, 1650 passed, 3 xfailed, 2 warnings in 54.81s
```

Both PR-reported numbers reproduce exactly: `4 passed` on the compat
check, and the full suite has exactly one failure on the PR branch
(`test_first_contact_fires_once_per_workspace`, present identically on
`main`) versus two on `main` (that same pre-existing failure plus the
compat check's own `test_current_head_is_clean` — precisely the red this
issue was filed about). "No new failures relative to main" is
independently confirmed; 1650→1652 passed matches the PR's account of
one new `/proc`-notice test plus the compat check's own test flipping
from fail to pass. "88 passed" corresponds to nothing found in PR #3282
by this session's own `gh pr view --json body,comments` fetch above —
whoever wrote the task brief was not quoting the PR.

## Why

The task's four questions map onto this project's own standing concern:
a green check is not the same claim as "the platform it checks for
works," and a check built from an enumerated allowlist is a known
failure shape here specifically (Section 2's `docs/handbooks/observer-verification.md`
citation). Verifying the check mechanism itself, rather than re-verifying
the fix's three named sites (already covered by the fix author's own
record plus this session's independent pytest reproduction in Section 4),
is the angle this session was assigned; a sibling verification, per the
spawning prompt, covers a different angle and was not read or coordinated
with.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 3281 --repo tokenmaxxxer/on-the-record`
(this session's own fetch) — names the three sites, the two must-nots,
and the "necessary, nowhere near sufficient" caveat quoted in Section 3.

canonical: `gh pr view 3282` / `gh pr diff 3282` (this session's own
fetch), head `b5a83907cdcb3000d472f3ed6e269b2d85ce44b9` — the deliverable
under review; the diff quoted across Sections 1-2 above is this fetch.

canonical: `on-the-record/checks/macos_bash32_compat.py`, read directly
in this session's own pre-fix worktree and in `/tmp/pr3282-check`; the
file is unmodified by PR #3282 except the `KNOWN_PROC_SITES` literal and
its adjacent comment (Section 2).

## Open findings

1. **`timeout` (GNU coreutils) is a live, uncaught macOS-breaking
   construct.** 3 live sites — derived: the `grep -nE '(^|[^A-Za-z0-9_./-])timeout[[:space:]]+[0-9]'`
   sweep quoted in Section 1, three matching lines — 2 in the exact file
   this PR edited (`scripts/issue-3041/run_pair.sh:96,109`), 1 in
   `on-the-record/hooks/stop-poll-rearm.sh:129`, untouched by the fix.
   No rule in `check_sh_file()` covers it (Section 1's nine-rule-shape
   enumeration). Resolution path: out of this session's scope
   (verification only); flag for a future rule addition to
   `_GNU_ONLY_BARE`.
2. **`_PROC_RE` does not match a quoted `/proc` literal without a
   trailing slash** (`os.path.isdir("/proc")`) — derived:
   `python3 /tmp/test_proc_regex.py`, Section 1, `False` on that exact
   sample. A real, currently-silent blind spot that PR #3282's own new
   line at `amendment_channel.py:482` sits inside, saved from being an
   actual miss only because the same file also contains a
   differently-shaped, matching `/proc` reference (Section 1). A new
   file whose only `/proc` dependency used this idiom would never be
   flagged. Resolution path: out of this session's scope; widen
   `_PROC_RE` to also match a bare `["']/proc["']` with no required
   trailing slash.
3. **The check's own runtime output gives no scope caveat.** derived:
   Section 3's two `--verbose` runs — the PR-branch output is the single
   line `[macos-bash32-compat] PASS`, no qualifying text. The
   necessary-not-sufficient caveat lives only in the Python docstring and
   in this round's hand-written prose (issue + PR descriptions), not in
   anything the check itself prints (Section 3). Resolution path: out of
   this session's scope; a one-line addition to the `PASS` message (e.g.
   "static scan only — no macOS/bash-3.2 execution performed") would
   close this without touching check logic.
4. **Test-depth-audit of `test_macos_bash32_compat.py`.**

   derived: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py --collect-only -q`
   — result:
   ```
   on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
   on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_decision_queue_stopgate_stat_c_fallback_is_recognized_safe
   on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_new_proc_site_outside_reviewed_set_is_flagged
   on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_would_have_caught_issue_2919_regressions

   4 tests collected in 0.01s
   ```
   matching Section 4's `4 passed`. Classification (source:
   `on-the-record/checks/test_macos_bash32_compat.py`, read directly this
   session):

   | Test | Class | Assertion cited |
   |---|---|---|
   | `test_current_head_is_clean` | GA | `assertTrue(ok, report)` on the real check's live-population result |
   | `test_would_have_caught_issue_2919_regressions` | GA | `assertTrue(any("flock"...))`, `assertTrue(any("[@]"...))` on pre-#2919 content, `assertEqual(head_violations, [])` on current content |
   | `test_decision_queue_stopgate_stat_c_fallback_is_recognized_safe` | GA | `assertEqual([v for v in violations if "stat -c" in v], [])` |
   | `test_new_proc_site_outside_reviewed_set_is_flagged` | GA | `assertEqual(len(violations), 1)` |

   Verification density = 4 GA / 4 total = 100% (all four rows above are
   GA; no EO/MD/Dead rows exist in the table). But the suite is
   Happy-Path-Only against the check's own blind spots found in this
   record: no test exercises any of the four `_GNU_ONLY_BARE` patterns;
   `flock` detection has no standalone unit test (only the historical
   git-history regression test, pinned to sha `29d00cb5...`, exercises
   it); `test_new_proc_site_outside_reviewed_set_is_flagged` only
   exercises the regex's true-positive case
   (`Path(f"/proc/{pid}/cmdline")`) — nothing in the suite tests finding
   2's false-negative case (`os.path.isdir("/proc")` going undetected).
   Resolution path: out of this session's scope; a test asserting
   `check.check_py_file(..., 'os.path.isdir("/proc")')` returns `[]`
   would document finding 2 as a known gap rather than leave it silent.
5. No other open findings.

## Next steps

None — terminal. Findings 1-4 are handoffs for a future session with
edit authorization; this record does not open one.

## Skill verdicts

skill-verdict: test-depth-audit — applied: invoked; classified all 4
tests in `on-the-record/checks/test_macos_bash32_compat.py` — table and
`4 GA / 4 total` derivation in Open finding 4 above (collect-only pytest
run cited there).

skill-verdict: silent-failure-audit — not-applicable:
`on-the-record/checks/macos_bash32_compat.py` has zero `try`/`except`
sites (`subprocess.run(..., check=True)` propagates loudly on failure).
`read_text(..., errors="replace")` silently substitutes invalid UTF-8
rather than erroring, so this session checked whether it currently
matters — derived: a per-file `.decode("utf-8")` sweep of the same 62
live `.sh` + 177 live `.py` files listed in Section 1 (`/tmp/live_sh.txt`,
`/tmp/live_py.txt`) — result: zero `UnicodeDecodeError` hits, so this is
a latent-only risk with no live error-handling chain to trace forward
today. The substantive audit questions this session needed (does the
check's own logic have blind spots) are covered under Sections 1-2
instead, using the coverage-audit method rather than the
error-absorption-tracing method this skill provides.

skill-verdict: adversarial-review — not-applicable: matched by the
post-dispatch skill_judge amendment channel, but `Skill({skill:
"adversarial-review"})` returned `Unknown skill` this session — not
mounted despite being judged a candidate. This session's task setup
already supplies the adversarial-review structure directly (a
structurally-independent second-verifier session with no access to the
sibling verification's record, per the spawning prompt), so the gap has
no practical effect on this record's method.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
not-applicable: same unmount as above (`Unknown skill`). This session
independently re-derived every number in Section 4 rather than citing PR
#3282's Test-plan checkboxes, which is the substance the skill would have
required.

other mounted skills: not triggered — `work-in-english` (record and all
internal work already in English per project convention; no Korean
authored this session to translate away from).
