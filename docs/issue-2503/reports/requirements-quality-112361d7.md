---
issue: 2503
role: requirements-quality-112361d7
author: requirements-quality-112361d7
skills: requirements-quality (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: on-the-record/directive/acceptance-format.md
    sha: 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9
  - path: gates/forbidden_action_rule.py
    sha: 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9
---

# issue-2503 — requirements-quality-112361d7 record

## What was done

1. Added a ROLE-FORBIDDEN ACTION bullet to `on-the-record/directive/acceptance-format.md`
   stating the rule (an `## Acceptance` bullet must not require an action the
   delivering role is categorically forbidden from taking) and the sanctioned
   follow-up wording ("name the follow-up with a drafted body in `## Open
   findings`; the orchestrator files it").
   canonical: `95d3b42b:on-the-record/directive/acceptance-format.md` (this
   commit's diff — the ROLE-FORBIDDEN ACTION bullet added before the
   pre-existing VISUAL-VERIFICATION bullet).
2. Implemented `gates/forbidden_action_rule.py`, an authoring-time check
   modeled on the existing `gates/acceptance_authoring_rule.py` shape
   (`check_issue_body(issue, body)` for text-only/network-free judging,
   `check(repo, issue)` wrapping a live `gh issue view`, and a CLI `main()`).
   canonical: `95d3b42b:gates/forbidden_action_rule.py` (new file, this
   commit).

## Why

CORE_BUILD_NOW=1 was set by the spawner (build-now bypass, contract v3 s19a),
so this record delivers directly on the assigned issue branch without the
two-phase proposal round.

#2479's original R3 bullet ("file that as a separate follow-up issue and link
it here") was unsatisfiable by construction — no role session can create a
GitHub issue (`gh-guard`, contract v3 s8/s9). The delivering session's honest
workaround still scored the gate short, and the orchestrator had to notice
and file #2501/#2502 by hand. The fix has two parts because a directive
sentence alone is advisory and a gate alone has no sanctioned rewording to
point authors at: the directive states the rule and gives the wording,
`gates/forbidden_action_rule.py` catches a bullet that ignores it.

The gate flags a file/open/create/raise verb within ~60 characters of
issue/ticket in the `## Acceptance` section, and skips a match when the
same window names the orchestrator/operator/a non-role account as the
actor instead — the sanctioned rewrite's own shape.
canonical: `95d3b42b:gates/forbidden_action_rule.py:47-52` (`_ROLE_REASSIGNED`
exemption pattern). It also treats an unfetchable issue body as a finding
rather than an empty (passing) list.
canonical: `95d3b42b:gates/forbidden_action_rule.py:109-114` (`check()`'s
`body is None` branch returns a non-empty list, not `[]`).

The regex is intentionally narrow — mirroring `acceptance_authoring_rule.py`'s
own narrow-trigger precedent (a broader mechanism-verb trigger was measured
elsewhere to newly block far more issues than it should, see
`acceptance-format.md`'s NEGATIVE CRITERIA entry). A bare mention or link of
an issue number carries no verb and never matches, per the issue's own
`must not` constraint — confirmed live below.

requirements-quality skill loaded and judged not applicable: this task adds
an authoring-time gate and a directive rule, it does not audit an inventory
of requirement/story sentences against EARS/QUS — the skill's own
"does this even need the procedure?" section routes infra/gate work like
this out before Step 1.

## Upstream basis

- `on-the-record/directive/acceptance-format.md` (commit 95d3b42b) — rule
  text and sanctioned wording added.
- `gates/forbidden_action_rule.py` (commit 95d3b42b) — new authoring-time
  gate.
- #2479's issue body (current, `gh issue view 2479`) supplied the R3 text
  used as the positive-case fixture; no git-history fallback was needed
  since the bullet is still present verbatim in the live issue body.

## Open findings

None outstanding. One scope note: the gate is a standalone CLI, invoked
manually like `acceptance_authoring_rule.py` and `artifact_smoke_rule.py`
rather than wired into `gates/ci.py`'s check graph or any
`on-the-record/hooks/*.sh` preflight — same not-yet-reachable class
`docs/specs/enforcement-boundary.md` already documents for those two
siblings.
derived: `grep -n "acceptance_authoring_rule\|artifact_smoke_rule" gates/ci.py`
— result: no matches (neither sibling gate is wired into the check graph
either, so this is the established pattern, not a gap introduced here).
Wiring any of the three into the check graph is a separate, narrower
follow-up; per this issue's own sanctioned wording it is named here rather
than filed, since filing a GitHub issue is the action this role is
forbidden from taking — the orchestrator files it if wanted.

## Acceptance evidence

- check: `on-the-record/directive/acceptance-format.md` states the rule and
  gives the sanctioned wording.
  canonical: `95d3b42b:on-the-record/directive/acceptance-format.md`'s
  ROLE-FORBIDDEN ACTION bullet — contains both the rule statement and the
  sanctioned wording "name the follow-up with a drafted body in `## Open
  findings`; the orchestrator files it."

- check: the authoring-time check rejects a forbidden-action bullet,
  demonstrated live against #2479's original R3 text as the positive case,
  and against a compliant rewrite as the negative case.
  acceptance: `python3 gates/forbidden_action_rule.py 2479` — result:
  ```
  gate blocked:
    - issue #2479's 'Acceptance' bullet requires an action the delivering role is forbidden from taking ("- check: state explicitly whether the gates' own refusal-message detail was found sufficient to self-correct from without the new directive text — if insufficient, file that as a separate follow-up issue and link it here rather than expanding this issue's scope.") — gh-guard refuses issue creation for every role session (contract v3 s8/s9: issues are the user's requirement backlog, user-authored only). Rewrite with the sanctioned follow-up wording: 'name the follow-up with a drafted body in `## Open findings`; the orchestrator files it.'
  ```
  exit code 1.
  derived: `python3 -c` script (this session, not persisted) importing
  `check_issue_body` directly with a compliant-rewrite Acceptance body
  ("... name the follow-up with a drafted body in \`## Open findings\`;
  the orchestrator files it.") — result: `[]` (printed "PASS: compliant
  rewrite produced no findings").
  derived: same script with a mention-only Acceptance body ("see issue
  #2501 and #2502 for the filed items", no verb-obligation on the
  delivering role) — result: `[]` — confirms the issue's own `must not`:
  a bare mention/link of an issue number does not block.

skill-verdict: work-in-english — applied: invoked; wrote this record, the
gate's docstrings/comments, and the directive addition in English (user's
prompt was Korean)
skill-verdict: requirements-quality — not-applicable: task is authoring an
infra gate + directive rule, not auditing an inventory of requirement/story
sentences against EARS/QUS (skill's own pre-check routes this out)

## What did not work

None.

## Next steps

None pending — both Acceptance checks above executed live this session
with the results shown there.
derived: `python3 gates/forbidden_action_rule.py 2479` — result:
```
gate blocked (see full output in Acceptance evidence above), exit 1
```
