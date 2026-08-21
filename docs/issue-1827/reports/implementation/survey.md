# Survey — issue #1827 (phase 5 FINAL: core board-gate R4 + citation-gate carrier-aware)

canonical checkout used for citation below: local clone
`/home/jwjung/tokenmaxxxer-core` (`tokenmaxxxer/tokenmaxxxer-core`),
`git log -1 --format=%H` this session → `38052e563c046e09d86105b026aeecd1d2417790`,
matching the commit the issue body names ("verified against core 38052e5").
This working repo (`on-the-record`) does not itself contain
`board-gate.sh`/`citation-gate.sh` — those live in the separate `core`
repo per the issue's "Target repo: tokenmaxxxer-core" line.

## board-gate.sh R4 — current identity source

R4's doc comment: `core/hooks/board-gate.sh:24-28`:

> R4  Branch. A role session writes an issue tree only from that issue's
> own role branch: writing docs/issue-<n>/... requires the current git
> branch to be exactly issue-<n>/<CLAUDE_ROLE>. Writing the board from
> main (or any other branch) is refused — every role output reaches
> main only through a PR the human merges (contract v3 s10).

The actual check, `core/hooks/board-gate.sh:719-784`:

- Branch resolution (`:723-731`) uses `git symbolic-ref --short HEAD`
  (not `rev-parse --abbrev-ref`) specifically because it "answers on a
  branch with no commits yet, and fails on detached HEAD — which is
  exactly the deny we want." `branch` is the raw string; no sidecar is
  consulted anywhere in this file.
