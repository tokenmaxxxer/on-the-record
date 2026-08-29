---
issue: 2729
role: technical-writing-style-guide-compliance+adversarial-review-93eb1d9c
author: technical-writing-style-guide-compliance+adversarial-review-93eb1d9c
skills: technical-writing-style-guide-compliance (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/merge-allow-gate.sh
    sha: same-commit
  - path: docs/issue-2719/reports/adversarial-review-36975768.md
    sha: cd7bbbbc4bac141f51f3f174da71bb442af24574
  - path: docs/issue-2719/reports/adversarial-review-5d983b72.md
    sha: cbb8a86faa7a0004d0c85ee8fa6ab8a34bd126b3
  - path: docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md
    sha: 01ffdde1d801a2cfc1241eb7168f252bfb14b137
  - path: on-the-record/hooks/quality-bar-gate.sh
    sha: e1f390ab6c01018ce805b00114232adfe86ab749
---

# issue-2729 — technical-writing-style-guide-compliance+adversarial-review-93eb1d9c record

## What was done

Fixed the "byte-identical" citation issue #2729 names.

### The claim, located

canonical: `git show e1f390ab:on-the-record/hooks/merge-allow-gate.sh`
lines 230-239 (the comment as committed at the start of this session)
and `docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
lines 151-158 (sha `01ffdde1`), both read directly this session.

```
#     `_TRIGGER_PATH_PATTERNS["secure-coding"]` is byte-identical to the
#     list removed here) lacking a `quality_bar_verdict: bar-met` line,
```
The `.sh` comment asserts "byte-identical" with no command cited. The
separate PR #2721 record names the command and claims its output is
"(no output — identical)":
```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)
(no output — identical)
```

### BEFORE: the cited command, run

derived: command below, run this session, verbatim as cited in
`docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
lines 155-157.
```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)
1,3c1,3
<         "secure-coding": ["**/auth/**", "**/*credential*", "**/*permission*",
<                            "**/*secret*", "**/*password*", "**/*login*",
<                            "**/*input*", "**/*sanitiz*", "**/*validat*"],
---
>     "secure-coding": ["**/auth/**", "**/*credential*", "**/*permission*",
>                        "**/*secret*", "**/*password*", "**/*login*",
>                        "**/*input*", "**/*sanitiz*", "**/*validat*"],
```
derived: the command above, run this session, does not produce "(no
output — identical)" as the cited sentence claims — it produces the
6-line diff shown, matching what both independent verifications
already reported — canonical:
`docs/issue-2719/reports/adversarial-review-36975768.md` lines 214-221
and `docs/issue-2719/reports/adversarial-review-5d983b72.md` lines
115-125, both read directly this session.

`docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
is PR #2721's own record, on a different role's branch — canonical: `gh
pr view 2721 --json state,mergedAt` → `{"state":"MERGED","mergedAt":
"2026-08-29T12:53:05Z"}`, run this session. Attempting to edit it from
this branch was refused — canonical: PreToolUse Edit hook error this
session, `board-gate: writing docs/issue-2719/ requires branch
issue-2719/technical-writing-style-guide-compliance+adversarial-review-93eb1d9c
(current: issue-2729/...), and issue #2729's body declares no matching
'maintenance-targets:' entry for issue-2719`. So the fix below lands in
`on-the-record/hooks/merge-allow-gate.sh` instead — the file issue
#2729's own Ask names, and the copy every future reader of this hook
actually encounters.

### AFTER: the fix and its reproducing commands

canonical: `on-the-record/hooks/merge-allow-gate.sh` current lines
230-248 (this commit), replacing the unqualified "byte-identical"
assertion with "same values, not the same bytes" plus the two commands
below.

```
$ diff <(git show d329e9b9^:on-the-record/hooks/merge-allow-gate.sh | sed -n '261,263p' | sed 's/^[[:space:]]*//') \
       <(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh | sed 's/^[[:space:]]*//')
(no output — identical once whitespace-normalized)
```
derived: command above, run this session — no output, agreeing with the
sentence it supports (acceptance bullet 1, after state).

The value-equality comparison (acceptance bullet 2), run and shown:
```
$ python3 -c "
import ast, subprocess
def lst(ref, path, a, b):
    if ref:
        text = subprocess.run(['git','show',f'{ref}:{path}'],capture_output=True,text=True,check=True).stdout
        lines = text.splitlines(keepends=True)
    else:
        lines = open(path).readlines()
    snippet = ''.join(lines[a-1:b]).strip().rstrip(',')
    return ast.literal_eval('[' + snippet.split('[',1)[1])
