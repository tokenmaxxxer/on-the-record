---
issue: 3182
role: implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf
author: implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf
skills: implementation-blueprint (skill-repository(c05de12)), conformance-review-traceability-and-evidence (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - scripts/preflight/consumer_preconditions.py
  - docs/handbooks/install-sufficiency.md
  - tests/test_issue_3182_citation_line_accuracy.py
type: repair
breaking: false
verdict: All two defects PR #3194's independent verification found are fixed. The tenth precondition (workspace_disk_headroom, citing spawn.py's _spawn_capacity_check) is added with its own remedy/source/detection; a dispatch-path sweep beyond it found three more real sys.exit gates, reported below as follow-up, not silently absorbed. All 5 imprecise/incorrect citations are corrected to the exact line the call sits on. A new test (test_issue_3182_citation_line_accuracy.py) opens every cited file at every cited line and asserts the call is actually there, so future code motion fails the suite instead of the citation quietly drifting. The handbook's "post-install hook" wording overreach is corrected to name the actual mechanism (a SessionStart first-run check) plugin.json actually supports.
loop_state: committing
upstream:
  - path: docs/issue-3182/reports/adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2.md
    sha: 3e04567719f435af2c88b0380cecb61be1cdd790
  - path: scripts/preflight/consumer_preconditions.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: docs/handbooks/install-sufficiency.md
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: spawn.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: pipeline.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: board.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: skills.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: plumbing.py
    sha: a526670a031f2181a8383c4cef9a7105843a7044
  - path: on-the-record/hooks/git-push-guard.sh
    sha: a526670a031f2181a8383c4cef9a7105843a7044
---

# issue-3182 — implementation-blueprint+conformance-review-traceability-and-evidence+test-derivation-e2a08abf record

## What was done

canonical: `gh pr view 3184` (before this round's commit) — `headRefName`
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
tip `a526670a`, `Closes #3182`. This is round 3 on that PR: PR #3194
(independent verification of PR #3184) found two real defects, in
`docs/issue-3182/reports/adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2.md`
(sha `3e04567719f435af2c88b0380cecb61be1cdd790`, read via `gh pr diff
3194 --name-only` then `git show pr-3194-review:<path>`), against 9/9
satisfied/unsatisfied verdicts, read-only behavior, and handbook honesty
that all stayed Present. This round fixes both defects directly on PR
#3184's own branch (not a new PR), continuing that delivery.

### 1. Completeness -- added the tenth precondition

derived: `sed -n '729,764p' spawn.py` (this round) confirms
`_spawn_capacity_check(path)` -- a `sys.exit`-enforced gate on
disk/inode headroom, called at `spawn.py:3229`
(`grep -n "_spawn_capacity_check(work)" spawn.py` -> `3229:
_spawn_capacity_check(work)`) before every workspace clone. PR #3194
found this missing from the nine preconditions. Added
`check_workspace_disk_headroom()` and a tenth `CHECKS` entry,
`workspace_disk_headroom`, in
`scripts/preflight/consumer_preconditions.py`:

- Detection mirrors spawn.py's own logic (same `MIN_FREE_BYTES_DEFAULT`/
  `MIN_FREE_INODES_DEFAULT` thresholds, same env-var overrides
  `MUSTER_MIN_FREE_BYTES`/`MUSTER_MIN_FREE_INODES`/
  `MUSTER_SKIP_SPACE_CHECK`) using `shutil.disk_usage()` and
  `os.statvfs()` -- both POSIX, present on macOS and Linux, no GNU-only
  tool shelled out to, consistent with the rest of the script's
  portability contract.
- `remedy` names the exact env vars an operator can use to free space or
  override the threshold.
- `source` cites `spawn.py:729-764` for the function, plus the specific
  `disk_usage()` call (`spawn.py:740`), the `sys.exit()` call
  (`spawn.py:745`), and the call site (`spawn.py:3229`).

derived: `python3 scripts/preflight/consumer_preconditions.py --json`
(this round, worktree outside `/tmp`)
```
result: 10 entries -- 9 satisfied ("posix_fork_support",
"claude_cli_on_path", "git_cli_on_path", "gh_cli_authenticated",
"git_identity_configured", "skill_repository_resolvable",
"home_claude_skills_dir_present", "target_repo_board_file_present",
"workspace_disk_headroom"), 1 unsatisfied ("remote_push_access",
mandated)
```

derived: `grep -n "sys.exit(" spawn.py pipeline.py board.py skills.py
plumbing.py` (this round, full sweep across the five files the existing
preconditions already cite), each match read in context with `sed -n`
and cross-checked one by one against the (now ten) `CHECKS` names, per
this round's brief ("say what you found, including nothing further if
that is the answer"). Not nothing further -- three more real gates were
found and are reported here as follow-up rather than added to `CHECKS`
this round, because this round's authorized scope was specifically the
one named gap; the majority of the remaining `sys.exit` sites are
argparse-style usage errors (`사용법: spawn.py ...`) or per-issue
business-state gates (`require_acceptance_gate`,
`require_requirement_linkage`, `require_no_repo_config`,
`require_repo_root` -- these depend on which issue/task is being worked,
not on whether the plugin-only install itself is missing something
structural, so they are judged out of the "install sufficiency" frame
and not counted as gaps):

- **`core_root()`/`core_plugin_dirs()`** (`pipeline.py:408-447,
  500-513`, confirmed via `sed -n '408,452p;500,513p' pipeline.py`) --
  `core_root()` requires a `tokenmaxxxer-core` checkout (auto-clones
  over the network if absent, `sys.exit`s if that fails);
  `core_plugin_dirs()` `sys.exit`s if any plugin `marketplace.json`
  declares is missing its directory. Called on the real dispatch path
  (`spawn.py:4118`, joined via `_core_future.result()` inside
  `_spawn_one()` -- `sed -n '4100,4125p' spawn.py`). Structurally the
  closest analog to `skill_repository_resolvable` (external repo,
  self-clones-or-fails) -- arguably the most central gap left, since it
  is a *second* required repository/plugin the on-the-record plugin
  alone does not supply.
- **`require_doctor()`** (`pipeline.py:521-548`, confirmed via `sed -n
  '521,549p' pipeline.py`) -- `sys.exit`s unless a CLI-version-specific
  "doctor" probe (hook-firing-in-headless measurement) has already run
  and matched the installed `claude` version, stored at
  `ROOT/runs/doctor-ok`. Called at `spawn.py:2859` (drive) and
  `spawn.py:2953` (main skills dispatch) -- both real dispatch paths
  (`grep -n "require_doctor()" spawn.py` -> `2859:` and `2953:`).
- **`ensure_target_remote()`** (`pipeline.py:786-820`, confirmed via
  `sed -n '786,822p' pipeline.py`) -- requires the target repo to have
  an `origin` git remote configured; `sys.exit`s under `--unattended` if
  absent (interactive sessions get a one-time setup prompt instead).
  Distinct from `target_repo_board_file_present` (which checks a file
  inside the repo, not remote configuration).

### 2. Citation accuracy -- all 5 imprecise/incorrect citations fixed

Per PR #3194's table, corrected in
`scripts/preflight/consumer_preconditions.py`:

| precondition | old source | new source | derived (this round) |
|---|---|---|---|
| `posix_fork_support` | `spawn.py:2668,4639`, both framed as "drive spawned role sessions" | `spawn.py:4639` as the real role-session path; `spawn.py:2668` reframed as "the same pattern also appears... for an unrelated feature" | `sed -n '4639p;2668p' spawn.py` -- both literally `child_pid = os.fork()`; only the *description* was wrong before, not the line, so both lines are kept but the claim about 2668 is corrected |
| `claude_cli_on_path` | `pipeline.py:663`, "execs it directly" | `pipeline.py:661` (the `cmd = [...]` assignment start) + `spawn.py:4761` (`_spawn_one()`'s actual `subprocess.Popen(cmd, ...)`) | `sed -n '661p' pipeline.py` -> `cmd = ["claude"...`; `sed -n '4761p' spawn.py` -> `proc = subprocess.Popen(` |
| `gh_cli_authenticated` | `plumbing.py:349` (a cache check) | `plumbing.py:355` | `sed -n '355p' plumbing.py` -> `t = subprocess.run(["gh", "auth", "token"], capture_output=True,` |
| `git_identity_configured` | `board.py:76-79` (`git add`) | `board.py:83-86` | `sed -n '83p' board.py` -> `subprocess.run(["git", "-C", str(root), "commit",` |
| `remote_push_access` | `on-the-record/hooks/git-push-guard.sh:341` only (remedy text) | `...:328` (`_ROLE_BRANCH_RE.match(d)`, primary enforcing logic) as citation, `:341` kept as the remedy-text origin | `sed -n '328p' on-the-record/hooks/git-push-guard.sh` -> `if dsts is not None and dsts and all(_ROLE_BRANCH_RE.match(d) for d in dsts):` |

`git_cli_on_path` (`pipeline.py:798`), `skill_repository_resolvable`
(`skills.py:96-112`), `home_claude_skills_dir_present` (`skills.py:338`),
and `target_repo_board_file_present` (`board.py:246-256`) were already
Present per PR #3194 and are unchanged.

**Regression test.** derived: `python3 -m pytest
tests/test_issue_3182_citation_line_accuracy.py -q` (this round,
worktree outside `/tmp`) -- result: 3 passed. Added
`tests/test_issue_3182_citation_line_accuracy.py`. Each `CHECKS` entry
now also carries a structured `line_anchors` field --
`[(file, line, expected_substring), ...]` -- separate from the
human-prose `source` string. The test imports `CHECKS` directly (not the
`--json` output, so it exercises the exact data the script's own
`source` field is built from), opens every anchor's file at every
anchor's line, and asserts the expected substring is present; it also
cross-checks that every anchor's filename is mentioned in that entry's
`source` prose, so the two representations of the same citation cannot
be edited independently without the test noticing. This makes the
citation-drift failure mode PR #3194 found (a citation right in spirit,
wrong by a handful of lines -- see the table above) fail the suite on
any future edit that moves the cited code, rather than requiring another
manual line-by-line audit to catch it again.

### 3. Handbook wording overreach

`docs/handbooks/install-sufficiency.md`'s `~/.claude/skills` proposal
said "a bundled post-install hook could populate this directory."
derived: `cat on-the-record/.claude-plugin/plugin.json` (this round) --
no install-time lifecycle field exists in the manifest; the CLI's hook
events are all session events (`SessionStart`, `PreToolUse`, ...), not a
marketplace install event. Reworded to name the actual mechanism -- the
same `SessionStart` first-run check the doc's other two proposals (git
identity, `approvers.md` discovery) already use -- and made explicit
that no true post-install hook exists to name instead.

### 4. Handbook kept in sync

Added a row for the new `workspace_disk_headroom` precondition to the
"Machine-level tools" table and a matching bullet under "Preconditions
that cannot be removed" (structural: a plugin cannot create disk space,
only refuse to clone before running out of it). Updated the
`remote_push_access` row's citation to the corrected `:328`. Updated the
"Reading this honestly" summary counts from nine/five to ten/six
(one satisfied outside `CHECKS`, four removable, six structural).

acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` (this round, worktree outside `/tmp`)
```
result: 3 passed
```
This independently re-derives the doc/script cross-reference (word-level,
not just my own hand count above) via
`test_every_precondition_name_is_traceable_into_the_doc`.

## Why

derived: the sweep in section 1 above (`grep -n "sys.exit(" spawn.py
pipeline.py board.py skills.py plumbing.py`, each hit read with `sed -n`
and classified) is this section's own basis for the scope call made
below -- restated here rather than re-derived, per record-order
guidance.

Fixed exactly what PR #3194 named, in the shape it asked for: one
precondition added with its own remedy/source/detection (not folded into
an existing entry, since it is a structurally distinct gate); all five
citations corrected to the exact line, not just "close enough"; a
regression test that makes the citation-accuracy property mechanically
checked going forward, since PR #3194's own framing was that the
citations are what make the enumeration auditable at all -- a
one-time fix without a test would let the same drift recur silently.

Chose to report the three additional dispatch-path gates found in the
sweep (`core_root`/`core_plugin_dirs`, `require_doctor`,
`ensure_target_remote`) rather than silently add them to `CHECKS`,
because this round's explicit brief authorized adding exactly the one
named gap and asked the sweep to "say what you found" -- treating that
as a reporting obligation, not a blank check to re-open the
completeness question and ship three more untested detection functions
in the same round a citation-accuracy regression test was also being
added. Absorbing them silently (finding them and not mentioning them)
would have repeated the exact failure mode this round exists to fix;
reporting them without shipping them respects the round's stated scope
while keeping the finding visible for a follow-up round.

## What did not work

None.

## Upstream basis

`docs/issue-3182/reports/adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2.md`
(PR #3194, sha `3e04567719f435af2c88b0380cecb61be1cdd790`) named both
defects fixed in this round, with file:line evidence for each, read via
`gh pr diff 3194 --name-only` then `git show pr-3194-review:<path>`.

`gh issue view 3182` (tokenmaxxxer/on-the-record#3182), quoted in this
round's task brief, for the "must not silently omit a real gate" and
"every precondition asserted must cite the file and line" contract text
this round's fixes are checked against.

Base for this round's edits: PR #3184's branch
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
tip `a526670a031f2181a8383c4cef9a7105843a7044` (unchanged since PR #3194
verified it). derived: `git diff --stat 6ae02cce..a526670a -- spawn.py
pipeline.py skills.py board.py plumbing.py
on-the-record/hooks/git-push-guard.sh` (this round) -- empty output, the
cited repo files match the sha PR #3194's own record claims it checked
against.

## Open findings

1. `core_root()`/`core_plugin_dirs()` (`pipeline.py:408-447, 500-513`,
   dispatch path via `spawn.py:4118`) is a real, currently-uncovered
   sys.exit gate requiring a second checkout (`tokenmaxxxer-core`) the
   on-the-record plugin does not supply (section 1 above). Resolution
   path: an eleventh `CHECKS` entry (e.g. `core_checkout_resolvable`),
   detection mirroring `check_skill_repository_resolvable`'s
   existence-check pattern against `_core_candidates()`'s resolution
   order, without triggering the real network clone.
2. `require_doctor()` (`pipeline.py:521-548`, dispatch path via
   `spawn.py:2859,2953`) is a real sys.exit gate requiring a
   CLI-version-specific probe to have already run
   (`ROOT/runs/doctor-ok`, section 1 above). Resolution path: a twelfth
   `CHECKS` entry checking that marker file against the installed
   `claude --version`, reported unsatisfied (not run) rather than
   triggering the real probe session.
3. `ensure_target_remote()` (`pipeline.py:786-820`, section 1 above) is
   a real `--unattended`-gated sys.exit requiring the target repo to
   have an `origin` remote, distinct from the existing
   `target_repo_board_file_present` file check. Resolution path: a
   thirteenth `CHECKS` entry, a read-only `git -C <cwd> remote get-url
   origin` check.

None of these three block this round's own acceptance checks or the new
citation-accuracy regression test; they are reported per this round's
explicit sweep instruction, not silently dropped.

## Next steps

derived: `git diff --stat` (this round, worktree) --
`docs/handbooks/install-sufficiency.md` and
`scripts/preflight/consumer_preconditions.py` changed (141
insertions/18 deletions), `tests/test_issue_3182_citation_line_accuracy.py`
added -- the concrete edit set this round's commit carries.

None from this round's own scope beyond the three "Open findings" above,
which are handoff candidates for a follow-up round, not blocking this
one. `loop_state: committing` reflects that this record and the code
changes it describes are committed and pushed to PR #3184's branch in
this same round; landing (merge) is out of this session's authority per
contract v3.

skill-verdict: implementation-blueprint — not-applicable: fixing five
existing citations, one new precondition entry in an existing `CHECKS`
list, and one new test file is a targeted repair inside an already-frozen
single-file structure, not new multi-module architecture requiring a
structure decision.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every citation correction and the new `workspace_disk_headroom`
entry above is pinned to file:line evidence re-derived in this round
(the tables in sections 1-2), and the new regression test operationalizes
the same file:line pinning as a machine check rather than prose alone.
skill-verdict: test-derivation — applied: invoked; the new
`test_issue_3182_citation_line_accuracy.py` is a decision-table
derivation (one row per `(file, line, expected_substring)` anchor)
driven directly from the defect PR #3194's verification found — a
citation that is superficially plausible but numerically wrong — rather
than a generic re-test of already-covered JSON-shape behavior.
other mounted skills: not triggered (work-in-english's guidance was
followed for all code/commit/doc text; it enforces via core hooks, not a
Skill-tool call).
