# Current-state survey — issue #856

derived: `ls on-the-record/hooks/*allow*.sh`
```
on-the-record/hooks/merge-allow-gate.sh
on-the-record/hooks/spawn-allow-gate.sh
```
canonical: `on-the-record/hooks/merge-allow-gate.sh`, `on-the-record/hooks/spawn-allow-gate.sh` (read in full)
Two allow-gates exist. Neither matches `gh issue create`, `gh issue comment`,
`gh pr comment`, `gh issue close`, or `gh pr close`, per a full read of both
files (`merge-allow-gate.sh` only matches `gh pr merge`;
`spawn-allow-gate.sh` only matches `python3 spawn.py` invocations, no
`gh issue`/`gh pr` string at all).

`on-the-record/hooks/hooks.json`'s `PreToolUse`+`Bash` block registers both
existing allow-gates as the last two entries in that matcher's hook list.

## Design to mirror

canonical: `on-the-record/hooks/spawn-allow-gate.sh`, `on-the-record/hooks/merge-allow-gate.sh` (read in full)

Both existing allow-gates share one shape:
- `case "${ORCHESTRATE_OFF:-}"` kill switch.
- Identity check: `session-role-bind.sh` SessionStart snapshot first (keyed
  by `session_id`, read from `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}`),
  live `CLAUDE_ROLE` env var fallback. Role non-empty -> `exit 0` unreached.
- Strict command-shape validation ported from issue #824/#834:
  `shlex.shlex(cmd, posix=True, punctuation_chars=True)`,
  `whitespace_split = True`; reject outright on any backtick, `$(`, or
  newline in the raw command string before tokenizing; after tokenizing,
  match against a small set of recognized token-prefix shapes (the verb
  itself, optionally preceded by `cd DIR &&`), and refuse if any token in
  the tail after the matched verb is purely composed of shell operator
  characters (`&&`, `;`, `|`, etc.).
- On match: emit `hookSpecificOutput.permissionDecision: "allow"` JSON,
  `exit 0`. On any unmatched shape: plain `exit 0`, no JSON — this hook
  only ever ADDS a permission signal, never emits `"deny"`.

`spawn-allow-gate.sh` is the closer analog for #856 (no readiness
predicate, no target-repo/checkout involvement needed) — `merge-allow-gate.sh`
additionally calls `gates/landing_readiness.py` because merging is a
destructive/consequential act; `gh issue create`/`comment`/`close` and
`gh pr comment`/`close` are non-destructive forge writes, so no equivalent
readiness check applies.

## Registration and spec surfaces touched by prior allow-gates

derived: `grep -n 'spawn-allow-gate\|merge-allow-gate' docs/specs/enforcement-boundary.md docs/specs/generated-paths.md`
```
docs/specs/generated-paths.md:26:| `spawn-allow-gate.sh` | n/a | reads/validates only, no write call |
docs/specs/generated-paths.md:27:| `merge-allow-gate.sh` | out-of-tree | safe ... |
docs/specs/enforcement-boundary.md:93:| `spawn-allow-gate.sh` | contract | new (issue #810 SCOPE EXTENSION 2): ...
docs/specs/enforcement-boundary.md:94:| `merge-allow-gate.sh` | contract | new (#810, candidate 4): ...
```
canonical: `on-the-record/hooks/gate-registration-guard.sh` (read, header docstring)
A newly-staged `on-the-record/hooks/*.sh` file with no matching row in
`docs/specs/enforcement-boundary.md` (and `docs/specs/generated-paths.md`
for its write-safety classification) is refused per that hook's own
docstring. A new allow-gate must add a row to both files in the same
commit, and (since `docs/specs/*` changed) regenerate
`docs/specs/reconciled-index.md` via `python3 gates/spec_index.py --update`
in the same commit (`spec-index-preflight.sh`).

## Existing deny gates over the same `gh` surface

derived: `grep -ln 'gh issue create\|gh issue comment\|gh pr comment\|gh issue close\|gh pr close' on-the-record/hooks/*.sh`
```
on-the-record/hooks/impact-guard.sh
on-the-record/hooks/delegated-judgment-gate.sh
```
canonical: `on-the-record/hooks/impact-guard.sh`, `on-the-record/hooks/delegated-judgment-gate.sh` (read in full)
`impact-guard.sh` denies a *batch* of two-or-more `gh pr merge` calls in one
Bash invocation — unrelated verb, not reached by the five verbs in scope
here. `delegated-judgment-gate.sh`'s own docstring states it "never denies
the underlying command; it only judges alongside it" (always exits 0 once
the payload is well-formed) — so it is not a deny gate for this surface
either. No existing gate in this repo currently denies `gh issue create`/
`comment`/`close` or `gh pr comment`/`close` outright; `approval-gate.sh`
denies role-session *file writes* (`Write`/`Edit`/`MultiEdit` matcher), not
`Bash` `gh` invocations, so it is not directly composable with a
Bash-matcher allow-gate on the same event either. The "deny gate still
wins" composition property is therefore demonstrated in the test suite
with a minimal stand-in deny gate, in the same JSON/exit-code shape a real
deny hook uses — proving the allow-gate itself never emits `"deny"`,
independent of any one specific existing gate's unrelated preconditions.

## Write set

New/changed files this build touches:
- on-the-record/hooks/gh-write-allow-gate.sh (new)
- on-the-record/hooks/test_gh_write_allow_gate.py (new)
- on-the-record/hooks/hooks.json (register the new hook)
- docs/specs/enforcement-boundary.md (registration row)
- docs/specs/generated-paths.md (registration row)
- docs/specs/reconciled-index.md (regenerated)
- docs/issue-856/reports/implementation/survey.md (this file)
- docs/issue-856/proposals/gh-write-allow-gate.md
- docs/issue-856/reports/implementation.md (phase-2 record)
