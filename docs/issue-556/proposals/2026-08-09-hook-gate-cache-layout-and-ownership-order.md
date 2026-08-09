---
status: proposed
files:
  - on-the-record/hooks/role-spec-reference-guard.sh
  - on-the-record/hooks/record-claim-guard.sh
  - on-the-record/gates/gates.py
  - on-the-record/gates/record_lint.py
  - on-the-record/gates/role_spec_shape.py
  - on-the-record/hooks/test_hook_cache_layout.py
  - docs/issue-556/reports/implementation/survey.md
---

## Request

Fix two compounding defects in `role-spec-reference-guard.sh` and
`record-claim-guard.sh`: (1) both resolve their `gates/` module directory as
`hooks/../../gates`, which does not exist once the plugin is copied into the
deployed cache layout, so importing the gate module raises
`ModuleNotFoundError`; (2) because each hook fails closed on any non-0/2
exit, that crash denies every write the hook sees — including writes to
paths entirely outside the hook's owned surface (memory dirs, scratchpads)
— because the ownership test currently runs *after* the crashable import.

## Constraints

- Fail-closed must be preserved for gate-owned paths: if the gate module is
  genuinely unimportable, a write to an owned path must still be denied.
- Paths outside the owned surface must pass through even when the gate
  module is completely broken — the ownership test itself must not depend
  on anything that can fail to import.
- No new third-party dependency; `gates.py`/`record_lint.py`/
  `role_spec_shape.py` are already stdlib-only or depend only on each other.

## Rationale

Two packaging options were weighed for making `gates/` reachable from the
plugin cache:

- **Symlink `on-the-record/gates` to the repo-root `gates/`.** Rejected:
  whether marketplace packaging follows symlinks when it copies
  `./on-the-record` into the cache is unverified, and a broken symlink in
  the cache reproduces exactly this issue's failure mode. A real file copy
  has no such dependency on packaging-tool symlink behavior.
- **Copy `gates.py`, `record_lint.py`, `role_spec_shape.py` into
  `on-the-record/gates/` as packaged files (chosen).** The three files are
  self-contained (stdlib-only, or depending only on the sibling `gates.py`
  copied alongside them) — verified by reading their import lists in the
  survey. This makes `on-the-record/` a complete, self-sufficient plugin
  tree, matching what the cache actually copies, at the cost of one
  small duplicated file set that mirrors the repo-root originals.

Ownership-before-import is not a design choice with a rejected alternative
— it is the issue's own stated acceptance requirement (checks 2 and 3) —
so no alternative is weighed for it.

## What will be done

- In both hooks' Python guard: move the ownership test (the
  `record_path_role`/regex check) to run first, using only stdlib logic
  that needs no `gates/` import — `role-spec-reference-guard.sh` inlines
  the same two-line regex `record_path_role` already applies (verification-
  family roles' `docs/issue-<n>/reports/<role>.md`), duplicated in the hook
  itself rather than imported, so the check does not depend on a
  successful import. `record-claim-guard.sh`'s ownership test is already a
  plain regex with no import dependency — it only needs to move above the
  `import record_lint` line.
- Only after the path is confirmed owned does the guard import the gate
  module, inside a `try/except ImportError` that calls `deny()` (exit 2) —
  preserving fail-closed for owned paths whose gate module can't load. The
  guard checks the resolved gates dir is a non-empty string *before*
  calling `sys.path.insert(0, ...)`: an empty string there means "current
  working directory" to Python, which would let a same-named file planted
  in cwd be silently imported instead of raising `ImportError` — an
  after-proposal hunt (stance 0, docs/reports/2026-08-09-hunt-hook-gate-cache-layout-and-ownership-order.md)
  reproduced exactly this bypass against the pre-fix hooks. When the
  resolved dir is empty, the guard treats that the same as an import
  failure (`deny()` for owned paths) without ever inserting `""` into
  `sys.path`.
- In both hooks' bash preamble: resolve `gates_dir` by checking, in order,
  `$script_dir/../gates` (packaged: `on-the-record/gates/`, matches the
  cache layout) then `$script_dir/../../gates` (repo-root dev layout);
  use whichever exists, or leave it unset if neither does — no more hard
  `cd ... && pwd` that can itself abort the assignment silently into an
  empty path passed straight to Python.
- Add `on-the-record/gates/gates.py`, `on-the-record/gates/record_lint.py`,
  `on-the-record/gates/role_spec_shape.py` as packaged copies of the
  repo-root originals.
- Add `on-the-record/hooks/test_hook_cache_layout.py`, a committed test
  covering the issue's three acceptance checks: (1) each hook invoked with
  `CLAUDE_PLUGIN_ROOT` pointed at a simulated cache dir (hooks + the new
  packaged `gates/` copied in, repo-root `gates/` absent) exits without an
  unhandled `ModuleNotFoundError`; (2) with the gate module deliberately
  made unimportable, a write outside the owned surface exits 0; (3) same
  broken-import setup, a write to an owned path (`docs/issue-*/reports/**`
  or the verification-family record shape) still exits non-zero.

## Out of scope

- Any hook other than `role-spec-reference-guard.sh` and
  `record-claim-guard.sh` — no other hook builds a `gates_dir` or imports a
  `gates/` module (confirmed in the survey).
- A general drift-prevention mechanism keeping the packaged `gates/` copies
  in sync with the repo-root originals automatically (e.g. a build step or
  a CI diff check) — noted as a follow-up, not built here; the copies are
  small (3 files) and change rarely.
- `impact-guard.sh`'s target-repo `gates/` resolution — a different
  mechanism (locates the *target* repo's own gates, not this plugin's).

## How you'll know it worked

- `bash -n` passes on both edited hooks.
- The new `on-the-record/hooks/test_hook_cache_layout.py` fails against
  the current `main` (reproducing the issue) and passes on this branch,
  covering all three acceptance checks from the issue body.
- Existing hook tests (`on-the-record/hooks/test_record_claim_guard.py`
  and any `role-spec-reference-guard.sh` coverage) still pass unchanged,
  confirming fail-closed and normal-path behavior are unaffected by the
  reordering.
