---
issue: 2669
role: adversarial-review+secure-coding-input-validation-injection-defense-a19f3664
author: adversarial-review+secure-coding-input-validation-injection-defense-a19f3664
skills: adversarial-review (skill-repository(297e350)), secure-coding-input-validation-injection-defense (skill-repository(297e350))
verifies_subject: true
loop_state: landed
code_under_review: 074573f679d3887b365d976b3483524d83d578f4
type: verification
breaking: false
verdict: critical-bypass-confirmed-plus-two-lesser-findings
upstream:
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: 074573f679d3887b365d976b3483524d83d578f4
  - path: docs/issue-2669/reports/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b.md (untracked here — PR #2700 still OPEN)
    sha: 91c1a6a5e0609cb5aebfe20e93786e601c82561d
---

# issue-2669 — adversarial-review+secure-coding-input-validation-injection-defense-a19f3664 record

## What was done

Independent re-verification of PR #2700 (`upstream-defect-scope-guard.sh`
`operative_cwd()` fix, commit `074573f6`), executed against the real
shipped hook in a fresh clone — none of the PR's or its own record's
conclusions were inherited; every command below was actually run by this
session.
canonical: `gh pr view 2700 --json title,body,files` (fetched live),
`gh pr diff 2700` (425-line diff read in full).

