# Scout brief — issue-533 (phase 1)

Non-product surface: `spawn.py` is internal orchestration tooling (this
repo's own CLI), not a user-facing product — so "best-in-class category
exemplars" doesn't apply directly. Per scout-directive's non-product
guidance ("scout the best of their own deliverable's kind"), the sweep
targeted (a) this codebase's own existing repo-scoping precedent and (b)
the general engineering pattern for avoiding key collisions in multi-tenant
registries — one round, single angle, saturated fast (the pattern is
well-established and the in-repo precedent already converges with it).

## Must-bes (what strong keying schemes assume)

- Tenant/scope identifier is a **prefix**, not a suffix or side field the
  lookup can forget to check — Kubernetes namespaces work exactly because
  every object lookup is inherently namespace-scoped; there's no
  "look up by name only" code path that can accidentally ignore namespace.
  ([Multi-tenancy | Kubernetes](https://kubernetes.io/docs/concepts/security/multi-tenancy/))
- A hierarchical key shape (`tenant:service:entity:id`) is the standard
  multi-tenant registry pattern specifically to prevent collisions and keep
  scoping mechanical rather than convention-based.
  ([Redis Key Namespaces for Multi-Tenant Apps](https://oneuptime.com/blog/post/2026-03-31-redis-key-namespaces-multi-tenant/view))
- When a collision is nonetheless possible (e.g. two tenants computing the
  same generated identifier), the accepted answer is a hard failure state,
  never a silent overwrite — Kubernetes subnamespace collisions "enter a
  failure state," they don't clobber the existing object.
  ([Kustomize/subnamespace collision handling](https://oneuptime.com/blog/post/2026-02-09-kustomize-namespace-transformer/view))

## Performance axes this fix competes on

1. **Scoping is structural, not optional** — every read path must be scoped
   by the same identifier the write path used; no code path may look up by
   `issue-<n>/<role>` alone once the scope exists.
2. **Collision behavior is loud** — an unexpected same-key write while the
   old entry is still live must fail hard, not overwrite.
3. **No new external dependency for the scope identifier itself** — the
   identifier must be derivable from state already local to the process.

## Adopt / skip

- **Adopt**: prefix-style composite key (`<repo>/issue-<n>/<role>`), hard
  error on live-entry collision, and scoping enforced at both `_put`
  (write) and `_lookup_roster_entry` (read) so `-C` actually changes which
  entries a lookup can see — matching the Kubernetes "namespace as a
  structural, not incidental, part of the lookup" must-be.
- **Skip**: a hash-suffixed key (`<subnamespace>-<hash>` style) — overkill
  for a two-component local scope (repo, already have a stable slug/dir
  name) and would make `workspaces.json` keys illegible to a human running
  `cat runs/workspaces.json` for debugging, which the current
  `issue-<n>/<role>` keys are optimized for.

## Gap line

The codebase already has the *identity-derivation* half of this pattern
(worktree provisioning at `spawn.py:3350-3389` derives repo identity from
`git remote get-url origin` and hard-`sys.exit`s on a mismatch) — the gap
is that this pattern was never extended to `WORKSPACE_INDEX`'s key space or
to `_lookup_roster_entry`'s read path, and `watch`'s `-C` flag is parsed
but never threaded down to the lookup at all (confirmed in survey.md).

## Stages

1 sweep stage (codebase precedent + one general-pattern web search),
JUDGE POINT 1 = the in-repo precedent and the general pattern agree exactly
(prefix-scoped composite key + hard-fail on collision) → no deepening
round needed, saturated immediately.

Sources:
- https://kubernetes.io/docs/concepts/security/multi-tenancy/
- https://oneuptime.com/blog/post/2026-03-31-redis-key-namespaces-multi-tenant/view
- https://oneuptime.com/blog/post/2026-02-09-kustomize-namespace-transformer/view
