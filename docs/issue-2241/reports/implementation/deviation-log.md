# issue-2241 implementation deviation log

- 2026-08-25T00:00:00Z inline implementation: added an explicit
  empty-after-parse rejection for `--skill` in spawn.py's new dispatch
  branch, plus two regression tests in test/test_spawn_skill_invocation.py
  (canonical:
  docs/issue-2241/reports/implementation/2026-08-25-hunt-stage-0-additive-skill-spawn.md
  — before-landing warrant-hunt finding, not called for by the stage-0
  proposal's `## What will be done` list). Stayed inside the frozen write
  set (spawn.py/test/test_spawn_skill_invocation.py), mechanical (input
  validation, no design/architecture judgment), landed in commit
  65f5163dc00f2ec50694479e097819faf07ecc03.
