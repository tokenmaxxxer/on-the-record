---
code_under_review:
  - docs/handbooks/setup.md
  - README.md
type: docs
breaking: false
verdict: pass
loop_state: committing
---

# issue-1781 phase-2 implementation record

## Summary of work

Delivered the phase-2 build approved via `APPROVE issue-1781/implementation`
(basis: docs/issue-1781/proposals/skill-repository-install-step.md), per
that proposal's frozen write set and its numbered plan section:

1. `docs/handbooks/setup.md`: added a skill-repository install step
   (bilingual 한국어/English mirrored paragraphs) to the "시작하기 /
   Getting started" section, right after the existing rulebooks/core
   auto-clone paragraph: sibling-clone-as-default
   (`$TOKENMAXXXER_RULEBOOKS/skill-repository`, zero-config) or an
   explicit `MUSTER_SKILL_REPO=<checkout>/skills` override, with the
   root-vs-`skills/` anti-pattern (#1761) called out explicitly.
2. Same section: pasted both fail-closed symptom strings verbatim (unset
   case; checkout-root case) so a consumer hitting either can
   self-diagnose by string match.
3. Same section: added a short paragraph documenting the four `--skills`
   sources (issue #1774) and the two fail-closed invariants (duplicate
   name across sources; a source directory carrying `hooks/`).
4. `README.md`: added a Quickstart paragraph naming skill-repository as
   the one exception to "no separate clone needed," linking to the new
   setup.md step.

## Why

basis: docs/issue-1781/proposals/skill-repository-install-step.md
(approved via `APPROVE issue-1781/implementation`, issue comment;
canonical: `gh issue view 1781 --comments`, read this session — the
comment thread shows three prior escalated judgment verdicts before the
final `APPROVE issue-1781/implementation` line from the account that
also authored the issue).

## Acceptance verification

Acceptance 1: "A fresh-install walkthrough following only the updated
docs reaches a successful mapped-role dry-run" — check: record pastes
the walkthrough commands and dry-run output executed live from a
clean-env simulation (unset `MUSTER_SKILL_REPO`, fresh temp clone).

acceptance: fresh clone + clean-env walkthrough, re-run this session
against the doc text as written above — result: as pasted below.

```
$ git clone https://github.com/tokenmaxxxer/skill-repository.git /tmp/skill-repo-clean-test2
$ ls /tmp/skill-repo-clean-test2
README.md  docs  install.sh  skills
```

Unset case (matches the fail-closed symptom pasted into setup.md above):

```
$ env -u MUSTER_SKILL_REPO -u TOKENMAXXXER_RULEBOOKS python3 -c "
import spawn
try:
    spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())
except SystemExit as e:
    print('sys.exit ->', e)
"
sys.exit -> --skills: skill-repository 체크아웃을 못 찾았다 — MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를 확인하라
```

Checkout-root case (the #1761 anti-pattern the docs now warn against —
matches the second fail-closed symptom pasted into setup.md above):

```
$ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test2 python3 -c "
import spawn
try:
    spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())
except SystemExit as e:
    print('sys.exit ->', e)
"
sys.exit -> --skills: 모르는 스킬 implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint — 쓸 수 있는 이름: docs, skills
```

Success case, following the doc text's instruction to point
`MUSTER_SKILL_REPO` at the checkout's `skills/` subdirectory:

```
$ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test2/skills python3 -c "
import spawn
r = spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())
print('source:', r['source']); print('skills:', r['skills']); print('skill_sha:', r['skill_sha'])
"
source: skill-repo
skills: ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint']
skill_sha: 8021ada
```

Mapped-role dry-run, same env, exit 0:

```
$ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test2/skills python3 spawn.py implementation "clean-env test" --issue 1781 --dry-run
{ "sandbox": {...}, ... }
(exit: 0)
```

acceptance: as pasted above — result: the docs as written (sibling-clone-
or-`MUSTER_SKILL_REPO`-pointed-at-`skills/`, both fail-closed symptoms
pasted verbatim) reproduce exactly the success and failure paths
re-confirmed live above, and the mapped role `implementation`
(docs/specs/role-source-allowlist.json:272-277) reaches a successful
`--dry-run` (exit 0) once the docs' instructions are followed. Acceptance
1 verdict: met.

Acceptance 2 (README Quickstart mentions the third repo, links setup.md):
canonical: `git diff -- README.md`, this session's own edit, read
directly — README.md now names skill-repository as the exception to
"no separate clone needed" and links `docs/handbooks/setup.md`. Verdict:
met.

Acceptance 3 (four `--skills` sources documented in one short paragraph):
canonical: `git diff -- docs/handbooks/setup.md`, this session's own
edit, read directly — the new paragraph lists skill-repository checkout,
installed plugins' `skills/<name>/`, `~/.claude/skills/<name>`, target
repo's `.claude/skills/<name>`, and the two fail-closed invariants.
Verdict: met.

## Doc-placement ladder

- [x] `docs/handbooks/setup.md` — skill-repository step + `--skills`
  sources paragraph added to "시작하기 / Getting started", bilingual
  mirrored.
- [x] `README.md` — Quickstart paragraph added, links setup.md's new
  section.

## What did not work

None.

## Open findings

None.

## Next steps

None for this delivery.

## Resolution path

N/A — no open findings.
