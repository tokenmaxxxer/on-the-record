# Conformance-review proposal — issue-304 phase 2 (Playwright cache mount)

## Upstream / basis

Issue #304. Merged architecture: `docs/issue-304/proposals/architecture.md`
(`APPROVE issue-304/architecture`). Delivered implementation: PR #307
(`issue-304/implementation`, merged, `APPROVE issue-304/implementation`),
commit `933be5e9` (`spawn.py`, `docs/issue-304/decisions/
playwright-cache-mount.md`, `docs/issue-304/reports/implementation.md`).

## Requirement list (extracted, verdict deferred to phase 2)

Requirements below are architecture.md's "What will be done (phase 2, on
approval)" list, items 1-3 verbatim, plus the verification criteria named
in architecture.md's "How this will be verified" section. Phase 2 renders
one Present/Surface/Absent/Incorrect/Unverifiable verdict per row, from the
artifact and spec only.

1. **Item 1 -- Add `("PLAYWRIGHT_BROWSERS_PATH", "~/.cache/ms-playwright")`
   to `PACKAGE_CACHE_DIRS` in `spawn.py`.** Source: architecture.md, "What
   will be done" item 1. Check: the tuple appears in `PACKAGE_CACHE_DIRS`,
   same `(env_var, default_path)` shape as the pre-existing entries; no
   other entry in that list changed.

2. **Item 2 -- Add a `playwright_cache_layer()` function mirroring
   `go_proxy_layer()`, wired wherever `go_proxy_layer()`'s result is wired
   into the spawned environment.** Source: architecture.md, "What will be
   done" item 2. Check: the function exists next to `go_proxy_layer()`,
   reads the same `PACKAGE_CACHE_DIRS` entry, checks the resolved host
   path against `s["sandbox"]["filesystem"]["allowRead"]`, and the call
   site sets `extra_env["PLAYWRIGHT_BROWSERS_PATH"]` in the same block and
   under the same `issue is not None` scope as the existing `GOPROXY`
   wiring. Also check: the diff touches no line under
   `sandbox.network.allowedDomains` or `PACKAGE_REGISTRY_HOSTS` -- the
   architecture's "zero network-surface cost" claim for this item is a
   verdict input, not an assumption.

3. **Item 3 -- Record an ADR under `docs/issue-304/decisions/` with a C4
   note on where the approval gate sits relative to
   `sandbox.network.allowedDomains`.** Source: architecture.md, "What will
   be done" item 3. Check: the ADR file exists, same commit, and states
   the filesystem-allowRead/denyRead layer and the
   network-allowedDomains-plus-Bash-approval-gate layer as two separate
   layers, naming which one this change touches.

4. **Item 4 (verification-coverage check, not a phase-2 deliverable
   item) -- the live-launch verification criterion architecture.md names.**
   Source: architecture.md, "How this will be verified" ("a
   Playwright-driven check in a role session no longer attempts a CDN
   fetch (observable via absence of an approval-gate prompt for that
   host)"). Check: whether `docs/issue-304/reports/implementation.md`'s
   "Effect verification" section reports this specific check as executed,
   and if not, whether the gap is disclosed as a limitation rather than
   asserted as done.

## Out of scope (phase 2 will not re-litigate)

- Whether keep-with-adjusted-settings was the right call versus
  removing/narrowing the sandbox -- that judgment belongs to the approved
  architecture proposal, not to this implementation-fidelity review.
- Code-quality judgment (naming, structure, efficiency) -- this role
  renders per-requirement fidelity verdicts only, never a holistic quality
  read.
- Issue #303's cache-enumeration-pattern replacement -- implementation.md's
  own scope note states this change follows the existing hardcoded-list
  pattern because #303 has not landed; not a conformance gap for #304.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `spawn.py`, `docs/issue-304/
decisions/playwright-cache-mount.md`, and architecture.md only -- the
builder's implementation.md prose ("Why", "What was done") is not read as
evidence for verdicts, consistent with this role's artifact-only rulebook;
it may be cited only to locate code, never to substitute for reading the
code and the ADR directly.

## What did not work

None yet -- phase 1, no verdicts attempted.

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None at phase 1.

## Next steps

Await approval (`APPROVE issue-304/conformance-review`). On approval:
render the phase-2 per-item verdicts (items 1-4 above) in
`docs/issue-304/reports/conformance-review.md`.

## Resolution path

Not applicable -- phase 1 has no findings to resolve.
