canonical: gh issue view 1664 (read this session)
skip-condition: spec leaves no design decision open — the issue body already fixes the shape (pure classify() over base-HEAD/merge-base/head content, sibling module in gates/'s shape, wire into merge_gate's evaluation path), the algorithm (compare content at three refs, refuse only when merge-base is stale relative to a later base commit that added now-missing lines), and the prior art (CI merge queues — cited in the issue itself). No exemplar sweep applies: this is an internal deterministic-gate module, not a product surface.

# Current state

canonical: gates/merge_gate.py:1-152 (read in full this session)
- `evaluate(root, repo, pr, subject)` returns `{"allowed": bool, "reasons": [str]}`. Checks (1) check-runner comment all-pass via `latest_check_runner_comment`+`parse_check_runner_result`, (2) required verification records via `required_verification_missing`. Only one `gh` call site (`latest_check_runner_comment`); everything else is pure/local. `main()` is a thin CLI: `python3 gates/merge_gate.py <pr> <subject> [--repo <path>]`.

canonical: tests/test_merge_gate.py:1-80 (read this session)
- fixture repo built with `git init`+`git commit` in `tmp_path`; `gh` calls monkeypatched via `subprocess.run` argv capture, per `tests/test_check_runner.py` convention. No network.

canonical: on-the-record/hooks/absorbed-branch-recut-guard.sh:1-104 (read in full this session)
- a PreToolUse hook, not a gate module — its own header comments describe branch-absorption detection (recut when a session's own branch was merged out from under it), not a diff/content-compare helper. Its header comments state the fail-open, local-git-state-only, no-network posture this new module should also follow. No function in this file is importable for content-diffing; only its documented posture (fail-open on missing tooling, local git state only) is carried forward.

canonical: `ls gates/` output this session
- no existing stale-revert-shaped module and no existing three-way content-diff helper anywhere under gates/.

canonical: `find . -iname "*merge_gate*test*"` output this session
- only tests/test_merge_gate.py exists; no existing stale-revert test file.

`git show <ref>:<path>` reads file content at a ref without checkout; `git merge-base <a> <b>` gets the merge-base commit — both are pure local git plumbing, no network, matching the issue's "Pure function over three file-content snapshots, no network" requirement once the caller obtains the three snapshots (classify() itself takes content, not refs, per acceptance criterion 1).

# Write set (frozen, planned — none of these paths exist yet)

- gates/stale_revert_guard.py (new) — classify(base_head_content, merge_base_content, head_content) returning a verdict/reasons structure per path, plus a thin git-wrapper layer (collect_snapshots(repo, base_ref, pr_head_ref)) that shells out to `git merge-base`/`git show`/`git diff --name-only` to build the three snapshots for each changed path.
- gates/merge_gate.py (existing, extend) — wire a stale-revert check into `evaluate()`, add reasons on REFUSE naming the reverted path(s).
- tests/test_stale_revert_guard.py (new) — unit tests per acceptance criterion 1 (REFUSE/ALLOW/intentional-removal cases + empty-state "merge-base == base HEAD" case), fixture-repo style matching tests/test_merge_gate.py.
- tests/test_merge_gate.py (existing, extend) — live reconstruction of the PR #1662-vs-#1661 shape (acceptance criterion 2): a fixture repo where a later base commit adds lines to a file, a stale branch (merge-base predates that commit) deletes them → REFUSE; same branch rebased onto base HEAD → ALLOW.

No new dependency, no env var, no schema/migration — pure-Python + git subprocess, matching merge_gate.py's existing footprint.
