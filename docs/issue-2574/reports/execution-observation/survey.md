# issue-2574 — execution-observation current-state survey

skill-verdict: work-in-english — applied: invoked; used to decide this
survey's and its sibling proposal's own language (English, matching
this repository's other execution-observation and implementation
records) versus the Korean the surrounding session directives are
written in.

Scout skip: no design decision is open here — this session verifies
already-landed code rather than proposing something new. Scout-protocol's
second mandatory skip condition applies ("the spec literally leaves no
design decision open"; `roles/specs/execution-observation.spec.json`'s
own `gate_c_status` says the same: mechanical aggregation, not
investigative finding). No scouting sweep was run.

## What issue #2574 asked for

canonical: `gh issue view 2574` (this session) — acceptance section,
quoted verbatim:
```
- check: an auto-spawned observer runs its git commands without an Approve signal — trigger the real `spawn_on_pr` path against a PR and quote the observer's output showing it proceeded
  must not: substitute a hand-typed spawn; the CLI path already works and is not the defect
- check: the divergence cannot recur silently — after the fix, show that a caller omitting the flag gets the same behavior as the CLI, or fails loudly; quote whichever it is
  must not: fix only the four call sites and leave the parameter default able to diverge again
- check: a genuinely two-phase spawn (`--two-phase`) still requires its Approve signal — run one and quote the denial
  must not: make everything build-now while fixing this
- check: all four call sites are named with their disposition — quote the grep
```
Plus an empty-state clause and a judgment call left open ("do observers
belong on the build-now path at all?"), resolved by an operator comment
on the issue (quoted below).

## What landed on `issue-2574/implementation` (PR #2578)

canonical: `gh pr view 2578 --json title,body,state,mergedAt,url` (this
session) —
```
state: OPEN
mergedAt: null
title: issue-2574: default _spawn_one() to single-phase so auto-spawned observers match the CLI
url: https://github.com/tokenmaxxxer/on-the-record/pull/2578
```
Not merged to `main` at observation time.

canonical: `git log --oneline origin/main..issue-2574/implementation`
(this session) —
```
1957cef8 issue-2574: capture no-per-category-carve-out quality-bar principle
ce86cc96 issue-2574: reconcile operator confirmation comment in the record
375d17a9 issue-2574: default _spawn_one() to single-phase so auto-spawned observers match the CLI
```

canonical: `git show --stat 375d17a9` (this session) —
```
docs/issue-2574/reports/implementation.md | 306 ++++++++++++++++++++++++++++++
gates/spawn_on_approve.py                 |  13 +-
gates/spawn_on_pr.py                      |  16 +-
lifecycle.py                              |  33 +++-
spawn.py                                  |  26 ++-
5 files changed, 384 insertions(+), 10 deletions(-)
```

The change: `_spawn_one()`'s own `single_phase` parameter default
(`spawn.py:2723`, unqualified name — was `False`, is now `True`), moved
to match the CLI's `effective_single_phase = not a.two_phase and not
a.checkpoint` computed at `spawn.py:2183` (unchanged). All four direct
callers now pass `single_phase` explicitly, judged per call site rather
than uniformly: `gates/spawn_on_pr.py`'s two auto-spawn sites and
`gates/spawn_on_approve.py`'s post-approval continuation get
`single_phase=True`; `lifecycle.py`'s watchdog-respawn path threads the
crashed session's own original `single_phase` value through a new
roster-entry field instead of a fixed value, so a crashed `--two-phase`
session cannot be silently promoted to build-now on restart. Every call
site carries a `이슈 #2574 disposition:` comment.

canonical: `gh issue view 2574 --json comments` (this session) — the
operator's confirmation comment (`issuecomment-5433139986`,
2026-08-27T01:21:04Z), quoted in relevant part:
```
Observers run single-phase. ... The first one is correct. Do not
deliberate it further and do not build a separate category for
observers ... every spawn path defaults to single-phase, whichever door
it came through ... `--two-phase` (and `--checkpoint`) remain the
explicit opt-in and still require their Approve signal ... observers get
no special case; they are simply not an exception to the default.
```
The implementation record reconciled this comment into its own "What
was done" section as an `amendments-reconciled:` line (canonical: `git
show ce86cc96` this session); this session confirms independently, from
the same `gh issue view` read, that the landed design
(`single_phase=True` at every direct call site, no per-role carve-out)
matches what the comment settled.

## Independent re-verification performed this session

acceptance: `git worktree add /tmp/v2574-worktree issue-2574/implementation`
(this session) — read-only worktree, no push, subsequently removed with
`git worktree remove /tmp/v2574-worktree --force`.

**Check 2 (shared default, AST-level, independent of `inspect.signature`
import).** derived: extracted `spawn.py` from `issue-2574/implementation`
via `git show`, parsed with Python's `ast` module (avoids importing the
module itself, which pulls in `deviation_log` and other package-relative
imports unavailable outside a full checkout) and located `_spawn_one`'s
`single_phase` parameter default directly in the AST — result:
```
single_phase default AST: Constant(value=True)
```
Also confirmed unchanged, `spawn.py:2183`:
```
effective_single_phase = not a.two_phase and not a.checkpoint
```
and the wiring that makes the shared default matter, `spawn.py:3410-3411`:
```
if single_phase:
    extra_env["CORE_BUILD_NOW"] = "1"
