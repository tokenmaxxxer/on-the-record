---
issue: 2670
role: adversarial-review+silent-failure-audit-6014566c
author: adversarial-review+silent-failure-audit-6014566c
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true
code_under_review:
  - path: on-the-record/hooks/approval-gate.sh
    sha: same-commit
  - path: pipeline.py
    sha: same-commit
type: review
breaking: false
verdict: Independent verification of on-the-record#2710 + tokenmaxxxer-core#348 (the CLAUDE_ROLE->CLAUDE_SKILL rename). Claims 2, 4, 6 PRESENT; Claim 5 PRESENT for core, partial for on-the-record; Claim 3 PARTIAL (gate pass/refuse pairs confirmed, literal nested spawn-to-PR disclosed as not done). Claim 1 (load-bearing safety claim) PARTIALLY PRESENT WITH A GAP -- core's two named gates crash-loud as claimed, but on-the-record's own approval-gate.sh has an un-mirrored silent no-op path neither PR's record discusses. See Open findings #1.
loop_state: terminal
upstream:
  - path: https://github.com/tokenmaxxxer/on-the-record/pull/2710
    sha: e4393321fdf6ff38f27c9478934ac9849aa6048f
  - path: https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/348
    sha: 434cfdd597ea3abe9129bc61896d122cc3ce631b
---

# issue-2670 — adversarial-review+silent-failure-audit-6014566c record

## What was done

Independent verification of `tokenmaxxxer/on-the-record#2710` (write side + on-the-record's own read side) and `tokenmaxxxer/tokenmaxxxer-core#348` (core's read side), the two companion PRs implementing #2670.
canonical: `gh pr view 2710 --json state,mergeStateStatus,mergeable,reviews` — result: `{"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE","reviews":[]}`, `state: OPEN`; `gh pr view 348 -R tokenmaxxxer/tokenmaxxxer-core --json state,reviews` — result: `state: OPEN`, `reviews: []`. Both PRs unmerged at review time.
canonical: this session's own `printenv CLAUDE_ROLE` — result: `adversarial-review+silent-failure-audit-6014566c` (the pre-rename var name is still what's set, consistent with `main` not yet carrying either PR).

All raw evidence below comes from fresh `git clone` + `git archive <PR-head-ref> | tar -x` extractions into `/tmp` (never a working-tree grep), executed by delegated background workers (`freelunch:freelunch-worker`, foreground/consumed same turn). Every command and its literal output that a claim below rests on is either reproduced in a code fence or cited via `derived:`/`canonical:` in the same paragraph. Anywhere I relied on the PR body's own claim rather than re-deriving it, that is marked "read", not "executed".

### Claim 1 — the safety argument (attacked hardest, per task instruction)

**The PR's claim:** no dual-read, no alias ships in either PR; a merge-order window exists but is loud (system-wide DENY via `core/hooks/approval-gate.sh` / `core/hooks/gh-guard.sh` crash-then-deny), not silent.

**Independently re-derived, core repo, both gates** —
derived: `grep -n -B3 -A15 'CLAUDE_ROLE' core/hooks/approval-gate.sh core/hooks/gh-guard.sh` on `/tmp/core-archive-main` (pre-rename archive of `origin/main`, extracted via `git archive origin/main | tar -x`):
```
core/hooks/approval-gate.sh:85  [ -n "${TOKENMAXXXER_SPAWNED:-}${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
core/hooks/approval-gate.sh:142 role = os.environ["CLAUDE_ROLE"].strip()      # bracket access
core/hooks/approval-gate.sh:72  trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT

core/hooks/gh-guard.sh:40       [ -n "${TOKENMAXXXER_SPAWNED:-}${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
core/hooks/gh-guard.sh:91       role = os.environ["CLAUDE_ROLE"].strip()      # bracket access
core/hooks/gh-guard.sh:30       trap ... EXIT  (same fail-closed remap)
```
derived: `diff` of both files, `/tmp/core-archive-main` vs `/tmp/core-archive-extract` (PR `#348` head) — result: only the token `CLAUDE_ROLE`->`CLAUDE_SKILL` changes, identical line numbers and shape on both sides, confirming the presence-check/trap/bracket-access structure is unchanged by the rename in both files.

