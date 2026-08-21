# issue-1814 phase-1 survey: branch-role decode, explicit-carrier candidates

canonical: gh issue view 1814

Scout skip: the candidate carrier set (co-injected directive file /
workspace sidecar / PR body trailer) is closed and named verbatim by
the issue body itself; there is no external field/product to benchmark
a role-carrier field against. This survey is the current-state read the
issue's "survey picks ONE with rationale" line asks for.

## The four regex sites (issue #1792 survey's "Dependency facts" bullet 4)

canonical: on-the-record/hooks/approval-gate.sh:107, on-the-record/hooks/pr-preflight.sh:97-110, on-the-record/hooks/contract-guard.sh:181-185, gates/flows.py:57,319

```
$ derived: grep -n "re.match(r\"^issue-" on-the-record/hooks/approval-gate.sh on-the-record/hooks/pr-preflight.sh on-the-record/hooks/contract-guard.sh
on-the-record/hooks/approval-gate.sh:107:bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
on-the-record/hooks/pr-preflight.sh:106:bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
on-the-record/hooks/contract-guard.sh:185:        bm = re.match(r"^issue-(\d+)/([\w-]+)$", br.stdout.strip())

$ derived: grep -n "_BRANCH_RE\|headRefName" gates/flows.py
gates/flows.py:57:                        "number,headRefName,createdAt,body,reviews",
gates/flows.py:319:                        m = _BRANCH_RE.match(pr.get("headRefName") or "")
```

1. `on-the-record/hooks/approval-gate.sh:107` — same
   `^issue-(\d+)/([\w-]+)$` regex; branch reaches this line already
   resolved (not a fresh `git`/`gh` call at this line).
2. `on-the-record/hooks/pr-preflight.sh:105-110` — `branch =
   r.stdout.strip()` from `git rev-parse --abbrev-ref HEAD`, then the
   same regex; `role = bm.group(2)`.
3. `on-the-record/hooks/contract-guard.sh:181-185` — `git rev-parse
   --abbrev-ref HEAD` into `br`, then the same regex against
   `br.stdout.strip()`.
4. `gates/flows.py:319` — `_BRANCH_RE.match(pr.get("headRefName") or
   "")` against a `gh pr list --json ...,headRefName,...` row
   (flows.py:57) — this site reads a remote PR listing field, not a
   local `git` call.

Three sites (`pr-preflight.sh`, `contract-guard.sh`, and
`approval-gate.sh`'s upstream branch resolution) run inside a local
workspace checkout; `gates/flows.py` runs off `gh pr list` JSON with no
local-checkout call visible in the cited source.

## Candidate carriers (named in the issue body)

**A. Co-injected directive file**
(`on-the-record/hooks/directive.sh`, fired every turn from
`UserPromptSubmit` — canonical: spawn.py:2475-2477, comment on
`poll_due()`: "`directive.sh` 가 매 턴 `UserPromptSubmit` 훅에서
부르므로"). This is prompt-injection machinery that writes into a live
session's model context, not a data record on disk that a
`PreToolUse`/CI-adjacent shell process can read independent of a live
session turn. Rejected — see proposal Rationale.

**B. PR body trailer.** Only readable once a PR exists; two of the
three shell hooks fire before/around PR creation itself
(`pr-preflight.sh` parses the *candidate* body being submitted — its
own `--body-file` handling starts at pr-preflight.sh:18). Requires a
network `gh pr view`/`gh pr list` round trip from every shell-hook site
that currently resolves role from local `git` alone, adding a new
failure mode (network, auth, rate limit) to those three call sites.
`gates/flows.py` already fetches `body` in the same `gh pr list` call
that yields `headRefName` (flows.py:57), so a trailer is a natural fit
there specifically.

**C. Workspace sidecar record.**
`derived: ls -la .on-the-record/` → `.on-the-record/` exists at the
workspace root today holding `auto-approval-state.json` and
`test-tiers.json` — an established convention for hook-readable,
session-local state, no network call. `spawn.py` clones/checks out this
workspace before hooks run and can write a `.on-the-record/role.json`
there at spawn time. The three shell-hook sites already resolve the
workspace root via a local `git rev-parse` call in the same function
they use today (pr-preflight.sh:97-105, contract-guard.sh:181,
approval-gate.sh's branch context) — reading a sidecar file alongside
that call adds no new dependency class.

## Open finding: gates/flows.py's checkout guarantee

```
$ derived: grep -n "headRefName\|checkout\|clone\|git " gates/flows.py | head -20
gates/flows.py:57:                        "number,headRefName,createdAt,body,reviews",
gates/flows.py:319:                        m = _BRANCH_RE.match(pr.get("headRefName") or "")
```

No clone/checkout call appears near gates/flows.py:319 in the cited
grep — flows.py's role-decode site reads only the remote `gh pr list`
JSON row, with no local workspace evidenced at that call site. A
`.on-the-record/role.json` sidecar written into the *spawn* workspace is
not directly reachable from a flows.py process unless flows.py is
invoked with that workspace as `cwd`. This is the deciding fact for the
proposal's per-site read strategy — see proposal Rationale.
