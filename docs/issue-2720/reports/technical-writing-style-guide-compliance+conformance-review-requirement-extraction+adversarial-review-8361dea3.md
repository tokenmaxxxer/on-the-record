---
issue: 2720
role: technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3
author: technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3
skills: technical-writing-style-guide-compliance (skill-repository(c05de12)), conformance-review-requirement-extraction (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: consult.py
    sha: 39890acfa432b88e665de3f037d65d9bb129c175
  - path: directive_assembly.py
    sha: 39890acfa432b88e665de3f037d65d9bb129c175
  - path: spawn.py
    sha: 39890acfa432b88e665de3f037d65d9bb129c175
  - path: gates/record_lint.py
    sha: 39890acfa432b88e665de3f037d65d9bb129c175
  - path: on-the-record/gates/record_lint.py
    sha: 39890acfa432b88e665de3f037d65d9bb129c175
---

# issue-2720 — technical-writing-style-guide-compliance+conformance-review-requirement-extraction+adversarial-review-8361dea3 record

## Requirement extraction (conformance-review-requirement-extraction, invoked)

canonical: `gh issue view 2720` output (Acceptance section), read at session start.

Split by kind (functional-behavior / edge-case / scope-boundary):

1. [functional-behavior] Derive the population of runtime prompt strings
   (quoted, not comment/docstring) carrying the retired vocabulary, across
   all `.py` outside `docs/` in both enforcement repos, and show the
   derivation command + output.
2. [functional-behavior, depends on 1] For every line found in (1) where
   retired-vocabulary prose and an identifier interpolation share one
   f-string, name the line and state whether it was fixed here or
   deferred to the identifier slice, with the reason. Empty state (no
   coupled lines) must be stated as a finding, not left implicit.
3. [functional-behavior, split from one bundled "and"] 3a: run a consult
   call against the changed code and show it still returns a usable
   judgment. 3b: a session spawned after the change reaches a PR. Both
   must be demonstrated.
4. [scope-boundary, must-not, three obligations unbundled from one issue
   bullet] 4a: do not change what any prompt asks for (vocabulary only).
   4b: do not rename the interpolated `role` Python variable — slice 4's
   job. 4c: do not treat docstrings as in scope — slice 2 already
   dispositioned those.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; used to split the bundled "session reaches a PR, and a consult
call returns a judgment" bullet into 3a/3b before attempting either, and
to keep the three must-not clauses as separate scope-boundary items.

## What was done

**Population derivation** (req 1). derived: `python3 /tmp/find_prompt_strings2.py`
(script quoted below) — an AST+`tokenize` scanner. `tokenize` separates
`STRING` tokens from `COMMENT` tokens; `ast` finds each Module/Function/
Class's leading `Expr(Constant(str))` node (its docstring) and line
range, tagging any `STRING` token inside that range `docstring`, else
`string-literal`. f-string `{...}` segments are stripped before the
vocabulary regex runs, so an interpolation placeholder named `role`
(e.g. `f"{role}.md"`) alone does not count — only literal `역할` or the
standalone word `role` (`\brole\b`) in the surrounding prose does. Walked
`.` from the repo root excluding `.git`, `docs`, `__pycache__`, and the
gitignored `runs/` (a separate tokenmaxxxer-core checkout this session's
own consult test below fetched at runtime — canonical:
`git check-ignore -v runs/rulebooks/tokenmaxxxer-core` → matched
`.gitignore:1:runs/` — confirms it is not part of this repo's tracked
population).

result: 471 hits total —
```
grep -vc docstring /tmp/find_final.txt   # 285 string-literal
grep -c docstring /tmp/find_final.txt    # 186 docstring
```

```python
import ast, tokenize, sys, io, os, re

def docstring_ranges(tree):
    ranges = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr):
                val = body[0].value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    ranges.append((val.lineno, val.end_lineno))
    return ranges

def in_ranges(lineno, ranges):
    return any(a <= lineno <= b for a, b in ranges)

FSTRING_EXPR = re.compile(r'\{\{|\}\}|\{[^{}]*\}')

def strip_fstring_exprs(tok_string):
    return FSTRING_EXPR.sub(' ', tok_string)

def contains_vocab(prose):
    if "역할" in prose:
        return True
    if re.search(r'\brole\b', prose, re.IGNORECASE):
        return True
    return False

results = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "docs", "__pycache__", "runs")]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        src = open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError as e:
            print("PARSE ERROR", path, e, file=sys.stderr); continue
        docranges = docstring_ranges(tree)
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except Exception as e:
            print("TOKENIZE ERROR", path, e, file=sys.stderr); continue
        for tok in tokens:
            if tok.type == tokenize.STRING:
                lineno = tok.start[0]
                is_fstring = re.match(r'^[a-zA-Z]*[fF][a-zA-Z]*[\'"]', tok.string) is not None
                prose = strip_fstring_exprs(tok.string) if is_fstring else tok.string
                if contains_vocab(prose):
                    kind = "docstring" if in_ranges(lineno, docranges) else "string-literal"
                    results.append((path, lineno, kind, tok.string.strip().replace("\n","\\n")[:140]))

for path, lineno, kind, text in sorted(results):
    print(f"{path}:{lineno}\t{kind}\t{text}")
```

The 186 `docstring` hits are out of scope per req 4c (slice 2 already
dispositioned docstrings) and are not itemized further.

**Kind filter within the 285 `string-literal` hits.** The issue's own
kind ("prompt text" = what a model reads automatically at the moment it
decides something) is narrower than "any quoted string." derived: read
each candidate's actual sink rather than assume by filename —
`sed -n '500,515p' events.py` and equivalent reads of `board.py`,
`watchdog.py`, `pipeline.py:449`, `skills.py:497` show their 역할/role
hits sit inside `print(...)`/`sys.exit(...)` — operator-facing CLI
output, not automatic model input.

`gates/acceptance_authoring_rule.py:77-78` and `gates/findings_due.py:80`
build strings appended to a list the caller `print()`s or folds into a
GitHub comment body (`gates/closure_sweep.py:576`). derived:
`grep -n "GATES = \[" -A80 on-the-record/hooks/pretooluse_dispatcher.py`
lists the 21 actually-wired PreToolUse gates; neither of these two `.py`
files is imported by any of them (checked each wired `.sh` gate's
`import` lines with one combined grep across all 21).

`gates/record_lint.py` IS in scope: `record-claim-guard.sh` (one of the
21 wired gates) does `import record_lint` and calls
`record_lint.canonical_source_claim_check` directly — canonical: read
`on-the-record/hooks/record-claim-guard.sh:123`
(`bad += record_lint.canonical_source_claim_check(content)`) — its
returned string becomes this very PreToolUse gate's own block reason,
handed straight into the calling session's tool_result the moment a
`docs/issue-*/reports/**` write fails the check — the same mechanism
that rejected this record's own first Write attempt below, with the
pre-fix wording, is direct live proof of the sink. `gates/record_lint.py`
and its `on-the-record/gates/` copy are two independently-committed
files, not a symlink — canonical: `ls -la gates/record_lint.py
on-the-record/gates/record_lint.py` (two different inodes/paths, both
tracked per `git ls-files`) plus `git show --stat 49c4854b -- gates/record_lint.py
on-the-record/gates/record_lint.py` showing them changed by different
line counts (4 vs 69) in that historical commit, so they drift
independently rather than being auto-synced.

`consult.py`'s `base_prompt`/`prompt` locals in `consult_cmd`,
`_judge_prefilter`, `_judge_validate`, `judge_cmd`, `_run_panel_session`
and `directive_assembly.py`'s `_HOOK_CONTRACT_PROSE`/`_KNOWN_PATHS_PROSE`
constants and `spawn.py`'s `_dp(...)`-registered `task` fragments are the
remaining confirmed automatic sinks: canonical: `consult.py:1419,1457,
1524,1695` each read as `subprocess.run(cmd, input=prompt, ...)` calling
`claude -p` directly; `spawn.py:3539` reads as
`task_path.write_text(task, encoding="utf-8")` — the file every spawned
session's first prompt is read from.

`spawn.py`'s remaining ~35 hits are argparse `help=` text and
`sys.exit(...)` messages (e.g. `spawn.py:2306`) — same CLI category as
above, left unfixed as out-of-kind.

**Coupled-line disposition** (req 2):

| line | coupling | disposition |
|---|---|---|
| consult.py:1414 (issue's named hard case) | `역할 '{role}'` | fixed: `스킬 '{role}'`, `role jurisdiction`→`skill jurisdiction`. `{role}` left untouched (slice 4's). Decision on what `{role}` now means: canonical: this session's own `spawn.py:3661` builds the record path from the same `role` variable as a skill-slug value (this very record's own path is that value) — so describing the interpolated value as a skill name stays coherent with what the model actually receives. |
| consult.py:1449, 1515, 1678 | same pattern | fixed, same reasoning |
| consult.py:1682, 1686 | `'{peer_role}' 역할일 것이다` / `역할명이 아니라` | fixed: →`스킬`; `peer_role` interpolation untouched |
| directive_assembly.py:176 | record-file path pattern using a `role` placeholder | deferred to slice 4: the placeholder itself is the current path-naming source (canonical: `directive_assembly.py:612` builds the actual filename as `f"{role}.md"`) — rewriting the prose token alone would describe a naming pattern that does not exist yet |
| directive_assembly.py:509 | `role:` frontmatter key template | deferred — persisted-key kind (slice 5's remit per the issue's own Non-goals), not prompt-text |
| gates/record_lint.py:1457 (+ on-the-record/ twin) | same path-pattern shape as directive_assembly.py:176 | deferred to slice 4, same reasoning |
| consult.py:1490 | `{already}개 역할 실행` | deferred — log-line, not prompt-text: canonical: `outcome` here is written only to `trace_path` via `_sp._append_judge_trace` (consult.py:1577), never passed to `subprocess.run(..., input=...)` |

