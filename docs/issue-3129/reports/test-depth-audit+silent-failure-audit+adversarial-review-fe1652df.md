---
issue: 3129
role: test-depth-audit+silent-failure-audit+adversarial-review-fe1652df
author: test-depth-audit+silent-failure-audit+adversarial-review-fe1652df
skills: test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3137's own deliverable against issue #3129
loop_state: landed
code_under_review: a0abb72dc132d723bae499503a396d8e79af81cd
type: defect-verification-record
breaking: false
verdict: 4 of 4 acceptance checks Present — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` (untracked path, from PR worktree) — result: 35 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` (untracked path) — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` (untracked path) — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 289 passed, 0 failed.
  3 of 3 must-nots Present (no gh polling on the hot path, notice is advisory-only never a permissionDecision, no kill-respawn dependency).
  Writer-automaticity Present: the marker write is not a step the orchestrator must remember — the same unmatched PostToolUse hook that surfaces notices also auto-detects `gh issue edit <n> ... --body...` in ANY session's own Bash calls and bumps the marker as a side effect.
  Hook classification wiring Present — acceptance: `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q` (untracked path, from PR worktree) — result: 6 passed.
  Same-repo cross-issue isolation Present.
  Notice content Present with a caveat (silent truncation past 2000 chars).
  Cross-platform mtime-independence Present by design (code inspection: zero mtime reads); macOS execution itself Unverifiable (no macOS host in this session).
  test/ 15 pre-existing failures Present as pre-existing and unrelated to this PR — derived: re-ran `python3 -m pytest test/ -q` at the PR's own merge-base commit 820e9dc5 — result: same 15 failed, 548 passed, 3 xfailed; derived: re-ran on current main 02c3c8cb — result: 563 passed, 3 xfailed, 0 failed (commit 73b614fd fixed them after this PR's base).
  One confirmed INCORRECT finding: the amendment marker is keyed by issue number ALONE, no repo/org component anywhere in `default_state_dir()`/`marker_path()` (a0abb72d:on-the-record/hooks/amendment_channel.py:76-94), so a worker session in one repo whose branch happens to be `issue-<n>/...` receives amendment notices actually written for a different repo's same-numbered issue — reproduced end-to-end below. Untested in the 35-case suite: every existing per-issue isolation test varies the issue number inside one shared repo/state_dir, never two repos with the same issue number.
upstream:
  - path: PR #3137 (branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019)
    sha: a0abb72dc132d723bae499503a396d8e79af81cd
---

# issue-3129 — test-depth-audit+silent-failure-audit+adversarial-review-fe1652df record

## What was done

Second independent, builder-blind verification of PR #3137 against issue
#3129, run in parallel with another verification session, emphasizing
the writer side and the wiring per the spawning prompt (the other
verification covers different ground).

canonical: `gh issue view 3129` output — the defect: a spawned session
reads its issue once at spawn and never again; cross-session messages to
it can never be approved (headless recipient, no user to approve);
amending the issue body reaches `check_runner`'s scoring but not the
running process. Acceptance checks named in the issue body: `tests/test_amendment_channel.py`
(untracked here — present only on PR #3137's branch),
`gates/probe_running_session_sees_amendment.py` (untracked here),
`gates/probe_amendment_notice_fires_once.py` (untracked here), and the
`tests/ -q` full suite. Must-nots: no `gh` polling from `PostToolUse`,
never a blocking gate, never rely on kill-and-respawn.

canonical: `gh pr view 3137` output — PR #3137 (branch
`issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`,
head `a0abb72d`) adds `a0abb72d:on-the-record/hooks/amendment_channel.py`
+ `a0abb72d:on-the-record/hooks/amendment-channel.sh` wired into
`PostToolUse` unmatched, keyed on an explicit content `version` field
(not raw mtime), plus `a0abb72d:tests/test_amendment_channel.py` (35
cases) and the two named probes.

derived: `git fetch origin pull/3137/head:pr-3137-review` then `git
worktree add /tmp/pr3137-review-b pr-3137-review` — result: worktree at
head `a0abb72d`. Every check below ran from that worktree
(`/tmp/pr3137-review-b`), never merged into or edited. The builder's own
record
(`a0abb72d:docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-a641f019.md`,
present only on PR #3137's branch, absent from this session's own
working tree) was read only after this session's own checks were
already run, per `defect-verification-independence-from-upstream-verdicts`
rule 1 — every number and claim below was independently re-derived, not
cited from that record.

### Writer-side automaticity (this verification's assigned emphasis)

derived: read `a0abb72d:on-the-record/hooks/amendment_channel.py:253-280`
(`maybe_write_from_command`) and `a0abb72d:on-the-record/hooks/hooks.json:74-89`
— the amendment-channel hook is registered in the **unmatched**
`PostToolUse` group (no `matcher` key, fires on every tool call, for
every session, orchestrator and worker alike, same `hooks.json` both
load). `run_hook` (lines 283-319) calls `maybe_write_from_command`
unconditionally on every invocation, which regex-detects `gh issue edit
<n> ... --body|--body-file ...` in the Bash command text and calls
`write_amendment` automatically — there is no separate command the
orchestrator must remember to run after editing an issue; the write is
a side effect of the orchestrator doing what it already does (`gh issue
edit ... --body`), not an added instruction whose execution is
optional. canonical:
`a0abb72d:tests/test_amendment_channel.py:330-339`
(`test_orchestrator_bash_call_in_this_same_run_hook_writes_the_marker`)
drives this through `run_hook` itself, not the lower-level function
directly. Present.

### Hook registration + classification wiring

derived: `grep -n "amendment" on-the-record/hooks/hook_classification.json`
(untracked path, run from `/tmp/pr3137-review-b`) — result: an entry at
lines 118-123 (`"script": "amendment-channel.sh"`, `"class":
"observability"`, rationale naming issue #3129) exists alongside the
`hooks.json` registration added in the same PR. acceptance: `python3 -m
pytest on-the-record/hooks/test_hook_classification.py -q` (untracked
path, run from `/tmp/pr3137-review-b`) — result:
```
6 passed in 0.92s
```
No #2872-shaped registration-without-classification gap. Present.

### Cross-issue / cross-repo attribution

canonical: `a0abb72d:tests/test_amendment_channel.py:160-166`
(`test_notices_are_per_issue_independently`) — confirms two DIFFERENT
issue numbers in the SAME repo/state_dir stay isolated. Present for
that dimension.

canonical: `a0abb72d:on-the-record/hooks/amendment_channel.py:76-94`
(`default_state_dir`, `marker_path`, `seen_path`) — `default_state_dir()`
returns `$OTR_AMENDMENT_STATE_DIR` or `$TMPDIR/otr-amendment` with no
repo/org component; `marker_path` is `issue-<n>.marker.json` keyed on
the issue number alone. Compared against sibling hooks
`a0abb72d:on-the-record/hooks/retry-loop-bound.sh` /
`a0abb72d:on-the-record/hooks/approach-cap-warning.sh`
(`OTR_RB_STATE_DIR`/`OTR_ACW_STATE_DIR`, both keyed by `session_id`,
which is globally unique) — those hooks don't have this problem because
they solve a different problem (a session's own state). This hook must
solve a genuinely cross-session, same-issue problem, so session_id
alone cannot be the key; but issue number alone is insufficient once
two different repos can share an issue number, and nothing here adds a
second key dimension for that.

derived: reproduced end-to-end via the shipped `run_hook` entrypoint
(not the isolated storage functions), script written to
`/tmp/cross_repo_repro2.py` (this session's own scratch file, not part
of either repo):
```python
import sys, json
sys.path.insert(0, "/tmp/pr3137-review-b/on-the-record/hooks")
import amendment_channel as ac

