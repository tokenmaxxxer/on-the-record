---
proposal: docs/issue-587/proposals/execution-observation.md
---

# Hunt record — issue-587-execution-observation

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — phase 2's "What will be done" step 1 requires creating a fixture target repo (a fresh temp-dir git repo with a minimal roles/*.json pair and an approvers.md), and steps 2-5 require driving the gate hook and the remediation spawn generator against that fixture (opening a candidate PR, running the gate, simulating a remediation PR/merge, re-judging), but the proposal's frontmatter write-set field names only two report paths under the reports subtree. No fixture-repo path, temp working directory, or driver-script path is declared anywhere in the write set.
Kind: design-error
Seed: docs/issue-587/proposals/execution-observation.md (frontmatter files-list vs. "What will be done" steps 1-5)
cap_seconds: 120
tier: default
diff_stat_lines: 145 insertions, 2 new files under docs/
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:02:00Z

### Reproduce
Read the proposal's frontmatter block (first ~4 lines) and compare against its "What will be done" section (steps 1-5):

```
sed -n '1,5p' <the proposal file>
grep -n "temp-dir\|fixture target repo\|delegated-judgment-gate\|remediation_spawn" <the proposal file>
```

### Observed
The write-set field lists exactly two report paths (a per-scenario report file and a top-level summary report file). The body's step 1 says the fixture is built as "a fresh temp-dir git repo with a minimal roles/*.json pair ... and an approvers.md," and steps 2-5 describe opening PRs, running the gate script, merging a simulated remediation commit, and re-running the gate inside that fixture. None of this filesystem footprint — the fixture repo location, any scratch/temp working area, or a driver script to orchestrate the fixture's git operations — appears in the declared write set.

### Expected
The declared write set should name (or explicitly delegate to a stated out-of-repo scratch convention, e.g. a $TMPDIR-based location) the fixture repo's location and any driver script used to construct and drive it, so phase 2's actual filesystem footprint matches what was approved in phase 1.
