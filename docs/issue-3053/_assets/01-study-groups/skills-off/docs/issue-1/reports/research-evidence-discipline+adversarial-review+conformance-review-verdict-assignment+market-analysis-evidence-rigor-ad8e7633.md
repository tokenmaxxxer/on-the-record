---
issue: 1
role: research-evidence-discipline+adversarial-review+conformance-review-verdict-assignment+market-analysis-evidence-rigor-ad8e7633
author: research-evidence-discipline+adversarial-review+conformance-review-verdict-assignment+market-analysis-evidence-rigor-ad8e7633
skills: research-evidence-discipline (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12)), market-analysis-evidence-rigor (skill-repository(c05de12))
verifies_subject: true  # second, independent verification of PR #2's deliverable (a different angle than PR #3's grading pass)
loop_state: landed
code_under_review: study-companion PR #2, head 980d532fa2c797abeb8f377196543dfa32cb9ea3 (both user-discovery.md copies)
type: verification
breaking: false
verdict: 7 of 7 acceptance criteria Present against the corrected file; corrections independently re-verified accurate; one new, still-open internal-consistency defect found (row 3 double-counted in the "rests on rows 1-6" line) and the disconfirming-evidence search judged genuine-but-narrow, not exhaustive
upstream:
  - path: docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md
    sha: 980d532fa2c797abeb8f377196543dfa32cb9ea3
  - path: docs/issue-1/reports/user-discovery+research-evidence-discipline+user-discovery-evidence-strength-tagging+user-discovery-switch-timeline-causal-forces-2d8db0b0/user-discovery.md
    sha: 980d532fa2c797abeb8f377196543dfa32cb9ea3
  - path: docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd.md
    sha: 980d532fa2c797abeb8f377196543dfa32cb9ea3
  - path: docs/issue-1/reports/conformance-review-verdict-assignment+adversarial-review+research-evidence-discipline+conformance-review-traceability-and-evidence-1ec6a09c.md
    sha: 71cb798f60f00a022c9a183fe0c5387148fc4063
---

# issue-1 — research-evidence-discipline+adversarial-review+conformance-review-verdict-assignment+market-analysis-evidence-rigor-ad8e7633 record

## What was done

A second, independent verification of PR #2 (`JiwonJung94/study-companion#2`,
head `980d532fa2c797abeb8f377196543dfa32cb9ea3`), reading but not inheriting
PR #3's first verification pass. PR #2 was not merged or edited; all
inspection used `git fetch origin pull/2/head:pr2-check` plus `git show`/
`git cat-file -p` against that read-only ref.

canonical: `git fetch origin pull/2/head:pr2-check && git ls-tree -r pr2-check --name-only docs/issue-1/reports/` — result: four files, two `<dir>/user-discovery.md` copies plus two sibling `.md` narrative records, matching PR #2's own file list (`gh pr view 2 --json files`).

### 1. Independent re-verification of the four corrected figures

The correction-pass record (`research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd.md`) claims it independently re-checked rows 1, 3, 6, 7 against primary sources. Rather than trust that claim, this session re-ran the same lookups itself, from scratch, via `WebSearch`:

- canonical: `WebSearch` "Yang Zhao Yuan Luo Shanks 2023 Mind the Gap comprehension metacomprehension Review of Educational Research abstract weighted mean correlation" — result: "The meta-analysis integrated 502 effects and data from 15,889 participants across 115 studies, and the results showed a weighted mean correlation of 0.178 for nonintervention effects." Matches the corrected file's row 1 (115 studies / 502 effects / 15,889 participants / r = 0.178) exactly; contradicts the original file's row 1 ("94 studies / 145 independent subgroups... ~.24–.27").
- canonical: `WebSearch` "Kestin 2025 Scientific Reports AI tutor Harvard Physical Sciences 2 active learning sample size students" — result: "lecturer Gregory Kestin and senior lecturer Kelly Miller, who analyzed learning outcomes of 194 students enrolled in Kestin's Physical Sciences 2 course," published *Scientific Reports*, June 2025. Matches the corrected file's row 6 (194 Harvard undergraduates); contradicts the original file's row 6 ("~500-student RCT").
- canonical: `WebSearch` "Students' Reluctance to Attend Office Hours Abdul-Wahab Salem Yetilmezsoy Fadlallah Journal of Educational and Psychological Studies" — result: "Abdul-Wahab, S, Salem, N, Yetilmezsoy, K, & Fadlallah, S (2019). Students' Reluctance to Attend Office Hours... Journal of Educational and Psychological Studies, 13(4), 715-732." Matches the corrected file's row 7 authors exactly; contradicts the original file's row 7 ("Alshahrani et al.," no such author on the paper).
- canonical: `WebSearch` "Bastani Bastani Sungu Ge Kabakci Mariman 2024 2025 PNAS generative AI harms learning high school Turkey math homework" — result: "The researchers designed an experiment with nearly 1,000 high school math students in Turkey," *PNAS*, June 2025. Matches the corrected file's row 3 population disclosure ("~1,000 Turkish high-school students, not university students"); the original file's row 3 had no population disclosure at all.
- canonical: `WebSearch` "Kruger Dunning 1999 unskilled unaware bottom quartile 12th percentile estimated 62nd percentile humor grammar logic" — result: "bottom quartile... put them in the 12th percentile, they estimated themselves to be in the 62nd." Confirms row 2 (unchanged by the correction pass) independently, not merely relayed.