payload_a = json.dumps({
    "session_id": "orchestrator-session", "tool_name": "Bash",
    "tool_input": {"command": "gh issue edit 42 --body 'corrected brief'"},
    "cwd": "/tmp/cross-repo-test/repo-a",
})
print("repo-a orchestrator:", ac.run_hook(payload_a))

payload_b = json.dumps({
    "session_id": "worker-in-repo-b", "tool_name": "Read",
    "tool_input": {}, "cwd": "/tmp/cross-repo-test/repo-b",
})
print("repo-b worker:", ac.run_hook(payload_b))
```
run against two independently `git init`'d repos (`repo-a`, `repo-b`, no
shared history), both checked out on branch `issue-42/some-role`, no
`OTR_AMENDMENT_STATE_DIR` override (both resolve the same default shared
`/tmp/otr-amendment`) — result:
```
repo-a orchestrator: [amendment] issue #42 was amended by the orchestrator at 2026-09-02T10:10:31.336820+00:00 -- re-read it before continuing. This is advisory: decide whether the correction is right, do not halt on it. Note: corrected brief
repo-b worker: [amendment] issue #42 was amended by the orchestrator at 2026-09-02T10:10:31.336820+00:00 -- re-read it before continuing. This is advisory: decide whether the correction is right, do not halt on it. Note: corrected brief
```
A worker in `repo-b` — standing in for study-companion in the task's
own example, since the orchestrator works both repos — receives, on an
unrelated `Read` tool call, an amendment notice actually written by an
orchestrator editing a *different* repo's issue #42, note text (the
actual corrected content) included. **Incorrect.** This is exactly the
shape of #3081 and #3095 (attribution defects landed the same day, per
the task description) and it is not covered anywhere in the 35-case
test suite: derived: `grep -n "repo\|study-companion\|cross.repo" *.py`
run inside `tests/` (untracked path, from `/tmp/pr3137-review-b`) —
result: matches only inside `_make_issue_repo`'s own body, never two
repos constructed in the same test — nor in either probe.

### Notice content

canonical: `a0abb72d:on-the-record/hooks/amendment_channel.py:165-175`
(`format_notice`) and `a0abb72d:on-the-record/hooks/amendment_channel.py:206-228`
(`_extract_note`). The note is not a diff and not a bare "your issue
changed, re-read it" — it is the literal `--body`/`--body-file` value
(the new content itself, or the file's content) truncated to
`_NOTE_MAX = 2000` chars, embedded directly in the `additionalContext`
string. For a body under 2000 chars this is enough for a worker session
to act on without a `gh` call of its own, confirmed by canonical:
`a0abb72d:tests/test_amendment_channel.py:111-116` and 322-326 (both
assert the actual note text appears in the notice string, not just that
a notice fired). Beyond 2000 chars the note is silently truncated
(`note[:_NOTE_MAX]` at `write_amendment` line 141) with no indication
truncation occurred — a worker would see a partial correction with no
signal it's incomplete. Present for the common case; a lower-severity
gap for amendment notes over 2000 chars.

### Cross-platform (Linux/macOS mtime independence)

derived: grepped for `mtime`/`st_mtime`/`getmtime`/`platform` across
each of the module and its tests/probes individually, all run from
`/tmp/pr3137-review-b` (every path below untracked in this session's
own tree, present only on PR #3137's branch): `amendment_channel.py`
(untracked) — zero matches; `tests/test_amendment_channel.py`
(untracked) — zero matches; `gates/probe_running_session_sees_amendment.py`
(untracked) — zero matches; `gates/probe_amendment_notice_fires_once.py`
(untracked) — zero matches. The design uses an explicit content
`version` counter throughout instead, and both probes' own docstrings
state this deliberately. This eliminates the risk class by construction
rather than by testing around it. Present by design; this session ran
everything on Linux only, so macOS execution itself is Unverifiable
here — no macOS host available to this session.

### Acceptance checks (independently re-run from the PR worktree)

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q`
(untracked path, run from `/tmp/pr3137-review-b`) — result: `35 passed
in 0.93s`. Present.

