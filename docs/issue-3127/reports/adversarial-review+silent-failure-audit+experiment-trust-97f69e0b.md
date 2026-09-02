---
issue: 3127
role: adversarial-review+silent-failure-audit+experiment-trust-97f69e0b
author: adversarial-review+silent-failure-audit+experiment-trust-97f69e0b
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3169's round-3 repair (commit 421bfb7a), attacking the git-command-failure/empty-result fix and its self-reported sweep
loop_state: done
code_under_review: PR #3169 branch issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675, commit 421bfb7a619a8eb70b74cd29d3768aa8c7649a51
type: verification
breaking: false
verdict: PR #3169 round 3 -- Present on its own stated claim and sweep;
  two gaps outside its declared axis found and recorded below (timeout
  handling, git-log output-shape validation); branch-staleness failure
  from PR #3219/round 3 still present and worse. Grades and evidence
  inline below each attack.
upstream:
  - path: PR-3169-branch:scripts/issue-3127/verify_preregistration.py
    sha: 421bfb7a619a8eb70b74cd29d3768aa8c7649a51  # this session's own branch does not carry this path's round-3 content; read/exercised from a scratch clone fetching origin/issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675 at this commit, per the task's instruction not to merge PR #3169 or edit its branch
  - path: PR-3169-branch:tests/test_issue_3127_verify_preregistration.py
    sha: 421bfb7a619a8eb70b74cd29d3768aa8c7649a51
  - path: PR-3169-branch:docs/issue-3127/decisions/pre-registration.md
    sha: 421bfb7a619a8eb70b74cd29d3768aa8c7649a51
  - path: docs/issue-3127/reports/silent-failure-audit+implementation-blueprint+experiment-trust-15d48cd6.md
    sha: same-commit  # round-3's own record, landed via PR #3222 (8205c160), already on this branch's history
  - path: docs/issue-3127/reports/adversarial-review+experiment-trust+silent-failure-audit-6095e2ff.md
    sha: fb5bdd13fd5695e598736ec251374f2e1e756323  # round-2 verification (PR #3219), read first per task instructions; its Present grades on merge-commit bind and --follow are not re-derived here
---

# issue-3127 — adversarial-review+silent-failure-audit+experiment-trust-97f69e0b record

## What was done

canonical: PR #3169 branch `issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675` at commit `421bfb7a619a8eb70b74cd29d3768aa8c7649a51`, fetched into a scratch clone and diffed against its own parent — read directly, not summarized from round 3's report.

