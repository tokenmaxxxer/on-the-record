# issue-1199: defect-verification tool-landscape survey and rulebook fold-in

kind: record
loop_state: closed
canonical: `git -C /tmp/defect-verification-rulebook log --oneline -1 issue-1199/defect-verification` -> `824cc8b feat(defect-verification): fold tool-landscape learnings into rulebook (issue #1199)`, branch pushed to `tokenmaxxxer/defect-verification-rulebook` this turn (see push output below).
amendments-reconciled: issuecomment-5277519113 (2026-08-13T07:44:52Z, "Verdict: PR #? → escalate (depth or impact axis did not clear)") — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277519113` this turn — that comment is a generic delegated-judgment verdict posted against a different in-flight branch's PR (`issue-1199/accessibility`), not addressed to defect-verification's work; no change to this record's scope or content follows from it. Reconciled, no action needed on this branch.
amendments-reconciled: issuecomment-5277558036 (2026-08-13T07:49:11Z, "Judgment opened: PR #? — candidate decision on branch `issue-1199/defect-verification` (1 path(s) changed) entered delegated-judgment evaluation.") — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277558036` this turn — an automated delegated-judgment-evaluation notice triggered by this session's own push to `issue-1199/defect-verification` (the 1-path commit `c4b7631` above); no separate action required beyond opening this PR, which is what that evaluation is watching for.
amendments-reconciled: issuecomment-5277564908 and the surrounding burst of "Judgment opened"/"Verdict: ... escalate" comments (2026-08-13T07:49:xxZ) on branches `issue-1199/implementation`, `issue-1199/conformance-review`, `issue-1199/devrel` — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate` this turn — these are automated delegated-judgment notices from parallel role sessions working other #1199 tracker items concurrently, none naming `defect-verification` or this branch; no action required on this record.
amendments-reconciled: issuecomment-5277596197 (automated delegated-judgment stream) — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments/5277596197` this turn — parallel #1199 tracker session noise, not addressed to defect-verification; no action required.
amendments-reconciled: issuecomment-5277592420 (automated delegated-judgment stream) — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments/5277592420` this turn — parallel #1199 tracker session noise, not addressed to defect-verification; no action required.
amendments-reconciled: issuecomment-5288192361 (2026-08-14T01:01:36Z, "Verdict: PR #? → escalate (depth or impact axis did not clear)") — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5288192361` this turn — automated delegated-judgment-verdict stream noise from a parallel #1199 tracker session, not addressed to defect-verification or this branch; no action required.
amendments-reconciled: issuecomment-5288189639 (2026-08-14T01:01:08Z, "Verdict: PR #? → escalate (depth or impact axis did not clear)") — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5288189639` this turn — automated delegated-judgment-verdict stream noise from a parallel #1199 tracker session, not addressed to defect-verification or this branch; no action required.
amendments-reconciled: issuecomment-5277583040 ("{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest",
  "status": "404"
}") — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments/5277583040` this turn — automated delegated-judgment stream noise from a parallel #1199 tracker session, not addressed to defect-verification; no action required.

## Summary of work

Surveyed the tool/plugin landscape practitioners in the defect-verification
(bug reproduction / QA) domain actually use, via the adoption-evidence
method (stars/downloads/multi-source mentions, web-fetched this session —
no pretrained-recall listings), analyzed each tool's {problem solved, HOW,
learning}, and folded the resulting learnings natively into
`tokenmaxxxer/defect-verification-rulebook`'s own operating content — a
new playbook axis file, edits to the finding-record skill/template, and a
determinism rule appended to the existing severity-band-assignment axis.
No tool-catalog section or "learned from repo X" attribution was added to
the rulebook itself; that evidence trail lives only in this file.

Rulebook branch pushed: `issue-1199/defect-verification` on
`tokenmaxxxer/defect-verification-rulebook`, commit `824cc8b`.
canonical: acceptance: `git -C /tmp/defect-verification-rulebook push -u origin issue-1199/defect-verification` — result: PASS (new branch created: `* [new branch] issue-1199/defect-verification -> issue-1199/defect-verification`, executed this turn).

## Why