acceptance: `python3 gates/probe_running_session_sees_amendment.py`
(untracked path, run from `/tmp/pr3137-review-b`) — result: `ok`, exit
0. Present.

acceptance: `python3 gates/probe_amendment_notice_fires_once.py`
(untracked path, run from `/tmp/pr3137-review-b`) — result: `ok`, exit
0. Present.

acceptance: `python3 -m pytest tests/ -q` (from `/tmp/pr3137-review-b`)
— result: `289 passed, 2 warnings in 10.45s`, 0 failed. Present,
matches PR's own stated claim.

acceptance: `python3 -m pytest test/ -q` (not an owned acceptance check
for this issue, run for completeness per the spawning prompt, from
`/tmp/pr3137-review-b`) — result:
```
15 failed, 548 passed, 3 xfailed in 31.95s
```
derived: re-ran the identical command at the PR's own merge-base commit
(`820e9dc5`, before any of PR #3137's changes, worktree
`/tmp/base-check`) — result:
```
15 failed, 548 passed, 3 xfailed in 32.28s
```
same 15 test names as the PR-worktree run, confirming these are
genuinely pre-existing and not caused by this PR. derived: re-ran on
current `main` (`02c3c8cb`, this session's own working tree) — result:
```
563 passed, 3 xfailed in 32.07s
```
0 failed. derived: `git show --stat 73b614fd` (issue-3091 work, landed
on main after PR #3137's base) — result: touches exactly
`test/test_convention_equivalence.py`,
`test/test_local_dependency_env.py`,
`test/test_spawn_artifact_skill_pairing.py`,
`test/test_spawn_cross_family_skill_selection.py`,
`test/test_spawn_skill_judge_haiku_timeout_overlap.py` — the same five
files the 15 PR-worktree failures live in. So "15 failed, owned by
#3091" is accurate as of this PR's base and already resolved on current
main by unrelated work — not a defect in this PR, just a staleness
artifact of its base.

### Must-not clauses

derived: `grep -n "subprocess\|gh " amendment_channel.py` (untracked
path, from `/tmp/pr3137-review-b/on-the-record/hooks`) — result: only
one `subprocess.run(["git", "-C", cwd, "rev-parse", ...])` call (local,
no network) in `issue_for_cwd`. No `gh`/network call on the hot path.
Present.

canonical: `a0abb72d:on-the-record/hooks/amendment_channel.py:322-334`
(`main()`) — only ever emits `hookSpecificOutput.additionalContext`,
never a `permissionDecision` field; `run_hook` returns a string or
`None`. Never a blocking gate. Present.

canonical: `gh pr diff 3137 --name-only` — this PR is purely additive
(new files + hook wiring), touches no spawn/kill code path. Never
treats kill-and-respawn as the answer, by omission of any such change.
Present.

### Supplementary audits (skills mounted for this task)

**test-depth-audit** on `a0abb72d:tests/test_amendment_channel.py` —
derived: `grep -c "def test_" test_amendment_channel.py` (untracked
path, run inside `tests/` from `/tmp/pr3137-review-b`) — result: 35.
canonical: read the full file — the overwhelming majority are Genuine
Assertion; every `MarkerReadWrite`, `FiresOncePerAmendment`, and
`AbsorbedAmendmentStopsAnnouncing` test asserts a specific returned
value or `None`/not-`None` with content checks (e.g.
`a0abb72d:tests/test_amendment_channel.py:116`
`assertIn("fix the brief", notice)`), not just absence-of-exception. No
Execution-Only or Dead tests found by this read. One Happy-Path gap
consistent with the Incorrect finding above: the suite has zero tests
constructing two different repos, so the cross-repo collision is
untested by construction, not by an oversight inside an existing test.

**silent-failure-audit** on
`a0abb72d:on-the-record/hooks/amendment_channel.py`'s error-handling
sites: canonical: read the full file — all of `read_marker`,
`write_amendment`, `_read_seen`, `check_notice`, `_extract_note`,
`issue_for_cwd` are Handled — fail open by explicit design, each
documented and each traced to a test. `write_amendment`'s own OSError
path was itself the subject of a fix already inside this PR (stderr
diagnostic added at
`a0abb72d:on-the-record/hooks/amendment_channel.py:267-280`, tested at
`a0abb72d:tests/test_amendment_channel.py:252-266`). Two smaller,
lower-severity sites were not given the same treatment: `main()`'s
`except OSError: pass` around `sys.stdout.write(...)`
(`a0abb72d:on-the-record/hooks/amendment_channel.py:333`) and around
`sys.stdin.read()` (line 326) both silently drop without a stderr trace
— the same Silently-Absorbed shape (bare `pass`) the PR's own fix
elsewhere in this file already recognizes and corrects one layer down.
Blast radius is small (an already-rare local I/O failure at the very
edges of the hook process) but worth naming precisely because the file
demonstrates it already knows how to do this correctly elsewhere.

## Why

derived: this session's own conversation transcript this turn (the
spawning prompt's stated instructions) — that prompt assigned the
writer side and the wiring as this session's specific emphasis (the
other parallel verification covers different ground), with four
concrete questions: is the write automatic; is the hook registered and
classified together; is the marker scoped correctly across issues and
repos; and is what's surfaced sufficient to act on. Each was answered
by reading the shipped code and independently reproducing behavior
rather than citing the builder's own record's numbers, per
`defect-verification-independence-from-upstream-verdicts` rule 1 and
`adversarial-review`'s blind-evaluator stance. The cross-repo
reproduction specifically was built as a minimal, from-scratch two-repo
scenario rather than inferred from reading the code alone, because a
claim about isolation is exactly the kind of thing that skill's rule 2
requires an actual negative-path attempt for, not just an inspection.

## What did not work

None — this session's checks all ran as planned; no approach was
started and abandoned.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used the
blind-evaluator stance (treat the deliverable as the thing to break,
not to defend) throughout this whole verification, most concretely in
building the from-scratch cross-repo reproduction under "Cross-issue /
cross-repo attribution" rather than accepting the code's own
isolation-by-issue-number framing at face value.

skill-verdict: implementation-audit — applied: invoked; this record's
own structure (Present/Surface/Absent/Incorrect/Unverifiable per
criterion, each with file:line evidence) follows its classification
taxonomy directly.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; per this record's own "What was done" section
(derived: the builder's record was read only after this session's own
`pytest`/probe runs had already produced their results, see the
worktree setup paragraph there), and the cross-repo scenario was a
deliberately-added negative-path attempt (rule 2) rather than only
re-running the suite's existing happy-path assertions.

skill-verdict: test-depth-audit — applied: invoked; classified
`a0abb72d:tests/test_amendment_channel.py` under "Supplementary audits"
above (Genuine Assertion density, the one Happy-Path gap on repo
isolation).

skill-verdict: silent-failure-audit — applied: invoked; traced every
error-handling site in `a0abb72d:on-the-record/hooks/amendment_channel.py`
under "Supplementary audits" above, including the two `main()` sites
not given the same stderr-diagnostic treatment as `write_amendment`'s
own fix.

skill-verdict: work-in-english — applied: invoked; this record, all
scratch scripts, and commit messages are in English; the end-of-turn
summary to the user follows in Korean per the policy.

other mounted skills: not triggered — `test-depth-audit`,
`silent-failure-audit`, and `adversarial-review` above are the three
skills this session's own role mounts. Of the broader configured list,
`prose-modes` did not apply (this record is a structured audit record
under record-shape, not reader-facing explanatory prose needing
style-mode selection) and `conformance-review-finding-record` did not
apply (its trigger path is a `conformance-review.md` file that does not
exist anywhere in this repository — untracked/absent, not this
session's own record path above).

## Upstream basis

- PR #3137, branch
  `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`,
  head `a0abb72dc132d723bae499503a396d8e79af81cd` (canonical: `gh pr
  view 3137` output and the fetched worktree at that head; not
  same-commit with this record).

## Open findings

derived: this session's own reproduction under "Cross-issue /
cross-repo attribution" above (`/tmp/cross_repo_repro2.py`) — result:
both `repo-a` (the amending orchestrator) and `repo-b` (an unrelated
worker) received the identical notice text for issue #42, confirming
the collision described in finding 1 below is live, not theoretical.

1. **Cross-repo marker collision (Incorrect, confirmed reproduced —
   full repro under "Cross-issue / cross-repo attribution" above)**:
   `a0abb72d:on-the-record/hooks/amendment_channel.py`'s
   `default_state_dir()` and `marker_path()` key the amendment marker
   by issue number alone, with no repo/org dimension. Two repos with an
   orchestrator working both (the task's own example: on-the-record and
   study-companion) that happen to share an issue number will
   cross-deliver amendment notices. Resolution path: add a repo-identity
   component to the state-dir or marker-path key (e.g. a hash of `git -C
   cwd remote get-url origin` or the repo's absolute toplevel path,
   resolved the same way `issue_for_cwd` already resolves the branch —
   one more local `git` call, no network) and add a test constructing
   two independent repos with the same issue number, the gap this
   session found missing from the 35-case suite.
2. **Untrapped truncation at 2000 chars (minor)**: `_NOTE_MAX` silently
   truncates the note with no marker of truncation; a worker seeing a
   truncated note has no signal that it's incomplete. Resolution path:
   append a `"... (truncated, re-read the issue for the full body)"`
   marker when `len(value) > _NOTE_MAX`.
3. **`main()`'s stdin/stdout OSError paths silently drop with no trace
   (minor)**: inconsistent with the stderr-diagnostic pattern this same
   PR already applied to `write_amendment`'s failure path one layer
   down. Resolution path: mirror the same one-line stderr write in
   `main()`'s two `except OSError` blocks.

## Next steps

This session's findings above are handed to whoever picks up PR #3137
next (its own author or a follow-up session) — this session does not
edit that PR, per the spawning prompt's explicit instruction ("do not
merge and do not edit PR #3137"). `loop_state: landed` — the
verification checks this session was assigned are all run and recorded
above; no further action is planned from this session.
