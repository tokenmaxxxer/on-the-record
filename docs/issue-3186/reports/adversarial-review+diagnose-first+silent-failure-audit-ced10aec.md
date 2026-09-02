---
issue: 3186
role: adversarial-review+diagnose-first+silent-failure-audit-ced10aec
author: adversarial-review+diagnose-first+silent-failure-audit-ced10aec
skills: adversarial-review (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # this record is an independent verification of PR #3193, the issue-3186 diagnosis deliverable
loop_state: landed
upstream:
  - path: 8ae24fbc6be20ed522c09d1e1062037f2eece4b6:docs/issue-3186/reports/diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1.md
    sha: 8ae24fbc6be20ed522c09d1e1062037f2eece4b6
---

# issue-3186 — adversarial-review+diagnose-first+silent-failure-audit-ced10aec record

## What was done

Independent verification of PR #3193 (tokenmaxxxer/on-the-record, issue
#3186's cross_family overhead diagnosis). Re-derived all four claims from
scratch — read the code myself, ran my own profiler, traced the call
graph myself, re-attributed the drift-guard log markers myself, ran the
full test suite, and diffed against origin/main myself — rather than
trusting the record's pasted numbers.

canonical: `gh pr view 3193` output (state: OPEN, 971 additions / 0
deletions on `git diff $(git merge-base origin/main pr-3193) pr-3193`)

### Claim 1 — `_cross_family_candidate_corpus()` has no subprocess/network calls, profiles under 50ms on ~273 real skills

Verdict: **Present.**

- Read `pipeline.py:1423-1495` directly and its three helpers in
  `skills.py` (`_local_skill_dirs`, `_installed_plugin_skill_dirs`,
  `_skill_content_hash`, `skills.py:175-232`): all pure
  `Path.iterdir()`/`Path.is_dir()`/`Path.read_bytes()`/`hashlib.sha256()`
  — no `subprocess`, `requests`, `urllib`, `socket`, or `os.system` in the
  function body or its call chain.
  derived: `sed -n '1423,1495p' pipeline.py | grep -n "subprocess\|requests\|urllib\|socket\|http.client\|os.system\|os.popen\|asyncio\|aiohttp"` — exit 1, no match
- `skills.py` does import `subprocess` (one call site, `skill_repo_sha()`,
  `skills.py:420-425`, shells out to `git rev-parse`) — confirmed by
  direct grep that `_cross_family_candidate_corpus()` never calls
  `skill_repo_sha()`.
  derived: `grep -n "skill_repo_sha(" *.py` then `sed -n '1423,1495p' pipeline.py | grep -n "skill_repo_sha"` — exit 1, no match inside the function body
- Independently profiled the function against this machine's real corpus
  (own throwaway script, `/tmp/verify_profile_3186.py` / `/tmp/verify_profile_3186b.py`,
  not part of the repo, not committed), wiring `pipeline._sp` via
  `import spawn` exactly as production code does:
  ```
  repo_root entries on disk: 274, corpus size: 272
  1st call: 0.0024s, 2nd call (warm): 0.0020s
  cProfile (no mirrored tier, hash path not forced): 13057 calls in 0.004s
  cProfile (home tier populated, forces hash-dedup on every candidate): 40361 calls in 0.016s
  ```
  derived: `python3 /tmp/verify_profile_3186.py` and `python3 /tmp/verify_profile_3186b.py`, executed live in this session against `/home/jwjung/skill-registry/skills` and `~/.claude/skills`
  Both independently-measured numbers (0.004s bare, 0.016s worst-case
  hashing) are well under 50ms and corroborate the record's own
  `/tmp/profile_cross_family_3186.py` run (0.015s cProfile, 40402 calls,
  corpus 272) to within measurement noise — same order of magnitude, same
  call count, same corpus size. "About 273 skills" matches (274 entries
  on disk, 272 after dedup).

### Claim 2 — the phase's real cost is downstream, in `_cross_family_skill_matches_with_consult()` / `_skill_judge_consult()`

Verdict: **Present.**

Traced the call graph myself, independent of the record's citations:
- `spawn.py:3940-3945` submits `_cross_family_skill_matches_with_consult`
  to a `ThreadPoolExecutor`; `spawn.py:4317-4323`'s `_timed("cross_family")`
  only joins that future — confirmed by direct read, same line ranges the
  record cites.
  canonical: spawn.py:3940-3945, spawn.py:4317-4323
- `_cross_family_skill_matches_with_consult()` (`consult.py:686`) calls
  `_bm25_cross_family_scores()` (`directive_assembly.py:735`), whose first
  step is `_cross_family_candidate_corpus()` (`directive_assembly.py:753`)
  — confirmed by direct read.
  canonical: directive_assembly.py:735-756
- When BM25 leaves candidate slots unfilled, `_skill_judge_consult()`
  (`consult.py:527`) runs a real `subprocess.run(...)` (`consult.py:617-620`)
  spawning a haiku-model session, `timeout=judge_timeout` — confirmed by
  direct read, matches the record's citation verbatim.
  canonical: consult.py:617-620

### Claim 3 — the drift guard fired zero organic times across the 153-log, 30-record sample, once reproductions and self-quotes are attributed away

Verdict: **Present, with a completeness gap in the record's own write-up (does not change the conclusion).**

Re-ran `scripts/issue-3186/measure_cross_family.py --report` from the PR
branch (`pr-3193`, via `git worktree add /tmp/pr3193-wt pr-3193`):
```
log files scanned: 154
bootstrap_timing lines found: 30
spawns with total > 1s: n=9 cross_family=88.044s total=119.628s share=73.6%
all spawns: n=30 cross_family=88.044s total=120.411s share=73.1%
named marker matches: 70 (template-literal excluded: 4, raw regex matches: 74)
```
derived: `python3 /tmp/pr3193-wt/scripts/issue-3186/measure_cross_family.py --report`, executed live in this session

The phase-share numbers (n=9/n=30, 73.6%/73.1%) reproduce **exactly** the
record's pasted figures. The named-marker count (70, vs the record's 52)
does **not** reproduce exactly — expected, not a defect: the scanned log
corpus includes the measuring session's own live transcript, so every
session that re-runs this script (this verification session included)
adds its own self-quotes of the marker text to the pool. `log files
scanned` also grew 153 → 154 for the same reason (this session's own log
file). The script's own report labels this count "raw" with an explicit
caveat for exactly this reason; the number is not meant to be a stable
constant.

