# Survey — issue #619: Korean strings in repo-bound output

## Scope of this survey

Swept the deployed surface (spawn.py, gates/*.py, on-the-record/gates/*.py,
on-the-record/hooks/*.sh) for Korean (Hangul) strings and classified each
site as repo-bound (lands in a GitHub issue/PR comment or a committed file)
or console-only (local stdout/stderr, never persisted to the repo or
GitHub). Method: `grep -rn -P '[\x{AC00}-\x{D7A3}]'` across non-docs source
files, then traced each hit's sink (does it feed a `subprocess.run(["gh",
"api", ...])` call writing a comment, or a `print()`/`file=sys.stderr`).
Comments and docstrings (never emitted at runtime) are excluded from the
inventory — issue #619 is about emitted output, not source prose.

## Repo-bound emitters (must change) — all in `spawn.py`

Four functions post Korean directly into `gh api` issue-comment bodies
(`repos/{slug}/issues/{issue}/comments`):

1. `_post_crash_comment` (around spawn.py line 2391) — body uses
   `f"트리거: {trigger}\n워크스페이스: {work}\n로그: {log}\n\n"` plus a Korean
   sentence about exhausted respawn attempts. The marker constant itself,
   `_CRASH_COMMENT_MARKER` (spawn.py line 2377), embeds Korean: `"...:
   crashed, 재스폰 상한({cap}) 도달"`.
2. `_post_stall_comment` (around spawn.py line 2419) — body uses
   `f"워크스페이스: {work}\n로그: {log}\n\n"` plus a Korean sentence about the
   stalled verdict and no-auto-respawn policy.
3. `_post_session_end_comment` (around spawn.py line 2459) — body uses
   `f"{marker} {line}\n\n워크스페이스: {work}\n로그: {log}"`.
4. `_post_stranded_push_comment` (around spawn.py line 2503) — body uses
   `f"브랜치: {branch}\n사유: {reason}\n상세: {detail[:200]}\n\n"` plus a
   Korean sentence about the session having stalled and needing human
   intervention.

Field labels repeated across these four: 워크스페이스 (workspace), 로그
(log), 트리거 (trigger), 브랜치 (branch), 사유 (reason), 상세 (detail).
Converting these to stable English labels (`workspace:`, `log:`,
`trigger:`, `branch:`, `reason:`, `detail:`) gives downstream consumers
(e.g. #597's framing writer, any future issue-comment scraper) one
consistent, locale-stable vocabulary instead of four ad hoc bilingual
templates.

## Parser dependency check

Searched `test_spawn.py` and `spawn.py` itself for anything matching the
Korean field labels or sentence text: none found. The only string matched
by code is the **marker constant as a whole** (`marker in c.get("body",
"")` idempotency checks inside each `_post_*_comment` function, and
equivalent assertions in `test_spawn.py` around lines 4539, 4604, 4647,
4674, 4719, 4975, 4473, 4509) — those all go through the
`_XXX_COMMENT_MARKER` constants, never a literal Korean string, so
changing the marker text (including the Korean substring inside
`_CRASH_COMMENT_MARKER`) requires no test-literal edits, only that the
constant itself changes consistently with its one use site. No parser in
this repo matches on the Korean body prose or field labels directly — the
field labels can be translated without touching a second unit, but the
*marker string's own Korean substring* is being changed too, in the same
unit that defines and formats it (`spawn.py`; no separate parser file).

## Console-only Korean (out of scope, left as-is)

Traced to plain `print()`/`file=sys.stderr` calls that never reach `gh`
or a file write — per issue #619's carve-out, local console-only UX may
stay Korean:

- spawn.py around lines 3590, 3601, 3625, 3627 — `clean` subcommand's
  per-workspace status lines and the "정리 끝 — 지움 N, 남김 N" summary
  (the exact string named in the issue text) — local CLI stdout only.
- spawn.py around line 3099 — kill-signal confirmation, `print()`.
- spawn.py around line 3886 — credential-leak-prevention warning,
  `print()`.
- spawn.py around line 4207 — live-log path, `print(..., file=sys.stderr)`.
- spawn.py around lines 4496, 4525 — respawn/uncommitted-changes hints,
  `print()`.
- spawn.py around line 3479 — argparse `help=` text for `watch`, surfaces
  only in `--help` output.
- `gates/*.py`, `on-the-record/gates/*.py`, `on-the-record/hooks/*.sh` —
  Korean found here is either (a) violation/refusal strings returned by
  gate functions and printed to local stdout/CI log, never posted to a
  GitHub comment or written into a committed record by the gate itself
  (traced every `gh api ... comments` call site in `gates/*.py`: the only
  one is `post_sweep_comments` in `gates/closure_sweep.py`, around line
  238, whose body comes from `format_report()`, which contains no
  Korean), or (b) hook-side regex patterns matching the *assistant's own*
  Korean prose in its replies (e.g. `role-test-claim-guard.sh` around
  line 55, `report-framing-check.sh` around line 39) — these are
  session-local refusal detectors, not repo-bound emitters, and are out
  of this issue's acceptance criteria (which is about emitters, not the
  assistant's conversational Korean).
- All docstrings and inline `#` comments throughout spawn.py, bench/,
  gates/, on-the-record/ — never emitted at runtime.

## Write set implied

- `spawn.py` — the four comment-emitting functions and the four marker
  constants (only `_CRASH_COMMENT_MARKER`'s embedded Korean substring
  needs a text change; the other three markers are already English).
- `test_spawn.py` — no literal-text changes expected (markers are
  referenced via constants, not retyped), but the full suite must still
  be run green after the emitter change since these tests assert on
  comment bodies built from the same f-strings.

No new dependency, no schema change, no migration.
