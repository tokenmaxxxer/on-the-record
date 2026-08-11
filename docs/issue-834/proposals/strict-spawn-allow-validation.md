---
status: proposed
files:
  - on-the-record/hooks/spawn-allow-gate.sh
  - on-the-record/hooks/test_spawn_allow_gate.py
  - docs/issue-834/reports/implementation.md
---

# Proposal — issue #834 step 1, implementation

## Request

Fix `on-the-record/hooks/spawn-allow-gate.sh`'s command-shape check: it
strips an optional `cd DIR &&` prefix (line 106) *before* searching the
remainder for shell chain/substitution operators (line 119), and the
prefix's directory slot (`\S+`) is unbounded — a command-substitution
payload with no internal whitespace placed in that slot gets consumed by
the strip and vanishes from what the operator search ever inspects, while
bash still executes it. A crafted `cd <substitution> && python3 spawn.py
...` command then gets `permissionDecision: allow` from this
default-on, plugin-only hook. Skip scouting: the design to apply is
already named in the issue and forbidden from being a fresh regex — see
survey's mandatory skip line.

## Constraints

- Do not touch `on-the-record/hooks/merge-allow-gate.sh` — issue #824
  already fixed it; this proposal's write set is `spawn-allow-gate.sh` and
  its test file only.
- Do not reopen whether this hook's auto-approve design should exist at
  all — issue #824 already weighed strict validation against dropping the
  `allow` branch entirely and recorded why strict validation is the
  primary fix for a mechanically-decidable shape (`docs/issue-824/proposals/strict-merge-allow-validation.md`
  lines 39-60); not revisited here.
- Do not touch `on-the-record/hooks/impact-guard.sh`'s reverse-direction
  false positive (quoted command strings counted as real invocations) —
  separate issue, not this one's shape.
- Every one of `test_spawn_allow_gate.py`'s 12 existing cases must keep
  passing with an unchanged allow/no-allow outcome — including the
  `cd`-prefixed allow case and the single-quoted-operator-in-task-text
  allow case, both of which a naive "reject any operator anywhere"
  rewrite would break.
- No regex-based quote-stripping or quote-pairing check may replace the
  current one — the issue explicitly asks to reuse issue-824's tokenizer
  design instead, on the strength of that design's own after-proposal
  hunt having already broken a hand-rolled regex approach once.

## Rationale

Considered patching the existing regex narrowly — bound the `cd`-prefix
directory slot to exclude `$`, backtick, and other substitution-starting
characters (e.g. tighten `\S+` to a character class), keeping the rest of
the file's regex-based structure intact. Rejected: this repairs only the
one concrete payload shape found so far. The underlying defect is that a
hand-written regex is being asked to track bash's real
quoting/substitution/operator state, and issue #824's own after-proposal
hunt already demonstrated that a differently-shaped but equally
regex-based check in this same file family (the quote-pairing approach
`merge-allow-gate.sh` first drafted) has a second, independent bypass
class once probed. Patching the symptom leaves the same root cause
in place for the next payload shape a hunt would find.