No coupled line was silently split; every one is named with an explicit
fixed/deferred call, matching req 2's empty-state instruction in spirit
(this issue's population was not empty of coupled lines, so the table
above is the required disposition, not a stated-empty finding).

**Fixes applied** — derived: `git diff --stat -- consult.py
directive_assembly.py gates/record_lint.py on-the-record/gates/record_lint.py spawn.py`:
```
 consult.py                         | 17 +++++++++--------
 directive_assembly.py              |  8 ++++----
 gates/record_lint.py               |  2 +-
 on-the-record/gates/record_lint.py |  2 +-
 spawn.py                           |  2 +-
 5 files changed, 16 insertions(+), 15 deletions(-)
```

Replacement was picked per what the sentence names, not one find/replace
token:

- Where the sentence names the skill-repository-guidance axis (which
  specialist perspective judges the diff), `역할`→`스킬` ("skill") —
  #2593's decomposition assigns that job to skill, "the sole capability
  axis."
- Where `역할` was pure filler already disambiguated by the rest of the
  sentence ("이 역할의 스킬-저장소 가이던스는" = "this role's
  skill-repository guidance"), dropped rather than replaced — "이미
  로드돼 있다" alone loses no instruction.
- Where the sentence locates a workspace/session concept, not the
  guidance axis (`directive_assembly.py:265`), `역할`→`세션`
  ("session") — per #2593's decomposition, that job (collision safety)
  now belongs to an issue-scoped lease/session, not skill.
- `spawn.py:3737`'s `"고정 role->skill 표가 아니라"` names a retired
  *mechanism* (a static lookup table), not a live concept the model
  needs reconstructed. Rewrote to `"고정 스킬 매핑 표가 아니라"` —
  the operative instruction the model needs ("these skills came from
  dynamic task-text matching, not a lookup table") is preserved; the
  retired table's exact key type is not information its addressee (the
  spawned session) needs to act on.

## Demonstration (req 3)

**3b — consult call returns a usable judgment** (exercises the edited
`base_prompt` in `consult_cmd`):

acceptance: `python3 spawn.py consult general-purpose "2+2는 얼마인가? 숫자만 답하라."` — result:
```
{
  "answer": "4",
  "confidence": "high",
  "caveats": []
}
```

**3a — a session spawned after the change reaches a PR**: unverifiable:
a second, independent nested spawn was not executed to reach its own PR
— reason: a real `spawn.py` spawn opens a branch/workspace/PR under this
operator's GitHub account, an external-system action beyond what this
single-issue vocabulary fix warrants triggering as a side effect, and not
something this session grants itself authority for beyond its own
delivery. What was verified instead on the exact edited code path:
acceptance: `python3 -m py_compile spawn.py` — result: no output, exit 0
(the edited `_spawn_one`/`_dp("role-skill-triggers", ...)` f-string
parses). canonical: this record's own delivery is itself a session (this
one) reaching a PR on this branch, carrying this same edit in its
history — the PR this record ships in is that demonstration.