Re-derived the manual attribution independently rather than trusting the
record's "7 files, all reproductions or self-quotes" claim:
- The record's own `_DRIFT_MARKER_RE` (`cross-family 후보 스킬 (\S+) 가
  둘 이상의 소스에서 겹친다`) matches in exactly 5 session-log files on
  this machine (checked with the same regex, independently, against all
  154 files): `...e794089c...` (6 hits), `...5bb45250...` (18 hits),
  `...81dab610...` (6 hits), `...550d1ad1...` (36 hits, the diagnosis
  session itself), and this verification session's own log (9 hits).
  derived: python regex scan (`re.compile(r"cross-family 후보 스킬 (\S+) 가 둘 이상의 소스에서 겹친다")`) over `glob.glob('~/.tokenmaxxxer/work/*.session.*.log')`, executed live in this session
- `...5bb45250...` carries the literal lines `REPRODUCED sys.exit: cross-family
  후보 스킬 product-discovery-hypothesis-preregistration 가 둘 이상의
  소스에서 겹친다 — skill-repo(/tmp/tmphd4xyfp9/...)` and `OK: still
  fail-closed when pin matches nothing: cross-family 후보 스킬 dup-skill
  가 둘 이상의 소스에서 겹친다 — skill-repo(/tmp/tmp15gzc66d/...)` —
  confirmed verbatim by direct grep, matching the record's quotes exactly.
  Both use `/tmp/tmp...` synthetic paths, i.e. deliberate guard-testing
  reproductions, not organic dispatch.
  derived: `grep -o "REPRODUCED sys.exit[^\"]\{0,150\}"` and `grep -o "OK: still fail-closed[^\"]\{0,150\}"` against that file, executed live in this session
- `...e794089c...` and `...81dab610...` both quote the same
  `background task \`b1uw8n1gz\` output` — `dispatch_stderr` from a
  synthetic `/tmp/...` reproduction, cited/re-cited across two issue-3127
  sessions investigating the same guard. Not organic.
  derived: python regex context-window scan against both files, executed live in this session
