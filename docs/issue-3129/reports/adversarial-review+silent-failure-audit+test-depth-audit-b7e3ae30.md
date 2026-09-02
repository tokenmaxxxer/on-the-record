---
issue: 3129
role: adversarial-review+silent-failure-audit+test-depth-audit-b7e3ae30
author: adversarial-review+silent-failure-audit+test-depth-audit-b7e3ae30
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's round-6 tip (fc8e23aa..6d604d90)
code_under_review: 6d604d905b614e4aec2a6d1e4460cb9645405735
loop_state: landed
type: defect-verification-record
breaking: false
verdict: PR #3137 round 6 (commit 6d604d90, verified in a dedicated worktree
  at /tmp/pr3137, untracked here) is INCORRECT on the headline claim it
  inherited from round 5 -- the positive success check
  (`_issue_url_from_response`'s `fullmatch`, untracked here) never matches a
  real Claude Code `Bash` `tool_response` (a structured object, not a bare
  string, per a live capture this session made -- see finding 2), so the
  amendment channel never records a marker for a real, successful `gh issue
  edit --body` call. Reproduced end-to-end against the production
  entrypoint. All 79 amendment-channel unit tests and both required gate
  probes pass anyway because every fixture in the suite constructs
  `tool_response` as a bare string -- a suite-wide blind spot the acceptance
  checks do not catch. The trust root (`registered_repo_for_pid`, untracked
  here) is Present and correctly fail-closed against every named attack.
  Round 6's restoration of `amends-landing-apply.sh` in `hooks.json`
  (untracked here) is Present as a fix but Incorrect as a diagnosis -- round
  5's first commit never touches `hooks.json` at all. The 333-vs-392/403
  suite-count gap is Present/accounted-for by branch staleness against
  `origin/main`, not a shrinking suite.
upstream:
  - path: PR #3137 (tokenmaxxxer/on-the-record), branch
      issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019,
      round-6 tip (untracked here; verified in worktree /tmp/pr3137)
    sha: 6d604d905b614e4aec2a6d1e4460cb9645405735
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9.md
      (PR #3191, round-4 verification, merged to main; present in this
      checkout)
    sha: 6234c49f0db648810666d246b0d9ab657a38a288
---

# issue-3129 — adversarial-review+silent-failure-audit+test-depth-audit-b7e3ae30 record

## What was done

canonical: `gh pr view 3137 --json headRefName,baseRefName,headRefOid` —
result: `{"headRefName":"issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019","baseRefName":"main","headRefOid":"6d604d905b614e4aec2a6d1e4460cb9645405735"}`.
Read first per the spawning prompt: PR #3191's round-4 verification
(`docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9.md`,
present in this checkout, merged as `6234c49f`), the round-5 record
(orphan commit `684a703a`, read via `git show 684a703a:docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-7c68ce58.md`,
not present in this checkout's working tree), and the round-6 record (read
via `git show 6d604d90:docs/issue-3129/reports/implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1.md`
in worktree `/tmp/pr3137`, untracked here). derived: `git worktree add /tmp/pr3137 origin/issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`
— result: `HEAD의 현재 위치는 6d604d90` — never merged or edited, per this
round's instructions.

### 1. The trust root (`registered_repo_for_pid`, replacing `cwd`) — Present

canonical: `on-the-record/hooks/amendment_channel.py:405-464` (untracked
here, PR #3137's branch, `/tmp/pr3137`), `registered_repo_for_pid()` —
walks this process's own `/proc` ancestry to a pid registered in
`spawn.py`'s roster (`runs/active.json`), pairing `start_time` against pid
reuse, never reading any `PostToolUse` payload field.

acceptance: `python3 attack2.py` (six attack scenarios, run this turn
against `/tmp/attack3129/attack2.py`, driving
`record_amendment_from_response()`, the real write-path entrypoint,
directly) — result:
```
### Scenario: registration ABSENT (no roster file at all) ###
NoRegisteredRepo()
### Scenario: registration file PRESENT BUT EMPTY ({}) ###
NoRegisteredRepo()
### Scenario: registration file MALFORMED (invalid JSON) ###
NoRegisteredRepo()
### Scenario: registration file present but a JSON ARRAY, not dict ###
NoRegisteredRepo()
### Scenario: real registration for REPO_A, cd elsewhere (REPO_B), edit response for REPO_A -- should still resolve via pid, ignore cwd ###
AmendmentWritten(repo='orgA/repoA', issue='42', version=1)
### Scenario: cd-steered cwd, but response claims REPO_B (the cd target) instead of registered REPO_A -- must be refused as RepoMismatch, not silently accepted via cwd ###
RepoMismatch(registered_repo='orgA/repoA', url_repo='orgB/repoB', issue='7')
### Scenario: point the lookup at a DIFFERENT session's registration (pid mismatch: registered pid is NOT this pid) ###
NoRegisteredRepo()
```
This is Present for every attack the task named against the *lookup*
mechanism itself: an absent, empty, malformed, or non-dict roster is
`NoRegisteredRepo` (never a fallback to `cwd`); a `cd` to a second real
checkout does not move attribution off the registered repo; a
registration keyed to a pid that is not this process's own ancestry is
invisible, not misattributed.

Caveat found, not evaluated by round 5 or round 6: derived:
`grep -rln "active\.json\|runs/active\|ROSTER" on-the-record/hooks/*.sh on-the-record/hooks/*.py`
(excluding `amendment_channel.py`, untracked here, PR #3137's branch, and
its own tests), run in `/tmp/pr3137` — empty result, i.e. no `PreToolUse`
gate in this repository protects `runs/active.json`'s own write-integrity.
`registered_repo_for_pid()`'s own docstring (`on-the-record/hooks/amendment_channel.py:422-428`,
untracked here, PR #3137's branch) claims this trust root is never a value
"the session could influence" — true of the kernel-tracked `/proc`
ancestry walk itself, but the roster *file's* `work` field is ordinary
file content this codebase does not independently protect. derived:
manual write to the roster file (`attack1.py` in `/tmp/attack3129`, this
turn) confirmed `registered_repo_for_pid()` simply reads through to
whatever the file currently contains — expected given the design's own
"no caching" choice, but it means the trust root's real-world strength
depends entirely on whether the roster file's actual production path is
reachable from a spawned session's own tool calls. unverifiable: this
review's sandbox has no access to a live `spawn.py` orchestrator process
or the real shared plugin install's filesystem permissions, so whether a
spawned session can reach the real roster path is not testable from here —
only the code-level behavior (the lookup trusts whatever the file says,
with no independent integrity check inside `amendment_channel.py` itself,
untracked here, PR #3137's branch) was reproducible.

### 2. The positive success check (`fullmatch` on `tool_response`) — Incorrect, severe

canonical: `on-the-record/hooks/amendment_channel.py:711-718` (untracked
here, PR #3137's branch), `_issue_url_from_response()`:
```python
    text = hook_input.tool_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.fullmatch(text.strip())
    if not m:
        return None
```
canonical: `on-the-record/hooks/hook_input.py:162-186` (untracked here, PR
#3137's branch, unmodified by this PR), `tool_response_text()` — returns
`raw` unchanged when it is already a string, else `json.dumps(raw)`; its
own docstring says `tool_response` is "usually the tool's own stdout as a
plain string" (line 167).

derived: captured a REAL `PostToolUse`/`Bash` payload this turn, not
synthesized. Built an isolated project at `/tmp/hookprobe` with its own
`.claude/settings.json` registering a `PostToolUse` hook (matcher `Bash`)
that dumps raw stdin to a file, then ran
`claude -p "Run the shell command: echo hello-world-probe" --dangerously-skip-permissions`
in that directory — result, `/tmp/hookprobe/captured_2053503_1788368871911957007.json`,
`python3 -m json.tool` output:
```json
"tool_response": {
    "stdout": "hello-world-probe",
    "stderr": "",
    "interrupted": false,
    "isImage": false,
    "noOutputExpected": false
}
```
`tool_response` for `Bash` is a structured object, not a bare string —
`tool_response_text()` therefore takes its `json.dumps(raw)` branch for
every real `Bash` call.

derived: reproduced the consequence this turn against
`record_amendment_from_response()` directly, using that exact captured
shape (only the `stdout` value substituted for a `gh issue edit` success
URL) — result:
```
Result against REAL Claude Code tool_response shape: NoIssueUrlInResponse(registered_repo='orgA/repoA')
```
derived: reproduced end-to-end this turn against the PRODUCTION entrypoint
itself (`on-the-record/hooks/amendment_channel.py`, untracked here, PR
#3137's branch, read from stdin — canonical:
`on-the-record/hooks/amendment-channel.sh:22`, untracked here, PR #3137's
branch, `python3 "$DIR/amendment_channel.py"`, the same invocation the
shipped hook wrapper uses), with a real roster registration for the
calling pid and a real git checkout with `origin` set to the target repo —
result:
```
$ echo '{"cwd":"/tmp/attack3129/e2e/repoA","tool_name":"Bash","tool_input":{"command":"gh issue edit 42 --body newbody"},"tool_response":{"stdout":"https://github.com/orgA/repoA/issues/42","stderr":"","interrupted":false,"isImage":false,"noOutputExpected":false}}' | OTR_ROSTER_PATH=/tmp/attack3129/e2e/roster.json OTR_AMENDMENT_STATE_DIR=/tmp/attack3129/e2e/state python3 /tmp/pr3137/on-the-record/hooks/amendment_channel.py
amendment-channel: gh issue edit ran but its tool_response carries no parseable https://github.com/<owner>/<repo>/issues/<n> URL (the call may have failed, or gh's output shape changed) -- no marker written; this session's own registered repo is orgA/repoA
exit=1
```
derived: `find /tmp/attack3129/e2e/state -type f` — no output; no marker
file was written. A genuinely successful `gh issue edit --body` call, run
by a correctly-registered session, is refused as if it had failed. This is
not one of the four edge shapes the spawning task named (trailing newline,
leading whitespace, ANSI codes, a warning line) — it is the unconditional,
only shape a real Bash `PostToolUse` hook ever produces.

derived: `grep -n "tool_response" tests/test_amendment_channel.py`
(untracked here, PR #3137's branch), run in `/tmp/pr3137` — every call
site constructs `tool_response` as a bare string. canonical:
`gates/probe_running_session_sees_amendment.py:192` (untracked here, PR
#3137's branch): `"tool_response": "https://github.com/%s/issues/%s" % (repo_slug, ISSUE)`
— the same bare-string shortcut, in the one probe the issue itself names
as the acceptance test for "a running session sees the amendment." This is
why neither `tests/test_amendment_channel.py` (untracked here, PR #3137's
branch) nor `gates/probe_running_session_sees_amendment.py` (untracked
here, PR #3137's branch) catches finding 2 — see "Acceptance checks" below
for their own re-run results.

Root cause isolated this turn: round 4 (commit `28e8e63f`, canonical: not
part of this round's own diff, `git log --oneline HEAD -- on-the-record/hooks/amendment_channel.py`
in `/tmp/pr3137` names it) used `.search()`, which — derived, run this
turn — DOES find the URL inside the json-dumped wrapper, because
`json.dumps` does not escape `/`:
```python
>>> import json, re
>>> text = json.dumps({"stdout": "https://github.com/orgA/repoA/issues/42", "stderr": ""})
>>> re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b").search(text)
<re.Match object; span=(12, 51), match='https://github.com/orgA/repoA/issues/42'>
>>> re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b").fullmatch(text.strip())
None
```
Round 5's switch from `.search()` to `.fullmatch()` (commit `7fa8906b`,
canonical: `git show 7fa8906b:on-the-record/hooks/amendment_channel.py`,
untracked here, PR #3137's branch, diff against its parent) is what breaks
the success path, applied to the whole `tool_response_text()`-coerced blob
rather than to the tool's own `stdout` field extracted first. canonical:
`on-the-record/hooks/amendment_channel.py:118-120` (untracked here, PR
#3137's branch) — the module's own docstring explicitly names the
"string-or-json-dumps coercion," so this consequence was a knowable risk
the design did not test for. derived: neither
`tests/test_amendment_channel.py` (untracked here, PR #3137's branch) nor
either gate probe (both grepped above) contains a dict-shaped
`tool_response` fixture anywhere.

Consequence beyond count 2's own scope: since `parsed` is `None` for every
real call, `RepoMismatch` (round 4's cross-repo "POLICY VIOLATION" check,
canonical: `on-the-record/hooks/amendment_channel.py:818-819`, untracked
here, PR #3137's branch) also never fires against real traffic — a genuine
cross-repo edit from a real session would be silently treated the same as
"no URL," not flagged as a violation.

### 3. The restored hook (`amends-landing-apply.sh` in `hooks.json`) — Present as fix, Incorrect as diagnosis

canonical: round-6 record, read via `git show 6d604d90:docs/issue-3129/reports/implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1.md`
in `/tmp/pr3137`, lines 45-65 — claims round 5's first commit (`7fa8906b`)
"deleted the pre-existing `PostToolUse` entry for
`amends-landing-apply.sh`... an accidental deletion during that edit."

derived: `git show 7fa8906b -- on-the-record/hooks/hooks.json`, run in
`/tmp/pr3137` — empty output; this commit does not touch `hooks.json`
(untracked here, PR #3137's branch) at all. derived:
`git log --oneline HEAD -- on-the-record/hooks/hooks.json`, run in
`/tmp/pr3137` — only two commits on this branch ever touch that file:
`61065ede` ("wire the hook into hooks.json/classification") and `fc8e23aa`
(round 6's restore). derived: `git show 61065ede -- on-the-record/hooks/hooks.json`
— an additive-only diff (adds `amendment-channel.sh`'s own entry), no
removal of `amends-landing-apply.sh` anywhere in that diff. derived:
`git show 820e9dc5:on-the-record/hooks/hooks.json | grep amends-landing-apply`
(`820e9dc5` = this branch's merge-base with `origin/main`, from
`git merge-base HEAD origin/main` run in `/tmp/pr3137`) — empty: the entry
did not exist at the branch's own fork point either.

The entry was never present on this branch's own history before round 6
added it. canonical: `tests/test_spawn_gate_wiring.py:115-148` (tracked in
this checkout, unmodified by PR #3137 — derived:
`git log -1 --format=%H -- tests/test_spawn_gate_wiring.py` in
`/tmp/pr3137` gives `7ee16612`, an issue-#3083 commit predating this
branch's fork) — `test_pre_existing_post_tool_use_commands_are_all_still_present`
diffs the live `hooks.json` against `origin/main`, a moving target it
re-fetches at test-run time, not this branch's own merge-base or history.
derived: `diff /tmp/otr-mergebase/on-the-record/hooks/hooks.json /tmp/otr-main-e73f/on-the-record/hooks/hooks.json`
(merge-base worktree at `820e9dc5` vs. a worktree of current `origin/main`,
both built this turn) — shows exactly this one addition, nothing else, in
the `PostToolUse` block, confirming `amends-landing-apply.sh` was added to
`main` (issue #3134, unrelated to this PR) after this branch diverged. So
the test began failing on this branch purely because `origin/main` moved
past it.

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -q`
(untracked here, PR #3137's branch, run this turn in `/tmp/pr3137`) —
result:
```
no failures (folded into the 333-passed run cited under "Acceptance checks" below)
```
Round 6's fix (adding the entry) fixes the symptom correctly, but round
6's own causal narrative naming `7fa8906b` as the deleting commit is
Incorrect against the executable evidence above.

### 4. The suite-count gap (333 on the branch vs. main) — Present, accounted for

derived: `git merge-base HEAD origin/main`, run in `/tmp/pr3137` —
`820e9dc5`. derived: `git log --oneline 820e9dc5..origin/main | wc -l` —
result: `58`. derived: `git log --oneline 820e9dc5..HEAD | wc -l` — result:
`24`. Main gained 58 commits unrelated to this PR since the branch forked;
the branch added 24 of its own. derived: `python3 -m pytest tests/ -q` run
this turn at the merge-base (worktree `/tmp/otr-mergebase`, checked out at
`820e9dc5`) — result: `1 failed, 253 passed` (254 total; the 1 failure is
the same `HooksJsonWiringIsAdditive` staleness test, already failing at
the fork point for the same live-diff reason). derived:
`diff <(cd /tmp/otr-mergebase && git ls-files tests/ | sort) <(cd /tmp/otr-main-e73f && git ls-files tests/ | sort) | grep '^>' | wc -l`
run this turn — result: `12` new test files added to `main` since the fork
point; the reverse diff (files removed on the branch relative to the
merge-base) is empty, confirmed by the same command with `<` in place of
`>` producing no output. `254` (branch's own baseline at the merge-base,
including its 1 pre-existing failure) plus `79` (`tests/test_amendment_channel.py`,
untracked here, PR #3137's branch, new on this branch) equals `333`,
matching the branch tip's own count exactly (see "Acceptance checks"
below, check 4). The gap to main's current count is accounted for entirely
by those 58 unrelated upstream commits / 12 new test files, not by
anything missing, renamed, or skipped on this branch.

### 5. Re-confirmed properties from earlier rounds

Command text never read for attribution: canonical:
`on-the-record/hooks/amendment_channel.py:462-466` (untracked here, PR
#3137's branch) — `_gh_issue_edit_body_call()` is used only as a shape
gate; the repo/issue values come from `registered_repo_for_pid()` and
`_issue_url_from_response()`, neither of which reads `command`. Present.

acceptance: `python3 -m pytest tests/test_amendment_channel.py::PreviouslyBrokenShapesAreNowIrrelevant -v`
(untracked here, PR #3137's branch, run this turn in `/tmp/pr3137`) —
result:
```
6 passed
```
PR #3170's five shapes still resolve at the detection layer; whether an
edit through one of these shapes actually writes a marker in production is
subject to the same finding-2 breakage as every other real call, since
detection and write-success are separate stages.

Every decline visible on stderr: canonical:
`on-the-record/hooks/amendment_channel.py:828-866` (untracked here, PR
#3137's branch), `_report_write_result()` — one distinct stderr line per
fail-closed variant; reproduced live in the finding-2 e2e run above
(stderr line present, exit 1) and in the six scenarios under finding 1.

acceptance: `python3 -m pytest tests/test_amendment_channel.py::RecordAmendmentFromResponse::test_failed_edit_error_text_containing_a_url_is_not_a_success -v`
(untracked here, PR #3137's branch, run this turn in `/tmp/pr3137`) —
result:
```
1 passed
```
A failed edit carrying a URL is refused, though now a narrower guarantee
than intended: under finding 2, no real `gh issue edit` call (success or
failure) ever produces a `fullmatch`, so this property no longer
distinguishes failed from successful edits in production.

## Acceptance checks

All four re-run this turn in `/tmp/pr3137` (PR #3137's own branch tip,
untracked here):

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` —
result:
```
79 passed in 1.06s
```
Mechanically green, but does not exercise the real `tool_response` shape
(finding 2 above).

acceptance: `python3 gates/probe_running_session_sees_amendment.py` —
result:
```
ok
exit 0
```
Mechanically green, but its own `orch_payload` uses a bare-string
`tool_response` (canonical:
`gates/probe_running_session_sees_amendment.py:192`, untracked here, PR
#3137's branch, cited above under finding 2).

acceptance: `python3 gates/probe_amendment_notice_fires_once.py` —
result:
```
ok
exit 0
```
Exercises the read-side notice path, unrelated to finding 2's write-side
breakage.

acceptance: `python3 -m pytest tests/ -q` — result:
```
333 passed, 2 warnings in 10.17s
```
Fully explained by branch staleness (finding 4 above), not by anything
missing on this branch.

canonical: the four `acceptance:` results directly above, all captured
this turn against `/tmp/pr3137`, are what this round's task required; none
of them constructs a real `tool_response`.

## Why

Per `adversarial-review`: this round's task named the trust root as the
highest-priority target ("the fourth attempt at it"), so it was attacked
first with the six scenarios under finding 1, including a check for
filesystem-level protection of the roster file itself (absent, and
unevaluated by any prior round per the empty grep cited there). The second
target (the positive success check) was attacked exactly as instructed —
the four named shapes were tried first, then, once that raised the
question of what a real `tool_response` actually looks like, this session
captured one live (`/tmp/hookprobe`, finding 2 above) rather than trusting
the module's own "usually...a plain string" docstring claim or the prior
rounds' citation of Claude Code's `cwd`-behavior docs as a stand-in for
`tool_response`'s own behavior.

Per `silent-failure-audit`: `NoIssueUrlInResponse` is not silent in the
narrow sense — canonical: the finding-2 e2e run above shows its one
stderr line firing correctly — but the system-level effect is a silent
failure of the feature: an orchestrator amending an issue has no reason to
think the correction was not recorded (the `gh issue edit` call itself
succeeds), and the one signal that would reveal the problem (this hook's
stderr line) lands in the spawned worker's own tool-call context, not the
orchestrator's. This is the shape silent-failure-audit exists to catch: a
fail-closed path that is individually correct but system-invisible because
nothing downstream reads that specific process's stderr.

Per `test-depth-audit`: canonical: `grep -n "tool_response" tests/test_amendment_channel.py`
(untracked here, PR #3137's branch, cited under finding 2) — every one of
the 79 tests' fixtures was checked for whether it used a realistic
`tool_response`; none do. Classified Happy-Path-Only at the suite level
for the one property (real-shape success) that determines whether the
feature works at all, despite Genuine Assertion coverage of every other
equivalence class the trust-root and detection-layer redesigns named. Both
required gate probes share the same gap (canonical:
`gates/probe_running_session_sees_amendment.py:192`, untracked here, PR
#3137's branch, cited under finding 2), which is why they did not catch
this regression despite being the acceptance criteria's own chosen
safeguard.

## What did not work

None. Every attack scenario planned was carried through to a concrete
result, including the live `claude -p` capture used to settle finding 2
definitively.

## Upstream basis

- canonical: PR #3191's round-4 verification
  (`docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9.md`,
  present in this checkout, merged `6234c49f`) — its Angle 2/3/5 verdicts,
  read via this checkout's own copy of the file, are the two Incorrect
  counts round 5 claims to repair.
- canonical: round-5 record, read via
  `git show 684a703a:docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-7c68ce58.md`
  (orphan commit, branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-7c68ce58`
  — derived: `git merge-base --is-ancestor 684a703a HEAD` (`HEAD` = PR
  #3137's own branch tip, run in `/tmp/pr3137`) returns non-zero, i.e. not
  an ancestor — this record is not reachable from PR #3137's branch, only
  its code commits `7fa8906b`/`9e42e12e`, same SHAs, are) — its account of
  the `cwd`→pid-ancestry swap and the `.search()`→`.fullmatch()` switch was
  independently re-derived against the code and a real payload in this
  record rather than taken on citation.
- canonical: round-6 record, read via
  `git show 6d604d90:docs/issue-3129/reports/implementation-blueprint+test-derivation+silent-failure-audit-15e1fab1.md`
  in `/tmp/pr3137` — its `hooks.json` diagnosis is independently re-derived
  and found Incorrect under finding 3 above.

## Open findings

1. **(Severe, blocking) The amendment channel does not record markers for
   real `gh issue edit --body` calls.** canonical: finding 2 above,
   including the live-captured payload and the production-entrypoint
   reproduction. Resolution path: `_issue_url_from_response()` needs to
   extract the tool's own `stdout` field from a structured `tool_response`
   before applying `fullmatch`, rather than fullmatching the whole
   `json.dumps`-coerced blob; the test suite and both gate probes need at
   least one case built from a real captured
   `{"stdout":...,"stderr":...,"interrupted":...,"isImage":...,"noOutputExpected":...}`
   shape. Not fixed in this round — this session's task was verification
   only, explicitly instructed not to edit PR #3137.

2. **The round-5 record is not part of PR #3137's own branch history.**
   canonical: the "Upstream basis" bullet above (`git merge-base --is-ancestor 684a703a HEAD`
   returns non-zero). Resolution path: none required for this issue's own
   acceptance (the code round 5 wrote is present and correct on the point
   it documents), but a future reader of PR #3137's branch alone would have
   no way to find round 5's own rationale.

3. **The roster file's own write-integrity has no gate in this codebase**
   (canonical: finding 1's grep above) — not proven exploitable from a
   spawned session's own tool calls (unverifiable: no access to the real
   shared plugin install's filesystem permissions from this review's
   sandbox), but also not evaluated or closed by canonical: any of rounds
   4-6's own records cited under "Upstream basis" above, each of which only
   compared "trust the roster" against "trust cwd."

## Next steps

None from this session for finding 4 (accounted for, no action needed) or
for the "re-confirmed" properties in finding 5 (already Present). Findings
1-3 remain open on PR #3137 and require a further repair round on that PR,
which this session was explicitly instructed not to perform — `loop_state: landed`
reflects this verification round itself being complete, not PR #3137 being
ready to land. Per this round's task, PR #3137 was not edited: derived:
`git -C /tmp/pr3137 status --short` — empty (no local changes in that
worktree), and not merged. This review's own worktrees (`/tmp/pr3137`,
`/tmp/otr-mergebase`, `/tmp/otr-main-e73f`) and sandboxes (`/tmp/attack3129`,
`/tmp/hookprobe`) are outside this repository and were not committed.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; structured this
session as a structurally independent attack against PR #3137's own
round-6 tip. canonical: findings 1-4 above, each independently re-derived
against the code, git history, and a live captured payload rather than
taken on the prior rounds' own citation.

skill-verdict: silent-failure-audit — applied: invoked; classified
`NoIssueUrlInResponse`'s individually-correct fail-closed behavior against
its system-level effect. canonical: the "Why" section's silent-failure-audit
paragraph above, and the finding-2 e2e reproduction confirming the stderr
line still fires under the real payload shape.

skill-verdict: test-depth-audit — applied: invoked; classified the
79-test suite and both gate probes by reading their own fixture
construction. canonical: `grep -n "tool_response" tests/test_amendment_channel.py`
(untracked here, PR #3137's branch) and
`gates/probe_running_session_sees_amendment.py:192` (untracked here, PR
#3137's branch), both cited under finding 2 — Happy-Path-Only for the one
property that determines whether the feature works at all, Genuine
Assertion for every other equivalence class.

skill-verdict: work-in-english — applied: invoked; this record, all
commands, and code citations are in English; only this session's final
user-facing summary is in Korean per policy.

other mounted skills: not triggered.
