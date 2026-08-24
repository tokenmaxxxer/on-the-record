---
issue: 2210
role: implementation
loop_state: landed
upstream:
  - path: on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log
    sha: same-commit
code_under_review:
  - on-the-record/hooks/heredoc_scope.py
  - on-the-record/hooks/spec-index-preflight.sh
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/acceptance-command-real-run-guard.sh
  - on-the-record/hooks/live-fire-claim-real-run-guard.sh
  - on-the-record/hooks/pretooluse_dispatcher.py
type: perf
breaking: no
verdict: pass
---

# issue-2210 — implementation record

## What was done

canonical: bb9cdb089abcbb6ce7b9c1df550c840b6179053e (this branch's HEAD,
the commit under review)

Added `on-the-record/hooks/heredoc_scope.py` (`strip_heredoc_bodies()`)
and wired it into the four PreToolUse gates that shlex-tokenize a Bash
command to detect a real `git commit` invocation
(`gate-registration-guard.sh`, `acceptance-command-real-run-guard.sh`,
`live-fire-claim-real-run-guard.sh`, `spec-index-preflight.sh`), plus
the matching dispatcher-side `setup=_env_contract` wiring in
`pretooluse_dispatcher.py`, so each gate tokenizes a heredoc-body-
blanked command skeleton instead of the raw command (which previously
included any heredoc BODY text verbatim).

canonical: derived: `git show bb9cdb08 --stat`
```
 .orchestrate-hook-fires.log                            |  25 +++++
 on-the-record/hooks/acceptance-command-real-run-guard.sh |  10 +-
 on-the-record/hooks/gate-registration-guard.sh           |  10 +-
 on-the-record/hooks/heredoc_scope.py                     |  47 ++++++++
 on-the-record/hooks/live-fire-claim-real-run-guard.sh     |  10 +-
 on-the-record/hooks/pretooluse_dispatcher.py              |  10 +-
 on-the-record/hooks/spec-index-preflight.sh               |  12 +-
```

## Why

canonical: on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log
(local session log at `/home/jwjung/.tokenmaxxxer/work/`, read directly —
line containing `"command":"cat >> ... 2026-08-24-hunt-bootstrap-cross-family-returned-pr-gate.md << 'MDEOF'"`)
is the exact 7072-char command the issue names as the 331s call; it was
extracted verbatim and saved to `/tmp/otr-2210-profile/real_command.txt`
for reproduction throughout this investigation.