- `...550d1ad1...` (the diagnosis session) and this verification session's
  own log are self-quotes: the diagnosis record's own prose quoting the
  marker, and this session's own tool calls/grep output quoting it back.

Independent conclusion: **zero of the 5 regex-matching files represent an
organic dispatch-time firing** — same conclusion as the record, reached
by independent re-attribution, not by re-reading the record's claim.

**Completeness gap found and not in the record:** the record's Task-2
manual-attribution step used a *looser* pattern
(`grep -rl "둘 이상의 소스에서 겹친다"`, no "cross-family 후보 스킬"
prefix) to find candidate files to read by hand, and reported finding
"7" files this way. Re-running that same loose grep independently finds
8 files (the extra one being this verification session's own log, which
did not exist yet when the record was written — expected). Three of
those files — `...0d4eb553...` (issue-3042), `...independent-verification-1...`
(issue-3129), and `...test-derivation-d2b8a13d...` (issue-3127) — do
**not** match the strict marker regex at all. Read their context
directly: all three quote a *different* guard, `skills.py:404`'s
`--skills: {name} 가 둘 이상의 소스에서 겹친다` (the explicit `--skills`
flag resolver's own fail-closed exit) — a message that shares the tail
phrase "가 둘 이상의 소스에서 겹친다" with the cross-family marker but is
not it (confirmed: only `pipeline.py:1490` has the "cross-family 후보
스킬" prefix; `skills.py:404` is the only other `sys.exit` in the repo
carrying the shared tail phrase).
derived: `grep -rn "둘 이상의 소스에서 겹친다" --include="*.py" .` — 2 results total, `pipeline.py:1490` and `skills.py:404`
The record's Task-2 prose says "every other match... traces to this
diagnosis session's own source-code quotes" without mentioning these
three files or the different-guard distinction. This does not change the
final answer — none of the three represents an organic cross-family
firing either (two are `Read`-tool source-code renders of `skills.py`,
one is issue-3129's own unrelated `--skills` guard-testing activity, per
direct inspection of the surrounding transcript) — but the record's
write-up of "7 files, all accounted for" undercounts what it actually
looked at and doesn't explain why 3 of those 7 don't match its own
script's regex. A reader checking the record's own numbers against its
own loose recon grep would hit this gap.

Sample-validity note: the record already states the limitation the task
asked about — "the sample is thin (153 session logs on one machine)"
and "a zero-organic rate over this sample does not prove the guard is
unnecessary" — and does not claim the zero rate licenses removing the
guard; it explicitly concludes the opposite ("reads as a correctly-priced
insurance check, not dead code"). This is an appropriately hedged
conclusion, not an overclaim: for 0 successes in n=30 Bernoulli trials,
the rule-of-three upper bound = 3/30 = 10%, so the population rate could
plausibly be up to roughly 1-in-10 — consistent with treating the guard
as unproven-unnecessary rather than proven-dead.

### Claim 4 — none of the four ranked options is worth its cost

Verdict: **Present, with one specific inaccuracy in the supporting mechanism explanation (does not change the ranking).**

Checked the docstring quote the record uses to reject Option 3 (narrowing
to resolved names only) against the actual source:
```
pipeline.py:1431-1432   걸리면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) fail-closed, 잡힌
                        소스를 전부 이름 붙여 보고한다.
```
canonical: pipeline.py:1428-1436 (matches the record's citation verbatim)

**Inaccuracy found in Option 1's reasoning:** the record states
"full-content sha256 only runs on an actual cross-tier name collision
(`pipeline.py:1481`)... so real-world cost is usually 0." Reading
`pipeline.py:1481` directly:
```python
if len(ms) > 1 and len({_sp._skill_content_hash(d) for _, d in ms}) == 1:
```
The hash-set comprehension is evaluated whenever a name is claimed by
2 or more sources at all (Python must compute the hashes to decide
whether `len({...}) == 1`) — not only when the sources' content already
differs. Per the function's own comment two lines below, multi-source
overlap without content drift ("`~/.claude/skills` 가 skill-repository
를 그대로 미러링해두는 경우가 흔하다") is described as common in real
deployments, not rare. So hashing runs on any routine tier-mirroring
overlap, not only on a true collision — the record's causal claim
("usually 0" real-world cost) inverts why the hash runs. I confirmed
this directly: my own profiling run with a populated `home` tier (which
mirrors the skill-repo tier on this machine) hashed every one of the
272 candidates (544 `_skill_content_hash` calls, matching the record's
own "worst case" cProfile trace almost exactly), which is the routine
mirrored-tier case here, not a contrived worst case.
derived: `python3 /tmp/verify_profile_3186b.py`, executed live in this session (see Claim 1 section)

This does not change the bottom line: even that "worst case" (which is
plausibly the common case, not a rare one) profiles at 0.016s, three
orders of magnitude under the phase's measured cost — so Option 1's
dismissal is still correct, just for a slightly different reason than
the record states.

### Test suite and empty-state

acceptance: `python3 -m pytest tests/test_issue_3186_diagnosis_artifacts.py -q` (run from `/tmp/pr3193-wt`, the PR-3193 worktree) — result:
```
11 passed in 0.84s
```

acceptance: `python3 -m pytest tests/ -q` (run from `/tmp/pr3193-wt`) — result:
```
385 passed, 2 warnings in 11.16s
```
The 2 warnings are a pre-existing, unrelated `pinned-fixture-divergence`
UserWarning in `test_skill_candidates_floor.py`, not caused by this PR's
diff (that test file is untouched by the PR — see No-change claim
section's merge-base diff stat, which lists only 3 changed files).

Drove the script's empty state two ways, independent of the record (which
only shows the live-data path):

acceptance: `python3 scripts/issue-3186/measure_cross_family.py --report --log-glob "/tmp/empty_logs_3186/*.log"` (empty directory) — result:
```
ERROR: no bootstrap_timing line found in any scanned session log (0 files matched '/tmp/empty_logs_3186/*.log'). This means NO DATA, not a 0% cross_family share or a 0% trigger rate -- do not treat this exit as a measurement.
exit 1
```

acceptance: `python3 scripts/issue-3186/measure_cross_family.py --report --log-glob "/tmp/empty_logs_3186b/*.log"` (one log file present, no bootstrap_timing line) — result:
```
ERROR: no bootstrap_timing line found in any scanned session log (1 files matched '/tmp/empty_logs_3186b/*.log'). This means NO DATA, not a 0% cross_family share or a 0% trigger rate -- do not treat this exit as a measurement.
exit 1
```
Both confirm the acceptance criterion's empty-state contract: loud,
nonzero exit, never a silent zero rate.

### No-change claim (protected paths)

acceptance: `git diff $(git merge-base origin/main pr-3193) pr-3193 -- pipeline.py directive_assembly.py` — result:
```
(no output)
```

acceptance: `git diff $(git merge-base origin/main pr-3193) pr-3193 --stat` — result:
```
 .../diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1.md | 498 +++++++++
 scripts/issue-3186/measure_cross_family.py                                  | 283 +++++++
 tests/test_issue_3186_diagnosis_artifacts.py                                | 190 +++++
 3 files changed, 971 insertions(+)
```
Confirms independently, against the actual merge-base
(`6ae02cced599252ad1c46daa068bff6eb71e0a1e`) rather than the record's
pasted diff stat: `pipeline.py` and `directive_assembly.py` are
byte-for-byte untouched, and the only three files changed are the two
intended deliverables plus the diagnosis record.

Note: `git diff origin/main pr-3193 --stat` (without the merge-base)
shows a large, noisy diff (17 files, thousands of deletions) because
`origin/main` has advanced past the PR's branch point with unrelated
work (other issues' report/script cleanups). That is a false signal of
scope creep — the merge-base diff above is the correct comparison and it
is clean.

### Silent-failure-audit pass on `measure_cross_family.py`

One error-handling site: `_read_text()` (script line 103-107) catches
`OSError` and returns `""` on any read failure — an unreadable log file
(permissions, race with rotation) is silently treated identically to an
empty file: no warning, no distinction in the final report between "0
files had data" and "N files existed but couldn't be read." Classification:
Silently Absorbed (default-value substitution without recording that a
fallback occurred). Low blast radius: `files_scanned` still counts the
path even if unreadable (`scan_logs()`, script line 145-154, appends to
`files_scanned` before attempting the read), so the reported file count
can silently overstate how many files actually contributed data — the
empty-state gate at `main()` only checks for zero *timing records* across
the whole corpus, not per-file read success. Not a correctness issue for
the numbers in the record (log files under `~/.tokenmaxxxer/work/` are
locally owned, not expected to be unreadable), but a real finding for
portability to a machine where that assumption doesn't hold.
canonical: `/tmp/pr3193-wt/scripts/issue-3186/measure_cross_family.py:103-107,145-154` (read directly in this session)

## Why

Task instructions and the adversarial-review skill both require
attacking the measurements directly rather than re-reading the record's
narrative and agreeing with it — a same-session self-review of the
diagnosis would have no incentive to recompute anything. I re-derived
every number from the actual code and actual logs on this machine,
independent of the record's pasted transcripts, before comparing.

## What did not work

None.

## Upstream basis

- PR #3193 (branch `pr-3193`, head `8ae24fbc`), fetched via
  `git fetch origin pull/3193/head:pr-3193` and checked out at
  `/tmp/pr3193-wt` via `git worktree add`.
- `8ae24fbc6be20ed522c09d1e1062037f2eece4b6:docs/issue-3186/reports/diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1.md`
  — the record under review, read via `git show pr-3193:<path>` (not
  present in this session's own worktree, which is on the issue-3186
  review branch, not `pr-3193`).
- `pipeline.py`, `skills.py`, `consult.py`, `spawn.py`,
  `directive_assembly.py` — read directly from this session's own working
  tree, confirmed unchanged by the PR.
  canonical: `git diff $(git merge-base origin/main pr-3193) pr-3193 -- pipeline.py directive_assembly.py` — no output (see No-change claim section above)
- `~/.tokenmaxxxer/work/*.session.*.log` (154 files on this machine at
  time of review) — read directly, independent of the record's pasted
  excerpts.

## Open findings

1. Record's Task-2 write-up ("7 files, all reproductions or self-quotes")
   doesn't reconcile against its own script's stricter marker regex — 3
   of those 7 files actually match a different, unrelated guard
   (`skills.py:404`'s `--skills:` resolver), not the cross-family marker
   at all. Doesn't change the zero-organic conclusion (independently
   re-verified above) but is a gap in the record's own rigor. Resolution
   path: none required — informational, diagnosis-only issue, no code to
   fix.
2. Record's Option-1 ranking narrative states hashing "only runs on an
   actual cross-tier name collision... usually 0" when the code actually
   hashes on any multi-tier name overlap (routine mirroring included).
   Doesn't change the ranking (worst-case profile still far under 50ms).
   Resolution path: none required — cosmetic inaccuracy in an already-
   correct conclusion.
3. `measure_cross_family.py`'s `_read_text()` silently absorbs `OSError`
   into an empty string, and `files_scanned` counts a path before
   confirming it was readable — a machine with unreadable log files would
   silently under-report data without the empty-state gate catching it
   (that gate only fires on zero *timing records* corpus-wide, not per-file
   read failure). Low real-world likelihood on this machine's own log
   directory. Resolution path: none required for this diagnosis-only
   issue; worth a one-line fix (log a warning per unreadable file) if the
   script is reused elsewhere.

## Next steps

acceptance: `python3 -m pytest tests/ -q` (run from `/tmp/pr3193-wt`) — result:
```
385 passed, 2 warnings in 11.16s
```
Verification finished this turn; no further action needed.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; drove the whole
verification stance — re-derive every measurement independently instead
of re-reading and agreeing with the record's pasted numbers, per the
task's explicit instruction to attack the measurements
skill-verdict: silent-failure-audit — applied: invoked; used to audit
`measure_cross_family.py`'s `_read_text()` OSError-swallowing path (Open
findings #3)
skill-verdict: diagnose-first — applied: invoked; used to judge the
record's sample-validity framing (rule-of-three reasoning on the 0-of-30
organic rate, Claim 3 section above) and to confirm the record does not
commit the "act before measuring" or "zero rate proves unnecessary"
errors this skill flags.
canonical: `python3 /tmp/pr3193-wt/scripts/issue-3186/measure_cross_family.py --report` (see Claim 3 section above), denominator_spawns=30, reproduced live in this session
