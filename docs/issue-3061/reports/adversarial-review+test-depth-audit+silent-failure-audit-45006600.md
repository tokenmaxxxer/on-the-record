---
issue: 3061
role: adversarial-review+test-depth-audit+silent-failure-audit-45006600
author: adversarial-review+test-depth-audit+silent-failure-audit-45006600
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # tenth independent verification of PR #3087's deliverable, this time of round 8's fix (PR #3218's record)
code_under_review: 39c3240f23ecce7a84cb940968ba60223c9c2a70
loop_state: landed
type: defect-verification-record
breaking: false
verdict: Round 8's two claims both hold, independently re-derived, plus one
  new, narrower Surface finding round 8 did not name. Tuple stays rejected
  and the corrected comment is accurate for the case it fixes and for
  plain instances of the other admitted types, but its headline phrase
  does not literally hold for the subclass cases (dict subclass, str
  subclass, IntEnum) the code also correctly accepts -- Surface, not flat
  Present. The 22-vs-20 count is confirmed a pytest-collection-scope
  difference, re-derived directly at this round's own tip, not only at an
  ancestor commit -- Present. The four historical genuine-escalation cases
  still correctly require a stop with an independently authored manifest
  -- Present, and this is the issue's intended behavior, not a shortfall.
  Nothing in this round's own scope is Incorrect.