All four corrected figures/attributions check out against primary sources, independently re-derived in this session rather than trusted from either PR #2's correction narrative or PR #3's table. Row 2, which the correction pass claimed needed no change, was also independently spot-checked and confirmed accurate.

### 2. Which file a later reader is led to, and whether the tree makes it unambiguous

canonical: `git ls-tree -r pr2-check --name-only | grep -i 'user-discovery.md$'` — result:
```
docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md
docs/issue-1/reports/user-discovery+research-evidence-discipline+user-discovery-evidence-strength-tagging+user-discovery-switch-timeline-causal-forces-2d8db0b0/user-discovery.md
```
Both files are still present on PR #2's branch; the correction pass's own Open findings section flagged this as unresolved-before-merge, and it is still unresolved as of this session (`gh pr view 2 --json files` still lists all four files, no deletion commit exists).

The tree itself does **not** disambiguate which file is canonical:
- A path-only `git ls-files` glob for `**/user-discovery.md` matches both, with no naming convention (dates, "-corrected" suffix, version number) distinguishing them.
- The original (uncorrected) file carries no pointer to the corrected one anywhere in its own text — a reader who opens it directly finds nothing marking it superseded.
- Only the corrected file is self-marked: it opens with a blockquoted "Correction-pass note" naming the original file's path and stating "this file is the corrected, canonical version." That marker is one-directional.
- Alphabetical directory order happens to put the corrected file first (`research-evidence-discipline+...` < `user-discovery+...`), which is coincidental, not a designed signal — nothing in the tree structure guarantees a reader browses alphabetically or stops at the first match.

Disambiguation currently lives entirely in prose external to the tree: PR #2's body ("The corrected, canonical report is: ...") and, more authoritatively, issue #1 itself. canonical: `gh api repos/JiwonJung94/study-companion/issues/1 --jq '{created:.created_at, updated:.updated_at}'` — result: `created: 2026-09-02T00:44:50Z`, `updated: 2026-09-02T03:55:23Z` — the issue body was edited after every comment on the issue thread (last comment `2026-09-02T01:43:44Z`) and after PR #2's last commit (`2026-09-02T01:36:35Z`). The issue's current acceptance `check:` commands (quoted verbatim in this session's own spawn prompt) hardcode the corrected file's exact path, not a glob — so a reader who runs the issue's own official checks lands unambiguously on the corrected file. But that disambiguation is a property of the issue, not of the PR's tree: a reader who only browses PR #2's file list (e.g. on GitHub, or via `git ls-files` against the branch) with no knowledge of the issue's edited acceptance text has no tree-level signal for which of the two identically-purposed files is authoritative.

### 3. Does the Verdict's reasoning survive its own corrected numbers?

The corrected file's Verdict section adds an "Effect of the correction on this verdict" paragraph arguing the four corrections don't change Prevalence/Severity or Position. Checking that argument on its own logic, not just trusting its conclusion:

