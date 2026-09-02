# Spaced-Repetition Review Scheduler — Design

## 0. Note on repo state

This repository currently contains no application code — only
`docs/specs/requirement-digest.md` and `docs/specs/approvers.md`. The single
requirement recorded there (R1) is about an unvalidated AI comprehension-gap
tutor and is still `[proposed]`; it is not the same feature as a
spaced-repetition scheduler, and there's no existing card/deck/user schema or
mobile/web codebase to anchor this design against. What follows is therefore
a greenfield proposal, not a description of how this fits existing code.

Before an implementation issue is opened, the team's own gate process
(`requirement-digest.md`, referenced by issue #1017) expects a cited R-ID.
This feature doesn't have one yet — worth adding an `R2:` entry (status
`proposed`) before work starts, so the linkage gate doesn't block the PR.

## 1. Goal and constraints

- Given a student's history of past answers (correct/incorrect, and ideally
  a difficulty rating), decide which flashcards are due for review today.
- Expose that "due list" identically to a mobile app and a web app — same
  answer, same ordering, no drift between clients.
- Mobile needs to work when briefly offline (reviewing on a bus/subway);
  web is generally online-only.

## 2. Core decision: scheduling logic lives on the server, once

The algorithm must **not** be reimplemented per client. If mobile and web
each embed their own copy of the scheduling math, they will eventually
disagree on what's "due" after a platform-specific bug fix, a data model
change, or an algorithm tune — and that's a confusing, hard-to-debug class of
bug for a review app specifically (the one thing users trust it to get
right). So:

- A single backend service owns the algorithm and is the source of truth.
- Both clients are thin: they call an API for "what's due" and "record this
  answer," and render/collect input. No scheduling math on-device, beyond
  the small amount needed for offline queuing (see §6).

## 3. Data model

Two tables, kept deliberately separate:

**`review_log`** (append-only, immutable)
| column | notes |
|---|---|
| id | |
| user_id | |
| card_id | |
| answered_at | timestamp |
| grade | e.g. again/hard/good/easy, or correct/incorrect |
| response_time_ms | optional, useful signal for difficulty |

Append-only because it's the durable record everything else is derived
from — if the scheduling algorithm changes later, we can recompute all
derived state from this log instead of losing history.

**`card_review_state`** (one row per user×card, mutable, derived)
| column | notes |
|---|---|
| user_id, card_id | composite key |
| due_at | when this card next becomes due |
| stability, difficulty | algorithm-specific parameters |
| reps, lapses | counters |
| last_reviewed_at | |

`card_review_state` is a cache/projection of `review_log`, not a second
source of truth — it exists so "give me due cards" is a fast indexed query
(`WHERE user_id = ? AND due_at <= now()`) instead of replaying the whole
log on every request.

## 4. Algorithm choice

Recommend **FSRS** (Free Spaced Repetition Scheduler) over classic SM-2:
better-documented predictive accuracy, actively maintained open
implementations (`ts-fsrs`, `py-fsrs`, etc.), and it's become the de facto
standard (Anki ships it). Use an existing library rather than hand-rolling
the math — this is the kind of thing that's easy to get subtly wrong and
hard to notice until retention data looks off weeks later.

Keep the algorithm implementation as a **pure function**: `(currentState,
grade, now) -> newState`. No I/O, no DB access inside it. That makes it
trivial to unit-test with known input/output pairs and to swap or A/B test
algorithms later without touching persistence or API code.

## 5. Module breakdown

```
services/review-scheduler/
  algorithm/           # pure FSRS (or chosen algo) implementation, no I/O
  domain/
    review_service.py  # orchestrates: log answer, update state, query due list
  api/
    routes.py           # REST endpoints, thin — validate input, call domain, serialize
  repository/
    review_log_repo.py
    card_review_state_repo.py
  jobs/
    due_cache_warmer.py # optional: precompute due lists off the request path (see §7)
```

The dependency direction is one-way: `api` → `domain` → `repository`/`algorithm`.
`algorithm` has zero dependencies on the others, which is what keeps it
independently testable.

## 6. API surface (consumed identically by mobile and web)

```
GET  /v1/reviews/due?limit=50
     -> [{ card_id, due_at, ... }]

POST /v1/reviews/{card_id}/answer
     body: { grade, answered_at, response_time_ms? }
     -> { new_due_at, reps, lapses }
```

Both clients hit the same endpoints — there is no separate "mobile API" and
"web API." A thin generated/shared client SDK (e.g. an OpenAPI-generated
client) is fine per-platform, but it should contain no business logic, only
HTTP plumbing and typed models.

## 7. Performance note

`WHERE due_at <= now()` is a simple indexed range query, not something that
generally needs precomputation. The `jobs/due_cache_warmer.py` line above is
explicitly optional — only worth adding if a specific user or admin view
(e.g., "review load forecast for the next 7 days") turns out to be slow in
practice. Don't build it up front.

## 8. Mobile offline support

Mobile is the one place a small amount of client-side logic is justified,
but it's a queue, not a scheduler:

- On answer, if offline: store `{card_id, grade, answered_at}` in a local
  outbox and optimistically remove the card from the locally cached due
  list for this session.
- On reconnect: replay the outbox against `POST /reviews/{card_id}/answer`
  in order (using the client-recorded `answered_at`, not server receipt
  time, so scheduling stays accurate).
- Server remains authoritative: if the same card was somehow also answered
  from web in the interim, both answers land in `review_log` in
  `answered_at` order and `card_review_state` reflects the latest — no
  special conflict resolution needed because the log is append-only and
  order is well-defined by timestamp.

## 9. Testing strategy

- **Algorithm**: pure unit tests, including golden-value tests against the
  reference FSRS implementation's known test vectors.
- **Domain/repository**: integration tests against a real (test) DB —
  answer a card, assert `card_review_state.due_at` moved and `review_log`
  got a row.
- **API**: contract tests per endpoint (request/response shape), run
  against both a "web-style" and "mobile-style" client stub to catch
  accidental platform-specific behavior early.
- **Cross-client parity**: one end-to-end test that fetches the due list,
  submits an answer, and refetches — asserting the card's new `due_at`
  matches what the algorithm unit tests predict for that grade.

## 10. Privacy note

`review_log` is per-user learning history. Scope all queries by `user_id`
at the repository layer (never trust a client-supplied user id without
auth), and support delete/export of a user's `review_log` +
`card_review_state` rows for account-deletion / data-request handling.

## 11. Open questions for the team

- Grading scale: binary correct/incorrect, or 4-point (again/hard/good/easy)?
  FSRS is designed for the latter and performs better with it, but it's a
  bigger UI lift on both clients.
- Deck/card ownership model doesn't exist yet in this repo — this design
  assumes `card_id` and `user_id` are already meaningful foreign keys
  elsewhere; that dependency should be resolved before this is scoped as
  an issue.
- Per the repo's own gate process, this needs an R-ID in
  `requirement-digest.md` before an implementation issue can cite it.
