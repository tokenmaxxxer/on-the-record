# Issue #846 — current-state survey

## Scope

Write set for the eventual fix: `on-the-record/hooks/retry-loop-bound.sh`,
`on-the-record/hooks/test_retry_loop_bound.py`, `docs/issue-846/reports`,
`docs/issue-846/proposals`. `on-the-record/hooks/merge-allow-gate.sh` and
`on-the-record/hooks/spawn-allow-gate.sh` are out of scope per the issue
body and are only read here for context, not edited.

## Where the cited hunt text actually lives (discrepancy worth flagging)

Issue #846 points to
`docs/issue-834/reports/implementation/2026-08-11-hunt-strict-spawn-allow-validation.md`
as the record carrying a `verdict: FINDING`, `kind: composition` stance with
the full repro.

canonical: `docs/issue-834/reports/implementation/2026-08-11-hunt-strict-spawn-allow-validation.md`,
this session's direct read (70 lines total) plus
`wc -l`/`grep -n "^## \|^Verdict"` on the same path
That file, as it exists on this branch and on `origin/main` today, carries
exactly one stance ("after-proposal — stance 0", `Verdict: NO FINDING`) —
no second stance is present in the committed file.

The `FINDING`/`composition` stance ("before-landing — stance 1: assume this
change and another plugin's rule cancel each other") is real, but it lives
only in the diff of `tokenmaxxxer/on-the-record` pull request #843, a PR
that never landed.
canonical: `gh pr view 843 --json state,mergedAt,mergeCommit,closedAt,baseRefName,headRefName`,
this session's direct call — reports `state: CLOSED`, `mergedAt: null`,
head `issue-834/implementation`. Issue #834's actual delivery commit is
`80426ea` ("issue-834: port strict shlex-based command-shape check into
spawn-allow-gate.sh (#842)"); that PR's diff does not include the hunt
file at all.

The stance-1 text — proposal path, hunt seed, cap/tier, the 3-step repro
script, and its observed output — is recoverable only through that PR's
file patch, not from any path currently in this working tree.
canonical: `gh api repos/tokenmaxxxer/on-the-record/pulls/843/files` filtered
to the hunt-file patch, this session's direct call. A later reader
following the issue's citation into this branch's copy of the file would
see only the `NO FINDING` stance. This survey reproduces stance-1's
finding independently below rather than relying on the unlanded text.

## Reproduction on this branch, before any fix

Ran the PR #843 stance-1 repro (recovered above), adjusted only for this
checkout's path, against `on-the-record/hooks/spawn-allow-gate.sh` and
`on-the-record/hooks/retry-loop-bound.sh` as they exist on this branch
today.

canonical: this session's own execution of the adapted 3-step repro
(command shown, output pasted verbatim below)
```
$ CMD='cd $(touch /tmp/pwned_poc_846)&&python3 spawn.py implementation "task" --issue 834'
$ bash on-the-record/hooks/spawn-allow-gate.sh <<< "$PAYLOAD"     # step 1
spawn-allow-gate exit: 0                        # empty stdout: no allow
$ # ...5x retry-loop-bound.sh post, simulating an unrelated gate's 5 denials...
$ bash on-the-record/hooks/retry-loop-bound.sh pre <<< "$PRE_PAYLOAD"   # step 3, 6th attempt
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
 "permissionDecisionReason": "retry-loop-bound: this exact Bash on 'cd $(touch /tmp/pwned_poc_846)&&python3 spawn.py implementation \"task\" --issue 834' has been denied 5 times this session with no change between attempts. ..."}}
pre exit: 0
```

`spawn-allow-gate.sh`'s strict shlex check withholds allow for this shape
(designed and landed for #834); `retry-loop-bound.sh`'s `pre` mode
independently supplies `permissionDecision: allow` on the 6th identical
attempt regardless, based only on the `(tool_name, command-string)` retry
count and the previous, unrelated denying gate's reason text. Current
behavior on this branch matches the composition defect the issue
describes.

## `retry-loop-bound.sh`'s current design

canonical: `on-the-record/hooks/retry-loop-bound.sh`, this session's direct
read, `pre` mode block (lines 181-227) and `_target()` (lines 130-138)
`count >= 2*K` denies outright (`exit 2`); the underlying gate is never
consulted again for that signature. `count >= K` writes one JSON object
combining `permissionDecision: "allow"`, `permissionDecisionReason`, and
`additionalContext` off the same string, unconditional on `tool_name`. For
a `Bash` call, `target` is the raw `tool_input["command"]` string — read
only to build the signature and to extract an `expected branch` substring
for the nudge text, never re-checked against the
`spawn.py`/`gh pr merge`-with-no-chaining-operator shape
`merge-allow-gate.sh`/`spawn-allow-gate.sh` care about.

## Why #507 chose `allow` at the K-th denial

canonical: `docs/issue-507/proposals/2026-08-08-retry-loop-bound.md`
(## Rationale section), this session's direct read
Built to answer #505's measurement that sessions burned 10+ minutes
retrying an identical denied write 22-52 times with no adaptation, even
though the denying gate's own message named the fix. The K-th `allow` is a
deliberate "let the retry through once, but hand it the corrective text"
choice over a pure abort, so the session does not have to burn a second
multi-minute storm just to notice the hint.

canonical: `docs/issue-507/reports/implementation.md` (## What was done,
## Upstream), this session's direct read
That design shipped as proposed and its approval trailer names
`APPROVE issue-507/implementation` on the issue thread.

canonical: `on-the-record/hooks/test_retry_loop_bound.py`, this session's
direct read (218 lines) plus
`grep -n 'TOOL = \|tool_name' on-the-record/hooks/test_retry_loop_bound.py`
```
28:TOOL = "Write"
```
No other `tool_name` literal appears anywhere else in the file — every
existing test function's `_post`/`_pre` call inherits `TOOL = "Write"`.
`docs/issue-505/reports/implementation.md` (lines 26-27, 47-70; #507's own cited
source) names an issue-474 `board-gate.sh` refusal on a `Write` and an
issue-147 refusal of the same shape; neither is a `Bash` command. #507's
proposal predates both `merge-allow-gate.sh` (issue #810) and
`spawn-allow-gate.sh` (issue #834) by issue number, and its own written
Constraints section describes only the `Write|Edit|MultiEdit|Bash`
matcher group as it existed at that time, with no `Bash`-scoped
allow-granting gate yet registered in it to compose against.

## Why `merge-allow-gate.sh`/`spawn-allow-gate.sh` never independently deny

canonical: `on-the-record/hooks/merge-allow-gate.sh` (header comment,
lines 1-27) and `on-the-record/hooks/spawn-allow-gate.sh` (header comment,
lines 1-35), this session's direct read of both, out of write set, not
edited
Each header states the hook "only ever ADDS a permission signal; it never
emits `deny` itself" — an unrecognized command shape falls through to
plain `exit 0` with no JSON, i.e. the same as if the hook were absent,
deferring to Claude Code's normal interactive-confirmation flow.
`merge-allow-gate.sh` lines 24-27 name the composition assumption this
issue's title turns on: "an existing deny gate's exit-code-2 on the same
call still wins over this hook's JSON allow *when both fire*" — the
qualifier is the exact gap `retry-loop-bound.sh`'s independent allow can
fall into once no other hook denies that specific call.

## `plan-order-guard.sh`'s fail-open (the repro's example unrelated denier)

canonical: `on-the-record/hooks/plan-order-guard.sh` (header comment,
lines 1-27), this session's direct read, out of write set, not edited
Denies a `spawn.py <role> ... --issue <n>` call that runs ahead of its
issue's declared plan order, resolved via `gh issue view --json body`; its
own comment states it "exits open, matching impact-guard.sh's
fail-open-on-ambiguity posture" on any `gh` lookup failure or unmatched
shape. Used in the repro purely as a realistic stand-in for "some
unrelated, state-dependent or fail-open gate denied this command 5 times,
then stopped" — per the issue's own Out of scope, the composition holds
for any gate with that shape, not specifically this one.

## Baseline suite state

canonical: `git rev-parse HEAD` and `git rev-parse origin/main`, this
session's direct run
```
ac9732a16c3bdc20c159ab472d126e6a76b08ad9
ac9732a16c3bdc20c159ab472d126e6a76b08ad9
```
Branch and `origin/main` are the same commit today, so a branch-vs-main
failure-set diff is trivially empty; this is the pre-change baseline the
eventual phase-2 delivery's post-change run compares against.

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
```
1222 passed, 2 skipped, 1 xfailed in 182.63s (0:03:02)
```

derived: `python3 -m pytest on-the-record/hooks/ -q`
```
268 passed in 53.64s
```

## Warrant hunt (after-proposal): is the `Bash`-only scope actually justified?

canonical: `docs/issue-846/reports/implementation/2026-08-11-hunt-narrow-retry-fatigue-allow-to-non-bash.md`,
after-proposal stance 0, this session's dispatch of `warrant:warrant-hunter`
The hunt returned `Verdict: FINDING`, `Kind: design-error`: the proposal's
draft Rationale asserted the risk "is specific to `Bash`" without checking
whether any `Write`/`Edit`/`MultiEdit`-scoped gate has the same shape as
`merge-allow-gate.sh`/`spawn-allow-gate.sh`. It reproduced
`retry-loop-bound.sh`'s K-tier `allow` firing for a `Write` call after five
denials from `approval-gate.sh` (a real, shipped, `Write|Edit|MultiEdit`
gate that documents its own fail-open path), landing on the same
"deliberately-withheld-allow gate gets overridden once it stops firing"
shape, just on `tool_name = "Write"` instead of `"Bash"`.

canonical: this session's own `grep -n "permissionDecision" on-the-record/hooks/{record-claim-guard,record-tiering-guard,role-spec-reference-guard,call-shape-guard,accumulation-claim-guard,approval-gate,deliverable-guard,retry-loop-bound}.sh`,
direct run
```
record-claim-guard.sh: 0
record-tiering-guard.sh: 0
role-spec-reference-guard.sh: 0
call-shape-guard.sh: 0
accumulation-claim-guard.sh: 0
approval-gate.sh: 0
deliverable-guard.sh: 0
retry-loop-bound.sh: 2
```
That resolves the finding rather than confirming it as a gap in the
proposed fix: `approval-gate.sh` denies or is silent — it never itself
emits `permissionDecision: "allow"` (its own header calls it "deny-only"),
and this grep (run against every hook `hooks.json` registers on the
`Write|Edit|MultiEdit` matcher — `retry-loop-bound.sh`'s own matcher line
plus the six-hook `Write|Edit|MultiEdit`-only group) shows `retry-loop-
bound.sh` is the *only* hook on that axis that ever emits
`permissionDecision` at all. So a `Write`/`Edit`/`MultiEdit` call has no
gate withholding a deliberate allow the way `merge-allow-gate.sh`/
`spawn-allow-gate.sh` do for `Bash` — when `approval-gate.sh` fails open,
there is no content-aware allow verdict being silently overridden, only
the same "unrelated gate stops denying, K-tier nudge lets the retry
through" behavior `#507` was built, tested, and approved to do. That is
exactly the composition the issue's own Out of scope section already
names generically ("상태 의존적이거나 fail-open 하는 어떤 게이트로도 같은
합성이 성립한다") and declines to ask this issue to fix. The hunt's
finding is real (the proposal's first draft asserted the `Bash`-only
scope instead of checking it) and is addressed here with the check it
asked for, not by widening the proposed fix — if a `Write`/`Edit`/
`MultiEdit`-scoped content-aware allow gate is added later, this same
grep is the check that would need to be re-run and, if it changes, this
scoping would need to widen with it.

## Judgment framing carried into the proposal

**Judgment 1 (keep `allow` at all?):** #507's own validated use (board-gate
wrong-branch, sandbox-scratchpad denials — see above) is entirely
`Write`-shaped; the design's value (teach instead of re-block) is grounded
in #505's measured retry storms. This issue's reproduction never
implicates that path. The composition risk is specific to `Bash`, the only
tool type any allow-granting content-aware gate exists for today. This
argues for keeping `allow` where it has always been used and never shown a
risk, and removing it only where the risk is reproduced.

**Judgment 2 (narrow scope, and where):** the issue names two placements —
the fatigue hook re-checking content itself, or a shared discriminator
function. A shared function needs `merge-allow-gate.sh`/
`spawn-allow-gate.sh` to expose or import it — both are frozen. Re-checking
content directly inside `retry-loop-bound.sh` (reimplementing the
`shlex`-based tokenize-then-check-operator-tokens test those two files
already own) creates a third independent copy of that same logic, exactly
the kind of copy this issue's own history shows can drift (#824's design
already needed a deliberate #834 port to reach a second file; a third,
independently-written copy inside a fatigue hook is more surface for the
same drift, not less). Neither offered placement is available without
touching a frozen file or duplicating its logic again. The proposal below
takes a third option not named in the issue text: scope the K-tier `allow`
branch out for `tool_name == "Bash"` categorically, keeping the
`additionalContext` nudge (a pattern `claim-scan-preflight.sh` already
uses on `PreToolUse` independent of any specific command match) for
`Bash`. This needs no knowledge of any specific gate's shape, cannot go
stale as the two named gates evolve or as new `Bash`-scoped allow-gates
are added later, and — per the test-coverage citation above — changes no
currently-tested behavior, since no existing fixture uses `tool_name =
"Bash"`.