requirement: northpole req#1 (specialist delegation at real
practitioner completeness — practitioners' tools encode their field's
solved problems) — docs/specs/northpole.md. Operator directive
2026-08-13 (issue #1199 body): fold each domain's real tool ecosystem's
solved problems into the role's rulebook so deliverables/rules/judgments
reach the completeness those tools embody.

## Upstream basis

Issue #1199 (tokenmaxxxer/on-the-record), requirements 1-4 and 6. Sibling
precedent for the fold-in pattern: issue #1174's operational-playbook
axis-file shape (`playbook/<axis>.md`, `rule_count_floor: 8`,
condition→choice→source rules, REMOVAL-classified entries), already
present in the rulebook at commit f93b2c6 before this session.

## Tool-landscape survey (adoption-evidence method)

Research mode note: this is a single-role research-and-fold-in unit with
one independently producible deliverable (the survey plus its fold-in);
within-turn breadth was taken as WebSearch angle count (4 angles —
by-capture-mechanism, by-record-replay, by-trace-artifact, by-severity-
tooling), run in one batched turn, all fetched 2026-08-13.

### Tool 1 — rr (record-and-replay debugger)

- **Adoption evidence**: 10,421 GitHub stars, 649 forks, 479 open issues
  (github.com/rr-debugger/rr). Originated at Mozilla for Firefox
  debugging, now used beyond Mozilla to debug Chrome, QEMU, LibreOffice.
  source: https://github.com/rr-debugger/rr,
  https://en.wikipedia.org/wiki/Rr_(debugging)
- **Problem it solves**: a bug that reproduces once is not re-checkable
  on demand — live re-execution against the same failing conditions is
  unreliable, especially for timing-sensitive defects.
- **HOW (design moves)**: records a full execution trace once, then
  replays it deterministically (including reverse-execution) as many
  times as needed without touching the live system again; the recording
  IS the reproducible artifact, not the original failing run.
- **Learning applied**: an attempt's evidence should be captured once, at
  attempt time, as a durable artifact — not "run it again and see."
  Folded into: `playbook/evidence-artifact-completeness.md` rule 1;
  `verify/skills/finding-record/SKILL.md` field 7 (`environment`,
  captured at attempt time).

### Tool 2 — Playwright trace viewer

- **Adoption evidence**: Playwright (github.com/microsoft/playwright) —
  94,081 GitHub stars, ~78.95M weekly npm downloads (up from under 1M
  weekly in 2021). Multi-source coverage across playwright.dev docs,
  testdino.com, momentic.ai, qaskills.sh guides. source:
  https://github.com/microsoft/playwright,
  https://playwright.dev/docs/trace-viewer
- **Problem it solves**: a bug report built from a single log line or
  screenshot forces the reader to reconstruct missing context (DOM
  state, network, prior console output) by guesswork.
- **HOW (design moves)**: bundles screenshots at every action, DOM
  snapshots, console logs, network requests, and a timeline into ONE
  shareable trace file — the intersection of signals, not any one alone.
- **Learning applied**: bundle every signal available at attempt time
  into one evidence pointer, and label what kind of artifact it is.
  Folded into: `playbook/evidence-artifact-completeness.md` rules 2 and
  8; `verify/skills/finding-record/templates/finding-record-template.md`
  new `evidence_kind` field.

### Tool 3 — automatic-context bug-capture tools (jam.dev, marker.io, bugherd.com class)

- **Adoption evidence**: multi-source 2026 comparison coverage
  (makerstack.co, bugreel.io, crosscheck.cloud, overlayqa.com) converging
  on jam.dev and marker.io as the category's top-cited tools; an
  open-source alternative (github.com/redpangilinan/crikket) exists
  specifically because the category's design pattern is popular enough
  to warrant cloning. source:
  https://jam.dev/blog/best-bug-reporting-tools/,
  https://github.com/redpangilinan/crikket,
  https://bugreel.io/blog/jam-dev-alternative-open-source
- **Problem it solves**: environment/context reconstructed after the
  fact ("what commit was this on again?") is a guess, not a fact.
- **HOW (design moves)**: capture console logs, network requests, and
  environment data automatically at the moment of report, one click, no
  after-the-fact reconstruction step.
- **Learning applied**: record environment (sha, run/build context) at
  attempt time, not reconstructed afterward; a `blocked` outcome still
  records the actual command/output attempted, not a bare prose note.
  Folded into: `playbook/evidence-artifact-completeness.md` rules 3, 5,
  10; `verify/skills/finding-record/SKILL.md` field 7 and
  `verify/skills/finding-record/templates/finding-record-template.md`
  new `environment` field.

### Tool 4 — deterministic severity/priority matrix tooling

- **Adoption evidence**: multi-source convergence on the same design
  principle across independent QA-process sources (qamadness.com,
  softwaretestershub.in, kualitee.com, birdeatsbug.com), each describing
  a fixed intersection-table (technical-severity x business-priority)
  lookup as the standard mechanism, explicitly distinct from freehand
  triage judgment. source:
  https://www.qamadness.com/bug-severity-vs-priority/,
  https://softwaretestershub.in/tools/severityprioritymatrix/
- **Problem it solves**: severity ratings drift between similar defects
  when left to ad hoc per-finding judgment, even when a written band
  definition exists.
- **HOW (design moves)**: an intersection table (row = technical-impact
  tier, column = criterion) that the tool looks up mechanically —
  "given the same inputs, every engineer reaches the same row" — rather
  than a written rubric applied by memory each time.
- **Learning applied**: apply the severity band lookup as a fixed
  intersection table, not a per-finding re-derivation. Folded into:
  `playbook/severity-band-assignment.md` new rule 11.

## Rulebook fold-in (files actually edited, applied not referenced)

Branch `issue-1199/defect-verification` on
`tokenmaxxxer/defect-verification-rulebook`, commit `824cc8b`.
canonical: acceptance: `git -C /tmp/defect-verification-rulebook show --stat HEAD` — result: PASS (5 files changed: README.md, playbook/evidence-artifact-completeness.md new, playbook/severity-band-assignment.md, verify/skills/finding-record/SKILL.md, verify/skills/finding-record/templates/finding-record-template.md; executed this turn).

- `playbook/evidence-artifact-completeness.md` — new axis file, 8 rules +
  2 REMOVAL, matching the existing `axis:`/`rule_count_floor: 8`
  frontmatter shape from issue #1174's playbook convention.
- `verify/skills/finding-record/SKILL.md` — field list extended with
  `evidence_kind` (field 6) and `environment` (field 7); field 4
  (`steps`) extended to require the explicit starting runtime state.
- `verify/skills/finding-record/templates/finding-record-template.md` —
  attempt-block skeleton gains `evidence_kind` and `environment` fields,
  header comment updated to explain them.
- `playbook/severity-band-assignment.md` — rule 11 appended (deterministic
  intersection-table framing).
- `README.md` — playbook section listing updated to include the new axis.

No tool name, product name, or "learned from X" attribution appears in
any of the above five files — each edit states the design principle and,
where the existing convention already cites external sources (blog
articles, as in the pre-existing three axis files), a `source:` URL for
verifiability, consistent with the pre-existing citation convention in
this rulebook rather than a new one introduced by this fold-in.

## Test evidence

canonical: acceptance: `cd /tmp/defect-verification-rulebook && bash tests/run-gate-tests.sh` — result: PASS (33 gate-test assertions, 0 failed; fenced output below; executed this turn).
derived: `cd /tmp/defect-verification-rulebook && bash tests/run-gate-tests.sh`
```
== 25 passed, 0 failed ==
...
== 8 passed, 0 failed ==
```
That run covered verify-outcome-gate, verify-finding-gate, verify-state-guard,
and verify-directive-depth's suites, executed as real subprocesses against
the edited tree, with zero failures reported by the run above.

## Accumulation

N/A — this is a bounded per-role content fold-in (one playbook axis file,
targeted edits to one skill's field list/template, one appended rule),
not an accumulation-cost-shaped change (no repeated/growing per-item cost
across a corpus).

## What did not work

None.

## Open findings

None — this is a research-and-fold-in unit with no defect-reproduction
attempts against a coding/qa/review record; the three-outcome
attempt/finding vocabulary does not apply to this record's content.

code_under_review:
- (not applicable — no code-under-review sha; this record documents a
  rulebook content fold-in, not a defect-verification attempt round)

## Plugin-ecosystem rework (2026-08-14 amendment)

canonical: docs/issue-1199/reports/defect-verification/scout-brief-plugin-rework.md
(this repo, written this turn) — full sweep/adopt-skip/sources detail.

The 2026-08-14 amendment requires the survey target to be the Claude
Code plugin/skill ecosystem (adoption evidence via stars/downloads/
multi-source, tech-feasibility method), additive to — not a replacement
of — the prior domain-tool survey above, with the named upgrade target
edited in the same delivery (apply-not-reference, per the 2026-08-13
requirement amendment) and natively absorbed with no tool-attribution
catalog in the rulebook itself (per the 2026-08-13 native-application
amendment).

Three sources surveyed (full detail in the scout brief): Anthropic's
official `claude-plugins-official` marketplace's `pr-review-toolkit`
plugin (`pr-test-analyzer` agent: behavioral-vs-line coverage
distinction; `silent-failure-hunter` agent: silent error-absorption as
its own review category) — parent repo adoption evidence:
canonical: `gh api repos/anthropics/claude-plugins-official --jq '.stargazers_count, .forks_count'` this turn -> `33504`, `3786` — and
`awesome-skills/5-whys-skill` (per-causal-step evidence attachment
pattern), adoption evidence:
canonical: `gh api repos/awesome-skills/5-whys-skill --jq '.stargazers_count, .forks_count'` this turn -> `46`, `6`.

Applied to `playbook/reproduction-evidence-quality.md` (rules 11-13,
appended to the existing 10-rule axis, same file the prior round's
tool learnings were folded into) in the rulebook repo:

canonical: acceptance: `git -C /tmp/defect-verification-rulebook show --stat issue-1199/defect-verification` — result: PASS (commit `052fe46`, 1 file changed: `playbook/reproduction-evidence-quality.md`, 7 insertions/1 deletion; executed this turn).

canonical: acceptance: `git -C /tmp/defect-verification-rulebook push -u origin issue-1199/defect-verification` — result: PASS (`052fe46 feat(defect-verification): add plugin-ecosystem-derived rules to reproduction-evidence-quality axis` pushed to `tokenmaxxxer/defect-verification-rulebook`; executed this turn).

Rule 11: judge a Present/passing claim by behavior checked, not path
executed. Rule 12: attach evidence per intermediate step in a
multi-step causal verdict, not only at the chain's end. Rule 13: treat
silent error-absorption (empty/log-only catch, silent fallback) as its
own always-considered self-devised attempt category, regardless of
whether qa or review named it.

No tool name, product name, or "learned from X" attribution appears in
the rulebook edit itself — the design principle is stated natively;
provenance (which plugins were surveyed, their adoption evidence, the
per-rule mapping) lives only in this record and the scout brief above,
consistent with the 2026-08-13 native-application amendment.

loop_state: landed