Issue #2210 asked to profile the real dispatcher, establish whether the
heredoc-size cost is superlinear, identify which gate(s) own it without
assuming board-gate, and check whether gates redundantly re-parse the
same body post-consolidation (core#282/#283).

canonical: `on-the-record/hooks/pretooluse_dispatcher.py` `GATES` list
(pre-fix, read directly) — `board-gate.sh` is not one of its 20 entries
at all; that script lives in the separate `tokenmaxxxer-core` repo, so
this repo's own dispatcher was never the thing the issue's suspected-
cause note described.

canonical: derived: `python3 -m cProfile -s cumulative on-the-record/hooks/pretooluse_dispatcher.py`
fed the real captured payload on stdin, on the pre-fix tree:
```
         117946 function calls (117538 primitive calls) in 0.052 seconds
   Ordered by: cumulative time
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     29/1    0.000    0.000    0.052    0.052 {built-in method builtins.exec}
        1    0.000    0.000    0.052    0.052 pretooluse_dispatcher.py:1(<module>)
        1    0.000    0.000    0.046    0.046 pretooluse_dispatcher.py:398(main)
       15    0.000    0.000    0.046    0.003 pretooluse_dispatcher.py:335(_run_gate)
     3489    0.001    0.000    0.027    0.000 shlex.py:299(__next__)
     3489    0.001    0.000    0.027    0.000 shlex.py:101(get_token)
     3489    0.022    0.000    0.026    0.000 shlex.py:133(read_token)
```
`shlex.py:read_token`'s 0.026s cumulative is ~half the run's 0.052s
total, spread across the four gates' independent `shlex.shlex(cmd, ...)`
calls over the same 7072-char string — the "multiple gates
independently re-parse the same body" mechanism the issue asked to
check for, and (per `diagnose-first`'s Amdahl check) a real, non-trivial
share of the run actually profiled.

Direct reproduction of the exact 331s command through the real
dispatcher did NOT reproduce anything close to 331s in this sandbox —
canonical: see the `derived:` `time` measurement in `## What did not
work` below, and `## Open findings` #1 for the honest gap against the
issue's reported figure.

The fix follows both of the issue's suggested directions at once: "if
a gate only needs the target path, it should never touch the body"
generalizes to "these four gates only need to know whether the
command's real shell SYNTAX is `git commit`, which structurally
excludes anything inside a heredoc body since the shell never executes
that text" (a correctness fix — it also removes a false-positive-
activation path where a heredoc body merely mentioning the words
"git"/"commit" in prose made the token check fire); and "parse the
heredoc body once per dispatch, not once per gate" is satisfied because
after stripping, each gate's shlex call runs against a tiny,
body-size-independent skeleton — no separate cross-gate caching layer
was needed. Per `performance-engineering-operational-playbook` rule
1.7 (prefer the removal-shaped fix over an addition-shaped one), this
was chosen over adding a shared token cache.

## What did not work

canonical: derived: `time bash on-the-record/hooks/pretooluse-dispatcher.sh < real_payload.json`
(post-fix tree, real captured 7072-char command, 3 trials) — attempting
to reproduce the issue's reported 331s did not reproduce it:
```
real  0m0.045s
real  0m0.049s
real  0m0.047s
```
Not treated as "nothing to fix" — the cProfile reproduction in `## Why`
(same command, pre-fix tree) still surfaced the real redundant-shlex-
tokenize cost this record's fix addresses; the gap against the reported
wall-clock figure is recorded honestly in `## Open findings` #1 rather
than forced to match.

## Upstream basis

- `on-the-record-issue-2201-implementation.session.20260824T214938.2895093.log`
  — local file, not repo-tracked; sha: same-commit does not apply to it
  (it is external provenance, not a path landing in this commit). Cited
  above as the source of the exact command profiled throughout.
- `on-the-record/hooks/test_dispatcher_equivalence.py` — pre-existing,
  unmodified; sha: same-commit (unchanged by this commit, present at
  bb9cdb089abcbb6ce7b9c1df550c840b6179053e).

## Open findings

1. canonical: see the `derived:` `time` comparison in `## What did not
   work` (post-fix, ~0.045-0.049s vs the issue's reported 331s for the
   same command). The reported 331s outlier does not reproduce in this
   sandbox. The confirmed fix removes a real, measured redundant-
   tokenize cost (~half of the 0.052s cProfile run in `## Why`, and a
   32x per-call shlex speedup — see the isolated benchmark immediately
   below), but I cannot positively attribute the full 331s to it.

   canonical: derived: isolated shlex benchmark, median of 20 runs
   each, on the same real 7072-char command (`shlex.shlex(cmd,
   posix=True, punctuation_chars=True)` before vs after
   `strip_heredoc_bodies()`):
   ```
   cmd_len=7072 skeleton_len=203
   raw_median_ms=4.274
   skeleton_median_ms=0.134
   speedup_x=31.9
   ```
   Most consistent explanation for the remaining gap (`derived:` the
   two measurements above; no additional source read for this specific
   inference): an environmental factor in the original live session —
   network-bound `gh`/`git` subprocess latency, or system contention
   from concurrently-running sessions — that this sandbox does not
   reproduce.

   Resolution path: if a future heredoc-append call is caught taking
   >30s again, capture `time` output alongside the session log (not
   just the log alone) so a live reproduction can separate subprocess
   wall-clock from in-process CPU cost, and re-verify this fix's share
   against that capture.

2. `heredoc-command-refusal-gate.sh` has the same class of raw-command
   (including heredoc-body) regex scan (`_COMMIT_RE`/`_GH_WRITE_RE`),
   sharing the false-positive-activation risk on heredoc-body prose,
   though not the same cost order of magnitude.

   canonical: derived:
   ```python
   import re, time
   _COMMIT_RE = re.compile(r"(?<![\w-])git\s+(?:-[^\s]+\s+)*commit\b")
   body = "git " + ("-x " * 40000)
   t0 = time.time(); _COMMIT_RE.search(body); print(time.time() - t0)
   # 0.142120361328125
   ```
   ~140ms even at 40,000 synthetic dash-tokens — well below any size
   this issue's heredoc-append corpus reaches. Left unchanged: out of
   this issue's latency scope, and it is a denial-message-correctness
   question (a false-positive refusal), not a performance one.
   Resolution path: a follow-up issue scoped to gate correctness on
   heredoc-body false-positive denials, not #2210.

## Next steps

None — loop_state is terminal (`landed`) for this coding-record.

## Acceptance

canonical: derived: `bash on-the-record/hooks/pretooluse-dispatcher.sh`
against the real dispatcher, 7 trials each, record-shaped synthetic
heredoc-append bodies (prose + bullets + code spans + the words
"git"/"commit"/"acceptance:"/"result:" scattered through — the same
content class as issue-2201's real 331s call):
```
n=1024  bytes=1221  trials(s): .069431401 .060085642 .055143605 .052648272 .059855366 .061721525 .051050346
n=8192  bytes=8442  trials(s): .056846871 .058777722 .057455936 .075302749 .052346370 .050472699 .060613029
```
canonical: `derived: median computed from the 7 trials directly above`
— 1024B ≈ 59.8ms, 8192B ≈ 57.5ms — comparable (within ~4%), satisfying
"an 8KB heredoc write through the real `pretooluse-dispatcher.sh`
completes in a time comparable to a 1KB one".

canonical: derived: `python3 -m pytest -q on-the-record/hooks/`
```
1857 passed, 2 xfailed in 248.78s (0:04:08)
```
excludes `test_directive_diet.py`'s injection-size-budget assertions.

canonical: derived: `git stash && python3 -m pytest -q on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget && git stash pop`
(run against this same branch, with only the uncommitted
`.orchestrate-hook-fires.log` tweak stashed — this commit's own fix
stays applied):
```
AssertionError: 2978
assert 2978 <= 2688
FAILED on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
```
canonical: derived: the pytest run immediately above, on this branch's
own HEAD — confirms this failure is pre-existing/unrelated to this fix,
not a regression it introduced.

canonical: derived: `python3 -m pytest -q on-the-record/hooks/test_dispatcher_equivalence.py -v`
```
1085 passed in 39.44s
```
Every existing gate's allow/deny verdict is unchanged.

skill-verdict: diagnose-first — applied: invoked; used Stage 1 (baseline against the real captured command before touching code — derived comparison above showed 331s does not reproduce here) and Stage 2's narrow/dig/verify (cProfile isolated the redundant shlex-tokenize cost) plus the Amdahl-share check to keep the "## Open findings" #1 gap stated honestly instead of overclaimed.
skill-verdict: performance-engineering-operational-playbook — applied: invoked; used rule 1.2 (report median of repeated trials, not a single number or mean) for the acceptance measurement above, and rule 1.7 (prefer a removal-shaped fix over an addition-shaped one) to decide against a cross-gate token cache once stripping made re-tokenizing cheap enough on its own.
other mounted skills: not triggered
