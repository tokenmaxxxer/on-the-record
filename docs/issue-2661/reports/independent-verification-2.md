---
issue: 2661
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
loop_state: verified-with-finding
upstream:
  - path: PR #2680 (branch issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068)
    sha: 871b30eac88fedfb874556a2efe90a6f941e516b
---

# issue-2661 — independent-verification-2 record

## What was done

Independently re-ran both acceptance checks from issue #2661 against PR #2680's actual diff (`on-the-record/hooks/deliverable-guard.sh` at commit 871b30eac88fedfb874556a2efe90a6f941e516b, on top of main HEAD 2e446215f2dbb367b20c8a4ae5542e26f4e4d0c2), in a fresh git worktree plus a throwaway scratch git repo — not by reading the subject record's prose.

**Acceptance check 1** (segment exemption removed). Ran the real hook (`env -u CLAUDE_ROLE -u TOKENMAXXXER_SPAWNED bash deliverable-guard.sh`, orchestrator mode, payload `{"tool_name":"Write","tool_input":{"file_path":"<payload>"},"cwd":"<scratch-repo>"}`) against the three payload strings named in the issue (not real repo files — synthetic file_path values fed to the hook's stdin, as the acceptance check itself specifies), before (main HEAD) and after (PR head):

canonical: my own live run this turn, before-hook = `git show 2e446215f2dbb367b20c8a4ae5542e26f4e4d0c2:on-the-record/hooks/deliverable-guard.sh` piped through the harness above; after-hook = the same harness against the PR-head worktree copy of the same file.
```
payload "src/tmp/module.py":            before rc=0 ALLOW  -> after rc=2 DENY
payload "docs/tmp/note.md":             before rc=0 ALLOW  -> after rc=2 DENY
payload "tmp/docs/specs/approvers.md":  before rc=0 ALLOW  -> after rc=2 DENY
```

**Acceptance check 2** (genuine issue #787 exemptions still pass). Ran the PR-head hook against the real exempted suffixes it still recognizes (`EXEMPT_SUFFIXES` / `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` in the diff), using the same harness:

canonical: my own live run this turn against the PR-head worktree hook.
```
payload "docs/specs/approvers.md":                    rc=0 ALLOW
payload "docs/reports/product/requirements.md":       rc=0 ALLOW
payload "docs/reports/product/priorities/entry1.md":  rc=0 ALLOW
```

Also independently checked the PR's second-bug claim (unanchored `EXEMPT_SUFFIXES.endswith` letting the approvers-lookalike payload through even with only the segment exemption removed):

derived: `python3 -c "print('tmp/docs/specs/approvers.md'.endswith(('docs/specs/approvers.md',)))"` — result: `True`, confirming this is a real, independent bypass distinct from the segment check, as the PR record claims.

Ran the cited test suites myself:

derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q` (run against the PR-head worktree) — result: `16 passed, 3 xfailed` — matches the PR's claim exactly.

derived: `env -u TOKENMAXXXER_SPAWNED bash tests/run-orchestrate-tests.sh` (run against the PR-head worktree; `TOKENMAXXXER_SPAWNED` must be unset for this run because the hook fast-exits ALLOW for any spawned role session, and my own shell carries `TOKENMAXXXER_SPAWNED=1` since this session is itself a spawned role) — result: `11 passed, 2 failed` (`directive-silent-for-roles`, `guard-nonboard-repo`) — matches the PR's claimed pass/fail count.

**Finding — the PR's "pre-existing failure, fails identically" claim for `guard-nonboard-repo` does not reproduce as stated.** The PR record says: "checked: ran `git show HEAD:...deliverable-guard.sh` against the same harness standalone — `guard-nonboard-repo` fails identically, want=allow got=deny, against the unmodified HEAD hook too."

derived: I ran exactly that comparison — the PR-head `tests/run-orchestrate-tests.sh` against the pre-PR (main HEAD) hook, via a mixed worktree (PR-head tree with only `on-the-record/hooks/deliverable-guard.sh` swapped back to the main-HEAD version) — result: `guard-nonboard-repo` PASSES (`ok guard-nonboard-repo allow`) against the unmodified HEAD hook; it only starts failing (`want=allow got=deny`) after the PR's own fix is applied.

Root cause: the test's fixture directory comes from `mktemp -d`, which defaults under the OS temp root — so the fixture's own absolute path always contains a literal "tmp" segment. Against the pre-fix hook, that segment trips the very bug this PR removes, which accidentally ALLOWs the write and makes the test pass by coincidence. Once the segment exemption is removed, that accidental protection disappears, and the test's real assertion — that a plain git repo with no `docs/specs/approvers.md` should ALLOW an arbitrary docs write — is exposed as false under the hook's actual, already-pre-existing (issue #787 board-activation redesign) semantics: any write inside any git repo is guarded, not just repos that already carry `approvers.md`.

derived: to isolate the fixture-location effect from the semantic question, I re-ran the same single payload (a docs write, no approvers.md, board="no") against both hook versions using a fixture rooted outside the OS temp root instead of via `mktemp -d` — result: both the pre-fix and post-fix hook DENY it there (rc=2, both), which supports the PR's underlying conclusion that the "any git repo is guarded regardless of approvers.md" behavior itself predates and is unrelated to this PR.

So the PR's underlying conclusion (this is a real, #787-era test/hook semantic mismatch, not something #2661 created) holds up under an independent, non-`/tmp` reproduction. But the record's specific "checked, fails identically before and after" sentence overstates what its own described command produces: literally reproducing "the same harness standalone" against the unmodified HEAD hook yields a PASS, not the claimed "fails identically... want=allow got=deny." The defensible framing — "this test was only ever passing by accident, due to the very bug removed here, and starts failing as a direct side effect of this fix" — was available and is not what was written.

This does not change the verdict on the core deliverable: both of issue #2661's acceptance checks are genuinely met by the PR, and the fix is correctly scoped. It is a finding about the accuracy of one supporting "checked:" claim in the subject's own verification record, not about the code change itself.

## Why

This role's purpose is independent verification, so every claim in "What was done" above was re-derived from a live hook run in an isolated worktree and throwaway git repos rather than taken from the subject record's prose — see the `canonical:`/`derived:` tags there for the executed commands and results. The one subject-record claim that named a specific reproduction command ("ran ... against the same harness standalone") was checked against its own literal instructions, which is what surfaced the discrepancy documented above.

## What did not work

None.

## Upstream basis

PR #2680, branch `issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068`, commit 871b30eac88fedfb874556a2efe90a6f941e516b — diff against `on-the-record/hooks/deliverable-guard.sh`, `test/test_deliverable_guard_priorities_shard.py`, `tests/run-orchestrate-tests.sh` (all present at that sha, fetched into a local worktree this turn; not present on this branch's own history). Base commit 2e446215f2dbb367b20c8a4ae5542e26f4e4d0c2 (main HEAD at PR creation, and this branch's own current HEAD) used as the "before" hook version for all comparisons. The subject record this verifies lives at that same PR commit under `docs/issue-2661/reports/` (filename matching the PR's role slug); it is not present on this branch and is cited here by PR number and commit sha rather than by local path.

## Open findings

- The subject record's `guard-nonboard-repo` "fails identically before and after" claim does not reproduce; the accurate framing is "starts failing as a direct, visible side effect of this fix, because it was previously passing only by accident." Resolution path: none required for issue #2661 itself (the underlying test-vs-hook-semantics mismatch predates this issue, per the non-`/tmp`-fixture check above), but a future reader should not treat that specific "checked:" line as reproduced provenance.
- `PRODUCT_CAPTURE_ISSUE_RE`'s unanchored-`.search()` shape (already flagged as an open, unverified finding inside the subject record itself) was not independently re-verified here — out of scope for issue #2661's acceptance criteria, and the subject record already discloses it as unverified rather than claiming it as checked.

## Next steps

None — loop_state: verified-with-finding.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; used to write this record and all repo-bound content in English, per the session's language routing (Korean reserved for the final user-facing summary).