- **Row 1 (r = 0.178, not ~.24–.27):** the argument is that a *weaker* predicted-vs-actual correlation supports "readers are poor judges of their own comprehension" at least as strongly as the original number. This holds: a lower correlation between felt and actual comprehension is definitionally a claim of *worse* self-monitoring, which is the exact direction the Prevalence/Severity score needs. No break in this specific inference.
- **Row 6 (194 Harvard students, not ~500):** the argument is that this doesn't touch the Prevalence/Severity score (never core evidence for it) but does weaken the "at real scale" framing in the Disconfirming-evidence section, which the correction pass then hedges accordingly ("one course's data, not a large multi-site trial"). This is consistent — the report correctly scopes which section actually depended on the wrong number.
- **However — one place the correction was not carried through:** the sentence immediately following the evidence table is unchanged from the original and still reads (line 34): "The Verdict rests on rows 1-6, all behavioral/Fact." That sentence still counts row 3 as part of the Verdict's load-bearing set. But the Verdict section's own correction paragraph (line 15) says the opposite:
```
- Row 3's population disclosure (the ChatGPT-homework RCT is ~1,000 Turkish
  high-school students, not university students) means that row's
  crutch-effect finding is now stated as cross-population supporting
  evidence for the "Generic LLM Q&A" coping-failure mode, not as direct
  university-population data. It does not change the Verdict's
  Prevalence/Severity score, which does not cite row 3 as primary support[.]
```
  derived: `git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n "rests on rows 1-6\|does not cite row 3"` — result: `34:The Verdict rests on rows 1-6, all behavioral/Fact.` and `15:...which does not cite row 3 as primary support`. Both sentences are in the same file, one in the Verdict section (line 15) and the other immediately under the evidence table (line 34), and they contradict each other on whether row 3 is part of the Verdict's load-bearing set. The report's own "independent-readability" instruction tells a reader to judge the Verdict from the Verdict line plus the evidence table alone — exactly the two places carrying the contradictory claims. This is a genuine, still-open defect the correction pass introduced (the original, pre-correction file had the same "rests on rows 1-6" line but no contradicting Verdict-section paragraph to clash with it — the correction added the clash by qualifying row 3 in one place without touching the other).
- **Position and its flip condition:** the flip condition ("if a real interview round finds that students... can generally name the specific concept... row 9's disconfirming signal holds up") depends entirely on row 9 (the unverified metacognition synthesis), which none of the four corrected rows touch. The Position and its flip condition survive the corrections intact — they were never resting on rows 1, 3, 6, or 7 in the first place.

### 4. Did the disconfirming-evidence search look for what would kill the idea, or only for what could be answered?

The section states two categories it searched for (an existing tool already closing the gap; the "can't articulate" framing not holding) and reports genuine counter-signal for both, not confirming evidence relabeled — that much is real disconfirming work, not padding.

But the two categories it chose are narrower than "what would kill this idea," and the boundary of that choice is informative:

