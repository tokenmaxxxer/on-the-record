# Survey — issue #1695

Scout skip: spec leaves no product-facing design decision open (internal
CLI scaffolding, format dictated by the existing generator's own output
shape) — skipping scout sweep per survey-order-directive's second skip
condition.

## Current state

- `spawn.py:878` `init_board(cwd, login)` — creates `docs/specs/approvers.md`
  in the target repo if absent; never overwrites (`dest.exists()` check at
  spawn.py:888). This is the `spawn.py init` entrypoint (dispatched at
  spawn.py:6816-6818).
  canonical: spawn.py:878-901
- `spawn.py:1038` `require_requirement_linkage` — blocks a fresh (no prior
  `issue-<n>/*` branch, no phase-2 approval yet) issue spawn unless its body
  cites an `R\d+` / `northpole req#<n>` ID or carries the
  `infrastructure/no-direct-requirement` tag. This gate reads the ISSUE BODY
  only — it never reads `docs/specs/requirement-digest.md` itself. The
  digest file's role is purely: give the human/agent something to cite an
  R-ID *from* on a brand new target repo, not something the gate machinery
  parses.
  canonical: gates/requirement_linkage.py:43-58 (`check_issue_body`)
- `gates/requirement_digest.py` — this repo's OWN generator: renders
  `docs/specs/requirement-digest.md` from `docs/specs/requirements.md` via
  `update()`/`--update`. Not reusable as-is for a fresh target repo: it
  requires `requirements.md` to already exist and parses `## R\d+` blocks
  from it.
  canonical: gates/requirement_digest.py:23-58 (`_REGISTRY_REL`, `parse()`, `update()`)
- This repo's own `docs/specs/requirement-digest.md` header assumes a live
  `requirements.md` registry, which a freshly inited target repo won't
  have — issue #1695 asks for a stub the human populates directly (first
  issue "adds R1 in the same flow"), not a generator invocation.
  canonical: docs/specs/requirement-digest.md:1-3

## Write set

- `spawn.py` — add a small helper that writes
  `docs/specs/requirement-digest.md` with a documented R-entry format stub,
  called from `init_board`, only when the file is absent.
- `tests/test_spawn.py` — unit tests: creates-when-absent (with format
  stub content), no-overwrite-on-second-run, existing-ledger-untouched.

No alternative implementation file exists to reuse — the generator is
registry-driven and requires `docs/specs/requirements.md` to already exist,
which a freshly inited target repo does not have (same citation as above).
