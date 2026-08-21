---
subject: issue-1803
code_under_review: spawn.py, test/test_convention_equivalence.py, test/test_roster_role_field.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation record — watch/roster explicit role field

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1803/proposals/watch-roster-role-field.md`), approved via
issue comment `APPROVE issue-1803/implementation` from `JiwonJung94`
(listed in `docs/specs/approvers.md`; single-account mode, same account
as PR #1804's author).
canonical: read gh issue view 1803 --json comments this session.

1. `spawn.py:4557` `_workspace_index_put` — dual-write: entry dict now
   `{"work": work, "log": log, "role": role}`. Key construction
   (`spawn.py:4576`) unchanged.
2. `spawn.py:4700` `_live_roster_matches` — reads `v.get("role")` first,
   falls back to `k.rsplit("/", 1)[1]` when absent.
3. `spawn.py:4720` `_ambiguous_watch_exit` — same field-first,
   fallback-second pattern for its candidate-list error text (cosmetic,
   per proposal item 5).
4. `spawn.py:4727` `_roster_fallback_entry` — the no-`role`-given
   candidate scan reads `e.get("role")` first; falls back to
   `re.match(rf"^issue-{issue}/([^/]+)$", k)` only when the field is
   absent, guarding the field-present branch with a
   `k.startswith(f"issue-{issue}/")` check so a field on an unrelated
   issue's key can't leak in.
5. `test/test_convention_equivalence.py` — three new cases added to
   `WatchRosterEquivalenceTest` (field-present path produces identical
   output to the key-split path, for all three read sites); zero edits
   to the three pre-existing golden cases.
6. `test/test_roster_role_field.py` (new, committed at a8220c54) —
   dual-write shape, field-read path, legacy-fallback path (empty-state
   case per acceptance §2), and string-key byte-identity.
   derived: `grep -c 'def test_' test/test_roster_role_field.py` → 8

## Why

Per the frozen #1792 migration-order entry 2 and this issue's
requirements 1-2: stop deriving `role` from the roster/workspace-index
string key by splitting it; carry an explicit field instead,
dual-written so the key format never changes, with read-side fallback
so legacy (pre-change) entries keep working identically.

## Upstream basis

- `docs/issue-1803/proposals/watch-roster-role-field.md` (phase-1,
  approved)
- `docs/issue-1803/reports/implementation/survey.md` (phase-1 current-state
  survey)
- `docs/issue-1792/reports/implementation.md:104-109` (frozen migration
  order)
- a8220c54 (this session's implementation commit)

## Acceptance verification

### 1. Equivalence harness green, additions-only diff

```
$ python3 -m pytest test/test_convention_equivalence.py -q
.........................                                                [100%]
25 passed in 0.82s
```

```
$ git diff --stat test/test_convention_equivalence.py
 test/test_convention_equivalence.py | 56 +++++++++++++++++++++++++++++++++++++
 1 file changed, 56 insertions(+)
```

`git diff test/test_convention_equivalence.py | grep '^-' | grep -v '^---'`
produced zero lines — no deletions, additions only.

canonical: acceptance: `python3 -m pytest test/test_convention_equivalence.py -q` — result: pass (25 passed, 22 pre-existing + 3 new, output pasted above), plus `git diff --stat` pasted above showing additions only

### 2. Dual-write/field-read/legacy-fallback + key byte-identity

```
$ python3 -m pytest test/test_roster_role_field.py -q
........                                                                 [100%]
8 passed in 0.84s
```

canonical: acceptance: `python3 -m pytest test/test_roster_role_field.py -q` — result: pass (8 passed, output pasted above, including the legacy-only-entry empty-state case and the key byte-identity case)

## What did not work

None.

## Test-tier note

No `.on-the-record/test-tiers.json` present at repo root — full-suite
tiering does not apply here; both acceptance checks ran the two named
files directly, each well under a second.

## Open findings

None.

## next steps

None — this record's kind (`implementation`) is at terminal `loop_state:
landed`.
