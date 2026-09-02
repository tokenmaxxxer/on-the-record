---
issue: 3228
role: adversarial-review+silent-failure-audit+test-depth-audit-00aea41d
author: adversarial-review+silent-failure-audit+test-depth-audit-00aea41d
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #3233, sha e92623b5e76dc7cb4f16c6023b9acb0461a649d1 (scripts/lint/silent_failure.py, tests/test_issue_3228_silent_failure_lint.py, scripts/lint/fixtures/silent_failure/**)
loop_state: complete
type: review
breaking: false
verdict: fail
upstream:
  - path: e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md
    sha: e92623b5e76dc7cb4f16c6023b9acb0461a649d1
  - path: e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py
    sha: e92623b5e76dc7cb4f16c6023b9acb0461a649d1
---

# issue-3228 — adversarial-review+silent-failure-audit+test-depth-audit record

## What was done

Independent verification of PR #3233 (`gh pr view 3233 --json headRefOid`
— canonical: head `e92623b5e76dc7cb4f16c6023b9acb0461a649d1`, base
`main`). Fetched the PR branch into a separate worktree (`/tmp/pr3233-wt`
via `git fetch` + `git worktree add`, never the PR's own checkout) and,
without editing, merging, or commenting on it, ran every acceptance
check myself, ran the lint against every individual before/after
fixture, ran it against the whole repository, attacked it with five
hostile inputs, and cross-checked the two "reconstructed from comments"
fixture claims against real git history not cited by
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md`.

acceptance: `python3 -m pytest e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py -q` (run in `/tmp/pr3233-wt`) — result:
```
11 passed in 0.87s
```
acceptance: `python3 scripts/lint/silent_failure.py --self-check` (run in `/tmp/pr3233-wt`) — result:
```
PASS: history_before/site3_git_failure_conflation.py: pre-repair shape is flagged
PASS: history_before/site4_missing_timeout.py: pre-repair shape is flagged
PASS: history_before/site1_2_consumer_preconditions.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site5_delegation_state_wildcard.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site6_forgeable_evidence.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_before/site7_amendment_channel_fixture.py: outside this mechanism's documented scope (not a subprocess-observation defect)
PASS: history_after/site3_git_failure_conflation.py: repaired shape stays quiet
PASS: history_after/site4_missing_timeout.py: repaired shape stays quiet
PASS: history_after/site1_2_consumer_preconditions.py: repaired shape stays quiet
PASS: history_after/site5_delegation_state_wildcard.py: repaired shape stays quiet
PASS: history_after/site6_forgeable_evidence.py: repaired shape stays quiet
PASS: history_after/site7_amendment_channel_fixture.py: repaired shape stays quiet
PASS: a nonexistent/unreadable file reports an error, not a silent skip
PASS: a permission-denied file reports an error, not a silent skip
PASS: a file with a syntax error reports an error, not a silent skip
PASS: a target with zero subprocess call sites is distinguished from a clean pass
PASS: scanning that same zero-call-site target end-to-end exits nonzero
```
Exit code 0. derived: `grep -c FAIL` on this transcript = 0; `grep -c PASS` = 17. Both acceptance checks named in the issue pass.

acceptance: `python3 -m pytest tests/ -q -m "not slow"` (run in
`/tmp/pr3233-wt`) — result:
```
551 passed, 2 warnings in 25.68s
```
matching the PR description's own claimed count (540 baseline + 11 new = 551).

**Verdict up front, canonical: the six investigations below (sections
1-6), each independently run this session.** The two required acceptance
checks pass and the catch-rate claim in the upstream record is honest
and independently reproducible (section 1), but the deliverable does not
do what issue #3228 actually asked for: nothing this PR wires into the
repo's automated checks ever runs `scripts/lint/silent_failure.py`
against a new or changed source file (section 5) — every automated
invocation only re-scans the lint's own bundled fixtures plus one
hardcoded regression target (two named functions in one file). A
brand-new subprocess call site with a missing timeout, written anywhere
else in the repo tomorrow, triggers nothing.

### 1. Catch rate — grade: Present

Ran the lint on each of the twelve fixture files individually (not only
through `--self-check`, which calls `scan_file` directly and proves less
about the CLI path). derived: `python3 scripts/lint/silent_failure.py <each fixture path>`, one invocation per file, this session:
```
history_before/site3_git_failure_conflation.py  -> 2 findings (SF001, SF003), exit 1
history_before/site4_missing_timeout.py         -> 2 findings (SF001 x2), exit 1
history_before/site1_2_consumer_preconditions.py -> "no subprocess call sites", exit 1
history_before/site5_delegation_state_wildcard.py -> "no subprocess call sites", exit 1
history_before/site6_forgeable_evidence.py       -> "no subprocess call sites", exit 1
history_before/site7_amendment_channel_fixture.py -> "no subprocess call sites", exit 1
history_after/site3_git_failure_conflation.py   -> OK: 1 subprocess call site(s), no findings, exit 0
history_after/site4_missing_timeout.py          -> OK: 2 subprocess call site(s), no findings, exit 0
history_after/site1_2_consumer_preconditions.py -> "no subprocess call sites", exit 1
history_after/site5_delegation_state_wildcard.py -> "no subprocess call sites", exit 1
history_after/site6_forgeable_evidence.py       -> "no subprocess call sites", exit 1
history_after/site7_amendment_channel_fixture.py -> "no subprocess call sites", exit 1
```
Count derived directly from the table above: 2 of the 7 named defects
(sites 3 and 4) are caught before repair and quiet after; the remaining
5 (grouped into 4 fixtures because sites 1 and 2 share one function) are
never observed at all. Confirmed by grep this session:
```
$ grep -L '^import subprocess' scripts/lint/fixtures/silent_failure/history_before/site1_2_consumer_preconditions.py scripts/lint/fixtures/silent_failure/history_before/site5_delegation_state_wildcard.py scripts/lint/fixtures/silent_failure/history_before/site6_forgeable_evidence.py scripts/lint/fixtures/silent_failure/history_before/site7_amendment_channel_fixture.py
scripts/lint/fixtures/silent_failure/history_before/site1_2_consumer_preconditions.py
scripts/lint/fixtures/silent_failure/history_before/site5_delegation_state_wildcard.py
scripts/lint/fixtures/silent_failure/history_before/site6_forgeable_evidence.py
scripts/lint/fixtures/silent_failure/history_before/site7_amendment_channel_fixture.py
```
all 4 listed, none imports `subprocess`. canonical:
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md`'s
own "Verdict on catch rate" section states this identical split; the
upstream record does not round it up or bury it — this is the one place
the PR is fully honest about a materially low number, and it survives
independent reproduction.

### 2. Fixture faithfulness — grade: mixed (Incorrect / Present / Surface)

Two fixtures (site 3, site 4) are real pre-repair code recovered via
`git show fb0bb0d3:scripts/issue-3127/verify_preregistration.py` — not
in dispute. checked: `git log --oneline -- scripts/preflight/consumer_preconditions.py delegation_state.py on-the-record/hooks/amendment_channel.py`
(run this session, branch-scoped, matching what the upstream record ran)
— result: each shows only a single post-repair commit on this branch's
own ancestry (`da899f2a`/`0f6cb358` for the first, `b6f5eb05` for the
second, `638620e4` for the third) — confirms independently that no
separate pre-fix commit exists on `main` for any of the three, as the
upstream record claims.

**The consumer-preconditions and delegation-state reconstructions — grade: Present.** canonical: the real repaired
file's own inline comments at sha
`f722841fcf28c0e299713af2a8e69015a6eaf673`
(`scripts/preflight/consumer_preconditions.py:210-227`,
`delegation_state.py:584-620`, both read via `git show
f722841fcf28c0e299713af2a8e69015a6eaf673:<path>` this session) narrate
the statvfs-exception-returns-`True` shape, the `if free_inodes and ...`
falsy-zero shape, and the bare-`fnmatch`-against-a-chained-command
shape, in the same words the reconstructed
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/history_before/site1_2_consumer_preconditions.py`
and
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/history_before/site5_delegation_state_wildcard.py`
implement. Faithful.

**Site 7 (`amendment_channel.py`) — grade: Incorrect.** This is the one
place the upstream record's git-history claim, though true on its face,
hides a richer trail on an abandoned sibling branch that the record
never ran a wider search to find, and the reconstruction built from the
merged commit's comments implements the wrong bug. derived: `git log --all --oneline --follow -- on-the-record/hooks/amendment_channel.py`
(a command the upstream record never ran — it only ran the
branch-scoped `git log --oneline`), this session — result:
```
638620e4	refs/heads/issue-3228/... issue-3129: local-file amendment channel for spawned worker mid-flight corrections (#3137)
f699f5c6	refs/remotes/origin/issue-3129/implementation-blueprint+test-derivation+silent-failure-audit-5d5e5a08 issue-3129: round-7 fix -- real Bash tool_response shape + fixture blind spot
7fa8906b	... issue-3129: repair round 5 -- launcher-owned trust root, positive success check
```
(plus five more earlier rounds, all on the same sibling ref). checked:
`git merge-base --is-ancestor f699f5c6 origin/main`, this session —
result: exit nonzero, "not an ancestor" — confirms these extra commits
sit on `origin/issue-3129/implementation-blueprint+test-derivation+silent-failure-audit-5d5e5a08`,
a squash-merge-superseded branch, not on `main`'s own history.

Issue #3228's own text for this defect: "a success check that never
matched the real payload shape passed all seventy-nine of its tests,
because every fixture was hand-written in a shape the real system never
produces." derived: `git show -s --format=%B f699f5c6`, this session —
result contains the identical figure verbatim:
```
PR #3205 found the round-5 positive success check ... never matches a
real Claude Code Bash tool_response ... 79 tests and both gate probes
passed against code that could not match a real payload
```
and the merged, current file's own module docstring at
`on-the-record/hooks/amendment_channel.py:213-241` (read this session,
exists on `main`) repeats that same figure in the same words.

canonical: the real bug this describes, confirmed by `git show
f699f5c6~1:on-the-record/hooks/amendment_channel.py`, read this session,
lines 705-712:
```
    text = hook_input.tool_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.fullmatch(text.strip())
    if not m:
        return None
    owner, repo, issue = m.group(1), m.group(2), m.group(3)
    return _IssueUrl("%s/%s" % (owner, repo), issue)
```
is that the pre-round-7 code already used `.fullmatch()` (from an
earlier round-5 fix) but read the response text through
`hook_input.tool_response_text()`, which `json.dumps()`-wraps a real
dict `tool_response` — so `fullmatch` against a bare URL pattern NEVER
matches a real payload, a total false negative. The PR's reconstructed
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/history_before/site7_amendment_channel_fixture.py`
instead implements a *different, already-fixed* bug — `.search()` (not
`.fullmatch()`) matching a URL-shaped substring inside a failed edit's
own error text, a false positive, canonical: that fixture file's own
`issue_url_from_response()`, read this session:
```
def issue_url_from_response(tool_response: object):
    text = _old_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.search(text)
```
That `.search()`-vs-`.fullmatch()` bug is real, but it belongs to round
5 (a false positive), fixed one round before the "79 tests, fixture
never matched a real payload" defect issue #3228 is actually citing (a
false negative caused by JSON-wrapping, round 7). The reconstruction
borrows round 7's narrative but implements round 5's mechanism. Since
this fixture contains no subprocess call either way, the mistake does
not change the catch-rate count in section 1 — but the PR's
proof-against-history claim for this specific site does not actually
reconstruct the defect issue #3228 named, and the upstream record's
"no separate pre-fix commit exists" statement is true only because it
never widened its own search to notice the richer trail existed to
check against.

**Site 6 (`verify_manipulation.py`) — grade: Surface.** canonical:
`scripts/consumer-path/verify_manipulation.py`'s current module
docstring, lines 17-26 (read this session) only describes the
*replacement* design in prose ("issue #3127's PR #3180 already
demonstrated this live for the previous design's own signal") with no
code for the forgeable design itself in this checkout. The reconstructed
`skill_was_invoked()` regex-matching a `Skill: <name>` line the spawned
process's own log could print is a reasonable inference from that prose,
but there is no prior commit or PR #3180 artifact in this checkout to
compare it against — Surface (unverifiable either way from what exists
in git history here), not Present, and not Incorrect.

### 3. Attacking the lint's own reliability — grade: Incorrect

The bundled self-check (transcript in "What was done" above) already
covers an unreadable/nonexistent file, a `chmod 000` file (via
`scan_file` directly), and a syntax-error file, and this session
reproduced all three independently with the same result (an `error` is
set, never a silent pass). Two attacks the self-check does NOT cover
both reproduce the exact silent-failure shape issue #3228 exists to
eliminate.

**Null byte — crashes uncaught, losing every other finding in the same
invocation.** canonical:
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py:350-362`,
`scan_file()` only catches `OSError` (unreadable) and `SyntaxError`
(parse); `ast.parse()` raises a bare `ValueError` on a null byte, caught
nowhere. derived: created `/tmp/sf_attack/crashtest/` with two files —
one genuinely missing a timeout
(`ok_should_be_flagged.py`, `subprocess.run(["ls"])` with no
`timeout=`) and one containing a null byte
(`nullbyte.py`) — then ran `python3 scripts/lint/silent_failure.py crashtest`, this session — result:
```
Traceback (most recent call last):
  File "scripts/lint/silent_failure.py", line 527, in <module>
    sys.exit(main())
  File "scripts/lint/silent_failure.py", line 360, in scan_file
    tree = ast.parse(text, filename=str(path))
ValueError: source code string cannot contain null bytes
```
exit code 1. The process aborts on the null-byte file with an unhandled
traceback before `ok_should_be_flagged.py`'s real SF001 finding is ever
printed — that finding is lost, not because it was silently skipped, but
because the whole scan died mid-directory. The exit code (1, Python's
default uncaught-exception behavior) is nonzero, so the literal PR
acceptance wording ("must not report a clean pass") is not technically
violated, but the documented promise in
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py:49-54`'s
own docstring — "prints every file this scan could not read or parse
(never silently skipped)" — is: this file is never named in any
structured `FileResult.error`, and any other file queued after it in the
same invocation loses its findings entirely.

**Permission-denied directory — silently indistinguishable from an
empty one.** canonical:
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py:372-381`,
`_expand_targets()` calls `Path(p).rglob("*.py")` for any directory
target. derived: created `/tmp/sf_attack/noperm/x.py` (contains
`import subprocess`), then `chmod 000 noperm`, this session — result:
```
$ python3 -c "from pathlib import Path; print(list(Path('noperm').rglob('*.py')))"
[]
```
`pathlib.Path.rglob` on this Python version (`python3 --version` this
session reported 3.10) silently swallows the `PermissionError` from
`os.scandir` and yields zero results rather than raising. Running the
lint's own CLI against the same still-`chmod 000` directory, this
session:
```
$ python3 scripts/lint/silent_failure.py noperm
no .py files found under the given target(s)
```
exit 1 — identical wording and identical exit code to the genuinely
empty, fully-readable case
(`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/fixtures/silent_failure/no_subprocess/`,
canonical: exercised in the self-check transcript above, same message).
This is a literal instance of the class issue #3228 names — "a check
that could not observe something reported the answer it would have
given if it had observed nothing" — reproduced inside the tool built to
catch it. canonical: read
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`
in full this session — neither `run_self_check()` nor any of its test
functions exercises `_expand_targets`/`rglob` against a
permission-denied directory; only `scan_file` is attacked directly with
`chmod 000` on a single *file*, which bypasses this code path.

A fifth attack, a symlink loop
(`/tmp/sf_attack/loopdir/sub/loopback -> ../sub`), produced no finding:
derived: `timeout 5 python3 -c "from pathlib import Path; print(list(Path('loopdir').rglob('*.py')))"`,
this session — result: returned the one real file with no hang and no
duplicate entries — `pathlib.Path.rglob` on Python 3.10 does not follow
directory symlinks for wildcard recursion. Not a defect.

### 4. Precision at repo scale — grade: Surface

derived: `python3 scripts/lint/silent_failure.py .` over the whole
repository (PR branch checked out in `/tmp/pr3233-wt`), this session —
piped to file, then:
```
$ grep -c '\[SF00' /tmp/full_scan.txt
594
$ grep -oE '\[SF00[0-9]\]' /tmp/full_scan.txt | sort | uniq -c
    450 [SF001]
     85 [SF002]
     59 [SF003]
$ grep -oE '^[^:]+:[0-9]+: \[SF00[12]\]' /tmp/full_scan.txt | sort -u | wc -l
535
```
Against
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md`'s
own cited total of 617 subprocess call sites across 138 files (its own
`git ls-files` derivation): 535/617 = 86.7% of every existing call site
in the repo would be flagged if this lint were pointed at the repo
today.

Spot-checked three flagged sites by reading the surrounding code this
session, canonical: `watchdog.py:225-234`:
```
    st = subprocess.run(["git", "-C", work, "status", "--porcelain", "-uall"],
                        capture_output=True, text=True)
    if st.returncode != 0:
        return "워크스페이스 상태 확인 실패(git status)"
    lines = [l for l in st.stdout.splitlines() if l.strip()]
```
a real `git status` call with no `timeout=`, whose `.returncode` *is*
checked (SF001 alone is correct here, not SF002 — matches the tool's own
finding). canonical: `tests/test_orphan_sweep.py:210-217`:
```
    subprocess.run(["git", "init", "-q"], cwd=w, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"],
                    cwd=w, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=w, check=True)
```
test-fixture git calls with `check=True` but still no `timeout=` (SF001
correctly fires regardless of `check=True`, which the tool's own logic
only uses to silence SF002). canonical: `watchdog.py:2036-2047`:
```
        result = subprocess.run(cmd, cwd=str(root), capture_output=True,
                                 text=True, timeout=contract.budget_seconds)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        ...
    failing_ids = _sp._standing_red_parse_failed_ids(output)
```
`result.returncode` is never checked before `output` (combining stdout
and stderr) is parsed for test-failure IDs, regardless of whether the
underlying command actually exited zero — precisely the shape issue
#3228 names. No false positive found in this sample of three sites.

So the mechanism's *precision* is good on this sample — it does not
spray obvious noise — but its magnitude at repo scale (the 86.7% figure
above) is never computed or stated anywhere in the upstream record.
canonical: that record's own "Deliberately not turned on: a full-repo
scan gate" paragraph gives the right conclusion (this cannot be turned
into a blocking gate over the existing codebase without either mass
remediation or a grandfather/baseline mechanism) but reaches it by
reasoning from one file's precision-gap incident, not from ever running
the scan it is reasoning about. The adoption-path statement exists in
principle but is not backed by the number that would justify it —
Surface, not Present.

