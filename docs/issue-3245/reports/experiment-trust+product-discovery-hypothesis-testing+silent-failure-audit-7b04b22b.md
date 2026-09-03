---
issue: 3245
role: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b
author: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b
skills: experiment-trust (skill-repository(c05de12)), product-discovery-hypothesis-testing (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: done
type: measurement
breaking: false
verdict: 0 of the registered n>=5 pairs were scored this run. The
  trust-rooted launcher (prepare_arms.py + run_pair.py) is built and
  unit-tested. The one real dispatch attempted (pair 01-study-groups,
  issues #19/#20) failed on both arms before either session did task
  work -- a freshly-measured, environment-wide CLI/hook regression
  (spawn.py's own doctor probe), not the on/off manipulation, is the
  cause. See "Reported results" and "Open findings" below.
upstream:
  - path: scripts/consumer-path/prepare_arms.py (PR #3185, issue #3183)
    sha: same-commit
  - path: docs/issue-3183/decisions/instrument-limitations.md
    sha: same-commit
  - path: scripts/issue-3127/run_consumer_pair.py (issue #3127)
    sha: same-commit
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: same-commit
---

# issue-3245 — experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b record

## What was done

canonical: this session's own tool transcript (dry-run + persisted-manifest + verify_manipulation.py invocations against `scripts/consumer-path/prepare_arms.py` and `scripts/consumer-path/verify_manipulation.py`)

1. Verified the apparatus end to end before any dispatch (issue's Step
   1).
   derived: `python3 scripts/consumer-path/prepare_arms.py --dry-run --skill-name adversarial-review`
   ```
   "arm": "off", "skills_root_exists": false, "file_count": 0
   "arm": "on", skill_files: 9 real, hashed entries from $MUSTER_SKILL_REGISTRY_ROOT
   "argv_identical_across_arms": true
   ```
   derived: `python3 scripts/consumer-path/verify_manipulation.py --manifest <persisted manifest> --transport <nonexistent>`
   ```
   {
     "manipulation_held": false,
     "pair_excluded": true,
     "reason": "transport record not found at ... -- pair excluded ..."
   }
   ```
   exit=1
   These reproduce PR #3185's own trust-root claims live rather than
   re-asserting the docstring: the off arm's skills root is a path that
   does not exist (not a stub), and `verify_manipulation.py` fails
   closed with no transport record on disk.

2. Made the pinning decision before running anything (issue's Step 2),
   written to `docs/issue-3245/decisions/pinning-and-sample-size.md`:
   pin the skill set (`product-discovery-hypothesis-preregistration`,
   continuing `docs/issue-3127/decisions/pre-registration.md`'s own
   choice, not re-picked) identically across both arms of a pair. This
   answers "what is this skill worth once the orchestrator has already
   selected it," not "what does today's system deliver end-to-end
   including its own selection noise" -- the latter is issue #3230's
   measurement, not this one. Also extends the registered sample size
   from n=2 to n>=5, stated in that same file before any pair under
   this run was scored.

3. Built `scripts/consumer-path/run_pair.py`: combines
   `prepare_arms.py`'s manifest (fresh, isolated HOME per arm; off arm's
   skills root never created) with `scripts/issue-3127/
   run_consumer_pair.py`'s dispatch mechanics (lint -> dispatch ->
   blocking `watch --follow`) and H1/H2 machinery
   (`collect_skill_invocation`, `gate_pair_on_h1`, `evaluate_pair_blind`,
   `scrub_skill_slugs`), reused by import. The off arm's `--skills`
   value carries the `skill-repo:` source qualifier (issue #2579,
   `scripts/consumer-path/run_pair.py::_skills_argument()`). The
   transport record is written to disk before either arm's `Popen()`
   (`run_pair.py::run_pair()`, transport write precedes the
   `execute_arm()` loop). Strips `CLAUDE_*`/`MUSTER_*`/`TOKENMAXXXER_*`
   and `CORE_BUILD_NOW` from the base env before layering each arm's
   override on top (`run_pair.py::_clean_base_env()`), so this
   orchestrating session's own build-now bypass cannot leak into a
   spawned arm.

4. Extended `verify_manipulation.py` with `--report` (acceptance check
   3): scans a root directory for every `manifest.json`, verifies each
   against its sibling `transport.json`.
   derived: `python3 scripts/consumer-path/verify_manipulation.py --report --root <empty dir>`
   ```
   {"status": "no-manifests-found", "pairs_found": 0, ...}
   ```
   exit=1

5. Wrote `tests/test_issue_3245_pair_results.py`.
   derived: `python3 -m pytest tests/test_issue_3245_pair_results.py -q`
   ```
   14 passed in 0.90s
   ```

6. Attempted one real pair (issue's Step 3): `01-study-groups` against
   the target repo's issues #19 (on) / #20 (off). See "What did not
   work" for the reproduced outcome.

7. Drafted (did not file) the three additional pairs' task text and
   issue bodies needed to reach n>=5, in `docs/issue-3245/decisions/
   drafted-followup-issues.md`.
   canonical: `runs/rulebooks/tokenmaxxxer-core/core/hooks/gh-guard.sh` lines 13-16, `gates/forbidden_action_rule.py` lines 7-9
   ```
   # Denied in role sessions (CLAUDE_SKILL set):
   #   gh issue create / close / reopen / edit      (user-only backlog)
   ```
   ```
   refuses it (contract v3 s8/s9: issues are the user's requirement backlog,
   user-authored only). The bullet was unsatisfiable by construction: the
   ```
   This session's own `CLAUDE_SKILL` env var is set (checked via
   `printenv` this session), so the same refusal applies here; this
   session did not attempt `gh issue create` given this reproducible,
   documented rule.

## Why

canonical: `gh issue view 3245` body, read this session and quoted in this session's own transcript

The issue's own text ("a five-pair run is expensive and a design error
found at pair five costs everything... report at each step rather than
only at the end") asks for staged verification rather than one
end-of-run claim. Verifying the trust root, recording the pinning
decision, and running exactly one real pair before attempting more
follows that structure directly. It is also what the evidence supported:
the first real pair surfaced a dispatch failure common to both arms (see
"What did not work"), for a cause unrelated to the on/off manipulation,
that would recur identically on every subsequent pair. Running four more
pairs before checking the first would have spent real target-repo
dispatches to re-learn the same fact four more times.

## What did not work

canonical: `docs/issue-3245/_assets/01-study-groups/result.json` (this session's own dispatch attempt, written by `run_pair.py` this run)

- The real dispatch of pair `01-study-groups` (issues #19/#20) failed on
  both arms before either session did any task work.
  ```
  "on":  {"status": "dispatch-failed", "dispatch_returncode": 1}
  "off": {"status": "dispatch-failed", "dispatch_returncode": 1}
  ```
  Both arms' `dispatch_stderr` (same file) carries two distinct signals:
  (a) a warning that issues #19/#20's own `## Acceptance` sections lack
  the `provenance:`/`empty state:` lines `on-the-record/directive/
  acceptance-format.md` requires (a pre-existing defect in those
  already-filed bodies, not written by this session); and (b) the
  actual blocking failure, quoted from `pipeline.py` (read this
  session):
  ```python
      if not ok.is_file() or ok.read_text().strip() != v:
          if version is not None:
              sys.exit(
                  f"이 CLI({v})에서 훅이 headless 로 도는 것을 아직 실측하지 않았다.\n"
  ```
  and `spawn.py` (read this session):
  ```python
      if fired_ups and fired_pre:
          d = ROOT / "runs"
          d.mkdir(exist_ok=True)
          (d / "doctor-ok").write_text(v)
  ```
  This session's actual dispatch triggered `require_doctor()`
  (`pipeline.py:524`), which ran a live hook-firing probe
  (`spawn.py:doctor()`, `spawn.py:2175-2219`, a real haiku-model `claude
  -p` session) against the installed CLI and found `UserPromptSubmit`/
  `PreToolUse` hooks did not fire headless -- the probe's own
  `dispatch_stderr` text (same `result.json`) reads "훅이 headless 에서
  발화하지 않는다" (hooks do not fire headless). `doctor()` fails closed
  by design in exactly this case: a CLI version under which plugin
  hooks stay silent would make every gate this repo depends on silently
  vanish in a spawned session.
  Consequence: this is not specific to issue #19/#20, the
  `product-discovery-hypothesis-preregistration` skill, or the on/off
  manipulation -- it blocks every `spawn.py --skills` dispatch on this
  machine, for any issue/skill/repo, until the CLI/hook mismatch is
  resolved. No further real dispatch was attempted after this was
  confirmed once, since a repeat would fail identically for the same
  environment-level reason.
- Reusing issues #19/#20's pre-existing PRs (target repo PRs #23, #25,
  seen via `gh pr list -R JiwonJung94/study-companion` this session) as
  an already-scored pair was considered and rejected: those PRs predate
  `prepare_arms.py` (PR #3185) and have no manifest+transport this
  launcher wrote before their dispatch, so `verify_manipulation.py`
  would correctly exclude them (no manifest on record) -- constructing
  one after the fact would misrepresent what was actually checked at
  dispatch time.

## Upstream basis

canonical: this session's own `Read` tool calls on `pipeline.py` and `spawn.py`
derived: `python3 scripts/consumer-path/prepare_arms.py --dry-run --skill-name adversarial-review`
```
"arm": "off", "skills_root_exists": false, "file_count": 0
"arm": "on", skill_files: 9 real, hashed entries from $MUSTER_SKILL_REGISTRY_ROOT
```

- `scripts/consumer-path/prepare_arms.py` / `verify_manipulation.py`
  (PR #3185, issue #3183) -- re-verified live this session with the
  command quoted immediately above, not taken from the docstring alone.
- `docs/issue-3183/decisions/instrument-limitations.md` §3 -- the
  "minimum of five paired trials" this issue's own registered
  sample-size floor is drawn from.
- `scripts/issue-3127/run_consumer_pair.py` and `docs/issue-3127/
  decisions/pre-registration.md` -- the dispatch/H1/H2 machinery reused
  by import, and the pre-registered metric/threshold/guardrail/skill
  choice this run amends (sample size only).
- `gates/forbidden_action_rule.py`, `runs/rulebooks/tokenmaxxxer-core/
  core/hooks/gh-guard.sh` -- the mechanically-enforced reason this
  session could not file the drafted follow-up issues itself.
- `pipeline.py:524` (`require_doctor`), `spawn.py:2175-2219`
  (`doctor()`) -- their text is quoted directly in "What did not work",
  not inferred from the stderr message alone.

## Reported results (per pair and in aggregate)

canonical: `docs/issue-3245/_assets/01-study-groups/result.json`, `gh pr list -R JiwonJung94/study-companion` (both read this session)

| Pair | On issue | Off issue | Manipulation check | H1 (skill invoked) | H2 (blind score) | Verification rounds | Wall clock to PR open | Cost | Scored? |
|---|---|---|---|---|---|---|---|---|---|
| 01-study-groups | #19 | #20 | held (`manipulation_check.manipulation_held: true`) | not measured -- neither arm produced a session log (`dispatch-failed`) | not computed -- H1 gate never reached (`h1: null`) | not measured | not measured | not measured | No -- excluded (`exclusion_reason` in `result.json`) |
| 02-onboarding-experiment | #21 | #22 | not attempted | -- | -- | -- | -- | -- | No -- not attempted this session |
| pairs 3-5 | not filed | not filed | not attempted | -- | -- | -- | -- | -- | No -- issues not filed (gh-guard) |

Aggregate: 0 of the registered n>=5 pairs scored this run.
`01-study-groups`'s pre-dispatch manipulation check held clean
(`docs/issue-3245/_assets/01-study-groups/manifest.json` and its sibling
`docs/issue-3245/_assets/01-study-groups/transport.json`, cross-checked
by `verify_manipulation.py`), but the pair is excluded from H2 per
`result.json`'s own `exclusion_reason` field: "at least one arm did not
reach watched-to-completion (on='dispatch-failed',
off='dispatch-failed')". A clean pre-dispatch manipulation check is a
narrower claim than a scored pair, and this record does not conflate the
two. No pair in this run is reported as scored without a passing
manipulation check recorded against it (the acceptance check's own
must-not) -- because no pair is reported as scored at all this run.

## Does the difference clear the pre-registered threshold?

acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py -q` -- result:
```
14 passed in 0.90s
```
acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py -q` -- result:
```
18 passed in 0.85s
```
acceptance: `python3 scripts/consumer-path/verify_manipulation.py --report` -- result:
```
{"pairs_found": 1, "pairs_included": ["...01-study-groups"], "pairs_excluded": [], "status": "reported"}
```
(exit 0 -- one manifest+transport pair found and its manipulation check
held; this is the launcher-owned trust-root check only, a different,
narrower claim from "scored," per "Reported results" above.)

Not answerable this run whether skills-on clears
`docs/issue-3127/decisions/pre-registration.md`'s decision rule (b)
(skills-on better if it wins in >=3 pairs and the combined margin is
>=3): that rule needs H2 scores from completed pairs, and the table
above shows none exist. This is not the "indistinguishable" outcome the
pre-registration's power statement describes (that requires the rule to
have been applied to real scores and land inside the ±2 band) -- it is
the narrower fact that the instrument producing a score never completed
a run this session. No null is asserted where no data was collected.

## Follow-on question: can this run's artifacts distinguish "opened but not followed" from "followed but unhelpful"?

canonical: `docs/issue-3245/_assets/01-study-groups/result.json`
```
"excluded_from_h2": true,
"exclusion_reason": "at least one arm did not reach watched-to-completion (on='dispatch-failed', off='dispatch-failed')"
```

No, not from this run's data, and the reason is mechanical rather than a
design gap: `collect_skill_invocation()` (`scripts/issue-3127/
run_consumer_pair.py`, read this session) already computes exactly this
distinction for a pair that reaches watched-to-completion -- it parses
`<workspace>.session.<ts>.<pid>.log` for a real `Skill` `tool_use`
entry, so `mounted_but_not_invoked` (opened but not followed) is already
a named field distinct from `invoked` (opened and followed, whose
quality is then what H2's blind score speaks to -- followed but
unhelpful would show as `invoked: true` alongside a losing H2 score, via
`gate_pair_on_h1()`). What this run lacks is not that metric, it is a
pair that reached the state the metric parses: the codefence above shows
both arms status `dispatch-failed`, so neither `claude -p` subprocess
got past `spawn.py`'s own preflight and no session log exists for
either arm. What would be needed: at least one pair reaching
`watched-to-completion` on both arms, which requires the CLI/hook
regression in "What did not work" to be resolved first; once that
holds, the machinery built this session answers the distinguishability
question without further instrumentation work.

## Open findings

1. CLI 2.1.259 does not fire plugin hooks in headless (`claude -p`)
   mode on this machine -- this session's own live `spawn.py doctor`
   probe, triggered during the `01-study-groups` dispatch attempt (see
   "What did not work" for the file:line citations). Blocks every
   `spawn.py --skills` dispatch repo-wide, not only this issue's
   measurement. This session cannot file a new issue (`gh-guard`);
   named here for the orchestrator/human to triage.
2. Issues #19 and #20's `## Acceptance` sections do not conform to
   `on-the-record/directive/acceptance-format.md` (missing
   `provenance:`/`empty state:` lines), surfaced as a warning in the
   same dispatch attempt, independent of finding 1. This session cannot
   edit them (`gh-guard` also refuses `gh issue edit` for role
   sessions, per the same hook lines cited in "What was done" §7).
3. Six follow-up issues (pairs 3-5, on+off each) are drafted but not
   filed -- `docs/issue-3245/decisions/drafted-followup-issues.md` has
   the bodies and the filing note.
4. The registered n>=5 floor (`docs/issue-3245/decisions/
   pinning-and-sample-size.md`) is unmet, at 0 scored this run, blocked
   on findings 1-3 in that order.

## Next steps

acceptance: `python3 -m pytest tests/test_issue_3245_pair_results.py -q` -- result:
```
14 passed in 0.90s
```
acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py -q` -- result:
```
18 passed in 0.85s
```

No further action from this session on the acceptance checks -- all
three run clean against the current tree (the third,
`verify_manipulation.py --report`, is quoted in "Does the difference
clear the pre-registered threshold?" above). The next actionable step
belongs to whoever can address finding 1 (this session has no path to a
different CLI version) and then re-attempt `01-study-groups`/
`02-onboarding-experiment`, after fixing issues #19/#20's Acceptance
sections per finding 2, and separately file the drafted pairs 3-5 per
finding 3.

## Skill verdicts

canonical: `scripts/consumer-path/run_pair.py` (this session's own edits, quoted below)
```python
                skipped_malformed_lines += 1
    except prepare_arms.ArmPreparationError as exc:
```

- skill-verdict: silent-failure-audit — applied: invoked; audited
  `scripts/consumer-path/run_pair.py`'s fallible operations
  (subprocess dispatch/lint/watch, `gh pr view`, `runs/ledger.jsonl`
  parsing, `prepare_arms.build_manifest()`). Found and fixed the two
  sites quoted immediately above: `collect_cost()` silently dropped
  malformed ledger lines with a bare `continue` (now counted in a
  returned `skipped_malformed_lines` field), and `run_pair()` called
  `prepare_arms.build_manifest()` unguarded (an `ArmPreparationError`
  would have crashed with a bare traceback instead of the same clean
  excluded-with-a-reason shape every other failure path in the module
  returns) -- now wrapped.
- skill-verdict: experiment-trust — applied: invoked; canonical:
  `docs/issue-3127/decisions/pre-registration.md`'s own "Scope note"
  section (read this session) already states this is "an offline,
  small-n (2-4) paired comparison with pre-assigned conditions... not
  random assignment of live production traffic to variants" -- Step 1's
  scope gate routes away from SRM/A-A machinery on that same basis, and
  none is invoked here. The Twyman's-law/base-rate discipline is
  applied narrowly: no null result is asserted where no data was
  collected (see "Does the difference clear the pre-registered
  threshold?" above).
- skill-verdict: product-discovery-hypothesis-testing — not-applicable:
  this skill governs product-cycle's `docs/proposals/` specification
  state machine (scoping/researching/hypothesis-registered/measuring);
  this issue's pre-registration amendment
  (`docs/issue-3245/decisions/pinning-and-sample-size.md`) is a
  research-measurement pre-registration record, not a product-cycle
  spec file moving through that state machine.
- other mounted skills: not triggered.
