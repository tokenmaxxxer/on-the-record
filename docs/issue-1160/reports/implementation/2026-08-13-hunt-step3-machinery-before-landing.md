---
proposal: docs/issue-1160/proposals/step3-machinery.md
---

# Hunt record — step3-machinery

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `need_detector.needs_due`'s glob evaluation escapes `target_root` via `..` segments in spec-supplied `present_patterns`/`absent_patterns`, letting a vendored spec read/match files outside the target project's own tree.
Kind: design-error
Seed: gates/need_detector.py (new), gates/test_need_detector.py (new), spawn.py `needs-due` subcommand
cap_seconds: 180
tier: default
diff_stat_lines: >200 (multi-file)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:05:00Z

### Reproduce
```
python3 -c "
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, 'gates')
import need_detector as nd

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    target = td / 'target'
    (target / 'roles' / 'specs').mkdir(parents=True)
    outside = td / 'outside'
    outside.mkdir()
    (outside / 'secret.txt').write_text('secret')
    spec = {
        'role': 'brand-design',
        'use_when': {'need_detector': {
            'present_patterns': ['../outside/*.txt'],
            'absent_patterns': []
        }}
    }
    (target / 'roles' / 'specs' / 'brand-design.spec.json').write_text(json.dumps(spec))
    due = nd.needs_due(target)
    print(due)
"
```

### Observed
```
[{'role': 'brand-design', 'reason': "present pattern matched '../outside/*.txt', no absent pattern matched"}]
```
`needs_due` fires based on a file (`outside/secret.txt`) that lives entirely outside `target_root`, because `_any_glob_matches` calls `target_root.glob(pat)` directly and `pathlib.Path.glob` honors `..` path components without any containment check on the resulting matches.

### Expected
The docstring states this module evaluates "a target repo's file tree" and is meant to support "arbitrary target project" trust boundaries (per proposal). A pattern containing `..` should either be rejected/sanitized before globbing, or matches should be filtered to require they resolve under `target_root`, so a target project's own vendored spec (or a spec shipped by this repo but applied to an untrusted target_root) cannot cause the detector to read/match paths outside the target tree it is supposed to be scoped to.
