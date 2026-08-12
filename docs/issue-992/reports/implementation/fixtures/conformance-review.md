Subject: issue-992

# Live-fire seed tasks — conformance-review (`alignment` axis)

Per `docs/handbooks/architecture-methodology.md`'s new
"Axis evaluation procedure — alignment" section. Each scenario is
constructed so applying the section's EXECUTE steps produces a verdict a
generic ("does this look aligned?") reading would not reach.

## Fixture 1 — worst-case recomputation catches a masked entry

Hypothetical conformance-review record under test:

```
subject: repo/module.py@abc123
entries:
  - test: "lint rule no-eval"                        result: X
  - test: "spec section 4.2 input validation"         result: Y
  - test: "spec section 4.3 output encoding"           result: X
summary line: "overall verdict: X (majority of entries agree)"
```
(X = the best-case EARL enum value, Y = the worst-case EARL enum value,
per EARL 1.0's severity order.)

- Generic reasoning: majority of entries agree on X, so the summary
  line looks reasonable -> axis verdict "supports".
- Methodology-correct (EXECUTE step 2, worst-case-across-entries per
  EARL 1.0's own severity order): the recomputed overall value is Y, not
  X, so the summary line is wrong regardless of how many entries agree.
  Axis verdict: "contradicts" — `finding.required_fix`: correct the
  summary line to the recomputed worst-case value and surface the
  entry that produced it, since averaging/majority across cited entries
  is not what EARL's schema defines conformance as.

Divergence: majority-vote intuition reaches "supports"; the
methodology's worst-case rule reaches "contradicts" on the same input.
This is the threshold #996 §5 calls a genuine judgment change, not a
wording difference.

## Fixture 2 — unresolvable `test` reference

Hypothetical conformance-review record under test:

```
entry: test="follows best practices for error handling" result=X assertedBy="review"
```

- Generic reasoning: the description sounds like a real check, mark it
  "supports".
- Methodology-correct (EXECUTE step 1, `test` must resolve to an actual
  conformance criterion — a spec section, requirement, or lint-rule
  identifier, not a paraphrase; EXECUTE step 3, `assertedBy` must name
  the actual session/tool, not a placeholder): neither field resolves to
  anything checkable. Axis verdict: "contradicts" — `finding.required_fix`:
  replace the vague `test` string with the actual spec section/lint-rule
  id being checked and name the real asserting session in `assertedBy`.

Divergence: the entry reads as plausible prose and a generic reviewer
would accept it; the methodology's reference-resolution requirement
rejects it outright because prose plausibility is not "resolves to a
real criterion."
