---
status: approved
files:
  - spawn.py
  - tests/test_spawn.py
---

# init should scaffold docs/specs/requirement-digest.md

## Request

`spawn.py init` on a fresh target repo creates `docs/specs/approvers.md`
but leaves the repo with no `docs/specs/requirement-digest.md`, so the
first `spawn.py implementation --issue N` on that repo is refused by the
requirement-linkage gate (#1017) — there is no R-ID to cite yet. `init`
should also scaffold the digest file (header + documented R-entry format +
empty list) when absent, and never touch an existing one.

## Constraints

- Never overwrite an existing `docs/specs/requirement-digest.md` (mirrors
  `init_board`'s existing approvers.md behavior, spawn.py:888).
- The stub must be a format the requirement-linkage gate's own `R\d+`
  pattern matches once a human fills in an entry (`gates/requirement_linkage.py:24`
  `_REQ_ID_RE = re.compile(r"\bR\d+\b")`).
- No dependency on `docs/specs/requirements.md` existing — a fresh target
  repo has neither file.

## Rationale

Considered reusing `gates/requirement_digest.py`'s `update()` generator to
produce the stub. Rejected: that function reads and parses
`docs/specs/requirements.md` (`_REGISTRY_REL`, `parse()` —
gates/requirement_digest.py:23-58); a freshly inited target repo has no
such registry, so invoking the generator would either crash or require
first fabricating a fake registry file just to generate from it. A static
stub written directly by `init` is simpler and matches the issue's own
described shape ("header + format comment + empty list").

## What will be done

- Add `init_requirement_digest(cwd) -> bool` to `spawn.py` near
  `init_board`: writes `docs/specs/requirement-digest.md` with a header
  comment, a `## R-entry format` block documenting the expected shape
  (`- R<n>: <description> [status] (source: #<issue>)`), and an empty
  entries list, only if the file does not already exist. Returns whether
  it wrote.
- Call it from `init_board` after the approvers.md step, printing a
  one-line confirmation on write and a "이미 있다" line on skip (mirrors
  the existing approvers.md messages at spawn.py:889/900).
- Unit tests in `tests/test_spawn.py`: (1) fresh tmp repo → file created,
  contains an `R\d+` example matching the gate's own regex; (2) running
  init twice → second run does not modify the file (mtime/content
  unchanged); (3) repo with a pre-existing digest file → `init_board`
  leaves its content untouched.

## Out of scope

- Wiring the digest file into `require_requirement_linkage`'s check logic
  (that gate already only reads the issue body, per survey — unchanged).
- Regenerating/updating an existing digest's stale entries — that's
  `gates/requirement_digest.py --update`'s job, untouched.

## Accumulation

This adds one new single-purpose helper (`init_requirement_digest`) called
once from `init_board`, not an inline subprocess/gh call or a per-repo
repeated-file edit — there is no roles/*.json-style list this touches
repeatedly. If future issues need more scaffolded files, they add their
own similarly-shaped `init_*` helper and call site; that is a fixed
one-function-per-file cost, not a growing per-invocation list this
proposal accumulates onto.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k requirement_digest` passes; a
fresh repo's `spawn.py init` run leaves a
`docs/specs/requirement-digest.md` whose format stub a human can copy to
add R1 and pass the linkage gate on their first issue.
