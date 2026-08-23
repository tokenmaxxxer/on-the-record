<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- LANDING REQUIREMENT-MET GRADE (issue #1651): as part of "verify it"
  above, before `gh pr merge`, spawn a builder-blind grader session —
  no access to the builder's context, given only the diff plus the
  issue's frozen `- check:` criteria (reuse the `adversarial-review`
  skill/consult independence pattern) — that runs
  `gates/requirement_met.py`. Its deterministic artifact-presence
  sub-check BLOCKS the merge; its semantic YES/NO/UNKNOWN verdict per
  criterion is recorded ADVISORY only and never blocks by itself.
- SCOPE ADHERENCE AT LANDING (issue #1658): also before `gh pr merge`,
  run `gates/scope_adherence.py` against the PR's touched files and the
  issue's `scope:` field. A declared-scope violation BLOCKS the merge;
  an undeclared scope is ADVISORY only (consumer repos with no `scope:`
  field proceed exactly as today).
- VERDICT-ASYMMETRY AT MERGE (issue #1669): before merging a PR on a
  reviewer verdict, run `gates/verdict_gate.py` `classify(verdict,
  merge_gate_result, tests_pass)`: CHANGES always respawns-with-findings;
  MERGE merges ONLY when `classify()` returns ALLOW_MERGE (the
  deterministic `merge_gate.py` `evaluate()` allows AND tests pass);
  every other outcome is HOLD — never merge on the LLM verdict alone. A
  correct MERGE blocked by a flaky deterministic gate surfaces to the
  human as a HOLD, not an auto-reject.
- STALE-REVERT AT MERGE (issue #1664): the same pre-merge step also runs
  `gates/stale_revert_guard.py` `classify()`/`check_pr()` — a PR whose
  merge would delete content base HEAD already has that was added after
  the PR's merge-base is REFUSED (rebase required), automating the
  PR#1662/#1675 catch the orchestrator previously had to make manually.
- ASSUMPTION-LEDGER INVENTED-CONFIRM AT INTAKE (issue #1665): before
  spawning a design-bearing issue, surface `gates/assumption_ledger.py`
  `invented_assumptions()` for that issue's body to the human for
  explicit confirmation. An unconfirmed `invented:` item BLOCKS the
  spawn — a mechanical issue (`assumptions-skip: mechanical`) proceeds
  unchanged.
