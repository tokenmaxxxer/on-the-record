---
subject: issue-2039
kind: survey
---

# Survey — per-mounted-skill verdict obligation (issue #2039)

## Where the mounted-skill list is assembled (spawn.py)

canonical: spawn.py:8143-8196 (read directly)

`spawn.py` builds the mounted-skill list into the spawned task's prompt text at two independent call sites, never into a machine-readable file:

- `spawn.py:8143-8151` — `--skills` path (issue #1742/#1774): if `skill_sources` is non-empty, appends a line literally prefixed `마운트된 스킬(--skills, 이슈 #1742/#1774): ` followed by a comma-joined `name (trigger) (source)` list.
- `spawn.py:8152-8182` — role→skill-repository mapping path (issue #1955/#1758): if `role_source["source"] == "skill-repo"`, appends `이 역할은 skill-repository(...)로 매핑됐다: 스킬 <names...> (skill-repository <sha>) 가이던스만 붙는다 — 집행은 core 훅뿐이다.<cross_family_clause>`. `role_skill_lines` folds in issue #2001's cross-family top-K matches, so this one line can carry both family-mapped and cross-family names.

derived:
```
grep -n "마운트된 스킬\|가이던스만 붙는다" spawn.py
```
matches at spawn.py line 8151 and spawn.py line 8181, confirming these two assembly points.

Both blocks are optional and independently gated; a session can carry either, both, or neither. Neither block writes a manifest anywhere in the target repo's working tree or in a location the target repo's git hooks/CI can read — the only place the mounted-skill list exists is the spawned session's own first-user-message text, inside its transcript.

Immediately after (`spawn.py:8191-8196`), a third block (issue #1960 phase B) fires whenever either list is non-empty: it appends the "스킬 점검" nudge instructing the session to cross-check the mounted list against the task before starting substantive work. This is exactly the directive text visible in this very session's own spawn prompt (canonical: this session's own first user message, which carries the "스킬 점검(이슈 #1960)" paragraph verbatim) — it is guidance-only prose, not a record-field requirement, and today has no corresponding record-side check at all (the gap #2039 is filed to close).

## Record-shape / record-fields enforcement surfaces

canonical: `find . -iname '*record-shape*' -o -iname '*record-fields*'` (run this session, output above) plus direct reads of gates/gates.py and on-the-record/hooks/record-claim-guard.sh

There is no file named `record-shape-gate.sh` or `record-fields-gate.sh` in this repo's live `on-the-record/hooks/` or `gates/` trees — that filename only exists under `docs/issue-167|170/_assets/rulebook-skeleton/**`, a skill-repository template snapshot, not this repo's own enforcement code. The live enforcement is split across two layers that mirror each other by design (`gates/record_lint.py`'s own module docstring, gates/record_lint.py:1-18, names this pattern explicitly):

1. **`gates/gates.py`** — CI/PR-diff-scoped checks, each `(work: Path, cfg: dict) -> list[str]`, called against `changed_files()` under `docs/issue-<n>/reports/<role>.md` (path matched by `RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")`, gates.py:289):
   - `record_frontmatter(text)` (gates.py:292-306) — the shallow `---`-delimited parser every other check builds on.
   - `record_enums(d, cfg)` (gates.py:309-356) — for each changed record, loads `roles/<role>.json`, and for every frontmatter field the role declares under `record_fields`, checks the record's value is in the declared enum. Unlisted fields are not checked (free text).
   - `record_wellformed_in(work)` / `record_wellformed(d, cfg)` (gates.py:407-436) — parseable `---` frontmatter, open+close delimiters present.
   - `record_refusal_reasoned(d, cfg)` (gates.py:362-398) — if `loop_state` is a refusal-family value (`refused`/`not-needed`/`cannot-verify`), requires a non-empty `reason:` field. This is the closest existing precedent for an "N declared X → N present-and-reasoned Y" shape check: it keys off `roles/<role>.json` for the declared shape, then scans the changed record body for compliance — but it never reads anything outside the record file itself. `roles/implementation.json` (canonical: full file read above) carries `record_fields` declaring only `loop_state`'s enum — no field there could express "how many skills were mounted for this particular spawn," because that count is a per-spawn fact, not a per-role constant.

2. **`on-the-record/hooks/*.sh`** — session-side PreToolUse/Stop hooks that approximate a `gates.py` check at write time, inside the spawned session, before the CI-side gate ever runs. `record-claim-guard.sh` (canonical: on-the-record/hooks/record-claim-guard.sh:1-40, full header read above) is the existing template for "write-time mirror of a `gates/record_lint.py`/`gates.py` check" — it receives one `Write|Edit|MultiEdit` tool call's resulting content via stdin JSON and cannot see anything beyond what that one tool call carries.

## How a hook could learn "N mounted skills" for the current session

The blocker: `gates.py`'s CI-side checks only ever see the changed record file plus `roles/<role>.json` (canonical: gates.py:309-398, full functions read above) — no channel carries the per-spawn mounted-skill list to them. But `on-the-record/hooks/deviation-log-guard.sh` (canonical: full file read above) establishes the pattern this issue needs on the session-hook side: a Stop hook can read `transcript_path` off the raw hook-event JSON (`e.get("transcript_path")`, deviation-log-guard.sh:59) and scan the JSONL transcript for the first-user-message text — which is exactly where spawn.py's `마운트된 스킬(...)`/`이 역할은 skill-repository(...)로 매핑됐다` lines land (spawn.py line 8151 and spawn.py line 8179, cited above). `product-capture-stopgate.sh` uses the same transcript-scan mechanism (referenced at deviation-log-guard.sh:18, transcript_path read near product-capture-stopgate.sh line 69 per that reference comment).

This means: a session-side hook (Stop, mirroring deviation-log-guard.sh's shape) can parse N skill names out of the transcript's mounted-skill line(s) and cross-check the record diff for N `skill-verdict: <name> — ...` lines. This is necessarily a session-side mechanism — the mounted-skill list only exists in that session's own transcript. A pure CI-side `gates.py` function scanning a merged PR has no transcript to read and cannot reconstruct N independently unless the mounted-skill list is also persisted into something the target repo's working tree carries (e.g., committed into the record's own frontmatter or a sibling manifest at write time) — which is itself an open design choice the phase-1 proposal has to resolve explicitly, not something the current codebase already decides.

## Existing dual-layer precedent (session hook + CI gate mirroring each other)

`record-claim-guard.sh`'s own header (canonical: on-the-record/hooks/record-claim-guard.sh:1-9) states the intended relationship: `gates.py` runs the canonical check as a CI diff-scan; the hook is "a write-time approximation of the same intent, not a byte-identical port." `gates/record_lint.py`'s module docstring (canonical: gates/record_lint.py:1-18) describes the same split for `record-claim-guard.sh`'s four ported checks, unified so "each rule's logic lives in exactly one place" (the `gates.py`/`record_lint.py` functions; the shell hook calls back into them via `python3 -m gates.record_lint`). A #2039 implementation should follow this same shape: one canonical check function under `gates/`, plus a session-side hook that approximates it early using the transcript-scan technique above.

## Test conventions

canonical: `ls on-the-record/hooks/` and `ls gates/` directory listings read above (record-tiering-directive.sh paired with test_record_tiering_directive.py in the same listing; record_lint.py paired with test_record_lint.py)

Existing hook tests pair 1:1 with each `.sh` hook under `on-the-record/hooks/` (e.g. `record-tiering-directive.sh` alongside `test_record_tiering_directive.py`), and gate-function tests live under `gates/test_*.py` (`gates/test_record_lint.py` covering `gates/record_lint.py`). A new hook and a new `gates.py`/`record_lint.py` check function for #2039 would follow that same pairing convention — exact filenames are a phase-2 implementation detail, not fixed by this survey.

## Skip-condition check (scout-directive)

This is an internal enforcement-mechanism change to this repo's own record-contract gates, not a product/UX-facing deliverable and not comparable to any external best-in-class product category — there is no external field to scout. Skip condition used: "the spec leaves no design decision open" does NOT apply (the transcript-scan-vs-persisted-manifest choice above is a real open design decision the proposal must resolve). Scouting is skipped instead because this is pure internal-infrastructure/gate-mechanism work with no external product category to compare against; the relevant prior art is this repo's own existing dual-layer hook/gate pattern, already covered directly above.