```

**Check 4 (all four call sites named), re-run against the landed tree,
not the implementation role's own scratch copies.** derived: `grep -n
"이슈 #2574 disposition" gates/spawn_on_pr.py gates/spawn_on_approve.py
lifecycle.py`, run against files extracted from `issue-2574/implementation`
via `git show issue-2574/implementation:<path>` — result:
```
gates/spawn_on_approve.py:249:        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰의
lifecycle.py:477:    # 이슈 #2574 disposition: 고정값 아님, 상속 — 두 호출부(watchdog-
lifecycle.py:518:    # 이슈 #2574 disposition: 고정값이 아니라 '상속' — 이 크래시한 세션이
lifecycle.py:557:    # 이슈 #2574 disposition: 고정값 아님, 상속 — `single_phase` 는 이
gates/spawn_on_pr.py:484:        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰은 이미
gates/spawn_on_pr.py:551:        # 이슈 #2574 disposition: single-phase(build-now) — 위
```
Six matches — `gates/spawn_on_pr.py` (2), `gates/spawn_on_approve.py`
(1), `lifecycle.py` (3: `_respawn_or_cap`'s own call site plus its two
callers `_auto_respawn_check`/`_self_trigger_respawn`). All four call
sites the issue named are covered. canonical: `git show
375d17a9:docs/issue-2574/reports/implementation.md` (read this session)
— its own "Acceptance evidence, check 4" section quotes only 5 lines
total (`spawn_on_pr.py` 2, `spawn_on_approve.py` 1, `lifecycle.py` 2 at
lines 515/554), one fewer than the 6 this session's own re-run above
just produced — omitting `lifecycle.py:477` — see "Discrepancy found"
below.

**Checks 1 and 3 (observer proceeds without Approve; `--two-phase`
still denies).** The implementation record's own live-harness script
for these two checks was ad hoc and deleted after that session (its own
stated "verify-at-landing convention, no persistent test file"), so this
session could not re-run the identical harness byte-for-byte. Instead,
confirmed the two structural facts that make the harness's claimed
result the only reachable outcome:

canonical: `on-the-record/hooks/approval-gate.sh` (read at this
session's own `HEAD`, `6f0c61ba`) lines 186-191:
```
if os.environ.get("CORE_BUILD_NOW") == "1":
    sys.stderr.write(
        "approval-gate: CORE_BUILD_NOW=1 — bypassing phase-2 approval check "
        "for issue-%d/%s write (%s).\n" % (issue, role, n)
    )
    sys.exit(0)
