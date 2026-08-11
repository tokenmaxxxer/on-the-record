# Survey — issue-742: permission-denial retry loop after #695

Scout: skipped. No product/exemplar field applies to the allowlist-scope
question itself — this is an empirical measurement task against this
repo's own `spawn.py`, the same skip condition used by
`docs/issue-304/reports/architecture/survey.md`. One scout-shaped
question did exist — "how does bypassPermissions actually relate to
`permissions.allow`, authoritatively" — and was answered by fetching
Anthropic's own Claude Code docs (cited in the empirical section below)
rather than skipped, since that answer is load-bearing for the
recommendation.

## Current-state: what issue #742 assumed vs. what's on `main` now

`spawn.py`'s `role_settings()` (lines 420-547) still builds a
`permissions.allow` list exactly as issue #742 describes:

```
$ grep -n 'allow = s.setdefault' spawn.py
502:    allow = s.setdefault("permissions", {}).setdefault("allow", [])
```

- `WebSearch`, `WebFetch`, `Read`, `Grep`, `Glob` (spawn.py:503-505)
- `_workspace_bash_allow(cwd)` — six `cd {cwd} && ...`-anchored venv/pip/test
  patterns (spawn.py:400-417), added only when `cwd is not None`
  (spawn.py:515-518)
- `MUSTER_MCP_ALLOW` entries, `mcp__`-prefixed only (spawn.py:535-539)

No general `Bash` entry exists anywhere in this list — issue #742's
premise is correct as a description of `role_settings()`'s
`permissions.allow` content, unchanged on `main` today.

What issue #742's premise does **not** account for: a second commit,
landed the same day and before this session's own branch point, changed
which permission *mode* every real role spawn runs under.

```
$ git log -1 --format='%H %ad %s' b762681
b7626813e0ed0d63885ad39444396146687aa2ce Tue Aug 11 10:38:06 2026 +0900 fix(issue-700): headless role sessions spawn with bypassPermissions
```

commit message (full):

```
fix(issue-700): headless role sessions spawn with bypassPermissions

After #695/#697 removed the role-session sandbox, every Bash call faces
the CLI approval classifier and headless sessions have no approving
turn — issue-698/699 sessions (and a target-repo issue-319 session)
died failed-no-commit on plain git add / gh calls. The sandbox had been
doubling as the execution license; operator decision makes
bypassPermissions the headless default. Enforcement stays with hooks
(PreToolUse exit 2), which bypassPermissions does not disable.
```

The resulting code, still on `main` today:

```
$ sed -n '3465,3467p;3588,3590p' spawn.py
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "--verbose"]
        cmd = ["claude", "-p", "--settings", settings_path,
              "--permission-mode", "bypassPermissions",
              "--output-format", "json"]
```

The first block is `spawn_cmd()` (real deliverable-producing role spawns,
what `_spawn_one()` uses); the second is `consult_cmd()` (advisory-only
spawns). Every other `["claude", ...]` subprocess call in `spawn.py`
(lines 326, 715, 3406) is a marketplace warm-up / plugin install /
hook-firing doctor probe — none does role work, none risks the
denial-retry loop issue #742 measures, and none carries `--permission-mode`
at all. So every code path that actually does role work is on
`bypassPermissions` already, unconditionally, for every role — there is
no role or invocation branch left on the old mode.

## What `bypassPermissions` does to `permissions.allow` (authoritative, not inferred)

Fetched from Anthropic's own docs, `https://code.claude.com/docs/en/permission-modes`:

> `bypassPermissions` mode disables permission prompts and safety checks
> so tool calls execute immediately, including writes to protected paths.

> Allow rules have no effect in `bypassPermissions` because everything
> else is already approved.

> [Hooks](/docs/en/hooks): custom permission logic via `PreToolUse` and
> `PermissionRequest` hooks

