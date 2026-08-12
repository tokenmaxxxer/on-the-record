# Current-state survey — issue #1017

## What exists today

- `gates/requirement_digest.py` (issue #930) renders
  `docs/specs/requirement-digest.md` from `docs/specs/requirements.md` —
  one line per live (non-`stale`) requirement, `- R###: <paraphrase>
  [<status>] (source: #<issue>)`.
- `spawn.py::requirement_drift()` (issue #930 req#6, wired into
  `_board_wide_sweep`) is the drift guard the issue's Basis cites. Each
  watchdog tick it lists open issues/PRs via `gh issue list` / `gh pr
  list`, regex-matches `\bR\d+\b` and `northpole req#<n>` in title+body,
  and prints two advisory lines: live requirement IDs mentioned nowhere
  open, and open issues/PRs citing no requirement ID at all. It never
  adds to `anomaly_count` (advisory contract, same as
  `accumulation_trend()`) and never blocks anything.
- `gates/acceptance_gate.py` (issue #310/#416/#499) is the closest
  existing "backstop for issue bodies" shape: `check_issue_body(issue,
  body)` is a pure function (issue number + body text in, violation list
  out, no `gh` call) so it is unit-testable offline; `check(root, issue)`
  wraps it with a `gh issue view` fetch. It is wired into session start
  via `spawn.py::require_acceptance_gate()`, which gates only when the
  issue already has phase-2 approval (`_ci._approved_roles_on_issue`) —
  phase-1/drafting issues are explicitly exempted ("Acceptance 가 아직
  초안 단계이므로 건드리지 않는다").
- Nothing today checks a newly-drafted issue for requirement linkage at
  draft time, and nothing propagates an issue's linked requirement
  ID(s) into the text handed to a spawned role session.
- `gates/test_requirement_digest.py` covers only `requirement_digest.py`
  itself (parse/render/check/update); it carries no linkage-check case
  today.

derived: `grep -n linkage gates/test_requirement_digest.py`
```
(no output — no existing linkage case)
```

## Gaps issue #1017 asks to close

1. **Issue-drafting anchor** — no gate exists that inspects a newly
   drafted issue for a missing requirement-ID citation (or an explicit
   infrastructure tag). `acceptance_gate.py` is the nearest sibling
   pattern (pure `check_*_body(issue, body)` function, offline-testable,
   wired at spawn time) but checks a different section (`## Acceptance`)
   for a different property (executable-artifact reference).
2. **Spawn-task linkage passthrough** — `spawn.py` has no code path that
   reads an issue's cited requirement ID(s) and includes them in the
   task text handed to a spawned role. `require_acceptance_gate` shows
   the established pattern for "read something from the issue body at
   spawn time and act on it."
3. **Digest-linked next-action line** — `requirement_drift()`'s
   `unmentioned_live` branch only prints the bare ID list
   (`열린 이슈/PR 어디에서도 언급되지 않는 살아있는 요구 {unmentioned_live}`).
   The digest line for that ID already carries a paraphrase and source
   issue (`- R001: <paraphrase> [status] (source: #321)`) — that text is
   available but currently discarded when building the warning.

## Write set implied by the above

- A new gate module under `gates/` for the drafting-anchor check,
  shaped like `acceptance_gate.py`: a pure `check_issue_body(issue,
  body)` function so it is usable both standalone and from
  `gates/test_requirement_digest.py`'s new cases.
- `gates/test_requirement_digest.py` — gains the linkage-check cases the
  issue's Acceptance section names explicitly: one case for an untagged
  new issue, one case for a tagged infrastructure issue.
- `spawn.py` — `requirement_drift()`'s uncited-live-requirement branch
  gains a concrete next-action line (requirement ID + its digest
  paraphrase + which issues/PRs are missing it); a passthrough point
  that includes an issue's cited requirement ID(s) in spawn-task text.
- The phase-2 implementation record (not written this phase — phase-1
  output only).

## Skip-condition check (scout directive)

Scouting in the external-field sense does not apply here: this is a
plugin-internal gates/orchestrator change with no external product
category to benchmark against. The applicable design decisions (tag
string, regex shape, next-action line wording) are settled by mirroring
`acceptance_gate.py`'s already-adopted, in-repo convention rather than
researching an external field — the spec and existing precedent leave
no open design decision that external scouting would inform. Recorded
per the scout directive's skip-record requirement.
