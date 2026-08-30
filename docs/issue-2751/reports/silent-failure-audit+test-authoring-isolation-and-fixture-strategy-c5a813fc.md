---
issue: 2751
role: silent-failure-audit+test-authoring-isolation-and-fixture-strategy-c5a813fc
author: silent-failure-audit+test-authoring-isolation-and-fixture-strategy-c5a813fc
skills: silent-failure-audit (skill-repository(c05de12)), test-authoring-isolation-and-fixture-strategy (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: e1b35a53626da83b163e6fcd70455b32db897f92 (issue-2741, PR #2746)
    sha: e1b35a53626da83b163e6fcd70455b32db897f92
---

# issue-2751 — silent-failure-audit+test-authoring-isolation-and-fixture-strategy-c5a813fc record

## What was done

No code change. The target method named in the issue,
`test_approval_gate_sh_is_byte_identical`, is not present under that name
anywhere in the current tree:

```
$ grep -rn "byte_identical\|test_approval_gate_sh_is_byte_identical" test/test_auto_approval_shadow_wiring.py
(no output)
```
canonical: grep output above — the method does not exist in the file the issue names.

`git log --all -p --follow -- test/test_auto_approval_shadow_wiring.py`
showed it was renamed from `test_approval_gate_sh_is_byte_identical` to
`test_shadow_wiring_code_never_invokes_approval_gate_sh` in commit
`e1b35a53` (issue-2741, PR #2746, "retire the role persisted key —
rename to skill, forward-only"):

```
$ git show e1b35a53 -- test/test_auto_approval_shadow_wiring.py
[... diff ...]
-    def test_approval_gate_sh_is_byte_identical(self):
-        """diff assertion: this PR's approval-gate.sh (working tree) must
-        be byte-identical to origin/main's copy."""
-        hook_path = "on-the-record/hooks/approval-gate.sh"
-        r = subprocess.run(["git", "diff", "--exit-code", "origin/main", "HEAD", "--", hook_path], ...)
-        self.assertEqual(r.returncode, 0,
-                          f"{hook_path} changed against origin/main:\n{r.stdout}\n{r.stderr}")
+    def test_shadow_wiring_code_never_invokes_approval_gate_sh(self):
+        """... rather than a `git diff` against `origin/main` for that path,
+        which would also flip on any unrelated, legitimate edit to the hook
+        file's own content (issue #2741 renamed a persisted dict key inside
+        it, orthogonal to shadow wiring) ..."""
+        invocation_re = re.compile(r"(subprocess\.\w+|os\.system|os\.popen|open)\([^)]*approval-gate")
+        for mod_path in ("gates/ci.py", "gates/auto_approval_class.py"):
+            text = (REPO_ROOT / mod_path).read_text()
+            self.assertIsNone(invocation_re.search(text), ...)
```
canonical: `git show e1b35a53 -- test/test_auto_approval_shadow_wiring.py` output above.

```
$ git merge-base --is-ancestor e1b35a53 origin/main && echo yes
yes
$ git merge-base --is-ancestor e1b35a53 HEAD && echo yes
yes
$ git show -s --format='%H %ci' e1b35a53
e1b35a53626da83b163e6fcd70455b32db897f92 2026-08-30 03:23:31 +0900
```
canonical: the three commands and their output above — `e1b35a53` is an
ancestor of both `origin/main` and this branch's `HEAD`, and its
timestamp (2026-08-30 03:23:31 +0900) precedes this issue's own
"Observed live 2026-08-30" note, so the rename already existed on
`origin/main` before this session began.

The replacement test never shells out to git, and no other test in the
suite performs a `git diff ... origin/main` / raw-returncode check of any
kind:

```
$ grep -rn "returncode" test/*.py | grep -i "diff\|origin"
(no output)
$ grep -rn '"diff"' test/*.py
(no output)
```
derived: the two grep commands above, run from the repo root — zero
matches confirms no live test currently reproduces the collapsing bug
this issue describes.

Because the assertion this issue targets no longer exists, and was
retired deliberately (not accidentally) by `e1b35a53` for a reason
independent of this issue — see the `git show e1b35a53` excerpt above,
which cites #2741's own content edit to `approval-gate.sh` as the
trigger — there is no byte-identical git-diff assertion left in the tree
to patch.

Demonstrated, live and side by side, that git's own exit codes still give
the clean separation the issue describes (no-diff vs diff-found vs
git-level error), independent of any Python wrapper:

```
=== Scenario A: clone with no resolvable origin/main ===
$ git clone -q --depth 1 --single-branch --branch <this-branch> <repo> /tmp/a
$ cd /tmp/a && git diff --exit-code origin/main HEAD -- on-the-record/hooks/approval-gate.sh
fatal: bad revision 'origin/main'
$ echo $?
128

=== Scenario B: clone where the file genuinely differs (committed ahead) ===
$ git clone -q <repo> /tmp/b && cd /tmp/b && git checkout -q -b scratch-diff
$ echo "# scratch content-diff marker" >> on-the-record/hooks/approval-gate.sh
$ git commit -qam "scratch: content diff marker"
$ git diff --exit-code origin/main HEAD -- on-the-record/hooks/approval-gate.sh
diff --git a/on-the-record/hooks/approval-gate.sh b/on-the-record/hooks/approval-gate.sh
+# scratch content-diff marker
$ echo $?
1
```
derived: the two clone/diff sessions above, run against this branch —
exit code 128 is a git-level failure with no diff printed ("bad
revision"), exit code 1 is a real printed diff hunk; the two are visibly
distinguishable at the git layer, exactly as the issue's own premise
states.

Could not exercise the issue's third acceptance check ("the frozen
assertion still fires on a real change to approval-gate.sh") against a
live pytest run of the *named* test, because that test no longer exists
(shown above). The replacement test
(`test_shadow_wiring_code_never_invokes_approval_gate_sh`) checks a
different property — no invocation/open call naming the hook inside
`gates/ci.py` / `gates/auto_approval_class.py`'s own source — and does
not fire on edits to `approval-gate.sh` itself.
canonical: `test_shadow_wiring_code_never_invokes_approval_gate_sh`'s own
body (quoted in the `git show e1b35a53` excerpt above) — it reads
`gates/ci.py` and `gates/auto_approval_class.py`, never
`on-the-record/hooks/approval-gate.sh`.

## Why

The obvious repair — recreate `test_approval_gate_sh_is_byte_identical`
with a fixed three-branch exit-code handler (no-diff / diff-found /
git-error, each getting its own message) — was rejected. That test's
literal freeze (any diff against `origin/main` for that one path, full
stop) is exactly what `e1b35a53` retired, for a reason independent of
this issue: per the `git show e1b35a53` excerpt in "What was done", it
flips on any legitimate future edit to the hook's content, not only
circular-trust violations. The prior record
`docs/issue-2600/reports/silent-failure-audit+test-authoring-isolation-and-fixture-strategy-d44249ff.md`
had already flagged this same test as forcing a choice between "freeze
is absolute, bytes included" and "freeze is about behavior, not bytes",
and explicitly deferred widening or retiring it to "a future slice that
can widen or retire this test as its own explicitly-scoped,
explicitly-approved change" (quoted verbatim from that record's own
"Why" section).

Rebuilding the byte-identical shape just to patch its exit-code handling
would silently undo `e1b35a53`'s already-merged decision as a side
effect of this unrelated issue, and would also mean writing brand-new
code today and then presenting this issue's own acceptance checks
running against that brand-new code as if they verified the artifact the
issue was filed about — which they would not.
canonical: the `git show -s --format='%H %ci' e1b35a53` timestamp quoted
in "What was done" (2026-08-30 03:23:31 +0900) precedes the issue's own
"Observed live 2026-08-30" note — the named target had already been
removed before the issue was filed.

## What did not work

Initial assumption, before reading the file, was that the target test
existed as described and only needed its exit-code branch fixed.
canonical: the grep in "What was done" returning no match redirected the
work to `git log --all -p --follow` on that file, which located
`e1b35a53` as the actual cause. No code was written and then reverted;
the pivot happened before any edit was made.

## Upstream basis

- `e1b35a53626da83b163e6fcd70455b32db897f92` (issue-2741, PR #2746,
  already on `origin/main`): removed `test_approval_gate_sh_is_byte_identical`
  and replaced it with a non-git-shelling static check, mooting this
  issue's named target.
- `docs/issue-2600/reports/silent-failure-audit+test-authoring-isolation-and-fixture-strategy-d44249ff.md`:
  prior record on the same test, already anticipating that
  retiring/widening it should be its own explicit, approved change.

## Open findings

- For the maintainer to decide, not this session: whether #1739's
  circular-trust guard should get an explicit git-diff-based freeze
  rebuilt (this time handling git's error exit code as its own branch,
  per this issue's original ask) now that `e1b35a53` removed the only one
  that existed, or whether the invocation-detection replacement in
  `e1b35a53` is considered sufficient going forward. Recommend closing
  #2751 as superseded by `e1b35a53` unless the team wants that explicit
  freeze rebuilt as its own scoped, approved follow-up.
- Repo-wide sweep for other tests that shell out to `git` and could
  collapse the diff-found/git-error distinction: out of scope per the
  issue's own non-goals. None found incidentally while investigating
  this one:
  ```
  $ grep -rn "returncode" test/*.py | grep -i "diff\|origin"
  (no output)
  ```
  derived: command and output above (same command cited in "What was done").

## Invariants checked

- No return of the retired `role` persisted-key axis in any reshaped
  form (issue #2741's rename):
  ```
  $ grep -rn '"role"\s*:' gates/ci.py gates/auto_approval_class.py on-the-record/hooks/approval-gate.sh | grep -v "skill"
  (no output)
  ```
  derived: command and output above.
- No new bug — failing-test set vs `origin/main`, compared as sets of
  names, not counts:
  ```
  $ python3 -m pytest test/ -q 2>&1 | grep "^FAILED" | sort > /tmp/branch_failed.txt
  $ git worktree add -q /tmp/otr-main-check origin/main
  $ (cd /tmp/otr-main-check && python3 -m pytest test/ -q 2>&1 | grep "^FAILED" | sort) > /tmp/main_failed.txt
  $ diff /tmp/main_failed.txt /tmp/branch_failed.txt && echo IDENTICAL
  IDENTICAL
  ```
  derived: command and output above — both sides list the same named
  failing tests, confirmed via `diff` (not a count comparison).
- No overhead increase: no production or test file was modified this
  session — `git status --porcelain` before opening the PR shows only
  `docs/issue-2751/` as untracked, no code-path changes to run.
- Monitor/watch machinery unbroken and not quieter:
  ```
  $ python3 -m pytest test/test_watchdog_heartbeat_noise.py -q
  6 passed in 0.87s
  ```
  derived: command and output above.

## Next steps

None — `loop_state: landed`. Recommend the maintainer read "Open
findings" above and decide whether to close #2751 as superseded or
request a follow-up that rebuilds an explicit byte-identical freeze with
correct git exit-code handling.

## Skill verdicts

- skill-verdict: silent-failure-audit — not-applicable: the error-handling
  code this skill audits (the git-shelling assertion) no longer exists in
  the tree to audit; see "What was done".
- skill-verdict: test-authoring-isolation-and-fixture-strategy —
  not-applicable: no test was authored or re-scoped this session; the
  target test was already removed by an unrelated, prior commit.
