---
subject: issue-930
kind: scout-brief
---

# Scout brief — requirement digest / drift guard (issue #930)

Mode: batched-sequential repo read (1 stage, ~2min wall-clock) — same
class as issue #922's precedent: this is a protocol/mechanism design
against this repo's own platform and existing conventions, not a
market/competitor choice. No external product exemplar applies; the
"field" to sweep is this repo's own already-shipped analogous
mechanisms, which set the bar this design must clear or explicitly
depart from.

## Must-bes extracted from this repo's own precedents

- `docs/specs/requirements.md` (append-only registry, R001 only so
  far) + `gates/gates.py` (`requirement_registry`, around line 641)
  already gives one requirement a `quote`/`source_issue`/`check`/
  `status` record and a staleness check wired into `gates/ci.py` — but
  these are raw entries, not a condensed digest a fresh session can
  read in one sitting, and nothing regenerates a derived summary from
  them.
- `docs/specs/reconciled-index.md` + `gates/spec_index.py` +
  `on-the-record/hooks/spec-index-preflight.sh` is the load-bearing
  precedent for "auto-maintained derived artifact, enforced hook-only,
  no CI": a PreToolUse Bash hook recomputes a derived file's expected
  content from the staged diff and DENIES the commit if the derived
  artifact wasn't regenerated alongside it. This is the exact
  auto-maintenance shape #930 needs, already proven and already
  req#7-compliant (plugin-only, no Actions, no explicit skill call).
- `docs/specs/enforcement-boundary.md`'s `accumulation_trend()` row
  (around line 49) is the load-bearing precedent for "advisory,
  non-blocking, watch-class" reporting on a board-wide cadence: it
  runs inside `spawn.py` `_board_wide_sweep()`, called every
  `roster_watchdog()` tick, and is explicitly non-blocking — the shape
  a drift guard must copy to stay compatible with the watch-class
  inviolable principle (report, never block).
- `on-the-record/hooks/directive.sh` already fires on every
  `UserPromptSubmit`, in every installed session, with no skill
  invocation — the existing zero-onboarding delivery channel a digest
  pointer should ride, rather than a new hook class.

## Gap line

What the repo already gives: a raw append-only requirement store with
a staleness check (`requirements.md`), a proven auto-regenerate-or-deny
hook pattern for derived docs (`spec_index.py`/`spec-index-preflight.sh`),
and a proven advisory board-wide reporting cadence
(`accumulation_trend()` inside `roster_watchdog()`).

What it does NOT give, and #930 must therefore supply: (1) a CONDENSED
digest distinct from the raw registry — one line per live requirement,
regenerated deterministically, sized O(requirement count) rather than
O(record count); (2) the auto-regenerate-or-deny wiring applied to that
new digest specifically (spec_index.py's wiring covers a fixed doc
list, not this new file); (3) a drift check that compares ACTIVE WORK
(open proposals/PRs) against the live requirement set, which
`accumulation_trend()` does not do today — it counts instance-shape
totals, not requirement-to-work alignment; (4) a fresh-session-reads-
digest-only acceptance harness, which nothing in `harness/` currently
exercises for the requirement registry.

## Adopt / skip

- Adopt: model the digest's auto-maintenance on `spec_index.py` +
  `spec-index-preflight.sh` verbatim (recompute-and-deny on staged
  diff) — proven, req#7-compliant, zero new hook class.
- Adopt: model the drift check on `accumulation_trend()`'s placement
  and non-blocking contract (inside `_board_wide_sweep()`, advisory
  report only) — matches the watch-class inviolable principle already
  documented for that row.
- Adopt: extend `directive.sh` to name the digest path, not a new
  SessionStart hook — reuses the channel already proven to reach every
  session with no explicit invocation.
- Skip: replacing `requirements.md` itself — it is the raw source of
  truth (append-only, one quote per requirement); the digest is a
  derived condensation on top, not a competing store.
- Skip: a digest that recomputes from the full docs/issue-*/reports
  tree — that scales O(records), which is exactly the drift #930
  names as the failure mode; the digest must derive only from
  `requirements.md` (already O(requirement count) by construction).

Sources:
- docs/specs/requirements.md (read this session)
- docs/specs/reconciled-index.md, gates/spec_index.py,
  on-the-record/hooks/spec-index-preflight.sh (read this session)
- docs/specs/enforcement-boundary.md (read this session)
- docs/specs/northpole.md, requirement #6 and #7 sections (read this
  session)
- on-the-record/hooks/hooks.json, on-the-record/hooks/directive.sh
  wiring (read this session)
