<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- REQUIREMENT DIGEST SYNC (issue #930, demoted from
  requirement-digest-preflight.sh): a commit that changes a requirement
  source also updates `docs/specs/requirements.md` (the digest) in the
  same commit — the digest drifting behind its sources was northpole
  req#6's silent-loss channel; keep them moving together, now by habit
  rather than a deny hook.

- REQUIREMENT ELICITATION (issue #1006 req#4): before drafting an issue,
  check whether the user's ask already carries a testable `## Acceptance`
  -shaped criterion (the same shape ACCEPTANCE FORMAT below requires). If
  it does not — the ask is vague or incomplete — ask 1-3 targeted
  clarifying questions in-conversation first, routed through the
  `requirements-quality` and/or `user-discovery` skills per their own
  trigger conditions, before drafting anything. A precise ask (acceptance
  criterion already clear) skips this and goes straight to issue
  drafting below — no detour.
- SCOPE-OPTION PROPOSAL (issue #1707): the trigger subclass is asks that
  are BOTH design-bearing (no testable acceptance shape yet) AND
  scope-ambiguous (more than one plausible scope) — a strict subset of
  the vague asks REQUIREMENT ELICITATION above already catches. Every
  other vague ask (design-bearing but scope-clear, or scope-ambiguous but
  not design-bearing) keeps REQUIREMENT ELICITATION's open-question path
  above unchanged; this check never fires for those. For the trigger
  subclass only, do not ask open questions — instead run the VALIDITY
  CONSULT below (#1024) ON THE VAGUE ASK ITSELF, first, before any option
  exists (issue #1712: closes the consult-ordering gap — options must
  cite a consult-trace, but #1024's consult otherwise only runs on the
  CONFIRMED ask, and at option-presentation time no confirmed ask, hence
  no trace, would yet exist). Derive the OPTION BLOCK from that
  consult's output — its trace is the `consult-trace:` cited per option,
  never an invented one. The option block is exactly 2 or 3 options,
  ordered by ascending scope size (the narrowest-scope option first), each carrying
  `scope:`, `cost:`, `risk:`, `non-goals:`, and `consult-trace:` fields
  (`consult-trace:` cites the validity/risk consult ref the option's
  alternatives/tradeoffs were drawn from — scribe-not-inventor: options
  must derive from consult output, not invented). Once the operator picks
  or edits one option, that becomes the confirmed requirement fed to the
  post-confirmation consult below (#1024); when the confirmed ask is
  unchanged from the vague ask this consult already ran on, that consult
  may reference the same trace instead of re-running it. NEUTRALITY RULE
  (verifiable, replacing an unverifiable "no preference" instruction):
  the literal token `recommended` (case-insensitive, any substring
  match), and the Korean synonyms `권장` and `추천` (either, as a
  substring match), MUST NOT appear anywhere inside the option block.
- VALIDITY CONSULT (issue #1024): before drafting an issue, route the
  confirmed ask through the `requirements-engineering` skill
  (feasibility, testability, consistency with
  `docs/specs/requirement-digest.md`, ordering against other live
  work) and, when the ask is risk-bearing (touches auth, data deletion,
  external credentials, or is flagged risk-bearing by
  `requirements-engineering` itself), also through `risk-management`.
  Record the consult's trace reference in the drafted issue body as
  `validity-consult: <ref>`. A trivial/mechanical ask (typo fix,
  wording change, no design decision) skips the consult and instead
  carries the literal tag `validity-consult-skip: trivial` — no other
  skip reason is accepted. This is a distinct check from ACCEPTANCE
  FORMAT below and from #1017's requirement-linkage citation — it does
  not gate on those, and they do not gate on this.
- DESIGN-RESEARCH INTAKE (issue #1653): before drafting a design-bearing
  issue (one that involves a design/methodology decision, not a purely
  mechanical change), require a prior-art/methodology trace — derived
  risks plus an effectiveness-verification plan, via the
  `tech-feasibility`/`prior-art-scan` skills — recorded in the drafted
  issue body as `design-research: <ref>`. A mechanical issue (no design
  decision) skips this and instead carries the literal tag
  `design-research-skip: mechanical` — no other skip reason is
  accepted. Checked by `gates/design_research_consult.py`. Distinct
  from VALIDITY CONSULT above (#1024) — this is the design-research
  axis, not the feasibility/risk axis.
- Requirements become ISSUES you draft and the user confirms (you are the
  scribe, never the inventor). Missing preconditions (GitHub remote,
  docs/specs/approvers.md) you offer to fill in conversation — always
  confirmed, never silent.
- `docs/specs/requirement-digest.md` is the condensed, auto-maintained
  pointer to every currently-live requirement (issue #930) — read it
  first, before `docs/specs/requirements.md`, when you need to
  reconstruct what the operator has already asked for across a long
  history of records.
