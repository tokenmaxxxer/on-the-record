---
issue: 2705
role: architecture-interface-contract-shape-952309f5
author: architecture-interface-contract-shape-952309f5
skills: architecture-interface-contract-shape (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
code_under_review: on-the-record/hooks/gate-registration-post-guard.sh, on-the-record/hooks/test_gate_registration_post_guard.py, docs/handbooks/hooks.md
type: hook (state-lifecycle bugfix + enumeration completion, additive; two-guard architecture unchanged)
breaking: no
verdict: PASS — checked: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` on this branch — result: 8 passed
upstream:
  - path: docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md
    sha: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0
  - path: ebe12baa532650990d18211aef1a54884e88ee19:docs/issue-2705/reports/adversarial-review-a243c784.md
    sha: ebe12baa532650990d18211aef1a54884e88ee19
  - path: PR #2864 review comment (JiwonJung94, 2026-08-30T07:36:03Z, CHANGES) — GitHub PR comment, not a repo path
    sha: same-commit
---

# issue-2705 — architecture-interface-contract-shape-952309f5 record

## What was done

Continued PR #2864 (`gate-registration-post-guard.sh`, this issue's weaker-promise
`PreToolUse`/`PostToolUse` companion for the bundled `git add && commit` shape) on its own branch
(`issue-2705/architecture-interface-contract-shape-3f3d4ef5`, head `de8ecb01`), addressing the two
items in the PR's CHANGES review comment. The two-guard architecture itself (strong
`gate-registration-guard.sh` unchanged, weaker `gate-registration-post-guard.sh` companion) is the
already-settled seam decision from that PR and is **not reopened here** — canonical: the review
comment's own words, "The seam decision itself is right and I am not reopening it," read via `gh
pr view 2864 --json comments` this turn.

### 1. Fixed the state-file lifecycle (the overhead claim)

Root cause, canonical: `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/gate-registration-post-guard.sh`
lines 151–158 (`_save()`, unchanged since PR #2864's own delivery):
```python
def _save(data):
    try:
        tmp = state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, state_path)
    except OSError:
        pass
