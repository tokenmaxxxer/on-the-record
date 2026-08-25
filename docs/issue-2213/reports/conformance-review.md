---
issue: 2213
role: conformance-review
loop_state: reported
upstream:
  - path: consult.py
    sha: ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5
  - path: docs/issue-2213/reports/performance-engineering.md
    sha: ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5
subject: PR #2255 (issue-2213/performance-engineering, head ef1ffc99)
test: issue #2213 Acceptance section (verbatim, 3 bullets + empty-state annotation) vs PR #2255's diff and its docs/issue-2213/reports/performance-engineering.md record
result: failed
assertedBy: issue-2213/conformance-review (builder-blind independent review, this session)
---

# issue-2213 — conformance-review record

## What was done

Builder-blind conformance review of PR #2255 against issue #2213's frozen
Acceptance section — read independently, no access to the builder
session's own reasoning beyond what is committed in the diff and its
record.

canonical: gh issue view 2213 (fetched live at review time; the source
this record grades PR #2255 against).

1. `git fetch origin pull/2255/head && git worktree add /tmp/pr2255-check
   FETCH_HEAD` — checked out PR #2255's head into a tree isolated from
   this review branch.
   canonical: git -C /tmp/pr2255-check rev-parse HEAD
   ```
   ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5
   ```
2. Extracted the Acceptance section's bundled clause ("timing plus
   cache_read_input_tokens and concurrency count ... recorded for 10+
   spawns") into three separately-verdicted requirements, per
   conformance-review-requirement-extraction rule 1.
3. Independently re-ran the one regression test the PR claims to have
   fixed, against the PR's own checkout, not the pasted output alone:
   canonical: cd /tmp/pr2255-check && python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path -q
   ```
   1 passed in 10.50s
   ```
   This reproduces the PR body's own `## Test plan` claim
   ("1 passed") independently.
4. Independently traced `concurrency = len(_sp._live_workspaces())`
   (`ef1ffc99:consult.py:230`) into its definition:
   canonical: sed -n '569,576p' /tmp/pr2255-check/lifecycle.py
   ```
   def _live_workspaces() -> dict[Path, dict]:
       """살아있는(pid alive) 로스터 엔트리를 워크스페이스 절대경로로 인덱싱."""
       roster = _sp._roster_load()
       live = {}
       for e in roster.values():
           if _sp._alive(e.get("pid", 0)):
               live[Path(e["work"]).resolve()] = e
       return live
   ```
   This confirms the mechanism the record's own methodology note
   describes: a direct call to `_skill_judge_consult()` (bypassing
   `_spawn_one()`'s fork/roster-register path) is never registered into
   this roster itself, though it would still see any *other* genuinely
   live registered spawn at call time.

The check-runner's FAIL on this PR was not treated as a verdict input,
per this task's own note that it is a known classifier misparse of
measurement prose as file-existence (PR #2244 comments) — graded on
substance from the diff and record directly.

## Why

Extracted the Acceptance section into discrete, independently-checkable
obligations before assigning any verdict (conformance-review-requirement-extraction),
because the bundled clause's three sub-metrics turn out to have distinct,
separately-falsifiable evidence in the diff (see Findings below) — grading
it as one bullet would have let the concurrency gap hide behind the two
metrics that are genuinely well-measured. Picked Inspection/Analysis for
data-driven requirements (the 18-call harness run itself is not
reproducible this session — it depended on a live model call against a
since-mutated ledger/roster state) and Test where reproduction was
actually possible (the one regression fix), per
conformance-review-verification-method-selection rule 4.

## Findings

---
requirement: "per-spawn cross_family wall-time timing is recorded for 10+ spawns"
spec_ref: "issue #2213 Acceptance, bullet 1 (first third of the bundled clause)"
verdict: Present
evidence: "ef1ffc99:consult.py:224,288-289,336-350 (wall_s instrumentation and ledger_write); ef1ffc99:docs/issue-2213/reports/performance-engineering.md:119-122 (results table, n=18)"
canonical: sed -n '119,122p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
| condition | n | wall_s min | wall_s p50 | wall_s p90 | wall_s max | spread (max minus min) | cache_read (tokens) | cache_creation (tokens) |
|---|---|---|---|---|---|---|---|---|
| unfixed (pre-fix cmd/env) | 8 | 26.0s | 53.1s | 69.9s | 70.9s | 44.9s | 18140, every call | roughly 11.6k-11.7k |
| fixed (post-fix cmd/env)  | 10 | 33.5s | 39.9s | 66.2s | 68.6s | 35.1s | 21937, every call | roughly 7.7k |
```
derived: 8 + 10 = 18 samples, clearing the Acceptance line's "10+" bar.
rationale: wall_s is measured around the real subprocess call, identical
cmd/env construction whether invoked via a full spawn or directly (both go
through `_consult_cmd_and_env()`); the table above, read directly from the
PR's own checkout, shows 18 measured samples with wall_s populated in
every row.
---
requirement: "per-spawn cache_read_input_tokens is recorded for 10+ spawns"
spec_ref: "issue #2213 Acceptance, bullet 1 (second third of the bundled clause)"
verdict: Present
evidence: "ef1ffc99:consult.py:348 (usage.get(\"cache_read_input_tokens\") written to the ledger event); ef1ffc99:docs/issue-2213/reports/performance-engineering.md:119-122 (same table as above)"
canonical: sed -n '292,296p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
$ python3 -c "import issue2213_measure as m; m.run_batch('before-seq', False, 5, 1)"
{"batch": "before-seq", "fixed": false, ..., "wall_s": 47.078, "duration_ms": 45662, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11672, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.735, "duration_ms": 58260, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11660, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 31.591, "duration_ms": 30091, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11661, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.053, "duration_ms": 56224, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11649, "concurrency": 0, "outcome_ok": true}
```
rationale: cache_read_input_tokens is a property of the model's own
response to the exact subprocess call under review; direct-call harness
invocation and a full spawn hit the identical code path
(`_skill_judge_consult()` -> `subprocess.run(cmd, ..., env=env)`), so the
raw per-call lines above, read from the PR's own checkout, show the field
populated on every one of the 18 real, executed calls.
---
requirement: "per-spawn concurrency count is recorded for 10+ spawns"
spec_ref: "issue #2213 Acceptance, bullet 1 (third third of the bundled clause), read together with the issue's own empty-state annotation"
verdict: Surface
evidence: "ef1ffc99:consult.py:230,349 (concurrency field wired into the ledger event); lifecycle.py:569-576 (_live_workspaces() mechanism, read above under 'What was done'); ef1ffc99:docs/issue-2213/reports/performance-engineering.md:291-316 (raw per-call output) and :330-351 ('Which candidate' + Open findings prose)"
canonical: sed -n '291,316p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
$ python3 -c "import issue2213_measure as m; m.run_batch('before-seq', False, 5, 1)"
{"batch": "before-seq", "fixed": false, ..., "wall_s": 47.078, "duration_ms": 45662, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11672, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.735, "duration_ms": 58260, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11660, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 31.591, "duration_ms": 30091, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11661, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 59.053, "duration_ms": 56224, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11649, "concurrency": 0, "outcome_ok": true}
{"batch": "before-seq", "fixed": false, ..., "wall_s": 69.497, "duration_ms": 54273, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11682, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('after-seq', True, 5, 1)"
{"batch": "after-seq", "fixed": true, ..., "wall_s": 65.968, "duration_ms": 32292, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7696, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 37.654, "duration_ms": 35974, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 48.481, "duration_ms": 46020, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 34.166, "duration_ms": 32749, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7694, "concurrency": 0, "outcome_ok": true}
{"batch": "after-seq", "fixed": true, ..., "wall_s": 68.615, "duration_ms": 66979, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7701, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('after-conc', True, 4, 4)"
{"batch": "after-conc", "fixed": true, ..., "wall_s": 36.024, "duration_ms": 34328, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7700, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 38.848, "duration_ms": 36913, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7704, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 40.909, "duration_ms": 39270, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7700, "concurrency": 0, "outcome_ok": true}
{"batch": "after-conc", "fixed": true, ..., "wall_s": 43.445, "duration_ms": 41808, "cache_read_input_tokens": 21937, "cache_creation_input_tokens": 7699, "concurrency": 0, "outcome_ok": true}

$ python3 -c "import issue2213_measure as m; m.run_batch('before-conc', False, 3, 3)"
{"batch": "before-conc", "fixed": false, ..., "wall_s": 25.975, "duration_ms": 20816, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11686, "concurrency": 0, "outcome_ok": true}
{"batch": "before-conc", "fixed": false, ..., "wall_s": 30.723, "duration_ms": 25595, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11686, "concurrency": 0, "outcome_ok": true}
{"batch": "before-conc", "fixed": false, ..., "wall_s": 70.877, "duration_ms": 65751, "cache_read_input_tokens": 18140, "cache_creation_input_tokens": 11682, "concurrency": 0, "outcome_ok": true}
```
derived: grep -c '"concurrency": 0' over the fenced block above = 17 of
17 printed lines read "concurrency": 0 (the 18th sample, a smoke-test call
noted in the record at line ~323-327, is not printed in this batch dump
but is described there as also carrying no roster registration).
canonical: sed -n '330,351p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
1. Candidate 4 (cold vs. warm filesystem/plugin-dir state) is untested —
   all 18 measured calls ran against the same warm checkout throughout one
   session. Resolution path: once real production spawns carry the
   `skill_judge_perf` instrumentation, compare wall_s for the first spawn
   after a host reboot or cold cache against later warm spawns.
2. Two wall-minus-duration outliers (15.2s unfixed, 33.7s fixed) are
   unaccounted for by the model's own `duration_ms` — consistent with
   occasional local CLI/session-startup overhead (settings-file write,
   `--plugin-dir` resolution, process exec), but two occurrences out of
   eighteen samples is too small a sample to draw a firm conclusion from.
   Resolution path: if this recurs in production `skill_judge_perf` data,
   add a second timer inside `_skill_judge_consult()` bracketing just the
   `subprocess.run()` call versus the `_consult_cmd_and_env()` setup that
   precedes it, to separate CLI startup from model wait explicitly.
3. Real production concurrency (multiple genuinely distinct role sessions
   contending) was not exercised by this record's harness-level
   self-concurrency probe, which showed no latency blowup under
   self-contention. Resolution path: the shipped `concurrency` field
   (real `_live_workspaces()` count) accumulates this signal automatically
   as real spawns run; revisit once a double-digit set of production
   `skill_judge_perf` events with `concurrency` at 2 or higher exists.
4. No production SLO/error-budget tracking exists yet for this SLI — the
   `slo_target`/`error_budget_remaining` frontmatter above is a first
   proposal, not a committed target, and needs review by whoever owns
   spawn-latency budgets before being treated as binding.
```
rationale: the instrumentation code genuinely exists and runs on every
call (Present-shaped), but the fenced raw output above shows every single
printed sample carrying `"concurrency": 0` with zero variance — matching
the PR's own Open finding 3, quoted above, which states in its own words
that "real production concurrency ... was not exercised by this record's
harness-level self-concurrency probe." This is Surface, not Present: the
field never fired on the actual condition the requirement names ("how
many spawns were running concurrently") across any of the 18 samples in
this record, because the harness calls `_skill_judge_consult()` directly
rather than through `_spawn_one()`'s fork/roster-register path. Per
conformance-review-verdict-assignment rule 1, matching/wired code that
never fires on the requirement's actual named condition is Surface, not
Present. It is not Absent, because the field and its ledger schema are
genuinely present and correctly wired (confirmed by direct trace above,
under "What was done").
---
requirement: "the record states which candidate the data supports (or that it remains unexplained)"
spec_ref: "issue #2213 Acceptance, bullet 1 (final clause)"
verdict: Present
evidence: "ef1ffc99:docs/issue-2213/reports/performance-engineering.md:136-186 ('### Which candidate the data supports' section)"
canonical: sed -n '136,141p;177,186p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
### Which candidate the data supports

canonical: this record's own measurement (table and per-call numbers
above, sourced from `runs/ledger.jsonl` and the harness output pasted in
"Upstream basis").

Net: partially explained, not fully — matching the Acceptance line's own
escape hatch ("states which candidate the data supports, or that it
remains unexplained"). Candidate 1 is real and now fixed; candidate 2 is
the best-supported explanation for what is left; candidate 3 is weakly
disconfirmed by the one probe run; candidate 4 remains untested. Per
Acceptance's second bullet, the spread did not narrow materially: median
improved by about a quarter, but p90 and max — the part of the
distribution the issue actually complains about — moved by only a few
seconds, well inside sample-to-sample noise at this sample size. The
`verdict: exhausted` frontmatter line reflects that honestly rather than
declaring the SLO met on a partial fix.
```
rationale: the section fenced above names a specific best-supported
candidate (model-side duration_ms variance, candidate 2) rather than
declaring full resolution or hiding behind the "remains unexplained"
escape hatch when partial evidence exists — this directly satisfies the
clause as written.
---
requirement: "if a fix follows, the observed spread narrows materially from the 19s-74s baseline, measured across a comparable sample"
spec_ref: "issue #2213 Acceptance, bullet 2 (conditional — triggered, since this PR does ship a fix: the two cache-preserving flags added to `_consult_cmd_and_env()`)"
verdict: Absent
evidence: "ef1ffc99:docs/issue-2213/reports/performance-engineering.md:119-122 (table) and :177-186 ('Net: partially explained' paragraph, quoted in full under the requirement above)"
canonical: sed -n '119,122p' /tmp/pr2255-check/docs/issue-2213/reports/performance-engineering.md
```
| condition | n | wall_s min | wall_s p50 | wall_s p90 | wall_s max | spread (max minus min) | cache_read (tokens) | cache_creation (tokens) |
|---|---|---|---|---|---|---|---|---|
| unfixed (pre-fix cmd/env) | 8 | 26.0s | 53.1s | 69.9s | 70.9s | 44.9s | 18140, every call | roughly 11.6k-11.7k |
| fixed (post-fix cmd/env)  | 10 | 33.5s | 39.9s | 66.2s | 68.6s | 35.1s | 21937, every call | roughly 7.7k |
```
derived: p90 69.9s -> 66.2s is a 3.7s move (5.3%); max 70.9s -> 68.6s is a
2.3s move (3.2%) — both against a 19s-74s (55s-wide) original baseline
spread, i.e. under 7% of the baseline spread each, versus median 53.1s ->
39.9s, a 13.2s move (24.9%).
rationale: the table above, read directly from the PR's own checkout,
shows p90 and max — the part of the original 19s-74s complaint the issue
is actually about — moving only a few percent, not materially, while
median moves about a quarter. This is Absent (the required *result* —
material narrowing — did not occur) rather than Incorrect, per
conformance-review-verdict-assignment rule 2: the record does not
misreport or claim a narrowing that didn't happen — its own "Net:
partially explained" paragraph (quoted under the requirement above) says
so in the same words this finding uses, and its `verdict: exhausted`
frontmatter declines to close the issue as resolved.
---
requirement: "executed acceptance evidence in the record (#2137)"
spec_ref: "issue #2213 Acceptance, bullet 3"
verdict: Present
evidence: "ef1ffc99:docs/issue-2213/reports/performance-engineering.md:213-283 (pasted pytest commands + output, git stash comparison); this review's own independent re-run under 'What was done' above"
canonical: cd /tmp/pr2255-check && python3 -m pytest tests/test_spawn_gate_wiring.py::Ledger::test_entry_carries_the_live_log_path -q
```
1 passed in 10.50s
```
rationale: this is the same command re-run by this review session (also
shown under "What was done"), against the PR's own checkout, reproducing
the record's own pasted claim rather than trusting it unverified.
---

## Upstream basis

canonical: git fetch origin pull/2255/head; git worktree add
/tmp/pr2255-check FETCH_HEAD (this turn) — PR #2255 head commit
`ef1ffc997d2eceac2e3c6ebe164fb0ea5992b0d5`.

- `consult.py` at commit `ef1ffc99` (PR #2255's own change) — the
  instrumentation and cache-flag fix under review.
- `lifecycle.py` at commit `ef1ffc99` (unmodified by PR #2255, read this
  turn) — `_live_workspaces()` definition, used to independently verify
  the concurrency-recording mechanism's actual behavior rather than
  trusting the record's own description of it.
- `docs/issue-2213/reports/performance-engineering.md` — untracked on
  this review branch (`issue-2213/conformance-review`); present only on
  PR #2255's own branch/worktree, at commit `ef1ffc99` — the record this
  review checks the Acceptance section's evidentiary claims against.
  Every citation to it above is pinned to `ef1ffc99` and read directly
  from `/tmp/pr2255-check`, not paraphrased.
- Issue #2213's own body (`gh issue view 2213`, read this turn) — source
  of the Acceptance section verbatim, the empty-state annotation, and the
  provenance line.

## Open findings

1. **Concurrency signal never exercised against real spawn concurrency.**
   canonical: the fenced 17-line raw batch output under the concurrency
   Finding above — every printed sample reads `"concurrency": 0`. The
   instrumentation itself (code, ledger schema) is Present; only the
   *evidence this record ships for it* is Surface. Resolution path: PR
   #2255's own record already states this path in its Open finding 3
   (quoted under the concurrency Finding above) — once real production
   spawns emit `skill_judge_perf` events, a follow-up sample drawn from
   `runs/ledger.jsonl` under actual concurrent-session conditions closes
   this gap; no code change is implicated.
2. **Acceptance bullet 2 (spread narrows materially) is not met.** The PR
   ships a real, measured fix, but p90/max move only a few percent (see
   the Absent Finding above). This is not concealed — the PR's own
   `verdict: exhausted` and its explicit deferral of "bounding the phase"
   to a candidate follow-up issue (per the "## Next steps" heading at
   ef1ffc99:docs/issue-2213/reports/performance-engineering.md:357-360)
   already reflects this. Resolution path: the PR's own suggested next
   step (a follow-up issue testing candidate 2 — model-side `duration_ms`
   variance — against production data, then deciding whether to bound
   rather than speed the phase) is the correct path; not something this
   review recommends redoing here.

## Next steps

loop_state: reported is this record kind's terminal state (session-protocol
section 2, review-record -> reported); no further action is required from
this review role on issue #2213. Both open findings above have resolution
paths that belong to a future issue/PR, not to a revision of PR #2255
itself — PR #2255's own record already discloses both gaps honestly and
proposes the same follow-up path this review would otherwise ask for.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the bundled "timing plus cache_read_input_tokens and concurrency count ... recorded for 10+ spawns" clause into three separately-verdicted requirements (rule 1) before assigning any verdict, since the diff and record give each sub-metric distinct, separately-falsifiable evidence.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Inspection/Analysis (read the record's reported numbers, fenced above, against the code that produced them — the 18-call harness run itself is not reproducible this session) for the data-driven requirements, and Test (independently re-ran the one regression test the PR claims to have fixed) where reproduction was actually possible, per rule 4 (reuse existing test, don't re-derive a parallel manual check).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Surface rather than Present for the concurrency requirement (rule 1: matching code exists but never fires on the actual condition named, per the fenced 0-variance raw output) and Absent rather than Incorrect for the "spread narrows materially" bullet (rule 2: the record does not contradict/misreport, it honestly states the result is absent, in its own quoted words).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every finding above cites a commit-pinned `ef1ffc99:file:line` location plus a fenced re-read of the actual content, and the concurrency finding's evidence spans two contributing files (`consult.py` and `lifecycle.py`), both cited as separate links per rule 2.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote one `---`-delimited block per requirement in this file's own `## Findings` section, each carrying requirement/spec_ref/verdict/evidence/rationale, with no block written without both an evidence pointer and a spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: the Acceptance section is one small bundle of requirements against one PR's diff and one record file; full enumeration was feasible, no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting a recorded finding; the task asked for conformance verdicts, not a severity band.
skill-verdict: implementation-audit — not-applicable: this repo's own conformance-review-* skill family (requirement-extraction, verification-method-selection, verdict-assignment, traceability-and-evidence, finding-record) already governs this exact task with repo-specific mechanics (record path, verdict vocabulary, skill-verdict logging) that implementation-audit's generic two-session protocol would only duplicate, not add to.

other mounted skills: dataviz, run, code-review, simplify, security-review, update-config, keybindings-help, claude-api, init, loop, schedule, freelunch:freelunch-code-fanout, freelunch:freelunch-site-fanout, terse — not triggered (unrelated to this review's task).