### 5. Wiring / "unwritable at authoring time" — grade: Incorrect (the deciding finding)

Enumerated every place `scripts/lint/silent_failure.py` is invoked
automatically, per the upstream record's own "Wiring" section
(canonical: that section, read this session):

1. `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`,
   auto-discovered by pytest. derived: a `grep -c "^def test_"` count
   over that file (run in `/tmp/pr3233-wt`), this session, matching the
   "11 passed" count in the acceptance transcript above. Read all of
   them this session: every one calls either `sf.scan_file()` /
   `sf.scan_targets()` against paths under
   `scripts/lint/fixtures/silent_failure/`, or the CLI's `--self-check`,
   or (`test_real_repaired_functions_stay_quiet`, the sole exception) a
   hardcoded regression target scoped to exactly two named functions in
   one file (`scripts/issue-3127/verify_preregistration.py`,
   canonical: `_REGRESSION_FUNCTIONS = ("_run_git",
   "_first_commit_for_path")` in that test file, read this session).
2. `gates/check_runner.py` re-running the issue's own two acceptance
   `check:` lines verbatim — both lines are `pytest
   e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`
   and `silent_failure.py --self-check`, i.e. the same fixture-only
   surface as item 1 above, not a second, independent surface.
3. `on-the-record/hooks/lint-test-on-edit.sh`, cited by the upstream
   record as "a fourth 'runs automatically' surface worth naming since
   the issue's whole ask is authoring-time enforcement." Read the hook
   in full this session (it exists on `main`, not PR-only): it runs
   `python3 -m py_compile <file>` (syntax only) plus an
   import-graph-selected subset of existing tests on every edited `.py`
   file. derived:
   `grep -n "silent_failure" on-the-record/hooks/lint-test-on-edit.sh`,
   this session — result:
