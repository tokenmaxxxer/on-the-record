# issue-2164 implementation — deviation log

- 2026-08-24T06:55:24Z, inline: widened the `룰북`→skill-repo rename beyond
  the issue's literally-named lines to satisfy its own grep-based acceptance
  criterion (zero `룰북` hits in either file, judged case-by-case) — added
  `pipeline.py:222,483,602,611` and fixed the identical dangling
  `plugin_dirs()` reference at `consult.py:438` alongside the named
  `pipeline.py:215`. Stayed inside the two files the issue names; see
  `docs/issue-2164/reports/implementation.md`'s "Rationale for deviations"
  for the full judgment call. Diff: `consult.py`, `pipeline.py` (same commit
  as the named-line edits).
