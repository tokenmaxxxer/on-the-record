---
issue: 2661
role: silent-failure-audit+secure-coding-input-validation-injection-defense-07028068
author: silent-failure-audit+secure-coding-input-validation-injection-defense-07028068
skills: silent-failure-audit (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: same-commit
---

# issue-2661 — silent-failure-audit+secure-coding-input-validation-injection-defense-07028068 record

## What was done

Build-now bypass (contract v3 s19a): CORE_BUILD_NOW=1 was set in this session's environment by the spawner — checked: `printenv | grep CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. So this record delivers directly on issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068, no phase-1 proposal round.

`on-the-record/hooks/deliverable-guard.sh` had an unconditional exemption: any write whose file_path contained a path *segment* literally named scratch, tmp, .git, or plugin-cache — anywhere in the path — was allowed with no filesystem check (`segs = [s for s in n.split("/") if s]; if any(s in ("scratch", "tmp", ".git", "plugin-cache") for s in segs): sys.exit(0)`).

Removed that segment check in full and replaced the comment explaining why (`on-the-record/hooks/deliverable-guard.sh` lines ~220-244). Also anchored a second, independently-discovered bypass in the same file: EXEMPT_SUFFIXES (the docs/specs/approvers.md-and-siblings allowlist) was matched with unanchored `n.endswith(EXEMPT_SUFFIXES)` against the raw, possibly caller-rooted path — so a payload like "tmp/docs/specs/approvers.md" passed this check on its own, independent of the segment exemption, merely by ending in the recognized suffix. Fixed by reusing the git-root-relative resolution already computed for the priorities-shard exemption (renamed `priorities_candidate` to `root_relative_n` since it now backs both checks) and requiring exact equality (`root_relative_n in EXEMPT_SUFFIXES`) instead of `endswith`.

PRODUCT_CAPTURE_ISSUE_RE (the docs/issue-\d+/reports/product/*.md regex) has the identical unanchored-`.search()` shape and is very likely the same class of bug, but no acceptance path here exercises it and I did not touch it — logged under Open findings below rather than fixed, matching the issue's own instruction not to expand scope past what's needed.

Updated two stale tests that assumed the old behavior:
- `tests/run-orchestrate-tests.sh`: the `guard-outside-trees` case (a top-level scratch/ path, wanted allow) is now `guard-scratch-not-exempt` (wants deny) — a board-repo write under a top-level scratch/ is now correctly denied, like any other unrecognized deliverable-shaped path.
- `test/test_deliverable_guard_priorities_shard.py`: updated a comment that asserted the (now-removed) tmp-segment exemption as a reason the fixture avoids the system tempdir, and added 5 new regression cases covering the src-tree, docs-tree, and approvers-lookalike payloads named in the issue's acceptance check (all now denied), a genuine docs/specs/approvers.md write (still exempt), and a top-level scratch/ write (now denied).

## Why

**Acceptance check 1** (run the real hook against the three file_path payloads the issue names and show the verdict for each) — verdicts, before and after, run against the real shipped hook in true orchestrator mode (`env -u CLAUDE_ROLE -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh` against a fresh `git init`'d temp repo, payload `{"tool_name":"Write","tool_input":{"file_path":"<path>"},"cwd":"<repo>"}`):

canonical: before fix (`git show HEAD:on-the-record/hooks/deliverable-guard.sh` piped through the same harness) — the src-tree payload (segments: src, tmp, module.py) RC=0 ALLOW; the docs-tree payload (segments: docs, tmp, note.md) RC=0 ALLOW; the approvers-lookalike payload (segments: tmp, docs, specs, approvers.md) RC=0 ALLOW — all three silently exempted.
canonical: after fix (working-tree hook, same harness) — the same three payloads: RC=2 DENY, RC=2 DENY, RC=2 DENY — all three correctly denied as ordinary deliverable-shaped paths.
The approvers-lookalike payload needed the second (EXEMPT_SUFFIXES-anchoring) fix as well as the segment-removal fix — checked: removing only the "tmp" entry from the segment tuple (leaving the rest of the file unchanged) still left this payload at RC=0, because the unrelated unanchored-suffix bug fires first in source order (the EXEMPT_SUFFIXES check runs before the segment check) — result: rc=0 EXEMPT even with the segment tuple patched, confirming this is a second, independent root cause and not a duplicate report of the first.

**Acceptance check 2** (identify what issue #787 actually needed exempted, construct those paths, show they still pass): dispatched a background research agent to find what real, currently-existing write path needs scratch, tmp, .git, or plugin-cache exempted. Findings, each spot-checked by me afterward:

- plugin-cache: no real path on disk or in code has this literal hyphenated segment. checked: `grep -rn "plugin-cache" .` across the repo — result: only prose/comment hits, never a path; the real plugin install layout is `~/.claude/plugins/cache/tokenmaxxxer/...` — "plugins" and "cache" are two separate segments, never joined. derived: `printenv | grep -E 'ON_THE_RECORD|CLAUDE_PLUGIN_ROOT_CORE'` — neither value contains a plugin-cache segment.
- scratch: no orchestrator/spawner code (spawn.py, roster.py, pipeline.py, the hooks) creates or writes a directory literally named scratch. All "scratch" hits in the repo are prose ("scratch notes", "scratch repo" in test/harness descriptions) or ephemeral test fixtures under /tmp, never a supported top-level convention documented in docs/handbooks/ or README.md — checked: `grep -rln "scratch/" docs/handbooks README.md CLAUDE.md` — result: no hits.
- tmp (as a project-relative segment, not the OS temp root): no orchestrator code creates a project-relative tmp/ directory. Every real "tmp" usage found (session-role-bind.sh, approval-gate.sh, etc.) is `os.environ.get("TMPDIR", "/tmp")` — the OS temp root, not a project convention — and the actual session workspace root is `~/.tokenmaxxxer/work/<repo>-<issue-role>` (MUSTER_WORKSPACE_ROOT), which has no tmp segment.
- .git: real — every git repo has one, including the plugin's own checkout (checked: `ls -d ~/.claude/plugins/marketplaces/tokenmaxxxer/.git` — result: exists) — but no legitimate Write/Edit/NotebookEdit tool call ever targets a path *segment* named .git; git manages its own internals through its own subprocess, never through Claude's Write tool. The removed header comment's own justification ("the muster checkout itself") was actually about the separate git-root-*walk* logic further down in the same file (finding the repo root to decide whether a write is "in a board repo" at all), not about a Write call's own path containing a .git segment — a different mechanism this fix does not touch.

Conclusion, stated plainly per the acceptance's own fallback clause ("state plainly if no real case needs it, and remove the exemption instead"): no real write path in this codebase, or in this system's actual plugin install layout, depends on any of the four segment names. The exemption is removed in full rather than narrowed.

**.git's distinct reasoning** (issue's explicit ask: settle, and state, whether .git belongs in that tuple for a different reason than the other three): scratch/tmp/plugin-cache are pure convention with zero real backing evidence anywhere in the codebase or on this install. .git is different — it is a real, universal directory that exists in every git repo, so it is not "unused" in the same sense. But it still does not belong in a write-path exemption: if a session's own Write/Edit tool call ever targeted a path containing a .git segment, that call would already be suspicious on its own terms (Claude's Write tool has no legitimate reason to target git-internal paths), so exempting it from the deliverable check does not protect any real workflow — it would only ever offer a disguise for an already-anomalous write. Removed for that reason, not by inheritance from the other three.

The must-not clause (do not decide the exemption from filesystem state the guarded actor can arrange) was honored by not inventing a fifth path-shaped resolution: the two remaining exemptions this fix touches (EXEMPT_SUFFIXES, PRODUCT_CAPTURE_PRIORITIES_DIR_RE) both now resolve through the same, already-landed git-root-walk mechanism from issue #2637 — not a new one — and inherit that mechanism's already-documented, already-expectedFailure-tested residual gap (a session can plant its own .git to steer the walk). No new filesystem-state dependency was added; an existing one, already reviewed and accepted for the priorities exemption, was extended to cover the sibling EXEMPT_SUFFIXES check consistently.

## What did not work

None.

## Upstream basis

`on-the-record/hooks/deliverable-guard.sh` at HEAD (commit 2e446215, this branch's parent commit) — the file this record modifies in the same commit. `docs/issue-787/reports/implementation/2026-08-11-hunt-h1-deliverable-guard.md` and commit 8b449d98 (`git show 8b449d98 -- on-the-record/hooks/deliverable-guard.sh`) — the change that introduced the segment exemption this record removes, read to recover its original stated justification before assessing whether that justification still holds. `test/test_deliverable_guard_priorities_shard.py` at HEAD — the existing regression suite for the sibling priorities-shard exemption, read to reuse its already-accepted root-resolution technique rather than inventing a new one.

## Open findings

- PRODUCT_CAPTURE_ISSUE_RE (`on-the-record/hooks/deliverable-guard.sh`, the docs/issue-\d+/reports/product/(requirements|priorities|philosophy|goals)\.md$ regex) is matched with unanchored `.search()` against the raw path, the same shape as the EXEMPT_SUFFIXES bug this record fixes — e.g. a payload like "tmp/docs/issue-5/reports/product/goals.md" is very likely also wrongly exempted, though I did not verify it live since no acceptance path here exercises it. Resolution path: a follow-up issue anchoring this regex against root_relative_n the same way EXEMPT_SUFFIXES and PRODUCT_CAPTURE_PRIORITIES_DIR_RE now are.
- The issue-#2637-documented git-root-walk gap (a session can plant its own .git directory or symlink to steer where the walk resolves "repo root" to) now also applies to the EXEMPT_SUFFIXES check, since it was moved onto the same resolution mechanism. This is an extension of an already-known, already-accepted residual (issue #2637 round 4, test/test_deliverable_guard_priorities_shard.py's three expectedFailure cases), not a new independent gap — no new test added for it here since #2637's existing expectedFailure cases already cover the walk itself. Resolution path: same as #2637's own open resolution — out of scope for a path-shaped fix per that issue's existing consult finding.
- tests/run-orchestrate-tests.sh's `directive-silent-for-roles` and `guard-nonboard-repo` cases fail both before and after this change — checked: ran `git show HEAD:on-the-record/hooks/deliverable-guard.sh` against the same harness standalone — `guard-nonboard-repo` fails identically, want=allow got=deny, against the unmodified HEAD hook too. Pre-existing, unrelated to this fix (a stale "board repo requires docs/specs/approvers.md to already exist" precondition that issue #787 itself removed without updating this test, and an unrelated directive.sh role-identity resolution difference under a spawned session's own environment). Not fixed here — out of scope for issue #2661, which is about the segment exemption in deliverable-guard.sh specifically. Resolution path: a separate test-hygiene issue.

## Next steps

None — loop_state: landed.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; used to frame the audit of the guard's own sys.exit(0) exemption paths as silent-allow defects (an exemption firing with no signal to the caller is the same failure shape as a caught-and-ignored exception — a decision point that silently drops the deny path) when tracing why each of the three acceptance payloads passed before the fix.
skill-verdict: secure-coding-input-validation-injection-defense — applied: invoked; used to choose exact-match allowlisting (root_relative_n in EXEMPT_SUFFIXES) over the unanchored substring/suffix matching that let a caller-controlled path smuggle a recognized suffix past the check — the same allowlist-vs-substring-match distinction the skill frames for validating untrusted input at a trust boundary (here, a session-reported file_path crossing into the guard's allow/deny decision).
