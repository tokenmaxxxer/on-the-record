# Install sufficiency

This handbook answers one question honestly: does installing only the
on-the-record plugin let a consumer session work on a target repo? The
short answer is still no, but less no than it was: issue #3231 removed
two of the ten preconditions issue #3182 traced, and gave two more a
better error instead of a silent late failure. This document names all
ten, states which were removed and how, and states which ones cannot be
removed at all.

The preflight script at `scripts/preflight/consumer_preconditions.py`
checks these preconditions on a live machine. Run it with `--json` for
machine-readable output, or with no flag for a human-readable report.
It never mutates the machine — it only observes and reports; none of
the mechanisms this document describes live inside that script.

## What a plugin-only install already satisfies

Three preconditions hold without any manual step, once a session has
started at least once with the plugin active (the two skill-corpus ones
below are shipped by a `SessionStart` hook, not by `plugin install`
itself — see "What was removed"):

- The marketplace `plugin install` clone brings `spawn.py`, `pipeline.py`,
  and the rest of the driver code. `on-the-record/commands/run.md:10`
  sets `ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` and drives every command
  through `python3 $ON_THE_RECORD/spawn.py`. That resolves correctly
  because the marketplace add clones the whole repository, not just the
  `on-the-record/` plugin subdirectory (`docs/handbooks/setup.md:43-45`).
  No separate checkout is needed for this one piece.
