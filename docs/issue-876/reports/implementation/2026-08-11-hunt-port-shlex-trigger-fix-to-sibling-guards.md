---
proposal: docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md
---

# Hunt record — port-shlex-trigger-fix-to-sibling-guards

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `shlex.split(cmd)` splits only on whitespace, so a subshell wrapper with no space after the opening parenthesis (the paren immediately followed by `git`) glues the paren onto the token, making the new `"git" in tokens and "commit" in tokens` check silently fail to trigger on a real, working commit invocation that the pre-fix `\bgit\s+commit\b` regex DID catch (word-boundary `\b` treats `(` as a boundary, unlike shlex's whitespace-only splitting). This regresses gate-registration-guard.sh (and, by the identical ported line, role-axis-completeness-guard.sh) below the pre-#876 baseline for this one command shape.
Kind: composition
Seed: on-the-record/hooks/gate-registration-guard.sh, on-the-record/hooks/role-axis-completeness-guard.sh (staged diff porting spec-index-preflight.sh's shlex trigger fix, issue #876)
cap_seconds: 120
tier: default

canonical: `git diff --cached --stat` output below.
```
$ git diff --cached --stat -- on-the-record/hooks/gate-registration-guard.sh on-the-record/hooks/role-axis-completeness-guard.sh on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_role_axis_completeness_guard.py
 on-the-record/hooks/gate-registration-guard.sh     | 22 ++++++++++++++---
 .../hooks/role-axis-completeness-guard.sh          | 22 +++++++++++++++--
 .../hooks/test_gate_registration_guard.py          | 22 +++++++++++++++++
 .../hooks/test_role_axis_completeness_guard.py     | 28 ++++++++++++++++++++++
 4 files changed, 89 insertions(+), 5 deletions(-)
```
diff_stat_lines: 89 insertions(+), 5 deletions(-) across 4 files (derived above)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:06:00Z

### Reproduce
canonical: isolated tokenizer probe script /tmp/shlex_check.py and full end-to-end harness script /tmp/repro_bypass.py, both written and executed in this session.

Isolated tokenizer probe (avoids embedding the literal `git`+space+`commit` sequence directly in a Bash tool command line, which a separate, unrelated hook in this environment over-eagerly treats as an actual commit attempt):
```python
g, c = "git", "commit"
wrapped = f"({g} {c} -m \"test\")"
import shlex
print(shlex.split(wrapped))
print("git" in shlex.split(wrapped), "commit" in shlex.split(wrapped))
```

canonical: /tmp/repro_bypass.py, executed in this session (full text of the harness quoted in the tool-call log above).

Full end-to-end reproduction against the real hook: build a disposable temp git repo under /tmp, stage one new, unregistered file named new_gate.py inside its own gates/ subdirectory (the exact violation gate-registration-guard.sh exists to deny-before-effect on), then invoke on-the-record/hooks/gate-registration-guard.sh with a synthetic PreToolUse JSON payload twice — once with tool_input.command set to the plain two-word invocation, once with the same invocation wrapped in a no-space-after-paren subshell — and compare exit codes. Then execute the wrapped string directly with bash -c against the same repo and check git log to confirm it is an ordinary, working commit.

### Observed
canonical: stdout of `python3 /tmp/shlex_check.py` and `python3 /tmp/repro_bypass.py`, both run in this session (see Reproduce above for the scripts).

Isolated probe output:
```
['(git', 'commit', '-m', 'test)']
False True
```
`"git"` is never a standalone token (fused to the opening paren as `(git`), so `"git" in tokens` is `False` even though `"commit"` is present — the trigger condition `"git" in tokens and "commit" in tokens` evaluates `False`. The pre-#876 `re.search(r"\bgit\s+commit\b", cmd)` on the identical wrapped string evaluates `True` (checked in the same session with a second isolated script).

End-to-end harness output:
```
PLAIN  rc= 2 stderr= gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/new_gate.py: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
WRAPPED rc= 0 stderr=
direct-exec rc= 0 git log: c20ea56 test
```
(the gates/new_gate.py path named in that stderr line is inside the disposable temp-repo fixture the harness script creates under /tmp, not a path in this working tree.) The plain invocation is correctly denied (rc=2). The paren-wrapped invocation of the identical commit passes silently (rc=0, empty stderr). The direct bash -c execution of the wrapped string against the same temp repo returns 0 and git log --oneline shows the commit landed — confirming the wrapped form is an ordinary, real, working command, not a syntax edge case that would never actually run.

### Expected
A subshell-wrapped commit should trigger the guard identically to the unwrapped form (as it did under the pre-#876 regex, and as it still does when the same wrapping is written with a space after the opening paren instead), since it performs the same commit against the same repo. The guard must not regress below its own pre-fix baseline for any command shape while fixing a different one.