```
10:# (docs/issue-2326/reports/silent-failure-audit+diagnose-first-0f11c1bf.md)
108:# it: the durable-evidence fix above is what closes the silent-failure
```
   both incidental citations of an unrelated issue's own past record and
   a generic phrase; the hook never invokes
   `scripts/lint/silent_failure.py`. Citing it as an authoring-time
   enforcement surface for this mechanism is incorrect — `py_compile`
   cannot detect a missing `timeout=` or an unchecked `.returncode`,
   which are both syntactically valid Python.

All three cited "runs automatically" surfaces resolve to exactly one
real thing: a regression test that guards the lint's own bundled
fixtures plus one two-function slice of one already-repaired file
against reintroduction. None of them ever calls
`scripts/lint/silent_failure.py` against a file an author writes
tomorrow — not on commit, not on PR, not on edit, anywhere. Issue
#3228's own text: "a mechanism that catches the class at authoring time,
in this repository's own tooling, so a new site cannot be written the
same way without something saying so." A new subprocess call site with a
missing timeout, written anywhere in this repo outside those two named
functions, today, triggers none of the three wired surfaces above. The
class remains exactly as writable as before this PR for every site
except the two it happens to have hardcoded a regression guard for. This
is a correctly-functioning, well-tested static-analysis *script* that is
not wired as an enforcement *mechanism* for new code — the PR's own
description conflates the two ("wires its self-check into the repo's
existing automatically-run test suite" is true, and is a different claim
from "wires enforcement of new call sites into the repo").

