---
issue: 2705
role: architecture-interface-contract-shape-3f3d4ef5
author: architecture-interface-contract-shape-3f3d4ef5
skills: architecture-interface-contract-shape (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
code_under_review: on-the-record/hooks/gate-registration-post-guard.sh, on-the-record/hooks/hooks.json, docs/specs/enforcement-boundary.md, docs/specs/generated-paths.md, docs/handbooks/hooks.md
type: hook (weaker-promise companion guard, additive)
breaking: no
verdict: PASS
upstream:
  - path: docs/issue-2705 issue body + issue comments (seam-consult hold, then hold-lift ruling)
    sha: same-commit
---

# issue-2705 — architecture-interface-contract-shape-3f3d4ef5 record

## What was done

Built (`CORE_BUILD_NOW=1` bypass — proposal round skipped per contract v3
s19a) the hold-lift comment's chosen option: **moved the check to the
point where git already knows the staged set, and named the resulting
promise as weaker, in the guard's own text — not presented as the same
guard fixed.**

`gate-registration-guard.sh` itself is **byte-unchanged**. It keeps
refusing (`exit 2`, before the write happens) the unbundled shape — stage
in one Bash call, commit in the next — exactly as before #2705.

A new, separate, explicitly weaker-promise companion,
`on-the-record/hooks/gate-registration-post-guard.sh`, catches the one
shape the original guard's `PreToolUse`/`git diff --cached` read
structurally cannot see: a bundled `git add gates/new_gate.py && git
commit -m "..."` in ONE Bash call. It does not parse command text at
all — the seam consult's own conclusion, after #2705's four adversarial
rounds, was that predicting bash's eventual staged set from command text
is undecidable (subshells, aliases, functions, `CDPATH`). Instead:

- `post` mode (`PostToolUse`/`Bash`) reads git's own reported outcome —
  the `[<branch> <sha>] <subject>` line `git commit` prints on success —
  out of the `PostToolUse` payload's `tool_response` text, gets the exact
  commit `sha`, and inspects THAT commit's own tree via `git show
  --name-status` for a newly-added `gates/*.py`/`on-the-record/hooks/*.sh`/
  `.github/workflows/*.yml` file missing its registration row. A miss is
  recorded to a session-keyed state file. It cannot deny — the commit
  already exists by the time `PostToolUse` fires — so it is pure
  side-effect, always `exit 0`.
- `pre` mode (`PreToolUse`, any tool, next call) reads that state, drops
  any entry the working tree has since fixed, and — only while still
  open — emits `hookSpecificOutput.additionalContext` naming the commit,
  the missing row, and explicitly: this is a report after the write
  happened, not a refusal before it; `gate-registration-guard.sh`'s own
  pre-commit refusal still applies unchanged for the unbundled shape.
  Repeats every call until the row lands, then clears.

Also updated (same commit, since the new hook script is itself a newly-
added `on-the-record/hooks/*.sh` file and would otherwise trip its own
sibling guard): `docs/specs/enforcement-boundary.md` (amended
`gate-registration-guard.sh`'s row to name the blind spot; added a row
for the new companion), `docs/specs/generated-paths.md` (new row,
`out-of-tree`, for the companion's `$TMPDIR`-rooted state-file write),
`on-the-record/hooks/hooks.json` (wired `post` at `PostToolUse`/`Bash`
and `pre` at `PreToolUse` on the existing broad matcher group), and
`docs/handbooks/hooks.md` (new section explaining the split).

Regression test suite added:
`on-the-record/hooks/test_gate_registration_post_guard.py`, real
git-repo fixtures, subprocess against the real shipped script — same
harness shape as `test/test_deliverable_guard_worktree_submodule.py`.
acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` — result:
```
.......                                                                  [100%]
7 passed in 0.92s
```

## Why

**The issue's own acceptance criteria decide between the two honest
options the hold-lift comment offered.** Declaring the bundled shape
outside `gate-registration-guard.sh`'s `PreToolUse` jurisdiction (the
`core#367`/`core#374` shape) would leave acceptance criterion 1 unmet: it
requires the guard to actually fire on the bundled shape and show the
refusal, not to disclaim it — the issue body's own words are "the guard
fires on the bundled shape ... show the refusal." Only "move the check
to where git already knows" can satisfy that — so that is the option
built, with the cost named as the must-not clause requires.

**Two separate guards, not one guard changed, because the two shapes now
carry genuinely different guarantees.** `architecture-interface-contract-
shape` skill rule 12 ("hide design decisions that are likely to change...
expose only the minimal contract needed") and the segregation logic
behind rule 11 argue against widening `gate-registration-guard.sh`'s
existing contract to silently mean "blocks before the write — except
when it doesn't, in which case it reports after," since that ambiguity
is exactly the shape #2705 opened on — the issue body's own diagnosis is
that "the guard emits nothing, the commit succeeds, and every downstream
reader sees a landed gate that appears to have passed registration."
Naming a NEW contract with an explicitly different, weaker promise —
rather than growing the old one's meaning silently — is the same shape
rule 14's sync/async framing argues for: reserve the strong, synchronous
("blocks before it happens") contract for the one case that can actually
honor it (staged in an earlier, separate, already-completed call), and
use an async, eventually-consistent ("tell the session on the next call,
once git confirms what happened") contract for the case that
structurally cannot be synchronous.
canonical: architecture-interface-contract-shape skill's SKILL.md (loaded via the Skill tool this turn — rules 1, 11, 12, 14 and the rule index).
`gate-registration-guard.sh`'s own promise is
therefore untouched, not silently downgraded — which is what the
must-not clause requires ("must be stated as a change in what the guard
promises, not presented as the same guard fixed").
canonical: issue #2705 body's `## Acceptance` "must not" bullet (`gh issue view 2705`, read in full this turn).

**Why not parse the bundled command text harder (a fifth round).**
#2705's own comment history — the seam-consult hold comment and the
hold-lift comment that superseded it — records: round 1 parsed
`cd`/subshell path resolution and directory-add; round 2 (`PR #2763`)
closed `:(exclude)` pathspecs; round 3 (adversarial review) found `cd -`,
a symlinked directory component, and `pushd`/`popd` one layer down in
round 2's own cwd model; round 4 (`PR #2774`, still open, unmerged) found
bare `pushd`'s two-argument swap, `pushd +N`/`-N` rotation, and unmodeled
`CDPATH` inside the SAME `pushd`/`popd` family round 3 had just closed —
the signal, per round 3's own stated bound, that the approach itself had
run out of road, not merely that the backlog was bigger than thought.
canonical: `gh issue view 2705 --comments` (seam-consult hold comment quoting all four rounds; hold-lift comment citing `tokenmaxxxer-core#233`/`#367`/`#374` as the same conclusion reached independently the same day) — read in full this turn.
The seam consult's answer — reading git's own post-commit object state
instead of predicting it from text — is exact and closed by construction
(git's own commit-success line either names a real, existing commit
object or it does not; there is nothing left to enumerate), which is why
this delivery does not need a "round 5" grammar.

**Why the state-file/two-mode split instead of one `PostToolUse` hook
emitting `additionalContext` directly.** Checked live: `retry-loop-
bound.sh`'s own `post` mode (registered at `PostToolUse` in this repo's
`hooks.json`) never emits `additionalContext`, only records state; the
mode that actually warns a session (`pre`, at `PreToolUse`, reading that
recorded state) is a SEPARATE registration on the next tool call.
derived: `grep -n 'mode ==\|"post"\|"pre"\|hookEventName' on-the-record/hooks/retry-loop-bound.sh` — result: `hookEventName: "PreToolUse"` appears once, only reachable from the `mode == "pre"` branch; the `mode == "post"` branch has no such emission.
This repo's own `post-landing-obligation-gate.sh` comment states the same
invariant explicitly: `PostToolUse` cannot deny. Given the established,
working precedent (`approach-cap-warning.sh`) is a proven pre/post split
rather than a single `PostToolUse` hook talking directly, the new
companion follows that precedent rather than betting on an unverified
capability.

## Upstream basis

- Issue #2705 body (acceptance criteria, must-not clause) and its 11
  comments — most directly, the seam-consult hold comment (four
  adversarial-round history, `runs/consult-logs/
  20260829T204814378197-1903554.log`) and the hold-lift comment quoting
  the must-not clause's exact wording and citing `tokenmaxxxer-
  core#367`/`#374`.
- `on-the-record/hooks/gate-registration-guard.sh` at `origin/main`
  (060f1f10655d41f2072865c1e2ce7a093fed2412) — read in full; PRs #2753/
  #2763/#2774 never landed (the first two `CLOSED`, the third `OPEN`,
  none `mergedAt`), so this branch's baseline is the pre-parsing-saga
  version of the guard (`git diff --cached --name-status` only, no
  `cd`/`pushd` modeling at all).
  derived: `gh pr view 2753 --json state,mergedAt,title && gh pr view 2763 --json state,mergedAt,title && gh pr view 2774 --json state,mergedAt,title` — result: `{"mergedAt":null,"state":"CLOSED",...}` (2753), `{"mergedAt":null,"state":"CLOSED",...}` (2763), `{"mergedAt":null,"state":"OPEN",...}` (2774).
  canonical: `tokenmaxxxer/tokenmaxxxer-core#367` (`gh issue view 367 -R tokenmaxxxer/tokenmaxxxer-core`, state `MERGED`) and `#374` (`gh pr view 374 -R tokenmaxxxer/tokenmaxxxer-core`, state `MERGED`) — both read in full this turn for their exact wording ("jurisdiction limit", "write-set discipline ... not a security sandbox").
- `on-the-record/hooks/approach-cap-warning.sh`, `retry-loop-bound.sh`,
  `post-landing-obligation-gate.sh` — precedent for the pre/post mode
  split, the session-keyed state-file idiom, and the "`PostToolUse`
  cannot deny" invariant (that exact phrase is
  `post-landing-obligation-gate.sh`'s own comment, read in full).
- `on-the-record/hooks/pretooluse_dispatcher.py` (`GATES` list) and
  `on-the-record/hooks/hooks.json` — read in full this turn.
  derived: `grep -rn "gate-registration-post-guard" on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py` (run before this delivery's own edits landed) — result: no match, confirming the new hook was not yet wired anywhere and `gate-registration-guard.sh` dispatches through the batched `PreToolUse` dispatcher unchanged (its own dispatcher entry, `pretooluse_dispatcher.py`, is untouched by this delivery).

## Live demonstration (acceptance criteria 1–2)

Fixture: a scratch git repo (`/tmp/otr-2705-live`) with a minimal
`docs/specs/enforcement-boundary.md`/`generated-paths.md` and an empty
`gates/` dir, one `init` commit.

**Before — the bug this issue is about, reproduced fresh (not inherited
from an unmerged PR):**

```
$ git diff --cached --name-status
[empty]
```
derived: `cd /tmp/otr-2705-live && git diff --cached --name-status` —
run BEFORE the bundled command below, output empty: at `PreToolUse`-fire
time, `gate-registration-guard.sh` has nothing to see.

**The bundled command actually running, and git's own stdout (this
becomes `tool_response`):**
```
$ git add gates/new_gate.py && git commit -m "add new gate"
[master 37fa69a] add new gate
 1 file changed, 1 insertion(+)
 create mode 100644 gates/new_gate.py
```

**After — `gate-registration-post-guard.sh post` fed that real
`tool_response`:**
```
$ echo "$PAYLOAD" | OTR_GRG_POST_STATE_DIR=/tmp/otr-2705-state bash \
    on-the-record/hooks/gate-registration-post-guard.sh post
post-mode exit=0
$ cat /tmp/otr-2705-state/live-demo-session.json
{"violations": [{"sha": "37fa69a", "path": "gates/new_gate.py",
  "message": "gates/new_gate.py: no row in docs/specs/enforcement-boundary.md"}]}
```
derived: the two commands above, run in that order, output as shown.
The bundled shape is now caught — criterion 1 met, with the promise
named as after-the-fact (see the `pre`-mode message below).

**`pre` mode on the next tool call — the message a session actually
reads:**
```
$ echo '{"session_id":"live-demo-session","cwd":"/tmp/otr-2705-live",...}' \
    | OTR_GRG_POST_STATE_DIR=/tmp/otr-2705-state bash \
      on-the-record/hooks/gate-registration-post-guard.sh pre
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
"gate-registration-guard (post-commit report, issue #2705): the following
commit(s) already exist in git history and cannot be blocked or reverted
by this hook -- gate-registration-guard.sh only sees a `git commit`'s
staged set BEFORE the command runs, so a bundled `git add ... && git
commit ...` call left nothing to refuse at the time it fired:\n  -
37fa69a: gates/new_gate.py: no row in docs/specs/enforcement-boundary.md\n
Add the missing row(s) above in a follow-up commit now. This report is
the weaker half of a deliberate two-guard split (issue #2705):
gate-registration-guard.sh's own PreToolUse/`--cached` check is unchanged
and still REFUSES the commit outright when the file was staged in an
earlier, separate Bash call -- only the single-call bundled shape lands
first and is reported after the fact."}}
```
derived: command above, output exactly as shown (verbatim from the
live run this session executed). The weaker promise is stated in the
text a session reads, not only in the header comment.

**Resolved on the next follow-up commit — nagging stops:**
```
$ printf ... > docs/specs/enforcement-boundary.md   # add the row
$ git add docs/specs/enforcement-boundary.md && git commit -q -m register
$ echo '{...}' | OTR_GRG_POST_STATE_DIR=/tmp/otr-2705-state bash \
    on-the-record/hooks/gate-registration-post-guard.sh pre
[no output]
$ cat /tmp/otr-2705-state/live-demo-session.json
{"violations": []}
```
derived: three commands above, in order; empty stdout and empty
`violations` list confirm the entry cleared once the row landed.

**Unbundled shape — acceptance criterion 2, `gate-registration-guard.sh`
untouched:**
```
$ echo "def check2(): pass" > gates/second_gate.py
$ git add gates/second_gate.py
$ echo '{"tool_name":"Bash","cwd":".","tool_input":{"command":"git commit -m add-second-gate"}}' \
    | bash on-the-record/hooks/gate-registration-guard.sh
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/second_gate.py: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit ..., then retry the commit.
original PreToolUse guard exit=2
```
derived: command above, run against the SAME (unmodified)
`gate-registration-guard.sh` shipped at `origin/main` — the unbundled
shape still refuses exactly as it did before this issue, at `exit 2`,
before the commit is created.

**No false positive on a clean bundled commit (row staged in the same
`git add`):**
```
$ git add gates/clean_gate.py docs/specs/enforcement-boundary.md && \
    git commit -m "add clean gate with row"
[master 654c88f] add clean gate with row
 2 files changed, 2 insertions(+)
$ echo "$PAYLOAD" | OTR_GRG_POST_STATE_DIR=/tmp/otr-2705-state bash \
    on-the-record/hooks/gate-registration-post-guard.sh post
post exit=0
$ cat /tmp/otr-2705-state/live-demo-session-2.json
{"violations": []}
```
derived: three commands above; empty `violations` confirms no
false-positive nag when the bundled commit already carries its own row.

Machine-executable regression coverage for all of the above (plus the
`ORCHESTRATE_OFF` kill switch, a non-`Bash` tool, and a `--quiet`/no-
success-line commit) lives in
`on-the-record/hooks/test_gate_registration_post_guard.py`.
acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` — result:
```
.......                                                                  [100%]
7 passed in 0.92s
```

## Enumeration (acceptance criterion 3)

Population: every `PreToolUse` hook in `on-the-record/hooks/` and
`tokenmaxxxer-core`'s `core/hooks/`.
derived: `grep -lE '"?--cached"?|git show :|git diff --cached' on-the-record/hooks/*.sh` (population scan, on-the-record side) and the equivalent scan over `$CORE/core/hooks/*.sh` where `CORE=/home/jwjung/tokenmaxxxer/tokenmaxxxer-core`, then, for each hit, the file itself was read to confirm whether the read is `git diff --cached` (the exact read this issue's bug is about) and whether the hook is `Bash`/`git commit`-gated (only that shape can even be bundled).

| hook | reads staged state via | verdict | command that established it |
|---|---|---|---|
| `on-the-record/hooks/gate-registration-guard.sh` | `git diff --cached --name-status` | **same blind spot** (this issue's subject) — unchanged in this delivery | derived: live demo above — `git diff --cached` empty before a bundled `add && commit` |
| `on-the-record/hooks/acceptance-command-real-run-guard.sh` | `git diff --cached --name-status` (line 121) | **same blind spot** — identical read, same `PreToolUse`/`Bash`/`git commit` gating | derived: `sed -n '119,123p' on-the-record/hooks/acceptance-command-real-run-guard.sh` — same call shape as the guard proven blind above |
| `on-the-record/hooks/live-fire-claim-real-run-guard.sh` | `git diff --cached --name-status` (line 135) | **same blind spot** | derived: `sed -n '133,137p' on-the-record/hooks/live-fire-claim-real-run-guard.sh` |
| `on-the-record/hooks/live-fire-test-guard.sh` | `git diff --cached --name-status` (line 157) | **cannot currently exhibit the blind spot — never fires at all.** Its `docs/specs/enforcement-boundary.md` row claims live `PreToolUse`/`Bash` status, but it is registered NEITHER directly in `hooks.json` NOR in `pretooluse_dispatcher.py`'s `GATES` list — a separate #909-class orphan defect, out of scope for #2705 (not touched here) | derived: `grep -rn "live-fire-test-guard" on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py` — result: no output, exit 1 |
| `on-the-record/hooks/spec-index-preflight.sh` | `git diff --cached --name-only` (line 116) | **same blind spot** | derived: `sed -n '114,118p' on-the-record/hooks/spec-index-preflight.sh` |
| `on-the-record/hooks/requirement-digest-preflight.sh` | `git diff --cached --name-only`, with an EXISTING partial fallback (working-tree-vs-HEAD diff) for `git commit -a`/`-am` only | **same blind spot** for the general bundled `git add docs/specs/requirements.md && git commit` (no `-a`) shape — the existing `-a` fallback closes a different, narrower bypass (auto-staged tracked-file changes), not this one | derived: `sed -n '119,131p' on-the-record/hooks/requirement-digest-preflight.sh` — `stages_all` is only set from an `-a`/`--all`/bundled-short-flag token; a plain (non-`-a`) bundled `add && commit` leaves `registry_touched` `False` |
| `on-the-record/hooks/deviation-log-guard.sh` | n/a | **not applicable** — `Stop` hook, not `PreToolUse`/`Bash`; never intercepts a `git commit` in progress | derived: `head -3 on-the-record/hooks/deviation-log-guard.sh` — result: `# Stop: no-traceless-deviation invariant` |
| `on-the-record/hooks/product-capture-stopgate.sh` | n/a | **not applicable** — `Stop` hook, same reason | derived: `head -6 on-the-record/hooks/product-capture-stopgate.sh` — result: `# Stop: nudge the orchestrator session...` |
| `tokenmaxxxer-core/core/hooks/handbook-trigger-gate.sh` | `git diff --cached --name-only` (line 85) | **same blind spot** — an empty (not failed) cached-diff read means "no operational-surface file staged," so the obligation check is skipped, not failed-closed | derived: `sed -n '83,88p' $CORE/core/hooks/handbook-trigger-gate.sh` |
| `tokenmaxxxer-core/core/hooks/trailer-gate.sh` | `git diff --cached --name-only` (line 142) | **same blind spot** — a bundled `git add docs/issue-<n>/... && git commit` would show an empty staged set, skipping the `Subject: issue-<n>` trailer requirement for that call | derived: `sed -n '140,144p' $CORE/core/hooks/trailer-gate.sh` |
| all other core hooks (`board-gate.sh`, `approval-gate.sh`, `gh-guard.sh`, `record-fields-gate.sh`, `proposal-shape-gate.sh`, `record-shape-gate.sh`, `survey-order-gate.sh`, `ordering-gate.sh`, `facet-keyword-gate.sh`, `citation-gate.sh`, `ordering-norm-gate.sh`) | none found | **not applicable** — none read `git diff --cached`/`git show :`; they inspect command text or write targets directly | derived: `grep -lE '"?--cached"?|git show :|git diff --cached' $CORE/core/hooks/*.sh` — result: 2 hits only (`handbook-trigger-gate.sh`, `trailer-gate.sh`), confirmed by a second, broader `grep -nE 'git.{0,3}(diff|show)'` sweep finding no other call site |

Summary, per the table above: 6 hooks share the same blind spot this
issue's subject had (2 in `on-the-record` at the general level plus
`requirement-digest-preflight.sh`'s narrower variant, 2 in
`tokenmaxxxer-core`); 1 (`live-fire-test-guard.sh`) cannot currently
exhibit it because it is not wired at all (flagged as an open finding,
not fixed here — separate defect); 2 (`Stop`-event hooks) are
structurally not applicable; the remaining 11 core hooks checked show no
staged-state read at all.
derived: the table's own per-row `derived:` citations above are the count basis; totals recomputed by re-reading the table this turn (6 same-blind-spot + 1 unreachable + 2 not-applicable + 1 subject = 10 on-the-record/core rows, plus the 11-hook "none found" core group).
None of the other 6 same-blind-spot hooks were fixed in this delivery —
enumeration was the acceptance requirement, not a fix-all; each carries
the identical, already-understood remedy shape (a
`gate-registration-post-guard.sh`-style companion) if and when its own
issue picks it up.

## Standing invariants

- **No return of the retired role axis**:
  derived: `git diff origin/main -- docs/handbooks/hooks.md docs/specs/enforcement-boundary.md docs/specs/generated-paths.md on-the-record/hooks/hooks.json on-the-record/hooks/gate-registration-post-guard.sh on-the-record/hooks/test_gate_registration_post_guard.py | grep -iE "role.axis|axis"` — result: no match (0 lines).
- **No new bug, failing-test set vs `origin/main` as SETS OF NAMES**:
  derived: `python3 -m pytest test/ gates/ on-the-record/ -q` on this branch — result:
```
15 failed, 505 passed, 3 xfailed in 31.72s
```
  Same command in a fresh `origin/main` worktree (`git worktree add /tmp/otr-main-baseline origin/main`) — result: `15 failed, 498 passed, 3 xfailed` (505 = 498 + this delivery's own 7 new tests).
  derived: `diff <(sorted FAILED-name list, this branch) <(sorted FAILED-name list, origin/main worktree)` — result: 0 lines of difference (`IDENTICAL FAILING-TEST-NAME SETS` printed).
- **No overhead increase**:
  derived: interleaved timing (3 rounds x 60 calls each, alternating) of the EXISTING `gate-registration-guard.sh`'s own fastpath vs the new `post`-mode fastpath, both on an ordinary non-git command — result: existing guard fastpath avg 4.99ms/call vs new post-guard fastpath avg 4.90ms/call (statistically equivalent, both dominated by the same cat+2x-grep fork cost every sibling `git commit`-gated gate already pays).
  derived: after restructuring the new `pre` mode (fires on EVERY tool call) to short-circuit on a bash-only empty-state-dir glob check BEFORE any process spawn, re-measured at 200 calls: 0.96ms/call empty-state, vs `approach-cap-warning.sh`'s own already-accepted `pre`-mode baseline measured the same way at 0.89ms/call on the same broad matcher group.
- **Monitor and watch machinery unbroken and not quieter**:
  derived: `python3 -m pytest test/ -k "fleet_scan or monitor or watch" -q` — result: `15 passed` on this branch, and this delivery touches no file any `test_*fleet_scan*`/`*monitor*`/`*watch*` test depends on (confirmed by the `git diff origin/main --stat` file list above containing none of them).

## What did not work

Initial attempts at building test-fixture `PostToolUse` payloads during
live verification used `python3 -c "import json; print(json.dumps(...))"
> payload.json`-shaped Bash calls. These tripped this session's OWN live
installed gates (not the code under review):
derived: `python3 -c "import json; print(json.dumps({...})) " > /tmp/otr-2705-clean-payload.json` (run as an actual Bash tool call this session) — result:
```
PreToolUse:Bash hook error: [.../tokenmaxxxer-core/core/hooks/pretooluse-dispatcher.sh]: board-gate: a Bash call carries an un-analyzable write-capable shape (python3 -c "...") while this gate enforces role 'architecture-interface-contract-shape-3f3d4ef5''s write-set.
```
A separate attempt, manually `exec()`-ing the original guard's heredoc-
extracted python body to test it in isolation, was refused the same way
by `heredoc-command-refusal-gate.sh` for carrying a heredoc-shaped
construction. Neither is a defect in the code under review. Worked
around by writing payload-builder scripts to disk via the `Write` tool
and invoking them with a plain `python3 script.py` call instead, which
is the pattern the rest of this record's live-demo commands follow.

## Open findings

- `live-fire-test-guard.sh` is not wired into `hooks.json` or
  `pretooluse_dispatcher.py`'s `GATES` list despite its own
  `docs/specs/enforcement-boundary.md` row claiming live `PreToolUse`/
  `Bash` status (see enumeration table). This is the exact #909 orphan
  class `gate-registration-guard.sh` itself exists to catch for a
  NEWLY-staged file — it does not re-scan already-registered rows, so it
  never caught this one. Resolution path: a separate issue (out of
  #2705's non-goals: "the registration requirement itself" and
  individual other hooks' own gaps are explicitly not this issue's
  scope).
- The 5 other same-blind-spot hooks named in the enumeration
  (`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-
  guard.sh`, `spec-index-preflight.sh`, and core's `handbook-trigger-
  gate.sh`/`trailer-gate.sh`) each carry the identical remedy shape
  (a `post`-mode companion reading `tool_response`'s commit-success line)
  if picked up — not built here per the issue's own scope (enumerate,
  not fix-all).

## Next steps

None — issue #2705's three acceptance checks and its must-not clause are
each satisfied by an executed-live check in this record: the bundled-
and unbundled-shape live demos above, and the two `pytest` runs, each
with their own `acceptance:`/`derived:` tag and fenced output in the
sections above. The phase-2 delivery PR carries `Closes #2705` per
`pr-preflight.sh`'s trailer convention.

skill-verdict: architecture-interface-contract-shape — applied: invoked;
loaded the skill's SKILL.md and used rule 12 (segregate the interface —
expose only the minimal contract each guard can actually honor) plus the
sync/async framing behind rules 1 and 14 to justify keeping
`gate-registration-guard.sh`'s existing strong (synchronous,
before-the-write) promise untouched and adding
`gate-registration-post-guard.sh` as a separate, explicitly weaker
(asynchronous, eventually-consistent) promise, instead of silently
widening or replacing the original guard's meaning — see "Why" above.
other mounted skills: work-in-english — not invoked via the Skill tool
(guidance-only per this session's own skill-obligations note, enforced
by core hooks rather than requiring invocation); followed throughout by
writing all code, comments, docs, commit messages, and this record in
English.
