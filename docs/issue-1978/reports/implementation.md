# issue-1978 phase 2 implementation record

Delivered: (A) `--single-phase` spawn flag -> `CORE_BUILD_NOW=1` in the
session env plus the authoritative single-phase contract line appended to
the assembled task; (B) per-mounted-skill "Use ..." trigger-line inlining
into the directive (name-only fallback when a SKILL.md carries no trigger
sentence, never silently dropped), injection respecting A's phase mode.
Without the flag / without mounted skills the directive and env are
byte-identical to before (asserted).

acceptance: `python3 -m pytest tests/test_spawn_directive_assembly.py -q -o addopts=""` — result: 8 passed (serial run).

Note (finalization deviation, logged by the orchestrator): three role
sessions completed this implementation but stranded uncommitted waiting on
the test run; a fourth crashed. Root cause measured during finalization:
the new tests pass serially in <0.3s each but HANG under the repo's
default pytest-xdist `-n auto` addopts — the same xdist-vs-`_spawn_one`
interplay earlier observed with `ProgressEvents` (issue #1959 review).
The tests therefore belong in the same serial-execution family; the
xdist-hang family itself is reported separately. Finalization (commit/
push/PR of the sessions' unmodified work) was performed by the
orchestrator after four strandings — see docs/reports/deviation-log.md.