Mechanism —
derived: `grep -n 'CLAUDE_SKILL\|TOKENMAXXXER_SPAWNED' pipeline.py` on `/tmp/otr-archive-extract`, line 722: `env = {"CLAUDE_SKILL": role, "TOKENMAXXXER_SPAWNED": "1", ...}` — `TOKENMAXXXER_SPAWNED` is written on the same dict-literal line as the role var and its own name is untouched by this rename, so it is present in every spawned session's env regardless of which side of the rename `pipeline.py` is on. That keeps the OR-presence-check in both core gates open, execution reaches the python body, and the unconditional bracket-access then `KeyError`s when the name it expects isn't the name that's actually set — the trap converts the non-0/non-2 exit to `exit 2` (DENY).

**Live before/after execution (executed, not read), core repo** —
derived: `bash core/hooks/tests/run-approval-gate-tests.sh` run against both `/tmp/core-archive-main` and `/tmp/core-archive-extract`:
```
run-approval-gate-tests.sh  MAIN: == 65 passed, 2 failed ==   PR HEAD: == 65 passed, 2 failed ==  (byte-identical FAIL lines both times)
run-gh-guard-tests.sh       MAIN: == 54 passed, 0 failed ==   PR HEAD: == 54 passed, 0 failed ==
core/hooks/tests/run-all.sh MAIN vs PR HEAD: `diff` of the full captured log — only an archive-path string and "40ms average" vs "41ms average" differ; every `== N passed, M failed ==` summary line is byte-identical between the two runs
```
This confirms both orders crash-then-deny as claimed, and confirms — via live execution, not the PR's own say-so — that neither gate's other behavior (allow-when-no-role, deny-when-role-set-and-unapproved) regressed.

