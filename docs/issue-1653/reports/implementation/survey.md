# Survey — issue-1653

Skip condition: spec leaves no design decision open. The issue body
prescribes the exact shape to build ("mirror `requirement_intake_consult.py`
exactly") and the exact tag vocabulary (`design-research: <ref>` /
`design-research-skip: mechanical`). There is no open design choice to
scout — the task is a direct structural mirror of an existing gate.

## Write set surveyed
canonical: gates/requirement_intake_consult.py (read in full this turn)
- `gates/requirement_intake_consult.py` (issue-1024) is the module to
  mirror: a closed-over regex pair, a pure `check_issue_body(issue, body)
  -> list[str]`, a gh-wrapped `check(repo, issue)` calling
  `gh_rest.fetch_issue_body`, and a `main()` CLI entrypoint.

canonical: gates/test_requirement_intake_consult.py (read in full this turn)
- Its test file is the test shape to mirror: trace-passes,
  skip-passes, neither-fails, arbitrary-skip-reason-fails cases, no
  network, run via `if __name__ == "__main__"`.

- `gates/gh_rest.py` — existing helper providing `fetch_issue_body(repo,
  issue)`; reused as-is, no changes needed.
- New files to write in this session: gates/design_research_consult.py,
  gates/test_design_research_consult.py (module + test pair, not yet
  committed). No wiring into `spawn.py` or hooks in this issue —
  explicitly deferred by the issue body to avoid colliding with #1652's
  spawn.py change.

## Prior decisions
canonical: gates/requirement_intake_consult.py comment block (read this turn)
- #1024's module comment records that the closed vocabulary is
  intentionally limited to `trivial` (not an arbitrary reason) to close
  an escape hatch found in a prior hunt. This issue reuses that same
  discipline with `mechanical` as the sole accepted skip reason.
