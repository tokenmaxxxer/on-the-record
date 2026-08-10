files:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py

## Request

Hunt #628 found that `delegated-judgment-gate.sh` exits 0 with no output
at all when `origin/main` is absent — a shape a fresh consumer clone can
have. Fix it so that shape produces an explicit outcome, never a silent
no-op; ship a red/green fixture pair.

## Constraints

- Never deny the underlying `gh pr create` command — the hook's existing
  fail-open posture (it only judges alongside the command) stays.
- No new dependency, no `gates`-package import, no on-the-record checkout
  resolution (zero-install consumer-surface constraint already documented
  in the script's header).
- The existing "diff succeeded, zero changed paths" silent exit is
  legitimate (nothing changed under the PR) and must stay silent —
  only the "diff command itself failed" case needs to become non-silent.

## Rationale

Two ways to fill the gap:

1. **Refuse-and-instruct** (chosen): detect that `git diff --name-only
   origin/main...HEAD` failed for reason "no such ref" specifically, and
   post one `gh issue comment` naming the missing ref and the fix
   (`git fetch origin main`), then exit 0.
2. **Resolve a sensible default**: silently fall back to comparing
   against local `main` (or another guessed ref) when `origin/main` is
   missing.

Alternative 2 is rejected: it swaps one silent behavior (no-op) for
another (silently diffing against a possibly-stale or wrong local ref)
in exactly the fresh-clone shape the hunt flagged as risky — a silent
fallback is *harder* to notice than the no-op it replaces, since it still
produces gate output, just against unverified data. Refuse-and-instruct
keeps the hook's fail-open posture (never blocks `gh pr create`) while
making the failure legible instead of guessing.

## What will be done

- In `_run`, or at the `origin/main` diff call site, distinguish
  "subprocess ran and exited non-zero" (current: collapsed to `None`,
  same as "genuinely empty diff") from a specific origin/main-missing
  signal. Concretely: before the `git diff` call, check whether
  `origin/main` resolves (e.g. `git rev-parse --verify -q
  refs/remotes/origin/main`); if it does not, post a `gh issue comment`
  stating evaluation was skipped because `origin/main` is absent, with
  the fetch instruction, then `sys.exit(0)` — instead of falling into
  the existing `if not paths: sys.exit(0)` branch.
- Leave the "ref resolves, diff has zero paths" path exactly as today
  (silent — legitimately nothing changed).
- Add to `test_delegated_judgment_gate.py`: a red/green fixture pair
  using the file's existing harness (`_init_target`, `_stub_gh`, `_run`)
  — one fixture that omits the `git update-ref
  refs/remotes/origin/main main` step `_init_target` normally performs
  (origin/main absent) and asserts the `gh` log now contains an explicit
  comment naming the missing ref; one fixture keeping `origin/main`
  present (the existing `_init_target` default) asserting current
  behavior is unchanged, reusing/extending an existing passing test as
  the green side of the pair.

## Accumulation

This adds one more explicit-signal branch alongside the script's
existing `sys.exit(0)` early-return chain (already ~8 such checks) and
one more inline `_gh([...])` call alongside the ~10 already in the file
— not a new pattern, an instance of the pattern the script already uses
throughout for "detect condition, post one comment, exit 0." If this
class of fix (a specific subprocess failure silently collapsed into the
generic empty-result branch) recurs at more `_run` call sites — e.g. the
line-336 `rev-parse --abbrev-ref HEAD` case named as out-of-scope below
— the third occurrence should factor a shared `_run_or_report(args,
missing_ref_message)` helper instead of a fourth copy-pasted
ref-existence check; not proposed here since this change introduces only
the first instance of the pattern.

## Out of scope

- The same `_run(["git", "rev-parse", "--abbrev-ref", "HEAD"])` silent-`None`
  pattern (line 336) for a missing/detached HEAD — different failure
  shape, not raised by the #628 hunt or issue #649's acceptance criteria.
- Any other `_run` call site in the script beyond the `origin/main` diff.
- `test_delegated_judgment_gate_triage.py` — it drives the gate via
  `DJG_TARGET`/`DJG_PAYLOAD` directly and does not exercise the `gh pr
  create` / origin-diff path this issue concerns.

## How you'll know it worked

- New red fixture: `origin/main` absent → `gh` log contains an explicit
  comment (not empty), hook still exits 0.
- New/extended green fixture: `origin/main` present, unrelated diff →
  behavior identical to current passing tests (silent when no paths
  changed, normal escalate/approve flow otherwise).
- `python3 on-the-record/hooks/test_delegated_judgment_gate.py` passes,
  all existing `t_*` tests included.
