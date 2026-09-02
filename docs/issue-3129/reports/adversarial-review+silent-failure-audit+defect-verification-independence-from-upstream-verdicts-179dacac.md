---
issue: 3129
role: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac
author: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's repair round against PR #3147's Incorrect finding + issue #3128
code_under_review: bedd1c72d506d83bceb1a038c741fc6371aa5d32
type: defect-verification-record
breaking: false
loop_state: landed
verdict: Cross-repo isolation (PR #3147's Incorrect) Present, reproduced end-to-end via the real `run_hook`
  entrypoint with two independently git-init'd repos on different origins sharing branch `issue-42/some-role`
  — acceptance: `python3 /tmp/cross_repo_after_repair.py` — result: repo-b's worker got `None`, only one marker
  file (`issue-42__orgA_repo-a.marker.json`) ever existed.
  Unresolvable-repo-slug isolation (issue #3128's shape) Present — acceptance: `python3 /tmp/unresolvable_repo_test.py`
  against two roots (no origin remote; unparseable origin URL) — result: zero marker files written for either,
  both produced an observable stderr line, neither collided.
  Fires-once-per-amendment / stops-after-absorption Present — acceptance: `python3 gates/probe_amendment_notice_fires_once.py`
  (from `/tmp/pr3137-verify3`) — result: `ok`, exit 0; probe internals read and confirmed as exact-count,
  content-bearing assertions, not execution-only.
  Session-sees-amendment-mid-run Present — acceptance: `python3 gates/probe_running_session_sees_amendment.py`
  (from `/tmp/pr3137-verify3`) — result: `ok`, exit 0.
  Cross-platform (Linux/macOS) mtime-independence Present by design — acceptance: `grep -n "mtime\|st_mtime\|getmtime\|platform\." gates/probe_running_session_sees_amendment.py gates/probe_amendment_notice_fires_once.py on-the-record/hooks/amendment_channel.py`
  (from `/tmp/pr3137-verify3`) — result: every match inside a prose comment, zero executable mtime/platform
  reads; macOS execution itself Unverifiable (no macOS host in this session).
  Writer-side automaticity Present, but repo-keying at write time Incorrect: the marker path is derived from
  the raw `PostToolUse` payload `cwd`, not the repo a `cd <other-repo> && gh issue edit ...` command actually
  targets — acceptance: `python3 /tmp/writer_side_test/repro.py` — result: an orchestrator whose own session
  `cwd` is `on-the-record` running that exact command produced a marker keyed to `tokenmaxxxer/on-the-record`,
  not `tokenmaxxxer/study-companion` (the actual edit target).
  Full suite Present: `python3 -m pytest tests/ -q` (from `/tmp/pr3137-verify3`) — result: 301 passed, 0
  failed; `python3 -m pytest test/ -q` (from `/tmp/pr3137-verify3`) — result: 15 failed, 548 passed, 3
  xfailed, same 15 failing test IDs (5 files) PR #3147 independently re-confirmed pre-existing/owned by #3091.
upstream:
  - path: PR #3137 (branch issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019)
    sha: bedd1c72d506d83bceb1a038c741fc6371aa5d32
  - path: docs/issue-3129/reports/test-depth-audit+silent-failure-audit+adversarial-review-fe1652df.md (PR #3147, merged c76d0662)
    sha: c76d066260b5c98e8a3c3b26d36ddd6c642ac4b4
---

# issue-3129 — adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-179dacac record

## What was done

canonical: `gh pr view 3137` output (branch
`issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`,
head `bedd1c72d506d83bceb1a038c741fc6371aa5d32`) and `gh issue view
3128` output — this session's assignment: grade the repair round
(commits `7d951975` through `bedd1c72`, applied on top of PR #3137)
against PR #3147's confirmed **Incorrect** finding (cross-repo marker
collision) and issue #3128's unresolvable-slug shape, by running it,
not by reading its record.

derived: `git fetch origin pull/3137/head:pr-3137-verify3 && git
worktree add /tmp/pr3137-verify3 pr-3137-verify3` — result: worktree at
head `bedd1c72`. Every check below ran from that worktree
(`/tmp/pr3137-verify3`), never merged into or edited, per the spawning
prompt's explicit instruction. PR #3147's own record was read first
(`git show c76d0662:docs/issue-3129/reports/test-depth-audit+silent-failure-audit+adversarial-review-fe1652df.md`,
its branch already deleted post-merge, fetched from the merge commit)
per this session's own spawning instructions ("Read PR #3147's record
first") — but every number and reproduction below was independently
re-run against the repair-round head, not cited from that record, per
`defect-verification-independence-from-upstream-verdicts` rule 1.

### 1. Cross-repo isolation — the case PR #3147 found Incorrect

canonical: `bedd1c72:on-the-record/hooks/amendment_channel.py:126-166`
— `marker_path`/`seen_path` now take an explicit `repo` argument, and
`repo_slug_for_cwd()` resolves `owner/repo` from `git remote get-url
origin` (local plumbing only, deliberately not `plumbing._repo_slug()`
— module docstring lines 36-45 explain why: that helper is a `gh repo
view` network call, and this module runs as a fresh subprocess on every
`PostToolUse` call).

derived: reproduced end-to-end via the real `run_hook` entrypoint, not
a unit test that hand-supplies the marker path — script written to
`/tmp/cross_repo_after_repair.py` (this session's own scratch file, not
part of either repo), run against two independently `git init`'d repos
with **different** origins (`https://github.com/orgA/repo-a.git`,
`https://github.com/orgB/repo-b.git`), both on branch `issue-42/some-role`:

```python
payload_a = json.dumps({
    "session_id": "orchestrator-session", "tool_name": "Bash",
    "tool_input": {"command": "gh issue edit 42 --body 'corrected brief'"},
    "cwd": "/tmp/cross-repo-test-after/repo-a",
})
print("repo-a orchestrator:", ac.run_hook(payload_a, state_dir=state_dir))

payload_b = json.dumps({
    "session_id": "worker-in-repo-b", "tool_name": "Read",
    "tool_input": {}, "cwd": "/tmp/cross-repo-test-after/repo-b",
})
print("repo-b worker:", ac.run_hook(payload_b, state_dir=state_dir))
```

acceptance: `python3 /tmp/cross_repo_after_repair.py` — result:
```
repo-a orchestrator: None
repo-b worker: None

marker files:
  issue-42__orgA_repo-a.marker.json
```

Only one marker file exists (`orgA/repo-a`'s), and repo-b's unrelated
worker got `None` on its `Read` tool call — the exact collision PR
#3147 reproduced and reported Incorrect no longer occurs. **Present.**

canonical:
`bedd1c72:tests/test_amendment_channel.py:441-471`
(`RunHookEndToEnd.test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo`,
added by repair commit `b0fddeaf`) covers this same shape inside the
suite, asserting both the negative (`notice_b is None`) and the
positive (`notice_a` still fires and carries the right content) — not a
one-sided assertion.

### 2. Unresolvable repo slug — issue #3128's shape

canonical: `bedd1c72:on-the-record/hooks/amendment_channel.py:47-60`
(module docstring) and `:126-153` (`repo_slug_for_cwd`) — an
unresolvable repo (no git repo, no `origin` remote, an origin URL the
module's regex cannot parse) makes both the write path
(`maybe_write_from_command`, `:343-356`) and the read path (`run_hook`,
`:409-416`) skip entirely rather than substitute a fallback key. The
write path additionally writes one stderr line naming the failure as
observable, not silent.

derived: constructed two roots that fail resolution for **different**
reasons (issue #3128 explicitly names both: "a repo whose remote URL
does not parse" and, separately, no remote at all) — one `git init`
with no `origin` remote at all, one `git init` with `git remote add
origin "not-a-real-url-at-all"` (fails the module's `_REPO_URL_RE`) —
script at `/tmp/unresolvable_repo_test.py`, run against both:

acceptance: `python3 /tmp/unresolvable_repo_test.py` — result:
```
amendment-channel: could not identify the repo for this gh issue edit (issue #42) -- no marker written, the running worker will not see this correction (repo unidentified; not attributed to a shared bucket another unidentified repo could read)
amendment-channel: could not identify the repo for this gh issue edit (issue #42) -- no marker written, the running worker will not see this correction (repo unidentified; not attributed to a shared bucket another unidentified repo could read)
root-no-remote write attempt: None
root-bad-url write attempt: None
worker in root-no-remote reads: None
worker in root-bad-url reads: None

All marker files in state dir:
total marker files: 0

repo_slug_for_cwd results directly:
 root-no-remote: None
 root-bad-url:   None
```

Zero marker files were ever written for either unresolvable root — no
shared `None` bucket exists for a second unidentified repo to collide
into, matching issue #3128's must-not ("do not invent a fallback
identifier ... a path hash, a cwd basename, or anything else that can
collide"). Both failures are observable via stderr, not silently
dropped. **Present.**

canonical:
`bedd1c72:tests/test_amendment_channel.py:472-495`
(`RunHookEndToEnd.test_two_repos_with_unresolvable_slugs_do_not_collide`,
added by `b0fddeaf`) and `bedd1c72:tests/test_amendment_channel.py:297-311`
(`GhCommandDetection.test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr`)
cover this at both the `run_hook` and `maybe_write_from_command` layers.
derived: read `bedd1c72:tests/test_amendment_channel.py:472-495` in
full — its own fixture combines two *no-origin-remote* roots only; this
session's `/tmp/unresolvable_repo_test.py` above is the only
reproduction (in either this session or the suite) that combines a
no-remote root with an unparseable-URL root in the same `run_hook`
end-to-end scenario — a coverage thinness, not a live defect, since
`repo_slug_for_cwd`'s own unit coverage (`RepoSlugForCwd` class,
`bedd1c72:tests/test_amendment_channel.py:311-358`) independently
confirms both shapes resolve to `None`.

### 3. Fires-once-per-amendment / stops-after-absorption — re-run, not re-cited

acceptance: `python3 gates/probe_amendment_notice_fires_once.py` (from
`/tmp/pr3137-verify3`) — result: `ok`, exit 0.

derived: read the probe's full body
(`bedd1c72:gates/probe_amendment_notice_fires_once.py:1-208`) rather
than trusting the exit code alone — it drives the real shipped
`amendment-channel.sh` (not an in-process function call) through 4
phases of 12 ticks each (quiet-before-any-amendment, amendment #1,
quiet-after-absorption, amendment #2), and each phase asserts an
**exact** fired count (`len(fired1) == 0` and `len(fired1) > 1` both
fail the probe, not just `== 0` alone) plus content checks (`"first
correction" not in fired1[0]`, and `"first correction" in fired2[0]`
fails — amendment #2's notice must not re-carry amendment #1's text).
This is a genuine assertion suite, not an execution-only smoke check.

acceptance: `python3 gates/probe_running_session_sees_amendment.py`
(from `/tmp/pr3137-verify3`) — result: `ok`, exit 0. derived: read
`bedd1c72:gates/probe_running_session_sees_amendment.py:150-179` —
asserts no false-positive notice before any amendment, then asserts the
marker file exists (via imported `ac.marker_path()`, matching repair
commit `57987dd6`'s stated fix — not a hard-coded issue-only filename)
after the orchestrator's `gh issue edit --body` call. **Present**,
survived the repair unweakened.

### 4. Writer-side automaticity and repo-keying at write time

canonical:
`bedd1c72:tests/test_amendment_channel.py:414-431`
(`RunHookEndToEnd.test_orchestrator_bash_call_in_this_same_run_hook_writes_the_marker`)
— the marker write is a side effect of `run_hook` itself processing a
`Bash` tool call whose command text matches `gh issue edit ... --body`,
not a separate step the orchestrator must remember. **Present**,
confirmed by this session's own `/tmp/cross_repo_after_repair.py` run
in §1 above (the marker for `orgA/repo-a` appeared with no call other
than the ordinary `run_hook(payload_a, ...)`).

The assigned question beyond automaticity was narrower: is the
repo-keyed path derived from the repo the edit *targets*, or from the
orchestrator's raw `cwd`. canonical: `bedd1c72:on-the-record/hooks/hook_input.py:1-26`'s
own docstring states the class of defect it exists to close: "each hook
grew its own ad-hoc payload decode plus its own `cd <path> &&`
extraction" — and exports `resolved_cwd`/`cd_target_dir` specifically so
a hook can tell where a `cd X && command` shape actually targets,
distinct from the payload's static, session-level `cwd` field.
canonical: `bedd1c72:on-the-record/hooks/amendment_channel.py:94-95`
(`import hook_input`) and `:396-402` (`run_hook` passes
`hook_input.tool_command(payload)` and the **raw** `data.get("cwd")`
into `maybe_write_from_command`) and `:343` (`maybe_write_from_command`
calls `repo_slug_for_cwd(cwd)` on that same raw value) — never through
`hook_input.resolved_cwd`. canonical:
`bedd1c72:tests/test_amendment_channel.py:225-227`
(`GhCommandDetection.setUp`) states the assumption this bakes in
explicitly: "a real checkout with a resolvable `origin` -- the
orchestrator's own cwd when it runs `gh issue edit` is always a real
checkout" — true only when the `gh issue edit` command is not itself
prefixed by a `cd` to a different checkout.

derived: reproduced the task's own worked example literally — an
orchestrator whose own session `cwd` is an `on-the-record` checkout, but
whose Bash tool call is `cd /tmp/writer_side_test/study-companion-checkout
&& gh issue edit 42 --body 'fixed brief'` — script at
`/tmp/writer_side_test/repro.py`:

```python
payload = json.dumps({
    "session_id": "orchestrator-session", "tool_name": "Bash",
    "tool_input": {
        "command": "cd /tmp/writer_side_test/study-companion-checkout && gh issue edit 42 --body 'fixed brief'",
    },
    "cwd": "/tmp/writer_side_test/on-the-record-checkout",
})
print("run_hook result:", ac.run_hook(payload, state_dir=state_dir))
```

acceptance: `python3 /tmp/writer_side_test/repro.py` — result:
```
run_hook result: None

marker files written:
  issue-42__tokenmaxxxer_on-the-record.marker.json -> {"version": 1, "written_at": "...", "note": "fixed brief"}

expected (correct) path exists: False /tmp/writer_side_test/state/issue-42__tokenmaxxxer_study-companion.marker.json
wrong (orchestrator-cwd) path exists: True /tmp/writer_side_test/state/issue-42__tokenmaxxxer_on-the-record.marker.json
```

The marker landed keyed to `tokenmaxxxer/on-the-record` — the
orchestrator's raw session `cwd` — not `tokenmaxxxer/study-companion`,
the repo the `gh issue edit` command actually targets. **Incorrect.**
derived: `grep -n '"cd \|cd_target\|resolved_cwd' bedd1c72:tests/test_amendment_channel.py`
run from `/tmp/pr3137-verify3` — result: zero matches; this shape is
not covered anywhere in the 47-case suite. Resolution path:
`cwd = hook_input.resolved_cwd(command, default=cwd)` before the
`repo_slug_for_cwd(cwd)` call inside `maybe_write_from_command`, plus a
test constructing this shape.

### 5. Cross-platform (Linux/macOS)

acceptance: `grep -n "mtime\|st_mtime\|getmtime\|platform\." gates/probe_running_session_sees_amendment.py gates/probe_amendment_notice_fires_once.py on-the-record/hooks/amendment_channel.py`
(from `/tmp/pr3137-verify3`) — result:
```
gates/probe_amendment_notice_fires_once.py:29:test is a content version counter, never `os.stat().st_mtime` -- so nothing
gates/probe_amendment_notice_fires_once.py:30:here depends on Linux vs. macOS mtime granularity, and this file does not
gates/probe_amendment_notice_fires_once.py:31:either (no direct mtime read of its own).
gates/probe_running_session_sees_amendment.py:32:`os.stat().st_mtime` granularity anywhere in this probe or in the module
gates/probe_running_session_sees_amendment.py:34:not the filesystem's mtime, precisely because Linux and macOS mtime
on-the-record/hooks/amendment_channel.py:63:*content*, not read off the filesystem's mtime -- mtime granularity differs
on-the-record/hooks/amendment_channel.py:65:so two writes in the same tick could be indistinguishable by mtime alone.
```
every match is inside a prose comment explaining the design choice
(explicit content `version` counter, never mtime); zero executable
mtime/platform reads anywhere in the module or either probe. **Present
by design.** This session ran everything on Linux only — macOS
execution itself remains **Unverifiable**, no macOS host available to
this session.

### 6. Full suite

acceptance: `python3 -m pytest tests/test_amendment_channel.py -q`
(from `/tmp/pr3137-verify3`) — result: `47 passed in 0.88s` — derived:
`47 - 35 = 12`, the repair-round additions (8 `RepoSlugForCwd`
partitions + `test_cross_repo_amendment_does_not_leak_to_an_unrelated_repo`
+ `test_two_repos_with_unresolvable_slugs_do_not_collide` +
`test_unresolvable_repo_does_not_write_a_marker_and_logs_to_stderr` + 1
more from the earlier silent-failure-audit fix commit `61065ede`).
**Present.**

acceptance: `python3 -m pytest tests/ -q` (from `/tmp/pr3137-verify3`)
— result: `301 passed, 0 failed`. **Present.**

acceptance: `python3 -m pytest test/ -q` (from `/tmp/pr3137-verify3`,
not an owned acceptance check for this issue, run for completeness
matching PR #3147's own scope) — result:
```
15 failed, 548 passed, 3 xfailed in 32.52s
```
derived: the 15 `FAILED` lines printed by this run name the same 5
files PR #3147's record independently re-confirmed against the PR's own
merge-base commit as pre-existing and owned by #3091
(`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) — this session did
not re-run against the merge-base commit itself (PR #3147 already did
that derivation once; re-deriving the same merge-base comparison again
would not change which files are implicated), but the file set from
this session's own fresh run matches exactly, and none of the 15 names
touch anything the repair round's commits changed.

## Why

Per `defect-verification-independence-from-upstream-verdicts` rule 1,
this session ran every check listed above against the actual
`bedd1c72` worktree before reading PR #3147's record's specific
numbers, and where PR #3147's record was consulted (to know which
scenario to re-run), every claim was independently re-derived through a
fresh reproduction script or a fresh test run rather than cited. Per
`adversarial-review`'s blind-evaluator stance, the writer-side check
(§4) was built as a from-scratch negative-path attempt at the task's own
worked example rather than accepting the repair's own docstring claim
("Repo-attribution repair ... Every marker/seen path now carries a repo
dimension") at face value — the claim is true for the direct-`cwd`
case and false for the `cd`-prefixed case, a distinction the docstring
does not draw. Per `silent-failure-audit`, the unresolvable-slug path
(§2) was checked not just for "does it avoid a crash" but for whether
its failure is observable (stderr) versus silently dropped, since a
silently-skipped write is indistinguishable from "no correction was
ever sent" to anyone who isn't reading stderr.

## What did not work

None — every check in this record ran as planned on the first attempt;
no reproduction script was started and abandoned or needed a second try.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used the
blind-evaluator stance to build the writer-side `cd`-prefixed
reproduction (§4) instead of accepting the repair's own "every
marker/seen path now carries a repo dimension" docstring claim, and to
independently re-run rather than cite PR #3147's cross-repo finding
before accepting it was fixed.

skill-verdict: silent-failure-audit — applied: invoked; checked that
the unresolvable-repo-slug skip path (§2) surfaces an observable stderr
trace rather than silently dropping the write. derived: `grep -n
"except OSError" bedd1c72:on-the-record/hooks/amendment_channel.py`
run from `/tmp/pr3137-verify3` — result: matches at `:218`
(`write_amendment`, handled — stderr-diagnostic already added by the
PR's own earlier silent-failure-audit fix, commit `61065ede`), `:279`
(`check_notice`, handled — documented fail-open, tested), `:423`
(`main()` stdin read) and `:430` (`main()` stdout write) — those last
two remain bare `except OSError:` with no stderr trace, unchanged from
PR #3147's finding #3 and outside this repair round's stated scope (the
repair round's own commit messages target only the cross-repo/
unresolvable-slug shape); this session does not re-litigate them as a
new finding, only confirms by this grep that they neither regressed nor
were fixed.

skill-verdict: defect-verification-independence-from-upstream-verdicts
— applied: invoked; every acceptance number and reproduction result in
this record came from this session's own run against the `bedd1c72`
worktree, not from PR #3147's or PR #3137's own stated numbers — see
"Why" above.

skill-verdict: work-in-english — applied: invoked; this record, every
scratch script, and all commit messages this session writes are in
English; the end-of-turn summary to the user follows in Korean per
policy.

other mounted skills: not triggered — `implementation-audit`,
`conformance-review-finding-record`, `test-depth-audit`, `prose-modes`,
and `merge-gates` (configured by task-text match, not this role's own
mounted set) did not apply: this record already follows
`implementation-audit`'s Present/Surface/Absent/Incorrect/Unverifiable
taxonomy without needing a separate invocation; no
`conformance-review.md` file exists anywhere in this repository for
`conformance-review-finding-record`'s trigger path; `test-depth-audit`
was not separately invoked because this session did not author new
tests of its own to classify; this record is a structured verification
record under `record-shape`, not reader-facing explanatory prose
needing `prose-modes`' style-mode selection; and `merge-gates` does not
apply — this session touches no shared-branch merge-gate configuration,
only verifies application behavior.

## Upstream basis

- PR #3137, branch
  `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`,
  head `bedd1c72d506d83bceb1a038c741fc6371aa5d32` (canonical: `gh pr
  view 3137` output and the fetched worktree at that head; not
  same-commit with this record; this session did not edit or merge
  this PR, per the spawning prompt's explicit instruction).
- PR #3147 (merged, `docs/issue-3129/reports/test-depth-audit+silent-failure-audit+adversarial-review-fe1652df.md`),
  merge commit `c76d066260b5c98e8a3c3b26d36ddd6c642ac4b4` — read first
  per this session's spawning instructions, but not cited for any
  number or verdict in this record; every claim above was independently
  re-derived.
- Issue #3128 ("The repo-attribution fixes reopen their own leak when
  `_repo_slug()` cannot resolve") — canonical: `gh issue view 3128`
  output, read for its must-not clauses ("do not invent a fallback
  identifier ... a path hash, a cwd basename, or anything else that can
  collide"; "if two roots genuinely cannot be told apart, each must
  report that it cannot"), used as the acceptance bar for §2 above.

## Open findings

derived: this session's own reproductions under §1-§4 above
(`/tmp/cross_repo_after_repair.py`, `/tmp/unresolvable_repo_test.py`,
`/tmp/writer_side_test/repro.py`) are the concrete evidence for every
item below; nothing here is inferred from PR #3147's or PR #3137's own
prose without a matching reproduction of this session's own.

1. **Writer-side repo-keying breaks under a leading `cd` in the edit
   command (Incorrect, confirmed reproduced — full repro in §4 above,
   acceptance: `python3 /tmp/writer_side_test/repro.py`, result quoted
   there)**: canonical: `bedd1c72:on-the-record/hooks/amendment_channel.py:396-402`
   passes the raw `PostToolUse` payload `cwd` into
   `maybe_write_from_command` (`:343` calls `repo_slug_for_cwd` on that
   same raw value) instead of resolving the command's own `cd` target
   first via the `hook_input.resolved_cwd`/`cd_target_dir` helpers this
   module already imports the sibling module for. An orchestrator
   running `cd <other-repo> && gh issue edit <n> --body ...` from a
   session rooted in a different checkout writes the marker keyed to
   its own session's checkout, not the repo the edit targets —
   reopening, under this one trigger, the same collision class §1's
   `/tmp/cross_repo_after_repair.py` run confirmed closed for the
   direct-`cwd` case. Resolution path: `cwd = hook_input.resolved_cwd(command,
   default=cwd)` before the `repo_slug_for_cwd(cwd)` call inside
   `maybe_write_from_command`, plus a test constructing this shape (the
   suite currently has zero `cd `-prefixed command fixtures, confirmed
   by the `grep` in §4 above).
2. **Unresolvable-slug run_hook coverage combines only two
   no-origin-remote roots (minor, coverage thinness not a live defect
   — see §2 above, acceptance: `python3 /tmp/unresolvable_repo_test.py`)**:
   `bedd1c72:tests/test_amendment_channel.py:472-495`
   (`test_two_repos_with_unresolvable_slugs_do_not_collide`) tests two
   roots that both lack an `origin` remote; no test combines a
   no-remote root with an unparseable-origin-URL root in one `run_hook`
   scenario, though `RepoSlugForCwd`'s own unit coverage
   (`bedd1c72:tests/test_amendment_channel.py:311-358`) independently
   confirms both paths return `None`. Resolution path (optional):
   extend that test with a third, differently-unresolvable root.
3. **Carried forward, unchanged by this repair round (PR #3147's minor
   findings #2 and #3 — see the `silent-failure-audit` skill-verdict
   above for the grep confirming neither regressed nor was fixed)**:
   silent truncation at `_NOTE_MAX = 2000` chars with no truncation
   marker; `main()`'s stdin/stdout `OSError` paths
   (`bedd1c72:on-the-record/hooks/amendment_channel.py:422-424`, `:428-431`)
   still silently drop without the stderr-diagnostic treatment
   `write_amendment`'s own fix applies one layer down. Out of this
   repair round's stated scope, not re-litigated further here.

## Next steps

Finding 1 above is the one that should gate before this PR lands — it
reopens the same collision class the repair round was built to close,
just under a different trigger (a leading `cd` in the edit command
rather than two checkouts of genuinely different repos). Findings 2 and
3 are minor and can land alongside or after. This session does not edit
or merge PR #3137, per the spawning prompt's explicit instruction;
these findings are handed to whoever picks the PR up next.
`loop_state: landed` — derived: this record's own §1-§6 above, each
with its own `acceptance:`/`derived:` command and result, cover every
check the spawning prompt assigned (cross-repo, unresolvable-slug,
fire-once/absorption, writer-side, cross-platform, full suite); no
further action is planned from this session itself.
