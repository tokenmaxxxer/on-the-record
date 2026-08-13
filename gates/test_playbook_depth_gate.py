"""issue #1174 (c) — hermetic tests for gates/playbook_depth_gate.py.

No network, no filesystem outside pytest's own tmp_path fixture — every
sample playbook text is an in-memory literal.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from playbook_depth_gate import evaluate, classify_block, main, _blocks_from_text


DECISION_RULE = (
    "- When the field type is a boolean, use a toggle switch, not a "
    "checkbox — checkboxes read as list-membership, not on/off state. "
    "source: Nielsen Norman Group, 'Checkboxes vs Toggle Switches' (2018)"
)
REMOVAL_RULE = (
    "- When a screen has more than 7 primary actions, drop the least-used "
    "ones behind a secondary menu (progressive disclosure) to reduce "
    "visual noise. source: Krug, Don't Make Me Think, 3rd ed., ch. 4"
)
GLOSSARY_LINE = "- Affordance is a property of an object that suggests its own usage."

# Derived from tokenmaxxxer/technical-writing-rulebook#25's actual
# playbook format (playbook/doc-type-selection.md, issue-1174/
# operational-playbook branch): numbered ("1. ") ordered-list rules,
# not heading or "-"/"*" blocks.
NUMBERED_DECISION_RULE = (
    "1. When the reader's stated goal is \"I want to learn by doing and "
    "have no working knowledge yet,\" choose **tutorial** — a tutorial "
    "puts the reader \"on rails\" toward one fixed destination with "
    "exact steps and no decision points, because a beginner cannot yet "
    "evaluate branches. source: https://diataxis.fr/start-here/"
)
NUMBERED_REMOVAL_RULE = (
    "6. When a single draft's outline mixes conceptual \"why\" prose "
    "with numbered action steps, split it into two documents rather "
    "than keep the mixed draft as one. **REMOVAL**: cut whichever half "
    "doesn't match the file's own doc-type before publishing, don't "
    "keep both halves \"for completeness.\" source: https://diataxis.fr/"
)
NUMBERED_DOT_RULE = (
    "1) When the reader already has baseline competence and states a "
    "concrete task, choose **how-to guide**, not tutorial — how-to "
    "guides help the reader reach a destination of their choosing. "
    "source: https://diataxis.fr/"
)


def test_decision_rule_accepted_as_addition():
    r = classify_block(DECISION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_removal_rule_accepted_as_removal():
    r = classify_block(REMOVAL_RULE)
    assert r["accepted"]
    assert r["category"] == "removal"


def test_glossary_block_rejected():
    r = classify_block(GLOSSARY_LINE)
    assert not r["accepted"]
    assert any("glossary" in reason for reason in r["reasons"])


def test_uncited_rule_rejected():
    uncited = "- When the field is numeric, use a stepper control instead of free text."
    r = classify_block(uncited)
    assert not r["accepted"]
    assert any("source" in reason for reason in r["reasons"])


def test_evaluate_passes_when_floor_met_and_removal_present():
    text = "\n\n".join([DECISION_RULE] * 4 + [REMOVAL_RULE])
    report = evaluate(text, floor=5, axes=["control-selection"])
    assert report["accepted_count"] == 5
    assert report["count_ok"]
    assert report["missing_removal_axes"] == []
    assert report["passed"]


def test_evaluate_fails_all_additive_playbook():
    text = "\n\n".join([DECISION_RULE] * 6)
    report = evaluate(text, floor=5, axes=["control-selection"])
    assert report["count_ok"]
    assert report["missing_removal_axes"] == ["control-selection"]
    assert not report["passed"]


def test_evaluate_fails_short_of_floor():
    text = DECISION_RULE
    report = evaluate(text, floor=5, axes=[])
    assert not report["count_ok"]
    assert not report["passed"]


def test_evaluate_glossary_shaped_file_never_reaches_floor():
    text = "\n\n".join([GLOSSARY_LINE] * 10)
    report = evaluate(text, floor=5, axes=[])
    assert report["accepted_count"] == 0
    assert not report["passed"]


def test_main_exit_code_pass(tmp_path):
    f = tmp_path / "playbook.md"
    f.write_text("\n\n".join([DECISION_RULE] * 2 + [REMOVAL_RULE]))
    rc = main([str(f), "--role", "ux-engineering", "--floor", "3", "--axes", "control-selection"])
    assert rc == 0


def test_main_exit_code_fail(tmp_path):
    f = tmp_path / "playbook.md"
    f.write_text(GLOSSARY_LINE)
    rc = main([str(f), "--role", "ux-engineering", "--floor", "3"])
    assert rc == 1


def test_main_missing_target(tmp_path):
    rc = main([str(tmp_path / "nope.md"), "--role", "x", "--floor", "1"])
    assert rc == 1


def test_numbered_decision_rule_accepted_as_addition():
    r = classify_block(NUMBERED_DECISION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_numbered_removal_rule_accepted_as_removal():
    r = classify_block(NUMBERED_REMOVAL_RULE)
    assert r["accepted"]
    assert r["category"] == "removal"


def test_numbered_dot_style_rule_accepted():
    r = classify_block(NUMBERED_DOT_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"


def test_evaluate_numbered_playbook_meets_floor_and_axis():
    text = "\n\n".join(
        [NUMBERED_DECISION_RULE] * 4 + [NUMBERED_REMOVAL_RULE]
    )
    report = evaluate(text, floor=5, axes=["doc-type-selection"])
    assert report["accepted_count"] == 5
    assert report["count_ok"]
    assert report["missing_removal_axes"] == []
    assert report["passed"]


def test_main_reads_directory(tmp_path):
    d = tmp_path / "playbook"
    d.mkdir()
    (d / "a.md").write_text(DECISION_RULE)
    (d / "b.md").write_text(REMOVAL_RULE)
    rc = main([str(d), "--role", "ux-engineering", "--floor", "2"])
    assert rc == 0


# issue #1174 gate fix 2 — real content pulled from
# tokenmaxxxer/technical-writing-rulebook PR #25, branch
# issue-1174/operational-playbook, playbook/minimalism-scoping.md rule 2
# and playbook/doc-type-selection.md's "## Rules" section marker.
RELOCATION_RULE = (
    "2. When a section explains background the reader does not need to "
    "complete the immediate task, move it to an explanation doc or a "
    "collapsed/linked aside rather than inline it — Carroll's minimalism "
    "principle is \"the smallest amount of information necessary to "
    "achieve the reader's goals,\" and unrequested background is exactly "
    "the surplus that principle targets. source: "
    "https://en.wikipedia.org/wiki/Minimalism_(technical_communication)"
)
BARE_SECTION_HEADER = "## Rules"


def test_relocation_rule_accepted_via_move_verb():
    r = classify_block(RELOCATION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_bare_section_header_not_counted_as_block():
    text = f"{BARE_SECTION_HEADER}\n\n{RELOCATION_RULE}"
    blocks = _blocks_from_text(text)
    assert len(blocks) == 1
    assert blocks[0].strip() == RELOCATION_RULE.strip()


def test_evaluate_real_minimalism_axis_excerpt_counts_relocation_rule():
    text = f"{BARE_SECTION_HEADER}\n\n{RELOCATION_RULE}\n\n{REMOVAL_RULE}"
    report = evaluate(text, floor=2, axes=["minimalism-scoping"])
    assert report["accepted_count"] == 2
    assert report["count_ok"]
    assert report["passed"]


# issue #1174 gate fix 3 — has_choice redesign: prescriptive content =
# verb-lexicon hit OR contrast/threshold markers (numeric target, em-dash
# prescription, rather-than/instead-of, imperative opening verb). These
# are the exact 12 blocks the pre-fix gate rejected from
# tokenmaxxxer/technical-writing-rulebook PR #25 (branch
# issue-1174/operational-playbook) despite being genuine, sourced,
# condition-gated decision rules with no verb-lexicon hit.
NUMERIC_TARGET_RULE = (
    "1. When drafting an instructional sentence, target roughly 15-20 "
    "words — the Oxford guide to plain English recommends sentences of "
    "15 to 20 words, and sentence length in words correlates negatively "
    "with readability across a century of studies. source: "
    "https://www.trinka.ai/blog/how-sentence-length-variation-improves-academic-readability/"
)
GROUP_UNDER_RULE = (
    "7. When a procedure has more than ~7 sequential steps, group them "
    "under subheadings by phase rather than leave one flat numbered "
    "list — working memory is the limiting resource at every "
    "granularity of the document. source: "
    "https://readabilityformulas.com/how-to-measure-cognitive-reading-load-to-improve-readability-of-any-text/"
)
SCOPE_IT_TO_RULE = (
    "3. When onboarding documentation is the reader's first contact, "
    "scope the fastest path so a working first call lands in under ~10 "
    "minutes — documentation that fails this window measurably loses "
    "developers to alternatives. source: "
    "https://www.digitalapi.ai/blogs/how-api-documentation-improves-developer-adoption"
)


def test_numeric_target_rule_accepted_without_lexicon_verb():
    r = classify_block(NUMERIC_TARGET_RULE)
    assert r["accepted"]
    assert r["reasons"] == []


def test_group_under_rule_accepted():
    r = classify_block(GROUP_UNDER_RULE)
    assert r["accepted"]


def test_scope_it_to_rule_accepted():
    r = classify_block(SCOPE_IT_TO_RULE)
    assert r["accepted"]


def test_technical_writing_pr25_fixture_passes_50_of_50():
    """derived: gh pr diff 25 --repo tokenmaxxxer/technical-writing-rulebook
    (branch issue-1174/operational-playbook), the five playbook/*.md
    files' added content reconstructed from the PR diff's '+' lines,
    unmodified. This is the real fixture named in the issue: 50 rule
    blocks across doc-type-selection, minimalism-scoping,
    style-guide-compliance, structure-comprehension, persuasion-trust."""
    files = {
        "doc-type-selection.md": _DOC_TYPE_SELECTION_MD,
        "minimalism-scoping.md": _MINIMALISM_SCOPING_MD,
        "style-guide-compliance.md": _STYLE_GUIDE_COMPLIANCE_MD,
        "structure-comprehension.md": _STRUCTURE_COMPREHENSION_MD,
        "persuasion-trust.md": _PERSUASION_TRUST_MD,
    }
    text = "\n\n".join(files.values())
    report = evaluate(text, floor=50, axes=[
        "doc-type-selection", "minimalism-scoping", "style-guide-compliance",
        "structure-comprehension", "persuasion-trust",
    ])
    rejects = [r for r in report["blocks"] if not r["accepted"]]
    assert report["accepted_count"] == 50, [
        (r["summary"], r["reasons"]) for r in rejects
    ]
    assert report["count_ok"]
    assert report["passed"]


def test_negative_fixtures_still_reject_after_redesign():
    """The has_choice redesign (verb lexicon OR contrast/threshold
    markers) must not turn glossary or uncited blocks into acceptances."""
    r = classify_block(GLOSSARY_LINE)
    assert not r["accepted"]
    uncited = (
        "- When the field is numeric, target a value between 1 and 10, "
        "rather than free text."
    )
    r2 = classify_block(uncited)
    assert not r2["accepted"]
    assert any("source" in reason for reason in r2["reasons"])


# issue #1174 gate fix 3 — the five playbook/*.md files' content from
# tokenmaxxxer/technical-writing-rulebook PR #25, branch
# issue-1174/operational-playbook (gh pr diff 25, '+' lines), verbatim.

_DOC_TYPE_SELECTION_MD = """---
axis: doc-type-selection
rule_count_floor: 10
---

# Doc-type selection (Diátaxis)

Decision rules for choosing exactly one Diátaxis quadrant per deliverable
(this rulebook's own `produces.doc-type` field). Research trail: layer 2
(named methodology, Diátaxis, verified at source) plus layer 1
(practitioner usage patterns as documented by the framework's own
maintainers and adopting orgs).

## Rules

1. When the reader's stated goal is "I want to learn by doing and have
   no working knowledge yet," choose **tutorial** — a tutorial puts the
   reader "on rails" toward one fixed destination with exact steps and
   no decision points, because a beginner cannot yet evaluate branches.
   source: https://diataxis.fr/start-here/

2. When the reader already has baseline competence and states a
   concrete task ("how do I do X"), choose **how-to guide**, not
   tutorial — how-to guides "help the reader reach a destination of
   their choosing" rather than a fixed one, so branching and
   prerequisites are acceptable where a tutorial would forbid them.
   source: https://diataxis.fr/

3. When the reader is mid-task and needs to look up a fact (a flag, a
   parameter, a field, a limit) rather than be taught, choose
   **reference** — reference is "factual, precise, and structured to
   help find specific details quickly," organized by the product's own
   structure, not by the reader's task sequence. source:
   https://diataxis.fr/

4. When the reader asks "why does it work this way" rather than "how do
   I do X," choose **explanation** — explanation is the only quadrant
   whose job is background/rationale rather than action, and mixing
   task steps into it re-creates the how-to/explanation confusion the
   framework exists to prevent. source: https://diataxis.fr/

5. Under a stated deadline of "first successful call in under 10
   minutes" (an onboarding artifact), choose **tutorial**, not
   reference — reference material assumes the reader can already
   navigate the product's structure, which a brand-new reader cannot;
   documentation that fails this window measurably loses developers to
   alternatives. source:
   https://www.digitalapi.ai/blogs/how-api-documentation-improves-developer-adoption

6. When a single draft's outline mixes conceptual "why" prose with
   numbered action steps, split it into two documents (explanation +
   how-to/tutorial) rather than keep the mixed draft as one — Diátaxis
   treats action-oriented and cognition-oriented content as
   orthogonal axes precisely because a reader mid-task cannot
   efficiently filter out background prose, and a reader seeking
   understanding cannot efficiently filter out step numbering. **REMOVAL**:
   cut whichever half doesn't match the file's own doc-type before
   publishing, don't keep both halves "for completeness." source:
   https://diataxis.fr/

7. When the reader already knows the tool and just needs a parameter's
   exact type/default/range, do not answer with a tutorial-style
   walkthrough — pick reference and drop any narrative framing
   ("First, let's..."), because reference's value is being scannable,
   and narrative framing forces linear reading against the reader's
   actual lookup behavior. source: https://diataxis.fr/

8. When a document was drafted as a tutorial but review shows the
   audience is not actually first-time users (e.g. it's gated behind an
   account they already have), reclassify to how-to and **REMOVE** the
   "on rails"/single-path framing — retaining tutorial framing for an
   audience that already has working knowledge produces exactly the
   condescension the style-guide-compliance axis flags separately.
   source: https://diataxis.fr/start-here/

9. When users progress through a product over time (new → competent →
   expert), do not try to serve every stage from the same document —
   users naturally move tutorial → how-to → reference → explanation as
   competence grows, so a single "one true doc" for a topic under-serves
   both ends; split by stage instead of merging. source:
   https://diataxis.fr/

10. **REMOVAL**: when a topic already has both a how-to guide and a
    reference entry for the same operation, do not add a third
    "overview" doc that restates both — merging duplicate framing
    across quadrants is the specific redundancy the minimalism axis's
    rule 1 also flags; the fix here is to delete the overlapping
    overview draft entirely rather than trim it, since its entire
    content already exists in the other two quadrants. source:
    https://diataxis.fr/ (four-quadrant orthogonality implies no
    quadrant should duplicate another's content)"""

_MINIMALISM_SCOPING_MD = """---
axis: minimalism-scoping
rule_count_floor: 10
---

# Minimalism / scoping

Decision rules for what to include vs. cut per section (this rulebook's
`produces.minimalism check` field). Research trail: layer 1 (practitioner
depth per John Carroll's minimalist-instruction canon) plus layer 3
(academic: subtraction neglect, cognitive-load/extraneous-load theory).

## Rules

1. When a draft section restates information already stated earlier in
   the same doc or in a linked doc, **REMOVE** the restatement and link
   instead — duplicate information "makes the page more dense with text
   but not with information," and progressive disclosure's value is
   destroyed once duplicated content forces the reader to re-verify
   which copy is current. source:
   https://www.algolia.com/blog/ux/information-density-and-progressive-disclosure-search-ux

2. When a section explains background the reader does not need to
   complete the immediate task, move it to an explanation doc or a
   collapsed/linked aside rather than inline it — Carroll's minimalism
   principle is "the smallest amount of information necessary to
   achieve the reader's goals," and unrequested background is exactly
   the surplus that principle targets. source:
   https://en.wikipedia.org/wiki/Minimalism_(technical_communication)

3. When drafting a first version of any procedure, default to writing
   the task-oriented steps first and add explanatory prose only where a
   reviewer flags a specific comprehension gap — Carroll found
   "training materials should present short task-oriented chunks, not
   lengthy, monolithic documentation," so explanation should be pulled
   in reactively, not drafted in by default. source:
   https://www.researchgate.net/publication/3229757_John_Carroll's_The_Nurnberg_Funnel_and_Minimalist_Documentation

4. When advanced/edge-case options exist alongside a common path, do not
   inline them into the main procedure — group them behind a labeled,
   collapsed subsection (progressive disclosure) so the common path
   stays short; multiple advanced-feature levels should nest into
   meaningful categories rather than flatten into one long list. source:
   https://www.webfx.com/blog/web-design/progressive-disclosure-in-user-interfaces/

5. When you are deciding how to shorten an over-long draft, actively
   search for content to CUT, not just content to compress — people
   "systematically default to searching for additive transformations
   and consequently overlook subtractive transformations," and this
   default gets worse "under higher cognitive load" (i.e., exactly when
   editing a dense draft), so cutting must be a deliberate, separate
   pass, not a byproduct of line-editing. source:
   https://www.nature.com/articles/s41586-021-03380-y

6. **REMOVAL**: when a draft outline has a section whose only content is
   definitional ("X is a mechanism that...") with no task or decision
   attached to it, delete the section rather than shrink it — a
   glossary-shaped paragraph inside a task-oriented doc adds surface
   area without adding actionable information, the same defect this
   program's depth-gate rejects in playbook rule blocks. source:
   https://www.researchgate.net/publication/3229757_John_Carroll's_The_Nurnberg_Funnel_and_Minimalist_Documentation

7. When a subtractive edit is available (delete a redundant paragraph)
   and an additive edit is also available (add a clarifying sentence)
   for the same comprehension problem, evaluate the subtractive option
   first and explicitly — explicitly reminding yourself that subtraction
   is on the table, or "putting a cost on adding parts while making
   removing parts free," measurably increases the rate at which
   subtractive fixes actually get chosen. source:
   https://sciencedaily.com/releases/2021/04/210407135801.htm

8. When boilerplate content (standard disclaimers, repeated setup steps)
   recurs across many docs, **REMOVE** it from each doc and centralize it
   in one linked location instead of leaving N copies — "consolidating
   redundant instructions and filtering recurring boilerplate content"
   is named directly as an extraneous-cognitive-load fix. source:
   https://arxiv.org/pdf/2605.19174

9. When a review finds a paragraph that took effort to write but does
   not change what the reader does next, cut it even though cutting
   feels like a loss of invested effort — minimalism's target is
   reader-goal alignment, not authorial completeness; the doc's
   quality bar is what remains being justified by the target-reader
   note, not by how much was written. source:
   https://en.wikipedia.org/wiki/Minimalism_(technical_communication)

10. When error-recovery content is missing (the user hits a failure and
    the doc has no path back), add it even though this axis otherwise
    biases toward cutting — Carroll's principle set explicitly requires
    "training materials and activities... provide for error recognition
    and recovery," so this is the one place the minimalism axis calls
    for addition, and it should be named as the deliberate exception
    rather than silently contradicting rules 1-9. source:
    https://www.instructionaldesign.org/theories/minimalism/"""

_STYLE_GUIDE_COMPLIANCE_MD = """---
axis: style-guide-compliance
rule_count_floor: 10
---

# Style-guide compliance (Google Developer Documentation Style Guide)

Decision rules for the `produces.style-guide compliance note` field.
Research trail: layer 2 (named standard, verified at source:
developers.google.com/style, plus the Federal plain-language guidelines
as a second named standard for corroboration/conflict-checking).

## Rules

1. When writing an instruction step, use imperative mood ("Click
   Submit"), not descriptive mood ("You should click Submit" / "The
   user clicks Submit") — the style guide instructs writers to "use the
   imperative mood to guide the reader effectively." source:
   https://developers.google.com/style

2. When a sentence has an actor performing an action, write it in
   active voice with the actor as subject — "use active voice: make
   clear who's performing the action" — because passive voice hides the
   actor exactly where a reader needs to know who/what does the work.
   source: https://developers.google.com/style

3. When addressing the reader, use second person ("you") and present
   tense, not third person or future tense — this is a named,
   consistent convention across the guide's person/tense sections, and
   switching person mid-doc is a compliance deviation to flag. source:
   https://developers.google.com/style/person?hl=en

4. When choosing a term that has a preferred/discouraged pair in the
   guide's word list (e.g. avoid ableist or unclear terms), use the
   word-list entry's preferred form — the word list exists specifically
   so writers don't re-derive terminology choices per document. source:
   https://developers.google.com/style/word-list

5. When tone risks becoming either stiff/formal or overly playful,
   target "conversational, friendly, and respectful without... slang or
   being overly colloquial" — like "a knowledgeable friend," not
   "pedantic or pushy" and not "super-entertaining." Both extremes are
   named failure modes, not just "be more casual." source:
   https://developers.google.com/style/tone

6. When an instruction could be phrased as a request ("Please click
   Submit") or a direct command ("Click Submit"), prefer the direct
   command and drop "please" — the guide calls for "ensur[ing]
   politeness without overusing 'please' in instructions," so
   politeness padding on every step is itself a deviation. **REMOVAL**:
   strip "please" from routine steps; keep it only where an action has
   real cost to the reader (e.g. destructive operations). source:
   https://developers.google.com/style/tone

7. When a legal/government-adjacent doc needs a second corroborating
   source for active-voice enforcement, cross-check against the Federal
   Plain Language Guidelines: "in an active sentence, the person or
   agency that's acting is the subject," matching Google's own rule —
   record convergence (no conflict) rather than picking one arbitrarily
   when both style authorities agree. source:
   https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/conversational/use-active-voice.md

8. When complex material has more than ~3 parallel conditions or
   options, restructure it as a bulleted list or table rather than a
   run-on sentence — plain-language guidance names "bullets and tables"
   for "complex material" as a distinct design feature, not just a
   formatting preference. source: https://digital.gov/guides/plain-language

9. **REMOVAL**: when a passive-voice sentence is found in review and no
   actor is named, do not just "soften" it — rewrite to name the actor
   and delete the passive construction outright; a partial fix (passive
   sentence trimmed for length but left passive) does not satisfy this
   axis's rule 2. source: https://developers.google.com/style

10. When a term is genuinely necessary but jargon to the target reader
    (per the target-reader note), keep the term but add a first-use
    gloss rather than either (a) silently using it unglossed or (b)
    avoiding the correct technical term altogether — "common, everyday
    words except for necessary technical terms" licenses jargon only
    when paired with explanation, not as an either/or choice. source:
    https://digital.gov/guides/plain-language"""

_STRUCTURE_COMPREHENSION_MD = """---
axis: structure-comprehension
rule_count_floor: 10
---

# Structure for comprehension (cognitive load)

Decision rules for sentence/paragraph/section structure. Research trail:
layer 3 (academic: cognitive load theory applied to sentence
comprehension, working-memory constraints on reading).

## Rules

1. When drafting an instructional sentence, target roughly 15-20 words —
   "the Oxford guide to plain English recommends sentences of 15 to 20
   words," and sentence length in words correlates negatively with
   readability across a century of studies. source:
   https://www.trinka.ai/blog/how-sentence-length-variation-improves-academic-readability/

2. When a sentence carries more than one independent clause plus a
   conditional, split it into two sentences — "longer sentences can be
   harder to process because they contain more ideas, clauses, and
   complex structures," and working memory is the bottleneck cognitive
   load theory identifies, not vocabulary difficulty alone. source:
   https://readabilityformulas.com/how-to-measure-cognitive-reading-load-to-improve-readability-of-any-text/

3. When a passage must carry technical detail (a caveat, a condition, a
   numeric threshold), allow a longer sentence there but keep the
   surrounding sentences short — sentence-length variation "supports
   chunking, with shorter sentences giving clean stopping points," so
   uniform shortening isn't the goal, controlled variation is. source:
   https://www.trinka.ai/blog/how-sentence-length-variation-improves-academic-readability/

4. When writing for readers who may be non-native speakers, using
   assistive tech, or have attention/reading disabilities, bias toward
   the short end of the 15-20 word range — shorter sentences
   "particularly benefit[] people with dyslexia, ADHD, non-native
   English speakers, and screen reader users," so accessibility need
   tightens this rule rather than relaxing it. source:
   https://www.siteimprove.com/blog/readability-plain-language-wcag/

5. When a single paragraph or chunk risks holding more than
   ~130-150 characters of new information before the next natural
   break, insert a break (list item, subheading, or sentence split) —
   text chunks in that range were found "the most appropriate length to
   enhance learners' text comprehension," correlated with working-memory
   capacity limits. source:
   https://readabilityformulas.com/how-to-measure-cognitive-reading-load-to-improve-readability-of-any-text/

6. **REMOVAL**: when editing a long sentence for comprehension, first try
   deleting subordinate clauses that don't change what the reader does
   next, before restructuring the sentence into multiple shorter ones —
   the cognitive-load fix is fewer ideas per sentence, and deletion
   reduces idea-count without adding new sentences to track. source:
   https://readabilityformulas.com/how-to-measure-cognitive-reading-load-to-improve-readability-of-any-text/

7. When a procedure has more than ~7 sequential steps, group them under
   subheadings by phase rather than leave one flat numbered list — this
   mirrors the same chunking rationale as rule 5 applied at the
   section level, not just the sentence level: working memory is the
   limiting resource at every granularity of the document. source:
   https://readabilityformulas.com/how-to-measure-cognitive-reading-load-to-improve-readability-of-any-text/

8. When a sentence's syntactic subject and its main verb are separated
   by a long embedded clause (long linear distance / high structural
   density), rewrite so subject and verb sit close together — memory
   load in sentence comprehension is driven by both linear distance and
   structural density between dependent elements, not sentence length
   alone. source: https://arxiv.org/pdf/2509.20916

9. When a draft uses a rare or highly technical word where a common
   synonym exists with no loss of precision, substitute the common
   word — "familiar words reduce processing time," an independent lever
   from sentence length. source:
   https://www.siteimprove.com/blog/readability-plain-language-wcag/

10. **REMOVAL**: when a sentence contains a hedge or filler clause ("it
    should be noted that," "in order to") that adds words without adding
    an idea, delete it outright rather than compress it — this is
    distinct from rule 6 (structural clause deletion): rule 6 targets
    subordinate content clauses, this targets zero-information filler
    phrasing, so both passes are needed on a dense draft. source:
    https://www.trinka.ai/blog/how-sentence-length-variation-improves-academic-readability/"""

_PERSUASION_TRUST_MD = """---
axis: persuasion-trust
rule_count_floor: 10
---

# Persuasion and trust (adoption-facing docs)

Decision rules for docs whose target-reader must decide to adopt/trust,
not just execute a known task. Research trail: layer 3 (academic:
Elaboration Likelihood Model, central vs. peripheral persuasion routes)
plus layer 1 (practitioner: developer-adoption documentation research).

## Rules

1. When the target reader is technically motivated and evaluating
   whether to adopt (high elaboration likelihood — they will actually
   read the argument), persuade through the central route: concrete
   working examples, exact API behavior, verifiable claims — not
   testimonials or brand framing — because "central route processing"
   is what drives agreement when the reader has motivation and ability
   to elaborate. source: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1679853/full

2. When the target reader is a decision-maker skimming (low elaboration
   likelihood — e.g. a manager evaluating a tool, not the engineer who
   will use it), peripheral cues (named companies using it, security
   certifications, response-time SLAs) carry real persuasive weight and
   should be surfaced early — "source factors... serve as simple
   acceptance or rejection cues when the elaboration likelihood is
   low." source: http://www.communicationcache.com/uploads/1/0/8/8/10887248/source_factors_and_the_elaboration_likelihood_model_of_persuasion.pdf

3. When onboarding documentation is the reader's first contact, scope
   the fastest path so a working first call lands in under ~10 minutes
   — "if a developer can't figure out how to make a first successful
   API call in under 10 minutes, chances are they'll look for
   alternatives," so this is a hard adoption-loss threshold, not a
   nice-to-have speed target. source:
   https://www.digitalapi.ai/blogs/how-api-documentation-improves-developer-adoption

4. When a doc can offer either a live/sandbox example or a
   read-only code snippet for the same feature, prefer the runnable
   sandbox — "developers who can test before committing are more
   likely to proceed, while those who can only test in production are
   more likely to delay... or abandon," so runnability itself is a
   trust lever, independent of prose quality. source:
   https://www.digitalapi.ai/blogs/how-api-documentation-improves-developer-adoption

5. **REMOVAL**: when a doc's draft contains marketing-style superlative
   claims ("blazing fast," "effortless") with no example or number
   backing them, delete the claim rather than tone it down — for a
   high-elaboration audience, an unverifiable peripheral claim inside
   otherwise technical prose reads as low-credibility noise and can
   undercut trust in the surrounding factual claims. source:
   https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1679853/full
   (peripheral cues persuade only when elaboration is low; injecting
   them into a high-elaboration context has no established positive
   effect and risks credibility loss)

6. When personal relevance is low (a reader browsing docs for a tool
   they don't yet need), do not front-load dense technical argument —
   motivation and ability to elaborate are shaped by "personal
   relevance, prior knowledge, and contextual complexity," so a
   low-relevance reader needs a peripheral hook (a concrete outcome, a
   short use-case) before the central-route detail, or they disengage
   before reaching it. source:
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8130952/

7. When documentation quality is the deciding factor being reported to
   stakeholders, treat clear docs as a strategic asset, not a
   cosmetic pass — "great documentation isn't a 'nice-to-have,' it's a
   strategic asset that builds trust and drives adoption" — so a
   review that scopes doc work as pure cleanup is scoping it wrong.
   source: https://builtin.com/articles/developer-documentation-as-product

8. When a claim about the product needs to persuade a skeptical
   technical reader, cite the verifiable artifact (a benchmark number,
   a spec section, a reproducible command) inline next to the claim
   rather than in an appendix — central-route persuasion depends on the
   reader being *able* to elaborate on the argument, which requires the
   evidence to be adjacent, not just present somewhere in the document.
   source: http://www.communicationcache.com/uploads/1/0/8/8/10887248/source_factors_and_the_elaboration_likelihood_model_of_persuasion.pdf

9. When a reader has low prior knowledge of the domain (per the
   target-reader note), do not rely on peripheral authority cues alone
   ("used by X") to carry adoption — low prior knowledge lowers ability
   to elaborate but the ELM literature ties source-cue reliance to low
   motivation, not low ability; a low-knowledge but motivated reader
   still needs central-route content, just written at their
   comprehension level (defer to the structure-comprehension axis for
   how). source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8130952/

10. **REMOVAL**: when a doc repeats the same trust-building claim (e.g.
    "used in production by thousands of teams") in multiple sections,
    cut it down to one placement near the reader's decision point (e.g.
    the top of an adoption-facing overview) — repetition of a peripheral
    cue does not compound its persuasive value in the ELM model and
    instead reads as padding, contradicting this rulebook's own
    minimalism axis. source:
    https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1679853/full"""
