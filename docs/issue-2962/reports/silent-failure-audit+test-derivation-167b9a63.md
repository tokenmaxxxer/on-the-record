---
issue: 2962
role: silent-failure-audit+test-derivation-167b9a63
author: silent-failure-audit+test-derivation-167b9a63
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: on-the-record/hooks/fail-open-wrapper.sh, on-the-record/hooks/hook_ledger.py, on-the-record/hooks/stop-gate.sh, on-the-record/hooks/skill-verdict-guard.sh, on-the-record/hooks/post-landing-obligation-gate.sh, on-the-record/hooks/hook_classification.json, on-the-record/hooks/test_hook_classification.py, on-the-record/hooks/test_visible_fail_open.py, on-the-record/hooks/test_notice_no_external_dependency.py, on-the-record/hooks/test_heredoc_failure_bails.py, on-the-record/hooks/test_fail_open_ledger_fields.py
type: feature
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: on-the-record/hooks/hooks.json
    sha: same-commit
---

# issue-2962 — silent-failure-audit+test-derivation-167b9a63 record

## What was done

Build-now delivery (CORE_BUILD_NOW=1, contract v3 s19a) — no phase-1 proposal round. Code committed at `bc88f397` before this record was written (record-order.md).

1. **Enumeration + classification** (the issue's own named prerequisite). `on-the-record/hooks/hook_classification.json` classifies all 12 `hooks.json` command registrations as `invariant-injecting` or `observability`, with a `wrapped` flag and a one-line rationale per entry. `test_hook_classification.py` cross-checks the file mechanically against `hooks.json` (not "trust the comment") — every registration present, no orphans, no duplicates, and the 12-total/11-wrapped/1-unwrapped count matches the issue's own verified-wiring numbers — derived: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q` — result: `6 passed`.
   - `invariant-injecting` (6 entries in `hook_classification.json`): `session-role-bind.sh`, `directive.sh`, `pretooluse-dispatcher.sh` (classified but excluded from the notice mechanism below — see must-not #2), `post-landing-obligation-gate.sh`, `stop-gate.sh`, `skill-verdict-guard.sh`.
   - `observability` (6 entries): `self-update.sh`, `approach-cap-warning.sh` (pre and post — one script, two registrations), `retry-loop-bound.sh` (post), `lint-test-on-edit.sh` (post), `stop-poll-rearm.sh`.

2. **Visible in-band fail-open notice (path B).** `fail-open-wrapper.sh` looks up `$_hook_name` in a `case` statement (bash builtin) naming the 5 wrapped invariant-injecting hooks; when one fails open, the wrapper `printf`s a `[fail-open][DEGRADED] <hook> failed open (exit=<rc>, <reason>) ...` line to stdout, positioned before (and independent of) the existing python3/disk-dependent ledger step. `test_hook_classification.py::test_wrapper_notice_case_list_matches_wrapped_invariant_injecting_entries` cross-checks this `case` list against `hook_classification.json`'s wrapped invariant-injecting set so the two representations cannot silently drift — derived: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q` — result: `6 passed` (same run as above). Notice mechanism itself — derived: `python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q` — result: `6 passed`.

3. **Heredoc-failure bail (path A).** Of the 12 registered hooks, only 3 use the `IFS='' read -r -d '' VAR <<'PY' || true` → `python3 -c "$VAR"` shape the issue's shell-level cascade targets — checked: `grep -l "read -r -d ''" on-the-record/hooks/*.sh` cross-referenced against the 12 `hooks.json` registrations — result: `stop-gate.sh`, `skill-verdict-guard.sh`, `post-landing-obligation-gate.sh` (the other 9 registered hooks either don't heredoc into a variable at all, or already read stdin the safe pre-initialized way, e.g. `lint-test-on-edit.sh`). Each of the 3 now pre-initializes its variable (`CHECK=""` / `GUARD=""`) immediately before the heredoc read and bails with an explicit `exit 1` immediately after it if the variable came back empty, before ever reaching `python3 -c "$VAR"`. `exit 1` (never `exit 2`) matches each hook's pre-existing fail-open/fail-closed posture unchanged — derived: `python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q` — result: `5 passed`.