This directly answers issue #742's second research question
("#695 이후 Bash 가 어느 계층에서 판정되는지 실측") for the
current state of `main`: since #700 landed, `permissions.allow`'s Bash
content (or lack of it) is not in the decision path for any real role
spawn at all — `bypassPermissions` pre-approves everything, and the only
remaining judge of a tool call is a `PreToolUse`/`PermissionRequest` hook
(gate) that explicitly exits non-zero. Widening `role_settings()`'s
`permissions.allow` now would not change what a `bypassPermissions`
session can or cannot run — the mode has already made that list inert
for the paths that matter.

## Empirical measurement — this exact session, live (provenance: executed-live)

This session (`CLAUDE_ROLE=implementation`, branch `issue-742/implementation`)
is itself a role session spawned by `spawn.py`'s `spawn_cmd()` — the
literal subject of issue #742's requested measurement. Confirmed via the
actual running process, not inferred:

```
$ ps -ef | grep -i "bypassPermissions" | grep -v grep
  501 24510 24508   0  3:11PM ??  claude -p --settings /var/folders/.../tmpcxamhg_f.json --permission-mode bypassPermissions --output-format stream-json --verbose --plugin-dir .../tokenmaxxxer-implementation/coding [...] --model sonnet
```

Four probes, one per pattern issue #742 names, run in this session with no
prior warm-up or special-casing:

| Pattern (issue #742's wording) | Probe command | Result |
|---|---|---|
| 복합명령(`&&`) 부분승인 | `echo step1 && echo step2` | succeeded, no prompt |
| `/tmp` 쓰기 | `echo hi > /tmp/issue742_perm_probe.txt && cat ... && rm ...` | succeeded, no prompt |
| 미승인 단순명령 (not in any `permissions.allow` entry above) | `python3 -c "print('probe-bare-python3-c')"` | succeeded, no prompt |
| BOM 패턴의 명령 모양 (python3 heredoc) | `python3 <<'EOF' / print(...) / EOF` | succeeded, no prompt |

A fifth probe not in the issue's four patterns but relevant to the
sandbox-removal ADR's accepted risk (writes outside the sandboxed
filesystem boundary): a bare `curl` to an arbitrary, non-allowlisted host
(`https://example.com`, not in `PACKAGE_REGISTRY_HOSTS`) also succeeded
with no prompt — consistent with `bypassPermissions` pre-approving
network calls too, and with the #695 ADR's already-accepted consequence
"network egress is no longer domain-limited."

```
derived: the four-row probe table above, each row run directly in this
session this turn — 4 commands, 4 succeeded, 0 permission denials
```

## BOM/유니코드 공백 — diagnosed separately, same layer

Issue #742 asks for BOM/unicode-whitespace denials to be diagnosed as a
possibly-independent cause. Two checks:

1. **Is our own code producing a BOM in generated Bash text?** Every
   `utf-8-sig`-encoded read in this repo is a *read*, not a write —
   `encoding="utf-8-sig"` strips a BOM defensively if one is already
   present in a file being read; it does not add one on write. Every
   matching call site reads, none writes:

   ```
   $ grep -rn "utf-8-sig" --include="*.py" . | grep -v "\.git/"
   spawn.py:1146:        text = record.read_text(encoding="utf-8-sig", errors="replace")
   spawn.py:1258:        text = p.read_text(encoding="utf-8-sig", errors="replace")
   gates/claims.py:104:            f.read_text(encoding="utf-8-sig", errors="replace"))
   gates/ci.py:256:        return base64.b64decode(content).decode("utf-8-sig", errors="replace"), None
   gates/claim_scan.py:192:        text = path.read_text(encoding="utf-8-sig", errors="replace")
   gates/record_lint.py:159:    text = path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""
   gates/gates.py:338,383,655,726,776,1249: same .read_text(encoding="utf-8-sig", ...) pattern
   on-the-record/gates/gates.py, on-the-record/gates/record_lint.py: duplicate paths, same pattern
   ```

   No raw BOM bytes and no `﻿`/` `/`​` literal exist in
   any tracked file:

   ```
   $ git grep -lP "\xEF\xBB\xBF" -- .
   (no output)
   $ grep -rlP "[\x{00A0}\x{200B}\x{FEFF}]" --include="*.py" .
   (no output)
   ```

   This repo's own code is not the source of the BOM/unicode whitespace
   issue #742's 27-count bucket names.

