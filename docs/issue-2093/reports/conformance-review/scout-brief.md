---
subject: issue-2093
role: conformance-review
kind: scout-brief
loop_state: surveying
---

# Scout brief — what a strong audit of a "must never crash" change checks

Mode: batched-sequential, 2 sweep angles, 1 round, no deepening stage
(saturation at judge point 1 — neither angle would change a review-plan
decision on a second round). Parallel dispatch was available; this sweep did
not use it, and states that rather than presenting a serialized sweep as
fan-out. Angles were aimed at two gaps the survey named: how to scope a
cross-product test population, and how to distinguish a real green result from
a vacuous one.

## Category must-bes (what the field assumes of an audit of this change-class)

- Robustness is defined by behaviour under exceptional execution conditions,
  so the audit's attention belongs on invalid input, not on the happy path.
  [testsigma]
- The observed failure signals are enumerated up front — crash, failed
  assertion, hang, leak — rather than summarised as a bare green result.
  [parasoft]
- A **negative control** exists: the contract is deliberately broken and the
  validator is shown to fire, so an all-green result is not the vacuous
  consequence of checks that cannot go red. [strug]
- Requirements link forward to the specific verification covering them — an
  RTM links a requirement to its verification, not to the containing module.
  [tutorialspoint]

## Performance axes the field competes on

1. **Population fidelity** — does the suite enumerate the real registration
   population, or a hand-picked subset that can drift from it silently?
2. **Falsifiability** — can the suite be shown to go red?
3. **Verdict honesty under absence** — is "not yet built" reported as such,
   rather than folded into a green summary.

## Adopt / skip

- **Adopt:** the negative-control check as a first-class review step. The
  implementation proposal already offers one (revert the `expanduser`, expect
  the tilde case to go red); this review re-executes it rather than taking the
  claim on trust. It is the highest-value single check available for a suite
  whose entire claim is "nothing crashed".
- **Adopt:** fault-classification vocabulary — record which signal each
  sampled cell was judged on (exit code, `Traceback` on stderr), rather than a
  bare green mark.
- **Skip:** fuzz/mutation *generation* inside the review. The field rates it
  highly for discovery, but this review's job is fidelity to a written
  acceptance list; generating fresh crash inputs would yield findings the
  issue never asked for while the stated checks go unexamined.

## Gap line

Already satisfied at the surveyed state: an enumerated edge-input corpus and
an enumerated failure signal (implementation proposal steps 2 and 5, per
survey §1). Missing at that state: any executed evidence — no test file exists
in the branch diff (survey §1) — and no stated verdict vocabulary or sampling
derivation (survey §3, §5). The review plan targets those three gaps, not the
whole field.

## Sources

```
https://testsigma.com/blog/robustness-testing/
https://www.parasoft.com/blog/what-is-robustness-testing/
https://onlinelibrary.wiley.com/doi/10.1155/2016/6589140   (Strug, mutation
  testing approach to negative testing)
https://www.tutorialspoint.com/software_testing_dictionary/requirements_traceability_matrix.htm
```
