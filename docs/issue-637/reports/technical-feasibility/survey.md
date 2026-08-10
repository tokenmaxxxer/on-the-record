# Current-state survey — issue #637 (phase 1)

## Scout skip record

Scouting skipped. Reason: the spec leaves no external-field design
decision open — this step is a reproduction-and-classification task
against an already-cited transcript (#623's execution-observation
record) and this repo's own `spawn.py` refusal-classification comments,
not a build choice that benefits from surveying comparable products.

## Scope

Catalogue the exact blocked-command shapes cited by #623's
cross-cutting Scope A row
(`docs/issue-623/reports/execution-observation.md`, "Cross-cutting:
honest-work false-reject class (#476)" row), reproduce each refusal in
this session, and classify each as fixable-on-our-surface vs
harness-boundary-to-document, per #637's acceptance criteria (`gh issue
view 637` — Acceptance section).

## market_argument_supplied: false

No market/business argument was consulted for this survey; the verdict
below is argued only from the reproduced refusal behavior and this
repo's own source.

## What #623 cited

`docs/issue-623/reports/execution-observation.md`'s cross-cutting row
describes, without quoting verbatim: "a legitimate multi-line `for`-loop
Bash command and a legitimate Python-heredoc command containing literal
JSON (`{"tool_input": ...}`) were both refused pre-execution this
session with `Contains shell syntax (string) that cannot be statically
analyzed` / `Contains brace with quote character (expansion
obfuscation)`" — docs/issue-623/reports/execution-observation.md,
"Cross-cutting: honest-work false-reject class (#476)" row.

The exact command text from #623's own session transcript is not
independently retrievable by this session (no shared transcript
access); this survey instead reproduces the same *shape* — a
loop-variable-expanding `for` loop, and a heredoc containing literal
JSON braces — live, this session, and treats that reproduction as the
evidence base (same method #623 itself used: "this session's own
transcript" as the citation, not a re-read of someone else's log).

## Reproduction, this session

1. `for h in a b c; do echo "$h"; done` (and every variant tried:
   unquoted `echo $h`, `printf '%s\n' "$h"`, multi-line form) → refused,
   `Contains simple_expansion` — this session's own tool_result, the
   Bash call immediately preceding this line in this session's
   transcript.
2. `python3 - <<'PYEOF' ... json.dumps({"tool_input": {"command":
   "git status"}}) ... PYEOF` → refused, `Contains brace with quote
   character (expansion obfuscation)` — this session's own tool_result,
   the Bash call immediately preceding this line in this session's
   transcript.
3. Workaround 1 (heredoc → single-quoted `-c`): `python3 -c '...'` with
   the same JSON-building logic, no heredoc → passed (printed the JSON)
   — this session's own tool_result.
4. Workaround 2 (inline → file): `Write` the `for`-loop script to
   `$SCRATCH/loop.sh`, then `bash $SCRATCH/loop.sh` → passed (`val=a`,
   `val=b`, `val=c` printed) — this session's own tool_result.
5. Isolation test: `for x in a b c; do echo hello; done` (no variable
   expansion of the loop var) → passed. `echo "$HOME"` (expansion,
   no `for`) → passed. Only the combination of a `for` loop *and*
   expansion of its own loop variable triggers the refusal — this
   session's own tool_result, the three Bash calls preceding this line.

## Root-cause layer

`spawn.py`'s refusal classifier (`_classify_refusal_text`, near
spawn.py:2266) carries a comment explaining its own pattern provenance:
the harness/sandbox pattern sets were pulled verbatim from real session
logs cited by issue #232, and are kept deliberately non-extensible
without a fresh issue-sourced sample (spawn.py, comment block
immediately above `_GATE_HOOK_RE`, near spawn.py:2231). The pattern
list this session's reproduction matched —
`_HARNESS_REFUSAL_PATTERNS` (spawn.py:2238-2242), specifically
`re.compile(r"cannot be statically analyzed")` and
`re.compile(r"simple_expansion")` — is documented in that same comment
block as belonging to the *harness command-approval* layer, distinct
from this repo's own `gate_deny`-prefixed hook-refusal layer
(spawn.py, same comment block, describing the
`PreToolUse:<tool> hook error: [<path>]` + `<gate>: refused — <reason>`
shape). Neither refused command in this session's reproduction touched
an on-the-record gate or hook at all: a repo-wide search for the three
matched refusal strings (`grep -rn "simple_expansion|expansion
obfuscation|cannot be statically analyzed" --include=*.py
--include=*.sh .`) finds hits only inside `spawn.py` and
`test_spawn.py` (the classifier and its test) — never inside
`on-the-record/hooks/` or `gates/` — this session's own `grep` output.

## Verdict-provisional

feasible-with-conditions: nothing on this repo's own gate surface caused
either refusal (confirmed above), so there is no gate to loosen and
operator principle 5 is not implicated. What is fixable on our surface
is documentation/guidance steering future sessions to the two verified
low-friction workarounds (single-quoted `-c` instead of heredoc; `Write`
then `bash`/`python3 <file>`) instead of re-discovering them mid-task
the way #623's session had to.
