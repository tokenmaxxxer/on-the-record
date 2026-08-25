---
proposal: docs/issue-2241/proposals/2026-08-25-stage-0-additive-skill-spawn.md
---

# Hunt record — stage-0-additive-skill-spawn

## before-landing — stance 0: assume the gate/guard just touched is bypassable — find the bypass

Verdict: FINDING — `--skill` accepts whitespace-only or comma-only garbage (e.g. `" "`, `",,,"`) and silently returns success with an empty skill list instead of hitting the fail-closed unknown-skill check that a real bogus name triggers.
Kind: silent-failure
Seed: skills.py resolve_skill_source() (new), spawn.py main() `if a.skill:` branch (new)
cap_seconds: 180
tier: size:200+
diff_stat_lines: ~263 across 4 files (2 modified, 2 new)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:03:00Z

### Reproduce
```
python3 -c "
import sys
sys.argv = ['spawn.py', '--skill', ' ', 'do the thing', '--issue', '42']
import spawn
spawn.main()
"
```
Compare with a real unknown skill name, which correctly fail-closes:
```
python3 -c "
import sys
sys.argv = ['spawn.py', '--skill', 'totally-bogus-skill-name', 'do the thing', '--issue', '42']
import spawn
spawn.main()
"
```

### Observed
The whitespace-only invocation prints (exit 0, no error):
```json
{
  "task": "do the thing",
  "issue": 42,
  "source": "skill-repo",
  "skills": [],
  "skill_sha": null
}
```
Same for `--skill ",,,"`. Root cause: `spawn.py`'s `if a.skill:` truthiness check only screens for the empty string / `None`, so any non-empty (even all-whitespace or all-comma) string enters the new branch and reaches `resolve_skill_source()`. Inside `skills.resolved_skill_dirs()` (unchanged, reused by the new function), the csv is split and stripped: `names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]`. When every comma-separated token strips to empty, `names == []`, and the function takes the early `if not names: return []` path *before* it ever reaches the `unknown = [n for n in names if n not in available]` fail-closed check (skills.py lines 116-129). `resolve_skill_source()` then happily returns `{"source": "skill-repo", "skill_dirs": [], "skills": [], "skill_sha": None}` and `spawn.py` prints it as a normal, successful resolution.

`test/test_spawn_skill_invocation.py` has no case for whitespace/comma-only `--skill` values — the gap is untested.

### Expected
A user who passes `--skill` with a garbage/malformed value (as opposed to omitting the flag) should get the same fail-closed error as `--skill totally-bogus-skill-name` does — "모르는 스킬 ... 쓸 수 있는 이름: ..." — not a silent, ostensibly-successful JSON blob claiming `"source": "skill-repo"` while resolving zero skills. The `not names: return []` short-circuit in `resolved_skill_dirs()` is correct for `--skills` (where an *omitted*/empty flag legitimately means "mount nothing, byte-identical path"), but `resolve_skill_source()` reuses that same helper for a flag (`--skill`) whose whole contract is "the user explicitly named skill(s) to resolve" — so a non-empty-but-garbage value should not be silently treated as "zero skills requested, success."
