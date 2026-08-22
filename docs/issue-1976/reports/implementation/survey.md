---
name: survey
subject: issue-1976
role: implementation
---

# Current-state survey — issue #1976

## Scope

`on-the-record/hooks/` (plus its tests). `spawn.py` is explicitly out of
scope — issue #1978 owns it right now.

## What exists today

Searched `on-the-record/hooks/*.sh` and `gates/*.py` for any gate that
denies a heredoc-shaped `git commit`/`gh pr create`/`gh issue create`/`gh
pr comment`/`gh issue comment` command with a message naming the
sanctioned alternative. None exists.

canonical: on-the-record/hooks/gh-write-allow-gate.sh:77,142-153,178-188 (read file:line)
`gh-write-allow-gate.sh` only ever emits `permissionDecision: "allow"`, never `"deny"`, exits early for any role session, and covers only five `gh issue/pr` verbs, never `git commit`.

canonical: on-the-record/hooks/live-fire-test-guard.sh:117-142 (read file:line)
`live-fire-test-guard.sh` parses a heredoc-shaped `-m` commit message for an unrelated test-coverage check; it does not deny on heredoc shape.

canonical: on-the-record/hooks/test-authoring-invariant-guard.sh:65-93 (read file:line)
`test-authoring-invariant-guard.sh` does the same heredoc-`-m` extraction for its own unrelated invariant check.

canonical: on-the-record/hooks/pr-preflight.sh:52-79 (read file:line)
`pr-preflight.sh` parses a heredoc-shaped `--body` for the issue-reference-rule check, not for shape.

canonical: `grep -rn heredoc on-the-record/hooks/*.sh` and `grep -rln "un-analyzable\|unanalyzable\|write-capable" gates/ on-the-record/`, executed live
No hook or gate denies a heredoc-shaped write command naming `-m -m`/`--body-file` as the alternative, and no test asserts such a message.

The actual refusal role sessions hit (per the issue's dogfooding note) is the host's own default write-capable-command permission classifier, which denies any Bash command whose shape it cannot analyze before any repo hook can add an actionable message.

unverifiable: the host classifier's own source is not present in this checkout to cite directly — this is inferred from gh-write-allow-gate.sh's own header comment describing "a fresh install's host permission classifier denies by default"

## Conclusion

This is a net-new hook to build, not an existing gate to reword. The closest sibling in shape/precedent is `gh-write-allow-gate.sh` (same role/session-identity primitive, same `PreToolUse`+`Bash` event, same zero-install python-in-heredoc pattern) — but inverted: instead of adding an `"allow"` signal for a benign shape, the new hook adds a `"deny"` signal with an actionable message for the un-analyzable heredoc shape, scoped to role sessions (the population the issue's dogfooding note is about).

design-research-skip: mechanical (per the issue's own `design-research-skip: mechanical` flag) — the fix is a shape-detection gate mirroring `gh-write-allow-gate.sh`'s existing identity/shape primitives; no product-facing design decision is open.