```
`_save()` writes a `<session>.json` file unconditionally — whether or not `data["violations"]` is
non-empty — and nothing in the file ever calls `os.remove`/`os.unlink`. The `pre`-mode bash-only
fast path (lines 97–103, unchanged) short-circuits on the state dir's mere *file existence*
(`for _f in "$STATE_DIR"/*.json; do [ -e "$_f" ] && ...`), never on content. So the first bundled
commit that touches a `gates/*.py`/`on-the-record/hooks/*.sh`/`.github/workflows/*.yml` file —
clean or violating — leaves a file behind and permanently defeats the fast path for every later
tool call sharing that `$TMPDIR`, on the broadest-matcher hook in the system. This is exactly
what PR #2867's round-4 verification measured: canonical:
`ebe12baa532650990d18211aef1a54884e88ee19:docs/issue-2705/reports/adversarial-review-a243c784.md`,
item 1 — `1.525 ms/call -> 33.925 ms/call` (~22x), against a hand-planted `{"violations": []}`
file standing in for that outcome.

Fix: `_save()` now deletes the state file (`os.remove`, `OSError` ignored — same fail-open shape
the rest of the file already uses) whenever `data["violations"]` is empty, instead of writing an
empty-list file. This is called from both the `post`-mode path (a clean bundled commit writes
nothing) and the `pre`-mode path (a resolved violation deletes its own entry rather than shrinking
to `{"violations": []}`). File existence and "a violation is genuinely outstanding" are now the
same fact, which is what the bash-only fast path's existence check has always assumed but the
Python side never guaranteed.

acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` (this branch) — result:
```
........                                                                 [100%]
8 passed in 0.98s
```
(7 tests carried over from PR #2864, 2 of them tightened to assert the state file is *absent*
rather than present-with-`[]` after a clean commit / a resolved violation, plus 1 new test,
`test_pre_mode_fast_path_survives_a_resolved_violation`, that swaps a marker-writing `python3`
stub onto `PATH` and asserts the marker is absent after the fast path's own bash-only check should
have returned before ever reaching the interpreter — and present while a real violation is still
open.)

Re-measured `pre`-mode latency (500-call `subprocess.run` loop, `n=500`, same shape PR #2867's own
round-4 review used) against three scenarios, all populated via the REAL shipped hook driven
through real bundled `git add && git commit` calls on a scratch fixture repo — not hand-planted
files — so the numbers reflect what this fix actually produces in use, not a synthetic state:

derived: ad hoc timing script written to `/tmp/otr-2705-timing2.py` this turn (not committed —
scratch verification only, same convention this issue's other records use for `/tmp` fixtures)
and run via `python3 /tmp/otr-2705-timing2.py` — result:
```
1. empty-state-dir, never touched (n=500): 1.176 ms/call
   files left in state dir after 30 real sessions (25 clean + 5 raised-then-resolved): []
2. dirty-from-ordinary-use, all resolved via real hook (n=500): 1.180 ms/call
3. one real open violation present, elsewhere in same TMPDIR (n=500): 31.548 ms/call
4. after that violation resolves, same TMPDIR, no restart (n=500): 1.173 ms/call
```
Scenario 2 is the "dirty from ordinary use" case the task brief asked for: 25 real clean bundled
commits (row staged in the same `git add`) and 5 real raised-then-resolved violations, all driven
through the actual `post`/`pre` hook, leave **zero** files behind and the fast path stays at
baseline (1.180ms vs 1.176ms empty — no measurable difference). Scenario 3 is "a state file
present": a single REAL open violation elsewhere in the same `$TMPDIR` correctly costs ~31.5ms/call
for every session sharing that directory (the bash-only check is directory-wide, not
session-scoped) — this is the honest cost of a violation that actually needs re-checking on every
call, not a regression, and scenario 4 shows it self-heals the moment that violation resolves,
with no restart needed.

Running the SAME script unmodified against the PRE-FIX script
(`git show de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:on-the-record/hooks/gate-registration-post-guard.sh`
written to a scratch path) reproduces the reported regression directly:

derived: same `/tmp/otr-2705-timing2.py` script, `HOOK` pointed at the pre-fix script instead — result:
```
1. empty-state-dir, never touched (n=500): 1.308 ms/call
   files left in state dir after 30 real sessions (25 clean + 5 raised-then-resolved): [30 files, including all 25 'clean-sess-*']
2. dirty-from-ordinary-use, all resolved via real hook (n=500): 31.726 ms/call
3. one real open violation present, elsewhere in same TMPDIR (n=500): 31.445 ms/call
```
— confirming scenario 2 is exactly where the pre-fix code regresses (1.3ms -> 31.7ms after ordinary
clean-commit traffic) and exactly where this fix restores it (1.180ms).

### 2. Finished the enumeration (acceptance criterion 3)

PR #2864's own enumeration table (`docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md`,
"Enumeration" section) classified `deviation-log-guard.sh` and `product-capture-stopgate.sh` as
"not applicable" (rows 305–306: `Stop` hooks, not `PreToolUse`/`Bash`, so they cannot exhibit
`gate-registration-guard.sh`'s specific blind spot) but verified that only via `head -3`/`head -6`
on each script — confirming the event-type comment, never checking whether either hook is actually
wired into `hooks.json`. PR #2867's round-4 review found both are ALSO never wired — the same
#909-class orphan defect the table already flags for `live-fire-test-guard.sh`, just missed for
these two because the wiring check was only run where the blind-spot hunt made it directly
relevant. Reproduced independently this turn, all three together:

canonical: `on-the-record/hooks/hooks.json`'s `Stop` array, read via a small Python snippet
(`json.load(open("on-the-record/hooks/hooks.json"))["hooks"]["Stop"]`) run this turn — result:
exactly 3 entries, `stop-poll-rearm.sh`, `stop-gate.sh`, `skill-verdict-guard.sh`. Neither
`deviation-log-guard.sh` nor `product-capture-stopgate.sh` appears.

derived: `diff on-the-record/hooks/hooks.json /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/hooks.json`
— result: differs only by this same PR's own new `gate-registration-post-guard.sh` `pre`/`post`
lines (4 lines total); the live installed copy shows the identical `Stop`-array absence.

derived: `grep -rl "deviation-log-guard\.sh\|product-capture-stopgate\.sh" --include="*.py"
--include="*.json" --include="*.yaml" --include="*.yml" .` (repo-wide) — result: one hit,
`harness/fixture-target/scenario.py`, which only invokes `product-capture-stopgate.sh` directly by
path as a test-fixture target (`HOOK = REPO_ROOT / "on-the-record" / "hooks" /
"product-capture-stopgate.sh"`), not a `hooks.json`/dispatcher wiring entry — no wiring reference
to either script exists anywhere.

derived: `grep -rn "live-fire-test-guard" on-the-record/hooks/hooks.json
on-the-record/hooks/pretooluse_dispatcher.py` (re-run this turn, not restated from either prior
record) — result: no match, exit 1, confirming `live-fire-test-guard.sh`'s own orphan status
independently.

All three orphans, together, with the command that established each verdict:

| hook | claimed live at | wiring check | verdict |
|---|---|---|---|
| `live-fire-test-guard.sh` | `PreToolUse`/`Bash` (enforcement-boundary.md row) | `grep -rn "live-fire-test-guard" on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py` — no match | never wired |
| `deviation-log-guard.sh` | `Stop` (enforcement-boundary.md line 170) | `hooks.json`'s `Stop` array read via `json.load` — absent | never wired |
| `product-capture-stopgate.sh` | `Stop` (enforcement-boundary.md line 159) | `hooks.json`'s `Stop` array read via `json.load` — absent | never wired |

Not fixed here — same as PR #2864's own treatment of `live-fire-test-guard.sh`, this is reported as
an open finding (below), out of #2705's non-goals ("the registration requirement itself is worth
keeping" and individual other hooks' own gaps are explicitly not this issue's scope).

## Why

**Fix the lifecycle, not the number, per the review comment's own instruction.** The review named
the exact defect (`_save()` unconditional write, no delete path, existence-only fast-path check)
and the exact fix shape ("a resolved or non-violating outcome should leave nothing behind, and the
fast path needs a check that distinguishes 'a violation is outstanding' from 'a file exists'").
Deleting the file on empty `violations` satisfies both halves with the smallest change: the
existing bash-only existence check needed no modification once the invariant "file exists iff a
violation is outstanding" is actually upheld by the Python side that owns state-file writes — the
alternative the review itself named (checking file size instead of existence) would have required
touching the fast path's own logic for no added correctness, since the real defect was never in
what the fast path checks, only in what `_save()` left there to be checked.

**Report the enumeration gap rather than fix the two hooks' wiring.** Issue #2705's own non-goals
say "the registration requirement itself" and individual other hooks' gaps are out of scope; PR
#2864 already established the precedent of reporting `live-fire-test-guard.sh`'s identical orphan
status as an open finding rather than wiring it up in the same delivery. Fixing
`deviation-log-guard.sh`/`product-capture-stopgate.sh`'s wiring here would silently expand this
PR's write-set beyond what the review asked for — the review asked to finish naming every orphan,
not to fix what naming them turns up — and beyond `architecture-interface-contract-shape` skill's
own segregation logic (rule 12: expose only the minimal contract each change actually needs to
touch) — a #2705 acceptance-criterion fix should not also turn into an unscoped #909 cleanup PR.

## What did not work

None.

## Upstream basis

- `docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md` (PR #2864's own
  delivery record) and `on-the-record/hooks/gate-registration-post-guard.sh`/
  `on-the-record/hooks/test_gate_registration_post_guard.py` at that PR's head,
  sha `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`.
- `ebe12baa532650990d18211aef1a54884e88ee19:docs/issue-2705/reports/adversarial-review-a243c784.md`
  (PR #2867's round-4 independent verification — overhead measurement methodology and enumeration
  undercount finding), sha `ebe12baa532650990d18211aef1a54884e88ee19`.
- PR #2864's review comment (JiwonJung94, 2026-08-30T07:36:03Z, "CHANGES") — the two items this
  record addresses, read via `gh pr view 2864 --json comments` this turn.

## Open findings

- `live-fire-test-guard.sh`, `deviation-log-guard.sh`, and `product-capture-stopgate.sh` are each
  claimed live in `docs/specs/enforcement-boundary.md` but absent from `hooks.json`/the
  `pretooluse_dispatcher.py` `GATES` list (the first) or `hooks.json`'s `Stop` array (the latter
  two) — see the enumeration table above for each one's own verifying command. Resolution path: a
  separate issue for the #909 orphan class generally; explicitly out of #2705's own scope (its
  non-goals name "the registration requirement itself" and other hooks' individual gaps).
- The 5 other same-blind-spot hooks PR #2864's own enumeration named
  (`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
  `spec-index-preflight.sh`, `requirement-digest-preflight.sh`, and core's
  `handbook-trigger-gate.sh`/`trailer-gate.sh`) each carry the identical remedy shape (a
  `post`-mode companion reading `tool_response`'s commit-success line) if picked up — unchanged
  from PR #2864's own record, not re-verified in this round since the CHANGES comment did not
  reopen that part of the enumeration.

## Next steps

Both CHANGES-comment items are addressed with executed-live checks in this record: the
state-lifecycle fix plus its regression test and dirty/open-violation re-measurement (item 1), and
the finished three-hook orphan enumeration (item 2).

acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` (this branch) — result:
```
8 passed in 0.98s
```

`loop_state` above is set to its terminal value on the strength of that check. The phase-2
delivery PR carries `Closes #2705` per `pr-preflight.sh`'s trailer convention, continuing on PR
#2864's own branch rather than opening a new one.

## Standing invariants

- **No return of the retired role axis**:
  derived: `git diff origin/main -- docs/handbooks/hooks.md docs/specs/enforcement-boundary.md docs/specs/generated-paths.md on-the-record/hooks/hooks.json on-the-record/hooks/gate-registration-post-guard.sh on-the-record/hooks/test_gate_registration_post_guard.py | grep -iE "role.axis|axis"` — result: no match (exit 1, 0 lines).
- **No new bug, failing-test set vs `origin/main` as SETS OF NAMES**:
  acceptance: `python3 -m pytest test/ gates/ on-the-record/ -q` (this branch) — result:
```
15 failed, 506 passed, 3 xfailed in 32.31s
```
  Same command on a fresh `git worktree add /tmp/otr-main-baseline-2705 origin/main` — result:
```
15 failed, 498 passed, 3 xfailed in 31.81s
```
  (506 = 498 + this file's 8 tests, one more than PR #2864's own 7.) derived: `diff
  <(sorted FAILED-name list, this branch) <(sorted FAILED-name list, origin/main worktree)` —
  result: 0 lines of difference, `IDENTICAL FAILING-TEST-NAME SETS` printed. Worktree removed after
  the check via `git worktree remove --force /tmp/otr-main-baseline-2705`.
- **No overhead increase** (the subject of this round, measured in the dirty state, not the empty
  one): see item 1 above in full — scenario 2 ("dirty from ordinary use," 25 real clean bundled
  commits + 5 real raised-then-resolved violations, all via the actual hook) measures 1.180ms/call
  vs a 1.176ms/call empty-state baseline — statistically equivalent, no permanent regression.
  Scenario 3 (a real open violation still outstanding) correctly costs ~31.5ms/call — a legitimate,
  self-healing cost (scenario 4 confirms it clears the moment the violation resolves), not the
  permanent one-way-door PR #2867 found in the pre-fix script.
- **Monitor and watch machinery unbroken and not quieter**:
  acceptance: `python3 -m pytest test/ -k "fleet_scan or monitor or watch" -q` (this branch) — result:
```
15 passed
```
  Same command on the `origin/main` worktree — result:
```
15 passed
```
  — identical pass count on both. derived: `grep -n "hook_fires\|hook-fires"
  on-the-record/hooks/gate-registration-post-guard.sh on-the-record/hooks/gate-registration-guard.sh`
  — result: no match in either file (exit 1) — unchanged from PR #2864's own delivery, this fix
  touches no fires-log surface.

skill-verdict: architecture-interface-contract-shape — not-applicable: this round makes no new
choice about a boundary contract's shape — the sync-vs-async, two-guard-not-one-guard decision PR
#2864 made under this same skill is explicitly settled and not reopened here (per the review
comment's own instruction); the work in this record is a state-lifecycle bugfix and a wiring-check
finishing pass, neither of which chooses or changes a contract shape.
other mounted skills: work-in-english — not invoked via the Skill tool (guidance-only per this
session's own skill-obligations note, enforced by core hooks rather than requiring invocation);
followed throughout by writing all code, comments, docs, commit messages, and this record in
English. conformance-review-finding-record, verify-finding-record — not invoked: this session
writes neither a `docs/issue-<n>/reports/conformance-review.md` nor a
`docs/issue-<n>/reports/defect-verification.md` file; it is the continuing implementation role for
PR #2864's own deliverable, not a conformance-review or defect-verification role.
