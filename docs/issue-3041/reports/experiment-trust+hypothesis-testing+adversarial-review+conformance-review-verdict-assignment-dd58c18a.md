---
issue: 3041
role: experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-dd58c18a
author: experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-dd58c18a
skills: experiment-trust (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12))
verifies_subject: true  # second, independent verification of PR #3052's own deliverable
loop_state: landed
code_under_review: PR #3052, sha bb966ce64714cdf17d550b46e14d8e4af332baaa
type: verification
breaking: false
verdict: 4 of 5 acceptance criteria Present; criterion 1 (harness invocation)
  graded Incorrect on independent re-derivation — run_pair.sh is committed
  non-executable, so the issue's own literal check fails against PR #3052 as
  committed, a gap the first review pass did not catch. Finding A (marketplace
  corpus never mounted) independently reconfirmed from raw session logs, plus
  a corrected invocation identified and live-tested: no single
  --setting-sources value satisfies both constraints, but adding
  --plugin-dir alongside the existing --setting-sources project,local does.
  Finding B (empty target repo at the pin) reconfirmed; re-pinning to main
  does not fix it for backend/data-shaped tasks.
upstream:
  - path: docs/issue-3041/reports/conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769.md
    sha: same-commit
  - path: PR 3052, branch issue-3041/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600
    sha: bb966ce64714cdf17d550b46e14d8e4af332baaa
---

# issue-3041 — experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-dd58c18a record

## What was done

canonical: `docs/issue-3041/reports/conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769.md`
(this repo, already on `main` at session start), read this session — that
record's Part 1 grades all 5 acceptance criteria Present; its Part 2 states
`run_pair.sh` passes `--setting-sources project,local`, excluding the `user`
scope where marketplace plugins register, so all 4 skills-on arms ran with
`plugins: []` and only 17 built-in skills.

canonical: `gh issue view 3041`, run this session — this session's charge:
re-derive that claim from the retained session logs directly rather than
accept it (Section 1 below), determine whether the harness can be corrected
in place (Section 2), and re-examine the target-repo-emptiness confound
(Section 3). derived: this session's own re-derivation in Sections 1-4
below, each carrying its own live-run citations — the first pass's record
was read for context but its findings were re-derived independently, not
inherited.

### 1. Independent re-derivation of Finding A (marketplace never mounted)