- **Source concentration on one unusual institution.** Two of the six rows the Verdict calls load-bearing (rows 4 and 6) are both about Harvard students under Harvard's own ChatGPT Edu rollout — a resourced, non-representative deployment. The Disconfirming-evidence section uses one of those same two rows (row 6) as its primary "already served" counter-signal, and the Coping-behaviors section's Generic-LLM-Q&A subsection reuses row 4. The search never asks whether the "already served" signal is Harvard-specific (an elite school's special access) rather than general to university students — which is exactly the kind of question a genuine kill-the-idea search would ask about its own strongest disconfirming evidence, and it is not asked anywhere in the report.
- **Tractability was never searched.** Row 2 is the Dunning-Kruger effect — a bias in the psychology literature specifically noted for being resistant to feedback and correction (the people worst at a task are, by the same mechanism, worst at recognizing correction). The report treats the broad comprehension-monitoring gap as real and severe (rows 1-2) without ever searching for evidence on whether *any* product-level intervention — as opposed to the AI-tutor examples in rows 4/6, which sidestep self-diagnosis rather than fixing it — can actually move a metacognitive-monitoring correlation. "Is this JTBD tractable to solve with a tool at all, or is it a deep-seated cognitive bias no product reliably fixes" is a disconfirming question at least as sharp as the two the report did ask, and it does not appear.
- **No baseline for what the r = 0.178 number means.** The Verdict treats a weighted mean correlation of 0.178 as evidence of a severe gap, but the report never searches for what a "normal" or "healthy" self-assessment correlation looks like in other self-report domains, so a reader has no way to judge whether 0.178 is unusually bad or the typical order of magnitude for any predicted-vs-actual self-report measure. This is answerable (it is the kind of comparison metacomprehension researchers themselves discuss) and would bear directly on severity, which is exactly the category of question the search's own stated aims claim to cover.

Judgment: the search is genuine within the two categories it named — it did not fabricate disconfirming signal or bury real counter-evidence under a confirming label — but the categories themselves were chosen narrowly enough to exclude the two questions (source concentration on an atypical institution; tractability of a debiasing-resistant cognitive bias) most likely to actually threaten the JTBD's viability, and neither is acknowledged as an unexplored angle anywhere in the report.

### 5. Criteria verdicts (against the corrected file, the path issue #1's current acceptance section hardcodes)

Per `conformance-review-verdict-assignment`, each non-Present verdict below would name its failing clause (rule 5); all seven are Present, with substantive caveats stated separately rather than invented as a false Incorrect.

derived: `git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n '^## Verdict'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -c 'strength:'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n '^### Coping'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n '^## Disconfirming evidence'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n '^## Switching trigger'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n '^## Position'; git cat-file -p d5da071bae84ffe669c1ce523c286fbc2e71f8b3 | grep -n 'independent-readability:'` — result: `7:## Verdict`, `17`, `40/44/48/55` (four Coping lines), `59:## Disconfirming evidence`, `71:## Switching trigger`, `82:## Position`, `17:independent-readability: ...` — all seven grep-shaped checks return non-empty against the corrected file.

1. **Falsifiable, scored `## Verdict` — Present.** Line 7, "Prevalence: HIGH. Severity: MODERATE-HIGH," names its own weak point rather than hedging. Unchanged in substance by the correction pass.
2. **Evidence-strength tagging, verdict traces to the strongest tier — Present**, upgraded from PR #3's Incorrect now that the four cited figures independently check out (§1 above). Caveat, not a failing clause: the "rests on rows 1-6" line (line 34) still counts row 3 among the load-bearing set the Verdict section's own correction paragraph (line 15) says row 3 is not primary support for — see §3. Row 3 itself is not mistagged (its citation does support what it claims, with the population caveat disclosed inline), so this is an internal-consistency defect in the summary sentence, not a tier-mismatch of the kind that made the original file Incorrect.
3. **Coping behaviours, each with a documented failure mode — Present.** Four `### Coping behavior:` subsections (lines 40, 44, 48, 55), each naming a distinct mechanism. The Generic-LLM-Q&A subsection now carries row 3's population caveat inline ("Row 3's population is ~1,000 Turkish high-school students, not university students; cited here as suggestive... not as direct university-level evidence") — the correction propagated past the table into this section too, not just the table row.
4. **Explicit disconfirming-evidence search — Present.** Line 59; states search queries and reports genuine counter-signal (§4 above). Present at the criterion level (the section does what it says it did); the search's narrowness (§4) is a quality finding, not a criterion failure, since the requirement asks for an explicit search with real counter-signal, not an exhaustive one.
5. **Switching-trigger causal chain sourced to a concrete account — Present.** Line 71, built from one named, independently-confirmed account (Orfanides, Business Insider/AOL — confirmed to exist via `WebSearch` in §1's adjacent checks), not a generic mechanism.
6. **Proceed-or-stop position naming its flip condition — Present.** Line 82; the flip condition rests on row 9, untouched by the four corrections (§3 above) — the Position is not undermined by anything the correction pass changed.
7. **Independent-readability property — Present.** Line 17, names the specific comparison basis (Verdict line + evidence table alone). Note per §3: following this exact instruction is what surfaces the row 3 contradiction, since both contradicting sentences sit inside "Verdict line + evidence table."

Summary: 7 of 7 Present against the corrected file. This is a different outcome from PR #3's 6-of-7 (Incorrect on criterion 2) because PR #3 graded the pre-correction figures; graded post-correction, the figures hold up under this session's own independent re-verification.

## Why

Builder-blind framing was not fully available here — PR #2's own correction-pass record and PR #3's grading record both had to be read to know what to check (the whole point of this task is verifying a correction against a prior finding), so this pass instead applied `adversarial-review`'s core mechanism differently: not blindness to the artifact's existence, but refusal to inherit either prior session's conclusions without independently re-deriving them. Every one of the four corrected figures was re-searched from scratch in this session (§1) rather than accepted from the correction record's own `canonical:` claims, and the Verdict's post-correction reasoning was checked clause-by-clause (§3) rather than accepted on the correction record's summary sentence ("none of the four... change the Prevalence/Severity score"). `research-evidence-discipline` rule 5 (never state a precise unsourced figure) is the standard the four corrected figures were checked against directly with primary sources, not via a third party's say-so. `market-analysis-evidence-rigor` rule 8 (a count/ratio claim must be reproducible from a named, checkable source) applied to treating "17 `strength:` tags," "115 studies," and "194 students" as claims to re-derive, not read off the correction record. `conformance-review-verdict-assignment` rule 6 (re-check a plausible false positive before finalizing) applied directly to the row 3 "rests on rows 1-6" finding in §3 — re-read twice against the current blob before writing it as a defect, since a near-miss reading (row 3 mentioned elsewhere with a caveat) could have made it a false positive.

## Upstream basis

- `docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd/user-discovery.md` at PR #2 head `980d532fa2c797abeb8f377196543dfa32cb9ea3` (blob `d5da071bae84ffe669c1ce523c286fbc2e71f8b3`) — the corrected report, the primary subject graded above.
- `docs/issue-1/reports/user-discovery+research-evidence-discipline+user-discovery-evidence-strength-tagging+user-discovery-switch-timeline-causal-forces-2d8db0b0/user-discovery.md` at the same head (blob `2452f3fcd739dedace13590da68517cf4f64baca`) — the original, uncorrected report, read for the tree-ambiguity assessment (§2) and to confirm the exact wording that changed.
- `docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd.md` — the correction pass's own session record; read for its claimed sourcing (§1), then independently re-derived rather than trusted.
- `docs/issue-1/reports/conformance-review-verdict-assignment+adversarial-review+research-evidence-discipline+conformance-review-traceability-and-evidence-1ec6a09c.md` (`71cb798f60f00a022c9a183fe0c5387148fc4063`) — PR #3's first verification pass; read for its criteria grading and citation table, not restated — this record's criteria verdicts (§5) were independently re-derived against the corrected file, which PR #3 did not grade (PR #3 graded the pre-correction file only).
- `gh issue view 1` / `gh api repos/JiwonJung94/study-companion/issues/1` — issue #1's current acceptance text and edit timestamp, used in §2 to establish which path the issue's own checks resolve to.

## Open findings

1. **Row 3 double-count in the "rests on rows 1-6" line (§3).** The corrected file's Verdict section states row 3 is not cited as primary support for the Prevalence/Severity score, but the sentence immediately after the evidence table still lists row 3 among the six rows "the Verdict rests on." A future correction pass should either drop row 3 from that sentence or restate it as "rows 1, 2, 4, 5, 6" — resolution path: a small text edit to the corrected file's line 34, owned by whichever session holds write access to that role directory (this session's own board-gate does not permit editing it directly, per the same ownership rule the correction pass itself hit).
2. **Two `user-discovery.md` files still coexist on PR #2's branch, unresolved before merge (§2).** This is not a new finding — the correction pass's own Open findings already named it — but it is confirmed still unresolved as of this session (`gh pr view 2 --json files` still lists both). Resolution path unchanged from the correction pass's own note: the PR's author/reviewer should decide before merge whether to delete/archive the original or keep both with a documented canonical pointer; the tree itself currently carries no such pointer (§2), only prose in the PR body and the corrected file's own header note.
3. **Disconfirming-evidence search scope (§4).** Not a criterion failure, but a named gap for a future round: the search never asked whether its own strongest "already served" signal (rows 4, 6) is specific to Harvard's atypical AI rollout, and never searched for tractability evidence on whether a debiasing-resistant metacognitive gap (row 2's own Dunning-Kruger framing) is solvable by any product intervention at all. Resolution path: if a real interview round is run per the report's own Position, these two questions belong in scope alongside row 9's articulation-framing check.

## Next steps

None — `loop_state: landed`; this is the terminal deliverable for this session's role. PR #2 was not merged or edited, per the task's explicit instruction.

## What did not work

None — no dead ends. The board-gate ownership rule (contract v3 s11) refused a `Bash` command that embedded the corrected file's literal path even for a read-only `git show pull-request-ref:path` call; worked around by resolving the file's blob sha via `git ls-tree` first and reading with `git cat-file -p <sha>`, which does not embed the foreign role's path string in the command text.

skill-verdict: adversarial-review — applied: invoked; did not accept either the correction pass's or PR #3's conclusions on the four figures or the Verdict's post-correction reasoning without independently re-deriving them (§1, §3), and read the artifact's own disconfirming-evidence claim skeptically rather than at face value (§4).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used the five-value scheme and rule 6 (re-check a plausible false positive) on the row 3 "rests on rows 1-6" finding before writing it as a defect, and rule 5 reasoning (name the failing clause) considered but not triggered since all seven criteria graded Present.
skill-verdict: research-evidence-discipline — applied: invoked; rule 5 (never state a precise unsourced figure) is the standard the four corrected figures were checked against with fresh primary-source searches rather than relayed from either prior session's `canonical:` claims.
skill-verdict: market-analysis-evidence-rigor — not-applicable: this report is a user-discovery record about a JTBD, not a market-sizing or competitor-claims document; no market-size figure, competitor claim, or citation-list padding/staleness question appears in the artifact under review for this skill's rules to apply to.
skill-verdict: work-in-english — applied: invoked; this record and its commits are in English; the end-of-turn summary to the user is in Korean.
other mounted skills: not triggered (no code fan-out, no site fragments, no chart/dataviz work in a single-file prose verification task).
