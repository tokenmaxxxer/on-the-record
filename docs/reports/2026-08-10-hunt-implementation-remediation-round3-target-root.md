---
proposal: docs/issue-587/proposals/implementation-remediation-round3-target-root.md
---

# Hunt record — implementation-remediation-round3-target-root

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: NO FINDING
Seed: docs/issue-587/proposals/implementation-remediation-round3-target-root.md (phase-1-only, no code changes yet)
cap_seconds: 120
tier: default
diff_stat_lines: 2 new doc files (proposal + survey), 0 code lines
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:02:00Z

Checked whether roster_reconcile new root param threaded into _remediation_merge_sweep target_root, issue depends on state nothing maintains. Read spawn.py _remediation_merge_sweep line 2109, roster_reconcile line 2158, and sibling helpers already called with a root arg: _issue_comments line 1122, _merged_pr_for_branch line 1103, _repo_slug line 1062 - all already accept and correctly use a root Path parameter. _remediation_merge_sweep already threads its own root param into decisions_dir, _repo_slug, _issue_comments, _merged_pr_for_branch, and subprocess.run cwd=root consistently. The plan adds a matching root kwarg on roster_reconcile and passes Path a.cwd resolve from main, mirroring how other CLI dispatch already uses -C. No dangling assumption found - the plumbing the proposal depends on already exists and is exercised identically elsewhere in the file. No reproduction of a broken invariant found within the cap.
