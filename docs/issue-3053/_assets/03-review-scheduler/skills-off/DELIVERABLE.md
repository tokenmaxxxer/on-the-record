# Spaced-repetition review scheduler — design

## Repo state, checked first

As of this writing the repo contains no application code at all — only
product-discovery artifacts:

- `docs/issue-1/` — the user-discovery research behind the "comprehension
  gap" job (evidence tables, verdicts, consult logs).
- `docs/issue-5/` — a one-pager (`docs/issue-5/specs/one-pager.md`) that
  turns issue #1's discovery into a specific job statement: detect,
  in the moment right after independent study, whether a student's felt
  comprehension matches their checked comprehension, and surface *where*
  (which section/concept) it doesn't. Explicitly scoped to *monitoring*
  only — it does not explain material, does not resolve gaps, and does not
  schedule anything.
- `docs/specs/` — a requirement digest and an approvers list, both
  process/governance artifacts, not code.

There is no framework, language, data layer, test setup, or directory
convention anywhere in the tree. This scheduler is therefore a green-field
design: nothing below is "matching existing style" because there is no
existing style to match. Every choice (language, module boundaries, storage
shape) is a fresh decision for this piece of work, not an inference from
precedent.

## Does this relate to the comprehension-gap job (issue #5)? Briefly: no, and it shouldn't share code — but it can share the underlying event.

The comprehension-gap one-pager is a **monitoring signal generated once, at
the end of a study session**: "your checked understanding of section 3 was
low." Its job statement explicitly ends at making a gap visible; it takes
no position on when the student should come back to it, and the one-pager
lists that as *out of scope by design*.

The review scheduler being asked for here is a **recurring, per-item
decision engine**: given a student's history of answers to a flashcard,
decide today whether that specific card is due, using a memory-strength
model (SM-2/FSRS-style), not a single end-of-session check.

They differ on every axis that matters for module boundaries:

