---
status: proposed
files:
  - spawn.py
  - test/test_skill_repo_managed_clone.py
---

## Request

`_skill_repo_root()` in spawn.py resolves only env `MUSTER_SKILL_REPO`
and the sibling clone `$TOKENMAXXXER_RULEBOOKS/skill-repository`
(issue #1742's deliberate phase-1 restriction, from before
skill-repository was public). Any mapped-role spawn with neither set
now fails closed — observed live on 2026-08-21 on a watchdog-initiated
spawn with no inherited env. Since skill-repository is now public, give
it the same managed-clone fallback `spawn.py` already runs for the
on-the-record/core checkouts: `MUSTER_SKILL_REPO` env > sibling clone >
managed clone of `https://github.com/tokenmaxxxer/skill-repository`,
reusing the existing clone/refresh helper's freshness policy and
offline-reuse behavior, with fail-closed preserved when all three
sources come up empty.

## Constraints

- Resolution order is fixed by the issue: env > sibling > managed
  clone. No reordering, no new precedence rule.
- Requirement 2: the managed-clone path must yield identical skill
  resolution and record fields (`source=skill-repo` + commit sha) as an
  env-pointed checkout of the same commit — no new/different fields for
  the managed-clone case.
- Requirement 4: env or sibling resolving must remain byte-identical to
  today, with **no network touch** in that case — the managed-clone
  branch must be unreachable whenever `_skill_repo_root()` already
  returns non-`None` from the first two checks.
- Requirement 3: fail-closed message must name the managed-clone
  attempt, not just env/sibling, when all three are unavailable.
- No change to the four-source `--skills` precedence (issue #1774) other
  than the skill-repo source becoming resolvable via the managed clone.

## Rationale

**Chosen approach:** inline a third instance of the existing five-step
managed-clone sequence (local-override check → managed-dir validity
check → pull-if-stale-else-reuse → clone-if-absent →
validity-recheck-or-fail) directly inside `_skill_repo_root()`, reusing
the existing primitives (`_locked_rulebook_dir`, `_run_net`,
`_pull_is_fresh`/`_mark_pulled`, `CLONE_TIMEOUT`, the
`ROOT/"runs"/"rulebooks"/<name>` area) verbatim — the same primitives
`core_root()` and `rulebook_checkout()` already share. Validity is
checked with plain `is_dir()` non-emptiness (skill-repository has no
marker file analogous to core's `plugin.json`; its own presence as a
non-empty directory is what `resolved_skill_dirs()` already treats as
"a real checkout" for the env/sibling cases, so the managed clone must
satisfy the identical bar to produce identical downstream behavior per
requirement 2).

**Rejected alternative 1 — extract a shared
`clone_or_reuse(name, url, valid) -> Path | None` helper used by all
three call sites (`core_root()`, `rulebook_checkout()`, and the new
skill-repo branch), refactoring the two existing sites to call it.**
Rejected because it touches `core_root()` and `rulebook_checkout()`,
both outside this issue's declared scope (`spawn.py`,
`test/test_skill_repo_managed_clone.py` — scope line in the issue names
the file, not "refactor the clone helper"), and because the two
existing instances already tolerate the same duplication
(`core_root()` did not generalize `rulebook_checkout()` when it was
added) — matching that established precedent keeps the diff to the one
new call site the issue actually asks for, at the cost of one more
repetition of the five-step sequence. If a fourth managed-clone
consumer appears later, that is the point to extract the shared helper,
not now.

