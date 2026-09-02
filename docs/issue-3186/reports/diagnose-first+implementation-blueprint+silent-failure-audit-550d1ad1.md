---
issue: 3186
role: diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1
author: diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1
skills: diagnose-first (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: pipeline.py (`_cross_family_candidate_corpus`, unchanged, read only)
    sha: same-commit
  - path: consult.py (`_cross_family_skill_matches_with_consult`, `_skill_judge_consult`, read only)
    sha: same-commit
  - path: spawn.py (`_BOOTSTRAP_PHASES`, `_timed("cross_family")` call site, read only)
    sha: same-commit
---

# issue-3186 — diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1 record

## What was done

Diagnosis-only (no fix implemented, per the issue's "must not"). Two new
deliverable files, no existing file touched:

- `scripts/issue-3186/measure_cross_family.py` — recomputes the
  cross_family phase-share and drift-marker match count from real session
  logs on any machine (glob overridable via `--log-glob` or
  `MEASURE_CROSS_FAMILY_LOG_GLOB`). Loud, nonzero-exit empty state when no
  `bootstrap_timing` line appears anywhere (never a silent 0%).
- `tests/test_issue_3186_diagnosis_artifacts.py` — tests against synthetic
  fixture log content (never depends on the real `~/.tokenmaxxxer/work/`
  contents), covering parsing, aggregation, report shape, and the
  empty-state contract.

acceptance: python3 -m pytest tests/test_issue_3186_diagnosis_artifacts.py -q — result:
```
...........                                                              [100%]
11 passed in 0.86s
```

### Finding 1 — subprocess/network calls inside `_cross_family_candidate_corpus()` and its direct call chain: none

```
$ sed -n '1423,1495p' pipeline.py | grep -n "subprocess\|requests\|urllib\|socket\|http.client\|os.system\|os.popen"
(no output, grep exit 1)
```
derived: sed -n '1423,1495p' pipeline.py | grep -n "subprocess\|requests\|urllib\|socket\|http.client\|os.system\|os.popen" -- exit 1, no lines matched

canonical: pipeline.py:1423-1495 (`_cross_family_candidate_corpus`)

The function's only three helpers — `_local_skill_dirs()`,
`_installed_plugin_skill_dirs()`, `_skill_content_hash()` (all in
`skills.py`) — do only `Path.iterdir()`/`Path.is_dir()`, one `json.loads()`
of a local `installed_plugins.json`, and
`hashlib.sha256((skill_dir/"SKILL.md").read_bytes())`:

```
skills.py:223  def _skill_content_hash(skill_dir: Path) -> str:
skills.py:228      try:
skills.py:229          data = (skill_dir / "SKILL.md").read_bytes()
skills.py:230      except OSError:
skills.py:231          data = b""
skills.py:232      return hashlib.sha256(data).hexdigest()
```
canonical: skills.py:223-232

`skills.py` does import `subprocess`, but its one call site
(`skill_repo_sha()`, `skills.py:420-425`, shells out to `git rev-parse`) is
used only by `resolved_skill_sources()` (the `--skills`-flag resolver,
`skills.py:302`) — a function `_cross_family_candidate_corpus()` never
calls. This rules out the whole subprocess/network category for the
literal function named in the issue title.

### Finding 2 — the "cross_family" bootstrap-timing phase is not `_cross_family_candidate_corpus()`

Tracing the timer's call graph:

```
spawn.py:4317              with _timed("cross_family"):
spawn.py:4322-4323             if _cross_family_future is not None:
                                    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
```
canonical: spawn.py:4317-4323

```
spawn.py:3940-3945     _cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                        _cross_family_future = _cross_family_executor.submit(
                            _cross_family_skill_matches_with_consult,
                            _cross_family_task_text, skill, _skill_repo_root(), issue, cwd,
                            k=_COMPOSED_SKILLS_TOPK,
                            home=Path.home(), target_repo_root=Path(cwd))
```
canonical: spawn.py:3940-3945

The timed span is a join on `_cross_family_skill_matches_with_consult()`
(`consult.py:686`), which calls `_bm25_cross_family_scores()` (which calls
`_cross_family_candidate_corpus()` as its first step — pure disk I/O, no
subprocess, per Finding 1) and then, when BM25 leaves unfilled candidate
slots after the declared-phrase fast path, calls `_skill_judge_consult()`
(`consult.py:527`):

```
consult.py:617-620     _call_t0 = time.monotonic()
                        for attempt_num, attempt_prompt in enumerate((base_prompt, retry_prompt), start=1):
                            r = subprocess.run(cmd, cwd=cwd or str(_sp.ROOT), input=attempt_prompt, text=True,
                                               capture_output=True, timeout=judge_timeout, env=env)
```
canonical: consult.py:617-620

— a real subprocess spawning a haiku-model session (`SKILL_JUDGE_TIMEOUT_DEFAULT
= 90` seconds per attempt, `consult.py:53`, up to 2 attempts). The
function's own comment names itself as the phase's real cost:

```
consult.py:552-554     # 이슈 #2213: 이 함수가 곧 "cross_family" 단계의 실측 비용이다
                        # (`_spawn_one` 이 이 호출을 감싼 future 를 join 만 재는 이유는
                        # `_cross_family_skill_matches_with_consult()` 독스트링 참고) —
```
canonical: consult.py:552-554

### Finding 3 — live profile of `_cross_family_candidate_corpus()`: single-digit milliseconds

Profiled from a standalone throwaway script (`/tmp/profile_cross_family_3186.py`
— not part of this repo, never touched pipeline.py, deleted after use,
never imported by any dispatch path) using `cProfile` (stdlib).

```
$ which py-spy
(no output, exit 1)
```
derived: which py-spy -- exit 1, py-spy is not installed in this sandbox

cProfile (deterministic/instrumenting, not sampling) was used instead.
This is a reasonable substitute here because the function is I/O- and
hashing-bound over a flat, non-recursive directory walk — no deep call
stacks for cProfile's per-call overhead to compound through — so its
instrumentation inflates absolute wall time but does not distort the
relative phase split this diagnosis needs.

Live run against this machine's real skill corpus:

```
$ python3 /tmp/profile_cross_family_3186.py
repo_root = /home/jwjung/skill-registry/skills
skill-repo entries on disk: 274
Unprofiled wall time (warm cache, 2nd call): 0.0086s
corpus size (candidates returned): 272

=== cProfile: top by cumulative time ===
         40402 function calls in 0.015 seconds
   1    0.000    0.000    0.015    0.015  pipeline.py:1423(_cross_family_candidate_corpus)
 272    0.000    0.000    0.007    0.000  pipeline.py:1481(<setcomp>)          # content-hash dedup
 544    0.000    0.000    0.007    0.000  skills.py:223(_skill_content_hash)
 546    0.000    0.000    0.004    0.000  pipeline.py:1459(add)
1099    0.001    0.000    0.003    0.000  {built-in method posix.stat}

=== manual phase split (throwaway instrumentation, not in pipeline.py) ===
enumeration (iterdir across tiers):                                   0.0016s over 546 dirs
hashing worst-case (sha256 every candidate's SKILL.md):                0.0050s over 544 files
BM25 scoring pass (_bm25_cross_family_scores, includes corpus build):  0.0300s, 201 scored docs
```
derived: python3 /tmp/profile_cross_family_3186.py

Split for the four buckets the issue asks about: (a) enumeration ≈
0.0016s, (b) hashing ≈ 0.0050s worst case (production code only reaches
`_skill_content_hash()` on an actual cross-tier name collision, per
`pipeline.py:1481`, so real-world cost is usually 0 — this profiling
script forced the worst case by hashing every candidate to bound it), (c)
scoring pass ≈ 0.0300s total (already includes (a)+(b)), (d) other — the
remainder is dict/set bookkeeping, unmeasurable at this scale. None of it
is subprocess or network (Finding 1). All four buckets sum to well under
50ms (0.05s).

### Finding 4 — real session-log corroboration

```
$ python3 - <<'PY'
import glob, re
files = glob.glob('/home/jwjung/.tokenmaxxxer/work/*.session.*.log')
for f in files:
    txt = open(f, errors='replace').read()
    for m in re.finditer(r'\[([^\]]*)\] bootstrap_timing (?:\w+=[0-9.]+ )*cross_family=([0-9.]+) [^\n]*total=([0-9.]+)', txt):
        skill, cf, total = m.group(1), float(m.group(2)), float(m.group(3))
        if cf > 1.0:
            window = txt[max(0, m.start()-4000):m.start()]
            judge_lines = re.findall(r'skill_judge[^\\"\n]{0,80}', window)
            print(skill, cf, total, judge_lines[-1] if judge_lines else None)
PY
product-discovery-hypothesis-preregistration-e8595864 26.184 29.543 skill_judge 자문 완료 — 2개 선택
independent-verification-1 3.164 3.868 skill_judge 자문 실패 — BM25 top-5 로 fail-open: error: 세션 종료 코드 1
```
derived: python3 regex scan above, executed live against ~/.tokenmaxxxer/work/*.session.*.log

Both slow spawns pair with a `skill_judge` consult-call log line
immediately before the `bootstrap_timing` line — one call returned (2
skills picked), one call was attempted and exited nonzero. Every observed
`cross_family` value under 0.01s pairs instead with a "no candidates, BM25
skipped the consult" log line:

```
$ python3 -c "
import glob, re
files = glob.glob('/home/jwjung/.tokenmaxxxer/work/*.session.*.log')
for f in files:
    txt = open(f, errors='replace').read()
    for m in re.finditer(r'\[([^\]]*)\] bootstrap_timing (?:\w+=[0-9.]+ )*cross_family=([0-9.]+) [^\n]*total=([0-9.]+)', txt):
        if float(m.group(2)) < 0.01:
            window = txt[max(0, m.start()-3000):m.start()]
            jl = re.findall(r'skill_judge[^\\\"\n]{0,80}', window)
            if jl: print(m.group(1), m.group(2), jl[-1])
"
implementation 0.0 skill_judge 자문 안 함 — BM25 후보 0개 (no-candidates)
implementation 0.0 skill_judge 자문 안 함 — BM25 후보 0개 (no-candidates)
```
derived: python3 -c script above, executed live in this session

### The two numbers

```
$ python3 scripts/issue-3186/measure_cross_family.py --report
issue-3186 cross_family diagnosis -- measured report
log files scanned: 153
bootstrap_timing lines found: 30

-- cross_family phase share of bootstrap total --
  spawns with total > 1s: n=9 cross_family=88.044s total=119.628s share=73.6%
  all spawns: n=30 cross_family=88.044s total=120.411s share=73.1%

-- drift-guard marker matches (raw, see caveat) --
  named marker matches: 52 (template-literal/source-render matches excluded: 2, raw regex matches before filtering: 54)
  denominator (bootstrap_timing-covered spawns): 30
  raw rate: 52/30 = 173.33%
  CAVEAT: this count cannot distinguish an organic dispatch-time abort from
  a deliberate manual reproduction of the guard ... manual attribution of
  each match is required before treating this as a production trigger rate.
```
acceptance: python3 scripts/issue-3186/measure_cross_family.py --report — result:
```
exit 0, report as shown directly above
```

Number 1, phase share: measures 73.6% share on the 9 real
`bootstrap_timing` records with total over 1 second, which is close to the
issue's own 74% figure.

Number 2, the script's own raw drift-marker count sits above 100%
(173.33%, printed in the fenced report immediately above) — this is
labeled "raw" in the report's own CAVEAT line and is not the true trigger
rate; see the next section for the manually attributed number.

### Task 2 manual attribution — the true trigger rate

```
$ grep -rl "둘 이상의 소스에서 겹친다" ~/.tokenmaxxxer/work/*.session.*.log | wc -l
7
```
derived: grep -rl "둘 이상의 소스에서 겹친다" ~/.tokenmaxxxer/work/*.session.*.log | wc -l

Reading the surrounding context in every one of those 7 files (excerpts,
read live in this session):

```
...REPRODUCED sys.exit: cross-family 후보 스킬 product-discovery-hypothesis-preregistration 가 둘 이상의 소스에서 겹친다 — skill-repo(/tmp/t...
...OK: still fail-closed when pin matches nothing: cross-family 후보 스킬 dup-skill 가 둘 이상의 소스에서 겹친다 — skill-repo(/tmp/tmp15gzc66d/skill-repo/dup-skill)...
```
canonical: on-the-record-issue-3127-implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250.session.20260902T215918.965814.log (session transcript, read live in this session)

Both quoted lines carry `"REPRODUCED sys.exit: ..."` / `"OK: still
fail-closed when pin matches nothing: ..."` prefixes — an agent working
issue-3127 deliberately built a synthetic tier collision under
`/tmp/tmp.../skill-repo/dup-skill` and a matching `local-user` path to
reproduce and verify the guard's fail-closed behavior as a manual test.
Every other match across the 7 files traces to this diagnosis session's
own source-code quotes (the marker regex/docstring in
`measure_cross_family.py`, and this session's own `grep`/read commands
echoed into its own transcript).

Attributing all matches by hand this way, the organic (real-dispatch)
count is zero out of the 30 bootstrap_timing-covered spawns (0%) scanned
above — same denominator as Number 1.
derived: manual review of all 7 files listed by the grep command above, read live in this session; cross-referenced against the 30-record denominator from `python3 scripts/issue-3186/measure_cross_family.py --report`'s "bootstrap_timing lines found: 30" line shown earlier

Two deliberate reproductions during guard testing (issue-3127) show the
guard fires correctly under a contrived collision; they are not evidence
it fires in production. A zero-organic rate over this sample does not
prove the guard is unnecessary. The sample is thin (153 session logs on
one machine), and most spawns in this environment only ever populate the
skill-repository tier — `~/.claude/skills` mirrors it byte-identically, so
the dedup step collapses that tier pair before the fail-closed branch is
reached:

```
pipeline.py:1481-1487      if len(ms) > 1 and len({_sp._skill_content_hash(d) for _, d in ms}) == 1:
                                # 실제 운영 환경에서는 `~/.claude/skills` 가 skill-repository 를
                                # 그대로 미러링해두는 경우가 흔하다 — 같은 이름이 같은
                                # `SKILL.md` 내용을 가리키면 어느 tier 를 골라도 채점 결과가
                                # 바이트 단위로 같으므로, 이건 "가리기"가 아니라 중복이다.
                                # fail-closed 는 내용이 실제로 갈릴 때만 발동한다.
                                ms = ms[:1]
```
canonical: pipeline.py:1481-1487

A guard with a measured 0-of-30 (0%) organic-trigger sample that costs
about 0.015s per spawn (Finding 3's cProfile run above) reads as a
correctly-priced insurance check, not dead code.

No new marker line was added to `pipeline.py`. A marker already exists and
is distinguishable — the phrase "cross-family 후보 스킬 ... 둘 이상의
소스에서 겹친다" (`pipeline.py:1490-1492`) is unique to this one
`sys.exit()` call site in the codebase. Per the issue's own preference
("prefer NOT touching pipeline.py at all unless you're certain this is
safe and necessary"), touching it was unnecessary.

## Why

The issue's own framing ("That phase is `_cross_family_candidate_corpus()`
...") is an approximation worth correcting before ranking Task 3's
options: the timed phase and the named function are not the same thing
(Finding 2 above). Every one of the four Task-3 options is phrased as an
optimization of the corpus-build/comparison step, and that step measures
under 50ms (Finding 3's cProfile run) — three orders of magnitude below
the phase's own measured cost (Number 1 above). Diagnosing
`_cross_family_candidate_corpus()` in isolation, as the issue title
literally asks, would have produced a dead end without Finding 2's
call-graph trace and Finding 4's log corroboration.

cProfile, not py-spy (not installed here, Finding 3), was chosen because
the function's shape (flat iteration + hashing, no deep recursion) means
cProfile's per-call instrumentation overhead does not distort the
*relative* phase split, even though it inflates absolute wall time versus
the unprofiled run (0.015s profiled vs 0.0086s unprofiled for the same
call, both in Finding 3's fenced run above — a roughly 1.7x inflation,
irrelevant three orders of magnitude below the phenomenon being
explained).

### Task 3 — ranked options, judged against the measured 0-of-30 trigger sample and the real cost location

Ranked worst-tradeoff-last; all four are mis-targeted relative to Finding
2 and Finding 4 (the actual 73%-plus cost lives in
`_skill_judge_consult()`'s subprocess call, not in
`_cross_family_candidate_corpus()`):

1. **Narrow what is compared** — least indefensible of the four, but still
   mis-targeted. The comparison is already minimal: full-content sha256
   only runs on an actual cross-tier name collision (`pipeline.py:1481`,
   quoted above), and Finding 3 measures that path at 0.0050s worst case,
   near 0s typical. Gives up: comparison fidelity (hashing only
   frontmatter instead of the full `SKILL.md` could miss a collision where
   only the body differs) for a saving already unmeasurable at 0.0050s.

2. **Cache keyed on corpus state** — would help only if enumeration and
   hashing were the bottleneck; Finding 3 measures 0.0016s enumeration
   plus 0.0050s hashing for 274 real skill-repo entries on this machine.
   Gives up: cache-invalidation correctness (a plugin install/uninstall or
   local-skill edit between refreshes could let a real collision go
   undetected until the cache's TTL expires) for a saving that does not
   exist at today's corpus size or cost location.

3. **Compute only for names actually resolved (not the full corpus)** —
   directly weakens the fail-closed guarantee. The whole reason the check
   enumerates the full corpus and fails closed on any collision (not only
   collisions among names a caller happens to pick) is in the function's
   own docstring:

   ```
   pipeline.py:1431   가 소스 두 개 이상에 걸리면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) fail-closed, 잡힌
   pipeline.py:1432   소스를 전부 이름 붙여 보고한다. `hooks/` 서브디렉터리를 든 후보는
   ```
   canonical: pipeline.py:1431-1432

   Narrowing to "only resolved names" means collisions in never-selected
   candidates go permanently unchecked — a structural regression of the
   guard's coverage promise, for a saving inside a phase already measured
   under 50ms (Finding 3).

4. **Move the check off the dispatch path into a periodic audit** — the
   check has no real synchronous cost to move (Finding 3: about 0.015s).
   Moving it off-path buys no measurable latency while opening a real
   window: a genuine collision would mount silently and run until the next
   audit cycle, for a check whose entire value is stopping the spawn
   before it uses possibly-wrong skill content. Trading synchronous
   fail-closed correctness for a latency win Finding 3 shows does not
   exist is the worst-judged option of the four.

**Recommendation outside the four given options:** the real target for
future latency work is `_skill_judge_consult()`'s subprocess call
(`consult.py:617-620`, quoted in Finding 2), for example caching the
judge's picked/rejected decision per task-text/candidate-set hash,
reducing `_CROSS_FAMILY_CONSULT_TOPN`, or accepting the LLM round trip as
the cost of a semantic (not lexical) skill-selection judgment. That
function was not asked to be fixed in this issue — flagged here as the
natural follow-up issue, informed by Finding 2 and Finding 4.

## What did not work

The first automated attempt at counting the drift-guard marker (regex
match count over raw log text, filtering only the un-interpolated
`{name}` template literal) produced a raw ratio above 100% (52-over-30 =
173.33%, printed in the fenced report under "The two numbers" above) —
mathematically impossible as a per-spawn trigger rate, because a single
session's transcript can quote the marker text many times (its own source
code, its own prior grep output) without the guard ever firing in that
spawn. This is not a bug in the regex; it is an inherent limit of grepping
session transcripts for marker text, since a transcript can quote its own
source or a deliberate reproduction and raw text matching cannot tell
those apart from an organic dispatch-time abort. The script labels this
count "raw" with a printed CAVEAT rather than presenting it as a trigger
rate (see `measure_cross_family.py`'s `trigger_rate_stats()` docstring);
the real, manually-attributed rate (Task 2 section above) is reported in
this record's prose, not computed by the script, because that attribution
required reading surrounding transcript context by hand.

## Upstream basis

- `pipeline.py:1423-1495` (`_cross_family_candidate_corpus`) — read only,
  unchanged (diff stat below).
- `directive_assembly.py:735-756` (`_bm25_cross_family_scores`, the call
  site) — read only, unchanged (diff stat below).
- `consult.py:527-825` (`_skill_judge_consult`,
  `_cross_family_skill_matches_with_consult`) — read only; identified as
  the real cost location (Finding 2, Finding 4).
- `spawn.py:790-795` (`_BOOTSTRAP_PHASES`), `spawn.py:3937-3945` (future
  submission), `spawn.py:4317-4323` (`_timed("cross_family")` join) — read
  only; identified as the timer's actual call graph.
- `~/.tokenmaxxxer/work/*.session.*.log` (153 files on this machine) —
  read only, source of the two measured numbers.

```
$ ls ~/.tokenmaxxxer/work/*.session.*.log 2>/dev/null | wc -l
153
```
derived: ls ~/.tokenmaxxxer/work/*.session.*.log 2>/dev/null | wc -l

- `/tmp/profile_cross_family_3186.py` — throwaway profiling script, not
  part of the repo, never imported by any dispatch path, not committed.

### Diff-stat proof (protected paths unchanged)

```
$ git diff origin/main -- pipeline.py directive_assembly.py
(no output -- zero-line diff)
```
derived: git diff origin/main -- pipeline.py directive_assembly.py

```
$ git diff origin/main --stat
 docs/issue-3186/reports/diagnose-first+implementation-blueprint+silent-failure-audit-550d1ad1.md | NN +++
 scripts/issue-3186/measure_cross_family.py                                                        | NN +++
 tests/test_issue_3186_diagnosis_artifacts.py                                                       | NN +++
 3 files changed, NN insertions(+)
```
derived: git diff origin/main --stat, run at commit time (exact line counts change as this record itself grows; the protected-path emptiness above is the load-bearing part)

No marker line was added to `pipeline.py` — a distinguishable marker
already existed (Task 2 section above), so the issue's conditional
permission to add one was not exercised.

## Open findings

- The real cost driver (`_skill_judge_consult()`'s subprocess call,
  `consult.py:617-620`) sits outside this issue's scope to fix — flagged
  above as the natural follow-up issue. Resolution path: file a new issue
  scoped to that function specifically, informed by Finding 2 and Finding
  4 above.
- The drift-guard's organic trigger sample sits at zero across the
  153-session-log scan on this one machine (Task 2 section above) — small
  and possibly unrepresentative of the full repo history across other
  machines. Resolution path: none needed for this issue — the measured
  sample is reported as-is with its limits stated, per the issue's own
  request to say so rather than infer confidence the data doesn't support.
  `scripts/issue-3186/measure_cross_family.py` is portable and could be
  re-run on other machines to grow the sample.

## Next steps

None — `loop_state: landed`.

acceptance: python3 -m pytest tests/test_issue_3186_diagnosis_artifacts.py -q — result:
```
11 passed in 0.86s
```

acceptance: python3 scripts/issue-3186/measure_cross_family.py --report — result:
```
issue-3186 cross_family diagnosis -- measured report
log files scanned: 153
bootstrap_timing lines found: 30
(exit 0; full report reproduced under "The two numbers" above)
```

PR opened targeting `main`; both commands above ran successfully in this
session against the current working tree, and the diff-stat proof above
shows the protected paths untouched.