| | Comprehension-gap monitor (issue #5) | Review scheduler (this task) |
|---|---|---|
| Trigger | End of one study session | Every day, independent of any session |
| Unit of decision | Section/concept, once | Individual flashcard, recurring |
| Output | A located signal ("section 3 is weak") | A due/not-due list per card |
| Core model | Checked-vs-felt comprehension score | Retention/forgetting-curve model |
| Consumer | The student, in-session | Mobile + web apps, on open/anytime |

Given that, I would **not** build the scheduler as a dependency of, or
inside, whatever module eventually implements the comprehension-gap
monitor. They should be separate modules with no import relationship in
either direction. The one place they legitimately *could* meet is data:
if the comprehension-gap monitor's per-section scored checks are backed by
the same underlying "student answered item X, got it right/wrong, took N
seconds" event, that event is exactly the input the scheduler also needs.
So: no shared code, but worth agreeing on one shared "attempt/answer event"
shape now, so a future integration doesn't require a data migration on
either side. I'd flag this as a five-minute conversation with whoever
builds issue #5, not a shared abstraction to build preemptively — issue #5
hasn't even been greenlit past the falsifier stage yet, and building an
abstraction to fit a job that might not proceed to build is the premature
generalization this task's own instructions warn against.

## Scope of the scheduler itself

Read a student's past answers → decide which cards are due today → expose
that list to mobile and web.

I'm treating "past answers" as: for each (student, flashcard) pair, a
history of attempts, each with a correctness signal (and ideally a
recall-difficulty signal — e.g., "again/hard/good/easy" à la Anki, not
just right/wrong, since that's what makes SM-2/FSRS worth using over a
fixed interval table).

### Module structure

```
scheduler/
├── domain/
│   ├── card_state.py        # CardState: card_id, student_id, stability,
│   │                         # difficulty, due_at, last_reviewed_at, reps
│   ├── review_event.py      # ReviewEvent: card_id, student_id, rating,
│   │                         # answered_at, latency_ms
│   └── algorithm.py         # pure function: (CardState, ReviewEvent) -> CardState
│                             # e.g. FSRS or SM-2 — no I/O, no framework, unit-testable alone
├── application/
│   ├── record_answer.py     # use case: persist ReviewEvent, recompute
│   │                         # CardState via domain/algorithm.py
│   └── get_due_cards.py     # use case: query CardState where due_at <= now,
│                             # return ordered list (most-overdue first)
├── ports/
│   ├── card_state_repo.py   # interface: load/save CardState per student
│   └── review_event_repo.py # interface: append-only event log
├── adapters/
│   └── <storage impl>       # e.g. Postgres/SQLite implementation of the two ports
└── api/
    ├── rest/                 # or GraphQL — one thin HTTP layer
    │   ├── GET  /students/{id}/due-cards
    │   └── POST /students/{id}/reviews   (submit an answer)
    └── (mobile and web both call this same HTTP surface —
         no separate SDK per client, no logic duplicated client-side)
```

Rationale for the shape, not the names:

- **domain/ has zero I/O and zero framework dependency.** The
  due/not-due decision is a pure function of (current state, algorithm
  parameters, current time). That's the part with real logic and real risk
  of getting subtly wrong (off-by-one interval bugs, clock/timezone bugs),
  so it needs to be the easiest part to unit-test in isolation — feed it a
  `CardState` and a list of `ReviewEvent`s, assert the resulting `due_at`.
- **application/ holds the two use cases the prompt actually asks for** —
  "read past answers" (`record_answer` is how they get recorded in the
  first place) and "decide what's due today" (`get_due_cards`). Keeping
  them as two named use cases, not a grab-bag service class, means each
  has one job and one test suite.
- **ports/ + adapters/ separation exists for exactly one reason:** mobile
  and web both need this list, and they should get it through the same API
  rather than each embedding scheduling logic. That means the scheduler
  itself must be backend/server-side, not client-side logic duplicated in
  a mobile app and a web app — otherwise the two clients will drift out of
  sync on what "due" means. The port interfaces exist so storage (Postgres
  vs. SQLite vs. whatever the rest of the app already picked) is decided
  once, not baked into the domain logic.
- **api/ is deliberately one HTTP surface, not one per client.** "Expose
  it to both apps" is a client-agnostic requirement — it argues for a
  single backend endpoint both clients call, not for a scheduler embedded
  twice.

### Data model (minimum viable)

- `review_events` — append-only: `student_id, card_id, rating, answered_at,
  latency_ms`. Append-only because re-deriving `card_state` from the full
  event history is the cheapest way to recover from a bug in the
  scheduling algorithm later — you can re-run a fixed algorithm over
  unchanged history rather than trusting a stateful column that was
  written by a possibly-buggy old version of the algorithm.
- `card_states` — one row per (student, card): current `stability`,
  `difficulty`, `due_at`, `reps`, `last_reviewed_at`. This is a derived/
  cached table, not a source of truth — it exists for query speed
  (`WHERE due_at <= now()`), and must be safely rebuildable from
  `review_events` alone.

### Algorithm choice

I'd default to **FSRS** (or SM-2 if the team wants something simpler to
reason about first and iterate later) rather than inventing a new
forgetting-curve model — this is a well-studied problem with existing
open-source reference implementations, and "which spacing algorithm" is
an implementation-swap decision that the `domain/algorithm.py` boundary
above is specifically designed to make cheap later, not something to
solve from scratch now.

### What I'd explicitly leave out for a first version

- Cross-device sync conflict resolution beyond "last write wins on
  `review_events` append" — events are append-only and timestamped, so
  simultaneous mobile+web use doesn't need special-casing until there's
  evidence it's a real problem.
- Any coupling to the comprehension-gap monitor's per-section scoring —
  see above; premature until issue #5 is greenlit.
- Notifications/push reminders — that's a consumer of `get_due_cards`,
  not part of the scheduler itself.