canonical: `git fetch origin pull/3052/head:pr-3052 && git worktree add
--detach /tmp/pr3052-worktree pr-3052` (a local ref/worktree, both since
deleted this session), run this session, then `jq -c '{plugins, skills,
tools}'` against the first line of all 4
`docs/issue-3041/_assets/*/skills-on.session.jsonl` files (PR #3052 sha
bb966ce6, untracked on this review's own branch) — result: identical across
all 4: `"plugins":[]`, `"skills"` equal to exactly the 17 built-in Claude
Code skill names, no `hypothesis-testing`/`experiment-trust`/`decision-brief`/
`product-discovery-hypothesis-preregistration`/`user-discovery` (the
marketplace skills the 4 task texts were written to trigger), `"tools"`
includes `"Skill"`.

derived: `jq -c 'select(.type=="assistant") | .message.content[]? |
select(.type=="tool_use" and .name=="Skill")'` against the same 4 files, run
this session — 0 matches in every file, independently reconfirming
`instrument.py`'s reported `skill_opens: 0` from the raw transcript rather
than from the tool's own summary output.

derived: this session's own two independent live re-derivations above —
Finding A holds, re-derived from primary evidence this session, not accepted
from the first pass's report of it.

### 2. Can the harness be corrected in place? (new — first pass did not attempt this)

canonical: `scripts/issue-3041/run_pair.sh` (PR #3052 sha bb966ce6,
untracked on this review's own branch), read this session —
`TOOLS_ON="Read,Glob,Grep,Write,Edit,TodoWrite,Skill"`, both arms pass
`--setting-sources project,local`.

canonical:
`docs/issue-3041/reports/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600/deviation-log/20260902T015319345479-d15976688e1a95fe.md`
(PR #3052 sha bb966ce6, untracked on this review's own branch), read this
session — the flag was added after "a `claude -p` smoke test outside this
repo surfaced this repo's own operator hooks (Stop-hook text) leaking into
the subprocess via user-level settings," to stop those hooks "from leaking
into the target-repo clone too."

canonical: `/home/jwjung/.claude/settings.json` (this machine's own
user-scope settings file, not part of this repo), read this session —
`{"enabledPlugins":{"on-the-record@tokenmaxxxer":true},
"extraKnownMarketplaces":{"tokenmaxxxer":{...}}}`. The operator-hook plugin
is registered exactly at the `user` scope `--setting-sources project,local`
excludes — this is why the flag suppresses the leak, and also why it drops
every other user-scope registration along with it, including whichever
plugin would carry the target task skills.

derived: `claude --help`, run this session — `--setting-sources` accepts
only `user, project, local` (no finer grain within a scope); a separate
flag, `--plugin-dir <path>`, "Load[s] a plugin from a directory or .zip for
this session only" — explicitly session-scoped, independent of
`--setting-sources`.

derived: `printenv MUSTER_SKILL_REGISTRY_ROOT` (this machine's own
environment), run this session — `/home/jwjung/skill-registry/skills`;
`ls -la /home/jwjung/.claude/skills`, run this session, shows it as a
symlink resolving to the same path. All 5 skills the 4 task texts were
written to trigger (`hypothesis-testing`, `experiment-trust`,
`decision-brief`, `product-discovery-hypothesis-preregistration`,
`user-discovery`) exist under `/home/jwjung/skill-registry/skills/*/SKILL.md`
— this is where the intended "full skill corpus" actually lives on this
machine, separate from the `on-the-record@tokenmaxxxer` plugin that carries
the hooks.

canonical: a live `claude -p` smoke test run by this session this turn, in a
throwaway `/tmp` workspace (`--max-budget-usd 0.2`, actual reported cost
`total_cost_usd: 0.0248`):
```
claude -p "Reply with the single word OK and stop." --model sonnet \
  --permission-mode bypassPermissions \
  --setting-sources project,local \
  --plugin-dir /home/jwjung/skill-registry \
  --tools "Read" --output-format stream-json --verbose \
  --max-budget-usd 0.2
```
result, from the `init` event: `"plugins":[{"name":"skill-registry",
"path":"/home/jwjung/skill-registry","source":"skill-registry@inline"}]` —
not `on-the-record@tokenmaxxxer` — and `"skills"` includes
`skill-registry:hypothesis-testing`, `skill-registry:experiment-trust`,
`skill-registry:decision-brief`,
`skill-registry:product-discovery-hypothesis-preregistration`,
`skill-registry:user-discovery`, plus the rest of the skill-registry corpus
and the 17 built-ins. derived: `grep -io
"stop.hook|hook_event|system-reminder|operator|warrant|freelunch|proposal-shape|SessionStart"`
over the full transcript this session — zero real matches (one
false-positive-looking hit is the unrelated skill name
`skill-registry:finance-unit-economics-proposal-shape`, confirmed by reading
the surrounding text). No hook-leak signal fired.

derived: the live probe above — the harness can be corrected in place, and
no single `--setting-sources` value alone does it, because `user` is this
environment's only source carrying plugin/marketplace registration and it is
all-or-nothing. Concrete fix, not yet applied to PR #3052 per this session's
charge not to edit it: add `--plugin-dir "$HOME/skill-registry"` (or the
portable form, derived from `$MUSTER_SKILL_REGISTRY_ROOT`'s parent) to the
skills-on arm's invocation in `run_pair.sh`, alongside the existing
`--setting-sources project,local`. The skills-off arm needs no change:
derived: `claude --help`, run this session — `--disable-slash-commands` is
documented as "Disable all skills," unaffected by corpus presence.
`evaluate_pair.py` needs no change either, since it runs with `--tools ""`
(no `Skill` tool regardless of corpus) per
`scripts/issue-3041/evaluate_pair.py` (PR #3052 sha bb966ce6, untracked on
this review's own branch), read this session.

### 3. Second confound: target-repo emptiness at the pin (re-examined)

canonical: `git clone https://github.com/JiwonJung94/study-companion.git`
run live this session (a separate clone from the first pass's own) — `git
ls-files` at the pin `e102772480545a6be0af733f51020c97e7357ba7` returns the
same 3 scaffolding files the first pass reported (a consult-log entry, an
approvers spec, a requirement-digest spec).

derived: `git log --oneline e102772480545a6be0af733f51020c97e7357ba7..main`,
run this session, against that live study-companion clone (a separate
repository cloned to a scratch path this session, not part of this
repository) — 4 commits, all under a directory named `docs/issue-1/reports/`
inside that scratch clone only, untracked here, which this session read
directly there — a closed on-the-record work item on study-companion's own
issue #1 ("is the comprehension gap a real, underserved job-to-be-done"),
producing product-research markdown (evidence-tagged JTBD findings) but zero
application, backend, or data code. derived: `git ls-files` on that clone's
`main`, run this session — still no `src/`, no app files, no schema.

canonical: `scripts/issue-3041/tasks/*.txt` (PR #3052 sha bb966ce6,
untracked on this review's own branch), read this session — all 4 task
texts are self-contained synthetic stakeholder scenarios that invent their
own context inline ("adding a feature where students can be matched into
small study groups," "a redesigned first-run onboarding flow," "a new
spaced-repetition review scheduler," "a test comparing two paywall
designs"), consistent with the first pass's aside that the current 4
"mostly already are" self-contained. Task 03 (review-scheduler) is the
partial exception — its text says "this will span several files or
modules... before writing the code, write up how you'd structure it," which
nominally invites reading the existing codebase's conventions, and (per the
`git ls-files` results above) finds none at the pin or at `main`.

derived: the live clone and task-text reads above — re-pinning alone does
not fix Finding B. Study-companion's `main` has gained real content since
the pin, but it is product-research prose about one JTBD, not
application/backend/data code — the two disciplines in PR #3052's 4-pair set
that would most benefit from repo grounding (backend architecture,
data/experiment-trust analysis) still have nothing to read at any commit
that exists as of this session. A durable fix needs either (a) the target
repo gaining application/backend/data code before backend- or data-shaped
tasks run against it, or (b) task texts staying self-contained (as 3 of the
current 4 already are) and saying so explicitly, rather than leaving the
issue's "heterogeneous product work... real target repo" framing implicitly
unmet for 2 of the 4 disciplines.

### 4. Verdict per acceptance criterion (conformance-review-verdict-assignment)

canonical: `gh issue view 3041`, run this session — the five literal `check:`
commands. All 5 re-run this session against
`git worktree add --detach /tmp/pr3052-worktree pr-3052` (sha bb966ce6,
since removed), not cited from the first pass's run of them.

1. **Harness exists, invocation documented.** check: `bash -c "test -x
   scripts/issue-3041/run_pair.sh && test -f scripts/issue-3041/README.md"`.
   derived: ran this exact command against the worktree this session — exit
   code 1 (fails). derived: `git ls-tree pr-3052 scripts/issue-3041/run_pair.sh`,
   run this session — mode `100644`, not `100755` (the git-tracked mode,
   read via `git ls-tree` directly from the tree object, not a
   `core.fileMode`/umask checkout artifact); `ls -la` on the worktree copy,
   run this session, shows `-rw-rw-r--`, confirming the same. **Verdict:
   Incorrect** — failing clause: the check's `test -x
   scripts/issue-3041/run_pair.sh` returns false because the file is
   committed non-executable. Not a mitigation of the verdict, but relevant
   context: canonical: `scripts/issue-3041/README.md` (PR #3052 sha
   bb966ce6, untracked on this review's own branch), read this session — the
   documented invocation is `bash scripts/issue-3041/run_pair.sh <args>`,
   which does not need the `+x` bit and was exercised successfully 4 times
   per `gh pr view 3052`'s own Test plan section, read this session — the
   harness is functionally complete and was actually run, but the issue's
   own literal, executed-live check on this repo state still fails as
   committed. derived: the first pass's own citations for this criterion
   (`gh pr diff 3052 --name-only` and the README's prose, not the literal
   `test -x` command) — it graded this criterion Present without running the
   check itself; this is the gap this session's independent re-derivation
   found.
2. **>=3 paired runs, >=2 disciplines, both arms retained.** check: `bash -c
   "test $(ls -d docs/issue-3041/_assets/*/ | wc -l) -ge 3"`. derived: `ls -d
   docs/issue-3041/_assets/*/ | wc -l` against the worktree this session —
   `4`. **Verdict: Present.**
3. **Blind scoring, blinding mechanism named.** check: `python3 -c
   "import json,glob; [json.load(open(f)) for f in
   glob.glob('docs/issue-3041/_assets/*/verdict.json')] and print('ok')"`.
   derived: ran this exact command this session — `ok`. Substantively
   re-checked beyond the bare parse: derived: `jq -r '.evaluator_prompt'`
   on `docs/issue-3041/_assets/01-study-groups/verdict.json` (PR #3052 sha
   bb966ce6, untracked on this review's own branch), then `grep -iE
   "skill|arm|document_1_actual|mounted"` over it, run this session — zero
   matches (no arm label leaks into the evaluator's own input); derived:
   `jq -c '{document_1_actual_arm, document_2_actual_arm}'` on the same
   file, run this session — the arm mapping lives only in that sibling
   field, never in the prompt text. **Verdict: Present.**
4. **Top-line verdict, per-pair scores.** check: `bash -c "test $(grep -l
   document_1_score docs/issue-3041/_assets/*/verdict.json | wc -l) -ge 3"`.
   derived: ran this exact command this session — `4`. derived: `jq -c
   '.evaluator_verdict'` on the same pair's verdict.json, run this session —
   `{"document_1_score": 8, "document_2_score": 8, "verdict":
   "indistinguishable", "reasoning": "..."}` (the top-level
   `document_1_score` field is a `null` placeholder; the real score is
   nested, and the `grep -l` check matches the field-name substring wherever
   it appears, satisfied either way). **Verdict: Present.**
5. **Secondary instrumentation script exists.** check: `bash -c "test -f
   scripts/issue-3041/instrument.py"`. derived: ran this exact command
   against the worktree this session — passes. canonical:
   `scripts/issue-3041/instrument.py` (PR #3052 sha bb966ce6, untracked on
   this review's own branch), read this session — computes `skill_opens`,
   `first_open_fraction`, and `interleaved_2plus` from the raw transcript,
   matching the issue's Scope bullet. **Verdict: Present.**

Must-not clause (no call-success/mount-count/open-timing as scoring input;
evaluator must not have generated either arm): derived: `jq -r
'.evaluator_prompt'` re-checked this session (criterion 3 above), holds —
the evaluator prompt contains only task text, rubric, and the two documents.

### Is the null trustworthy?

derived: Sections 1-3 above — no, not as evidence about the skill layer
specifically, same reason the first pass gave: a session with the `Skill`
tool declared but only 17 irrelevant built-in skills behind it scores the
same as a session with no `Skill` tool at all, which is weaker than
"mounting the target skill layer does not change the deliverable." What this
session adds: Section 2 above gives a specific, live-tested flag combination
(`--setting-sources project,local --plugin-dir <skill-registry>`) that would
give the skills-on arm a first real chance to select the target skills on
task text written close to their trigger vocabulary. Until that re-run
exists, "the skill layer doesn't help" remains unverified.

## Why

canonical: `gh issue view 3041`, run this session — the task instructed
re-deriving the invalidation claim from primary session logs rather than
accepting it, then determining whether the harness's own confound (Finding
A) is fixable in place, and re-examining the target-repo confound (Finding
B) for whether re-pinning alone closes it.

canonical: `/home/jwjung/skill-registry/skills/experiment-trust/SKILL.md`,
read this session via the Skill tool, Step 1 — its scope gate routes an
offline paired comparison with no random assignment away from SRM/A-A
machinery. derived: `gh issue view 3041`, run this session — the issue body
describes exactly that kind of comparison, so the gate applies here the same
way.

canonical: `/home/jwjung/skill-registry/skills/adversarial-review/SKILL.md`,
read this session via the Skill tool — its core mechanism is never to trust
the artifact's own narrative and to re-derive from its retained logs.
derived: Section 4 criterion 1 above (`bash -c "test -x
scripts/issue-3041/run_pair.sh && ..."`, run this session, exit code 1) —
applying that mechanism this session is why the literal check was actually
executed instead of inferred from the README's prose, and is what surfaced
the executable-bit defect.

canonical:
`/home/jwjung/skill-registry/skills/conformance-review-verdict-assignment/SKILL.md`,
read this session via the Skill tool — rule 2 (Incorrect, not Absent, for an
artifact that actively contradicts the requirement's literal stated
condition) and rule 5 (name the failing clause). derived: Section 4
criterion 1 above applies both rules directly to the `test -x` result.

canonical: `gh pr view 3052`, run this session, Open findings section — PR
#3052's own record logs a pre-registration gap (no numeric win threshold
fixed before running). canonical:
`/home/jwjung/skill-registry/skills/hypothesis-testing/SKILL.md`, read this
session via the Skill tool, Step 4 — its registration-form gate places that
gap downstream of, not a substitute for, Section 1's corpus finding, since a
pre-registered threshold on a corpus-free `Skill` tool would not have made
the manipulation meaningful either.

## What did not work

None — no reversals during this session. `git archive` (used for the first
read of `run_pair.sh`'s permissions) did not preserve the executable bit,
which briefly looked like a checkout artifact. canonical: `git ls-tree
pr-3052 scripts/issue-3041/run_pair.sh`, run this session — mode `100644`
(reads the tree object's mode directly, independent of checkout method).
derived: `bash -c "test -x scripts/issue-3041/run_pair.sh && test -f
scripts/issue-3041/README.md"` against a `git worktree add --detach`
checkout, run this session — exit code 1. Both agree, so the non-executable
finding is real, not a byproduct of `git archive`.

## Upstream basis

- PR #3052, sha bb966ce64714cdf17d550b46e14d8e4af332baaa — fetched via `gh
  pr view 3052`, `gh pr diff 3052 --name-only`, and `git fetch origin
  pull/3052/head:pr-3052` into `git worktree add --detach`, both since
  removed this session. `docs/issue-3041/_assets/` (untracked on this
  review's own branch) and `scripts/issue-3041/` (untracked on this
  review's own branch) are as committed in PR #3052 at this sha; every path
  under either cited above was read from the worktree this session.
- Issue #3041 body — `gh issue view 3041`, run this session.
- canonical: the first verification pass, already on `main`:
  `docs/issue-3041/reports/conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769.md`
  — read this session for context, not inherited; every claim from it
  re-derived independently in Sections 1-3 above.
- `scripts/issue-3041/run_pair.sh`, `evaluate_pair.py`, `README.md`,
  `instrument.py` — PR #3052 sha bb966ce6, untracked on this review's own
  branch, read this session from the worktree.
- The deviation log recording why `--setting-sources project,local` was
  added — PR #3052 sha bb966ce6, path cited in Section 2 above, untracked on
  this review's own branch.
- `/home/jwjung/.claude/settings.json`, `claude --help`, `printenv
  MUSTER_SKILL_REGISTRY_ROOT`, `ls -la /home/jwjung/.claude/skills` — this
  machine's own configuration (not part of this repo), read/run this
  session, underlying Section 2's corrected-invocation finding.
- A live `claude -p` smoke test run by this session in a throwaway `/tmp`
  workspace (max spend $0.2, actual $0.0248) — the corrected-invocation
  probe transcript in Section 2.
- `https://github.com/JiwonJung94/study-companion.git`, cloned live this
  session to a scratch path (a separate repository, not reachable from this
  one) — pin `e102772480545a6be0af733f51020c97e7357ba7` and `main`,
  underlying Section 3.

## Open findings

- Criterion 1's Incorrect verdict has a one-line fix
  (`chmod +x scripts/issue-3041/run_pair.sh`) not applied here, per this
  session's charge not to edit PR #3052.
- Finding A's corrected invocation (Section 2) is identified and live-tested
  in isolation, but not yet applied to `run_pair.sh` or re-run against the 4
  pair directories under `docs/issue-3041/_assets/` (PR #3052 sha bb966ce6,
  untracked on this review's own branch), read this session in Sections 1
  and 4 above. This is new work, not started here — a re-run with the
  corrected invocation from Section 2 does not exist yet.
- Finding B (Section 3): no resolution path exists within PR #3052 as it
  stands; a future re-run needs either real application/backend/data content
  in the target repo, or task texts that state their self-containment
  explicitly.
- none other.

## Next steps

canonical: this record's own Sections 1-4 above — loop_state is terminal
(landed): Section 1 re-derived Finding A independently from primary logs,
Section 2 determined the harness's confound is correctable in place and
identified plus live-tested the specific fix, Section 3 re-examined and
answered the re-pinning question for Finding B, and Section 4 assigned an
independent verdict per acceptance criterion including one divergence from
the first pass on criterion 1. derived: this session made no `git push`, no
`gh pr merge`, and no `gh pr edit` call against #3052 anywhere in this
transcript, and both the local `pr-3052` ref and the `/tmp/pr3052-worktree`
worktree were deleted (`git branch -D pr-3052`, `git worktree remove`) rather
than pushed — PR #3052 was not merged or edited this session. No further
action from this session; the Open findings above name the follow-up work
without starting it.

## Skill verdicts

- skill-verdict: experiment-trust — applied: invoked; canonical:
  `/home/jwjung/skill-registry/skills/experiment-trust/SKILL.md`, read this
  session via the Skill tool — Step 1's scope gate confirms this offline
  paired harness has no random assignment, so SRM/A-A machinery does not
  apply. derived: `gh issue view 3041`, run this session — re-confirms the
  gate's applicability against the issue body's own description of the
  comparison.
- skill-verdict: adversarial-review — applied: invoked; canonical:
  `/home/jwjung/skill-registry/skills/adversarial-review/SKILL.md`, read
  this session via the Skill tool — its core mechanism (never trust the
  artifact's own narrative, re-derive from its retained logs). derived:
  Section 4 criterion 1 above (`test -x`, exit code 1, run this session) —
  applying that mechanism is why the check was actually executed this
  session rather than inferred from the README's prose.
- skill-verdict: conformance-review-verdict-assignment — applied: invoked;
  canonical:
  `/home/jwjung/skill-registry/skills/conformance-review-verdict-assignment/SKILL.md`,
  read this session via the Skill tool — rule 2 (Incorrect, not Absent, for
  an artifact that actively contradicts the requirement's literal stated
  condition) and rule 5 (name the failing clause) shaped criterion 1's
  verdict in Section 4. derived: rule 6 (re-check a plausible false positive
  once before finalizing) — `git ls-tree` plus a fresh worktree checkout,
  both run this session, re-verify the non-executable finding rather than
  reporting it off the first `git archive`-based read (see What did not
  work).
- skill-verdict: hypothesis-testing — applied: invoked; canonical:
  `/home/jwjung/skill-registry/skills/hypothesis-testing/SKILL.md`, read
  this session via the Skill tool, Step 4's registration-form gate. derived:
  `gh pr view 3052`, run this session, Open findings section — places PR
  #3052's own logged pre-registration gap downstream of, not a replacement
  for, Section 1's corpus finding above.