**Rejected alternative 2 — require a marker file inside the
skill-repository clone (mirroring core's `plugin.json` check) before
treating it as valid.** Rejected because skill-repository ships no such
marker today, and inventing one would mean either (a) requiring an
out-of-scope change to the skill-repository repo itself, or (b) picking
an arbitrary existing file (e.g. a specific skill's `SKILL.md`) as a
proxy marker, which is more fragile than the `is_dir()`-non-empty check
`resolved_skill_dirs()` already applies uniformly to every
`_skill_repo_root()` return value today. Matching the existing
validity bar is what requirement 2's "identical skill resolution"
actually requires.

## Accumulation

This proposal inlines a third copy of the five-step managed-clone
sequence (see Rationale) rather than extracting a shared helper, so it
is fair to ask what happens if a fourth (or fifth) managed-clone
consumer shows up later. Answer: each new consumer adds one more inline
copy of the same five-step shape, parameterized by its own repo
URL/managed-dir name/validity check — linear growth, not compounding,
since every copy is independent (no shared mutable state, no coupling
between copies). The threshold this proposal sets: the third instance
(this one) is still tolerable duplication, matching the precedent that
`core_root()` did not generalize `rulebook_checkout()` either; a fourth
instance is the trigger to extract the shared `clone_or_reuse(name,
url, valid) -> Path | None` helper described as rejected-alternative-1
above, at which point all three-then-four call sites would be
refactored onto it in one pass rather than added to piecemeal.

## What will be done

1. Extend `_skill_repo_root()` (spawn.py:5147-5163): after the env and
   sibling checks both miss, add a managed-clone branch targeting
   `ROOT / "runs" / "rulebooks" / "skill-repository"`, wrapped in
   `_locked_rulebook_dir(d)`:
   - If `d` is already a non-empty directory (has at least one
     non-dot subdirectory, matching what `resolved_skill_dirs()`
     already treats as usable), refresh via `_pull_is_fresh(d)` /
     `_run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], ...)` /
     `_mark_pulled(d)`, same as `core_root()` — on network failure the
     existing local commit is kept and returned (offline reuse,
     requirement 1).
   - Else clone with `_run_net(["git", "clone", "-q",
     "https://github.com/tokenmaxxxer/skill-repository.git", str(d)],
     label, timeout=CLONE_TIMEOUT)`; on success return `d`, on failure
     (or resulting dir still invalid) fall through to the existing
     `None` return.
2. Update the fail-closed message at spawn.py:5176-5177
   (`resolved_skill_dirs()`) to name the managed-clone attempt as a
   third source alongside `MUSTER_SKILL_REPO` and the sibling path
   (requirement 3). Audit `resolve_role_source()`
   (spawn.py:5348-5376) and any other `sys.exit` reachable via
   `_skill_repo_root() is None` for the same message update.
3. Update `_skill_repo_root()`'s docstring (spawn.py:5148-5152) to
   drop the "no managed-clone fallback (issue #1742)" statement and
   describe the new three-source order.
4. Add `test/test_skill_repo_managed_clone.py` covering the acceptance
   checks verbatim:
   - env scrubbed + sibling absent + managed area fresh → managed
     clone runs, resolution succeeds, `source=skill-repo` with the
     clone's commit sha.
   - env scrubbed + sibling absent + clone unreachable + no
     pre-existing managed clone → fail-closed, message names all three
     attempted sources.
   - env set → managed-clone helper (the clone/pull git calls) is not
     invoked; assert via mocking/monkeypatching the git subprocess call
     (or `_run_net`) and asserting zero calls, not just asserting the
     returned path.
   - sibling present → same not-invoked assertion.
5. Paste a live dry-run (env unset, no sibling, managed area fresh) into
   the phase-2 implementation record per acceptance check 1.

## Out of scope

- Refactoring `core_root()` or `rulebook_checkout()` to share a common
  helper with the new skill-repo branch (rejected alternative 1;
  deferred per Accumulation's fourth-instance threshold).
- Any change to skill-repository's own repository content (adding a
  marker file, etc.) (rejected alternative 2).
- Changes to the four-source `--skills` precedence logic itself
  (issue #1774) beyond the skill-repo source becoming reachable via
  managed clone — `resolved_skill_sources()` / `resolve_role_source()`
  bodies are otherwise untouched.
- Pinning the managed clone to a specific commit — it follows the same
  freshness/TTL policy as the other managed clones (issue is silent on
  pinning, and requirement 1 only asks for "reuse the existing
  clone/refresh helper" behavior).

## How you'll know it worked

- `test/test_skill_repo_managed_clone.py` passes, covering all four
  acceptance-check cases above (fresh managed clone, fail-closed with
  no sources, env-set no-invoke, sibling-present no-invoke).
- A live dry-run with `MUSTER_SKILL_REPO` unset, no sibling checkout,
  and a fresh (or absent) managed-clone area produces a roster/directive
  record with `source=skill-repo` and the cloned checkout's commit sha,
  pasted into the phase-2 record.
- Manual check: with `MUSTER_SKILL_REPO` set or the sibling present, no
  network call fires (verified by the same no-invoke assertion pattern
  used in the tests, or by running with network disabled).