### 6. Scope honesty about the other defects — grade: Present

Issue #3228's own text names three of the seven ("the falsy zero, the
forgeable evidence, the fixture that never matched the real payload") as
illustrative examples of defects that "do not look like subprocess call
sites at all"; the per-fixture scan in section 1 above (grep output
quoted there) shows the actual set is larger: sites 1, 2, 5, 6, 7 (the
statvfs-exception, the falsy-zero, the fnmatch wildcard chain, the
forgeable evidence, and the fixture-realism defects) — none of their
`history_before` fixtures contains `import subprocess`, confirmed by the
same grep quoted in section 1. canonical:
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md`'s
own weighing table names candidate (c), the tri-state convention, as the
only one of the four weighed candidates that would have caught every
named defect, and states plainly this PR did not build that one. That is
an honest scope statement, not an overclaim, independent of the wiring
defect in section 5.

## Why

The method above follows the three mounted skills directly rather than
re-trusting the PR's own self-reported numbers: silent-failure-audit's
design rule (every finding needs a cited catch site and a cited absence
of downstream effect) is why sections 3 and 5 above trace to the
specific uncaught exception type and the specific hook file contents,
canonical: `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:scripts/lint/silent_failure.py:350-362`
and `on-the-record/hooks/lint-test-on-edit.sh`'s own grep output quoted
in section 5, rather than stopping at "the self-check passes";
adversarial-review's blindness-to-intent framing is why the
fixture-faithfulness check in section 2 went to git history the upstream
record itself did not run (`--all --follow`) rather than re-verifying
only the command the record already ran; test-depth-audit's
execution-vs-verification distinction produced the test classification
under "Open findings" below.

## Upstream basis

- PR #3233, head `e92623b5e76dc7cb4f16c6023b9acb0461a649d1`
  (canonical: `gh pr view 3233 --json headRefOid`, this session), base
  `main`.
- `e92623b5e76dc7cb4f16c6023b9acb0461a649d1:docs/issue-3228/reports/silent-failure-audit+implementation-blueprint+test-derivation-ed55a103.md`
  — the record whose claims this review checks.
- `scripts/issue-3127/verify_preregistration.py` at commit `fb0bb0d3`
  (pre-repair, real) and at `f722841fcf28c0e299713af2a8e69015a6eaf673`
  (repaired, real) — read via `git show` this session.
- `on-the-record/hooks/amendment_channel.py`'s abandoned sibling-branch
  history: `f699f5c6` and its parent, on
  `origin/issue-3129/implementation-blueprint+test-derivation+silent-failure-audit-5d5e5a08`
  — confirmed not an ancestor of `main` (`git merge-base --is-ancestor
  f699f5c6 origin/main`, this session), read via `git show
  f699f5c6~1:on-the-record/hooks/amendment_channel.py` and `git show
  f699f5c6 -- on-the-record/hooks/amendment_channel.py`.

## Open findings

Test-depth pass over
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`,
read in full this session, all test functions accounted for
(derived: a `grep -c "^def test_"` count over that file, run in
`/tmp/pr3233-wt`, matched the "11 passed" figure the acceptance
transcript at the top of this record already shows). Classification:
ten are Genuine Assertion (each asserts a specific
`r.error`/`r.findings`/`returncode`/stdout property that would fail
under a real regression). One, `test_documents_five_of_seven_as_out_of_scope`
(line 84), is Execution-Only-shaped, canonical:
```
def test_documents_five_of_seven_as_out_of_scope():
    assert len(_CAUGHT) == 2
    assert len(_MISSED) == 4  # covers defects 1, 2, 5, 6, 7 (1+2 share a fixture)
```
it asserts properties of two hardcoded lists local to the test file
itself without invoking the lint at all, so it can only fail if someone
edits those two literals in the same file; it verifies nothing about
`scripts/lint/silent_failure.py`'s actual behavior beyond what
`test_catches_sites_3_and_4_before_repair` and
`test_stays_quiet_on_all_seven_sites_after_repair` already do. Minor,
not blocking. Verification density (Genuine Assertion count over total
test count) = 90.9%.

