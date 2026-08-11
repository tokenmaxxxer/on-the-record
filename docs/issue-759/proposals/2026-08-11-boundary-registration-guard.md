---
status: proposed
files:
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/specs/reconciled-index.md
  - tests/test_gates.py
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
  - on-the-record/hooks/hooks.json
  - docs/issue-759/reports/implementation.md
---

## Request

Issue #759: `main` keeps landing red. On current `main` three tests fail —
two (`gates/test_boundary.py::t_all_gates_modules_recorded`,
`gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint`)
because issue-730 added `on-the-record/hooks/record-claim-shape-directive.sh`
without a row in `docs/specs/enforcement-boundary.md` or
`docs/specs/generated-paths.md`; one
(`tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge`)
because issue-682's `_pr_index_all` fast path broke it the same way it
broke a sibling test that #689/#691 already fixed once, five hours earlier
the same day. #689 repaired the same red-main shape once (2026-08-11
00:08) with no mechanism preventing recurrence; the omission reappeared
inside one day. This proposal both restores green and adds the missing
landing-time check so the next new gate/hook lands its spec row in the
same commit instead of relying on someone remembering to run the pytest
suite (this repo runs no CI — #460).

## Constraints

- No GitHub Actions / CI introduction — #460 already decided that; any
  check must attach to an existing zero-install hook or gate path, per
  the issue body's own instruction.
- The three current failures are the only test cleanup in scope — no
  other red/yellow test gets touched.
- The new guard must fail open on any environment gap (missing
  `python3`/`git`, not a `git commit` command, nothing relevant staged)
  and fail closed only on a positively-determined missing-registration —
  same boundary every sibling `PreToolUse`+`Bash` `git commit` guard in
  this repo already draws.
- Whatever mechanism #759 adds must not be a mechanism #744 is already
  scoped to weaken, and must not silently duplicate #744's investigation.

## Rationale

**Fix `tests/test_gates.py`'s missing mock, not `gates/closure_sweep.py`.**
The failing test's own mocks (`spawn._pr_for_branch`,
`closure_sweep._pr_view_state_body`, `ci._fetch_ref_file`) show it targets
the per-branch fallback path, but it never mocks `_pr_index_all`, so
`find_violations` takes the (correct, working-as-designed) list-based fast
path issue #682 added and shells out to the real `gh pr list` against a
nonexistent tmp directory. The alternative — changing
`find_violations`/`_pr_index_all` so the fast path can't run unmocked —
was rejected: the fast path's own behavior is exactly what issue #682
intended (367s -> 8.9s) and is exercised correctly by every other
`closure_sweep` test; changing production code to accommodate one test's
missing mock would be fixing the wrong side of a defect a sibling test in
`gates/test_closure_sweep.py` already demonstrated how to fix correctly.

**Port the registration check inline into a new `PreToolUse`+`Bash`
`git commit` hook, over shelling out to `pytest` from a hook.** The
issue's own framing offers this as one of two options ("사후 테스트를
실제로 돌게 만들기(호출자 배선)"). Rejected in favor of porting: every one
of the 26 existing `on-the-record/hooks/*.sh` scripts that gates on
`git commit` (`spec-index-preflight.sh`, `role-axis-completeness-guard.sh`)
ports its check logic inline or imports the specific module it needs —
none shells out to `pytest`. A consumer repo installing this plugin has no
guarantee that `gates/test_boundary.py`'s full pytest environment is
present or fast at hook-invocation time (zero-install is the standing
constraint every sibling states in its own header comment); porting the
same derive-and-compare logic `gates/test_boundary.py`/
`gates/test_generated_paths.py` already implement keeps this hook
consistent with its 2 closest siblings instead of introducing a new,
unprecedented "hook calls pytest" pattern.

