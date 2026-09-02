---
issue: 3182
role: adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2
author: adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), conformance-review-traceability-and-evidence (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3184's deliverable
loop_state: done
type: verification
breaking: false
verdict: changes-requested
upstream:
  - path: scripts/preflight/consumer_preconditions.py
    sha: a7176f5daa94793f3b7691a4d58b58e56fb3a89e
  - path: docs/handbooks/install-sufficiency.md
    sha: a7176f5daa94793f3b7691a4d58b58e56fb3a89e
---

# issue-3182 — adversarial-review+silent-failure-audit+conformance-review-traceability-and-evidence-7ee545a2 record

## What was done

canonical: `gh pr view 3184` — additions:931 deletions:0, four commits
on `pr-3184-review` (fetched via `git fetch origin
pull/3184/head:pr-3184-review`, tip `a526670a`), title "issue-3182:
consumer-loop preflight + install-sufficiency handbook", `Closes #3182`.

Independent verification of PR #3184 (tokenmaxxxer/on-the-record), which
delivers `scripts/preflight/consumer_preconditions.py` (nine cited
preconditions, `--json`/human report, exit 0|1, claimed read-only) and
`docs/handbooks/install-sufficiency.md` (1 satisfied / 4 removable / 5
structural claim) for issue #3182. PR #3184 itself was never edited,
merged, or commented on; verification ran against disposable worktrees
checked out from the fetched `pr-3184-review` ref.

### 1. Completeness of the nine-precondition enumeration — Absent (one real gap found)

derived: `sed -n '729,751p' spawn.py` (this repo's working tree,
`b9446c8b`, confirmed identical to `6ae02cce` for this file below)
```
MIN_FREE_BYTES_DEFAULT = 3 * 119 * 1024 * 1024   # ~357MB
MIN_FREE_INODES_DEFAULT = 1000

def _spawn_capacity_check(path) -> None:
    ...
    try:
        usage = shutil.disk_usage(probe)
    except OSError:
        return
    min_bytes = int(os.environ.get("MUSTER_MIN_FREE_BYTES", MIN_FREE_BYTES_DEFAULT))
    if usage.free < min_bytes:
        sys.exit(
            f"스폰을 거부한다: {probe} 에 여유 공간이 부족하다 "
            ...
        )
    try:
        st = os.statvfs(probe)
    ...
```

`spawn.py:729-751` defines `_spawn_capacity_check(path)`, called before
any workspace clone is attempted. It measures `shutil.disk_usage(probe)`
and calls `sys.exit(...)` when free bytes fall below
`MIN_FREE_BYTES_DEFAULT` (~357MB), and a parallel `os.statvfs` inode
check follows in the same function. This is a `sys.exit`-enforced gate
on the exact "spawn dispatch" code path the issue's brief names,
structurally identical in kind to `target_repo_board_file_present`
(also a pre-spawn `sys.exit` gate) — but it is absent from `CHECKS` in
`scripts/preflight/consumer_preconditions.py:141-227`.

derived: `grep -n '"name":' scripts/preflight/consumer_preconditions.py`
(reviewed copy at PR #3184 sha `a7176f5d`, placed in this worktree at
`scripts/preflight/consumer_preconditions.py` for citation-checking
only, not staged for this branch)
```
result: 9 name entries — posix_fork_support, claude_cli_on_path, git_cli_on_path,
gh_cli_authenticated, git_identity_configured, skill_repository_resolvable,
home_claude_skills_dir_present, target_repo_board_file_present, remote_push_access
```
None of these nine names covers disk/inode headroom.

Two candidates considered and judged **not** missing:
- **Network reachability to github.com** — not enumerated as its own
  entry, but every check that would fail without it
  (`gh_cli_authenticated` via `gh auth status`, and the loop's own
  `git fetch`/`git push` calls at `pipeline.py:853` and `board.py:90-92`)
  already requires a live network path to observe/succeed. Judged
  **covered under a different name**.
- **A distinct "agent account" (`MUSTER_AGENT_GH_TOKEN`)** — the issue
  text names this explicitly. derived: `sed -n '338,361p' plumbing.py`
  confirms `_resolve_gh_token()` falls back to the operator's own `gh
  auth token` when `MUSTER_AGENT_GH_TOKEN` is unset ("1계정 기본" —
  1-account default is a supported mode, not a failure). Since the loop
  functions correctly without a distinct agent identity,
  `gh_cli_authenticated` substantively covers this. Judged **Surface**,
  not Absent.
- Python version and a `jq` dependency in hooks were checked and ruled
  out: derived: `grep -n "sys.version_info" spawn.py pipeline.py
  skills.py board.py plumbing.py` → no output (no version gate exists);
  derived: `grep -rn '^\s*jq \|[^#]jq -' on-the-record/hooks/*.sh | grep
  -v '^\s*#'` → no output (no real, non-comment `jq` invocation).

### 2. Citation accuracy — 5 of 9 source citations Incorrect or Surface

canonical: every `source` field read via `grep -n '"source"' -A0
scripts/preflight/consumer_preconditions.py` against the reviewed copy
(PR #3184 sha `a7176f5d`), each opened at the cited file:line with
`sed -n '<N>p' <file>` against this working tree's `spawn.py`/
`pipeline.py`/`skills.py`/`board.py`/`plumbing.py`/
`on-the-record/hooks/git-push-guard.sh`, all at `b9446c8b`.
derived: `git diff --stat 6ae02cce..b9446c8b -- spawn.py pipeline.py
skills.py board.py plumbing.py on-the-record/hooks/git-push-guard.sh`
→ empty output (zero diff), confirming line numbers in `b9446c8b`
match the `6ae02cce` sha the builder's record claims it read.

| precondition | source cited | verdict | evidence |
|---|---|---|---|
| `posix_fork_support` | `spawn.py:2668,4639` | Surface | `sed -n '4639p' spawn.py` → `child_pid = os.fork()`; `awk` scan for nearest preceding `def` places line 4639 inside `_spawn_one()` (`def _spawn_one` at `spawn.py:3791`) — correct, the real role-session spawn path. `sed -n '2668p' spawn.py` → also `child_pid = os.fork()`, but the nearest preceding `def` is `main()` at `spawn.py:2221`; the surrounding comment at `spawn.py:2663-2664` reads "`_spawn_one()` 이 실제 스폰 세션에 쓰는 것과 같은 os.fork()+setsid()+... 패턴" ("the same pattern `_spawn_one()` uses...") — i.e. this fork is in a *different* feature (background validity-consult), acknowledged by its own comment as mirroring, not being, the cited path. |
| `claude_cli_on_path` | `pipeline.py:663` | Surface | `sed -n '661,664p' pipeline.py` → line 663 is inside the literal `cmd = ["claude", "-p", ...]` (`pipeline.py:661-664`), a real citation. But `spawn_cmd()`'s own body (`pipeline.py:603-783`) ends `return cmd, env` at line 783 — it does not exec; the actual `subprocess.Popen(cmd, ...)` runs later, in `spawn.py:_spawn_one()` (confirmed via `grep -n "cmd, extra_env = spawn_cmd" spawn.py` → `spawn.py:4534`, followed by `grep -n "proc = subprocess.Popen" spawn.py` → `spawn.py:4761`). The citation's "and execs it directly" claim is Incorrect; the file:line itself is fine. |
| `git_cli_on_path` | `pipeline.py:798` | Present | `sed -n '798p' pipeline.py` → `r = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"], ...)` — exact match. |
| `gh_cli_authenticated` | `plumbing.py:349` | Incorrect | `sed -n '349p' plumbing.py` → `if _sp._GH_TOKEN_CACHE is not None:` — a cache check, not the subprocess call. `sed -n '355p' plumbing.py` → `t = subprocess.run(["gh", "auth", "token"], capture_output=True,` — the described call is 6 lines away from the cited line. |
| `git_identity_configured` | `board.py:76-79` | Incorrect | `sed -n '76,79p' board.py` → `git ... "add" ...` and the start of a staged-diff check — a `git add`, not the described `git commit`. `sed -n '83,86p' board.py` → `subprocess.run(["git", "-C", str(root), "commit", "-m", ...])` — the described call is 7 lines away from the cited range. |
| `skill_repository_resolvable` | `skills.py:96-112` | Present | `sed -n '96,112p' skills.py` → `_skill_repo_root()` body, exactly `MUSTER_SKILL_REPO` env > sibling clone > `_skill_repo_managed_root()` fallback — matches the citation's description verbatim. |
| `home_claude_skills_dir_present` | `skills.py:338` | Present | `sed -n '338p' skills.py` → `tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")` — exact line match. |
| `target_repo_board_file_present` | `board.py:246-256` | Present | `sed -n '246,256p' board.py` → `require_board()`, checks `_sp.MARKER` (`= "docs/specs/approvers.md"`, `grep -n '^MARKER' spawn.py` → `spawn.py:804`), `sys.exit`s if absent — matches. |
| `remote_push_access` | `on-the-record/hooks/git-push-guard.sh:341` | Surface | `sed -n '336,344p' on-the-record/hooks/git-push-guard.sh` → line 341 is remedy text inside a `deny(...)` call for the fail-closed edge case where the remote's default branch cannot be resolved. `sed -n '308,329p' on-the-record/hooks/git-push-guard.sh` → the primary enforcing logic is `_ROLE_BRANCH_RE.match(d)` at line 328, which defines/permits the `issue-<n>/<slug>` shape the precondition's name refers to; 341 is a secondary, edge-case reference. |

derived: counting the "verdict" column above (applied by hand to the
table) → 4 Present (`git_cli_on_path`, `skill_repository_resolvable`,
`home_claude_skills_dir_present`, `target_repo_board_file_present`), 3
Surface (`posix_fork_support`, `claude_cli_on_path`, `remote_push_access`),
2 Incorrect (`gh_cli_authenticated`, `git_identity_configured`) = 4 + 3
+ 2 = 9, matching the total entry count from section 1's `grep -n
'"name":'` derivation. 5 of the 9 entries (3 Surface + 2 Incorrect)
carry a citation defect per the table above.

None of the 5 defective citations point at genuinely unrelated code —
every one is in the right function or the right statement, which
bounds the severity — but the issue's own text ("every precondition
asserted must cite the file and line that requires it") is not met
exactly for over half the entries.

### 3. Satisfied/unsatisfied verdicts — Present (all 8 independently reproduced correct; 1 correctly-mandated unsatisfied)

canonical: `python3 scripts/preflight/consumer_preconditions.py --json`
(reviewed copy, PR #3184 sha `a7176f5d`, run in a disposable worktree
outside `/tmp`)
```
result: 9 entries, 8 satisfied ("posix_fork_support", "claude_cli_on_path",
"git_cli_on_path", "gh_cli_authenticated", "git_identity_configured",
"skill_repository_resolvable", "home_claude_skills_dir_present",
"target_repo_board_file_present"), 1 unsatisfied ("remote_push_access")
```

Independently re-derived every field without importing the script:
- `posix_fork_support` true — derived: the script's own reported
  detail, `platform=linux fork=True setsid=True`, cross-checked against
  `uname` → `Linux`, and `python3 --version` → `Python 3.10.12` (a
  version with both attributes present).
- `claude_cli_on_path` / `git_cli_on_path` true — derived: `which
  claude` → `/home/jwjung/.local/bin/claude`; `which git` →
  `/usr/bin/git`.
- `gh_cli_authenticated` true — derived: `gh auth status` → "✓ Logged
  in to github.com account JiwonJung94".
- `git_identity_configured` true — derived: `git config --get
  user.name` → `Jiwon Jung`; `git config --get user.email` → set
  (non-empty).
- `skill_repository_resolvable` true — derived: `printenv
  MUSTER_SKILL_REPO` → `/home/jwjung/skill-registry/skills`; `ls -d
  /home/jwjung/skill-registry/skills` → exists.
- `home_claude_skills_dir_present` true — derived: `ls -d
  ~/.claude/skills` → exists.
- `target_repo_board_file_present` true — derived: `ls -d
  docs/specs/approvers.md` (in the worktree) → exists.
- `remote_push_access` false, hardcoded — this is the mandated
  behavior, not over-strict: the issue's own "must not" clause requires
  "must not report satisfied for a precondition it could not actually
  observe; unobservable means missing," and checking real push
  acceptance requires a mutating `git push` the script must never
  perform.

### 4. Handbook honesty — Present, with one phrasing overreach noted

canonical: `docs/handbooks/install-sufficiency.md` (reviewed copy, PR
#3184 sha `a7176f5d`), read in full and checked against the plugin's
actual mechanisms.

Checked all nine claims against what the plugin can actually do.

**Four "could be removed" claims** — grounded in a real, already-used
mechanism. derived: `grep -rl SessionStart on-the-record/hooks/` →
`spawn-allow-gate.sh`, `approval-gate.sh`, `self-update.sh` and others
already register for `SessionStart`, so "a `SessionStart` hook could
check git identity" and "a `SessionStart` hook could detect a missing
board file" (the git-identity and approvers.md proposals) cite a
mechanism that demonstrably exists in this plugin today — Present. The
`~/.claude/skills`-population proposal's phrase "bundled post-install
hook" overstates what Claude Code plugin hooks can literally trigger
on: derived: `cat on-the-record/.claude-plugin/plugin.json` → no
install-time lifecycle field exists in the plugin manifest, and Claude
Code's hook events are session events (`SessionStart`, `PreToolUse`,
...), not a marketplace install event. The realistic mechanism is the
same `SessionStart` first-run check the doc uses for the other two
proposals, not a distinct "post-install" hook. Surface — the proposal
is buildable, the label for it is imprecise. The skill-repository
vendoring proposal makes no mechanism claim beyond "the plugin package
could vendor a snapshot," which is a packaging change, not a hook
claim — Present.

**Five "cannot be removed" claims** — re-examined each for a modest
counter-fix the doc omitted. `claude` CLI and push-access-to-remote are
unchallengeable (the plugin runs inside the former; the latter is a
GitHub-side permission, not a local one). POSIX fork support is
genuinely structural: derived: the fork+setsid+dup2 pattern recurs at
both `spawn.py:2668-2680` and `spawn.py:4639-4649` (two independent
call sites doing the same detach dance), so it is load-bearing in
multiple places, not a one-line swap. `git` CLI: pure-Python
alternatives exist (dulwich, pygit2) but replacing it would also
require rewriting the shell-command-parsing hook gates
(`on-the-record/hooks/git-push-guard.sh`,
`on-the-record/hooks/gate-registration-guard.sh`) that key off literal
`git` invocations in Bash-tool command text — not modest, so "cannot be
removed [without a disproportionate rewrite]" holds. `gh` authentication
has one arguable stretch: "only the operator's own `gh auth login` can
produce" a token is slightly absolute — a plugin-driven OAuth
device-flow could in principle produce a token without a pre-existing
`gh auth login` — but that still requires an operator authorization
step, so the substance of the claim (some external GitHub auth step is
unavoidable) holds even if the specific mechanism named is not the only
possible one. No claim in the "cannot be removed" list is actually
removable with modest work; the list is not padded to excuse the gap.

### 5. Read-only behavior — Present (after ruling out an environmental false positive)

Initial testing inside `/tmp/pr3184-worktree` (a `git worktree add`
checkout) showed the reviewed copy's `PreflightReadOnlyTest` failing
intermittently under this repo's own default `pytest.ini` `addopts =
-n auto`, with the tracked file `scripts/preflight/consumer_preconditions.py`
itself losing content and a stray `mutation_side_effect.txt` appearing.
This was pursued as a potential genuine defect. It resolved to a false
positive caused by the shared sandbox host, not the deliverable:

derived: source inspection — `grep -n "open(\|write_text\|shutil\.\(copy\|move\|rmtree\)" scripts/preflight/consumer_preconditions.py`
→ no output; the script contains zero file-write calls anywhere in its
~230 lines.

derived: `cd /home/jwjung/pr3184-review-wt-parent/wt && python3 -m
pytest tests/test_issue_3182_preflight.py -q` (identical test file, a
worktree outside `/tmp`), repeated three consecutive times:
```
result: 7 passed in 9.52s
result: 7 passed in 8.81s
result: 7 passed in 9.12s
```
`git status --porcelain` was empty after each of the three runs above.

Mid-test in the original `/tmp` location, the `/tmp/pr3184-worktree`
directory itself vanished (`pytest` raised `FileNotFoundError: [Errno
2] No such file or directory: '/tmp/pr3184-worktree'`), which a
read-only Python script cannot cause to itself — this points at an
external `/tmp`-sweep on a machine running many concurrent, unrelated
sessions. derived: `find / -maxdepth 6 -iname conftest.py 2>/dev/null |
grep -v /proc | head -20` → returned 20 paths, all under other
sessions' `/tmp` worktrees and unrelated home-directory checkouts,
confirming this is a heavily multi-tenant host.

derived: `ls /tmp > before; python3 scripts/preflight/consumer_preconditions.py
>/dev/null 2>&1; python3 scripts/preflight/consumer_preconditions.py
--json >/dev/null 2>&1; ls /tmp > after; diff before after`
```
result: 59a60
> _after_immediate.txt
```
(the only new entry is the diff's own output-capture file, created by
this review's own shell redirection — no file created by the script
itself).

Conclusion for this section: the script does not mutate the working
tree. The exact same read-only test genuinely fails inside a `git
worktree` under `/tmp` on this host — a host-level artifact this
review traced and ruled out above — while the identical run outside
`/tmp` is clean every time, as shown in the three repetitions above.

### 6. Silent-failure audit of the preflight's own error handling — Present, 0 Silently Absorbed

canonical: `sed -n '39,49p' scripts/preflight/consumer_preconditions.py`
(reviewed copy, PR #3184 sha `a7176f5d`) and `sed -n '206,227p'
scripts/preflight/consumer_preconditions.py`, read in full per the
silent-failure-audit procedure (enumerate every catch site, classify
Handled/Silently-Absorbed/Unreachable).

- `_run_readonly()` (`consumer_preconditions.py:39-49`): `except
  Exception` → returns `(-1, "", f"{type(exc).__name__}: {exc}")`.
  **Handled**: callers treat any non-zero/`-1` returncode as
  unsatisfied; the exception text is preserved and surfaces in the
  `remedy` field, not swallowed.
- `run_checks()` (`consumer_preconditions.py:206-227`): each `c["fn"]()`
  call wrapped in `try`/`except Exception` → `ok, detail = False, f"check
  raised {type(exc).__name__}: {exc}"`. **Handled**: a defect inside any
  single check degrades that one entry to `satisfied: false` with the
  exception recorded, never a crash and never a silently-assumed
  `true` — exactly the fail-closed contract the issue's "must not"
  clause requires.
- derived: `grep -n "except" scripts/preflight/consumer_preconditions.py`
  → 3 matches total (the two above plus one nested `except OSError` in
  `check_skill_repository_resolvable`, which also degrades to the
  function's default `return False, (...)` rather than swallowing).
  No empty catch blocks, no bare `return None`/`return []` swallowed by
  an unchecking caller, and no default-value substitution that hides a
  failure were found.

### 7. Acceptance checks — Present (outside `/tmp`)

canonical: run in `/home/jwjung/pr3184-review-wt-parent/wt` (a `git
worktree` checked out from `pr-3184-review`, outside `/tmp`), 3
consecutive repetitions of each command below, all identical results:
```
acceptance: python3 -m pytest tests/test_issue_3182_preflight.py -q
result: 7 passed (identical on all 3 repetitions)
acceptance: python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"
result: 3 passed (identical on all 3 repetitions)
acceptance: python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q
result: 3 passed (identical on all 3 repetitions)
```

## Why

canonical: sections 1, 2, 5, and 7 above (this record's own derivation:
`sed`/`grep`/`awk` reads against `spawn.py`/`pipeline.py`/`skills.py`/
`board.py`/`plumbing.py`/`on-the-record/hooks/git-push-guard.sh`, plus
the `python3 -m pytest` runs, all executed in this session and
reproduced verbatim above).

Attacked the enumeration first, per the task brief, because a missing
precondition is the deliverable's central risk: the issue exists
specifically to make gaps visible, so an enumeration that appears
exhaustive but silently omits a real gate defeats the point of writing
one at all. Traced spawn dispatch independently of the script's own
citations and found `_spawn_capacity_check` this way (section 1) —
cross-checking only the nine cited lines would have missed it entirely.

Verified every citation next because the issue's contract text ("every
precondition asserted must cite the file and line that requires it")
is falsifiable per-entry and directly testable by opening the file.
The five imprecise/incorrect citations (section 2) share a pattern:
each points at the right function, often the right statement, but the
exact line drifts by a handful of lines from the line that actually
does what the description says — consistent with citations written
from memory of the function's shape rather than resolved by a tool
that pins exact line numbers.

Pursued the `/tmp` mutation finding to a root cause rather than either
dismissing it or reporting it uncritically, because the read-only
property is one of the issue's two explicit "must not" clauses and a
false accusation would be as much a review failure as a missed one.
The three convergent signals in section 5 (source has no write calls;
the three outside-`/tmp` reruns shown in section 5 are each clean; the
worktree directory itself disappeared mid-run inside `/tmp`) were
needed together — any one alone would have been ambiguous.

## What did not work

None. The `/tmp` mutation investigation in section 5 is not a reversed
approach — it is the review working as intended: an alarming signal
was chased to ground rather than reported at face value in either
direction.

## Upstream basis

Reviewed artifact: PR #3184 (tokenmaxxxer/on-the-record), branch
`pr-3184-review` fetched from `refs/pull/3184/head`, tip commit
`a526670a`.

- `scripts/preflight/consumer_preconditions.py` — sha `a7176f5daa94793f3b7691a4d58b58e56fb3a89e`
- `docs/handbooks/install-sufficiency.md` — sha `a7176f5daa94793f3b7691a4d58b58e56fb3a89e`
- `tests/test_issue_3182_preflight.py` — sha `a526670a1836bcc5e93d1ff5c9d0c2c93a7c8dd1`
- `tests/test_issue_3182_install_sufficiency_doc.py` — sha `a526670a1836bcc5e93d1ff5c9d0c2c93a7c8dd1`
- The builder's own delivery record (PR #3184, path
  docs/issue-3182/reports/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923.md,
  sha `e666b20b` per the PR's commit list) was read via `git show
  pr-3184-review:<path>` and is not reproduced at that path in this
  worktree, since that record path belongs to a different skill's
  write-set under this repo's board-gate (contract v3 s11) and this
  session writes only its own record.

Cited-against repo files (all confirmed identical between
`6ae02cced599252ad1c46daa068bff6eb71e0a1e`, the sha the builder's
record claims it read, and this branch's base
`b9446c8bfba74b4d90a22e5cb86acb39a3d5144d`):
derived: `git diff --stat 6ae02cce..b9446c8b -- spawn.py pipeline.py
skills.py board.py plumbing.py on-the-record/hooks/git-push-guard.sh`
```
result: (empty — no output, zero diff)
```
`spawn.py`, `pipeline.py`, `skills.py`, `board.py`, `plumbing.py`,
`on-the-record/hooks/git-push-guard.sh`, all sha
`b9446c8bfba74b4d90a22e5cb86acb39a3d5144d`.

Issue: `gh issue view 3182` (tokenmaxxxer/on-the-record#3182), quoted
verbatim in this session's task brief.

## Open findings

canonical: sections 1-7 above; each item below repeats its section
reference rather than re-deriving evidence already shown there.

1. **Absent** — `_spawn_capacity_check` (`spawn.py:729-751`, disk/inode
   headroom before workspace clone) is a real pre-spawn `sys.exit` gate
   not covered by the nine preconditions (section 1). Resolution path:
   add a tenth `CHECKS` entry (e.g. `workspace_disk_headroom`) citing
   `spawn.py:740,746` (the `disk_usage` call and the `sys.exit`), with a
   remedy pointing at `MUSTER_MIN_FREE_BYTES`/freeing space, plus a
   corresponding handbook row.
2. **Incorrect** — `gh_cli_authenticated`'s source cites `plumbing.py:349`
   (a cache check); the actual `gh auth token` call is `plumbing.py:355`
   (section 2). Resolution: update the source field to `plumbing.py:355`.
3. **Incorrect** — `git_identity_configured`'s source cites `board.py:76-79`
   (`git add`); the actual `git commit` call is `board.py:83-86`
   (section 2). Resolution: update the source field to `board.py:83-86`.
4. **Surface** — `remote_push_access`'s source cites
   `on-the-record/hooks/git-push-guard.sh:341` (a deny-message string in
   a fail-closed edge case); the primary enforcing logic is
   `_ROLE_BRANCH_RE.match(d)` at line 328 (section 2). Resolution: cite
   line 328, optionally alongside 341 for the remedy text's origin.
5. **Surface** — `posix_fork_support`'s source cites `spawn.py:2668`
   (background validity-consult fork) alongside `spawn.py:4639`
   (`_spawn_one`, correct); only 4639 is actually "drives spawned role
   sessions" (section 2). Resolution: drop 2668 or reframe it as "the
   same fork+setsid pattern used at 4639."
6. **Surface** — `claude_cli_on_path`'s source description "spawn_cmd
   builds cmd ... and execs it directly" is wrong about where the exec
   happens (`spawn.py:_spawn_one`, ~line 4761, not inside `spawn_cmd`
   itself) (section 2). Resolution: soften to "spawn_cmd builds the cmd
   list that `_spawn_one()` execs."
7. **Surface** — the handbook's `~/.claude/skills` removability proposal
   labels its mechanism a "bundled post-install hook," which Claude
   Code's plugin system does not literally have (no install-time
   lifecycle event; hooks are session events) (section 4). Resolution:
   reword to "a `SessionStart` first-run check," matching the
   git-identity and approvers.md proposals' actual mechanism.
8. **Methodology note for future re-verification** — the builder's own
   mutation-proof (`git status --porcelain` diff empty) showed no diff
   when the builder ran it, but this reviewer's rerun of the identical
   test flaked when run inside a `git worktree` under `/tmp` on this
   shared host (section 5). Not a defect in the deliverable itself —
   traced to host `/tmp` interference and ruled out in section 5 — but
   worth a one-line "tested outside /tmp" caveat in future records on
   similarly busy hosts.

Severity summary: none of the above make the deliverable
non-functional — section 7 reproduces all three acceptance-check
commands with zero failures across three repetitions each, section 5
confirms the read-only guarantee holds, and section 3 confirms every
satisfied and unsatisfied verdict on this machine is independently
correct. Items 2-7 are citation-precision defects against the issue's
own "cite the file and line that requires it" clause; item 1 is a
genuine enumeration gap.

## Next steps

canonical: this record's own sections 1-7 (no further verification
pending; the items below are handoff recommendations, not open
questions).

Recommended for the builder or a follow-up round: apply items 1-7 from
"Open findings" above (one missing `CHECKS` entry, four citation
corrections, two wording softenings). No design changes are needed —
the precondition model, the honesty framing, and the read-only
implementation are all sound; the defects found are citation-precision
and one enumeration gap, not structural. This record's own loop is
terminal (see frontmatter `loop_state`).

skill-verdict: adversarial-review — applied: invoked; ran PR #3184's
script and handbook through the blind-evaluator lens (a structurally
independent session verifying another session's deliverable per the
task brief), producing the per-item Present/Surface/Absent/Incorrect
grading above with located, re-derivable evidence for each.
skill-verdict: silent-failure-audit — applied: invoked; enumerated both
error-handling sites in `consumer_preconditions.py`
(`_run_readonly`, `run_checks`, plus the nested `except OSError`),
classified all three Handled, 0 Silently Absorbed — section 6.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
every citation-accuracy verdict above pins file:line-range,
the sha it was checked against, and (section "Upstream basis") the sha
the reviewed record itself claims for each upstream file, per the
skill's file:line+sha citation rule.
