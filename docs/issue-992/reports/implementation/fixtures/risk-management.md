Subject: issue-992

# Live-fire seed tasks — risk-management (`finding_method`/`anti_pattern`)

Per `roles/specs/risk-management.spec.json`'s new `finding_method` and
`anti_pattern` fields.

## Fixture 1 — restated-risk treatment reads as filled-in but is not treated

Hypothetical risk-register entry under test:

```
risk_id: R-014
description: "third-party auth library has a known supply-chain risk"
likelihood: medium
impact: high
treatment: "this is a supply-chain risk that should be watched"
owner: "platform team"
```

- Generic reasoning: every required field carries a non-empty string
  (treatment and owner both hold text), the entry looks well-formed.
- Methodology-correct (finding_method item 3, treatment-completeness
  check per NIST IR 8286 lineage): "should be watched" names no
  accept/mitigate/transfer/avoid action and no concrete step — it
  restates the description rather than treating the risk. Also,
  finding_method item 3's owner check and anti_pattern
  "Owner-as-team": "platform team" is a whole team, not an accountable
  individual/role instance. Finding: anti_pattern "Restated-risk
  treatment" (no action verb) and "Owner-as-team" (no accountable
  owner) — both fields hold text but neither carries the content the
  schema's own fields exist to require.

Divergence: field-non-emptiness reaches "well-formed entry"; the
methodology's content check (does the string actually name an action
and an accountable individual) reaches "unactioned, unowned risk
dressed as a filled-in record."

## Fixture 2 — unregistered supply-chain risk from a new dependency

Hypothetical scenario: the reviewed artifact's diff adds a new
third-party npm package to the dependency manifest. The risk register
(the set of all current `risk_id` entries) carries no entry whose
`description` names that package.

- Generic reasoning: the risk register already has entries covering
  "dependencies" generically, so the axis/finding check has something to
  point at.
- Methodology-correct (finding_method item 1, third-party/supply-chain
  sweep per NIST SP 800-161r1 §2): a new dependency requires its own
  registered risk_id before or at the point it lands — a generic
  "dependencies" entry elsewhere in the register does not cover a
  specific new package. Finding: anti_pattern "Missing supply-chain
  entry" — `finding.target_path` inside risk-management's own
  write_scope, `required_fix` naming the specific new dependency that
  needs its own risk_id.

Divergence: checking whether the register carries *any* dependency-
related entry reaches "covered"; checking whether *this specific new
dependency* has its own registered risk_id reaches "unregistered
supply-chain risk," which is the actual C-SCRM requirement.