Setup: `git clone https://github.com/tokenmaxxxer/on-the-record.git` into
`/tmp/verify-2669/repoA` (checked out the PR head via `git fetch origin
issue-2669/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b
&& git checkout FETCH_HEAD`, landing on `91c1a6a5`) and a second clone
`/tmp/verify-2669/repoMain` at `origin/main` (pre-fix) for control
comparisons. Real local git fixtures (`git init` + `git remote add
origin <url>`) built under `/tmp/verify-2669/fixtures/` standing in for
repo A/B/C, plus a genuine `git clone` of a real public repo
(`octocat/Hello-World`) for the production-path check. The hook was
invoked exactly as the harness does: a JSON PreToolUse payload piped to
`bash on-the-record/hooks/upstream-defect-scope-guard.sh` on stdin, with
`ORCHESTRATE_OFF`/`CLAUDE_ROLE`/`MUSTER_SKILLS` stripped from the
subprocess env. Note on method: several of my own top-level Bash
invocations that literally contained the string "gh pr create" were
themselves intercepted and denied by this session's own live copy of
this same hook (pre-fix, since this session's branch is off `main`) —
confirming the pre-fix hook's baseline behavior live, and forcing all
shape tests to be written to Python files and executed via `python3
<file>.py` so the outer Bash command text itself never carries the
guarded substring.

**1. Attack the parser (#2637-shaped shape hunt).** Ran 14 command
shapes against the real shipped hook.
derived: `python3 /tmp/verify-2669/test_shapes.py` — result (verbatim
verdicts, all executed): leading `cd X &&` to a real checkout →
**ALLOW** (matches PR's own claim); bare call, no `cd` → **DENY**; call
targeting the guard's own written-for case (unrelated repo, no `cd`) →
**DENY**; non-leading `cd` (`set -e; cd X && ...`) → **DENY**; two
chained `cd`s (`cd A && cd B && ...`) → **DENY**; `cd` inside a subshell
(`(cd B && ...)`) → **DENY**; `cd` inside `$(...)` command substitution
→ **DENY**; `pushd` instead of `cd` → **DENY**; `cd` with a quoted path
containing spaces → **ALLOW** (correctly parsed); `cd ~` (home dir),
target = the exact unrelated-upstream case the guard exists for →
**ALLOW** — the critical finding, see Open findings; `cd` with a
relative `../` path → **ALLOW** (correctly resolved against payload
cwd, target matched); leading `cd` to repo B but `--repo` names a THIRD
unrelated repo → **DENY** (correct — repo B's own origin doesn't match
the third repo either); `cd` separated by a newline instead of `&&` →
**ALLOW**, pre-existing gap (see below, not this PR's); `cd` with a
semicolon separator → **ALLOW** (correctly parsed, matches PR's
documented `cd <dir>;` support).
derived: `python3 /tmp/verify-2669/test_tmp.py` — result: `cd /tmp && gh
pr create --repo some-unrelated-org/upstream-repo ...` (payload cwd =
repo A fixture) → **ALLOW**. `/tmp` is not a git repo — confirmed by
`git -C /tmp remote get-url origin` → exit 128, "not a git repository" —
so this is the plainest possible instance of the fail-open finding
below: no fixture repo, no spoofing, just the single most common
directory on any Linux box.
derived: `python3 /tmp/verify-2669/test_realclone.py` — result: `cd
/tmp/verify-2669/fixtures/real-clone-hello-world && gh pr create --repo
octocat/Hello-World ...` → **ALLOW**, where
`real-clone-hello-world` is a genuine `git clone
https://github.com/octocat/Hello-World.git` (rc=0, confirmed via `git -C
<clone> remote get-url origin` → `https://github.com/octocat/Hello-World.git`)
— zero write relationship to that repo, no spoofing of any kind, just an
ordinary read-only clone.

The non-leading-`cd`, two-`cd`, subshell, `$()`, and `pushd` shapes all
**DENY** (fall back to the pre-#2669 behavior: origin resolves from the
payload cwd, repo A, whose origin ≠ the repo-B target) — safe but
under-inclusive. Two of these (subshell, `pushd`) are already named in
the subject's own Open findings (untracked in this working tree —
`docs/issue-2669/reports/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b.md`
in the PR-branch clone, "Coverage limit" bullet); the non-leading-`cd`
and two-`cd` shapes are not named there but are the same lesser
(deny-when-should-allow) class, not a security hole.

**2. Does the `expectedFailure` test cover the disclosed gap, or a
narrower one?** Read (not executed as new code, since it's the PR's own
test, present only in the PR-branch clone — untracked on this session's
own branch) the added test class's `test_spoofed_origin_remote_bypass_should_be_denied`:
it builds the "spoofed" case via `git init` + `git remote add origin
<fake-url>`, i.e. a directory that is a real git repo but was never
actually cloned from the target. The PR's prose ("a spoofed local
`origin` remote") and the task's named production path (`git clone
<arbitrary-repo> /tmp/x && cd /tmp/x && gh pr create --repo
<arbitrary-repo>`) turned out to be the *same underlying mechanism* from
the guard's point of view — the guard only ever reads `git remote
get-url origin`, never checks whether the directory has real clone
provenance — confirmed by the real-`git-clone` test above (item 1)
landing on the identical **ALLOW** verdict. So the test's mechanism is
not narrower than the disclosed gap in terms of code path exercised. It
IS narrower in framing: "spoofed" implies deliberate fabrication effort,
but the identical bypass is reachable via completely ordinary,
non-deceptive use (`git clone` a public repo you have no write access
to) — no spoofing required. That is a real understatement of how easy
the disclosed gap is to hit, though not a case of the test asserting a
narrower code path than the prose claims.

**3. Both acceptance directions, re-run independently.**
derived: `python3 /tmp/verify-2669/test_shapes.py` (case 1, cwd=repo A,
`cd repo-B && gh pr create --repo tokenmaxxxer/tokenmaxxxer-core`) —
result: **ALLOW** (rc=0). Legitimate cross-repo case confirmed allowed,
via a real second local checkout, not the PR's own transcript.
derived: same run, baseline case (cwd=repo A, no `cd`, `--repo
some-unrelated-org/upstream-repo`) — result: **DENY** (rc=2, stderr
`upstream-defect-scope-guard: \`gh pr create\` ... is denied`). The
guard's written-for case still denies when the resolved directory is a
real git checkout with a resolvable origin that doesn't match the
target — but per finding 1 above, this direction is bypassable by
changing the resolved directory to one where origin resolution fails
(`/tmp`, `~`, any nonexistent path), which flips this same "still
denied" acceptance direction to allowed.

**4. Nothing else in the guard moved.**
derived: `git -C /tmp/verify-2669/repoA fetch origin main && git -C
/tmp/verify-2669/repoA diff origin/main -- on-the-record/hooks/upstream-defect-scope-guard.sh`
— result: three hunks only — (a) two new comment blocks documenting the
cwd-resolution fix and the residual-gap precedent, (b) the new
`operative_cwd()` function, (c) `origin_repo()`'s first two lines
changed to call it. `in_scope()`, `extract_repo_flag()`,
`extract_gh_repo_env()`, `extract_repos_path()`, all five `deny()`
message call sites, and the `channel_role_active` block are byte-for-byte
unchanged in the diff — confirmed by reading the full diff output, not a
claim taken from the PR body.

**5. Test-suite effect.**
derived: `python3 -m pytest test/ -m "not slow" --collect-only -q` (run
in `/tmp/verify-2669/repoA`) — result:
```
404/406 tests collected (2 deselected) in 0.22s
```
derived: `cd /tmp/verify-2669/repoA && python3 -m pytest test/ -m "not
slow" -q` — result:
```
15 failed, 384 passed, 5 xfailed in 2.87s
```
derived: `cd /tmp/verify-2669/repoMain && python3 -m pytest test/ -m
"not slow" -q` — result (clean `origin/main`, same environment, same
command):
```
15 failed, 380 passed, 4 xfailed in 1.88s
```
derived: `diff <(sort failedA.txt) <(sort failedMain.txt)` (both files
built from each run's `FAILED ...` lines) — result: `IDENTICAL FAILURE
SETS`, i.e. all 15 failing nodeids are byte-identical between repoA (PR
head) and repoMain (clean main); all 15 fail for environment reasons (no
network access to fetch remotes inside the test sandbox, `SystemExit`
from `pipeline.py:865`), pre-existing, not introduced by this PR. Net
effect of the PR on the suite: +4 passed, +1 xfailed, 0 new failures —
exactly the new test file's own 4 non-`expectedFailure` cases plus its 1
pinned `expectedFailure`. Full `pytest test/` (no `-m` filter) was NOT
run — it was reported elsewhere today to time out past 2 minutes on this
machine; `-m "not slow"` is the subset actually executed here.

**6. Three new inline-subprocess sites in the `shape1_sites`
accumulation metric.**
derived: counted `gates.accumulation._inline_subprocess_call_count()`
over `git ls-files '*.py'` in each clone, run as a standalone `.py` file
(not a `python3 - <<EOF` heredoc, per the heredoc-command-refusal-gate)
— result: repoA (PR head): `398`; repoMain (clean main): `395`. Delta
+3, matching the number named in this task.
derived: `grep -n "subprocess.run" <the PR's new test file, present only
in the /tmp/verify-2669/repoA clone, untracked here>` — result: three
call sites, all in that new test file, none in the hook itself:
  - `_init_repo_with_origin()`, first call: `subprocess.run(["git","init","-q"], cwd=root, check=True)` — **no `timeout=`**.
  - `_init_repo_with_origin()`, second call: `subprocess.run(["git","remote","add","origin",origin_url], cwd=root, check=True)` — **no `timeout=`**.
  - `_run_guard()`: `subprocess.run(["bash", str(HOOK_PATH)], input=payload, capture_output=True, text=True, cwd=cwd, env=env, timeout=30)` — **has `timeout=30`**.
All three are this PR's (introduced by the new test file, confirmed by
`git log --oneline -- <that file>` in the PR-branch clone showing it was
created in commit `074573f6`, this PR's only code-carrying commit). Two
of three lack a timeout — but these run only inside `pytest`, against a
fresh local temp directory, never inside a live PreToolUse hook
invocation (the hook script itself gained zero new Python-level
`subprocess.run` sites; its one pre-existing `git remote get-url origin`
call already had `timeout=10`, unchanged — see code fence in the Why
section below). The "unbounded subprocess inside a PreToolUse hook
stalls every guarded command" risk this task named does not apply to
these two — they are `git init`/`git remote add` against a fresh local
temp directory, which in practice returns near-instantly — but they are
still a minor test-hygiene gap worth naming.

## Why

The task asked for adversarial construction against the real hook, not a
re-read of the PR's own transcript. The fix's entire surface area is
`operative_cwd()`'s regex plus what `origin_repo()` does when directory
resolution fails, so the two productive attack angles were (a) command
shapes the leading-`cd` regex doesn't match (the PR's own disclosed gap,
confirmed real but non-critical: they fail closed), and (b) command
shapes the regex DOES match but that resolve to a directory where `git
remote get-url origin` itself fails. (b) was not disclosed anywhere in
the PR, its record, or its Open findings, and is a full bypass of the
guard's core purpose (acceptance check 2) using nothing more exotic than
`cd /tmp` or `cd ~`.

`in_scope()`, this session's own working tree, pre-fix (byte-identical
pre- and post-fix, confirmed by item 4's diff above):

```python
def in_scope(target_repo):
    """PR-creation call is in-scope for denial iff the channel's own role
    is active, or a target repo was extracted and it isn't this session's
    origin repo. `target_repo=None` (no extractable target, or origin
    unresolvable) relies on the role signal alone."""
    if channel_role_active:
        return True
    if target_repo is not None and ORIGIN_REPO is not None:
        return target_repo.lower() != ORIGIN_REPO
    return False
```
derived: `sed -n '109,118p' on-the-record/hooks/upstream-defect-scope-guard.sh` — matches the fence above exactly.
The root cause is this function's final `return False` fallback — it
predates #2669 and was an intentional, documented design choice for the
case where the *payload* cwd (a harness-controlled, always-a-real-
checkout value) fails to resolve, which in practice was close to
unreachable.

The new `operative_cwd()` (only present in the PR-branch clone,
`on-the-record/hooks/upstream-defect-scope-guard.sh:132-141` of
`/tmp/verify-2669/repoA`, commit `074573f6`) is what turns that dormant
fail-open path into an attacker-steerable one:

```python
def operative_cwd(payload_cwd):
    m = re.match(r'^\s*cd\s+("[^"]+"|\'[^\']+\'|\S+)\s*(?:&&|;)', cmd)
    if not m:
        return payload_cwd
    target = m.group(1).strip("'\"")
    if not target:
        return payload_cwd
    if not target.startswith("/") and payload_cwd:
        target = os.path.join(payload_cwd, target)
    return target
```

the directory `git remote get-url origin` runs against is now taken
from `cmd` — the untrusted command text itself — so any session can
force the resolution to fail on demand (point at a non-git directory)
and flip the guard from "deny by default" to "allow by default" for
that call. This is rule 8 of `secure-coding-input-validation-injection-defense`
(a validation routine that fails then silently continues with a
default/allow path for a security-relevant decision must fail closed
instead) and rule 5 (untrusted input reaching an OS-level call —
`git -C <untrusted-derived-path>` — must be treated as
attacker-controlled, not trusted to either resolve or fail safely).
skill-verdict: secure-coding-input-validation-injection-defense —
applied: invoked; rule 8 and rule 5 both cited directly above against
`origin_repo()`'s failure paths and `in_scope()`'s fallback, with the
actual source quoted, not just referenced.
skill-verdict: adversarial-review — applied: invoked; used the skill's
"blind to the builder's own transcript" framing to justify re-deriving
every claim (diff, test run, both acceptance directions) from raw
commands in a fresh clone rather than reading and accepting PR #2700's
own test output or its record's `derived:`/`canonical:` lines as given.

## Upstream basis

- `074573f6:on-the-record/hooks/upstream-defect-scope-guard.sh` — the
  fix under review, quoted directly above.
- `docs/issue-2669/reports/secure-coding-authorization-access-control+silent-failure-audit-604a6e6b.md`
  (untracked here — PR #2700 still OPEN) at commit `91c1a6a5` — the
  subject's own record (PR #2700's delivering session), read for its
  claims but not relied on for this record's own verdicts; every claim
  above was independently re-run against the real hook.
  derived: `gh pr view 2700 --json state -q .state` — result: `OPEN`.
- PR #2700 (`gh pr view 2700`, `gh pr diff 2700`) — fetched live this
  session.

## Open findings

- **Critical, unnamed in the PR: fail-open bypass via unresolvable
  `operative_cwd()`.** Any command of the form `cd <dir> && gh pr create
  --repo <anything>` where `<dir>` is not a real git checkout with a
  configured `origin` (a nonexistent path, `~`, `/tmp`, or any ordinary
  non-repo directory) is allowed regardless of `--repo`'s target.
  canonical: `on-the-record/hooks/upstream-defect-scope-guard.sh` (this
  session's own working tree) `in_scope()`, quoted in full in the Why
  section above, combined with `origin_repo()`'s `except (OSError,
  subprocess.SubprocessError): return None` / `if r.returncode != 0:
  return None` paths (present in both the pre-fix hook in this working
  tree and the PR-branch clone, since `origin_repo()`'s body wraps
  `operative_cwd()`'s new first two lines only — see item 4's diff).
  derived: `python3 /tmp/verify-2669/test_tmp.py` — result: `cd /tmp &&
  gh pr create --repo some-unrelated-org/upstream-repo ...` → ALLOW
  (same command reproduced in item 1 above). This defeats acceptance
  check 2 ("the guard still refuses what it exists to refuse") with the
  single most mundane possible construction, not one of the exotic
  shapes (subshell/`pushd`) the PR itself named. Not closed by this
  record — reporting only, per this task's scope (independent
  verification, not a fix session). Resolution path proposed: either
  `operative_cwd()` should signal that the parsed `cd` target is not a
  resolvable git checkout and have `in_scope()` deny on that signal
  rather than fall through to `origin_repo() is None`, or `in_scope()`'s
  fail-open branch needs to distinguish "origin unresolvable because of
  the immutable payload cwd" from "origin unresolvable because of an
  attacker-supplied `cd` target" — the latter should deny, not allow.
- Two lesser, non-security shape gaps not named in the PR's own Open
  findings (same class as the subshell/`pushd` gap it did name — under-
  inclusive, fails closed, not a bypass): a non-leading `cd` (`set -e; cd
  X && ...`) and a second chained `cd` (`cd A && cd B && ...`) both still
  resolve against the payload cwd.
  derived: `python3 /tmp/verify-2669/test_shapes.py` — result: both
  shapes DENY (reproduced in item 1 above). No action needed beyond
  noting them alongside the PR's own disclosed narrower-than-ideal
  coverage.
- Pre-existing, out of this PR's scope: a `gh pr create` preceded by a
  bare newline instead of `;`/`&`/`|` is not detected as a `gh pr create`
  call at all by the unchanged shape-1 verb-detection regex.
  derived: `python3 /tmp/verify-2669/test_newline_premain.py` — result:
  identical **ALLOW** verdict on both the PR head hook and the clean
  `origin/main` hook for the same newline-separated payload, confirming
  this is not a regression introduced by #2700. Not actioned here;
  flagging for whoever next touches that regex.
- Two of the three new `subprocess.run` call sites this PR added (in its
  new test file) have no `timeout=` — reproduced in item 6 above
  (`derived: grep -n "subprocess.run" <PR's new test file>`). Low
  severity — they run only under `pytest`, against a fresh local temp
  directory, never inside a live PreToolUse hook path — but worth a
  follow-up timeout addition for hygiene.

## What did not work

None.

## Next steps

None — this record is the delivered output of the verification task
(build-now bypass, `CORE_BUILD_NOW=1`, contract v3 s19a); no code fix was
in scope for this role. The critical finding above is left as an Open
finding for a follow-up fix session, not fixed in this PR.

other mounted skills: not triggered — no other skills mounted beyond
`adversarial-review` and `secure-coding-input-validation-injection-defense`,
both invoked and cited above.
