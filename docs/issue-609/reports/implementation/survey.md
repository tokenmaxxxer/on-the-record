# Current-state survey — issue #609: implementation (phase 1)

Grounded in `docs/issue-609/proposals/product-discovery.md` and
`docs/issue-609/proposals/architecture.md` (both merged, PR #614/#618); does not re-derive either.
This survey adds only what implementation needs that architecture did not need to inspect: the
exact code sites the build touches.

## Files the build will touch (confirmed by reading, not the architecture proposal's prose)

- `on-the-record/hooks/delegated-judgment-gate.sh` — the deployed, zero-install `gh pr create`
  hook (issue #573, extended #581/#597). Its `gh pr create` branch (from `if not re.search(r"\bgh\s+pr\s+create\b", cmd)` through the end of the heredoc) already: resolves `issue`/`branch`/`pr_ref`
  from the current git branch and diff, computes `paths` via `git diff --name-only
  origin/main...HEAD`, and — after the existing depth/impact AND-gate and panel synthesis — writes
  `docs/issue-<n>/decisions/auto-<seq>.md`. Triage must run as new inline Python in this same
  heredoc, reusing `paths`, `issue`, `pr_ref`, `ROLES`/`role_scope`/`glob_matches`, the already-ported
  `reversibility_grade`/`LOW_IMPACT` computation, and `parse_axis_evaluations`/
  `latest_axis_evaluation` (all defined above the point triage inserts). Confirmed: `_gh()`,
  `escalate()`, `rfc3339()`, and `decisions_dir` are already in scope by the time the existing
  panel-synthesis block runs, so triage can reuse them without redefinition.
- `gates/role_spec_shape.py` — `check_axis_evaluation_entry` (line 135) is reused verbatim, no
  edit. A new function alongside it, named `check_open_decision_item`, taking an entry dict and the
  set of owning-role names, validates the thin upstream shape (item / source_role / source_path /
  candidate_axes) the same way `check_axis_evaluation_entry` validates its own entry — confirmed
  this file's existing pattern (module-level `check_*` functions taking a dict and returning a
  reason list, no class, no I/O) is what every other shape check here already follows.
- `roles/specs/*.spec.json` — `open_decision_item` needs a `required_fields` entry only on roles
  that can plausibly record one: confirmed by reading `roles/*.json` that `write_scope` for most
  roles targets exactly one record file (`docs/issue-<n>/reports/<role>.md`), the same file the
  existing "Open questions resolved" prose section already lives in (survey confirms this section is
  present in every role record that has faced an ambiguity, e.g. this very survey chain). The write
  set below scopes the schema addition to the role the issue's live-evidence case names directly:
  `requirements-engineering`. Extending every role's spec is a larger, unbounded write set the
  architecture proposal never froze — deferred, see Out of scope.
- A new test module under `gates/`, sibling to the existing `test_role_spec_shape_batch*.py` files,
  covering `check_open_decision_item` only (mirrors the batch-file-per-concern convention already in
  place: batch files never edit an earlier batch's tests, confirmed by every existing batch test
  file's own docstring).
- A new standalone test harness for the hook's triage logic. `on-the-record/hooks/` has no existing
  test harness for `delegated-judgment-gate.sh` itself (confirmed by directory listing: no test file
  targeting this hook exists anywhere in the repo) — the existing gate is validated only by its own
  heredoc running correctly inline, no extracted-and-unit-tested Python module. Given the
  zero-install constraint (the heredoc must stay a single inline script, not an importable module),
  the triage addition is tested the same way: a standalone Python harness that extracts the heredoc's
  Python source (regex between the `<<'PY'` markers, same technique needed to reach the code under
  test at all) and execs it against constructed fixture repos (temp dirs with a git worktree,
  `roles/*.json`, and role record files), asserting on the written triage audit record's fields and
  on the escalate/resolve outcome — the only test strategy available without breaking the
  zero-install posture, confirmed by inspecting how `_run`/`_gh` are structured (subprocess calls
  against `cwd=TARGET`, so a fixture-repo temp dir with `ORCHESTRATE_OFF` unset and `gh` unavailable
  runs the gate logic and skips network calls to real gh, since `_gh()` swallows subprocess errors by
  design).

## What already exists and is reused verbatim (per architecture proposal sections 2-4, confirmed)

- `docs/decisions/2026-08-10-judgment-axis-matrix.md`'s 5-axis to 1-role table — read at runtime via
  `ROLES[role]["judgment_axes"]` (already loaded by `load_roles()` in the existing hook), not
  re-parsed from the markdown file. Confirmed: the hook never reads the ADR file directly; axis
  ownership is already materialized into `roles/*.json`.
- The two-axis AND gate (`DEPTH and LOW_IMPACT`, current hook) — triage's threshold-exceeded
  condition is `not (DEPTH and LOW_IMPACT)`, the exact boolean already computed for the
  candidate-decision path, confirmed reusable unchanged since triage fires in the same
  `gh pr create` invocation, over the same `paths`/`issue`.
- `axis_evaluation` parsing (`parse_axis_evaluations`, `latest_axis_evaluation`) — triage looks up
  each eligible role's evaluation of the open-decision item the same way the existing panel path
  looks up a candidate-decision evaluation; confirmed the citation target differs (item's
  `source_path` instead of a `docs/product/*.md` entry) but the parser itself needs no change,
  since it only extracts axis_evaluation HTML-comment blocks by key:value line, not by citation
  content.

## Degradation, confirmed still live

The judgment-capture corpus directory this repo's depth axis reads from is still empty (confirmed
by directory listing: it holds no entries). `DEPTH` therefore evaluates `False` for every path list,
so the reused AND gate never clears — every open-decision item's threshold-exceeded condition is
`True` unconditionally today, matching product-discovery's and architecture's restated degradation
clause verbatim. No special-case branch needed in the triage code for this; it falls out of reusing
`DEPTH` unmodified.

## Write surface boundary (what implementation does NOT need to touch)

- No new hook file, no new `gates/` package import into the zero-install heredoc (confirmed
  constraint, architecture proposal section 7).
- No change to `check_axis_evaluation_entry`, `parse_axis_evaluations`, `reversibility_grade`,
  `load_roles`, or `glob_matches` — all reused unmodified, confirmed by re-reading each function's
  current signature against what triage needs as input.
