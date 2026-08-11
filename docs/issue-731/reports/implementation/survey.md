# Survey — issue #731

## Scope

Audit #726 rows 7 and 23 flag two on-the-record-own conventions that are
enforced only by a gate, with no proactive statement anywhere in
on-the-record's own commands/docs:

- **Row 7 (hard-shape)** — `on-the-record/hooks/call-shape-guard.sh`
  (`subprocess_call_shape_divergence` check, lines 153-165, port of
  issue #419's check): denies a write when call sites sharing the same
  `(argv[0], argv[1])` use different semantic flag sets (`-X`/`--method`/
  `-f`/`--field`).
- **Row 23 (advisory, decision:block)** —
  `on-the-record/hooks/report-framing-check.sh` (lines 66-69): a Stop
  hook that blocks a PR/board report reply missing one of the four
  issue-#320 framing elements (resolved problem / prior cost / newly
  possible / still broken).

## Where on-the-record's own commands/docs live

- `on-the-record/commands/run.md` — the orchestrator's main loop
  instructions; this is where reactive-gate mechanisms already get
  cross-referenced proactively (e.g. `## 같은 모양의 재발은 마킹하거나
  기계가 잡는다 (#419)` documents the sibling-marker half of #419's
  check, and the accumulation-cost section right after it).
- `on-the-record/commands/consult.md` — a narrower advisory command;
  grepped, no call-shape or report-framing material.
- `docs/handbooks/on-the-record.md` — operator-facing handbook, not a
  role-facing convention doc.

## Current state of the two conventions in commands/*.md

- Row 7: the `## 같은 모양의 재발은 마킹하거나 기계가 잡는다 (#419)`
  section in `on-the-record/commands/run.md` documents check 2
  (`sibling_mention_check`) proactively ("함수/클래스 정의 바로 위에
  `# sibling: ...` 주석을 붙이면 ...") but describes check 1
  (`subprocess_call_shape_divergence`) only as a gate behavior ("호출부들이
  flag 모양이 다르면 ... 잡는다") — what the gate catches, not a style
  rule stated as something to do ("동일한 (argv[0], argv[1]) 호출부는
  flag 모양을 통일해서 써라"). Confirmed via
  `grep -n "call-shape\|argv\[0\]\|flag consistency"
  on-the-record/commands/*.md` — only that one reactive mention.
- Row 23: no mention of "resolved problem / prior cost / newly possible
  / still broken" or issue #320's four-element framing anywhere under
  `on-the-record/commands/*.md`. Confirmed via
  `grep -n "report-framing\|resolved-problem\|prior-cost\|newly-possible\|
  still-broken" on-the-record/commands/*.md` — no hits. The framing
  requirement exists only inside `report-framing-check.sh`'s block-reason
  string, surfaced to a session only after it already wrote a
  non-compliant reply.

## Write set (projected)

- `on-the-record/commands/run.md` — add a proactive style-rule line to
  the existing `#419` section for row 7 (call-shape consistency), and a
  new short section for row 23 (report framing), placed near the other
  Stop-hook-adjacent material since report-framing-check is a Stop hook
  keyed to board/PR report replies.
- No code, no gate/hook changes — this issue's acceptance is a doc-only
  proactive statement; the existing gate/hook enforcement is unchanged.

## Skip-condition check (scout directive)

This is a small, single-file documentation addition restating an
already-fully-specified mechanical check (the gate's own logic is the
spec) in prose form. No product-shaped design decision is open — the
four framing elements and the flag-consistency rule are fixed by the
existing hook code, not chosen here. Per the scout directive's skip
condition (spec leaves no design decision open), scouting is skipped:
there is no external category or exemplar to compare a one-paragraph
internal style-rule addition against.
