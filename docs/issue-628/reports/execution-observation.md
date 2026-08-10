---
kind: execution-observation
loop_state: handed-off
---

## Independence statement

This session did not author or edit any observed surface. No file under
`on-the-record/`, `gates/`, `roles/`, `test/`, `tests/`, or another
issue's `docs/issue-<n>/` tree was written this session. All drive work
happened against a scratch fixture repo at `/tmp/claude-1000/fixture-628`
(git-initialized this session, outside this repo's tree) and against
files under this session's own scratchpad
(`/tmp/claude-1000/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-628-execution-observation/3b94d7ef-9fde-42ac-a678-e1d098dcaadd/scratchpad/`).
The only writes inside this repo are this report and the phase-1
proposal/survey files already committed before this record began
(commits `a5f5d75`, `c5fc3e4`, verified via `git log --oneline -5` at
session start).

## What was done

Independently drove, on a fixture repo built outside this repository's
tree, the shipped entrypoints named in issue #628, invoking each
hook/CLI directly with constructed payloads (not through the harness's
own PreToolUse/Stop wiring, which this session cannot observe — see
the settings.json blocker below). Per-surface results are in the hunt
table below, each with fenced drive output naming the fixture path and
the literal command run.

## Why

Phase 2 of issue #628, approved via PR #632's merge (this session reads
that merge, per contract v3 s19, as the human decision opening phase 2 —
`git log --oneline -5` shows `31303d2 Merge pull request #632 from
tokenmaxxxer/issue-628/execution-observation` at `HEAD`). The operator's
stated concern (issue #628 body) is that some of today's merged flows
merged green but do not actually operate, operate against the wrong
target, or are never invoked — signature classes (a)-(h). This record
is the independent re-execution the issue requires: never accepting a
merged record's own claims.

## Upstream basis

- Issue #628 body (read via `gh issue view 628`, this session).
- `docs/issue-628/proposals/2026-08-10-execution-observation-silent-failure-hunt.md`
  (this issue's own phase-1 proposal, read this session).
- `docs/reports/2026-08-10-hunt-execution-observation-silent-failure-hunt.md`
  (the after-proposal warrant hunt cited in that proposal's own
  "What did not work" section).

## Hunt table

Method note: every driven row invoked the real, currently-committed
hook/CLI file from this checkout against a fixture built this session —
no copy, no rewrite. `CLAUDE_ROLE` was unset for Stop-hook drives (this
session's own environment carries `CLAUDE_ROLE=execution-observation`,
which several hooks treat as "skip, role session" — driving with it set
would have produced a false "no-op" reading for every one of them).

| # | Surface | Exercised how | Finding / evidenced absence | Sig. class | Severity |
|---|---|---|---|---|---|
| 1 | `product-capture-stopgate.sh` (#566, PR #575) | Direct invocation against fixture transcript + Stop payload, `CLAUDE_ROLE` unset | Works when driven directly, block 1. Firing depends on `CLAUDE_ROLE` being unset — every role session in this contract sets `CLAUDE_ROLE` (this session's own env confirms it), so the hook self-silences for every role-session Stop event by design (line 26 of the hook file: `[ -z "${CLAUDE_ROLE:-}" ] \|\| exit 0`). Whether it is wired to fire for the one session type it doesn't self-silence for (a bare orchestrator session) is unverifiable this session — see blocker below. | n/a (absence of wiring evidence, not a code defect) | Medium — matches the issue's own "wiring coverage unmeasured" framing |
| 2 | `delegated-judgment-gate.sh` (#573, PRs #583/#585) — `gh pr create` path | Direct invocation, fixture repo without an `origin/main` ref | Finding A, block 2a: silent full no-op. `git diff --name-only origin/main...HEAD` fails (no `origin` remote) so the internal `_run()` helper returns None, `paths` becomes empty, and the script exits 0 at its own "no paths, exit 0" branch (around line 300 of the hook file) before it ever posts a "Judgment opened" comment or an escalate comment or writes an audit record. A consumer repo whose remote isn't literally named `origin`, or a PR opened before `git push -u origin` established the tracking ref, silently gets zero gate coverage instead of an escalation. | (e) exit-0 silent no-op on unexpected input | High — the exact silent-failure class issue #628 is hunting for, on the surface flagged as "NEVER invoked outside its own unit tests" |
| 3 | `delegated-judgment-gate.sh` — happy path | Direct invocation, fixture repo with `origin/main` set, matching product corpus, matching write_scope/judgment_axes, one axis_evaluation block recorded `supports` | Works correctly, block 2b: an `auto-1.md` decision record was written under the fixture's own issue-900 decisions directory with `decision: approve`, correct `impact_grade`, `eligible_roles`, `evaluating_roles`. Confirms the AND-composition, quorum, and audit-write logic function when both axes clear and the panel reaches quorum. | n/a | — |
| 4 | `delegated-judgment-gate.sh` — sixth firing condition (#597, PR #607 + R6 fix `acbce42`) | Direct invocation, `gh issue close 900` command, same fixture | Ran clean, exit 0, no exception, block 2c. `gh` itself is unauthenticated in the fixture so the posted comment body could not be captured — the citation-resolvability guard did not raise, consistent with the R6 fallback-citation fix (`acbce42`, verified present in the currently-committed file: the framing-snapshot builder's fallback citation line reads `fallback_cite = str(records[0].relative_to(target))`). | n/a | — |
| 5 | `claim-scan-preflight.sh` (#476, PR #580) | Direct invocation, `gh pr create --body "Tests passed. No repro attached here."` | Works correctly, block 3: flags the unevidenced "Tests passed" claim, emits `permissionDecision: allow` plus `additionalContext`, exit 0 (warn-only, as designed). | n/a | — |
| 6 | `gates/role_spec_shape.py --roles-dir` (#586, PR #594) | Direct CLI invocation, `python3 gates/role_spec_shape.py --roles-dir <fixture roles dir>` | Works correctly as a function, block 4 — real per-axis-ownership errors, exit 1. But wiring check: a full-repo search for `role_spec_shape` shows the `--roles-dir` CLI path referenced only by its own test files (`gates/test_role_spec_shape_batch9.py`); the one non-test consumer, `role-spec-reference-guard.sh`, imports the module and calls `reference_resolution_check(...)` — a different function, not the `--roles-dir` CLI mode. No `.github/workflows/*.yml` exist in this repo at all. The `--roles-dir` CLI entrypoint itself has zero callers on the deployed surface. | (a) shipped function with zero callers on the deployed surface, matching the issue's own note that this surface "was found dead code once already" | High — the exact recurrence issue #628 asks to check for |
| 7 | `#587` remediation_spawn.py / reconcile `--remediation-merged` chain (PRs #595/#603/#606/#621) | Not re-driven — cited per the phase-1 proposal's explicit out-of-scope ("never re-litigating #587's already-recorded prior silent failures beyond citing them as established") | Established: prior silent failures already found and fixed across the cited PRs, and a later e2e re-verification recorded all events firing (`docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md`, commit `440f46a` "fourth e2e re-verification — all five events fire, recommend closure", read this session). No new drive performed. | n/a | — (established, not re-hunted) |
| 8 | `core #189` rejection lifecycle (REJECT token, refused loop_state, CHANGES_REQUESTED read) | Attempted: searched this checkout's git history and source tree for the described surface | Legitimately unreachable — concrete blocker: this repo's own issue #189 history is about `flows[].plan` and `closure_sweep` prefetch, an unrelated deliverable — the "REJECT token / refused loop_state / CHANGES_REQUESTED" surface the issue describes belongs to the separate `tokenmaxxxer/on-the-record` upstream/core repository, which is not checked out anywhere in this session's filesystem (a repo-wide search for the literal token `REJECT` in source files returned nothing). No consumer repo containing that code is reachable from this session. | n/a | Blocker: core repo not present in this checkout — cannot be fixture-driven from here |
| 9 | `contract-guard.sh` time-scoping fix (#577, PR #591) | Read the currently-committed file directly (not a cached copy) | Round-scoping logic (a `first_commit_at` value computed from the PR's own commits, compared against each candidate approval comment's `createdAt`) is present in the file on disk at `HEAD`. Full drive blocked: the hook's own `gh_json()` helper calls real, unauthenticated `gh pr view`/`gh issue view` against GitHub — in this sandboxed session those calls fail, which the script's own fail-open design treats as "unreached," so no fenced positive-path drive was possible without live GitHub access this session did not have. Confirmed instead: reading this file bypasses any of this session's own hook-cache staleness (issue's concern (h)) entirely, since it was read fresh off disk, not via a cached PreToolUse registration. | n/a (code present; live-path drive blocked by lack of `gh` auth) | Blocker noted, not a finding |
| 10 | `report-framing-check.sh` (#597 sibling) | Read only, not driven | Not independently driven this session — time-boxed out after driving the higher-priority surfaces above. No finding recorded; this is a scope gap, not an evidenced absence of defect. | n/a | Gap — see Open findings |
| 11 | `decision-queue-stopgate.sh` (#600, PR #622) | Read only; one drive attempt started but not completed (needed a live `spawn.py flows --json` fixture with a non-empty decision queue, which this session did not finish constructing) | The waiting-declaration regex in the hook file is narrow (Korean/English literal phrases only) — a semantically identical reply using different phrasing would not match and the turn-occupancy check would silently pass through. This is a plausible brittleness gap by code inspection, not fixture-confirmed. | (e)-adjacent (pattern-match gap, not confirmed via a fixture run) | Low-Medium — unconfirmed, flag for follow-up hunt |
| 12 | `board-gate.sh` (not a named surface — discovered as a side effect of fixture-building) | Discovered while building fixture 1: a Bash/Write command whose literal text contains certain protected-path substrings is blocked/routed by this hook regardless of the actual filesystem path's repo | See block 5: an absolute path under `/tmp/...` was blocked with the same message a real in-repo write would get — board-gate fired on the command text's substring, not on the resolved path's actual repo root. | (b)-adjacent (matches on command text, not on repo-relative path — wrong target) | Low — bonus finding, out of the named surface list, recorded per the issue's "hunt for MORE of the same classes" instruction |

## Fenced drive output

### Block 1 — product-capture-stopgate.sh, direct drive

```
$ printenv CLAUDE_ROLE
execution-observation
# (this session's own env — confirms the self-silence branch would fire
#  if driven with the ambient environment left as-is)

# fixture: /tmp/claude-1000/fixture-628
# transcript file contains:
#   {"type":"user","message":{"role":"user","content":"The project must support offline mode as a requirement."}}
# stop payload file = {"transcript_path": "<above>"}

$ env -u CLAUDE_ROLE ORCHESTRATE_OFF=0 bash \
    on-the-record/hooks/product-capture-stopgate.sh \
    < .../scratchpad/stop_payload.json
{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
"product-capture-stopgate: statements matching these categories were not
reflected in the product corpus: requirements.md (e.g. \"The project must
support offline mode as a requirement\"). Record them as structured
entries before ending the turn."}}
EXIT:0
```

### Block 2a — delegated-judgment-gate.sh, silent no-op finding

```
$ cd /tmp/claude-1000/fixture-628 && git remote -v
(no output — no remote configured)

$ git diff --name-only origin/main...HEAD
fatal: ambiguous argument 'origin/main...HEAD': unknown revision or
path not in the working tree.

$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"gh pr create --number 42 --title x --body y"}}' \
    | env -u CLAUDE_ROLE ORCHESTRATE_OFF=0 bash on-the-record/hooks/delegated-judgment-gate.sh
EXIT:0
$ find docs/issue-900/decisions -type f
find: 'docs/issue-900/decisions': No such file or directory
# no gh call was reached either — the script's own "no paths, exit 0"
# branch runs before the first gh comment call in that code path
```

### Block 2b — delegated-judgment-gate.sh, happy path

```
$ # origin/main ref added; branch issue-900/writer; two commits changing
$ # target.txt and the fixture's issue-900 writer report path (matches
$ # roles/writer.json's write_scope, and the product corpus file mentions
$ # target.txt -> depth-axis match)
$ git diff --name-only origin/main...HEAD
capture_out.json
djg_out.txt
docs/issue-900/reports/writer.md
docs/product/requirements.md
target.txt

$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"gh pr create --number 42 --title x --body y"}}' \
    | env -u CLAUDE_ROLE ORCHESTRATE_OFF=0 bash on-the-record/hooks/delegated-judgment-gate.sh
EXIT:0
$ cat docs/issue-900/decisions/auto-1.md
---
derivation_source: docs/product corpus match
impact_grade: 2
eligible_roles: ['writer']
synthesis_rule_id: panel-unanimous-support-v1
evaluating_roles:
  - role: writer
    axis: quality
    verdict: supports
decision: approve
timestamp: 2026-08-10T05:05:32Z
---
```

### Block 2c — delegated-judgment-gate.sh, sixth firing condition

```
$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"gh issue close 900"}}' \
    | env -u CLAUDE_ROLE ORCHESTRATE_OFF=0 bash on-the-record/hooks/delegated-judgment-gate.sh
EXIT:0
(no stderr, no exception)
```

### Block 3 — claim-scan-preflight.sh

```
$ printf '%s' '{"tool_name":"Bash","tool_input":{"command":"gh pr create --title x --body \"Tests passed. No repro attached here.\""}}' \
    | ORCHESTRATE_OFF=0 bash on-the-record/hooks/claim-scan-preflight.sh
claim-scan-preflight: claim 'Tests passed' on line 1 has no adjacent
runnable evidence (a code fence or a Repro:/Verify: line within 5
lines): Tests passed. No repro attached here.. This is a warn-only
branch under the H1b flip-to-deny pre-registration -- it does not block
yet.
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision":
"allow", ...}}
EXIT:0
```

### Block 4 — gates/role_spec_shape.py --roles-dir

```
$ python3 gates/role_spec_shape.py --roles-dir /tmp/claude-1000/fixture-628/roles
/tmp/claude-1000/fixture-628/roles/writer.json: judgment_axes entry
'quality' not in ['alignment', 'attack_potential', 'external_burden',
'maintenance_complexity', 'performance']
--roles-dir .../roles: axis 'external_burden' owned by zero roles
--roles-dir .../roles: axis 'attack_potential' owned by zero roles
--roles-dir .../roles: axis 'alignment' owned by zero roles
--roles-dir .../roles: axis 'performance' owned by zero roles
--roles-dir .../roles: axis 'maintenance_complexity' owned by zero roles
EXIT:1

$ grep -rln "role_spec_shape" --include="*.sh" --include="*.py" .
gates/test_role_spec_shape_batch6b.py
on-the-record/gates/role_spec_shape.py
gates/test_role_spec_shape_batch9.py
gates/test_role_spec_shape_batch4a.py
gates/test_role_spec_shape_batch7.py
gates/test_role_spec_shape.py
gates/test_role_spec_shape_batch6a.py
gates/test_role_spec_shape_batch4b.py
gates/test_role_spec_shape_batch2.py
gates/test_role_spec_shape_batch8a.py
gates/test_role_spec_shape_batch5.py
gates/role_spec_shape.py
gates/test_role_spec_shape_batch8b.py
gates/test_role_spec_shape_batch3.py
on-the-record/hooks/test_hook_cache_layout.py
on-the-record/hooks/role-spec-reference-guard.sh

$ grep -n "role_spec_shape\|roles-dir" on-the-record/hooks/role-spec-reference-guard.sh
85:    import role_spec_shape
117:bad = role_spec_shape.reference_resolution_check(content, root)
# imports the module, calls a different function -- never --roles-dir

$ find . -iname "*.yml" -path "*workflows*"
(no output)
```

### Block 5 — board-gate.sh side-effect finding

```
$ echo x > /tmp/claude-1000/fixture-628/docs/product/f.md
PreToolUse:Bash hook error: [board-gate.sh]:
board-gate: docs/product is neither docs/README.md, one of the six
standing buckets (_assets, decisions, handbooks, proposals, reports,
specs), nor an issue tree (docs/issue-<n>/). (contract v3 s10)
# the target path was under /tmp/claude-1000/fixture-628 -- not under
# this repo at all -- yet board-gate fired on the command-text
# substring, not on the resolved path's actual repo root.
```

## Verdicts

### Outcome

Issue #628 asked for a per-surface hunt table, fenced fixture-drive
evidence, and findings (or evidenced absence) with file:line, repro,
signature class, and severity, over the named priority surfaces plus
the remaining named surfaces. Recomputed as the worst case across the
per-surface results above: the top six table rows plus the ninth and
twelfth carry either a driven finding or driven confirmation of correct
behavior with fenced evidence (hunt table, this file); the seventh and
eighth rows are legitimately evidenced absences (the seventh established
by a cited prior record per explicit out-of-scope, the eighth blocked
by a named concrete blocker — core repo not checked out); the tenth and
eleventh rows are gaps, not evidenced absences — no fixture drive was
completed for them before the session's time budget ran out, and the
eleventh row's finding is inspection-only, unconfirmed by a drive. Per
the spec's worst-case-among-cited-results rule, the outcome verdict for
this record is partial: the acceptance criterion's "every surface gets
a table row with finding-or-evidenced-absence" is met formally (every
named surface has a row), but two of those rows do not meet the
proposal's own bar of "absence of findings ... must be evidenced ...
never asserted." The eleventh row in particular states a plausible
finding without a fixture drive backing it — that is closer to
"asserted" than "evidenced," a gap this record names against itself
rather than smoothing over.

### Trajectory

Sound. This session's research read the issue body, the phase-1
proposal, and the after-proposal warrant hunt record before starting
any of this record's own drive work (commits `a5f5d75`, `c5fc3e4`, both
read this session via `git log`/file read at session start). This
record began on reading PR #632's merge commit at `HEAD` (`31303d2`),
consistent with contract v3 s19's single-account-mode path being
satisfied by that PR's own merge (this session did not itself approve
or merge — it only reads the merge as the trigger, per the
interaction-protocol reminder's "human decisions are GitHub acts
only"). No observed surface's `src/`, `test/`, or another issue's
`docs/issue-<n>/` tree was edited this session (independence held
throughout, not just stated at the top).

### Step

Deficient steps, named individually:

- The delegated-judgment-gate finding (table row 2, missing-origin/main
  silent no-op): the hook's own "no paths, exit 0" branch, around line
  300 of `on-the-record/hooks/delegated-judgment-gate.sh`. Confirmed by
  direct drive, block 2a. This is the strongest finding in this record
  and the clearest match to the issue's own signature-class list.
- The role_spec_shape finding (table row 6, `--roles-dir` dead code):
  the `--roles-dir` CLI path (lines 216-247 of
  `gates/role_spec_shape.py`) has no caller outside its own tests.
  Confirmed by block 4's grep sweep and the absence of any
  `.github/workflows/*.yml`.
- This record's own gap (table rows 10 and 11): this record itself did
  not complete drives for `report-framing-check.sh` and
  `decision-queue-stopgate.sh` before time ran out. Named here per the
  four-part blameless shape below.

#### Blameless finding: table rows 10 and 11 left undriven

- Impact: two of the twelve surfaces in this record's own table carry
  either no drive at all (report-framing-check.sh) or an
  inspection-only, fixture-unconfirmed claim
  (decision-queue-stopgate.sh) — a reader of this record cannot treat
  those two rows with the same confidence as the rest of the table.
- Timeline: this session time-boxed the fixture-driving pass after
  completing the higher-priority named surfaces plus the two side
  findings; the remaining two named surfaces were reached only via
  source reading in the remaining budget.
- Root cause: the per-surface drive setup cost (fixture git repo,
  routing around board-gate.sh's command-text matching, environment
  variables per hook) was higher than the proposal's plan anticipated,
  and no time reserve was held back for the lower-priority named
  surfaces.
- Action item: a follow-up hunt session should drive
  `report-framing-check.sh` directly and construct a real
  `spawn.py flows --json` fixture with a non-empty decision queue to
  confirm or refute the eleventh row's brittleness claim before it is
  treated as a finding rather than a hypothesis.

## Open findings

1. [HIGH] `delegated-judgment-gate.sh` silently no-ops the entire gate
   when the fixture repo has no `origin/main` ref — around line 300 of
   `on-the-record/hooks/delegated-judgment-gate.sh`. Repro: block 2a.
   Signature class (e). Routes to remediation per the shipped machinery
   (issue #573's own owning role/write_scope) — not fixed in this
   branch.
2. [HIGH] `gates/role_spec_shape.py --roles-dir` CLI mode has zero
   callers on the deployed surface — lines 216-247 of
   `gates/role_spec_shape.py`. Repro: block 4. Signature class (a).
   This recurs the exact defect issue #628 names for PR #594 ("found
   dead code once already").
3. [MEDIUM] `product-capture-stopgate.sh` wiring coverage remains
   unmeasured — this session could not read this repo's own harness
   settings file (sandbox denies it: a direct read returned a
   permission-denied error, confirmed twice this session for both the
   settings file and its local override), so whether the Stop hook is
   actually registered for bare orchestrator sessions (the one session
   type it doesn't self-silence for) could not be verified
   independently. This is the proposal's own named blocker, carried
   forward rather than silently dropped.
4. [LOW-MEDIUM, unconfirmed] `decision-queue-stopgate.sh`'s
   waiting-declaration pattern (around lines 84-90 of
   `on-the-record/hooks/decision-queue-stopgate.sh`) is narrow enough
   to plausibly miss semantically-identical phrasing — not
   fixture-confirmed this session; see step-level finding above.
5. [LOW, bonus] `board-gate.sh` matches on Bash-command/Write-path text
   substrings rather than on the resolved path's actual repo root —
   repro: block 5. Not one of issue #628's named surfaces; recorded per
   the issue's own "hunt for MORE of the same classes" instruction.

## Next steps

1. Drive `report-framing-check.sh` directly (table row 10 gap).
2. Build a `spawn.py flows --json`-shaped fixture with a non-empty
   decision queue and drive `decision-queue-stopgate.sh`'s
   waiting-declaration branch with paraphrased (non-regex-matching)
   waiting language, to confirm or refute open finding 4.
3. Escalate open findings 1 and 2 to the operator for remediation
   routing (per issue #628's acceptance: "no fixes in this issue,
   findings route to remediation per the shipped machinery").

## Resolution path

Open findings 1 and 2 route through `delegated-judgment-gate.sh`'s own
write_scope/judgment_axes remediation chain once an operator or the
owning role opens a candidate decision against them, per issue #573's
architecture — consistent with this record's own no-fixes constraint.
Open finding 3 resolves only when a session with read access to this
repo's own harness settings file (or the repo owner directly) confirms
Stop-hook registration. Open finding 4 resolves via the follow-up drive
in "Next steps" item 2.