- `skill-repository resolvable`: the `skill-corpus-bootstrap.sh`
  `SessionStart` hook runs `spawn.py ensure-skills`, which calls the same
  `_skill_repo_root()` resolution a real `--skills` spawn already used
  (env > sibling clone > managed clone, issue #1789) — the hook just
  moves *when* that call first happens, from "inside the first `--skills`
  spawn" to "session start." See "What was removed" below.
- `~/.claude/skills` populated (read as: *present* — see that section's
  caveat on what "populated" means here): the same hook creates this
  directory if absent, empty.

Nothing else on the list below is satisfied by a plugin-only install.

## What it does not satisfy

The table lists every other precondition the loop's real code paths
require, grouped by when the loop first needs it.

### Machine-level tools (needed before the first spawn)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| `claude` CLI on PATH | `pipeline.py:661` builds `["claude", "-p", ...]`; `spawn.py:4761` is what actually execs it, inside `_spawn_one()`. | No — see "cannot be removed" below. |
| `git` CLI on PATH | `pipeline.py:798` shells out to `git remote get-url origin` during workspace bootstrap. | No — see "cannot be removed" below. |
| `gh` CLI, authenticated | `plumbing.py:355` runs `gh auth token` to fetch the token spawned sessions use as `GH_TOKEN`. | No — see "cannot be removed" below. |
| Git identity configured (`user.name`, `user.email`) | `board.py:83-86` runs `git commit` directly during `init --push`; an unset identity fails that commit. | No, but the error moved earlier — see "stays manual, with a better error" below. |
| POSIX fork support | `spawn.py:4708` calls `os.fork()`/`os.setsid()` to detach each spawned role session (the same pattern also appears at `spawn.py:2706`, for an unrelated feature). | No — see "cannot be removed" below. |
| Disk/inode headroom before a workspace clone | `spawn.py:735-768` (`_spawn_capacity_check`, called at `spawn.py:3298`) exits before cloning if free bytes or inodes fall below a threshold. | No — see "cannot be removed" below. |

### Skill resolution (needed the first time `--skills` names a role)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| skill-repository resolvable | `skills.py:122-137` (`_skill_repo_root`) looks for `MUSTER_SKILL_REPO`, a sibling clone, or an already-populated managed clone — in that order. | Yes — shipped, see "what was removed" below. |
| `~/.claude/skills` populated | `skills.py:408` reads this path as one of four skill sources. | Yes (existence only) — shipped, see "what was removed" below. |

### Target-repo state (needed before any spawn against that repo)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| `docs/specs/approvers.md` present | `board.py:246-256` (`require_board`) exits before spawning if this file is absent from the target repo. | No, but discovery improved — see "stays manual, with a better error" below. |
| Push access to `origin` for the spawning account | `on-the-record/hooks/git-push-guard.sh:328` requires every spawned session to push its own `issue-<n>/<skill>` branch. | No — see "cannot be removed" below. |

## What was removed (issue #3231)

- **skill-repository resolvable — tier: on-first-need-with-notice,
  automatic.** `skills.py`'s `_skill_repo_managed_root()` already cloned
  skill-repository into the plugin's own cache
  (`runs/rulebooks/skill-repository/`) when nothing else resolved it —
  issue #1789 shipped that months before this handbook's first version
  claimed "no automatic clone" (`docs/handbooks/setup.md`, fixed by this
  issue). What was missing was *proactivity*: that clone only ran inside
  a real `--skills` spawn, so a session's first `--skills` attempt paid
  the network round-trip inline, or failed outright if offline with no
  prior clone. The `skill-corpus-bootstrap.sh` `SessionStart` hook now
  calls `spawn.py ensure-skills` (`skills.py:ensure_skill_corpus_cli`) at
  session start instead, so the corpus is usually already there by the
  time a spawn needs it.

  The tier is automatic-with-notice, not silent. Cloning into the
  plugin's own cache is safe to do unasked — it writes nothing the user
  owns. But a multi-second network fetch happening invisibly, the first
  time a user tries `--skills`, is a worse surprise than one line on
  stderr at session start (`[skill-repo] skill-repository 를 받는 중`).
  This issue's own must-not says the same thing: prefer telling the
  user over surprising them.

  This issue's acceptance requires demonstrating the interrupted-fetch
  case, so the fetch itself was hardened. `_skill_repo_managed_root()`
  now clones into a scratch directory next to the final path. It checks
  the git subprocess's own exit code *and* the checkout's actual
  content, and only then `os.replace()`s the scratch directory into
  place. A fetch killed mid-transfer — network drop, process kill,
  anything short of the clone finishing — leaves the scratch directory
  as garbage, cleaned up on the next attempt. The real path stays
  untouched, so `skill_repository_resolvable` keeps reading unsatisfied
  until a fetch actually completes.

  Before this change, `git clone` targeted the final path directly. A
  kill after some (not all) skill directories had already been checked
  out could leave that path non-empty. The same "any non-dot
  subdirectory exists" validity check would have read that partial
  state as satisfied. `test/test_skill_repo_managed_clone.py` and
  `tests/test_issue_3231_install_removals.py` both exercise this.

- **`~/.claude/skills` populated — tier: automatic.** The same
  `SessionStart` hook creates this directory (under the user's own home
  directory, `Path.home() / ".claude" / "skills"`) if it's absent, empty. This
  is the lowest-risk removal in the set: `skills.py:213`
  (`_local_skill_dirs`) already treats an absent directory and an empty
  one identically (zero skills contributed either way), so creating it
  changes nothing about what skills resolve — it only satisfies the
  precondition's literal definition (existence, not content). No
  content is written, so there's nothing to interrupt and nothing that
  can read as "populated" when it isn't; the risk this issue's must-not
  clause is aimed at (a corpus that looks complete but isn't) does not
  apply to an intentionally-empty directory.

## Stays manual, with a better error

Two preconditions cannot be removed — the operator's own git identity is
their choice to make, and a target repo's board file is per-repo state
the plugin has no authority to invent before a session ever opens that
repo — but issue #3231 moved both failures earlier, from deep inside a
spawned session to a `SessionStart` notice
(`install-precondition-notices.sh`), the same "tell, don't surprise"
call as the skill-corpus fetch above:

- **Git identity.** The hook runs `git config --get user.name`/
  `user.email` (read-only — it must not modify the user's global git
  config, and doesn't) and prints the exact `git config --global` remedy
  if either is unset, instead of letting the failure surface inside
  `board.py`'s `git commit` during `init --push`.
- **`docs/specs/approvers.md`.** The plugin already shipped the fix —
  `spawn.py init -C <repo>` creates this file — what was missing was
  discovery. When the hook's cwd looks like a git checkout (a `.git`
  directory present) with no board marker, it prints the `init` command
  as a suggested next step.

Neither check flips its preflight bit: `check_git_identity_configured()`
and `check_target_repo_board_file_present()` still observe the same
real state they always did, honestly, and a printed reminder does not
change that state. What changed is how early the operator finds out.

## Preconditions that cannot be removed

Four preconditions are structural. No plugin-side change removes them,
because each one names a real external system the loop has no
authority over. (Git identity and the board-file precondition moved out
of this list's predecessor into "stays manual, with a better error"
above — the precondition itself is still unremovable, but the failure
mode improved.)

- **The `claude` CLI itself.** The plugin runs inside that CLI. It
  cannot bootstrap the program that hosts it.
- **The `git` CLI.** Every workspace clone, branch checkout, and PR
  push in the loop shells out to a real `git` binary. There is no
  pure-Python substitute that speaks the same remote protocols.
- **`gh` authentication.** The loop reads a GitHub identity token that
  only the operator's own `gh auth login` can produce. A plugin cannot
  authenticate on the operator's behalf.
- **POSIX fork support.** `os.fork()`/`os.setsid()` are properties of
  the host operating system. This is also why native Windows is out of
  scope (`docs/handbooks/setup.md`) — WSL supplies the missing POSIX
  layer, a plugin cannot.
- **Push access to the target repo's remote.** Whether `origin` will
  accept a push is a permission the remote host (GitHub) grants, not
  something the local machine or the plugin can decide. The preflight
  script reports this precondition as unsatisfied unconditionally,
  because checking it for real would require an actual write.
- **Disk/inode headroom on the host.** Free bytes and free inodes are
  properties of the machine the session runs on. A plugin cannot
  create disk space; it can only refuse to clone before running out
  (`spawn.py:735-768`), which is what it already does.

## Reading this honestly

Ten preconditions were traced from real code paths. Before issue #3231,
one was satisfied by a plugin-only install. After it, three are — the
skill corpus (the precondition that mattered most: a `--skills` spawn
finding nothing was the difference between the loop working and not)
and its local-override directory both moved from manual to automatic-
with-notice. Two more preconditions still cannot be removed, but no
longer fail silently late — they surface at session start instead. Four
remain genuinely structural: they name a CLI, an OS capability, a
remote-side permission, or free disk, none of which any plugin change
can supply. The gap this document exists to make visible is smaller now
than it was, and still real where it remains.