Setup: a scratch clone of this repo (`git clone` into `/tmp/pr3169_check/repo`), `origin` remote repointed at `https://github.com/tokenmaxxxer/on-the-record.git` (a clone whose `origin` is a local filesystem path cannot resolve `gh`'s owner/repo inference — this produced a spurious first-pass failure on acceptance check 3 unrelated to the code under review, diagnosed and corrected before the runs below). Round 2's verification record and round 3's own record (both cited in frontmatter `upstream:`) were read first per task instructions; round 2's merge-commit bind and `--follow` fix were not re-attacked.

### Attack 1 — nonzero exit, real stderr

derived: `python3 -m pytest /tmp/pr3169_check/adversarial_probe.py::Attack1_NonzeroWithStderr -q -s` against `verify_preregistration.py` at `421bfb7a`, `subprocess.run` mocked one level below the file's own `_run_git` wrapper to inject `git log` returncode 128 / stderr `fatal: bad object HEAD` — result:
```
Attack1 (nonzero+stderr): False | could not determine commit history -- `git log --diff-filter=A --format=%H --reverse -- docs/issue-3127/decisions/pre-registration.md` failed (exit 128): fatal: bad object HEAD -- a failed git command is not evidence the path has no commits yet, so this cannot be read as a pass (fail closed)
1 passed in 0.13s
```
Present: `ok=False`, message names the literal command, the exit code, and states "fail closed".

### Attack 2 — nonzero exit, silent (no stderr)

derived: same probe, `Attack2_NonzeroSilent`, `git log` returncode 1 / stderr `""` — result:
```
Attack2 (nonzero silent): False | could not determine commit history -- `git log --diff-filter=A --format=%H --reverse -- docs/issue-3127/decisions/pre-registration.md` failed (exit 1):  -- a failed git command is not evidence the path has no commits yet, so this cannot be read as a pass (fail closed)
1 passed in 0.13s
```
Present: fail-closed path does not depend on stderr being non-empty to fire; command and exit code are still named.

### Attack 3 — command that times out

derived: `grep -n "timeout" scripts/issue-3127/verify_preregistration.py` on `421bfb7a` — result:
```
$ grep -n "timeout" scripts/issue-3127/verify_preregistration.py
(no matches, exit 1)
```
derived: `grep -n "subprocess.run" scripts/issue-3127/verify_preregistration.py` — result:
```
$ grep -n "subprocess.run" scripts/issue-3127/verify_preregistration.py
74:    return subprocess.run(["git", "-C", str(repo_root), *args],
79:    return subprocess.run(["gh", *args], capture_output=True, text=True)
```
Neither of the file's two `subprocess.run` call sites passes `timeout=`. derived: same probe, `Attack3_Timeout`, `subprocess.run` mocked to raise `subprocess.TimeoutExpired` on the `git log` call (the only way to observe any behavior at all, since without a configured timeout the real code path never raises this in production — a real hang just blocks) — result:
```
Attack3 (timeout): UNCAUGHT TimeoutExpired propagates out of verify()
Attack3 verdict: uncaught-exception
1 passed in 0.13s
```
Absent: `TimeoutExpired` is not caught anywhere in `verify()` or `main()`; it propagates uncaught. In real operation (no injected mock) there is no timeout configured at all, so a genuine hang (network stall on `gh`, a git credential prompt, a lock wait) blocks the process indefinitely rather than "failing closed with the command and its status named" — it does not fail at all, it never returns. This is outside round 3's own declared scope: `GitCommandError`'s docstring (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:50-62`) says "Raised when a git command ... exits non-zero," and round 3's sweep report does not mention timeouts. Not a regression introduced by round 3; a gap outside the axis it swept.

### Attack 4 — malformed output on a successful (exit 0) call

derived: first pass mocked both `git log` calls to return the same garbage stdout on exit 0, which coincidentally routed into the squash-collision fallback for an unrelated reason (`_resolve_via_pr_history`, missing `verification_pr:` field). Re-run isolating the injection to only the pre-registration path's call, results path left genuinely uncommitted — `/tmp/pr3169_check/adversarial_probe2.py`:
```
Attack4b (malformed prereg stdout, results legitimately uncommitted): True | OK: docs/issue-3127/decisions/pre-registration.md committed at NOT-A-VALID-SHA-LINE; docs/issue-3127/_assets/consumer-path-results.json not yet committed (working tree only), so it cannot precede the pre-registration
```
Surface: `_first_commit_for_path` (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:108-114`) does not validate that a `--format=%H` line looks like 40 hex characters — any non-blank line on exit 0 is accepted as a commit sha. Traced forward per silent-failure-audit's Step 3: the `results_commit is None` branch (`421bfb7a:scripts/issue-3127/verify_preregistration.py:318-325`) already returns `ok=True` unconditionally on any non-`None` `prereg_commit`, garbage or real, so this specific branch's outcome is unchanged by the malformed value. The two branches where a garbage sha would matter -- `merge-base --is-ancestor` (`:336-352`) and `_resolve_via_pr_history`'s merge-commit bind (`:241-247`) -- both fail on a non-object garbage string via real git/gh errors, which are already handled as hard failures there (see Attack 7). No downstream path was found where this malformed-output gap flips a genuine ordering violation into a pass; recorded as a minor robustness gap, not a correctness defect, under Open findings below.

### Attack 5 — legitimate empty result (real "no commits yet")

derived: same probe, `Attack5_LegitimateEmpty`, no mocking — real git repo, one unrelated commit, query for a path with no history — result:
```
Attack5 (legitimate empty, real git): None
1 passed in 0.13s
```
Present: unchanged from pre-fix behavior; the legitimate-empty case was not swept into the failure bucket.

### Attack 6 — gh command nonzero exit with stderr, inside the PR-history fallback

derived: `Attack6_GhNonzeroWithStderr`, `gh pr view <n> --json commits` returns exit 1 / stderr `gh: rate limited`, `mergeCommit` lookup and bind already satisfied — result:
```
Attack6 (gh commits nonzero+stderr): False | `gh pr view 42 --json commits` failed or returned no commits -- cannot resolve the pre-squash order (fail closed: unavailable evidence is not a pass)
1 passed in 0.13s
```
Present: fails closed, names the failing `gh` invocation.

### Attack 7 — merge-base given a bogus (non-existent) object

derived: `Attack7_MergeBaseRealError`, real git repo with both paths committed, `merge-base --is-ancestor <real-sha> <40-hex-zeros-and-dead>` run directly (not mocked) — result:
```
Attack7 (merge-base bogus object) exit code: 128 stderr: fatal: Not a valid object name 0000000000000000000000000000000000dead
1 passed in 0.13s
```
Present: confirms live that a real git error on this call exits `128` (not `1`), and `421bfb7a:scripts/issue-3127/verify_preregistration.py:341-352` already branches `0`/`1`/other explicitly, treating anything other than `0` or `1` as a hard error rather than "not an ancestor" -- this branch predates round 3 (present unchanged since round 2's commit `34401620`, confirmed by reading `34401620:scripts/issue-3127/verify_preregistration.py:301-312`, byte-identical to the round-3 version at this site) and round 3's report correctly lists it as "already correct, no code change."

### Independent re-sweep

derived: read every one of the 7 candidate sites in `421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py` myself (`_run_git`/`_first_commit_for_path`, `_read_frontmatter`, `_repo_owner_repo`, `_pr_merge_commit`, `_pr_commit_order`, `_first_pr_commit_touching`, `merge-base --is-ancestor`) and classified each independently, per `defect-verification-independence-from-upstream-verdicts`, before diffing against round 3's own table in `docs/issue-3127/reports/silent-failure-audit+implementation-blueprint+experiment-trust-15d48cd6.md` (frontmatter `upstream:`, same-commit). Agreement on all 7: site 1 (git-log for `_first_commit_for_path`) fixed this round; sites 2-6 (`_read_frontmatter`, `_repo_owner_repo`, `_pr_merge_commit`, `_pr_commit_order`, `_first_pr_commit_touching`) each collapse a `gh`/parse failure and a legitimate-empty result to the same `None`, and every caller of each already fails closed uniformly on `None` -- no branch reads `None` as a pass; site 7 (`merge-base --is-ancestor`) confirmed already-correct pre-round-3 above (Attack 7). No site was found that round 3's own sweep missed, within the sweep's own declared axis (git-command-failure vs. legitimate-empty). The timeout gap (Attack 3) and the output-validation gap (Attack 4) are a different axis -- hang-safety and output-shape validation -- that round 3's sweep never claimed to cover (its own docstring scopes the rule to "exits non-zero").

### Recorded limitation

derived: `git show 421bfb7a -- docs/issue-3127/decisions/pre-registration.md` on the scratch clone — result (added section, verbatim):
```
+## Limitation of the mechanical ordering check
+
+`scripts/issue-3127/verify_preregistration.py` proves *construction* order:
+which commit exists first in git's (or, on the squash-collapse fallback, the
+originating PR's) recorded history. It does not and cannot prove *decision*
+order. Git ancestry has no way to see what happened before a commit was
+made -- a threshold could be decided after privately observing a result and
+only then committed first, and the check would read that as a clean pass,
+identical to a threshold that was genuinely fixed in advance. ...
+Nobody should read a passing `verify_preregistration.py` run as proving more
+than "the recorded construction order was correct" -- it says nothing about
+what the author knew before writing either file.
```
Present: it is its own top-level section immediately after the rule it qualifies, states plainly that the check proves construction order not decision order, and gives the concrete failure mode (deciding after observing, then committing in order) the hedge would otherwise obscure. Not buried, not hedged into meaninglessness.

### Acceptance checks and full test suite

derived: run on the scratch clone at `421bfb7a`, `origin` remote pointed at the real GitHub repo:
```
$ python3 scripts/issue-3127/run_consumer_pair.py --dry-run
[... dry-run plan printed, nothing executed ...]
exit=0
$ test -f docs/issue-3127/_assets/consumer-path-results.json
exit=0
$ python3 scripts/issue-3127/verify_preregistration.py
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
exit=0
```
acceptance: all three of issue #3127's acceptance checks — result: exit 0 (fences above).

derived: `python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q` on the scratch clone — result:
```
...................                                                      [100%]
19 passed in 0.86s
```
matches round 3's own claimed count (19 passed).

derived: `python3 -m pytest tests/ -q` on the scratch clone — result:
```
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
1 failed, 370 passed in 10.24s
```
Same single failure PR #3219 and round 3 both noted, in `tests/test_spawn_gate_wiring.py` (path confirmed tracked via `git ls-files | grep test_spawn_gate_wiring.py`), class `HooksJsonWiringIsAdditive`, method `test_pre_existing_post_tool_use_commands_are_all_still_present` — a branch-staleness artifact (missing two `PostToolUse` hooks added on `main` after this branch was cut), not caused by round 3's fix.

derived: `git fetch https://github.com/tokenmaxxxer/on-the-record.git main && git log --oneline HEAD..FETCH_HEAD | wc -l` on the scratch clone — result:
```
50
```
Round 3 measured 48 at the time it ran; re-measured now at 50 -- more commits landed on `main` in the interval. Still present, and growing. PR #3169's branch needs an integration/rebase pass before it can land; not performed here per the task's "do not merge PR #3169, do not edit PR #3169" instruction.

## Why

The task named this residual finding as the fifth recurrence of the same defect shape (a check that cannot observe something reports the answer it would have given had it observed nothing) across files tonight, and said the value of a sweep is entirely in whether it was done properly. The re-sweep above was done by classifying each site from the code first, then diffing against round 3's own table (`defect-verification-independence-from-upstream-verdicts`), not by reading round 3's table and confirming it looks reasonable. The five attack vectors (stderr-bearing failure, silent failure, timeout, malformed output, legitimate empty) were run as real subprocess-level injections against the actual file, one level below the file's own `_run_git`/`gh_runner` wrappers, so this verification does not inherit any blind spot in round 3's own test doubles. The timeout and malformed-output findings were pursued past the first failing assertion to determine whether they are exploitable (would flip a genuine violation into a pass) rather than merely present, per silent-failure-audit's Step 3 forward-trace requirement -- see Attack 4's trace above, which is why it is graded Surface (real gap, no exploitable consequence found) rather than Incorrect.

## What did not work

None.

## Upstream basis

See frontmatter `upstream:` for exact paths/shas. Round 2's verification record and round 3's own record were read first per task instructions; this record does not re-derive their Present grades on the merge-commit bind or the `--follow` fix (round 2), only re-derives round 3's fix and its sweep independently, per each attack section above.

## Open findings

1. **No timeout on either `subprocess.run` call site** (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:73-75,78-79`) -- see Attack 3. A real hang blocks indefinitely rather than failing closed. Outside round 3's declared axis, not a regression. Resolution path if a future round wants to close it: add `timeout=` to both calls plus a caught `subprocess.TimeoutExpired` -> fail-closed branch. Not fixed here (task instruction: do not edit PR #3169).
2. **`_first_commit_for_path` does not validate git-log output shape on a successful exit** (`421bfb7a619a8eb70b74cd29d3768aa8c7649a51:scripts/issue-3127/verify_preregistration.py:108-114`) -- see Attack 4. Traced forward, no exploitable false-pass found; recorded as a minor robustness gap, not a correctness defect.
3. Branch staleness against `origin/main` -- see "Acceptance checks and full test suite" above (50 commits behind, one pre-existing unrelated test failure). Unchanged by this round; out of scope for this record (task: do not merge PR #3169).

## Next steps

No further action is queued by this record itself -- the seven attacks and the acceptance/test-suite runs are all recorded with their commands and output under "What was done" above.

Whether to open a round 4 for open finding 1 (timeouts, listed above) is a judgment call for whoever owns PR #3169 next -- this record surfaces it but does not act on it unilaterally, consistent with round 3's own choice to record (not act on) the construction-vs-decision-order limitation.

skill-verdict: adversarial-review — applied: invoked; used its blind, builder-independent attack structure (fresh scratch clone, `subprocess.run` mocked one level below the file's own wrappers, no reliance on round 3's own test doubles) to construct the seven attacks and the independent re-sweep above.
skill-verdict: silent-failure-audit — applied: invoked; used its Step 1-3 procedure (enumerate every subprocess/error-handling site, classify Handled/Silently-Absorbed/Unreachable, forward-trace each candidate to a downstream consequence) to re-derive the 7-site sweep and to determine that the Attack-4 malformed-output gap, while a real Silently-Absorbed-shaped pattern at the source, has no downstream consequence that changes a verification outcome.
skill-verdict: experiment-trust — not-applicable: no A/B experiment result was interpreted or acted on this round; `run_consumer_pair.py` was invoked only in `--dry-run` mode (plan printed, nothing executed).