Behavioral coverage gap, directly matching section 3 above. derived: a
`grep -n "chmod\|null"` search over that same test file (run in
`/tmp/pr3233-wt`), this session — result: one `chmod`-adjacent hit only
inside the imported `sf.run_self_check()` body (via the `sf` module
import), zero hits inside any test function body, and zero `null`/
`\x00` hits anywhere in the file. So none of the test functions
exercises `_expand_targets`/directory-`rglob` against a
permission-denied directory, and none exercises a null-byte file — both
gaps are exactly where the two Incorrect-graded reliability findings in
this review were found; the suite's own coverage stops at `scan_file`
called directly (the self-check's path) rather than the CLI's actual
directory-expansion path.

Unresolved items this review recommends before this PR is considered to
satisfy issue #3228: (a) the wiring gap in section 5 — no automated
surface scans a new or changed file, so the class is not "unwritable"
for any site the two hardcoded regressions don't already name; (b) the
null-byte crash and permission-denied-directory conflation in section 3;
(c) the site-7 fixture's wrong mechanism in section 2, which should
either be corrected to the real round-7 defect or reframed as
"illustrative, not a reconstruction" rather than filed alongside sites 3
and 4's real recovered code.

## Next steps

None from this review session — reviewing only; PR #3233 was not
edited, merged, or commented on, per this task's own constraint
(canonical: this session's own tool-call transcript shows only `gh pr
view`/`gh pr diff` read calls and worktree-local file operations against
`/tmp/pr3233-wt`, never `gh pr edit`/`gh pr merge`/`gh pr comment`).

## What did not work

None on the record-worthy path. The symlink-loop attack (section 3) is
the one avenue tried that produced no finding — `pathlib.Path.rglob` on
this repo's Python 3.10 does not follow directory symlinks during
wildcard recursion, so neither a hang nor a mis-scan occurred; recorded
above as a negative result, not omitted.

skill-verdict: adversarial-review — applied: invoked; used its blind,
intent-independent framing to check the fixture-faithfulness claims in
section 2 against git history the PR's own record did not consult
(`--all --follow`), rather than re-verifying only the commands the
record already ran.
skill-verdict: silent-failure-audit — applied: invoked; used its
catch-site/downstream-effect design rule to trace the null-byte crash
(section 3) to the specific uncaught `ValueError`, the
permission-denied conflation to the specific `rglob`/`PermissionError`
swallow, and the wiring gap (section 5) to the specific absence of any
hook or gate that invokes the lint against a real file.
skill-verdict: test-depth-audit — applied: invoked; classified every
test in
`e92623b5e76dc7cb4f16c6023b9acb0461a649d1:tests/test_issue_3228_silent_failure_lint.py`,
computed verification density under "Open findings" above, and named
the one Execution-Only-shaped test and the two behavioral coverage gaps
there.
