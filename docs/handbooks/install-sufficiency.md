# Install sufficiency

This handbook answers one question honestly: does installing only the
on-the-record plugin let a consumer session work on a target repo? The
short answer is no. Several preconditions live outside the plugin's
reach. This document names them, states which ones the plugin could
remove, and states which ones it cannot.

The preflight script at `scripts/preflight/consumer_preconditions.py`
checks these preconditions on a live machine. Run it with `--json` for
machine-readable output, or with no flag for a human-readable report.
It never mutates the machine — it only observes and reports.

## What a plugin-only install already satisfies

One precondition holds today without any manual step: the marketplace
`plugin install` clone brings `spawn.py`, `pipeline.py`, and the rest
of the driver code. `on-the-record/commands/run.md:10` sets
`ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` and drives every command
through `python3 $ON_THE_RECORD/spawn.py`. That resolves correctly
because the marketplace add clones the whole repository, not just the
`on-the-record/` plugin subdirectory (`docs/handbooks/setup.md:43-45`).
No separate checkout is needed for this one piece.

Nothing else on the list below is satisfied by the install step alone.

## What it does not satisfy

The table lists every other precondition the loop's real code paths
require, grouped by when the loop first needs it.

### Machine-level tools (needed before the first spawn)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| `claude` CLI on PATH | `pipeline.py:663` execs `["claude", "-p", ...]` directly to start every role session. | No — see "cannot be removed" below. |
| `git` CLI on PATH | `pipeline.py:798` shells out to `git remote get-url origin` during workspace bootstrap. | No — see "cannot be removed" below. |
| `gh` CLI, authenticated | `plumbing.py:349` runs `gh auth token` to fetch the token spawned sessions use as `GH_TOKEN`. | No — see "cannot be removed" below. |
| Git identity configured (`user.name`, `user.email`) | `board.py:76-79` runs `git commit` directly during `init --push`; an unset identity fails that commit. | Partially — see "could be removed" below. |
| POSIX fork support | `spawn.py:2668` and `spawn.py:4639` call `os.fork()`/`os.setsid()` to detach each spawned session. | No — see "cannot be removed" below. |

### Skill resolution (needed the first time `--skills` names a role)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| skill-repository resolvable | `skills.py:96-112` (`_skill_repo_root`) looks for `MUSTER_SKILL_REPO`, a sibling clone, or an already-populated managed clone — in that order. | Partially — see "could be removed" below. |
| `~/.claude/skills` populated | `skills.py:338` reads this path as one of four skill sources. No plugin install writes anything here. | Partially — see "could be removed" below. |

### Target-repo state (needed before any spawn against that repo)

| Precondition | Why the loop needs it | Removable by the plugin? |
|---|---|---|
| `docs/specs/approvers.md` present | `board.py:246-256` (`require_board`) exits before spawning if this file is absent from the target repo. | Partially — see "could be removed" below. |
| Push access to `origin` for the spawning account | `on-the-record/hooks/git-push-guard.sh:341` expects every spawned session to push its own `issue-<n>/<skill>` branch. | No — see "cannot be removed" below. |

## What could be removed by changing the plugin

Four of the nine preconditions above are partially addressable. None
of the fixes below are shipped yet — they are concrete proposals, not
claims about current behavior.

- **Git identity.** A `SessionStart` hook could check `git config
  --get user.name`/`user.email` and print a one-line remedy before the
  first Bash tool call, instead of letting the failure surface deep
  inside a spawned session's `git commit`. This does not remove the
  precondition — the operator still configures git identity once —
  but it moves the failure to install time, where it is cheap to fix.

- **skill-repository.** The plugin package could vendor a snapshot of
  skill-repository's content inside `on-the-record/skills/`, refreshed
  on a release cadence. This trades a manual clone for a version-skew
  risk: vendored skills would lag the upstream skill-repository between
  releases. That tradeoff needs an explicit decision, not a silent
  default.

- **`~/.claude/skills`.** A bundled post-install hook could populate
  this directory from a plugin-shipped skill set on first run. Doing
  this changes what "install" means, from "add a plugin" to "add a
  plugin and write into the user's home directory" — a bigger
  footprint that should be opt-in, not automatic.

- **`docs/specs/approvers.md`.** The plugin already ships the fix:
  `spawn.py init -C <repo>` creates this file. What is missing is
  discovery — nothing prompts a first-time operator to run it. A
  `SessionStart` hook could detect a target repo with no board marker
  and print the `init` command as a suggested next step.

## Preconditions that cannot be removed

Five preconditions are structural. No plugin-side change removes them,
because each one names a real external system the loop has no
authority over.

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

## Reading this honestly

Nine preconditions were traced from real code paths. One is satisfied
by a plugin-only install today. Four have a concrete, partial fix a
future plugin change could ship. Five are structural and stay outside
the plugin's reach permanently. The gap this document exists to make
visible is real — it does not close by writing more documentation.
Closing it, where it can close, means shipping the four remedies
above, one at a time, each as its own change with its own tradeoff
made explicit.
