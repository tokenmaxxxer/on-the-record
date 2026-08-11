---
kind: scout-brief
---

# Scout brief — issue #895

Mode: parallel (3 WebSearch calls, one turn). Stages used: 1 (sweep
only). canonical: WebSearch results for "SWE-bench task category
taxonomy", "coding agent benchmark ambiguous underspecified requirement
clarifying question evaluation", "equivalence class boundary value
analysis test case design" (this session) — judge point 1 found no
exemplar mismatch and the category distribution + ambiguity taxonomy
below directly answer #895's open decision (which requirement types to
add), so a deepening round would not change the matrix; stopped at
saturation.

## Category must-bes (what a credible requirement-type matrix assumes)

- canonical: [Epoch AI, "What skills does SWE-bench Verified evaluate?"](https://epoch.ai/publications/what-skills-does-swe-bench-verified-evaluate)
  (WebSearch result, this session) — states the SWE-bench Verified task
  distribution is 87% bug fixes / 9% feature requests / 4%
  refactorings. A bug-fix-only matrix therefore covers only the majority
  slice, not "any requirement" — matching #895's own framing that a bug
  fix is "the easiest shape."
- canonical: [SWE-Bench Pro, arXiv:2509.16941](https://arxiv.org/pdf/2509.16941),
  [SWE Atlas, arXiv:2605.08366](https://arxiv.org/pdf/2605.08366),
  [SWE-Compass, arXiv:2511.05459](https://arxiv.org/pdf/2511.05459)
  (WebSearch results, this session) — each of these three later
  SWE-bench-family benchmarks widens category coverage beyond bug-fix:
  SWE-Bench Pro adds feature additions and refactors that create/alter
  classes and methods; SWE Atlas adds Q&A, test-writing, and refactoring
  categories; SWE-Compass broadens to refactoring, performance, and
  code-understanding, describing prior benchmarks as "heavily skewed
  toward Python-centric bug fixing."
- canonical: [ClarifyCodeBench, arXiv:2607.00711](https://arxiv.org/pdf/2607.00711),
  [ClarEval, arXiv:2603.00187](https://arxiv.org/html/2603.00187v1)
  (WebSearch results, this session) — both benchmarks treat ambiguity as
  its own evaluated axis, distinct from feature-add or bug-fix, because
  ambiguous requirements cause a large top-1-accuracy drop and models,
  per the source wording (not this document's own claim), "struggle to
  distinguish between well-specified and underspecified instructions."

## Performance axes the field competes on

1. Category coverage breadth (bugfix vs. feature vs. refactor vs.
   ambiguity vs. multi-file) — narrower benchmarks are explicitly framed
   as a known limitation by their own successors (same three sources
   above).
2. Ambiguity-type granularity — canonical:
   [ClarEval](https://arxiv.org/html/2603.00187v1) (WebSearch result,
   this session) splits ambiguity into missing-goal, missing-premises,
   and ambiguous-terminology as distinct injection types, not one
   "ambiguous" bucket.
3. Evaluation method matched to task type — canonical: [SWE
   Atlas](https://arxiv.org/pdf/2605.08366) (WebSearch result, this
   session) — per the source, a single binary exit-code-style
   test-execution metric does not fit every category, and it recommends
   a multifaceted per-category evaluation setup.

## Adopt / skip

- Adopt: cover the four widely-recognized categories (bugfix — already
  run in #893; feature-add; refactor/multi-file; ambiguous) as the
  field's own convergent minimum, matching #895's acceptance bar
  (feature-add, multi-file, failing-test-driven, ambiguous named as the
  floor). canonical: sources above (Epoch AI, SWE-Bench Pro, SWE Atlas,
  ClarEval).
- Adopt: give the ambiguous-requirement fixture a NAMED ambiguity type
  (missing-premise, from ClarEval's own taxonomy) rather than a vague
  "underspecified" label, since the harness's fixtures are single-scenario
  and a named type is more measurable than an unnamed one. canonical:
  [ClarEval](https://arxiv.org/html/2603.00187v1).
- Skip: reproducing SWE-Compass's full 8-type/10-language matrix or a
  sampled top-k statistical regime — northpole's harness (canonical:
  `docs/specs/northpole-harness.md` §1, read in full this session) is one
  fixture-target repo scored per-run against 8 fixed signals, not a
  large sampled benchmark; matching the field's full apparatus is out of
  proportion to #895's ask (extend the existing harness, not rebuild a
  benchmark suite).
- Skip: importing a distinct evaluation metric per category (SWE Atlas's
  own recommendation) — #895's acceptance bar is explicit that scoring
  stays on "the EXISTING signals" (canonical: issue #895 body, read in
  full this session), so each new fixture type is scored by the same 8
  signals already in `harness/signals.py` (canonical: `harness/signals.py`,
  read in full this session), not a new metric family.

## Segment fit

on-the-record's harness is a single hermetic fixture-target repo scored
by a small fixed signal table, not a large sampled leaderboard, so the
right reference class is "how many distinct requirement shapes does a
credible SWE-agent benchmark distinguish," not "how large a sample."

## Gap line

Current state (canonical: `harness/` directory listing + `docs/specs/
northpole-harness.md`, read in full this session) has exactly one
fixture (`fixture-target/`) and one requirement type
(`REPRESENTATIVE_REQUIREMENT` in `harness/driver.py`, a single-file bug
fix) — meeting none of the field's "more than one category" must-be yet.
The field's widening pattern (bugfix-only -> +feature -> +refactor ->
+ambiguity as a distinct axis) matches the direction #895 already names
in its own candidate list; this scout corroborates that list against the
external field and adds one refinement (name the ambiguity type) not
present in #895's issue text.

## Sources

- https://epoch.ai/publications/what-skills-does-swe-bench-verified-evaluate
- https://arxiv.org/pdf/2509.16941 (SWE-Bench Pro)
- https://arxiv.org/pdf/2605.08366 (SWE Atlas)
- https://arxiv.org/pdf/2511.05459 (SWE-Compass)
- https://arxiv.org/pdf/2607.00711 (ClarifyCodeBench)
- https://arxiv.org/html/2603.00187v1 (ClarEval)