- `role` (used at `:742` as `_bm.group(2) == role`, and at `:772` as
  `expected = "%s/%s" % (issue_dir, role)`) comes from `CLAUDE_ROLE` —
  read earlier in the same script (outside the quoted excerpt above,
  in the shared preamble every rule in this file uses; R3 at
  `:19-22` already documents that role sessions get it "from
  on-the-record").
- `:770-784`: for every `docs/issue-<n>/...` write hit (`issue_hits`),
  `expected = "<issue_dir>/<role>"` is compared against `branch` with a
  plain string `==`. On mismatch it falls to the maintenance-targets
  exception (`:734-768`, a live `gh issue view` lookup, unrelated to
  role/branch identity) and, failing that, denies at `:779-784` citing
  the required branch name literally in the message
  ("writing docs/%s/ requires branch %s (current: %s)").

So R4's ENTIRE identity source today is: `CLAUDE_ROLE` (env) +
`git symbolic-ref --short HEAD` (branch string), compared by exact
match against the literal pattern `issue-<n>/<role>`. No file (sidecar
or otherwise) is read for identity anywhere in `board-gate.sh` — grep
of `.on-the-record` or `role.json` across the file, this session,
returns no match.

## citation-gate.sh CIT_BRANCH — current derivation and consumption

Derivation, `core/hooks/citation-gate.sh:38`:

```
export CIT_BRANCH="$(git -C "${CLAUDE_PROJECT_DIR:-$(pwd)}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
```

(Note: this uses `rev-parse --abbrev-ref`, not `symbolic-ref --short`
like board-gate.sh — a pre-existing inconsistency between the two
gates, out of scope here since the issue only asks for carrier-aware
dual-read, not derivation-mechanism unification.)

Consumption inside the embedded python, `core/hooks/citation-gate.sh:84`
(`branch = os.environ.get("CIT_BRANCH", "")`) and
`core/hooks/citation-gate.sh:276-291`
(`check_whole_doc_keyword_and_ref_plus_branch`):

```python
def check_whole_doc_keyword_and_ref_plus_branch(row, text):
    low = text.lower()
    keyword_present = any(n in low for n in row["keyword_needles"])
    ref_re = re.compile(row["issue_ref_regex"])
    refs = ref_re.findall(text)
    ref_numbers = [a or b for (a, b) in refs]
    if not (keyword_present and ref_numbers):
        return row["missing_message"]
    branch_m = re.match(row["branch_regex"], branch)
    if branch_m:
        branch_issue = branch_m.group(1)
        if branch_issue not in ref_numbers:
            return row["branch_mismatch_message_template"].format(
                refs=", ".join(sorted(set(ref_numbers))), branch=branch, branch_issue=branch_issue
            )
    return None
```

`row["branch_regex"]` — the only row in the shipped config that uses
this check function — is defined at
`core/hooks/citation-config.json:185`:

```json
"branch_regex": "^issue-(\\d+)/",
```

**Finding (issue requirement 2, "record with file:line citation, no
change"): `CIT_BRANCH` is consumed only through this single regex,
which captures group(1) as the issue number and stops at the first
`/`. It never captures or reads a role/name segment of the branch —
`branch_issue` is compared only against the doc's own cited issue
numbers (`ref_numbers`), never against `CLAUDE_ROLE` or any role
string.** Grep of `citation-gate.sh` and `citation-config.json` for
`role`/`CLAUDE_ROLE` near any `branch` variable, this session, finds
no such use — the only place `role` appears in `citation-gate.sh` is
`os.environ.get("CIT_ROLE", "")` at `:78`, which selects which
citation-config ROW applies (a config lookup key), never anything
derived from the branch string. So citation-gate.sh's CIT_BRANCH
consumption is **already role-free** — issue-number-only — and per the
issue's own requirement 2 ("if issue-number-only, the finding is
recorded ... and no change is made"), citation-gate.sh needs NO
dual-read change in this initiative.

## The established sidecar dual-read pattern (from #1814/#1818/#1821/#1824)

Sidecar writer: `spawn.py:7625-7639` (`_write_role_sidecar`), called
from `issue_workspace()` at `spawn.py:7684`, `:7708`, `:7753` (3 call
sites, all workspace-spawn paths). Shape, written once per spawn to
`<workspace-root>/.on-the-record/role.json`:

```json
{"role": "<role-str>", "issue": <issue-int>}
```

Fail-open by design: a write failure just means the sidecar is absent
and every consumer falls back to the legacy mechanism.

Consumer pattern, verbatim from
`on-the-record/hooks/approval-gate.sh:109-169` (landed for #1821, the
most directly analogous prior phase — a *gate* hook, same shape core's
board-gate.sh needs):

```python
cwd = e.get("cwd") or os.getcwd()
issue = None
branch_role = None
try:
    with open(os.path.join(cwd, ".on-the-record", "role.json"), encoding="utf-8") as f:
        sidecar = json.load(f)
    if (isinstance(sidecar, dict) and isinstance(sidecar.get("role"), str)
            and isinstance(sidecar.get("issue"), int)):
        issue = sidecar["issue"]
        branch_role = sidecar["role"]
except (OSError, ValueError):
    pass

if issue is not None:
    # sidecar resolved — attempt an INDEPENDENT branch parse purely for
    # cross-checking, never to replace the sidecar's own values.
    try:
        r2 = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        r2 = None
    if r2 is not None and r2.returncode == 0:
        bm2 = re.match(r"^issue-(\d+)/([\w-]+)$", r2.stdout.strip())
        if bm2:
            cross_issue = int(bm2.group(1))
            cross_role = bm2.group(2)
            if cross_issue != issue or cross_role != branch_role:
                deny(
                    "sidecar role/issue (issue-%d/%s) disagrees with the "
                    "branch-parsed role/issue (issue-%d/%s) — workspace "
                    "state is inconsistent." % (issue, branch_role, cross_issue, cross_role),
                    "make .on-the-record/role.json and the current branch "
                    "name agree on the same issue-<n>/<role>, or remove the "
                    "stale sidecar.",
                )

if issue is None:
    # ... byte-identical legacy branch-regex parse, unchanged from pre-#1821
```

Same shape/pattern is asserted repo-wide, not just for approval-gate.sh:
`test/test_convention_equivalence.py:420-424`
(`test_hooks_read_role_json_sidecar_before_falling_back`) asserts
`approval-gate.sh`, `pr-preflight.sh`, and `contract-guard.sh` source
text each contains both `.on-the-record` and `role.json` literals — the
three on-the-record-side consumers of this exact sidecar shape. Core's
board-gate.sh will be a fourth (new-repo) consumer of the same shape;
there is no existing core-side consumer to diff against (grep of
`role.json`/`.on-the-record` across `core/hooks/*.sh`, this session,
returns no match anywhere in core).

## bash 3.2 compatibility constraints already established

Both target files are already bash-3.2-annotated:

- `core/hooks/board-gate.sh:64-65`: "bash 3.2: a quoted heredoc nested
  inside $( … ) is NOT literal — read the program at top level" — this
  is why the python body is fed via `IFS='' read -r -d '' VAR <<'PY'`
  into a shell variable and later run as `python3` fed that variable,
  rather than `python3 <<PY` wrapped inside a `$(...)`.
- `core/hooks/citation-gate.sh:40-41`: "payload travels via env, never
  re-read from stdin inside the heredoc below (issue #245 bash-3.2
  guard: no heredoc-in-command-substitution)" — same constraint, and
  citation-gate.sh instead uses a top-level `python3 <<'PYEOF'` (not
  wrapped in `$(...)`), passing payload/branch/role via exported env
  vars (`CIT_PAYLOAD`, `CIT_BRANCH`, `CIT_ROLE`), so this is a second,
  independently-viable pattern for the same constraint.
- The same guard note ("issue #245 bash-3.2 guard: no
  heredoc-in-command-substitution") also appears verbatim at
  `core/hooks/facet-keyword-gate.sh:34` and
  `core/hooks/ordering-norm-gate.sh:34`, and
  `core/hooks/lib/role-directive.sh:25` separately notes avoiding
  `${var^^}` "to stay inside parse-check.sh's bash-3.2 compatibility" —
  confirming this is a house-wide constraint in core, not local to
  these two files. No associative-array or `mapfile` usage exists in
  either target file (grep, this session, no match) — nothing to
  migrate away from on that front; the only hazard is the
  heredoc-in-`$()` pattern above, and any new sidecar-read code added
  to board-gate.sh's existing `IFS='' read -r -d '' CORE_BOARD_GATE
  <<'PY'` block (or citation-gate.sh's existing `python3 <<'PYEOF'`
  block) automatically inherits the safe pattern already in place —
  the new code is plain Python inside the already-safe delivery
  mechanism, not a new heredoc-in-`$()` site.

## Summary of what phase 2 will touch

1. `core/hooks/board-gate.sh` — R4 section, `:719-784` (specifically the
   branch-resolution block `:723-731` and the per-hit comparison loop
   `:770-784`): add a sidecar-preferred, legacy-fallback,
   mismatch-fail-closed identity resolution, reusing the
   `on-the-record/hooks/approval-gate.sh:109-169` shape.
2. `core/hooks/citation-gate.sh` — NO code change. `CIT_BRANCH`
   (`:38`, consumed at `:84` and `:276-291` via
   `citation-config.json:185`'s `branch_regex`) is already
   issue-number-only; this survey records that finding per issue
   requirement 2.
