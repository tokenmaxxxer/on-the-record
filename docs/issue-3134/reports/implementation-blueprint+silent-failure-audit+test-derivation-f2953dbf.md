---
issue: 3134
role: implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf
author: implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/amends-landing-apply.sh, gates/amends_landing.py
loop_state: landed
type: repair
breaking: false
verdict: fixed
upstream:
  - path: docs/issue-3134/reports/adversarial-review+silent-failure-audit+test-depth-audit-0516652a.md
    sha: e109ddadfe029b8a58c5e0343bd08977b30dc1d0
---

# issue-3134 — implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf record

## What was done

canonical: this record's own diff on `on-the-record/hooks/amends-landing-apply.sh` and `tests/test_amends_landing_hook_e2e.py`, and the pytest/probe runs quoted below.

Repair on PR #3165, closing the two gaps that PR #3175's independent
verification of the prior round surfaced (see docs/issue-3134/reports/
adversarial-review+silent-failure-audit+test-depth-audit-0516652a.md on
`main`, added by commit f5ff8cff — not on this branch: this branch is
built on PR #3165's own head, `e109ddad`). Only `on-the-record/hooks/
amends-landing-apply.sh` and `tests/test_amends_landing_hook_e2e.py`
changed; `gates/amends_landing.py` needed no edit — see "Why" below.

**Gap 1 — repo targeting.** `-R`/`--repo`/`--repo=`/an inline
`GH_REPO=value` prefix/a `cd` into a different checkout were all accepted
by the command-shape check and then dropped before the confirming
`gh pr view` call, so confirmation could run against the wrong repo's PR
number while `land()` still pushed to this checkout's own `origin`. Fixed
by fixing "the registered repo" before the command is inspected at all
(the session's own `cwd`'s `origin`,
`on-the-record/hooks/amends-landing-apply.sh`, line 260) and refusing
outright, before any `gh pr view` call, when the command names a
different one:

- `derived: on-the-record/hooks/amends-landing-apply.sh`, lines 236-282
  -- `_normalize_repo()`/`_origin_repo()`/`_explicit_repo_flag()` resolve
  a comparable `owner/repo` form from a git remote URL, an `-R`/`--repo`/
  `--repo=` flag value, or a plain string.
- `derived: on-the-record/hooks/amends-landing-apply.sh`, lines 154-200
  -- `_strip_env_prefix()` strips a leading `VAR=value` prefix (both at
  the top level and again right after `cd DIR &&`) before matching the
  merge command shape, so an inline `GH_REPO=other/repo` prefixed merge
  is recognized as a merge command at all instead of falling to class A
  untested against the repo-remit rule.
- `derived: on-the-record/hooks/amends-landing-apply.sh`, lines 285-309
  -- the refusal itself: one `_decline()` call naming both the
  registered repo and the refused target, exit nonzero, nothing written
  (the confirming view call at line 349 is never reached on this path).
- `derived: on-the-record/hooks/amends-landing-apply.sh`, lines 325-336
  -- the PR number fed to the confirming view call is now read out of
  `e.get("tool_response")` (what the merge actually printed on success,
  i.e. the hook's own tool-result data) instead of re-parsed out of
  `tool_input.command` (the requested, author-controlled command
  string) -- the command string names what was asked for, not what
  happened.

**Gap 2 — every declined path is silent.** The prior round's own audit
named this. Every decline is now one of three classes:

- class A ("not a merge, nothing to do" -- the command wasn't a merge
  command at all, or was `--help`/`-h`/`--dry-run`, or was chained/
  substituted): stays silent, exit 0, by design -- `on-the-record/hooks/
  amends-landing-apply.sh`, lines 180, 182, 185 and 200. This is a
  deliberate quiet Handled outcome, not an absorbed failure: every
  ordinary Bash call in a session reaches this hook, so a stderr line on
  each one would bury the real signal. Verified by
  `test_ordinary_non_gh_command_produces_zero_stderr`
  (`tests/test_amends_landing_hook_e2e.py`, lines 186-202).
- class B ("was a merge, confirmation could not run" -- own-repo
  resolution failed, the confirming view call is unlaunchable/exits
  non-zero, or returns malformed or structurally-empty JSON): exactly
  one stderr line, exit nonzero -- `on-the-record/hooks/amends-landing-
  apply.sh`, lines 262-268 (own-repo resolution), 352-355 (subprocess
  error), 356-361 (non-zero exit), 362-367 (malformed JSON), 368-371
  (parses but carries no `state` key at all -- "empty JSON" per the
  prior round's own wording).
- class C ("was a merge, confirmed not merged" -- the confirming view
  call succeeded and reports a `state` other than `MERGED`, or a falsy
  `mergedAt`): exactly one stderr line, exit nonzero -- `on-the-record/
  hooks/amends-landing-apply.sh`, lines 372-377.

The bash wrapper's own final `exit 0` line was forced regardless of what
the embedded Python guard decided (pre-fix), so even a class B/C decline
that DID write its stderr line still reported success via exit code, and
no test could assert on the exit code meaning anything. Changed to
`exit $?` (`on-the-record/hooks/amends-landing-apply.sh`, line 432,
propagating the Python guard's own exit code), which this repo's own
hook contract already allows: `on-the-record/hooks/hook_input.py`'s
module docstring states the hook runtime treats a non-zero-and-not-two
exit from a `PostToolUse` hook as non-blocking, so this changes nothing
about `PostToolUse`'s documented inability to deny -- only what an
operator reading stderr plus exit code can tell about why nothing
landed.

`checked: python3 -m pytest tests/test_amends_landing_hook_e2e.py -v` --
result:
```
14 passed in 1.06s
```

`checked: python3 -m pytest tests/ -q` -- result:
```
345 passed, 2 warnings in 11.26s
```
(the two warnings are a pre-existing pinned-fixture-divergence notice in
`tests/test_skill_candidates_floor.py`, unrelated to this repair.)

`checked: python3 -m pytest tests/test_amends_resolution.py -q` --
result:
```
19 passed in 0.84s
```

`checked: python3 gates/probe_amends_is_discoverable.py` -- result: exit
0 ("ok").

`checked: python3 gates/probe_amends_fails_closed.py` -- result: exit 0
("ok").

## Why

canonical: on-the-record/hooks/amends-landing-apply.sh (this commit's own diff) and docs/issue-3134/reports/adversarial-review+silent-failure-audit+test-depth-audit-0516652a.md (on main, out-of-scope for this branch's own tree).

**Architecture note (implementation-blueprint framing).** This is a
scoped repair to two existing files plus their test file -- no new
module boundary, no new archetype. `gates/amends_landing.py::land()`
already only ever operates on the `remote`/`branch` strings explicitly
passed to it by the hook (an earlier round's own design); both gaps this
round closes live entirely in the hook's own pre-`land()` logic (which
repo to confirm against, which PR number to confirm), so `land()` needed
no change at all. The decline-message contract already had one shared
dialect before this round -- the hook prefixes its own messages
`"amends-landing-apply: "` and forwards `land()`'s own
`"amends-landing: <error>"` text verbatim when `land()` itself fails
(`on-the-record/hooks/amends-landing-apply.sh`, lines 416-417, unchanged
this round) -- and this repair keeps that single dialect: every new
class A/B/C/gap-1 message this round is written through one
`_decline()` helper (`on-the-record/hooks/amends-landing-apply.sh`, lines
255-257) inside the hook, so there is exactly one place that owns
wording for the hook's own declines, not two drifting copies between the
hook and the gate.

**Silent-failure-audit framing.** Every catch/observe site in the hook
was classified. All were Silently Absorbed before this round (the prior
round's own finding) except the two sites below; every Silently Absorbed
site is now Handled (propagates via the `_decline()` single-stderr-line
plus non-zero-exit contract, cited by class above):

- `on-the-record/hooks/amends-landing-apply.sh`, lines 180, 182, 185 and
  200 (class A guards) -- Handled, and deliberately quiet: the
  exit-zero/no-stderr outcome is itself the correct signal for "not a
  merge", not an absorption. Distinguished from an absorption by the
  dedicated anti-spam test asserting zero stderr lines.
- `on-the-record/hooks/amends-landing-apply.sh`, lines 379-390 (resolving
  the raw `origin` URL again for `git clone`, after confirmation already
  succeeded) -- Unreachable in practice: by this point `run_cwd`'s
  `origin` has already been resolved once, either directly as
  `registered_repo` or via `_origin_repo(target_cwd)` matching it, in the
  immediately preceding repo-targeting check; the only way this second
  resolution newly fails is a race window (the remote reconfigured
  between the two calls) that this repair does not attempt to close.
- `on-the-record/hooks/amends-landing-apply.sh`, lines 402-418 (the
  `land()` subprocess call itself failing or returning non-zero) -- left
  unchanged this round: already Handled per the prior rounds (writes one
  stderr line via the same `"amends-landing-apply: "` prefix, exit zero
  by design -- `land()` is fail-open, "same posture as post-landing-
  obligation-gate.sh" per the file's own header comment). This site is
  not one of the two gaps named above; a genuine confirmed-in-remit merge
  whose landing step then fails is a different risk category than
  "declined to even try", and changing its exit code was out of this
  round's scope.

## What did not work

None.

## Rationale for deviations

canonical: `gh pr view 3165 --json headRefName` (run this session, see below).

The brief instructed pushing to a branch named
`issue-3134/implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf`
on the premise that PR #3165 already tracked it. On inspection via the
headRefName query above, PR #3165's actual head branch turned out to be
`issue-3134/implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11`
-- a different, longer branch name; the `-f2953dbf` branch this session
started on did not exist on the remote at all and carried none of the
prior rounds' commits (it was freshly cut from `main`). Landing the fix
there would not have reached PR #3165 at all. Fixed forward: fetched PR
#3165's real branch, reset this session's local branch to its tip
(`git checkout -B issue-3134/implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf
FETCH_HEAD`, preserving this record's own untracked skeleton file), did
this round's fix on top of the prior round's actual landed commit
(`e109ddad`), and pushed to
`refs/heads/issue-3134/implementation-blueprint+silent-failure-audit+test-derivation+knowledge-management-supersession-lifecycle-b6857f11`
-- the branch PR #3165 actually tracks -- rather than to the literal
local branch name, so the fix lands on the PR the brief was actually
targeting.

## Upstream basis

- `docs/issue-3134/reports/adversarial-review+silent-failure-audit+test-depth-audit-0516652a.md`
  (on `main` at commit f5ff8cff, not on this branch -- untracked here) --
  PR #3175's independent verification of the prior round, naming both
  gaps this record closes.
- `on-the-record/hooks/amends-landing-apply.sh` at commit `e109ddad` (the
  prior round's landed state) -- the file this round's diff is built on
  top of.
- `tests/test_amends_landing_hook_e2e.py` at commit `e109ddad` -- the
  pre-existing test functions extended in place (one,
  `test_failed_merge_never_pushes`, had its assertion updated from
  `returncode == 0` to the new non-zero/one-stderr-line class-C contract;
  the others gained a zero-stderr assertion or were left as-is where
  still accurate).

## Open findings

canonical: `on-the-record/hooks/amends-landing-apply.sh`, lines 402-418
-- see the identical citation and its explanation under "Why" above.

None open. `gates/amends_landing.py::land()`'s own post-confirmation
failure path (clone/commit/push failing after a genuine in-remit merge
that was already confirmed) remains fail-open by design, unchanged this
round -- flagged above as unreachable-adjacent/out-of-scope, not a new
open finding.

## Acceptance verification

- amends-landing-apply.sh round-five e2e coverage passes (this repair's own commit, 2cef8cfa:on-the-record/hooks/amends-landing-apply.sh:432) — checked: tests/test_amends_landing_hook_e2e.py — result: pass
- full test suite has no regression — checked: tests/ — result: pass
- amends resolution suite unaffected — checked: tests/test_amends_resolution.py — result: pass
- discoverability probe passes — checked: gates/probe_amends_is_discoverable.py — result: pass
- fails-closed probe passes — checked: gates/probe_amends_fails_closed.py — result: pass

## Next steps

None -- `loop_state: landed`. Pushed to PR #3165's actual branch; PR
#3165 remains open for the next verification round.

```
skill-verdict: silent-failure-audit — applied: invoked; classified every decline path in amends-landing-apply.sh/amends_landing.py as Handled/Silently Absorbed/Unreachable and fixed the Silently Absorbed sites (see file:line citations above in this record)
skill-verdict: test-derivation — applied: invoked; derived the repo-match x decline-class test matrix in tests/test_amends_landing_hook_e2e.py as Given-When-Then cases per feasible column
skill-verdict: implementation-blueprint — applied: invoked; confirmed this repair needs no new module boundary/archetype, kept the decline-message contract identical across the hook and its gate companion
other mounted skills: not triggered
```