removed = lst('d329e9b9^', 'on-the-record/hooks/merge-allow-gate.sh', 261, 263)
kept = lst(None, 'on-the-record/hooks/quality-bar-gate.sh', 240, 242)
print('removed == kept:', removed == kept)
"
removed == kept: True
```
derived: command above, run this session — `True`. The engineering
conclusion the original claim supported (removing the `secure-coding`
half of the routing-fix is not a net capability loss, because
`quality-bar-gate.sh` already denies the same merges on the same pattern
values) is unchanged and stays stated in the comment — canonical:
`on-the-record/hooks/merge-allow-gate.sh` lines 230-248, current text,
read directly.

### Independent review of the fix

canonical: this session's Agent-tool call, subagent
`a79ee359e2b78027d`, output returned this session (full text available
in this session's transcript).

Per the adversarial-review skill's Step 2, a fresh Agent-tool subagent
with no access to this session's context reviewed the first draft of
the `.sh` comment fix, given only the unified diff and told to find
problems. It returned two real findings: (a) the draft cited this record
as containing "commands run and shown" before the record existed —
hollow at that point; (b) the draft comment claimed to correct an
earlier "byte-identical .. no output" citation "here" (in the `.sh`
file), but the prior `.sh` text (quoted under "The claim, located"
above) never said "no output" — that phrase existed only in the
separate PR #2721 record, not in this file. Both are fixed in the
current text: this record now exists with the commands actually run
(sections above), and the comment's wording (current text, canonical
above) says only "replacing this comment's prior unqualified
'byte-identical' assertion, which cited no command" — true of the text
quoted under "The claim, located." A third, style-only finding (a bare
`--` where the file's surrounding prose uses an em dash) was also fixed
in the current `.sh` text.

## Why

The must-not in issue #2729 rules out two easy wrong fixes: deleting the
claim, which would leave the `secure-coding` capability removal
unjustified, and weakening it to an assertion with no command, which
reproduces the exact problem the issue reports. The fix keeps the
asymmetric-loss reasoning legible while making the cited command
actually reproduce what the prose says.

The raw diff isn't empty because the removed `merge-allow-gate.sh` copy
of the list was nested one function-level deeper (inside
`_routing_fix_should_withhold`) than `quality-bar-gate.sh`'s
module-level `_TRIGGER_PATH_PATTERNS` dict — canonical: the BEFORE diff
output above, every differing line pair off by exactly 4 leading spaces.
Stripping that whitespace, or parsing both sides as Python list
literals, isolates the glob values and shows they match — both shown
under "AFTER" above.

- skill-verdict: technical-writing-style-guide-compliance — applied: invoked;
  reviewed the added `.sh` comment prose and this record's
  prose for active voice with named actors, list-vs-run-on structure,
  and passive constructs needing a named actor rewrite. The comment is
  internal code documentation, not reader-facing instructional text, so
  the imperative-mood/second-person/"please" rules don't govern it — it
  describes what the code does rather than instructing a reader through
  steps. The new `.sh` text uses active voice throughout — canonical:
  `on-the-record/hooks/merge-allow-gate.sh` lines 230-248, current
  text, e.g. "quality-bar-gate.sh independently DENIES...", "A
  whitespace-normalized diff and a parsed-list equality check both
  confirm...". No unglossed new jargon or word-list violations found.
- skill-verdict: adversarial-review — applied: invoked; spawned an
  independent Agent-tool subagent (fresh context, diff only, no spec or
  intent) per the protocol — canonical: this session's Agent tool call
  and its returned output, described under "Independent review of the
  fix" above. It returned two real, correctly located findings and one
  style nit; all three fixed before landing.

## What did not work

The first draft of the `.sh` comment fix cited this record as already
containing "commands run and shown" and claimed to correct a "no
output" citation that had never existed in this file — canonical: the
independent evaluator subagent's findings, quoted under "Independent
review of the fix" above. Caught by that subagent; fixed by writing this
record with the commands actually run and correcting the comment's
wording to describe only what the prior `.sh` text actually said (quoted
under "The claim, located" above). No deviation from the approved
scope — a defect in the first draft, corrected before landing.

## Upstream basis

- `on-the-record/hooks/merge-allow-gate.sh` — same-commit; the file
  edited by this fix.
- `docs/issue-2719/reports/adversarial-review-36975768.md` (sha
  `cd7bbbbc4bac141f51f3f174da71bb442af24574`) — canonical: its lines
  210-235 ("One reproducibility defect found"), read directly this
  session; matches the BEFORE section above. One of the two independent
  verifications that found this defect.
- `docs/issue-2719/reports/adversarial-review-5d983b72.md` (sha
  `cbb8a86faa7a0004d0c85ee8fa6ab8a34bd126b3`) — canonical: its lines
  118-125 and 256-266, read directly this session; matches the BEFORE
  section above. The second independent verification naming the same
  defect.
- `docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
  (sha `01ffdde1d801a2cfc1241eb7168f252bfb14b137`) — canonical: its
  lines 149-158, read directly this session; matches "The claim,
  located" above. PR #2721's own record; not editable from this branch
  (board-gate; see "Open findings").
- `on-the-record/hooks/quality-bar-gate.sh` (sha
  `e1f390ab6c01018ce805b00114232adfe86ab749`) — canonical: its lines
  232-242, read directly this session; confirms the `secure-coding`
  entry's current line range used in the cited commands above.
- `gh issue view 2729` (read live this session, canonical) — the issue
  body, Ask/Acceptance/Non-goals sections quoted and satisfied above.

## Open findings

1. `docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
   lines 151-158 still carry the original unreproducing "(no output —
   identical)" citation verbatim — canonical: PR #2721 state MERGED and
   this branch's board-gate refusal, both quoted under "BEFORE" above.
   Resolution path: none needed for this issue's acceptance — issue
   #2729's own Ask names `on-the-record/hooks/merge-allow-gate.sh`'s
   comment as the fix target (fixed above), and both citing
   verifications already logged the discrepancy in their own records. A
   future session on a branch the board-gate recognizes for
   `docs/issue-2719/` could apply the same correction there.

## Next steps

None — landed. `on-the-record/hooks/merge-allow-gate.sh`'s comment now
carries a "same values, not the same bytes" claim backed by two commands
that reproduce, both shown above next to the sentences they support.
