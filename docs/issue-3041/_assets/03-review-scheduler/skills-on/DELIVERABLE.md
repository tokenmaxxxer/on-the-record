# Spaced-Repetition Review Scheduler — Design

## Assumptions (repo has no existing app code to anchor to)

This repo currently contains only discovery docs, not a mobile/web codebase, so I can't
tell what languages or frameworks the mobile and web apps are actually built in. The
design below is stack-agnostic on purpose. Before implementation, confirm:

- Is there already a backend/API server, or would this scheduler introduce one?
- Do mobile and web already share a backend, or does each talk to its own service?
- Is offline use required on mobile (student reviewing on a subway with no signal)?

If those answers change the picture, the module boundaries below still hold — only the
transport (REST/GraphQL/RPC) and where the "client" code lives would change.

## Core decision: one scheduling brain, two thin clients

The scheduler must not be implemented twice (once per platform). Two implementations
of a spaced-repetition algorithm will drift — a card marked "easy" on web and "hard" on
mobile due to a rounding or interval-formula difference is a correctness bug that's hard
to catch in QA and erodes trust in the "due today" list. So:

- All scheduling logic (deciding intervals, due dates, ease factors) lives **server-side**,
  in a single service.
- Mobile and web are both just clients of one API: `GET /reviews/due` and
  `POST /reviews/{cardId}/answer`. Neither app computes due dates itself.
- If mobile needs offline review (recommended for a study app — students study without
  connectivity), the client caches the due list and queues answers locally, but the
  *authoritative* recompute still happens server-side on next sync. The client never
  owns the algorithm, only a temporary offline queue.

## Module breakdown

```
scheduler/
  core/                  # pure logic, no I/O, no framework deps
    algorithm.py          # e.g. SM-2-derived interval/ease-factor calc
    models.py              # CardState, ReviewLog, DueDecision (plain data types)
  service/               # application layer, orchestrates core + persistence
    due_cards.py           # "what's due for user X today" query logic
    record_answer.py       # ingest an answer, call core.algorithm, persist new state
  api/                   # HTTP/RPC boundary consumed by both clients
    routes.py              # GET /reviews/due, POST /reviews/{cardId}/answer
    serializers.py
  persistence/
    repository.py          # CardState/ReviewLog storage, behind an interface
  tests/
    test_algorithm.py       # exhaustive unit tests on core, no DB needed
    test_due_cards.py
    test_api_contract.py
```

The critical boundary is **`core/` has zero I/O and zero framework dependencies**. It's
pure functions: `next_state(current_state, answer_quality, reviewed_at) -> CardState`.
This is the highest-risk, highest-value code to get right (it's the actual "spaced
repetition" logic), so it should be trivially unit-testable and independently
verifiable against known SM-2 test vectors, without spinning up a DB or server.

## Data model (minimum viable)

- `flashcards`: id, deck_id, front, back, created_by, created_at
- `card_review_state`: (user_id, card_id) → ease_factor, interval_days, repetitions,
  due_at, last_reviewed_at
- `review_log`: append-only history — user_id, card_id, answered_at, quality/correctness,
  response_time_ms (optional, useful later for difficulty calibration)

`review_log` is append-only and is the source of truth for "past answers." Never
mutate it — `card_review_state` is a derived/cached projection computed from it (or
incrementally updated per answer, same result). Keeping the log append-only means the
scheduling algorithm can be changed later and *replayed* over history without losing
data, which matters a lot for a first version of an algorithm the team will want to
tune.

## API surface exposed to both apps

- `GET /reviews/due?deck_id=&limit=` → ordered list of cards due now, plus count due
  today/this week for the UI's progress indicators.
- `POST /reviews/{cardId}/answer` → body: `{quality: 0-5 (or correct/incorrect + confidence)}`,
  returns the updated `CardState` (new due date) so clients can show "see you again in
  3 days" without a second round-trip.

Both mobile and web call the exact same endpoints. No platform-specific scheduling
endpoints — if one client needs different due-list shaping (e.g., mobile wants a
smaller page size for a swipe UI), that's a query param, not a different code path.

## Algorithm choice

Start with a well-known, well-tested formula (SM-2 or a documented variant like
Anki's) rather than inventing one. Spaced repetition has decades of validated
research behind SM-2-family algorithms; a novel algorithm is a research project, not
a v1 feature. Isolating it in `core/algorithm.py` behind a stable interface means it
can be swapped or A/B tested later without touching the API or either client.

## Suggested build order

1. `core/algorithm.py` + exhaustive unit tests against known SM-2 test vectors. No DB,
   no API — this can be reviewed and validated on its own.
2. `persistence/` + `service/` wired to a real (or in-memory, for tests) datastore.
3. `api/` routes, with contract tests that assert response shape (both clients will
   depend on this contract, so lock it early).
4. Mobile and web integration, in parallel — both are now just HTTP clients against a
   stable contract from step 3.
5. (If needed) offline queue on mobile, built against the same API — batched
   `POST /reviews/.../answer` calls replayed on reconnect.

## Testing strategy

- `core/`: pure unit tests, deterministic, no mocks needed — this is where algorithm
  correctness bugs actually live, so it deserves the heaviest test investment.
- `service/`: integration tests with a real/in-memory DB, covering "due list excludes
  cards not yet due," "answering a card updates its due date," timezone edge cases
  (a "day" boundary for a student depends on their local time, not UTC midnight).
- `api/`: contract tests both client teams can run against to verify they're not
  drifting from the actual response shape.

## Open questions to resolve with the team before coding

- Timezone handling for "due today" — per-user local day boundary, not server UTC.
- New-card introduction rate (how many new cards per day get added to the due queue,
  vs. only reviewing already-seen cards) — affects `due_cards.py` query logic.
- Whether "quality" of an answer is a 0-5 self-rating (classic SM-2) or inferred from
  correct/incorrect + response time — this changes the `core/algorithm.py` input shape
  and is worth deciding before writing it, not after.
