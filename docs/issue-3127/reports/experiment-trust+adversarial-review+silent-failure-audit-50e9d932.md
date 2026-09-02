---
issue: 3127
role: experiment-trust+adversarial-review+silent-failure-audit-50e9d932
author: experiment-trust+adversarial-review+silent-failure-audit-50e9d932
skills: experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #3176 head db9f7d085c0071ae2171716fbc51201d8e17aead (`scripts/issue-3127/run_consumer_pair.py`'s H1 re-operationalization), base f5ff8cfff74be29ccf16ca209e1cfcc71edf0b03
loop_state: done
type: verification
breaking: false
verdict: PR #3176 is Incorrect overall. Two independent, live-reproduced trust-root failures in the new gate (`compute_h1_manipulation()` / `collect_skill_invocation()`): (1) a spawned session can forge its own invocation evidence by appending one raw line to its own `.session.*.log` -- demonstrated on a real log copy; no non-model-writable alternative exists on this machine today. (2) the harness's own `build_stub_skill_repo()` frontmatter-only stub is, BY DESIGN, invoked by every off-arm session that reaches it -- demonstrated on the real skills-off log for study-companion issue #20 (PR #3174's dispatch) -- and `compute_h1_manipulation()` cannot distinguish that from a genuine corpus leak, so it reports every such off arm as "the corpus leaked through" and fails H1. Under the harness's own design, no pair can structurally ever pass the new gate. A third, independent gap (stale-log substitution via `_find_latest_session_log()`'s mtime-only tie-break) is also live-reproduced. Narration/Bash-string false positives (the third angle asked for) are correctly rejected. The pre-registration amendment itself is Present -- it changes only H1's observation source, no pair is scored before or after it, and `verify_preregistration.py`'s ordering property is neither broken nor newly reintroduced by the amendment (it was already broken, unchanged, by PR #3172's pre-existing squash-merge finding). All acceptance-check and test-suite numbers PR #3176 claims (dry-run exit 0, results.json present, verify_preregistration.py exit 1 same defect, 33 passed, 356 passed) reproduced live, unmodified.
upstream:
  - path: PR #3176 (tokenmaxxxer/on-the-record, branch issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-81dab610), commits c5b0d7f2e980b399a86f3e2b575898ab5e5060ed, db9f7d085c0071ae2171716fbc51201d8e17aead
    sha: db9f7d085c0071ae2171716fbc51201d8e17aead
  - path: PR #3172 (tokenmaxxxer/on-the-record, branch issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c)'s own record, docs/issue-3127/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c.md
    sha: 570205e4d3e0921ef2892ea87a2659b142f90dc7
  - path: runs/consult-logs/20260902T125610799701-948846.log
    sha: same-commit
  - path: PR #3174 (tokenmaxxxer/on-the-record)'s real dispatch of study-companion issue #20's skills-off arm
    sha: same-commit
---

# issue-3127 — experiment-trust+adversarial-review+silent-failure-audit-50e9d932 record

## What was done

canonical: this session's own live command transcript below. Independent,
builder-blind verification of PR #3176's H1 re-operationalization (issue
#3127 blocker B), per this session's own spawning instructions to attack the
trust root along six named angles. This session neither wrote nor discussed
PR #3176 before this review (fresh session, no shared context with its
builder) -- `adversarial-review`'s structural-independence requirement.

**Setup.** derived: `gh pr view 3176 --repo tokenmaxxxer/on-the-record
--json ...` and `gh pr diff 3176` -- read the full 977-line diff. derived:
`git fetch origin issue-3127/implementation-blueprint+experiment-trust+
silent-failure-audit-81dab610:pr-3176-ref` and `git worktree add
/tmp/pr3176-wt pr-3176-ref` -- an isolated read-only checkout, never editing
PR #3176's own branch. Read `docs/handbooks/observer-verification.md` (this
record's own `verifies_subject: true` field per its guidance) and PR #3172's
record (`docs/issue-3127/reports/experiment-trust+product-discovery-
hypothesis-testing+silent-failure-audit-e794089c.md`, read via `git show
pr-3172-ref:<path>`) and `runs/consult-logs/20260902T125610799701-
948846.log`.

