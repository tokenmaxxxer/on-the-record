# Survey — issue #1141

## Scout: skipped

Pure bugfix (survey-order-directive skip condition #1): the defect is a
missing env-var injection with a known-good sibling implementation in
the same file to mirror. No design/product decision is open.

## Root cause

canonical: spawn.py:4368-4406 (consult_cmd, read directly), spawn.py:4283-4306 (spawn_cmd, read directly)

`spawn.py:4368` `consult_cmd()` builds its subprocess env at
`spawn.py:4405`:

```
env = {**os.environ, "CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
```

It never sets `CLAUDE_PLUGIN_ROOT_CORE`.

Compare `spawn_cmd()` (the delivery-session path), `spawn.py:4296-4305`,
which resolves `core_dir` from `core_plugins` and injects
`env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)` — added for issue #182
specifically so rulebook gate hooks can find core's shared
`hooks/lib/gate-lib.sh` without depending on a relative fallback that
only works inside an installed/consumer layout.

`terse.sh` sources, at its own line 18:

```
. "${CLAUDE_PLUGIN_ROOT_CORE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/hooks/lib/gate-lib.sh"
```

canonical: /home/jwjung/tokenmaxxxer-core/terse/hooks/terse.sh:18 (read directly)

Without `CLAUDE_PLUGIN_ROOT_CORE`, the fallback resolves to
`<rulebook-checkout>/terse/hooks/lib/gate-lib.sh` — a path that has
never existed; `gate-lib.sh` lives only under the sibling `core` plugin.

canonical: derived: find / -path /proc -prune -o -iname "gate-lib.sh" -print 2>/dev/null

```
$ find / -path /proc -prune -o -iname "gate-lib.sh" -print 2>/dev/null
/home/jwjung/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh
```

Single hit, under `core/hooks/lib/`; zero hits under any `terse/` tree
across every rulebook checkout on this machine.

The source fails, `terse.sh` prints `terse.sh: cannot source gate-lib.sh`
and `exit 2`, and that stderr text becomes the entire "model output"
`consult_cmd()` later fails to parse as verdict JSON — matching the
signature the issue describes (hook-block error text captured as model
output, no verdict JSON present).

`spawn_cmd()`'s own comment documents the exact failure mode this
reproduces (spawn.py:4293-4299, read directly): "이 변수를 주입하지
않으면 상대 fallback 이 룰북 클론 내부를 가리켜 실배포에서 해석 실패 →
무가드 source 와 결합 시 게이트 전면 fail-open." `consult_cmd()` never
received that fix when it was added for issue #182 — a drift between
the two spawn paths, the same drift class the `consult_cmd()` docstring
itself flags for rulebook loading via `plugin_dirs()`/`role_settings()`
reuse (spawn.py:4377-4380, read directly) but which this one env line
escaped.

## Requirement 2 (fail-open / loud-skip scope) — where it lives

canonical: directory listing of /home/jwjung/tokenmaxxxer-core (separate git checkout, read directly this session) vs. this repo's own root (no terse/ or core/hooks/lib/ tree present)

`terse.sh` and `gate-lib.sh` are files in the `tokenmaxxxer-core`
GitHub repo, not in this repo (`on-the-record`). This repo's role-
handoff contract restricts the write set to files inside this
checkout; `tokenmaxxxer-core` is a separate clone, separate issue
tracker, separate role sessions per the `docs/issue-<n>` convention
observed under `~/.tokenmaxxxer/work/tokenmaxxxer-core-issue-*`.
Requirement 1 ("fix the generator") is answerable from this repo —
`consult_cmd()` is exactly "the generator" the requirement names.
Requirement 2 (hard-block vs fail-open scope) requires editing
`terse.sh`'s own source-guard, which lives in `tokenmaxxxer-core`, not
here — outside this issue's reachable write set. The proposal below
scopes to requirement 1 (root-cause fix) + requirement 3 (regression
test) and documents requirement 2 as a cross-repo follow-up to file
against `tokenmaxxxer-core`.

## Files that will change

- `spawn.py` — inject `CLAUDE_PLUGIN_ROOT_CORE` into `consult_cmd()`'s
  subprocess env, mirroring `spawn_cmd()`.
- `gates/` — new hermetic gate test asserting `consult_cmd()`'s env
  resolves `gate-lib.sh` against a fixture layout (i.e. the env var a
  consult subprocess receives points at a directory containing
  `hooks/lib/gate-lib.sh`), pinned so the two spawn paths cannot
  re-diverge silently again.

## Alternative considered and rejected

Duplicate `core_plugin_dirs()`'s resolution inline inside `terse.sh`'s
own bash fallback (widen the relative-path fallback to also check a
`core` sibling directory next to the rulebook checkout) — rejected
because that file is not in this repo's write set (see above), and even
if it were, it would re-implement path resolution `consult_cmd()`
already has correct machinery for (`core_plugin_dirs()`), producing two
competing resolution strategies instead of one shared one.