**Trigger only on a newly-staged (git-status `A`) mechanism file, not on
every commit.** Rejected "re-run the full completeness check on every
`git commit`": both prior-art siblings scope their trigger narrowly
(`spec-index-preflight.sh` only re-checks a spec file that is itself
staged and changed; `role-axis-completeness-guard.sh` only fires when a
`roles/*.json` file is staged) — a check that fires on unrelated commits
(editing docs, fixing an already-registered gate's internals) is exactly
the ambient-noise failure mode #744 is investigating. Scoping the trigger
to "a brand-new `gates/*.py`/`on-the-record/hooks/*.sh`/
`.github/workflows/*.yml` file just entered the staged set" matches
#441/#684's actual acceptance wording ("기록되지 않은 게이트가 조용히
존재한다") — the moment of concern is exactly file creation, nothing
broader.

**Keep #759 and #744 as separate issues, not merged.** Investigated per
the issue's own instruction (see the survey's "#744 relationship"
section). #744 names three specific, different noise sources
(`reconciled-index.md` companion-regen guidance,
`record-claim-guard.sh` backtick-path false positives on not-yet-created
paths, `reports/hunt-*.md` ownership routing) — none of them
`enforcement-boundary.md`/`generated-paths.md` registration. #744's own
acceptance criterion requires legitimate denials to keep denying; a
denial for a genuinely unregistered gate module is legitimate by
construction (that is what #441/#684 exist to catch). Merging would
conflate a noise-reduction audit of three unrelated mechanisms with a new
mechanism addition that #744's own rules already endorse keeping strict.
Kept separate; this proposal's own new hook adds itself as one more
"legitimate denial" #744's regression coverage should protect, not weaken.

## What will be done

1. Add the two missing rows (`record-claim-shape-directive.sh`) to
   `docs/specs/enforcement-boundary.md` (verdict `contract`, same act-class
   as the existing `directive.sh` row) and `docs/specs/generated-paths.md`
   (classification `n/a`, same as the existing `record-claim-guard.sh` row
   — confirmed no write call in the file).
2. Add a fixed `tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge`
   mock for `closure_sweep._pr_index_all` (`lambda root: (None, True)`,
   with the matching teardown), mirroring the fix already landed for the
   sibling test in `gates/test_closure_sweep.py`.
3. Add `on-the-record/hooks/gate-registration-guard.sh` — new
   `PreToolUse`+`Bash` hook. On a staged `git commit` whose
   `git diff --cached --name-status` includes an `A` (added) entry under
   `gates/*.py` (excluding `test_*.py`/`__init__.py`, matching
   `gates/test_boundary.py`'s own `_actual_mechanisms()` exclusions),
   `on-the-record/hooks/*.sh`, or `.github/workflows/*.yml`: read the
   staged (or, if not itself staged, on-disk) content of
   `docs/specs/enforcement-boundary.md` and deny the commit if the new
   file's basename has no row there; for a newly-added `on-the-record/hooks/*.sh`
   file specifically, additionally check `docs/specs/generated-paths.md`
   the same way. Fails open on missing `python3`/`git`, a non-`git commit`
   Bash command, or no matching newly-staged file. `ORCHESTRATE_OFF` kill
   switch, matching every sibling.
4. Add `on-the-record/hooks/test_gate_registration_guard.py`: a red case
   (new `gates/*.py` file staged with no boundary row -> denied, exit 2),
   the acceptance criterion's required green case (a change touching no
   new mechanism file -> passes untouched), and a case where the new
   file's row is staged in the same commit -> passes.
5. Wire `gate-registration-guard.sh` into `on-the-record/hooks/hooks.json`'s
   `PreToolUse`+`Bash` matcher array, next to `role-axis-completeness-guard.sh`.
6. Add an `enforcement-boundary.md` row and a `generated-paths.md` row for
   `gate-registration-guard.sh` itself (`contract` / `n/a` respectively —
   it only reads and denies, same shape as its two siblings), then
   regenerate `docs/specs/reconciled-index.md`
   (`python3 gates/spec_index.py --update`), the mandatory companion for
   any `docs/specs/*` edit.
7. Re-run `python3 -m pytest gates/ tests/ -q` and confirm 0 failures.

## Out of scope

- Introducing GitHub Actions/CI (already decided against, #460).
- Any test cleanup beyond the three named failures.
- #744's three named noise items — investigated for overlap only, not
  addressed here.
- Auto-classifying a new row's verdict text (e.g. guessing `contract` vs
  `repo-local` for a brand-new gate module) — the guard requires a row to
  exist, matching #441/#684's own presence-only check; judging the
  correct verdict text stays a human/session decision at write time, same
  as it is today.

## How you'll know it worked

- `python3 -m pytest gates/ tests/ -q` — 0 failures (currently 3).
- `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py -q`
  — new red/green fixture cases pass, demonstrating a new unregistered
  gate module is denied at the landing path and a non-registration-target
  change passes untouched (issue #759's second acceptance criterion,
  including its stated empty-state green case).

## Accumulation

This touches two accumulation-prone shapes: `on-the-record/hooks/hooks.json`
gains one more repeated one-line entry (26 existing `PreToolUse`/`Bash`
command lines today; this is entry 27, same shape as every prior guard
addition — no shared helper exists for this file because each hook is
deliberately a self-contained, zero-install script, so there is nothing
to factor out), and `docs/specs/enforcement-boundary.md`/
`docs/specs/generated-paths.md` each gain 2 more table rows. If N more
gate modules or hooks land after this proposal, each contributes exactly
one row to each spec table and, for a hook, one `hooks.json` line — linear
growth already inherent to these three files' existing design (every one
of the current hooks and spec rows already grew the same way, one at a
time, since issue #441/#684/#457). `gate-registration-guard.sh` itself
uses two inline `subprocess.run` calls (`git diff --cached --name-status`,
`git show :<path>`) — the same two calls `spec-index-preflight.sh` and
`role-axis-completeness-guard.sh` already each make independently; no
third repetition-worth extracting a shared helper for yet, and no sibling
hook imports another hook's subprocess logic (each stays a standalone
script by design), so this proposal does not introduce a new instance of
the inline-subprocess-accumulation shape #424 tracks — it repeats an
already-accepted two-instance pattern for a third time in the same style.