**Both merge orders, confirmed by code read (not the PR's assertion alone)** —
derived: same `grep`/`diff` evidence above, applied to both directions:
- **on-the-record merges first**: `pipeline.py` writes `CLAUDE_SKILL`; core still reads `CLAUDE_ROLE`. `TOKENMAXXXER_SPAWNED` keeps the presence check open in both core gates; `os.environ["CLAUDE_ROLE"]` is now absent -> `KeyError` -> `exit 2`. Loud deny.
- **core merges first**: core reads `CLAUDE_SKILL`; `pipeline.py` still writes `CLAUDE_ROLE`. Same mechanism, mirrored: `os.environ["CLAUDE_SKILL"]` absent -> `KeyError` -> `exit 2`. Loud deny.

Both orders check out against the code as read. This part of Claim 1 is **PRESENT**.

**The gap the PR's own analysis does not address.** The task's accuracy note asks whether `on-the-record/hooks/approval-gate.sh`'s own documented no-op (line 9: "No-ops immediately unless CLAUDE_SKILL is set") is reachable in the window, or forced loud first. Read via a targeted follow-up worker —
derived: `grep -n -B3 -A15 'CLAUDE_SKILL' on-the-record/hooks/approval-gate.sh` on `/tmp/otr-archive-extract`:
```
on-the-record/hooks/approval-gate.sh:9   # No-ops immediately unless CLAUDE_SKILL is set — orchestrator-authored
on-the-record/hooks/approval-gate.sh:62  [ -n "${CLAUDE_SKILL:-}" ] || { trap - EXIT; exit 0; }
```
This is **not** OR'd with `TOKENMAXXXER_SPAWNED` — unlike both of core's gates (compare against the `core/hooks/approval-gate.sh:85` fence above). Within on-the-record's own repo this is safe against the two-repo merge-order window as literally defined (write site `pipeline.py:722` and this read site change in the same commit `e4393321fdf6ff38f27c9478934ac9849aa6048f` — canonical: `gh pr view 2710 --json commits` first-commit `oid: e4393321...`, `messageHeadline: "issue-2670: rename CLAUDE_ROLE to CLAUDE_SKILL (write side + on-the-r…"` — so pipeline.py and this file's read can never desync from each other in on-the-record's own git history). But the mitigation as stated ("merge back-to-back, no session spawned in between") implicitly assumes hook *code* only changes at the instant a new session is spawned. That does not hold for a session already running when on-the-record's merge lands, if hook scripts are read live from the shared plugin checkout (`$ON_THE_RECORD`, one filesystem path, not a per-session pinned clone) rather than pinned to the commit current at that session's own spawn. In that scenario the in-flight session's env still carries the old var name (set once at spawn, never rewritten) while the hook script it invokes has already updated to check the new name; since this presence check has no `TOKENMAXXXER_SPAWNED` fallback, it fails and `|| exit 0` fires silently — no log line, ALLOW.

I could not confirm or rule out whether hook code is live-reloaded mid-session versus pinned at session start — that is an operational question outside what git/gh evidence answers, and I found no discussion of it in either PR's record. Reporting the code asymmetry as confirmed (shown in the fence above) with the reachability question open — see Open findings #1. Also: `on-the-record/hooks/deliverable-guard.sh` was **not touched** by PR #2710's diff —
derived: `gh pr diff 2710 --name-only` — result: 22-file list, `deliverable-guard.sh` absent from it — consistent with it having already migrated to a `TOKENMAXXXER_SPAWNED`-only presence check under a prior issue (canonical: `git -C /tmp/core-verify-clone log pr348 --oneline -20` — line `20e32f0 issue-327: migrate presence-only CLAUDE_ROLE readers to TOKENMAXXXER_SPAWNED (#330)`, core repo), which would mean it is unaffected by this rename and could provide overlapping coverage — but I did not fetch its source, so I cannot state how much of approval-gate.sh's own enforcement (an issue #2538 identity check, not a plain presence check, per `on-the-record/hooks/approval-gate.sh:86-91` comments in the fence above) it actually overlaps with. Left as Open finding #4, not asserted either way.

**Full reading-site enumeration, both repos, built from `grep` independently before comparing to either PR's list** (H = Handled/loud-deny-or-equivalent, S = Silently Absorbed on absence, N/A = not a write-enforcement read) —
derived: per-file `grep -n -B3 -A15 'CLAUDE_ROLE'` (core, on `/tmp/core-archive-main`) and `grep -n -B3 -A15 'CLAUDE_SKILL'` (on-the-record, on `/tmp/otr-archive-extract`), one call per file listed, full raw dumps in the delegated workers' transcripts:

| file | absent-behavior | class |
|---|---|---|
| core/hooks/approval-gate.sh | `KeyError` -> trap -> `exit 2` (fence above) | H |
| core/hooks/gh-guard.sh | `KeyError` -> trap -> `exit 2` (fence above) | H |
| core/hooks/board-gate.sh:735 | `role = os.environ.get("CLAUDE_ROLE", "").strip()` -> `role=""`, routes a `not role` branch | S (blast radius not traced — Open finding #2) |
| core/hooks/handbook-trigger-gate.sh:28 | `role="${CLAUDE_ROLE:-}"`, this file's `deny()`=`exit 0` always (issue #282 DEMOTE) | S, pre-existing advisory, not new to this rename |
| core/hooks/trailer-gate.sh:29 | same shape, `deny()`=`exit 0` | S, pre-existing advisory |
| core/hooks/proposal-shape-gate.sh:14 | `role="${CLAUDE_ROLE:-proposal-shape}"`, `deny()`=`exit 0` | S, pre-existing advisory |
| core/hooks/record-fields-gate.sh:66-71 | default-empty + explicit `deny(...)` call, but this file's `deny()`=`exit 0` | S, loud stderr / silent pass-through allow |
| core/hooks/record-shape-gate.sh:66 | `role="${CLAUDE_ROLE:-record-shape}"`, this file's `deny()`=`exit 2` (not demoted) | S (blast radius not traced — Open finding #2) |
| core/hooks/survey-order-gate.sh:70 | default-empty -> python fallback `"implementation"` | S, routing default only, not a block/allow decision |
| core/hooks/directive.sh, lib/role-directive.sh | OR'd w/ TOKENMAXXXER_SPAWNED, default-empty | S but text-rendering only, never gates a write |
| core/hooks/ordering-gate.sh | full-file read: no `os.environ`/`${CLAUDE_ROLE...}` reference at all, only a comment stating the dispatch table was retired from role-keying (issue #331) | N/A |
| on-the-record/hooks/approval-gate.sh:62 | bare `${CLAUDE_SKILL:-}` -> `exit 0` (fence above) | **S — not OR'd w/ TOKENMAXXXER_SPAWNED, see gap above** |
| on-the-record/hooks/deviation-log-guard.sh:166 | `role = role or (os.environ.get("CLAUDE_SKILL") or None)` | S, but this file's own refusal path is `additionalContext` only, never `decision:"block"` per its own header comment (lines 47-49) — pre-existing advisory shape |
| on-the-record/spawn.py:2368,2375; consult.py:958,1307,1675; deviation_log.py | `.get()` reads (spawn.py, informational deviation-log-path only) or dict-literal writes (consult.py) | N/A |
| on-the-record/hooks/{session-role-bind,pretooluse_dispatcher,quality-bar-gate,role-deviation-directive,skill-verdict-guard,upstream-defect-scope-guard}.sh | full-file greps: no `os.environ["CLAUDE_SKILL"]`/`.get("CLAUDE_SKILL", ...)` read in any of the six — `CLAUDE_SKILL` appears only in comments, or the file was migrated to read `TOKENMAXXXER_SPAWNED` (`pretooluse_dispatcher.py:246`) or `MUSTER_SKILLS` (`upstream-defect-scope-guard.sh:138`) instead | N/A |

**Verdict on Claim 1: PARTIALLY PRESENT.** The specific claim (core's two named gates crash-loud in both merge orders) is confirmed true by the code and live-execution evidence above. The broader implicit claim — "the window fails loud, period" — has one confirmed counter-example (on-the-record's own `approval-gate.sh`) whose real-world reachability depends on an operational fact I could not verify, plus two core gates (`board-gate.sh`, `record-shape-gate.sh`) with non-demoted deny paths whose absent-behavior I did not have time to trace to a blast radius. Not a "this is unsafe to merge" verdict — a "the enumeration in the PR is incomplete" verdict, and the incompleteness includes an asymmetric design choice (on-the-record's gate lacking the OR-guard core's gates have) that neither record explains.

### Claim 2 — 0 occurrences outside docs/, no compound variant

derived: `grep -rln 'CLAUDE_ROLE' . | grep -vE '^(\./)?docs/' | wc -l`, run inside each `git archive <PR-head> | tar -x` extraction (never a working-tree grep):
```
on-the-record, /tmp/otr-archive-extract (PR #2710 head, pr2710):  0
on-the-record, /tmp/otr-archive-main (origin/main):                22   (60 occurrences via the -o variant, matching PR #2710's own stated "60 occurrences / 22 files")
tokenmaxxxer-core, /tmp/core-archive-extract (PR #348 head, pr348): 0
tokenmaxxxer-core, /tmp/core-archive-main (origin/main):            44   (200 occurrences via the -o variant, matching PR #348's own stated "200 occurrences / 44 files")
```
Compound-variant check —
derived: `grep -roE 'CLAUDE_ROLE[A-Z_]*' . | sort -u`, all four archives above: only the bare `CLAUDE_ROLE` token outside `docs/`, every archive. One compound variant, `CLAUDE_ROLE_SIG`, was found — but only inside `docs/issue-698/proposals/2026-08-11-session-scoped-role-identity.md` (doc prose, not a reader), same in both on-the-record archives. **PRESENT**, independently re-derived.

Methodology note: the literally-specified filter `grep -v '^\./docs/'` does not match this environment's `grep -rln . .` output (no `./` prefix emitted), so it silently passes everything through unfiltered — both workers caught this independently, ran the as-specified command for traceability, then separately ran the corrected filter (`^(\./)?docs/`) shown above to get the real count. Raw fact, not a methodology substitution hidden from the reader.

### Claim 3 — end-to-end spawn + gate pass/refuse pair

Gate-level pass/refuse pairs —
derived: same `run-approval-gate-tests.sh`/`run-gh-guard-tests.sh` live runs cited under Claim 1 (`== 65 passed, 2 failed ==` and `== 54 passed, 0 failed ==`, identical on `/tmp/core-archive-main` and `/tmp/core-archive-extract`) — these runs include an explicit no-role-> allow vs role-set-> deny matrix for both gates (`run-approval-gate-tests.sh` `norole()`/`run allow human-approved`; `run-gh-guard-tests.sh` `run allow norole-merge`/`run deny role-merge`), executed live both before and after, byte-identical pass counts both times. This independently satisfies "at least one gate still refuses what it refused before."

The literal nested spawn-to-PR test —
canonical: on-the-record PR #2710's own record — untracked in this reviewer's own checkout, since PR #2710 is unmerged and that path does not exist on this repo's `main`; read instead from inside the PR-head archive at `/tmp/otr-archive-extract/docs/issue-2670/reports/refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c.md`, obtained via `git archive pr2710 | tar -x`, not via a path resolvable in this working tree. Its "Rationale for deviations" section states this was **not performed**: "requires the northpole harness's own operator-wired live-session step and a throwaway fixture host/token this headless turn doesn't have standing to provision." What did happen live, that same session: `gh pr create --repo tokenmaxxxer/tokenmaxxxer-core ...` succeeded, producing PR `#348` (canonical: `gh pr view 348 -R tokenmaxxxer/tokenmaxxxer-core --json url` — result: `https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/348`) — the builder session itself is a session-reaching-a-PR, though not a nested-spawn test of the post-rename spawn path specifically. **Verdict: PARTIAL.** Gate-level requirement independently confirmed by execution above; the literal "spawn a session end to end" sub-requirement is disclosed as not done in the upstream record, not silently dropped or misrepresented.

### Claim 4 — both merge orders

Covered under Claim 1 above via the same `grep`/`diff`/live-test evidence — both directions traced from the actual code on both archives, both **PRESENT**.

### Claim 5 — test-suite delta, nodeid level

Core (executed, live) —
derived: `bash core/hooks/tests/run-approval-gate-tests.sh`, `run-gh-guard-tests.sh`, `run-all.sh`, run on both `/tmp/core-archive-main` and `/tmp/core-archive-extract`:
```
run-approval-gate-tests.sh: == 65 passed, 2 failed == (both archives, byte-identical FAIL lines)
run-gh-guard-tests.sh:      == 54 passed, 0 failed == (both archives)
run-all.sh:                 full log diff shows only an archive-path string and 40ms->41ms timing jitter differing; every "== N passed, M failed ==" line identical
python3 -m pytest test/ -m "not slow" --collect-only -q  (core-archive-extract):  6 tests collected in 0.01s, 0 errors
python3 -m pytest tests/ -m "not slow" --collect-only -q (core-archive-extract): 54 tests collected in 0.03s, 0 errors
```

On-the-record (partially executed) —
derived: `git diff --name-only origin/main pr2710 -- test/ tests/` (in `/tmp/otr-verify-clone`):
```
test/test_approval_gate_carriers.py
test/test_branch_role_field.py
test/test_upstream_defect_scope_guard_cross_repo_cwd.py
tests/run-orchestrate-tests.sh
tests/test_stop_gate.sh
```
(5 files.) Full diffs of all 5 were read in full — every hunk is a literal `CLAUDE_ROLE`->`CLAUDE_SKILL` (or `-u CLAUDE_ROLE`->`-u CLAUDE_SKILL`) substitution inside an existing test body; no test function was added or removed in any of the 5 diffs, so the nodeid set is unchanged by direct diff inspection (not by running pytest).
derived: `python3 -m pytest test/ -m "not slow" --collect-only -q` on `/tmp/otr-archive-extract`:
```
408/410 tests collected (2 deselected) in 0.22s
```
Run once, on the PR-head archive only — **not** run on the `main` archive for a side-by-side count in this review, exit code 0, no collection errors. A full non-collect-only comparison run was not attempted, since this task's own instructions warn that `pytest test/` has been timing out in this environment on prior turns today. The PR body's own claim of an equal-failure-count `pytest -q` run before/after (via `git stash`) is read from the PR body text, not independently re-executed here. Disclosed gap, not a silent pass-through: Claim 5 is PRESENT for core (executed) and present-by-structural-diff for on-the-record's nodeid set, but on-the-record's pass/fail-count claim specifically is Unverifiable within this review's time budget — Open finding #3.

### Claim 6 — naming decision

canonical: on-the-record PR #2710's body (`gh pr view 2710 --json body`, read live) and on-the-record's own record file (same path/caveat as Claim 3, read via the PR-head archive) — `CLAUDE_SKILL` chosen over a more precise `CLAUDE_SUBJECT`, for consistency with 7 prior renames in the same sweep (`MUSTER_ROLE_MODEL`->`MUSTER_SKILL_MODEL`, `OTR_ROLE_BIND_STATE_DIR`->`OTR_SKILL_BIND_STATE_DIR` on-the-record; 5 more in core per PR #347's own body), citing that two of the seven already carry the same "not actually a bare skill name" imprecision unopposed. Reasoning cites `gh pr view 2668` and `gh issue view 2593` as its own sources. Applied consistently —
derived: same `diff` evidence under Claim 1/2 — every renamed site in both repos uses `CLAUDE_SKILL`, no repo introduces a different name. **PRESENT.**

## Why

Adversarial-review skill applied: built an independent reading-site enumeration from `grep` before comparing against either PR's own list (per the task's explicit instruction), specifically hunting for any gate whose absent-behavior is silent rather than loud, since the skill's premise is that a builder session's context already contains the reasoning behind its own safety argument and structurally won't contradict it. Found one gap neither PR's record discusses (on-the-record's own `approval-gate.sh` lacking the `TOKENMAXXXER_SPAWNED` OR-guard core's gates have) — full evidence under Claim 1 above.

Silent-failure-audit skill applied directly to Claim 1: classified every located `CLAUDE_ROLE`/`CLAUDE_SKILL` read as Handled (propagates as a blocking exit code) vs. Silently Absorbed (default/fallback value, execution continues) vs. not-applicable, per the skill's H/S/U taxonomy, rather than accepting the PR's binary "loud not silent" framing — this produced the two-tier picture in the reading-site table under Claim 1 (two genuinely loud enforcement gates in core, several pre-existing-advisory gates unaffected by this rename either way, and one on-the-record gate whose silence is new to this analysis).

Both PRs use `Advances #2670` rather than `Closes` —
canonical: `gh pr view 2710 --json body` / `gh pr view 348 -R tokenmaxxxer/tokenmaxxxer-core --json body`, both bodies end with `Advances #2670` — correctly reflects an intentional split delivery (no single commit can span two remotes), consistent with the hook-contract's partial-delivery convention.

## What did not work

None — this is a review record; nothing was built, so nothing failed to build.

One harness note, disclosed per the injection-flagging instruction rather than acted on: a delegated worker's raw-evidence dump for on-the-record's remaining reading sites returned with the wrapper `[harness: subagent output matched instruction-shaped pattern(s): settings-json...]`, neutralizing embedded `<`/control characters in its returned text.
canonical: the full neutralized text of that worker's return, read in this session's own transcript — the apparent trigger is verbatim-quoted source comments mentioning `.claude/settings.local.json` and `hooks.json` (e.g. inside `on-the-record/monitors/test_poll_heartbeat.py`'s own comments), not an actual embedded instruction; no directive-shaped content requiring separate user action was found after reading through it.

## Upstream basis

- `https://github.com/tokenmaxxxer/on-the-record/pull/2710` (head `e4393321fdf6ff38f27c9478934ac9849aa6048f`, OPEN — canonical: `gh pr view 2710 --json state,mergedAt`, this session)
- `https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/348` (head `434cfdd597ea3abe9129bc61896d122cc3ce631b`, OPEN — canonical: `gh pr view 348 -R tokenmaxxxer/tokenmaxxxer-core --json state,mergedAt`, this session)
- `https://github.com/tokenmaxxxer/on-the-record/issues/2670`
- on-the-record PR #2710's own record — untracked in this reviewer's own checkout (PR #2710 unmerged, so this path does not exist on this repo's `main`); cited above by its in-PR-archive path only (`docs/issue-2670/reports/refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c.md`, inside `/tmp/otr-archive-extract`), never as a path resolvable in this working tree.

## Open findings

1. **On-the-record's own `approval-gate.sh:62` presence check is not OR'd with `TOKENMAXXXER_SPAWNED`**, unlike both of core's crash-loud gates.
   derived: `grep -n -B3 -A15 'CLAUDE_SKILL' on-the-record/hooks/approval-gate.sh` on `/tmp/otr-archive-extract` — result: line 62 is `[ -n "${CLAUDE_SKILL:-}" ] || { trap - EXIT; exit 0; }`, no `TOKENMAXXXER_SPAWNED` reference anywhere in this file (full evidence and mechanism discussion under Claim 1 above).
   Whether this is exploitable depends on whether on-the-record's hook scripts are read live from the shared `$ON_THE_RECORD` checkout mid-session or pinned to the commit current at session-spawn time; not determinable from git/gh evidence alone. Resolution path: confirm the hook-loading model, or add the same OR-guard to this file's presence check before merge as a defense-in-depth measure regardless of the answer.
2. **`core/hooks/board-gate.sh` and `core/hooks/record-shape-gate.sh`** both have non-demoted (`exit 2`-capable) logic reading `CLAUDE_ROLE`/`CLAUDE_SKILL` via a default-empty/default-string fallback rather than bracket access.
   derived: `grep -n -B3 -A15 'CLAUDE_ROLE' core/hooks/board-gate.sh core/hooks/record-shape-gate.sh` on `/tmp/core-archive-main` — result: `board-gate.sh:735 role = os.environ.get("CLAUDE_ROLE", "").strip()`; `record-shape-gate.sh:66 role="${CLAUDE_ROLE:-record-shape}"`, this file's own `deny()` function exits 2 (not demoted, per the full-file read under Claim 1's table). Neither crashes-loud in the merge window — each silently takes whatever branch its default routes to, and I did not complete a forward-trace of either file's full logic to determine the blast radius (unlike the two gates traced fully under Claim 1). Resolution path: repeat the trace this audit did for core's two crash-loud gates, on these two, specifically to establish whether the default-routed branch is fail-closed or fail-open for each.
3. **On-the-record's pytest pass/fail delta was not independently re-executed.**
   derived: `python3 -m pytest test/ -m "not slow" --collect-only -q` on `/tmp/otr-archive-extract` — result:
```
408/410 tests collected (2 deselected) in 0.22s
```
   `--collect-only` was the only invocation attempted this review (see Claim 5); a full non-collect-only comparison run against `/tmp/otr-archive-main` was not attempted, since this task's own instructions warn that `pytest test/` has been timing out in this environment on prior turns today. The PR body's own claim of an equal-failure-count `pytest -q` run before/after (`git stash`-based) is read from the PR body text — not independently re-executed or verified by this review.
4. `on-the-record/hooks/deliverable-guard.sh` was not fetched.
   derived: `gh pr diff 2710 --name-only` — result: 22-file diff list, `deliverable-guard.sh` absent from it (full list and discussion under Claim 1 above). Its presence-check mechanism is believed migrated to `TOKENMAXXXER_SPAWNED`-only under core issue #327 (canonical: core `git log` line `20e32f0 issue-327: migrate presence-only CLAUDE_ROLE readers to TOKENMAXXXER_SPAWNED (#330)`), but that is core's migration, not confirmed for on-the-record's own copy of the file specifically — bears on how much redundant coverage exists if finding #1 is reachable.

## Next steps

None required from this record — it is a terminal independent-verification record. Findings #1-#4 above are handed to whoever next touches either PR (send-back candidates, not blockers this record is authorized to act on).

skill-verdict: adversarial-review — applied: invoked; built an independent reading-site enumeration from grep rather than the PR's own list per the task instruction, and surfaced a gap (on-the-record approval-gate.sh's missing OR-guard) neither PR's record discusses, consistent with the skill's premise that a builder session won't contradict its own safety narrative
skill-verdict: silent-failure-audit — applied: invoked; classified every CLAUDE_ROLE/CLAUDE_SKILL reading site in both repos as Handled/Silently-Absorbed/N-A per the skill's taxonomy (see table under Claim 1), rather than accepting the PR's binary loud-vs-silent framing, producing Open findings #1 and #2
other mounted skills: not triggered
