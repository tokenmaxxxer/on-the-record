---
proposal: docs/issue-1761/proposals/skill-axis-phase-3-pilot.md
---

# Hunt record — skill-axis-phase-3-pilot

## after-proposal — stance 1: spawn.py resolution mechanism vs skill-repository's real skills/ subdir layout

Verdict: FINDING — resolved_skill_dirs() treats skill names as immediate children of the skill-repository checkout root, but the real skill-repository layout (and this proposal's own plan) nests skills one level deeper under `skills/`, so the proposal's "no code changes" allowlist entry will fail-closed at runtime instead of resolving.
canonical: python3 -c reproduction below, executed this turn — result: SystemExit "--skills: 모르는 스킬 upstream-defect-report-subtraction — 쓸 수 있는 이름: docs, skills"
Kind: design-error
Seed: docs/issue-1761/proposals/skill-axis-phase-3-pilot.md ("What will be done" steps 1-2, "How you'll know it worked"), docs/issue-1761/reports/implementation/survey.md ("skill-repository target layout" section, which itself records `.gitignore, README.md, docs/, install.sh, skills/` as skill-repository's top level and "treats each name as an immediate child directory of repo_root" for resolved_skill_dirs, without flagging the mismatch)
cap_seconds: n/a (not provided by dispatcher)
tier: n/a (not provided by dispatcher)
diff_stat_lines: n/a (phase-1 docs-only files probed, not a diff)
started_at: 2026-08-21T00:00:00Z
ended_at: 2026-08-21T00:15:00Z

### Reproduce
```
python3 - <<'PYEOF'
import tempfile, os, sys
from pathlib import Path
sys.path.insert(0, ".")
import spawn

tmp = tempfile.TemporaryDirectory()
repo_root = Path(tmp.name)
# mimic real skill-repository layout: skills live under skills/<name>/SKILL.md
(repo_root / "skills" / "upstream-defect-report-subtraction").mkdir(parents=True)
(repo_root / "skills" / "upstream-defect-report-subtraction" / "SKILL.md").write_text("x")
(repo_root / "README.md").write_text("x")
(repo_root / "docs").mkdir()

os.environ["MUSTER_SKILL_REPO"] = str(repo_root)
resolved = spawn._skill_repo_root()
print("resolved repo root:", resolved)

dirs = spawn.resolved_skill_dirs("upstream-defect-report-subtraction", resolved)
print("OK", dirs)
PYEOF
```

### Observed
```
resolved repo root: /tmp/tmp7_tf3kjl
SystemExit: --skills: 모르는 스킬 upstream-defect-report-subtraction — 쓸 수 있는 이름: docs, skills
```

### Expected
`resolved_skill_dirs()` should resolve `upstream-defect-report-subtraction` to `<checkout>/skills/upstream-defect-report-subtraction`, matching where the proposal plans to actually add the SKILL.md files (per the survey's own live `gh api` inventory of skill-repository's real top-level layout: `skills/` holds all 33 existing skill dirs flat, e.g. `skills/diagnose-first`). Instead `resolved_skill_dirs()` (unchanged per the proposal's Constraints) looks for the name directly under `MUSTER_SKILL_REPO`/the checkout root, so `_skill_repo_root()` would need to resolve to `<checkout>/skills` rather than `<checkout>` for this proposal's plan to work with zero spawn.py changes — this env-variable-vs-real-layout mismatch is not addressed anywhere in the proposal, and the existing test suite (test/test_spawn_role_skill_resolution.py, test/test_spawn_skills_mount.py) only ever exercises synthetic fixtures where the checkout root itself directly contains flat "alpha"/"beta" dirs, never the real `skills/` subdir nesting, so this gap is currently untested and would only surface when someone actually points MUSTER_SKILL_REPO at a real skill-repository clone root as the proposal instructs.