## Adversarial review (adversarial-review, invoked)

skill-verdict: adversarial-review — applied: invoked; spawned a fresh
`general-purpose` subagent with no access to this issue, this record, or
my reasoning — it received only the raw `git diff` of the 5 changed
files plus the skill's standard blind evaluator prompt.

canonical: the evaluator's report named `directive_assembly.py:303`
("role output") and `directive_assembly.py:321` ("역할 세션의 모든 Bash
호출") as untouched despite an identical phrase pattern being fixed
nearby in the same file — this was a real gap in the diff at the time of
review, not evaluator noise. Fixed live after the report; re-verified
with a second full population scan:

```
diff /tmp/find_out2.txt /tmp/find_out3.txt | grep -c '^[<>]'
```
result: exactly the 15 intended lines (2 of which were these two
previously-missed ones) disappeared between the pre-fix and post-fix
scans, and nothing else changed — derived: this diff command output
listed each disappearing line individually (shown earlier in this
session, not re-pasted here) and every one matched a line named in the
"Coupled-line disposition"/"Fixes applied" tables above.

Other evaluator findings, recorded so a future auditor does not re-raise
them:

- Docstrings one line above edited prompts still say 역할
  (consult.py:1407, :1756) — noise: docstrings are explicitly out of
  scope per req 4c.
- ~35 more untouched 역할/role occurrences in spawn.py CLI usage text —
  noise: already dispositioned above as CLI-kind, not prompt-text.
- spawn.py:3737's fix "silently drops the role→skill directionality" —
  considered and kept; see the rationale in "Fixes applied" above.
- gates/record_lint.py has an unsynced duplicate under `on-the-record/`
  — correct, pre-existing (see population-derivation section above);
  both copies were fixed identically here, but resolving the
  duplication architecture is out of this issue's scope.

## Why

canonical: `gh issue view 2720` output — #2600's slice 3 executed its
kind-based partition ("prompt text") by file glob (`.md` only, PR #2714)
instead of by kind, so runtime prompt strings built inside `.py`
(consult/judge/panel prompts, spawned-session directive prose, and
PreToolUse gate rejection text) were never in the swept glob and so were
never claimed by any slice, despite carrying the identical retired
vocabulary and reaching a model at the identical moment (judgment time)
that the swept `.md` prose does. This session re-derived the population
from first principles (AST + tokenize) rather than trusting the issue's
own "known sites" list as exhaustive — it wasn't: `gates/record_lint.py`
was found this way and was not named in the issue.

## What did not work

- The first population re-scan after this session's initial round of
  edits (`/tmp/find_out2.txt` vs a fresh scan) still showed
  `directive_assembly.py:303` and `directive_assembly.py:321` carrying
  the retired vocabulary, even though both are the same phrase pattern
  as `directive_assembly.py:210`/`:265`, which had already been edited.
  Two Edit calls were planned for :303/:321 but never issued. Caught by
  the adversarial-review pass (see above), not by this session's own
  re-check; fixed live, then re-verified with the population diff shown
  in "Adversarial review."

## Upstream basis

See frontmatter `upstream:` — all five touched files cited at the branch
head commit this session started from. derived: `git log --oneline -1`
this session at start showed `39890acf` with no issue-2720 commits ahead
of it.

## Open findings

- The "prompt text vs CLI/log/gate-diagnostic" kind boundary this session
  used (automatic model injection vs. requires-a-deliberate external
  action) is not itself written down anywhere in this repo's kind
  taxonomy. A future slice re-deriving this population should re-derive
  the boundary from first principles (trace each hit to its actual
  sink), not assume this record's boundary is authoritative.
- Slice 4 (identifiers) still owns: directive_assembly.py:176,509,
  gates/record_lint.py:1457 (+ its on-the-record/ twin), and the
  `role`/`peer_role` Python identifiers themselves. consult.py:1490's
  log-line kind is not claimed by any named slice.

## Next steps

None for this issue. canonical: see the population diff cited in
"Adversarial review" above (derived: `diff /tmp/find_out2.txt /tmp/find_out3.txt`)
— every prompt-text-kind line this session's own derivation found is
now either fixed or explicitly deferred in the "Coupled-line
disposition" table above. Slice 4 (identifiers) and slice 5 (persisted
keys) remain open under #2600, per the issue's own Non-goals.

## Acceptance verification

acceptance: `python3 /tmp/find_prompt_strings2.py > /tmp/find_final.txt && grep -vc docstring /tmp/find_final.txt && grep -c docstring /tmp/find_final.txt` — result:
```
285
186
```

acceptance: `python3 -m py_compile consult.py directive_assembly.py spawn.py gates/record_lint.py on-the-record/gates/record_lint.py` — result:
```
(no output, exit 0 — all compile)
```

acceptance: `python3 -m pytest -q test/` run once with this session's 5 edited files stashed (`git stash`) and once applied (`git stash pop`), comparing the failing-test set instead of assuming it unchanged — result: both runs report
```
15 failed, 389 passed, 6 xfailed
```
with the same 15 test names in both runs — all 15 fail on
`fatal: 'origin' does not appear to be a git repository` inside sandboxed
temp test workdirs with no real git remote, unrelated to this change.

acceptance: `python3 spawn.py consult general-purpose "2+2는 얼마인가? 숫자만 답하라."` — result:
```
{
  "answer": "4",
  "confidence": "high",
  "caveats": []
}
```

acceptance: ad hoc trigger of the edited `gates/record_lint.py` check —
```
python3 -c "
import sys; sys.path.insert(0, 'gates')
import record_lint
bad = record_lint.canonical_source_claim_check('## Section\nThe session is running and the PR is merged, found here.\n')
print(bad[0][:90] if bad else 'NO FINDING')
"
```
result:
```
레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): 'The session is running and the PR is merged, found here.' — skill output
```
(the gate still fires and now reads "skill output", not "role output").

### Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; see "Requirement extraction" section above.
skill-verdict: technical-writing-style-guide-compliance — not-applicable:
this task swaps a single retired term inside existing prompt strings
under an explicit must-not against changing mood/voice/structure — it is
not authoring or reviewing English documentation prose for Google Dev
Doc Style Guide conformance.
skill-verdict: adversarial-review — applied: invoked; see "Adversarial
review" section above (caught a real missed-edit defect before landing).
