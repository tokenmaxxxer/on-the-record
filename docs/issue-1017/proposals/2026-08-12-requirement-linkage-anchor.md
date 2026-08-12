---
status: proposed
files:
  - gates/requirement_linkage.py
  - gates/test_requirement_digest.py
  - spawn.py
  - docs/issue-1017/reports/implementation.md
---

## Request

The watchdog's drift guard (`spawn.py::requirement_drift()`, issue #930
req#6) advisory-warns every tick when a live requirement is cited
nowhere open, but nothing re-anchors work to requirements — detection
without correction. The user asks for three concrete anchors: (1) a
draft-time backstop flagging a new issue that cites no requirement ID
and carries no explicit infrastructure tag, (2) spawn-task text that
passes an issue's cited requirement ID(s) through to the spawned role,
and (3) a drift warning that names the specific missing digest linkage
instead of a bare ID list. Advisory stays advisory for existing issues;
the structural check applies only to newly drafted issues/spawns.
Plugin-only, default-on.

## Constraints

- No retroactive blocking of existing issues — only new issue drafts and
  new spawns are checked structurally.
- The explicit "no direct requirement" escape must be a distinct,
  greppable tag string, not free prose (mirrors `acceptance_gate.py`'s
  `unverifiable:` convention).
- `gates/test_requirement_digest.py` gains the linkage-check cases named
  in the issue's Acceptance section: an untagged new issue is caught by
  the check, and a tagged infrastructure issue is accepted by it.
- Default-on, no config flag to disable it (req#7, mirrors how
  `acceptance_gate.py` has no opt-out).

## Rationale

Considered folding the linkage check into `gates/acceptance_gate.py`
itself (one file, one gate, less surface) instead of a new
`gates/requirement_linkage.py` module. Rejected: `acceptance_gate.py`
checks a specific section (`## Acceptance`) for a specific property
(does it point at an executable artifact) and is wired to fire only
*after* phase-2 approval — the opposite lifecycle point from what #1017
needs (issue-drafting time, before any approval exists). Merging the two
would either weaken acceptance_gate's phase-2-only trigger or force the
new check to piggyback on a wiring point it doesn't belong at. A
separate module mirroring acceptance_gate's shape (pure
`check_issue_body(issue, body)`, offline-testable) keeps both checks
independently wired at their own correct lifecycle point and keeps
`gates/test_requirement_digest.py`'s new cases importing one clear
symbol.

Considered making the digest next-action line reconstruct the missing
linkage via a second `gh` round-trip. Rejected: `requirement_drift()`
already loads `docs/specs/requirement-digest.md` and its per-ID
paraphrase/source line before computing `unmentioned_live` — the
concrete next-action text is already in memory; a second network call
would duplicate cost `requirement_digest.py`'s own module docstring
explicitly designs against (O(live requirement count), not O(issue
history)).

## What will be done

1. `gates/requirement_linkage.py`: `check_issue_body(issue, body) ->
   list[str]` — pass-through when the body cites at least one `R\d+` ID
   (or `northpole req#<n>`, matching `requirement_drift()`'s existing
   regexes) or carries the literal tag `infrastructure/no-direct-requirement`;
   otherwise one violation string naming the issue and the missing
   linkage/tag. `check(root, issue)` wraps it with a `gh issue view`
   fetch, same shape as `acceptance_gate.check`.
2. `spawn.py`: wire the new check at issue-drafting time alongside the
   existing `require_acceptance_gate` call path (new issues only — no
   retroactive scan of open issues); and thread an issue's cited
   requirement ID(s) into the spawn-task text builder so a spawned role
   session sees which requirement(s) it serves.
3. `spawn.py::requirement_drift()`: for each ID in `unmentioned_live`,
   look up that ID's already-parsed digest line (paraphrase + source
   issue) and print a concrete next-action line — which requirement,
   what its digest entry says, and (when available) which open
   issues/PRs are missing the citation — replacing the bare ID-list
   print for that branch. The advisory/non-blocking contract
   (`anomaly_count` never incremented) is unchanged.
4. `gates/test_requirement_digest.py`: add the linkage-check cases named
   in the issue's Acceptance section (untagged new issue is caught;
   tagged infrastructure issue is accepted; issue citing a real `R\d+`
   ID is accepted).
5. `docs/issue-1017/reports/implementation.md`: phase-2 record, written
   at the start of phase 2 per the record-shape directive.

## Accumulation

`gates/requirement_linkage.check(root, issue)` adds one more `gh issue
view` call to the same family `acceptance_gate.check` and
`require_acceptance_gate` already make at spawn/draft time — it does not
add a new per-tick loop. It fires once per issue draft, not once per
watchdog tick, so it does not scale with open-issue count the way
`requirement_drift()`'s existing `gh issue list --limit 1000` /
`gh pr list --limit 1000` pair does. If drafting volume grows Nx, the
added cost is Nx one-shot `gh issue view` calls at draft time, each
independent and already bounded by the same per-issue-view cost
`acceptance_gate.check` pays today — no new unbounded list/scan is
introduced. The `requirement_drift()` next-action line reuses the
already-parsed digest entries in memory (no added `gh` call at all), so
it does not change that function's O(live requirement count) +
O(open issue/PR count) per-tick cost.

## Out of scope

- Retroactive linkage checking of already-open issues (advisory stays
  advisory for those, per the issue's own constraint).
- Changing `acceptance_gate.py` itself.
- Any change to `requirement_digest.py`'s render format — the next-action
  line is assembled in `requirement_drift()` from the existing digest
  text, not a new digest field.

## How you'll know it worked

- `python3 gates/test_requirement_digest.py` passes, including the new
  linkage cases.
- `gates/requirement_linkage.check_issue_body` returns a violation for a
  drafted-issue body with no `R\d+`/`northpole req#` mention and no
  `infrastructure/no-direct-requirement` tag, and returns `[]` for a
  body carrying either.
- `requirement_drift()`'s uncited-live-requirement print names the
  requirement's digest paraphrase and source issue, not a bare ID list.
