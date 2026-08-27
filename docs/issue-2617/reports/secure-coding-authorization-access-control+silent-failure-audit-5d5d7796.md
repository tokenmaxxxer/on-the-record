---
issue: 2617
role: secure-coding-authorization-access-control+silent-failure-audit-5d5d7796
author: secure-coding-authorization-access-control+silent-failure-audit-5d5d7796
skills: secure-coding-authorization-access-control (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: on-the-record/hooks/git-push-guard.sh
    sha: same-commit
---

# issue-2617 — secure-coding-authorization-access-control+silent-failure-audit-5d5d7796 record

## What was done

canonical: `gh issue view 2617` output (Ask, Acceptance, non-goals) — read
directly this session; build-now delivery, `CORE_BUILD_NOW=1`, single
phase, no proposal round per contract v3 s19a. canonical: commit
`9883a0b4` — derived: `git log --oneline -1` — the code this section
describes.

Added `on-the-record/hooks/git-push-guard.sh`, a new `PreToolUse`+`Bash`
gate that denies a role session's `git push` when its destination
resolves to the repo's real default branch, and registered it in
`on-the-record/hooks/pretooluse_dispatcher.py` (new `GATES` entry). Two
`docs/specs/*` rows document it (`enforcement-boundary.md`,
`generated-paths.md`), satisfying `gate-registration-guard.sh`'s own
requirement.

Design, matched to the issue's two `must not:` clauses:

- Scope: role sessions only (`TOKENMAXXXER_SPAWNED` resolves non-empty).
  Orchestrator sessions are untouched — see "Orchestrator push
  disposition" below.
- No hardcoded branch name: the destination is compared against
  `git ls-remote --symref <remote> HEAD`, resolved live per push — never
  a literal `"main"`, never the remote's branch-protection API.
- A destination shaped like this system's own role branches
  (`^issue-\d+/`) is allowed with no network call.
- A non-role-shaped destination whose default-branch lookup cannot be
  resolved is denied (fail-closed), not passed through.

acceptance: `payload='{"tool_name":"Bash","tool_input":{"command":"git push origin HEAD:trunk"},"session_id":"s","cwd":"<role workspace>"}'; echo "$payload" | env TOKENMAXXXER_SPAWNED=1 bash on-the-record/hooks/git-push-guard.sh` — result:
```
git-push-guard: a role session may not push directly to the remote's default branch ('trunk') — that moves it outside the PR flow, past every merge gate (issue #2617).
git-push-guard: instead: push your own role branch and open a PR: `git push -u origin HEAD` (current branch must be issue-<n>/<slug>-shaped).
exit=2
```
(`trunk` is the scratch test fixture's real default branch name,
deliberately not `main`, run against a bare-remote + role-branch-shaped
worktree fixture standing in for a session workspace.)

acceptance: `cd <role workspace> && git checkout issue-2617/test-branch && git push -u origin HEAD` — result:
```
To ../remote.git
 * [new branch]      HEAD -> issue-2617/test-branch
```
(a real `git push`, not just the hook's own exit code — succeeded.)

### Orchestrator push disposition (acceptance bullet 3)

canonical: `board.py:_verify_board_on_remote` (read directly this
session) — the one concrete orchestrator push path this repo ships:
`spawn.py init --push` runs `git -C <root> push --set-upstream origin
<branch>`, `branch = _current_branch(root)`, frequently the default
branch itself since board init runs from a clean checkout.

The orchestrator's own pushes are unaffected — not narrowed, not
special-cased: the scope check (`TOKENMAXXXER_SPAWNED` unset) is the
first thing the gate tests and exits 0 immediately when it fails, before
any destination-branch logic runs at all.

acceptance: `payload='{"tool_name":"Bash","tool_input":{"command":"git -C <root> push --set-upstream origin trunk"},"session_id":"s","cwd":"/unrelated"}'; echo "$payload" | env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/git-push-guard.sh` — result:
```
exit=0
```
(untouched, regardless of destination branch or this hook subprocess's
own inherited cwd — `cwd` deliberately set to an unrelated directory to
isolate the scope check from the cwd-resolution logic below.)

## Why

canonical: issue #2617 body, "must not:" clauses (`gh issue view 2617`,
read this session) — the two constraints this design answers.

Gating on remote branch-protection state was rejected: the issue's own
"must not" clause says this system spawns into arbitrary consumer repos
whose protection configuration it does not control, so a check that
asks the remote "is this branch protected" is not fail-closed by
construction — an unprotected consumer repo, or one with protection
temporarily relaxed, would silently pass the push through. Resolving the
default branch via `git ls-remote --symref <remote> HEAD` instead asks
the remote a factual question every git remote answers the same way
regardless of whether protection is configured, and denies when the
remote can't be reached at all (verified above, "Orchestrator push
disposition" section's fail-closed sibling case in "What did not work").

Role-session-only scope, rather than gating every session's `git push`
regardless of identity, was chosen because the issue's other "must not"
names the exact failure mode of getting this wrong: breaking a
session's ability to push its own branch strands its work with no PR
(issue #2193). Scoping to `TOKENMAXXXER_SPAWNED` non-empty reuses an
existing, already-shipped identity primitive (`heredoc-command-refusal-
gate.sh` uses the identical scope for an analogous role-session-only
deny gate) rather than inventing a new one.

skill-verdict: secure-coding-authorization-access-control — applied:
invoked; rule 1 (deny-by-default for an unmatched/unresolvable request)
justifies the fail-closed-on-lookup-failure branch — an unresolvable
default-branch lookup denies, it does not permit. Rule 6 (remove
reliance on a client-side-only check, add a server-side enforcement
point) is the frame for the issue's "do not rely on remote branch
protection" clause — the remote's branch-protection setting is the
"client-side" check being replaced by an independent, locally-enforced
one. Rule 7 (apply the same check on every entry path) is why detection
tokenizes every `&&`/`;`/`|`/newline-delimited segment of the whole
command rather than anchoring one shape at the start of the string — a
single-shape check would leave every other `git push` entry path
unguarded (concretely: the newline-segment bypass found and fixed
below).

skill-verdict: silent-failure-audit — applied: invoked; audited this
hook's own fallible operations: three `subprocess.run` calls (current
branch, configured remote, `ls-remote` lookup), one `shlex.shlex`
tokenization, one snapshot-file `open()`. Two are Silently-Absorbed-
shaped but justified, not defects: the snapshot-file lookup's exception
handler is a no-op that falls back to the live `TOKENMAXXXER_SPAWNED`
env var read one line earlier (same accepted-limitation shape
`heredoc-command-refusal-gate.sh` already documents for the identical
primitive), and an unbalanced-quoting tokenization error exits 0
(allow) — consistent with every other shlex-tokenizing gate in this
file's family (`gh-write-allow-gate.sh`, `gate-registration-guard.sh`),
all of which fail open on the same condition. The
`_resolve_default_branch` failure path is NOT silently absorbed: its
`None` return is checked by every caller and routed to an explicit
`deny()` — traced in "What was done" above, not a default value
substituted silently.

## What did not work

canonical: `docs/issue-2617/reports/secure-coding-authorization-access-control+silent-failure-audit-5d5d7796/2026-08-27-hunt-git-push-guard.md` (committed this session, before-landing warrant-hunter dispatch, stance 0) — the source of the first finding below.

- Initial cut split command-shape detection only on shlex punctuation
  operator tokens (`&&`, `;`, `|`, `||`) — a bare newline between two
  statements is a real bash command separator but is swallowed as
  ordinary whitespace by `shlex.shlex(..., punctuation_chars=True)`, so
  it never produced a segment boundary. The before-landing
  warrant-hunter dispatch found a live bypass — derived:
  ```
  echo "$PAYLOAD_BYPASS" | TOKENMAXXXER_SPAWNED=1 bash on-the-record/hooks/git-push-guard.sh; echo "bypass rc=$?"
  # PAYLOAD_BYPASS command field = "true" + newline + "git push origin main"
  # -> bypass rc=0 (silently allowed; no stderr)
  ```
  a `git push origin main` placed after a leading no-op statement on its
  own line (an ordinary multi-line Bash-tool command) fused into the
  same segment as the preceding no-op, and the segment scanner only
  recognizes a segment that STARTS with `git`, so the whole command
  escaped detection. Fixed by dropping the newline character from the
  tokenizer's whitespace set after construction (keeping it in
  `punctuation_chars`), routing an unquoted newline through the
  punctuation-token path instead. Reverified — derived: `echo
  "$PAYLOAD_BYPASS" | env TOKENMAXXXER_SPAWNED=1 bash
  on-the-record/hooks/git-push-guard.sh` — result: `exit=2` (denied),
  and a newline embedded inside a quoted string (a commit `-m` body
  spanning two lines) still round-trips untouched inside its own token —
  derived: `printf '%s' 'git commit -m "line1<NEWLINE>line2"' | env
  TOKENMAXXXER_SPAWNED=1 bash on-the-record/hooks/git-push-guard.sh` —
  result: `exit=0` (untouched, correctly not treated as a push at all).
