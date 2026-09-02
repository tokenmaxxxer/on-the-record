# Spaced-repetition review scheduler — structural design

## Repo state, as found

As of this writing the repo contains no application code at all — only
product-discovery artifacts under `docs/issue-1` (the comprehension-gap
discovery report) and `docs/issue-5` (that job's one-pager), plus two
repo-process spec files (`docs/specs/approvers.md`,
`docs/specs/requirement-digest.md`). There is no `package.json`, no
`CLAUDE.md`, no source tree, no existing layering or naming convention
anywhere. So this is a genuine green-field design: nothing below "matches
existing conventions" because none exist yet. If a team member later reads
this and finds a codebase already in place, treat this document as the
proposal that predates it, not as a description of what's there.

## Relation to the comprehension-gap job (issue-5) — brief

Keep this **structurally separate**, not integrated, at least for now:

- Different job, different moment. Issue-5's one-pager targets the
  *monitoring* job — an immediate, one-time comprehension check right after
  a solo study session, ending the moment the gap is "visible and located."
  The one-pager is explicit that what the student does next is out of scope
  ("What the student does with that signal ... is outside this product's
  job"). A spaced-repetition scheduler targets a different job entirely:
  durable retention of previously-learned material, reviewed on a
  recurring schedule over days or weeks, independent of any single
  study session.
- Different content shape. The comprehension-gap product's output is a
  located accuracy signal ("section 3 was weak"), not a flashcard. Whether
  that signal could ever seed a flashcard, or nudge a due date, is a real
  question — but answering it requires discovery work issue-5 hasn't done
  (does that product even produce flashcard-shaped content? no evidence
  either way in the landed report), so building that coupling now would be
  inventing a dependency the discovery work hasn't earned.
- Practical implication: no shared domain model, no import between the two
  areas of the codebase. If a future integration is validated, it should
  show up as the scheduler *consuming* a comprehension-signal event through
  the same repository-interface seam described below, not as a merged
  domain model. That's a one-line note to revisit later, not a build item
  now.

## Archetype classification

This isn't one archetype — it's two components, classified separately,
with the boundary between them named explicitly (per the "mixed archetypes"
rule: don't force one archetype onto the whole system).

- **The scheduling algorithm itself → Domain-Rich App (4).** Given a
  card's review history (grades and timestamps), computing the next due
  date and updated scheduling state (interval, ease/difficulty, stability
  — whatever the chosen algorithm's parameters are) is a non-trivial
  business rule that exists independent of any database, any API, any
  client. This is exactly the "rules that exist even without a database"
  test for archetype 4, and it's also the single most important thing
  this system does — worth protecting behind a real domain boundary rather
  than letting it leak into request handlers.
- **The surface that exposes "what's due today" to mobile and web →
  Data-Centric App shape (3), thin.** Recording an answer and reading the
  due list is otherwise CRUD-shaped: parse input, call the domain, persist,
  return. No business logic belongs at this layer — it's a controller that
  hands work to the domain layer described above.

## Why one API, not two client implementations

The single most important structural decision here, stated as a Parnas
question: **what design decision does the scheduling algorithm hide, and
where does that hiding happen?** It must happen in exactly one place. If
the "which cards are due" logic is computed independently by the mobile
app and the web app — even from the same server-stored review history —
the decision is hidden nowhere, both clients will drift out of sync with
each other over time (different rounding, different timezone handling,
different bugs), and a future algorithm change means finding and fixing it
twice. So: mobile and web are both **callers of one backend API**; neither
computes scheduling state locally. This also settles the "expose that list
to both apps" part of the brief structurally, not case-by-case.

## Module layout

```
scheduler/
  domain/                        # zero framework/DB imports
    card.ts                      # Card entity: id, contentRef, ownerId
    review_log.ts                # ReviewLog entry: cardId, gradedAt, grade
    scheduling_state.ts          # value object: interval, ease/difficulty,
                                  #   dueDate — output of the algorithm
    scheduling_algorithm.ts      # pure function:
                                  #   (currentState, grade, reviewedAt) -> newState
                                  #   this is the one thing the whole module
                                  #   exists to protect — see below
    review_history_repository.ts # interface only: append(), forCard(), forStudent()
    card_state_repository.ts     # interface only: get(), save(), dueBefore(studentId, asOf)

  application/                   # depends on domain only, no framework
    record_answer.ts             # use case: append to history, run the
                                  #   algorithm, persist new state
    get_due_cards.ts             # use case: query card_state_repository
                                  #   for studentId + "asOf" timestamp,
                                  #   return ordered queue

  infrastructure/                # depends on domain + application
    <db>_review_history_repository.ts   # implements the domain interface
    <db>_card_state_repository.ts       # implements the domain interface
    clock.ts                            # single source of "now" — see
                                         #   open questions below

  interface/                     # outermost — thin, archetype-3 shaped
    http/
      get_due_cards_controller.ts   # GET /due-cards -> application.get_due_cards
      record_answer_controller.ts   # POST /reviews  -> application.record_answer
```

Both the mobile app and the web app call the same `interface/http`
endpoints; neither imports anything from `domain/` or `application/`
directly.

## What each boundary hides (Parnas test, one sentence each)

- `scheduling_algorithm.ts` hides: **how a graded answer changes when the
  card comes due next.** This is the only file that should ever change
  when the team tunes or swaps the algorithm.
- `*_repository.ts` interfaces hide: **where and how review history and
  scheduling state are stored.** Swapping databases later should touch
  only `infrastructure/`.
- `application/*` hides: **transaction boundaries and authorization** (is
  this student allowed to see/record this card's state) — orchestration,
  not business rules.
- `interface/http/*` hides: **the wire format** (HTTP verbs, status codes,
  request/response shape) — nothing else. If a controller contains
  scheduling logic or a raw query, that's a boundary violation to fix
  immediately, not a tech-debt note.

No two modules hide the same decision; if a future review finds
scheduling logic duplicated into a controller or into a client app, that's
the signal the boundary has already started to erode.

## Testing note

Because the algorithm is a pure function in `domain/`, it should be
unit-testable with synthetic review histories and no database or network
— first review ever, consecutive failures, the exact boundary of "due
today," and the timezone question below are all cheap to cover this way.
That cheapness is the payoff of putting the algorithm in its own
domain-rich module rather than inline in a request handler.

## Open questions this design deliberately leaves unresolved

These are real decisions, not deferred by accident — each needs its own
call before or during implementation, but none of them changes the module
boundaries above:

- **Which algorithm** (SM-2, a Leitner-box variant, FSRS, something
  custom). The domain boundary is designed so this choice is swappable
  without touching application, infrastructure, or interface code — but
  the choice itself isn't made here. Don't introduce a Strategy-pattern
  abstraction for multiple algorithms until there's a second concrete one
  to support; one algorithm, one direct implementation, per the rule of
  three.
- **What counts as "today."** Student local time vs. server UTC changes
  which cards show up as due, especially near midnight. This has to be an
  explicit decision passed into `get_due_cards` (an `asOf` argument, not
  an implicit `now()` call inside the domain layer) — resolving it
  silently inside the algorithm would hide a decision that actually
  belongs to the interface layer, which knows the caller's timezone.
- **Offline mobile review.** If the mobile app needs to let a student
  review cards with no network and sync later, that's a genuinely
  different archetype for that slice (event-driven, idempotent sync
  against the same domain/application core) — not a reason to change
  anything above, but a reason not to assume the HTTP interface layer is
  the only caller of `application/` forever.
