---
proposal: docs/issue-1123/proposals/consult-raw-output-persist-complex-question.md
---

# Hunt record — consult-raw-output-persist-complex-question

## after-proposal — stance 4: assume the write set cannot carry the work; find a needed path missing from `files:`

Verdict: FINDING — frozen `files:` list omits the issue-scoped consult-log path (`docs/issue-1123/reports/consult-log.md`) that `_consult_trace_path()` actually writes to when `--issue` is passed, while the list only names `docs/reports/consult-log.md`
Kind: design-error
Seed: docs/issue-1123/proposals/consult-raw-output-persist-complex-question.md (frozen files: spawn.py, gates/test_consult_json_parse.py, docs/reports/consult-log.md); docs/issue-1123/reports/implementation/survey.md
cap_seconds: 60
tier: default
diff_stat_lines: ~250 (two new docs files)
started_at: 2026-08-13T09:40:08+09:00
ended_at: 2026-08-13T09:48:00+09:00

### Reproduce
```
cd <repo>
python3 -c "
import sys; sys.path.insert(0,'.')
import spawn
print(spawn._consult_trace_path(1123))
print(spawn._consult_trace_path(None))
"
```

### Observed
```
/…/docs/issue-1123/reports/consult-log.md
/…/docs/reports/consult-log.md
```
The proposal's own "Constraints" section acknowledges the issue-scoped
variant exists ("every consult attempt still traces exactly one line to
`docs/reports/consult-log.md` (or the issue-scoped variant)"), and phase-2
work on this very issue is expected to run `spawn.py consult ... --issue
1123`, which routes through `_consult_trace_path(1123)` →
`docs/issue-1123/reports/consult-log.md` — not the frozen
`docs/reports/consult-log.md`. The "How you'll know it worked" bullet
("a live smoke ... logs `ok:` in `docs/reports/consult-log.md`") will
either write to the wrong file relative to what actually happens (if run
with `--issue`) or silently mismatch the frozen write set (if the
implementer improvises the extra path without it being declared).

### Expected
The `files:` list should include `docs/issue-1123/reports/consult-log.md`
(or explicitly generalize the entry to cover both trace-path variants),
since the phase-2 live-smoke step described in the proposal will run
under `--issue 1123` and therefore write to the issue-scoped path, not
the one path that is actually frozen.