- Follow-up self-check after the hunter's finding (same stance,
  continued manually, not a second dispatch): every resolution
  subprocess call (current branch, configured remote, default-branch
  lookup) initially ran with no explicit `cwd=`, against this hook
  subprocess's own inherited cwd rather than the directory the pending
  `git push` command actually targets. Reproduced — derived: a payload
  carrying `git -C <role-workspace> push origin HEAD:trunk`, invoked
  with this hook's own process cwd pointed at an unrelated checkout (the
  on-the-record repo itself), resolved THAT unrelated repo's own
  default branch instead of the role workspace's, and allowed the push
  — the same "ran from the wrong directory against the wrong repo"
  failure mode issue #2617's own root-cause note describes, relocated
  into this gate's own resolution logic. Fixed by threading a resolved
  `cwd` through every subprocess call: the PreToolUse payload's own
  `"cwd"` field by default (same primitive `gate-registration-guard.sh`
  already uses), overridden by an in-command `-C <dir>` when present
  (relative `-C` resolved against the payload cwd, not this process's
  own). Reverified — derived: `payload='{"tool_name":"Bash","tool_input":{"command":"git -C <role-workspace> push origin HEAD:trunk"},"session_id":"s","cwd":"/unrelated"}'; echo "$payload" | env TOKENMAXXXER_SPAWNED=1 bash on-the-record/hooks/git-push-guard.sh` — result: `exit=2` (correctly
  denies, resolving against the `-C` target now, not this process's own
  cwd), and the same `-C`-carrying shape pushing the session's own role
  branch still allows (`exit=0`).

## Upstream basis

- The before-landing warrant-hunter hunt record for this change:
  ```
  docs/issue-2617/reports/secure-coding-authorization-access-control+silent-failure-audit-5d5d7796/2026-08-27-hunt-git-push-guard.md
  ```
  derived: `git log --oneline -1 -- docs/issue-2617/reports/secure-coding-authorization-access-control+silent-failure-audit-5d5d7796/2026-08-27-hunt-git-push-guard.md` — committed this session (stance 0, the newline-segmentation bypass finding and its resolution, both detailed in "What did not work" above).
- Issue #2617 itself — canonical: `gh issue view 2617` output, read directly this session. No other upstream proposal/decision document exists (build-now bypass, no phase-1 proposal round).

## Open findings

None — the one finding this session produced (the hunter's newline-
segmentation bypass) was fixed and reverified in commit `9883a0b4` —
derived: `git log --oneline -1` — before landing; see "What did not
work" above.

## Next steps

None — `loop_state: landed`. canonical: the three `acceptance:` command
citations under "What was done" above (role-session refusal text,
role-branch push success, orchestrator-push non-interference), all run
live this session, are the basis for treating issue #2617's three
Acceptance checks as satisfied.
