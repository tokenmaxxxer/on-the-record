# Scout brief — issue-759

## Mode

Batched-sequential fallback, not parallel fan-out: this is a repo-internal
process-tooling decision (a git-commit-time registration guard inside this
plugin's own custom hook framework), so the strongest comparable field is
this repository's own sibling hooks, not an external product category —
read directly rather than spun out to parallel search agents. One external
web angle was run alongside to check for a stronger established pattern
name. 1 stage.

## Category must-bes (internal field: this repo's own `PreToolUse`+`Bash`
`git commit`-time guards)

- Fail open on any environment gap (no `python3`/`git`, not a `git commit`
  command, nothing relevant staged) — never block an unrelated commit.
  Fail closed only on a positively-determined violation.
- Read STAGED content via `git diff --cached --name-only` +
  `git show :<path>`, not the working tree — reflects exactly what would
  land, matches pre-existing-file edits mid-flight correctly.
- Port the check logic inline (or import from a candidate `gates/` dir
  found by walking up from the hook's own location) rather than shelling
  out to `pytest` — zero-install, no guaranteed test-runner or full repo
  checkout at hook-invocation time in a consumer repo.
- `ORCHESTRATE_OFF` kill switch, same case pattern every sibling uses.
- A sibling `test_<name>.py` in the same directory, not folded into an
  existing test file.

## Performance axes this field competes on

1. **Blast radius of a false positive** — `spec-index-preflight.sh` and
   `role-axis-completeness-guard.sh` both scope their trigger to "a
   specific tracked path is in the staged diff", not "every commit" —
   keeps unrelated commits untouched.
2. **Where the check logic lives** — port-inline (both siblings) vs.
   import-with-fallback-candidates (`role-axis-completeness-guard.sh`,
   because its check module can lag between `gates/` and the packaged
   `on-the-record/gates` copy). No sibling shells out to `pytest`.
3. **Fail-open vs fail-closed boundary** — both siblings draw the line at
   "positively determined violation only"; anything else (missing tool,
   wrong command, no staged match) is fail-open, never a refuse-by-default.

## Adopt

- Trigger scope: fire only when the staged diff introduces a NEW file
  under `gates/*.py`, `on-the-record/hooks/*.sh`, or
  `.github/workflows/*.yml` (git status "A" for that path) — not on every
  commit. This is the same "narrow, positively-determined trigger"
  principle as both siblings, and it is also the direct answer to the
  #744 tension (see the proposal's Rationale): a check that only ever
  fires at the exact moment a new mechanism file appears cannot be the
  kind of ambient noise #744 is scoped to remove.
- Read staged content via `git diff --cached --name-only` / `git show
  :<path>`, matching both siblings exactly.
- Fail open on every environment/non-match condition; fail closed only
  when a newly-staged mechanism file has no matching row in the target
  spec (checking the STAGED version of the spec file if it too is
  staged, else the on-disk version — same fallback `spec-index-
  preflight.sh` already uses for its own tracked index file).

## Skip

- Shelling out to `pytest gates/test_boundary.py gates/test_generated_paths.py`
  from the hook (the issue's own "사후 테스트를 실제로 돌게 만들기" framing
  as literally invoking pytest) — no sibling hook in this repo does this;
  all port the check logic inline or import it. Introducing a
  shell-to-pytest precedent here would be the one guard in 26 that
  doesn't match the family's zero-install shape.
- A full-repo completeness re-scan on every commit — narrower staged-new-
  file trigger is both cheaper and quieter, matching axis 1 above.

## Gap line

The current state (pre-#759) has zero git-commit-time enforcement for
`enforcement-boundary.md`/`generated-paths.md` completeness — only the
post-hoc pytest tests, which nothing runs at landing time. The category's
must-bes (fail-open safety, staged-content read, narrow trigger, inline
port) are all absent for this specific pair of specs even though they are
already implemented twice for other specs (`reconciled-index.md`,
`roles/*.json`). This is a gap in coverage of an established pattern, not
a missing pattern.

## Segment fit

One line: this is closer to `spec-index-preflight.sh` than to
`role-axis-completeness-guard.sh` — both target specs are simple
mechanism-name -> verdict-row tables (like the index's path -> hash rows),
not a cross-file ownership computation (like axis ownership across all
`roles/*.json`), so port-inline over import is the better-fitting sibling
to follow structurally.

## Web angle (external, 1 query, no strong finding)

Generic pre-commit-hook guides confirm the "block on commit rather than
CI" pattern is common practice for CI-less repos, but returned nothing
specific to "new module must be listed in a registry" enforcement beyond
generic doc-freshness pre-commit hooks — no named pattern more specific
than what the internal sibling hooks already establish. Internal prior
art remains the primary and sufficient reference.

Sources:
- [Effortless Code Quality: The Ultimate Pre-Commit Hooks Guide](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)
- [Git Hooks - A Guide for Programmers](https://githooks.com/)

## Stage count / mode used

1 stage (sweep only — internal read + 1 web query), batched-sequential
(not parallel fan-out: single internal-read angle plus one confirmatory
web query, not multiple independent search angles needing concurrent
dispatch). Judge point 1: internal prior art alone answered every
must-be/axis question; the web query added no new decision-relevant
signal, so deepening stopped after stage 1 (saturation).
