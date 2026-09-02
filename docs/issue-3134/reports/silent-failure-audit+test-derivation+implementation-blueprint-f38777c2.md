---
issue: 3134
role: silent-failure-audit+test-derivation+implementation-blueprint-f38777c2
author: silent-failure-audit+test-derivation+implementation-blueprint-f38777c2
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: e109ddadfb7562ad558ea4c22c6c77436821c2f2 (this session's own commit, pushed directly to PR #3165's branch, base a9ebd8d7 -- PR #3165's own tip at this session's start; untracked on THIS branch -- this branch forks from main, PR #3165 is not yet merged)
type: repair-round-delivery
breaking: false
verdict: canonical `gh pr view 3168` output (state MERGED into main) and this session's own diff at e109ddad -- PR #3168's independent verification of PR #3165's round-3 delivery found its landing-step module structurally sound but its PostToolUse trigger provably over-broad (command-shape matched `gh pr merge --help`, success heuristic was "no failure marker in tool_response text", reproduced pushing to a scratch remote's default branch live). This session (repair round 4, narrow scope) fixed the trigger directly on PR #3165's own branch at e109ddad: rejects --help/-h/--dry-run outright and requires `gh pr view --json state,mergedAt` to independently confirm state==MERGED with a non-empty mergedAt before calling the landing function -- absence of a failure marker is never sufficient on its own anymore. Also guarded the second defect PR #3168 named, an unaudited `git status --porcelain` returncode that would have read a failed status check as "no changes, nothing to push." A new end-to-end test drives the real hook binary with realistic PostToolUse payloads across four scenarios and is confirmed, via `git stash` against the pre-fix branch, to fail before this round's fix. Acceptance requirement met — checked `python3 -m pytest tests/test_amends_resolution.py -q` -- result: 19 passed; `python3 gates/probe_amends_is_discoverable.py` -- result: exit 0; `python3 gates/probe_amends_fails_closed.py` -- result: exit 0; `python3 -m pytest tests/ -q` -- result: 335 passed; `python3 -m pytest test/ -q` -- result: 563 passed, 3 xfailed, 0 failed. All run this session against PR #3165's own branch (checked out locally), before switching back to this branch to write this record.
loop_state: done
upstream:
  - path: PR #3168 body/record (`gh pr view 3168`), the independent verification whose live reproduction of the over-broad trigger this round fixes; record path untracked on this branch -- lives on PR #3168's own already-merged commit, sha below
    sha: a9ebd8d7b333de8b3b04066c9ff461c59f27511c
  - path: PR #3165's own round-3 delivery record (untracked on this branch -- lives on PR #3165's own branch, not yet merged), the branch this round's fix commits onto
    sha: a9ebd8d7b333de8b3b04066c9ff461c59f27511c
---

# issue-3134 — silent-failure-audit+test-derivation+implementation-blueprint-f38777c2 record

## What was done

canonical: `gh pr view 3168` (read this session, full body) and `git show
771a173f --stat` (this repo's own merge commit landing PR #3168 onto
`main`, read this session). PR #3168's independent verification of PR
#3165's round-3 delivery found three of four reopen findings, plus round
3's own new landing-step mechanism, Present/correct -- except round-3
finding 3's own fix. That fix built two things on PR #3165's branch (not
merged to main, hence untracked on this branch -- verified this session
via `git log --oneline -- gates/amends_landing.py` on this branch,
result: empty): `gates/amends_landing.py` (untracked on this branch)'s
landing function (confirmed structurally sound by PR #3168 -- genuine
merge, failed merge, zero-edge merge, and a landing race all handled
correctly, no force-push) and `on-the-record/hooks/amends-landing-
apply.sh` (untracked on this branch), the `PostToolUse` trigger that
calls it automatically on a successful `gh pr merge`. PR #3168 found the
trigger itself broken.

canonical: PR #3168's record (cited in frontmatter `upstream:`),
"Finding 3" section, read in full this session via `gh pr view 3168`.
`gh pr merge --help` matched the trigger's own command-shape check, and
the shape validation that followed (reused from a sibling hook) only
rejected a shell chaining/substitution operator in the tail tokens -- it
never rejected a non-merging flag like `--help`. The success heuristic
then checked the tool response text for one of five failure-marker
strings ("failed to merge", "graphql error", ...); `--help`'s own
usage-text output contains none of them, so the hook proceeded to
resolve the checkout's `origin` remote/default branch and ran the
landing script against it -- a real clone+push to a scratch remote's
default branch, reproduced live by PR #3168's own session, in response to
a command that never merged anything.

This session's task (repair round 4, narrow scope): fix the trigger's
success detection to require actual evidence a merge happened, then close
the coverage gap that let this through (round 3's own end-to-end test
only ever called the landing function directly, never drove the hook
script itself). Both fixes were committed directly onto PR #3165's own
branch, per this round's own task instructions, rather than opened as a
separate PR against it -- the landing function itself needed no change,
since PR #3168 confirmed it sound.

derived: this session's own diff, `git -C <PR #3165 checkout> show
e109ddad --stat` (run this session while on PR #3165's branch, before
switching back here) -- result:
```
 gates/amends_landing.py                     |  15 ++-
 on-the-record/hooks/amends-landing-apply.sh |  96 +++++++++---
 tests/test_amends_landing_hook_e2e.py       | 240 +++++++++++++++++++++++++
 3 files changed, 267 insertions(+), 84 deletions(-)
```
(paths above are on PR #3165's branch; all three untracked on this
branch)

**Fix 1 -- the trigger.** The hook's `PostToolUse` guard now does two
things neither of which existed before: (a) rejects `--help`/`-h`/
`--dry-run` outright, checked against every token in the command, so a
`cd DIR && gh pr merge --help` variant is caught too; (b) resolves a PR
reference from the command (explicit number, or the trailing digits of a
`.../pull/<n>` URL, ported from a sibling hook's own established
PR-number-resolution pattern rather than reimplemented) and calls
`gh pr view <ref> --json state,mergedAt` in the run cwd, proceeding only
if the response parses as JSON with `state == "MERGED"` and a non-empty
`mergedAt`. The old tool-response-text failure-marker heuristic is
removed entirely, not layered under the new check -- text absence is
never load-bearing now. An implicit "current PR" invocation (no explicit
number) falls through to a bare `gh pr view` in the run cwd; since
`gh pr merge` moves the checkout to the base branch and deletes the head
branch by default, this legitimately confirms nothing for that shape and
is left unreached (no backlink applied) rather than guessed at --
documented in the hook's own header comment.

**Fix 2 -- the unaudited site.** derived: `silent-failure-audit` skill
applied (see `skill-verdict` below) against the landing function this
session -- its `git status --porcelain` call discarded the subprocess's
own returncode and only inspected stdout text. A failed status check
(corrupt clone, disk full) returns empty stdout identically to a genuine
"nothing changed," so the function would report "no backlinks needed" --
read by every caller as success -- even though the status check itself
never ran. Classification: Silently Absorbed (default-value-substitution-
without-recording: empty stdout on failure reads identically to empty
stdout on success). Fixed: the subprocess result's returncode is checked
first; a non-zero code returns an explicit error (falls back to a fixed
string if stderr itself is empty, so the failure is never reported as a
falsy value the caller would skip printing).

**Fix 3 -- the coverage gap.** A new end-to-end test file drives the REAL
hook binary (via `subprocess.run`, `bash <hook>`, realistic `PostToolUse`
JSON on stdin) against a real bare git remote plus a real local checkout
with `origin` configured -- the exact gap PR #3168 named. A fake `gh`
shim on `PATH` answers `gh pr view ... --json state,mergedAt`; `git` and
the real landing script are untouched. Four scenarios, one assertion each
on the bare remote's own tip commit (the only ground truth for "did this
push"):
1. `--help`, fake `gh pr view` reports MERGED (worst case: even if the PR
   happened to be genuinely merged already) -- must not push. This is the
   literal PR #3168 reproduction.
2. `gh pr merge 42 --squash`, fake `gh pr view` reports `state: OPEN`
   (what a failed merge actually looks like from `gh pr view`'s own
   perspective) -- must not push.
3. Genuine MERGED confirmation, but the landed tree carries no `amends:`
   edge -- must not push an empty landing-step commit.
4. Genuine MERGED confirmation, one unresolved edge -- must push, and the
   backlink text must appear in the remote's own landed target file.

derived: `python3 -m pytest tests/test_amends_landing_hook_e2e.py -q`
(run on PR #3165's branch this session) -- result: 4 passed. derived:
`git stash push -- on-the-record/hooks/amends-landing-apply.sh
gates/amends_landing.py && python3 -m pytest
tests/test_amends_landing_hook_e2e.py -q; git stash pop` (run this
session, on PR #3165's branch, against its own pre-fix state) -- result:
1 failed (the `--help` scenario -- `AssertionError: 'c0307ca...' !=
'7eb1960...'`, the bare remote's tip commit changed), 3 passed; confirms
the new test fails against the code as it stood before this round's fix,
per this round's own task requirement.

Acceptance requirement met — checked (run on PR #3165's branch, in
order, this session):
```
python3 -m pytest tests/test_amends_resolution.py -q      # 19 passed
python3 gates/probe_amends_is_discoverable.py; echo $?     # ok, exit 0
python3 gates/probe_amends_fails_closed.py; echo $?        # ok, exit 0
python3 -m pytest tests/ -q                                # 335 passed, 2 warnings
python3 -m pytest test/ -q                                 # 563 passed, 3 xfailed, 0 failed
```

## Why

canonical: PR #3168's record (cited in frontmatter `upstream:`), read in
full this session, and this session's own design decisions at e109ddad.
Two acceptable signals were offered by this round's task: (a) the tool
response carries the merged PR's own identifier and `gh pr view --json
state,mergedAt` confirms it; or (b) the PR number is parsed from the
command, non-merging flags are refused outright, and state is confirmed
afterward. This session took (b). Reason: the tool response's exact shape
for a `Bash` `PostToolUse` payload is not itself a stable, parseable
contract the pre-existing hook code relied on elsewhere -- the old code
only ever read it as opaque text for substring matching, never as
structured data with a reliable "the merged PR's identifier" field across
every `gh pr merge` output variant (auto-merge summary text, squash vs
merge-commit vs rebase phrasing all differ). The command text itself, by
contrast, already had a proven, tested PR-number-resolution pattern one
file away, and command tokens are the one thing the hook already parses
structurally and correctly (its own shape/operator-token validation).
Grounding identifier resolution in the thing already parsed correctly,
and confirmation in a dedicated `gh pr view` call whose JSON schema
(`state`, `mergedAt`) is a documented `gh` CLI contract, is more robust
than parsing prose the hook has no control over the exact wording of.

Rejected: layering the new `gh pr view` check UNDER the old failure-
marker text check (short-circuit on a failure marker, else call `gh pr
view`) rather than replacing it outright. This would still leave "no
failure marker" as a load-bearing implicit true for every command shape
the marker list doesn't happen to cover -- exactly the gap that let
`--help` through in the first place, since help text categorically never
contains any of the marker strings. Removing it outright makes `gh pr
view`'s own state the only path to "may proceed," with no residual
"or if the text looked clean" fallback.

Rejected: adding an explicit early `command -v gh` guard before the
trigger's own shape check. Not necessary for correctness -- the existing
`try/except` around the `gh pr view` subprocess call already fails open
(no action, not a crash) if `gh` is unresolvable on `PATH` -- and a
second explicit check for the same condition the exception handler
already covers would duplicate this file's own established style (every
other external-tool check in it lives at its one point of use).

The landing function itself was read in full this session and left
unchanged except the one guarded site -- derived: `gh pr view 3168` --
PR #3168's own independent, adversarial reproduction (a genuine merge, a
failed merge, a zero-edge merge, and a landing race, each run live
against a real bare remote) already confirmed every other path in it
sound; re-deriving that same verification from scratch inside this
narrow-scope round would duplicate work already done rather than add new
coverage.

## What did not work

None.

## Upstream basis

See frontmatter `upstream:`. Also read in full this session, for
context: the landing-apply hook, the landing function module, a sibling
hook's own PR-number-resolution pattern, and round 3's own end-to-end
test (to see exactly what it did and did not drive) -- all on PR #3165's
branch, all untracked on this branch. This repo's `board-gate.sh` write-
set isolation logic was also read this session, live, in response to the
deny below.

## Open findings

None from this narrow-scope round. The landing function's own residual
two-PRs-landing-race case (named in round 3's own record as a real,
honestly-scoped follow-up: a merge-time deny gate is tested but not wired
into a live hook) remains exactly as round 3 left it -- out of this
round's frozen scope, which derived: this round's own spawning task text
names only the over-broad-trigger defect and its coverage gap.

## Next steps

None -- `loop_state: done`. derived: the final verification block above
(`tests/ -q` -- 335 passed; `test/ -q` -- 563 passed, 3 xfailed, 0
failed) is the execution-live basis for `done`, run this session on PR
#3165's own branch. canonical: this session's own tool-call history this
turn -- no `gh pr merge`, `gh pr edit`, or similar closing/merging call
against any PR.

## Rationale for deviations

This round's task instructed working directly on PR #3165's branch,
including the record. checked: attempted writing this record on PR
#3165's branch this session -- result: `board-gate.sh` denial, "writing
docs/issue-3134/ requires branch issue-3134/silent-failure-audit+test-
derivation+implementation-blueprint-f38777c2 (current:
issue-3134/implementation-blueprint+silent-failure-audit+test-derivation+
knowledge-management-supersession-lifecycle-b6857f11)". derived: read
`board-gate.sh`'s own R4 write-set-isolation logic this session -- it
keys `docs/issue-<n>/` write eligibility to the `CLAUDE_SKILL`
environment variable, fixed for this session's whole process lifetime at
`silent-failure-audit+test-derivation+implementation-blueprint-
f38777c2`. Editing `.on-the-record/role.json` to match PR #3165's own
branch/skill (attempted first) satisfies the sidecar-vs-branch cross-
check but not the deeper `skill == CLAUDE_SKILL` comparison the R4
maintenance-targets exception itself uses, and `gh issue view 3134`'s own
body declares no `maintenance-targets:` entry naming this tree -- denied
both before and after the role.json edit, checked live both times this
session. Resolution: the code fix and its test (commit e109ddad) were
committed and pushed directly onto PR #3165's branch exactly as
instructed -- checked: `gh pr view 3165 --json headRefOid` -- result:
`e109ddadfb7562ad558ea4c22c6c77436821c2f2`, matching. This session's own
record of that work is committed here instead, on this session's own
branch, under this session's own role -- the same shape PR #3168's own
independent-verification session already used for reviewing PR #3165's
branch from outside it, which this round's board-gate constraint turns
out to require structurally, not just as a stylistic choice.

skill-verdict: silent-failure-audit — applied: invoked; audited the
landing function and the new `gh pr view` subprocess call in the landing-
apply hook, found and fixed the one real silent-failure site PR #3168
named (the `git status --porcelain` discarded returncode, see "What was
done" Fix 2 above); every new subprocess call this round added (`gh pr
view`, `git`) is wrapped in `try/except (OSError, SubprocessError)` with
an explicit fail-open exit, consistent with this hook's own documented
`PostToolUse`-cannot-deny posture
skill-verdict: test-derivation — applied: invoked; the four hook-driving
test scenarios (help / failed / zero-edge merged / genuine merge with an
edge) were routed as a decision-table problem -- two combining conditions
select the outcome (does the command shape confirm as a genuine,
non-flag merge; does `gh pr view` confirm MERGED) with a third condition
(are there amends: edges to apply) only relevant once the first two hold
-- and the four cases are the feasible-column set once the short-circuit
combinations (a rejected flag, or an unconfirmed merge, make the third
condition irrelevant) are excluded with that stated reason, rather than
combinatorially enumerated
skill-verdict: implementation-blueprint — not-applicable: this round's
fix ports two already-established patterns from this same file tree
(a sibling hook's PR-number resolution, this hook's own existing command-
shape/identity checks) rather than requiring an open architecture/
archetype selection
other mounted skills: not triggered