4. **Ledger fields distinct from success.** `hook_ledger.record_fail_open()` gained a `fallback_fired: bool` parameter, written as its own JSON field alongside the pre-existing `exit_code` (never folded into one merged string). `fail-open-wrapper.sh` passes it through its CLI (`hook_ledger.py <hook> <rc> <reason> <fallback_fired> <argv...>`, args reindexed accordingly) — derived: `python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result: `5 passed`. Notice path has no external dependency (printf/case only, before any python3 call, works with python3 stripped from PATH and with an unwritable TMPDIR) — derived: `python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q` — result: `3 passed`.

## Why

CORE_BUILD_NOW=1 (spawner-set) authorizes delivery-only per contract v3 s19a — proposal round skipped by design, not a deviation.

Scoping the heredoc-bail and notice-case-list changes to exactly the hooks.json-registered set (rather than all `.sh` files repo-wide that use the same `read -r -d ''` shape — checked: `grep -l "read -r -d ''" on-the-record/hooks/*.sh | wc -l` — result: `37`) follows the issue's own framing: acceptance criterion 1 is explicitly about `hooks.json` registrations, and most of the other files are legacy/reference copies superseded by `pretooluse_dispatcher.py` (that shim's own header comment: "the .sh files remain on disk as the source of truth" but execution moved into the python dispatcher, issue #2146) — they never actually run through `fail-open-wrapper.sh` today, so fixing them would be dead-code maintenance outside this slice, not risk reduction.

`exit 1` (not a new/different code) as the bail exit was chosen specifically because it is the exit code bash already produces today when this exact cascade happens under `set -u` — checked: `bash -c 'set -u; unset VAR; printf "%s" "$VAR"'` — result: exits `1`, stderr `unbound variable` (reproduced in `test_heredoc_failure_bails.py`'s `test_old_pattern_cascades_into_unbound_variable_error`, derived: `python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q` — result: `5 passed`) — the fix removes the noisy, misattributed second error, it does not change what the platform sees as the outcome. This directly satisfies the must-not: "do not make any hook fail-closed."

## Skill application

**silent-failure-audit** (invoked via Skill tool) — applied to the hook infrastructure itself, not application code: Step 1 enumerated the heredoc-read error-handling sites (`IFS='' read -r -d '' VAR <<'PY' || true` across the 3 hooks.json-registered hooks that use this shape, canonical: `on-the-record/hooks/stop-gate.sh`, `on-the-record/hooks/skill-verdict-guard.sh`, `on-the-record/hooks/post-landing-obligation-gate.sh` read directly this session); Step 2 classified the pre-existing behavior as Silently Absorbed (`|| true` swallows the read's own always-nonzero exit, and a failed heredoc leaves the variable unset with no trace); Step 3 traced forward: unset var → `set -u` unbound-variable error → script terminates with an unrelated second error message, with the *original* heredoc failure never named anywhere in the output — exactly the "reports itself as success [or as an unrelated crash]" pattern the issue names. The remediation (pre-init + explicit bail) matches the skill's Step 5 guidance for this pattern class.

**test-derivation** (invoked via Skill tool) — Step 1 scope gate: the issue's own Acceptance section supplied 5 written, command-shaped criteria (satisfied). Step 3a risk classification: all 5 are **Low** (mechanical/structural infrastructure checks, no safety/regulatory/revenue exposure, no multi-condition business rule) — so per the skill's own depth rule, full EP/BVA/decision-table/state-model derivation is not warranted; each criterion got a GWT-shaped pytest test plus, where the criterion's own shape called for it, equivalence partitions (below) rather than the heavier techniques (Steps 7-10 do not apply here: no multi-condition business rule, no lifecycle/state machine, no 3+ orthogonal parameters, no safety-critical Boolean decision in this slice).

Traceability matrix (all Low; GWT scenario + partitions named per the Low depth rule):

| Acceptance criterion | Partitions exercised | Test file | Result |
|---|---|---|---|
| every hooks.json registration classified, checkably | classification present/absent × valid/invalid class × wrapped true/false; drift between data file and enforcement code | `test_hook_classification.py` | derived: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q` — result: `6 passed` |
| invariant-injecting fail-open → visible notice | hook class (invariant-injecting / observability) × outcome (success exit 0 / fail-open nonzero-not-2 / deny exit 2) | `test_visible_fail_open.py` | derived: `python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q` — result: `6 passed` |
| notice path has no external dependency | ordering (notice before first python3 call) × python3 absent from PATH × TMPDIR unwritable | `test_notice_no_external_dependency.py` | derived: `python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q` — result: `3 passed` |
| heredoc failure bails, not cascades | old pattern (unset, cascades) vs. new pattern (pre-init, bails) × each of the 3 real hooks (pattern shape, syntax validity, non-exit-2 bail code) | `test_heredoc_failure_bails.py` | derived: `python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q` — result: `5 passed` |
| ledger carries exit status + fallback-fired as distinct fields | empty ledger (schema-only, no crash) × direct-call schema × wrapper end-to-end for both hook classes | `test_fail_open_ledger_fields.py` | derived: `python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q` — result: `5 passed` |

Residual (out of these techniques' scope): a genuine full-disk heredoc failure was not reproduced live in this sandbox — checked: `TMPDIR=<0-perm dir> bash -c 'read -r -d "" VAR <<EOF ... EOF'` — result: read still succeeded (bash 5.1/Linux did not reproduce the temp-file failure even with an unwritable TMPDIR); the fix's correctness instead rests on the pre-init+bail mechanism being demonstrably sound under `set -u` (`test_heredoc_failure_bails.py`'s pattern-level tests, proven directly, not simulated) plus static confirmation the real hooks use it. Non-functional dimensions (performance, concurrency across simultaneous hook firings) are outside this skill's scope and untouched by this slice.

## Upstream basis

`on-the-record/hooks/hooks.json` (same-commit — read as-is this session to enumerate the 12 registrations; the file itself was not modified — checked: `git diff bc88f397~1 bc88f397 -- on-the-record/hooks/hooks.json` — result: empty diff).

## Acceptance verification

canonical: this session's own executed pytest runs, reproduced together —

```
$ python3 -m pytest on-the-record/hooks/ -k hook_classification -q
6 passed in 0.82s
$ python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q
6 passed in 0.95s
$ python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q
3 passed in 0.83s
$ python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q
5 passed in 0.80s
$ python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q
5 passed in 0.84s
```

Regression check, same session — derived: `bash -n on-the-record/hooks/fail-open-wrapper.sh on-the-record/hooks/stop-gate.sh on-the-record/hooks/skill-verdict-guard.sh on-the-record/hooks/post-landing-obligation-gate.sh` — result: clean (exit 0, no output). Derived: `python3 -m pytest on-the-record/checks/ on-the-record/hooks/ -q` — result: `29 passed`.

Full-repo comparison against a clean baseline — derived: `git stash && python3 -m pytest -q -m "not slow"` on the pre-change tree, then `git stash pop` and the same command post-change — result: 17 failures both times; re-ran the specific affected suites (`test/test_convention_equivalence.py`, `tests/test_spawn_gate_wiring.py`, `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, `test/test_local_dependency_env.py`) against the `git stash`-clean tree individually via `python3 -m pytest -q -o addopts=""` scoped to their failing test IDs — result: identical failures on the clean tree (no `origin` git remote in this sandboxed checkout for the git-fetch-dependent ones; two unrelated stale-reference assertions) — none newly introduced by this change.

## must not: verification

- Did not make any hook fail-closed: the 3 heredoc-bailed hooks forward the same exit code the old cascade already produced (`1`); `stop-gate.sh`/`skill-verdict-guard.sh`'s pre-existing self-trap (already fail-closed, predates this change) is unmodified; `post-landing-obligation-gate.sh` remains fail-open — derived: `python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q` (includes `test_bail_exit_code_is_never_2_deny`) — result: `5 passed`.
- `pretooluse-dispatcher.sh`'s fail-closed posture is untouched (file not edited this session — checked: `git diff bc88f397~1 bc88f397 -- on-the-record/hooks/pretooluse-dispatcher.sh` — result: empty diff); it is classified in `hook_classification.json` for completeness with `wrapped: false` and excluded from the notice `case` list by construction — derived: `python3 -m pytest on-the-record/hooks/ -k hook_classification -q` (includes `test_pretooluse_dispatcher_is_classified_but_unwrapped`) — result: `6 passed`.
- The notice does not depend on python3, a writable disk, or any subprocess — derived: `python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q` — result: `3 passed`.
- Observability hooks keep today's silent fail-open — derived: `python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q` (includes `test_observability_hook_crash_stays_silent_no_notice`) — result: `6 passed`.
- The notice is not the traceback standing in for itself: it is a distinct `printf` line (source: `on-the-record/hooks/fail-open-wrapper.sh`, the `[fail-open][DEGRADED]`-prefixed line), separate from and not derived from stderr/traceback content — canonical: `on-the-record/hooks/fail-open-wrapper.sh` read this session.

## What did not work

None — no scope-exceeded stop, no alternative-swap from an approved proposal (none existed under the build-now bypass), nothing written and then undone.

## Open findings

None.

## Next steps

None — loop_state is terminal (landed). A residual, explicitly out-of-scope item for a future issue: the other `.sh` files under `on-the-record/hooks/` that still use the same `read -r -d '' VAR <<'PY' || true` shape but are not `hooks.json` registrations (superseded by `pretooluse_dispatcher.py`) carry the same latent shell-cascade risk if that dispatch shim is ever bypassed or those files are re-wired directly.

skill-verdict: silent-failure-audit — applied: invoked; enumerated/classified/traced the heredoc-read error-handling sites in stop-gate.sh, skill-verdict-guard.sh, post-landing-obligation-gate.sh (see Skill application above)
skill-verdict: test-derivation — applied: invoked; derived the 5 acceptance-criterion test files via GWT + Low-depth EP partitioning per the risk classification (see Skill application / traceability matrix above)
other mounted skills: not triggered