2. **Is the BOM pattern the same CLI-classifier layer #700 already
   bypassed, or a genuinely separate gate?** The "Contains Unicode
   whitespace" wording issue #742 quotes is the CLI's own approval-prompt
   text — the same classifier that produces the compound-command and
   unapproved-simple-command prompts, per the docs excerpt above
   ("`bypassPermissions` mode disables permission prompts and safety
   checks"). The live probe above (`python3` heredoc, the exact shape
   the issue cites for the 12-retry BOM case) reproduced no denial in
   this `bypassPermissions` session. This is consistent with BOM/unicode-
   whitespace denials sharing the same root layer as the other three
   patterns, already addressed by #700 — not a second, independent gate
   still open after #700.

This repo has no local copy of the 219-session/1,540-refusal log corpus
issue #742 cites (searched `docs/`, `runs/` for a denial-log or
performance-analysis artifact — none found); that count is accepted as
given context from the issue body, not independently re-derived here.
The historical counts plausibly predate `b762681` (2026-08-11 10:38, the
morning of the same day) — this survey does not claim to know their
exact timestamp relative to that commit, only that every role-work code
path on `main` today runs past that commit.

## Representative task, this session (문서 커밋 + PR 생성 + 테스트 실행)

The rest of this phase-1 turn — committing this survey and the proposal,
opening the PR, and the test run below — **is** the representative task
issue #742's Acceptance-1 asks for, executed live in a headless role
session:

```
$ python3 -m pytest gates/test_boundary.py gates/test_generated_paths.py tests/test_gates.py -q
...
FAILED gates/test_boundary.py::t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
3 failed, 121 passed in 25.39s
```

Matches exactly the three pre-existing reds named in this session's
operating instructions (owned by issue-759, not touched here) — no new
failures.

```
$ python3 -m pytest tests/test_spawn.py -k "allow or permission or bash_entry or workspace_bash" -q
17 passed, 384 deselected in 7.28s
```

Today's `role_settings()` allowlist-building logic is already covered by
this passing suite and does not need new tests to keep working as-is —
the proposal below touches only comments in that function, not behavior.

## Judgment: what belongs in the allowlist

Nothing. Expanding `permissions.allow` in `role_settings()` — the
compound-command, simple-command, and `/tmp`-write patterns issue #742
names as candidates — would have **no behavioral effect** on any real
role spawn: `bypassPermissions` already "has no effect" for allow rules
per the docs cited above, and every role-work spawn path is already on
that mode. This satisfies Acceptance-1's own stated empty state:
"확장 대상이 없다고 판단되면 그 근거와 함께 거부 0건 기준선을 기록하고
종료한다" — the 0-denial baseline is the four-probe table above,
executed live in this session. Acceptance-2 ("확장된 허용목록이
워크스페이스 밖 쓰기를 새로 허용하지 않음을 단위 테스트로 단언") is
correspondingly N/A per its own stated empty state, since no expansion
is proposed.

The one gap the survey does surface: `role_settings()`'s comments at
spawn.py:492-501 and 507-518 still describe the pre-#700 threat model
("headless 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이
없어서 permissions.allow 에 없는 규칙은 그냥 거부된다") as the reason
those `permissions.allow` entries exist, without noting that `bypassPermissions`
(landed after those comments were written, for #58/#65/#153/#558) has
since made the list's Bash-relevant portion inert for the spawn paths
that use it. A future maintainer reading only those comments would
reasonably conclude `permissions.allow` is still the operative Bash
boundary — it is not; `PreToolUse`/`PermissionRequest` hooks are. This
is a documentation-accuracy gap, not a functional one, and is proposed
below as a comment-only annotation.