upstream:
  - path: docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-10935689.md (PR #3216, ninth independent verification)
    sha: 081e7971d0020f343c43b206255decc51a022cd9
  - path: docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-71ee9aae.md (PR #3218, round 8's fix -- the record this verification attacks)
    sha: same-commit
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3087 (code under review, round 8's tip)
    sha: 39c3240f23ecce7a84cb940968ba60223c9c2a70
---

# issue-3061 — adversarial-review+test-depth-audit+silent-failure-audit-45006600 record

## What was done

Tenth independent, builder-blind verification of PR #3087's scope-manifest
delegation seam, attacking round 8's fix (tuple allowlist comment
correction plus the 22-vs-20 count reconciliation) at commit `39c3240f`,
then stepping back to answer the seam's own governing question: does the
orchestrator now stop asking for authority it was already granted, for the
cases the issue names.

derived: `git worktree add /tmp/pr3087-verify10 origin/issue-3061/implementation-blueprint+silent-failure-audit+test-derivation+decision-brief-f458808c` then `git -C /tmp/pr3087-verify10 rev-parse HEAD` (this session, this turn) — result: `39c3240f23ecce7a84cb940968ba60223c9c2a70`, matching round 8's own frontmatter `code_under_review` claim.

derived: `ls test/test_delegation_state.py` run in this record's own checkout (this session, this turn) — result: "그런 파일이나 디렉터리가 없습니다" (no such file) — confirming `test/test_delegation_state.py` is untracked in this checkout, PR #3087-only; it exists only at `/tmp/pr3087-verify10/test/test_delegation_state.py`, the PR #3087 worktree. Every reference to `test/test_delegation_state.py` anywhere below in this record is that worktree path, always untracked in this checkout, PR #3087-only.

derived: `grep -n "def format_wake_outcomes" on-the-record/monitors/poll_heartbeat_delta.py` run in this record's own checkout (this session, this turn) — result: zero matches, versus a match at `/tmp/pr3087-verify10/on-the-record/monitors/poll_heartbeat_delta.py:101` — the base file exists on both branches (introduced by issue #3120) but the `format_wake_outcomes` function is untracked in this checkout, PR #3087-only. `on-the-record/monitors/test_wake_outcomes.py` (a different, whole file) is likewise untracked in this checkout, PR #3087-only, per the same `git diff origin/main...39c3240f --stat` reproduction cited in Item 3 below.

### Item 1 — the tuple edge and its corrected comment: **Surface**

Read `/tmp/pr3087-verify10/delegation_state.py:295-329` (the module-level
comment above `_MANIFEST_MAX_DEPTH`) and `:330-345` (`_check_no_surrogates`'s
docstring). The stated rule: the allowlist is "the narrower set of Python
types a save-then-load round trip hands back as the SAME type it started
as: `str`, `int`, `float`, `bool`, `None`, and the two containers
`dict`/`list`" — explicitly narrower than "everything `json.dumps()` can
write," with `tuple` named as the worked example (clears `json.dumps()`,
fails the round-trip-same-type test because `json.loads()` always hands
back a `list`).

Re-tested tuple rejection directly against this round's own code, rather
than accepting round 8's reproduction as sufficient.

derived: `python3 -c "import delegation_state as ds, tempfile
with tempfile.TemporaryDirectory() as repo:
    try:
        ds.grant(repo, 'scope', 'jiwon', skill_env='', manifest=[{'tool':'Bash','resource':'x','meta':(1,2,3)}])
        print('ACCEPTED')
    except ds.MalformedManifestError as e:
        print('REJECTED:', str(e)[:70])"` (this session, this turn, at commit `39c3240f`) — result: `REJECTED: manifest entry 0['meta'] is a tuple, which is not a type a manifest value may be` — the tuple edge remains closed, unchanged from the ninth verification's own reproduction.

Re-derived the premise the comment's stated rule rests on: `python3 -c "import json; print(json.dumps((1,2,3)))"` → `[1, 2, 3]` (no error), and `python3 -c "import json; print(json.loads(json.dumps((1,2,3))) == (1,2,3))"` → `False` — `json.dumps()` accepts a tuple, `json.loads()` never hands one back, so the two do not compare equal after a round trip; this is the exact fact the corrected comment cites for excluding tuple, independently re-derived here rather than taken from round 8's own record.

**But graded Surface, not flat Present: independently tested the stated rule against all seven types the ninth verification exercised, not only tuple.**

derived: `python3 -c "
import delegation_state as ds, tempfile, enum

class MyDict(dict): pass
class MyStr(str): pass
class Custom: pass
class IntColor(enum.IntEnum):
    RED = 1

def try_grant(label, meta):
    with tempfile.TemporaryDirectory() as repo:
        try:
            ds.grant(repo,'scope','jiwon',skill_env='',manifest=[{'tool':'Bash','resource':'x','meta':meta}])
            disk = ds.load_state(repo)
            reloaded = disk['manifest'][0]['meta']
            print(label, 'ACCEPTED', 'reload_type=', type(reloaded).__name__, 'equal=', reloaded==meta, 'same_python_type=', type(reloaded)==type(meta))
        except ds.MalformedManifestError as e:
            print(label, 'REJECTED:', str(e)[:55])

try_grant('bytes_value', b'hello')
try_grant('set_value', {1,2,3})
try_grant('tuple_value', (1,2,3))
try_grant('custom_object', Custom())
try_grant('dict_subclass', MyDict({'a':1}))
try_grant('str_subclass', MyStr('hello'))
try_grant('int_enum', IntColor.RED)
"` (this session, this turn, at commit `39c3240f`) — result:
```
bytes_value REJECTED: manifest entry 0['meta'] is a bytes, which
set_value REJECTED: manifest entry 0['meta'] is a set, which
tuple_value REJECTED: manifest entry 0['meta'] is a tuple, which
custom_object REJECTED: manifest entry 0['meta'] is a Custom, which
dict_subclass ACCEPTED reload_type= dict equal= True same_python_type= False
str_subclass ACCEPTED reload_type= str equal= True same_python_type= False
int_enum ACCEPTED reload_type= int equal= True same_python_type= False
```

For the three subclass cases — `dict` subclass, `str` subclass, `IntEnum`
— the code correctly *accepts* the value (unchanged and correct, matching
the ninth verification's own grading of these three as Present), but each
`same_python_type` reads `False` in the result above: the round trip does
NOT hand back "the SAME type it started as" for any of them (`MyDict`
reloads as plain `dict`, `MyStr` as plain `str`, `IntColor.RED` as plain
`int`), yet `equal` reads `True` for all three. Taken literally, the
comment's own stated criterion ("hands back as the SAME type it started
as") would predict these three should be rejected the same way tuple is —
none of the four round-trips to its own starting type — but only tuple is
actually rejected, because the code's real discriminator is not type
identity but equality preservation under `isinstance`-based admission
into one of the seven base categories: `dict`/`str`/`int` equality is
structural/value-based and does not require the comparison partner to be
the exact original subtype, while `tuple`'s own equality specifically
requires the other operand to also be a `tuple` (so `(1,2,3) !=
[1,2,3]`), which is why tuple alone fails and the three subclasses do not.
The ninth verification's own record already grounded the subclass
acceptance this same way ("the allowlist is `isinstance`-based ... rather
than `type()`-identity"); round 8's replacement comment does not carry
that framing forward and instead states a same-type criterion that is
accurate for tuple and for non-subclass instances of the other six types,
but is not literally accurate for the subclass cases the code also has to
get right.

**Why Surface and not Incorrect:** the code's actual accept/reject
behavior for all seven exercised types is unchanged from the ninth
verification's own findings and is not mis-described in any way that
would mislead an edit to break something a test would not catch — the
`isinstance` gate itself, not the English sentence describing it, is what
the test suite pins. Confirmed by mutation: widened the container check
from `isinstance(value, (dict, list))` to `isinstance(value, (dict, list,
tuple))` in a scratch copy at `/tmp/pr3087-verify10/delegation_state.py`
(reverted immediately after), then re-ran the hostile-shape tests.

derived: `python3 -m pytest test/test_delegation_state.py -k "test_tuple_is_rejected_even_though_json_dumps_accepts_it or HostileManifestShapeTest" -q` (this session, this turn, against the mutated copy of the untracked-in-this-checkout, PR #3087-only `test/test_delegation_state.py`) — result: `3 failed, 2 passed` — `test_grant_refuses_every_hostile_shape_without_crashing_or_writing`, `test_tuple_is_rejected_even_though_json_dumps_accepts_it`, and `test_is_covered_rejects_every_hostile_shape_with_a_reported_stderr_line` all fail once tuple is admitted, confirming the test suite (not the comment) is what actually pins the reject-tuple behavior. Reverted via `cp /tmp/delegation_state.py.bak delegation_state.py`, then confirmed clean via `git diff --stat delegation_state.py` (this session, this turn) — no output, i.e. zero lines changed, before continuing.

Test-depth-audit on the new test (`test_tuple_is_rejected_even_though_json_dumps_accepts_it`, in the untracked-in-this-checkout, PR #3087-only `test/test_delegation_state.py:943-966`): **Genuine Assertion** — asserts the `json.dumps()` premise, asserts round-trip inequality (`assertNotEqual`), asserts `MalformedManifestError` is raised, asserts `load_state()` returns `None`; confirmed non-decorative by the mutation immediately above (the test fails when the code it guards is weakened).

### Item 2 — the 22-vs-20 pre-existing-failure reconciliation: **Present**

Round 8 reconciled the discrepancy at commit `3312d19c` (the tip
immediately before round seven's own fix). Independently re-derived here
at `39c3240f` itself — the actual commit under review this round, not an
ancestor.

derived: `python3 -m pytest test/ tests/ -q` (this session, this turn, at commit `39c3240f`) — result: `20 failed, 822 passed, 3 xfailed` — matches round 8's own claimed count at this same commit.

derived: `python3 -m pytest -q -m "not slow"` (no path arguments, full default collection; this session, this turn, at commit `39c3240f`) — result: `22 failed, 1039 passed, 3 xfailed`.

derived: extracted and sorted the `FAILED`-line sets from both runs above into two files, then `comm -13 scoped20.txt full22.txt` and `comm -23 scoped20.txt full22.txt` (this session, this turn) — result: `comm -23` (lines only in the 20-scoped set) is empty, confirming the 20-set is a strict subset; `comm -13` (lines only in the full-collection set) returns exactly two names:
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py::MacosBash32CompatTest::test_current_head_is_clean
```
— the identical two names round 8's own record cites, there derived only at `3312d19c`; here independently re-derived directly at this round's own tip `39c3240f`.

Confirmed neither extra failure is introduced by any round of this issue.
Both live in directories that no change to `delegation_state.py` or to
the untracked-in-this-checkout, PR #3087-only `test/test_delegation_state.py`
ever touches.

derived: `git log --oneline -1 -- harness/fixture-operator-experience/test_flow.py on-the-record/checks/test_macos_bash32_compat.py` (this session, this turn) — result: last touched by `71167c3a` (issue #2924, macOS/bash-3.2 compat check) and `7742c225` (issue #1006, operator-experience layer) — neither commit belongs to issue #3061 or any of its round commits (`3312d19c`, `fdb57899`, `39c3240f`).

derived: `git fetch origin main -q && python3 -m pytest -q -m "not slow" harness/fixture-operator-experience/test_flow.py on-the-record/checks/test_macos_bash32_compat.py` (this session, this turn, run from the `/tmp/pr3087-verify10` worktree against `origin/main`) — result: `2 failed, 6 passed` — both fail identically on plain `origin/main`, for reasons unrelated to delegation state: the macOS check reports unrelated `scripts/issue-3041/` bash-3.2 guard violations and an unrelated `/proc` dependency in `amendment_channel.py`. These are pre-existing, environment-level failures, not this issue's drift.

Twenty-two equals twenty plus the two extra names above, for different
pytest scopes, at the same commit — confirmed independently at this
round's own tip. Nothing shrank between rounds; the count difference was
always a scope difference (bare `pytest -q` versus `pytest test/ tests/
-q`), never a fixed or reintroduced failure.

### Item 3 — stepping back: does the orchestrator now stop asking for authority it was already granted?

**The four historical cases: Present, re-confirmed with an independently authored manifest.**

The four historical cases (PR #3097 "dropping the legacy table," PR #3102
"deleting the customer table," PR #3107 "the irreversible prod deploy,"
PR #3122 "the prod secret rotation" — `RegressionFailureCasesTest` in the
untracked-in-this-checkout, PR #3087-only `test/test_delegation_state.py:340-420`)
are the four real asks a now-deleted lexical classifier used to
misclassify as redundant across earlier verification rounds of this issue
— each is actually a genuine, irreversible, undelegated escalation that
must still stop, per the issue's own must-not clause ("do not suppress
the orchestrator's genuine escalations"). A fifth-round verification (the
fifth independent verification of this seam) already re-derived these as
Present with its own manifest; re-derived again here with a third,
independently authored manifest — routine dev-workflow grants (`git *`,
`gh *`, `pytest *`, `npm *`, `Edit`/`Write`/`Read` `*`), none of which
cover a raw `psql`/`deploy-prod.sh`/`rotate-prod-secrets.sh` invocation —
at this round's own tip, `39c3240f`.

derived: constructed synthetic session-log events for each of the four asks (the verbatim ask text plus the actual destructive command as the next `tool_use` event) against the manifest above, then ran both `ds.is_covered()` directly and `ds.audit()` over the synthetic transcript (this session, this turn, at commit `39c3240f`) — result:
```
PR#3097 drop legacy table           audit_flagged=0  is_covered=False
PR#3102 delete customer table       audit_flagged=0  is_covered=False
PR#3107 prod deploy                 audit_flagged=0  is_covered=False
PR#3122 prod secret rotation        audit_flagged=0  is_covered=False
```
All four are correctly still uncovered (`is_covered=False`) and correctly
not misreported as an avoidable stop (`audit_flagged=0`) — for these four
cases specifically, the delegated operator is not being made to repeat
"keep going" to re-affirm authority already granted, because none of
these four actions was ever covered by any manifest a real operator would
plausibly write; the seam correctly still requires a fresh decision here,
which is the behavior the issue explicitly protects, not the pattern it
targets.

**The acceptance criteria themselves, re-run at this round's tip:**

derived: `python3 spawn.py delegation-state --repo .` (this session, this turn, at `39c3240f`) — result: `no standing delegation recorded` — the empty state reports none rather than erroring, matching the issue's own stated empty-state requirement.

derived: `python3 spawn.py delegation-state --audit --since 2026-09-02 --repo .` (this session, this turn, at `39c3240f`) — result: `0 turn(s) since 2026-09-02 asked for authority a recorded delegation already covered (scanned 0 session log(s)).`

derived: `grep -rn 'no-op wake\|advanced nothing\|idle-wake' watchdog.py on-the-record/monitors/` (this session, this turn, at `39c3240f`) — result: multiple hits, including `watchdog.py:1989-1992`'s own report comment (pointing at `poll_heartbeat_delta.py::format_wake_outcomes`, a function present at `39c3240f` but untracked in this record's own checkout, per the "What was done" section above) and `on-the-record/monitors/test_wake_outcomes.py` (also untracked in this checkout, PR #3087-only, per the "What was done" section above), confirming the idle-wake/no-op-wake distinction exists in both the producer and its test at this commit.

All three acceptance checks named in the issue pass exactly as specified,
re-run directly at this round's tip rather than assumed from round 8's or
the ninth verification's own record.

**But the deeper question the issue title asks — does an operator who
already granted authority stop having to repeat "keep going" — is only
partly answered by what is actually wired up.** Checked what, besides
`delegation_state.py` itself and its own test file, references it at all.

derived: `grep -rln "delegation_state\|delegation-state" --include="*.py" --include="*.md" .` (this session, this turn, run from the repo root of the `/tmp/pr3087-verify10` worktree at `39c3240f`) — result: exactly `delegation_state.py`, `spawn.py`, the untracked-in-this-checkout, PR #3087-only `test/test_delegation_state.py`, and this issue's own round-8 record — zero hits in `on-the-record/hooks/`, `on-the-record/directive/`, `watchdog.py`, or any settings/hooks-wiring file.

derived: `grep -n "delegation_state\|delegation-state" spawn.py` (this session, this turn) — result: one `import delegation_state` plus the `delegation-state` CLI subcommand's own argparse help text and dispatch at `spawn.py:2757-2786` — a subcommand an operator or a session must explicitly invoke, not something consulted automatically before the orchestrator emits a stop.

derived: read `on-the-record/directive/delegation-loops.md` (the always-on directive text the issue itself quotes as already present and already insufficient — "YOUR GOAL LOOP ... continue until the goal is reached or you are genuinely blocked on the user") and `on-the-record/hooks/delegation-post-gate.sh` (issue #707's unrelated self-approval-citation gate) in full (this session, this turn) — neither file references `delegation_state.py`, `is_covered()`, or the manifest mechanism anywhere.

canonical: `gh issue view 3061 --repo tokenmaxxxer/on-the-record` output, acceptance-bullet section, read in full this session, this turn — the second bullet's own wording is "detectable after the fact," not "prevented live."

So PR #3087 gives the orchestrator machinery to record standing delegation
as durable, read-back-able state, and to detect — after the fact, via
`--audit` — that a given stop was redundant against a recorded manifest.
It does not wire `is_covered()`/`describe()` into any live pre-ask gate or
per-turn context injection that would keep the orchestrator from asking
about a covered action in the first place. Concretely: if an operator
grants `git *` and the orchestrator's very next planned action is a `git
commit`, nothing in this diff stops the orchestrator from still asking
about it in the moment — `is_covered()` would correctly return `True` if
queried, and a later `--audit` run would correctly flag that stop as
avoidable, but nothing queries it live today. This is not graded
Incorrect against PR #3087, because the acceptance criteria this round
was handed literally ask for after-the-fact detectability (canonical
citation above), not live prevention, and after-the-fact detectability is
what exists and passes above. It is the honest answer to this round's own
step-back question: for the pattern the issue opened over — an operator
delegating and still having to repeat "keep going" turn after turn — this
seam makes the pattern countable and auditable; it does not yet prevent
it in the moment. Closing that remaining gap, if it is to be closed, is
further work this commit does not contain.

## Why

canonical: the reproductions in Items 1-3 above (this record's own
`derived:`-tagged commands and their results, all executed at this
round's own tip `39c3240f` this session, this turn, unless a specific
ancestor commit is named for comparison).

Item 1's method: read round 8's stated rule, then test it against every
concrete type the ninth verification exercised, rather than only the one
type round 8's own commit message names. This is the same method the
ninth verification itself used against the round-seven record's stated
rule, and is what surfaced the subclass gap here — testing all seven
types instead of re-running the existing suite is what found the
imprecision.

Item 2's method: re-derive the reconciliation at the actual commit under
review (`39c3240f`) rather than accepting round 8's derivation at an
ancestor commit as sufficient — a scope-difference explanation that holds
at one commit but not at the tip under review would itself be a finding;
it holds at both, confirmed independently at both.

Item 3's method: take the round's own instruction literally — express
each historical case against a manifest this session authored itself, not
the shipped fixture — and separately check what the delivered diff
actually wires into live orchestrator behavior versus what it only makes
available via explicit CLI invocation, grounded in the `grep`/read
reproductions above rather than an assumption either way.

## Open findings

None Incorrect. One Surface-graded finding:

- Finding (Surface, Item 1). Round 8's corrected module comment states the
  allowlist rule as round-tripping to "the SAME type it started as," which
  is accurate for tuple (the case it was written to fix) and for
  non-subclass instances of the other six admitted types, but is not
  literally true for the three subclass cases (dict subclass, str
  subclass, IntEnum) the code also correctly accepts — those round-trip to
  their plain base type, not their original subclass, yet are accepted
  because the real rule is `isinstance`-based structural admission with
  equality, not type identity, preserved.
  derived: the type-and-equality probe and the mutation check in Item 1
  above (this session, this turn, at `39c3240f`) are this finding's own
  evidence — `same_python_type=False`/`equal=True` for all three subclass
  cases, and three tests failing when tuple is admitted, confirming the
  `isinstance` gate (not the comment's wording) is what the suite pins.
  No functional defect. Resolution path, if a future round closes it: fold
  in the ninth verification's own more precise framing ("`isinstance`-based
  ... rather than `type()`-identity") alongside the tuple explanation
  already present, or narrow the sentence to scope it explicitly to
  non-subclass values.

And one scoping observation, not a defect against this round's own scope:

- Observation (Item 3). No hook, directive, or per-turn context injection
  consults `delegation_state.py` anywhere outside its own module, its own
  test file, and `spawn.py`'s CLI dispatch.
  derived: the three `grep`/read reproductions in Item 3 above (this
  session, this turn, at `39c3240f`) are this observation's own evidence
  — zero hits outside those three files, and neither
  `on-the-record/directive/delegation-loops.md` nor
  `on-the-record/hooks/delegation-post-gate.sh` references the mechanism.
  The seam is detection/bookkeeping only, matching the issue's own
  acceptance-bullet wording exactly (canonical citation, Item 3 above),
  but leaving the live "operator still has to repeat keep going for a
  covered action in the moment" pattern unaddressed by this PR alone. Not
  a finding against PR #3087's stated acceptance criteria; recorded
  because this round's own step-back question asked for the honest answer
  beyond the acceptance checks' pass/fail.

## What did not work

Nothing attempted in this round was abandoned or reverted, with one
deliberate, reverted exception used to verify the new tuple regression
test is genuine rather than decorative:

derived: widened `delegation_state.py`'s container `isinstance` check
from `(dict, list)` to `(dict, list, tuple)` in the `/tmp/pr3087-verify10`
scratch copy, re-ran `python3 -m pytest test/test_delegation_state.py -k
"test_tuple_is_rejected_even_though_json_dumps_accepts_it or
HostileManifestShapeTest" -q` (this session, this turn) — result: `3
failed, 2 passed`, confirming the mutation breaks the guard as expected —
then reverted via `cp /tmp/delegation_state.py.bak delegation_state.py`
and confirmed a clean diff via `git diff --stat delegation_state.py`
(this session, this turn) — no output, zero lines changed — before
continuing. An intentional, temporary probe, not a dead end.

## Next steps

`loop_state: landed` for this verification round: the findings above are
reported, not fixed, per this protocol's no-merge/no-edit-to-PR-#3087
instruction.

derived: this round's three own acceptance-criteria commands, re-run at
`39c3240f` (this session, this turn): `python3 spawn.py delegation-state
--repo .` → `no standing delegation recorded`; `python3 spawn.py
delegation-state --audit --since 2026-09-02 --repo .` → `0 turn(s) ...`;
`grep -rn 'no-op wake\|advanced nothing\|idle-wake' watchdog.py
on-the-record/monitors/` → multiple hits (full results in Item 3 above)
— all three pass exactly as specified in the issue.

derived: `python3 -m pytest test/ tests/ -q` at `39c3240f` (this session,
this turn) → `20 failed, 822 passed, 3 xfailed`; `python3 -m pytest -q -m
"not slow"` at `39c3240f` (this session, this turn) → `22 failed, 1039
passed, 3 xfailed` — both re-confirmed directly in this section as the
basis for Item 2's Present grade, not merely cross-referenced.

Nothing in this round's own scope graded Incorrect: Item 1 graded Surface
(a documentation-precision gap, not a functional defect, confirmed by the
mutation check above), Item 2 graded Present (re-derived directly at this
round's own tip, commands repeated immediately above), Item 3's
four-historical-cases check graded Present (re-derived with an
independently authored manifest, `audit_flagged=0`/`is_covered=False`
across all four, per Item 3 above). On that basis, this specific
mechanism — `_check_no_surrogates()`'s type allowlist and its
now-corrected comment — has no further open Incorrect finding as of this
round, and a further round need not re-open the tuple allowlist itself
absent new evidence. The scoping observation in Item 3 (live pre-ask
wiring, versus after-the-fact detection) is a question about what issue
#3061 still needs beyond PR #3087, not a defect in PR #3087 itself — a
decision for the operator or orchestrator on whether a follow-up issue
should wire `is_covered()`/`describe()` into a live pre-ask check, which
is outside this record's own authority to open.

skill-verdict: adversarial-review — applied: invoked; structured this
session as builder-blind reproduction against round 8's delivered code
and its own stated comment, independently authoring test manifests and
attacking the comment's literal claim against all seven types the ninth
verification exercised rather than accepting round 8's own narration or
re-running its existing test suite — the Item 1 Surface finding and the
Item 3 live-wiring observation are both direct products of that method.
skill-verdict: test-depth-audit — applied: invoked; classified the new
`test_tuple_is_rejected_even_though_json_dumps_accepts_it` (untracked in
this checkout, PR #3087-only `test/test_delegation_state.py:943-966`) as
Genuine Assertion and confirmed non-decorative via mutation (widening the
container `isinstance` check to admit tuple breaks three of five
`HostileManifestShapeTest` methods, including this one — derived, Item 1
above).
skill-verdict: silent-failure-audit — applied: invoked; re-confirmed the
tuple rejection's write path (uncaught `MalformedManifestError`
propagation out of `grant()`) and read path (`_safe_manifest()` catch →
stderr line → fail-closed `[]`) both still classify Handled, not Silently
Absorbed, via the same `HostileManifestShapeTest` suite run this session
(Item 1 above); round 8's change was comment- and test-only, so no new
error-handling site exists to classify beyond re-confirming the existing
one still holds.
