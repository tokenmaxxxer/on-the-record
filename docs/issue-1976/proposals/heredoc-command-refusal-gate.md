---
status: proposed
files:
  - on-the-record/hooks/heredoc-command-refusal-gate.sh
  - on-the-record/hooks/test_heredoc_command_refusal_gate.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
---

## Request

Issue #1976: role sessions' first `git commit`/`gh pr create` attempt
routinely uses a heredoc-shaped message/body and is refused by the
host's default write-capable-command classifier as un-analyzable, with
no actionable next step — sessions burn 1-3 retries discovering the
single-line `-m -m`/`--body-file` workaround independently. Acceptance:
the refusal text for a heredoc commit/PR shape must include the literal
sanctioned alternative, asserted by the hook's own test, run live.
Scope: `on-the-record/hooks/` only — `spawn.py` is issue #1978's.

## Constraints

- design-research-skip: mechanical (per the issue's own flag) — no
  product-facing design decision is open; scouting was skipped for this
  reason.
- Scope is `on-the-record/hooks/` + its tests; `spawn.py` (the other
  half of the issue's either/or acceptance path) is out of bounds.
- Must not regress `gh-write-allow-gate.sh`'s existing orchestrator
  quoted-heredoc allow path for the five `gh` verbs it recognizes.

## Rationale

Considered extending `gh-write-allow-gate.sh` itself to also cover role
sessions and `git commit`, rather than adding a new hook. Rejected: that
gate's own design (survey citation:
on-the-record/hooks/gh-write-allow-gate.sh:15-16,58-77) is contractually
orchestrator-only ("(a) CLAUDE_ROLE resolves empty — orchestrator only,
never a role session") and only ever emits `"allow"`, never `"deny"` —
repurposing it to deny for role sessions would invert its documented
composition guarantee ("this hook only ever ADDS a permission signal; it
never emits deny itself") that other gates rely on for safe ordering.
Also, `git commit` is entirely outside its five recognized verb shapes,
so extending it would mean bolting an unrelated verb and an unrelated
(deny, not allow) polarity onto a gate whose registered contract row
explicitly promises neither.

Considered relying solely on the host's own default classifier message
and doing nothing in this repo. Rejected: the classifier's message is
not editable from this repo (see survey's `unverifiable:` note), so
"make the refusal actionable" can only be satisfied by a hook this repo
owns.

Chose: a new, narrowly-scoped hook,
`heredoc-command-refusal-gate.sh`, mirroring `gh-write-allow-gate.sh`'s
proven identity/shape-detection primitives (SessionStart-snapshot role
resolution, zero-install python-in-heredoc `PreToolUse`+`Bash` pattern)
but with inverted polarity (deny, not allow) and inverted role scope
(role sessions, not orchestrator) — the exact population and command
shapes the issue's dogfooding note names.

## What will be done

- Add `on-the-record/hooks/heredoc-command-refusal-gate.sh`: for a role
  session, denies (`permissionDecision: "deny"`, exit-code-2) a `git
  commit`/`gh issue create`/`gh issue comment`/`gh pr create`/`gh pr
  comment` command containing any `<<` heredoc redirection, with a
  message naming the sanctioned alternative literally (two `-m` flags
  for `git commit`; `--body-file <path>` for the `gh` verbs). A command
  already in the sanctioned shape (no `<<`) is untouched.
- Add its live-fire test,
  `on-the-record/hooks/test_heredoc_command_refusal_gate.py`, asserting
  the exact deny/no-op outcomes and that the deny message contains the
  literal alternative text, run live via `python3
  on-the-record/hooks/test_heredoc_command_refusal_gate.py`.
- Wire it into `on-the-record/hooks/hooks.json`'s `PreToolUse`+`Bash`
  matcher group.
- Add its rows to `docs/specs/enforcement-boundary.md` and
  `docs/specs/generated-paths.md` (mechanical registration required by
  `gate-registration-guard.sh`/`live-fire-test-guard.sh`).

## Out of scope

- `spawn.py` / the spawned task directive's command-form contract line
  (issue #1978's territory).
- Changing the host's own default permission classifier (not reachable
  from this repo).
- Extending `gh-write-allow-gate.sh`'s orchestrator-only allow path to
  cover role sessions or `git commit` (see Rationale).

## How you'll know it worked

`python3 on-the-record/hooks/test_heredoc_command_refusal_gate.py`
passes live, asserting: a role session's heredoc-shaped `git commit`/`gh
pr create`/`gh issue comment` is denied with a message containing the
literal `-m "<title line>" -m "<body line>"` / `--body-file <path>`
alternative; the sanctioned two-`-m`/`--body-file` shape and the
orchestrator session are both untouched (exit 0, no stderr).