```
This bypass precedes every other check in the file (issue-open state,
approvers.md presence, APPROVE-comment scan) — confirmed by reading the
file in file order, this session. Combined with the `if single_phase:
extra_env["CORE_BUILD_NOW"] = "1"` wiring above and
`gates/spawn_on_pr.py`'s explicit `single_phase=True` at its two call
sites (quoted in the check-4 grep above), the mechanism checks 1 and 3
exercise end-to-end is independently verified at the source level. Full
behavioral re-run (spinning up an equivalent live harness) was not
attempted — this role's scope is to verify already-landed claims, not
to re-author a deleted verification harness from scratch absent a
specific reason to doubt the transcript, and no such reason surfaced.

**Regression check, independently re-run on both trees.** derived:
`python3 -m pytest test/ -q` inside `/tmp/v2574-worktree`
(`issue-2574/implementation`) — result:
```
13 failed, 251 passed in 2.45s
```
Same 13 failing test names the implementation record quotes
(`test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_local_dependency_env.py`). derived: the same command run directly
on this session's own branch (`issue-2574/execution-observation`, based
on pre-fix `main`, no diff applied) — result:
```
13 failed, 251 passed in 2.35s
```
byte-identical failing-test-name set. Independently confirms no
regression, without relying on the implementation record's own `git
stash` comparison.

## Discrepancy found: implementation record's check-4 quote undercounts

canonical: `git show 375d17a9:docs/issue-2574/reports/implementation.md`
(read this session, quoted verbatim above under "Check 4") — its
"Acceptance evidence, check 4" section quotes a 5-line grep result:
`spawn_on_pr.py` 2 hits, `spawn_on_approve.py` 1 hit, `lifecycle.py` 2
hits at lines 515/554. Re-running the identical command against the
actual landed tree (derived: grep output quoted above under "Check 4")
produces 6 lines — a third `lifecycle.py` hit at line 477, on
`_respawn_or_cap`'s own `_spawn_one()` call site. derived: `git show
375d17a9 -- lifecycle.py` (this session) confirms this third comment is
real code added in the same commit, not a citation artifact of this
session's own extraction method. The substantive acceptance requirement
— all four call sites named with their disposition — is still met, and
is in fact satisfied more thoroughly than the record's own quote shows
(one more explanatory comment, not one fewer). This is a
citation-accuracy defect in the implementation record's evidence quote,
not a functional defect in the shipped fix.

## Issue #2574's own state — a phase-2 board-eligibility blocker

canonical: `gh issue view 2574 --json state,stateReason` (this session)
— result:
```
state: CLOSED
stateReason: COMPLETED
```
Closed despite PR #2578 (which carries `Closes #2574`) still being
`OPEN`/`mergedAt: null` — GitHub did not auto-close it via merge; the
issue was closed some other way (an operator action, not investigated
further — out of this role's scope).

canonical: `sed -n '178,204p' on-the-record/hooks/approval-gate.sh` (this
session, read at `HEAD`) confirms the check order: the `CORE_BUILD_NOW=1`
bypass (quoted above) runs first; below it, before either approval-signal
path (a PR review Approve, or an issue comment exactly `APPROVE
issue-2574/execution-observation`) is evaluated, the file checks
`issue_state != "OPEN"` and denies unconditionally if so — the same
precondition order a prior execution-observation session documented for
the identical situation on issue #2180 (canonical: `git log --oneline
--all -- docs/issue-2180/reports/execution-observation/survey.md`, this
session, confirms that file's commit history on this repository).

canonical: `printenv | grep -i CORE_BUILD_NOW` (this session) — no
output; `printenv CLAUDE_ROLE` — `execution-observation`. No
`CORE_BUILD_NOW` stamp present in this session's own environment.

This session's task briefing states it was "PR 생성 시 자동 스폰됨
(spawn_on_pr.py)" (auto-spawned on PR creation) — exactly one of the two
`gates/spawn_on_pr.py` call sites this same issue's fix gives
`single_phase=True`. Had that fix already been deployed to the live
infrastructure enforcing *this* session's own gates (as opposed to
merely landed on an unmerged branch/PR in this git repository), this
session's environment should carry `CORE_BUILD_NOW=1`, and the
issue-state check above would never be reached at all. It is not present
— this session is, itself, encountering a live instance of the exact
observer-blocked-without-recourse shape issue #2574 describes, using a
closed issue in place of the issue's own PR-#650 example. This is
consistent with, not contradictory to, the fix under review: the fix
lives in this repository's `issue-2574/implementation` branch and an
open, unmerged PR (#2578) — it has not yet merged to `main`, let alone
propagated to whatever separately-deployed installation is currently
enforcing gates on this very session.

## Write surface this record actually needs

Only this role's own phase-2 record,
`docs/issue-2574/reports/execution-observation.md` (present in this
session's working tree, untracked — no prior commit on any branch has
staged it), plus the phase-1 docs this survey/proposal round itself
produces: this survey file itself, and a proposal file this session
writes next under `docs/issue-2574/proposals/` (untracked, created by
this session — no prior commit references it). No code path is touched
by this role.

Two independent denials this session, both carrying the same
approval-gate text quoted above under "Issue #2574's own state":

1. A `Write` tool call attempting to fill in
   `docs/issue-2574/reports/execution-observation.md` directly, this
   turn — denied before any content reached disk.
2. A `Bash` tool call whose command string contained the literal token
   `docs/issue-2574/reports/execution-observation.md` (a `cat` of that
   path, read-only, no write verb) — also denied. A `Bash` call with the
   same read-only content but no reference to that literal path string
   (e.g. `git status --short` alone) was not denied, matching an
   existing prior diagnosis of this same classifier on issue #2180
   (canonical: `git show --stat cbafba89 -- docs/issue-2180/reports/execution-observation/survey.md`,
   this session, confirms that survey file's own "Write surface"
   section, cited above, was committed to this repository's history):
   it string-matches the role's record-file token anywhere in the
   command line rather than distinguishing read verbs from write verbs,
   so any Bash command that merely mentions the path — even to read it
   — routes into the full execution-surface check.
