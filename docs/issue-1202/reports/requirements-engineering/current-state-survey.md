# Issue #1202 — current-state survey (requirements-engineering)

## Scout skip record

Skip condition: no external product surface — this is an internal
orchestration-protocol design (advisory queue schema, gate, CLI verbs).
Precedent used instead of an external sweep: this repo's own
need-detector / consult / panel machinery, cited below.

## Precedent read (canonical citations)

canonical: gates/need_detector.py:1-70

```
Advisory-only (issue #1160 requirement 2): this module never spawns a role
session — `needs_due()` is a pure classifier, `format_report()` only
formats text for an orchestrator's existing board-reading step to print
alongside `roles-due`'s own advisory output.
```

canonical: spawn.py:5254-5276

```
    if a.role == "roles-due":
        ...
        due = _roles_due.roles_due(Path(a.cwd).resolve())
        lines = _roles_due.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "needs-due":
        ...
        due = _need_detector.needs_due(
            Path(a.cwd).resolve(), root=Path(__file__).parent.resolve())
        lines = _need_detector.format_report(due)
        for line in lines:
            print(line)
        return 0
```

Reading: `needs-due` is the direct CLI template for requirement 4 — a
new advisory line source (`findings-due`) can slot into the same
board-reading step, printing lines only, never spawning.

canonical: spawn.py:4542-4631

```
def consult_cmd(role: str, question: str, issue: int | None = None,
                cwd: str | None = None) -> dict:
```

Reading: `consult_cmd()` loads a role's rulebook via
`role_settings()`/`plugin_dirs()`, runs one bounded headless session,
parses a trailing JSON verdict, and appends one trace line via
`_append_consult_trace()` regardless of outcome (`finally` block).
Requirement 5 (ideate/draft/review) is a sibling-verb extension of this
function family.

canonical: spawn.py:4681-4702, spawn.py:4646-4661

```
def _run_panel_session(role: str, peer_role: str, question: str, cwd: str | None) -> dict:
```
```
def _panel_record_path(issue: int | None, slug: str) -> Path:
    if issue is not None:
        return ROOT / "docs" / f"issue-{issue}" / "reports" / "panel" / f"{slug}.md"
    return ROOT / "docs" / "reports" / "panel" / f"{slug}.md"
```

Reading: panel already shows a second consult-family verb with a
different return shape (multi-turn transcript, `_append_panel_turn()`),
reusing `consult_cmd()`'s session-assembly helpers. The template for
ideate/draft/review: shared assembly + trace-append, diverging only in
prompt template and record path.

canonical: derived below

```
$ ls docs/findings 2>&1
ls: cannot access 'docs/findings': No such file or directory
```

Reading: every advisory/consult path read above lives inside the six
standing buckets (`docs/reports/consult-log.md`,
`docs/issue-<n>/reports/panel/<slug>.md`). `docs/findings/<role>/`, as
the issue text names it, does not exist yet and sits outside that
bucket set — the proposal's Ambiguities section resolves this path
choice.

canonical: derived below

```
$ grep -rn "N=3\|rate.bound\|per.session.*cap" spawn.py gates/
```
(empty output)

Reading: no prior per-session numeric rate cap exists in this codebase;
requirement 3's counting mechanism is new, not reused.

canonical: docs/specs/approvers.md

```
- JiwonJung94
- jjongkwann
```

Reading: these are the only accounts whose PR Approve /
`APPROVE issue-<n>/<role>` comment opens phase 2, per this session's own
role-handoff contract v3 directive. Requirement 4's finding-into-issue
confirmation is a separate, lighter-weight human act — the proposal
keeps the two apart rather than routing findings through this same
approvers.md gate.

## Open questions this proposal must settle

1. Queue location: `docs/findings/<role>/` (issue's literal wording) vs.
   a bucket-compliant path such as `docs/reports/findings/<role>/`.
2. Whether "rate bound N=3/session" counts findings written this
   session only, or cumulative against an existing queue.
3. Whether ideate/draft/review get one shared `spawn.py consult <verb>
   <role> "..."` dispatcher or three new subcommands.