Considered dropping the `cd DIR &&` prefix shape entirely — require a bare
`python3 <...spawn.py> ...` invocation only, no prefix tolerance. Rejected:
that prefix is a currently-relied-upon, already-tested capability
(`t_cd_prefixed_spawn_invocation_gets_allow`), not part of the defect —
removing it fixes nothing about the bypass (the bypass lives in the
unbounded directory-slot capture, not in the prefix's existence) while
regressing a legitimate use this issue is not asked to remove.

Considered leaving `spawn-allow-gate.sh` unfixed until an eventual shared
helper unifies it with `merge-allow-gate.sh`'s check into one library
function, reasoning that fixing them at different times invites drift.
Rejected: the issue reports this hook as "배포돼 무장된 상태" (shipped and
armed) with an already-published `docs/issue-824/proposals/...` design to
copy — the gap between "known bypass in a live gate" and "shipped fix" is
the risk that matters here, not code-sharing tidiness; a shared-helper
refactor is a separate, lower-urgency proposal if wanted later.

**Chosen design:** port `merge-allow-gate.sh`'s corrected check verbatim
in shape — reject the whole command outright (before any stripping) if a
backtick, `$(`, or newline appears anywhere in it; tokenize the full,
unstripped command with `shlex.shlex(cmd, posix=True,
punctuation_chars=True)`; recognize exactly two token shapes
(`["python3"|"python", SPAWN_PATH, ...args]` or `["cd", DIR, "&&",
"python3"|"python", SPAWN_PATH, ...args]`, `SPAWN_PATH` ending in
`spawn.py`); reject if any token outside the one tolerated `&&` position
is composed entirely of operator characters. Verified live, this session
(survey's traces), that this tokenizer classifies every existing test
payload the same way the current code does, and rejects both the
`$(...)`-in-dir-slot and backtick-in-dir-slot reproductions of this
issue's bypass — the latter via shape mismatch alone (the substitution's
own punctuation tokens land where the shape requires a literal `"&&"`),
even before the upfront reject clause runs.

## What will be done

- `on-the-record/hooks/spawn-allow-gate.sh`: replace the "command-shape
  resolution" / "reject if any shell-chaining/substitution operator is
  reachable" / "must be exactly a python3 ... spawn.py invocation" block
  (current lines 104-125) with:
  - an outright reject (fall through, no allow) if a backtick, `$(`, or a
    literal newline appears anywhere in the command;
  - tokenization of the full command via `shlex.shlex(cmd, posix=True,
    punctuation_chars=True)` with `whitespace_split = True`; a
    `ValueError` (unbalanced quoting) falls through unreached, same
    fail-open posture as today;
  - shape recognition for `[PYBIN, SPAWN_PATH, *tail]` (`PYBIN` in
    `("python3", "python")`, `SPAWN_PATH` ending in `spawn.py`) or
    `["cd", DIR, "&&", PYBIN, SPAWN_PATH, *tail]`, rejecting if any token
    in `tail` (plus `DIR` for the `cd`-prefixed shape) is composed
    entirely of `shlex`'s punctuation characters plus `;`;
  - the existing spawn-path resolution/existence check (unchanged) runs
    only after the shape check passes.
  - the file's own top-of-file comment block updated to describe the
    fixed check, mirroring how `merge-allow-gate.sh`'s comment documents
    issue #824's fix.
- `on-the-record/hooks/test_spawn_allow_gate.py`: keep all 12 existing
  cases unmodified; add regression cases for — a command-substitution
  payload hidden in the `cd` prefix's directory slot, using both `$(...)`
  and backtick forms (this issue's exact reproduction); chain-appended
  `&&` is already covered by `t_unquoted_chained_command_after_spawn_is_unreached`,
  so add the remaining directions/operators issue-824's own regression set
  covers for parity: chain-prepended `;`, chain-appended `;`,
  chain-appended `|`, and a backslash-escaped-quote payload
  (`python3 spawn.py review 42 \';evil;'X'`-shaped) that a naive
  quote-pairing regex would desync on. The pure bare-invocation and
  `cd`-prefixed-invocation green cases already exist
  (`t_orchestrator_spawn_invocation_gets_allow`,
  `t_cd_prefixed_spawn_invocation_gets_allow`) and stay as the acceptance
  criteria's required green-path coverage.
- Run `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` and
  confirm no *new* failure appears relative to this proposal's recorded
  baseline (`docs/issue-834/reports/implementation/survey.md`'s Baseline
  section: 1 pre-existing, unrelated failure —
  `t_all_generators_recorded_and_disjoint` — 1209 passed, 2 skipped, 1
  xfailed).
- Write `docs/issue-834/reports/implementation.md`, this role's phase-2
  record, citing this proposal and the survey as upstream basis.

## Out of scope

- `on-the-record/hooks/merge-allow-gate.sh` (issue #824, already landed).
- Reconsidering the auto-approve policy itself (issue #824's own Rationale
  already weighed and decided this).
- `on-the-record/hooks/impact-guard.sh`'s reverse-direction false positive
  (quoted command strings counted as live invocations) — a different file,
  a different failure direction, a separate-issue candidate.
- `gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint`'s
  pre-existing failure (a `stop-poll-rearm.sh` / issue-801 concern) —
  recorded in the survey's Baseline section as this session's honest
  starting state, not fixed here.
- A shared-helper refactor unifying `merge-allow-gate.sh` and
  `spawn-allow-gate.sh`'s now-identical-in-shape check into one library
  function — a real future improvement, but a different, lower-urgency
  proposal (see Rationale).

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_spawn_allow_gate.py -q`
passes, including the new cases proving a command-substitution payload
hidden in the `cd`-prefix directory slot (both `$(...)` and backtick
forms), both chain directions, `;`, `|`, and the backslash-escaped-quote
payload all get no `allow` decision, while a bare `python3 spawn.py ...`
invocation and a legitimate `cd <path> && python3 spawn.py ...` invocation
still do. `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
reports the same 1209-passed baseline plus the new regression cases, with
no new failure beyond the pre-existing, out-of-scope
`t_all_generators_recorded_and_disjoint` one.