**Angle 1 -- forge the trust root from inside a spawned session.**

Path discoverability: derived: `grep -n "_session_log_path" pipeline.py`
```
def _session_log_path(cwd: str) -> Path:
    ts = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    return Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")
```
-- deterministic naming, sibling of the workspace dir, both under
`$MUSTER_WORKSPACE_ROOT` (`~/.tokenmaxxxer/work/`), which this session's own
mounted directives already say is browsable (`known-paths.md`). A spawned
session can `ls` its own parent directory and find its own log path with no
special knowledge.

Writability: derived: `grep -n "Popen\|preexec_fn\|setuid\|user=" spawn.py`
-- no match for any privilege-drop mechanism; the dispatch call is
```
proc = subprocess.Popen(
    cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    text=True, env={**os.environ, **extra_env}, start_new_session=True,
)
```
(spawn.py:4761-4764) -- no container/chroot/uid change, confirmed by
`whoami`/`id -u` inside this session returning the same `jwjung`/`1000` that
owns every real `.session.*.log` file under `~/.tokenmaxxxer/work/`
(derived: `ls -la ~/.tokenmaxxxer/work/*.session*.log | head` --
`-rw-rw-r-- 1 jwjung jwjung ...`). PR #3176's own amendment independently
states the same thing (`docs/issue-3127/decisions/pre-registration.md`'s
amendment: "This machine runs every spawned session unsandboxed, as the
same OS user").

Forgery, constructed against a real session log copy: copied the real
skills-on log for study-companion issue #21
(`study-companion-issue-21-product-discovery-hypothesis-preregistration-
dbeb1ea3.session.20260902T213536.864722.log`) to a scratch file.
derived: before -- `measure_skill_invocation.analyze()` on the copy returns
`invoked_skills: ['product-discovery-hypothesis-preregistration']`,
`'usability-eval' not in invoked_skills` (it is mounted but genuinely never
called). Appended one line to the copy:
`{"type":"assistant","message":{"content":[{"type":"tool_use","name":
"Skill","input":{"skill":"usability-eval"}}]}}` -- exactly the shape
`collect_skill_invocation()`'s own docstring calls the non-forgeable
signal. derived: after -- `analyze()` on the modified copy now returns
`invoked_skills: ['product-discovery-hypothesis-preregistration',
'usability-eval']`, `'usability-eval' in invoked_skills` is `True`. One
appended line, accepted with no validation of session ID, tool-call ID,
sequencing, or any signature.

**Verdict, angle 1: Incorrect.** Per this session's own instructions: a
forgery accepted by the check makes the item Incorrect regardless of the
record's own residual-risk note -- and PR #3176's amendment does state this
risk honestly, but stating a risk is not the same as closing it, and the
acceptance bar for a manipulation-check *gate* is that a subject cannot
forge its own pass. What would close it: PR #3176's own forgeability table
already checked the one candidate that would (a PostToolUse hook firing
before the model's own generation sees the result) and found it does not
exist for the Skill tool. derived: `grep -n "matcher" on-the-record/hooks/
hooks.json` -- no `Skill` matcher, reconfirmed this session. Even if such a
hook existed, its own output file would need to live somewhere this
session's same-uid Bash cannot later touch -- under the current
unsandboxed, same-user threat model confirmed above, no locally-written
artifact closes this; only process-level sandboxing (separate uid/container
per spawned session) or an out-of-process recorder the session holds no
write credentials for (a remote/off-machine log, or a write gated to a
different OS user) would.

**Angle 2 -- the frontmatter-only stub.**

derived: `grep -n "build_stub_skill_repo\|frontmatter only" scripts/issue-
3127/run_consumer_pair.py` (on the PR #3176 branch) --
```
def build_stub_skill_repo(skill_name: str, dest: Path) -> Path:
    """Create a REAL, on-disk skill-repo directory containing only
    `skill_name`'s frontmatter (name + description), no procedure body --
    the "corpus present but empty" stub the skills-off arm's
    `MUSTER_SKILL_REPO` points at.
```
(run_consumer_pair.py:127-131, unmodified by PR #3176, pre-existing from an
earlier round). The stub exists specifically so a skills-off session's
Skill-tool call resolves instead of crashing.

Found and inspected a REAL skills-off session log that was not one of the
two PR #3176 verified against: `study-companion-issue-20-product-discovery-
hypothesis-preregistration-e8595864.session.20260902T220919.1063021.log`,
still present on this machine. canonical: `gh pr view 3174 --repo
tokenmaxxxer/on-the-record`, read this session -- confirms PR #3174 fixed
issue #3127's blocker A (the cross-family tier conflict that blocked every
off-arm dispatch in PR #3172) and its own body states it "ran the harness
live against ... issue 20, pair 01-study-groups's skills-off arm ...
dispatch now succeeds." This is that real run's log.

derived: `measure_skill_invocation.analyze()` on this log --
`mounted: []` (nothing shows as mounted, consistent with skills-off), but
`invoked_skills: ['hypothesis-testing', 'product-discovery-hypothesis-
preregistration', 'product-discovery-jtbd-problem-framing',
'work-in-english']` -- the target skill genuinely invoked. Traced the raw
log line for this call:
```
{"type":"user","message":{"role":"user","content":[{"type":"tool_result",
"tool_use_id":"toolu_01XskRV4q6PAMFXqKT8wCozZ","content":"Launching skill:
product-discovery-hypothesis-preregistration"}]}, ...
"tool_use_result":{"success":true,"commandName":"product-discovery-
hypothesis-preregistration"}}
```
followed immediately by the session reading
`/tmp/issue-3127-skills-off-live-cs285bkf/product-discovery-hypothesis-
preregistration/SKILL.md` -- the exact `build_stub_skill_repo()`-generated
stub, frontmatter only, no body -- confirmed by reading its content:
`description: issue #3127 skills-off arm stub -- frontmatter only, no
procedure body, so the named skill resolves (fail-closed unknown-skill
rejection never fires) but carries no actual guidance content.`

Ran PR #3176's own `compute_h1_manipulation()` (copied verbatim from the
PR branch into a scratch import, real workspaces built from the real
issue-19-on and issue-20-off logs, nothing mocked):
```
{
  "on_invocation": {"invoked": true, ...},
  "off_invocation": {"invoked": true, "mounted": [],
                      "invoked_but_not_mounted": true, ...},
  "differs": false,
  "reason": "the skills-off arm's session log ALSO recorded a Skill
             tool_use call naming 'product-discovery-hypothesis-
             preregistration' -- the corpus leaked through ..."
}
```
H1 fails this real pair. But this off arm did exactly what
`build_stub_skill_repo()` was built for it to do -- invoke the named skill
and receive a contentless stub. `compute_h1_manipulation()` computes
`invoked_but_not_mounted: true` (an internal-consistency signal the
function itself returns) but never reads it to distinguish "invoked the
harness's own known-empty stub" from "invoked a genuinely leaked corpus" --
both collapse to the same `invoked: true` boolean from
`collect_skill_invocation()`, and the gate fails identically either way.

Because every off-arm session that reaches a dispatched state is, BY THE
HARNESS'S OWN DESIGN, directed (via the spawn directive's cross-family
skill-injection text) to invoke the named skill and IS ABLE TO (the stub
exists precisely so this call resolves rather than crashing), this is not
an edge case: it is the off arm's designed, expected behavior on every real
run. **Verdict, angle 2: Incorrect** -- live-reproduced against real data
above, and structurally severe: as coded, no real pair can ever satisfy
`compute_h1_manipulation()`'s `differs: True` branch, because the one
condition it requires of the off arm (`not off_invocation["invoked"]`) is
false by harness design whenever the off arm actually runs. derived: `grep
-n "test_both_arms_invoked_is_a_leak_and_fails" tests/
test_issue_3127_h1_and_scoring.py` on the PR branch -- confirms PR #3176's
own new test suite encodes the opposite assumption (that off-arm invocation
is always a leak) as a passing unit test, using a synthetic fixture that
never modeled the stub-invocation case this real log demonstrates.

**Angle 3 -- narration text / Bash command string, no real Skill tool_use.**

derived: constructed a real Bash `tool_use` line (properly JSON-serialized,
matching how the CLI itself would emit it) whose `command` field's literal
text contains the substring pattern `"name":"Skill","input":{"skill":
"usability-eval"}`, appended to a real log copy. Because JSON string
values are backslash-escaped when embedded (`\"name\":\"Skill\"...`), the
raw-substring checks `measure_skill_invocation.analyze()` runs
(`'"name":"Skill"' in line and '"type":"tool_use"' in line`, then
`call_re = re.compile(r'"name":"Skill","input":\{[^}]*"skill":"([^"]+)"')`)
do not match text nested inside another tool's `command`/`content` string
field. derived: `analyze()` on the modified copy -- `usability-eval` still
absent from `invoked_skills`. **Verdict, angle 3: Present** -- correctly
returns `invoked: false` for this sub-vector, because the check's raw-line
matching happens to align with standard JSON string escaping. This does
not rescue the check overall: angle 1's forgery works precisely because it
writes a genuinely new top-level JSON line rather than embedding text
inside an existing field.

**Angle 4 -- multiple `.session.*.log` files, stale-log leak.**

derived: `_find_latest_session_log()`'s own selection rule --
```python
candidates = sorted(parent.glob(workspace.name + ".session.*.log"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
return candidates[0] if candidates else None
```
picks by **mtime**, not by the timestamp encoded in the filename. Built two
logs for one synthetic workspace: an older one (filename ts
`20260901T000000`) with a genuine Skill-tool invocation, and a newer one
(filename ts `20260902T999999`) with none. In natural creation order,
`_find_latest_session_log()` correctly picks the newer, uninvoked one.
derived: after a single `touch` on the OLDER file (no content edit, no
special privilege -- any process that can write to the directory, which
per angle 1's writability finding a spawned session can) -- the selection
flips: `candidates[0]` becomes the stale, invoked log, and
`collect_skill_invocation()` on the result now returns `invoked: True`,
`mounted: ['my-skill']` -- the WRONG arm's data, silently substituted with
no error, no warning, and no distinguishing field in the returned dict.
**Verdict, angle 4: Incorrect** -- a second, independent trust-root gap.
derived: `grep -n "respawned session leaves multiple" scripts/issue-3127/
run_consumer_pair.py` -- `_find_latest_session_log()`'s own docstring
acknowledges multiple logs are an expected respawn scenario, so this is not
a contrived edge case; PR #3176's residual-risk analysis discusses content
forgery but never discusses file-selection substitution, a strictly
cheaper attack (no content knowledge needed at all).

**Angle 5 -- real logs, invoked for each.**

derived: ran `measure_skill_invocation.analyze()` against all three real
logs still present on this machine for skill
`product-discovery-hypothesis-preregistration`:
- study-companion issue #19 (skills-on, PR #3172's arm): `invoked: True`
  (matches PR #3176's own claim).
- study-companion issue #21 (skills-on, PR #3172's arm): `invoked: True`
  (matches PR #3176's own claim).
- study-companion issue #20 (skills-off, PR #3174's dispatch, not one of
  the two logs PR #3176's own record cites): `invoked: True` -- this is the
  live data underlying angle 2's finding above. PR #3176's record states
  "no real off-arm data exists" (true of PR #3172's own two off arms, which
  never dispatched, canonical: PR #3172's own record, "What was done" step
  4, read this session) but this third, real off-arm log did exist on this
  machine and was not checked before that claim was written.

**Angle 6 -- the pre-registration amendment.**

derived: `gh pr diff 3176` on `docs/issue-3127/decisions/pre-
registration.md` -- the amendment is a pure insertion (lines 96-104 of the
diff, `+` only) after the existing Pre-registration-form/Power-statement
content; no line inside the existing "Pre-registration form" section
(decision rule (b), guardrail (c), sample size (e)) is touched. The
amendment's own closing line states this explicitly: "the decision rule
..., guardrail ..., secondary metrics ..., sample size ..., and the power
statement above all remain exactly as registered."

No scored pair before or after the amendment: derived: `git show pr-3176-
ref:docs/issue-3127/_assets/consumer-path-results.json` -- `"run_status":
"not_executed"`, `"decision": "unmeasured -- not a null result (no data
was collected this session)"` -- byte-identical in substance to the same
file on `main` before this PR (both report zero measured arms).

`verify_preregistration.py`'s ordering property: unaffected either way.
derived: `_first_commit_for_path()` uses `git log --diff-filter=A --follow`
-- only the commit that first ADDS the path. derived: `git log pr-3176-ref
--diff-filter=A --follow --format=%H -- docs/issue-3127/decisions/pre-
registration.md` returns exactly one hash, `fb0bb0d3...`, the same commit
PR #3172 already found is also the first commit for
`consumer-path-results.json` (the pre-existing squash-merge same-commit
defect). PR #3176's own amendment commit (`db9f7d08`, a MODIFY, not an ADD)
does not appear in that list and therefore cannot change what
`verify_preregistration.py` checks. derived: `python3 scripts/issue-3127/
verify_preregistration.py` on the PR #3176 worktree -- exit 1, identical
message citing `fb0bb0d3`, reproducing PR #3172's finding exactly.
**Verdict, angle 6: Present.** The amendment changes only H1's observation
source, no pair is scored either side of it, and it neither fixes nor
newly reintroduces the ordering defect -- that defect is orthogonal to
content amendments because the check only ever looks at a file's first ADD
commit. Open, secondary observation (not a regression from this PR):
derived: reading `verify_preregistration.py`'s `_first_commit_for_path()`
source above -- this also means the check would provide zero protection
against a *future* amendment that quietly weakened the decision rule after
seeing partial data; it verifies file-creation order, not content
stability across amendments, and today that protection depends entirely on
the record's own honesty.

**Tests, run live in an isolated worktree (`/tmp/pr3176-wt`, PR #3176's
own head, never the PR's actual branch):**
derived: `python3 -m pytest tests/test_issue_3127_h1_and_scoring.py
tests/test_issue_3127_run_pair.py tests/test_issue_3127_run_consumer_pair.py
-q` -- 33 passed (matches PR #3176's claim).
derived: `python3 -m pytest tests/ -q` -- 356 passed, 2 warnings (the same
pre-existing, unrelated pinned-fixture-divergence warnings PR #3176's
record names -- matches its claim).
derived: `bash -c "python3 scripts/issue-3127/run_consumer_pair.py
--dry-run"` -- exit 0. `test -f docs/issue-3127/_assets/consumer-path-
results.json` -- present. `python3 scripts/issue-3127/
verify_preregistration.py` -- exit 1, same defect cited above.

## Why

`experiment-trust` Step 5's discipline (Twyman's-law: an observation that
looks like a clean pass deserves a forward trace before being trusted) is
what this session applied to `compute_h1_manipulation()`'s own `differs:
True` branch -- it looks like a working gate on the two logs PR #3176
cited, but tracing forward against a third, real log that PR #3176's own
session did not check (issue #20, produced by a sibling PR's real dispatch
around the same time) showed the gate fails every off-arm run that behaves
as the harness's own stub-building code designed it to. This is exactly
the class of anomaly-that-deserves-independent-validation-before-trusted
Step 5 exists to catch, mirrored onto a manipulation-check's own internals
rather than onto a headline effect size.

`adversarial-review`'s structural-independence requirement is what makes
angle-1's forgery test meaningful: this session shares no context with
PR #3176's builder session, so the forgery was constructed from the
mechanism's own stated contract (a JSON line matching
`collect_skill_invocation()`'s documented signal shape) against real data,
not from insider knowledge of how the builder intended it to be read.

`silent-failure-audit` applied to the new code
(`collect_skill_invocation()`, `_find_latest_session_log()`,
`compute_h1_manipulation()`): derived: `grep -n "try:\|except" scripts/
issue-3127/run_consumer_pair.py` over the new code range -- no new
try/except sites, matching PR #3176's own claim; `_find_latest_session_log
()`'s `Path.stat()` calls propagate uncaught, and `collect_skill_invocation
()` delegates to `measure_skill_invocation.analyze()`'s pre-existing,
already-handled `OSError`/`json.JSONDecodeError` paths. No new
Silently-Absorbed site found. The defects this session found (angles 1, 2,
4) are not silent-failure-audit findings in the strict sense -- no
exception is caught and swallowed anywhere in the new code -- they are
construct-validity/trust-root defects in what the code correctly-and-
loudly reports, which is why `experiment-trust` and `adversarial-review`,
not `silent-failure-audit`, are this record's primary instruments.

Did not attempt a live spawn to generate fresh forgery/off-arm data:
the three real logs already on this machine (issues 19, 20, 21) were
sufficient to construct and reproduce every angle live, and a fresh
`--execute` spawn would have re-incurred real GitHub/compute side effects
this session's own instructions did not ask for.

## What did not work

None -- no approach was tried and abandoned this session. The angle-3
narration/Bash-string test initially used a naive `json.dumps()`-wrapped
literal to simulate a Bash command's stdout containing the target pattern
and (correctly) failed to trigger a false positive because JSON escaping
neutralized it; this is the actual, informative result reported under
angle 3, not a discarded attempt.

## Upstream basis

- PR #3176 (`tokenmaxxxer/on-the-record`, sha
  `db9f7d085c0071ae2171716fbc51201d8e17aead`, branch issue-3127/
  implementation-blueprint+experiment-trust+silent-failure-audit-81dab610)
  -- the subject of this verification, not merged, not on this branch;
  canonical: `gh pr diff 3176` / `gh pr view 3176 --json ...`, read this
  session via an isolated `git worktree` at its head, never edited.
- PR #3172's record (`docs/issue-3127/reports/experiment-trust+product-
  discovery-hypothesis-testing+silent-failure-audit-e794089c.md`, sha
  `570205e4d3e0921ef2892ea87a2659b142f90dc7`, not on this branch) -- the
  construct-validity finding PR #3176 responds to, and the two real
  skills-on session logs (issues #19, #21) used in angles 1/3/5. derived:
  `ls ~/.tokenmaxxxer/work/ | grep -E "issue-19-|issue-21-"` -- both real
  session-log files present on this machine, read this session.
- PR #3174 (`tokenmaxxxer/on-the-record`) -- fixed issue #3127's blocker A
  and produced the real skills-off session log for issue #20 this record's
  angle-2 finding depends on. canonical: `gh pr view 3174 --repo
  tokenmaxxxer/on-the-record`, read this session.
- `runs/consult-logs/20260902T125610799701-948846.log` (sha: same-commit)
  -- the consult PR #3176 cites; its own caveat 2 ("assumes the harness
  actually emits a non-model-writable Skill-tool invocation record") is
  the assumption angle 1 tested and found false. canonical: the consult
  log file itself, read this session (17 lines, quoted in "What was done"
  Setup).
- `docs/handbooks/observer-verification.md` (sha: same-commit) -- basis
  for this record's `verifies_subject: true`.

## Open findings

1. **Forgeable trust root** (angle 1) -- `collect_skill_invocation()`'s
   signal can be fabricated by a single appended line from within the
   spawned session's own Bash access. canonical: this session's own live
   forgery reproduction in "What was done", angle 1. Not fixed here
   (verification-only session, per this session's own instructions not to
   edit PR #3176). Resolution path: process-level sandboxing per spawned
   session, or an out-of-process recorder writing somewhere the session
   holds no write credentials for -- both outside this issue's current
   scope.
2. **Stub-invocation misclassified as corpus leak** (angle 2) --
   `compute_h1_manipulation()` cannot distinguish "off arm invoked the
   harness's own known-empty stub" from "off arm invoked a genuinely
   leaked skill," both read as `invoked: true` and fail the gate
   identically. canonical: this session's own live reproduction against
   the real study-companion issue #20 log in "What was done", angle 2. As
   coded, this appears to make `differs: True` unreachable for any off arm
   that actually dispatches and behaves as `build_stub_skill_repo()` was
   designed for it to. Resolution path: gate on whether the off arm's
   invocation resolved to the known-empty stub path (already computable --
   `invoked_but_not_mounted` is returned but unused) rather than on raw
   `invoked` alone.
3. **Stale-log substitution** (angle 4) -- `_find_latest_session_log()`'s
   mtime-only tie-break lets any process that can `touch` an old sibling
   log silently substitute the wrong arm's data, with no error and no
   distinguishing field in the result. canonical: this session's own live
   `touch` reproduction in "What was done", angle 4. Resolution path:
   tie-break on the timestamp encoded in the filename (already parsed
   elsewhere by `_session_log_path()`'s own format) rather than
   filesystem mtime, or refuse to pick when multiple candidates exist
   rather than silently picking one.
4. PR #3172's four already-open findings (cross-family tier conflict --
   fixed by PR #3174 per this session's own angle-2 verification above;
   `spawn.py watch` roster-lookup misreporting; `verify_preregistration.py`
   's squash-merge defect, reconfirmed unaffected by this PR's amendment
   in angle 6 above) are unchanged and out of this session's scope.
   canonical: PR #3172's own record, "Open findings" section, read this
   session.

## Next steps

None from this session -- `loop_state: done`. canonical: the acceptance
checks and test suite reproduced live in "What was done" above (`dry-run`
exit 0, results.json present, `verify_preregistration.py` exit 1, 33
passed, 356 passed) are this session's own terminal evidence; nothing
further is pending in this session's own scope. A future session fixing
findings 1-3 above should re-verify against the same three real logs this
session used (issues #19, #20, #21) -- derived: `ls ~/.tokenmaxxxer/work/
| grep -E "issue-19-|issue-20-|issue-21-"`, confirmed present at the time
of this review -- before claiming the trust-root gate is closed.

skill-verdict: experiment-trust — applied: invoked; Step 1 scope gate
confirmed offline/pre-assigned n=2-4, SRM/A-A machinery not applicable --
canonical: `docs/issue-3127/decisions/pre-registration.md`'s own "Scope
note" section, read this session; Step 5 Twyman's-law forward trace
applied to `compute_h1_manipulation()`'s own `differs: True` branch against
a third real log PR #3176 did not check, surfacing angle 2 (see "Why")
skill-verdict: adversarial-review — applied: invoked; this session shares
no context with PR #3176's builder session (fresh session, artifact-only
review per the protocol); all six angles constructed and run live rather
than assessed from the PR's own prose (see "What was done")
skill-verdict: silent-failure-audit — applied: invoked; classified the new
code's error-handling surface (zero new catch sites, all fallible
operations propagate or delegate to already-handled paths) -- canonical:
this session's own `grep -n "try:\|except"` over the new code range in
"Why", no matches -- and found the session's real defects lie in construct
validity, not silent absorption, stated explicitly rather than forced into
this skill's taxonomy
