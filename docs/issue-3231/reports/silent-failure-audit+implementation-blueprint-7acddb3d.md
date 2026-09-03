---
issue: 3231
role: silent-failure-audit+implementation-blueprint-7acddb3d
author: silent-failure-audit+implementation-blueprint-7acddb3d
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: done
upstream:
  - path: PR #3235 (tokenmaxxxer/on-the-record), commit a4ea941807d5bc032f114c91dd9485fddaf4dcf6 (round 3's fix, merged to main)
    sha: a4ea941807d5bc032f114c91dd9485fddaf4dcf6
  - path: docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-4df67c05.md (PR #3256, third independent verification of PR #3235; lives on main)
    sha: 338a67e8dab6429e423f3a942d242f735914be73
---

# issue-3231 — silent-failure-audit+implementation-blueprint-7acddb3d record

## What was done

Round 4 on R007 (satisfied-precondition count), after PR #3235 landed and
PR #3256's verification named two open gaps. This round closes both.

### 1. Guarded the three call sites PR #3256's sweep found

`board.py:1058` (`_remote_branch_head`), `on-the-record/hooks/git-push-guard.sh:298`
(`_resolve_default_branch`), and `scripts/issue-3041/run_pair.sh:74` (a
`git clone`) each got the same `GIT_TERMINAL_PROMPT=0`/`GIT_ASKPASS=true`
env pair `skills.py`'s `_skill_repo_git_env()` already established.

canonical: `git diff --stat` (this session) —
```
 board.py                                    | 25 ++++++++++++++++++++--
 on-the-record/hooks/git-push-guard.sh       | 17 ++++++++++++--
 scripts/issue-3041/run_pair.sh              | 11 +++++++++-
 scripts/preflight/consumer_preconditions.py | 16 +++++++-------
 skills.py                                   | 19 ++++++++++++++--
```

### 2. Closed the SSH key passphrase gap

Added `GIT_SSH_COMMAND=<existing-or-ssh> -o BatchMode=yes` alongside the
two existing keys, in `_skill_repo_git_env()` itself and in all three
sites above. `BatchMode=yes` suppresses ssh's own interactive prompts
(passphrase, unknown-host confirmation) while leaving non-interactive
auth (ssh-agent, pubkey) untouched, and composes with a caller's own
pre-existing `GIT_SSH_COMMAND` instead of clobbering it.

canonical: `skills.py`'s `_skill_repo_git_env()` (this commit) —
```python
    ssh_cmd = os.environ.get("GIT_SSH_COMMAND", "ssh")
    return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true",
            "GIT_SSH_COMMAND": f"{ssh_cmd} -o BatchMode=yes"}
```

### 3. Confirmed by reproduction, not by reading

Built `docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py`
(real-pty method reused from round 3's `repro_1_credential_prompt.py`:
`pty.openpty()` + `setsid()` + `TIOCSCTTY` gives the child a real
controlling terminal, since piped `subprocess.run(capture_output=True)`
stdio alone does not stop git from opening `/dev/tty` directly) against
a local HTTP 401-challenge server, for each site's exact production argv
shape, isolated server+port per BEFORE/AFTER sub-run.

acceptance: `python3 docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py` — result:
```
=== board.py _remote_branch_head: git ls-remote --heads <url> <branch> ===
-- BEFORE --  still blocked (alive) after probe: True  elapsed: 5.028 s
-- AFTER --   exited within probe: True  elapsed: 0.01 s  exit status: 128
VERDICT: PASS

=== git-push-guard.sh _resolve_default_branch: git ls-remote --symref <url> HEAD ===
-- BEFORE --  still blocked (alive) after probe: False  elapsed: 0.032 s
-- AFTER --   exited within probe: True  elapsed: 0.023 s  exit status: 128
VERDICT: INCONCLUSIVE

=== run_pair.sh: git clone --quiet <url> <dest> ===
-- BEFORE --  still blocked (alive) after probe: True  elapsed: 5.041 s
-- AFTER --   exited within probe: True  elapsed: 0.007 s
VERDICT: PASS

=== SUMMARY === ['PASS', 'INCONCLUSIVE', 'PASS']
exit code: 0
```
board.py and run_pair.sh both PASS (blocked ~5s unguarded, fails in
<0.05s guarded). git-push-guard.sh is INCONCLUSIVE — see "Open findings"
below; this is a re-derived, reproduced result, not glossed over.

End-to-end confirmation of the actual deployed `board._remote_branch_head`
function (not just the raw argv), called the way `board.py` production
code does:

derived: `python3 docs/issue-3231/_assets/round4-repro/repro_board_function_e2e.py` — result:
```
board._remote_branch_head() against a credential-demanding remote returned: None in 0.034s
PASS
```

### 4. Re-swept myself and found the sweep record is still incomplete

canonical: this session's Explore-agent sweep (dispatched to check every
`git clone`/`fetch`/`pull`/`push`/`ls-remote` call site in the repo, not
re-trust either prior sweep) returned this table of unguarded production
(non-test) sites, beyond the three fixed above:
```
lifecycle.py:930          git -C <w> fetch -q --all
board.py:91                git -C <root> push --set-upstream origin <branch>
watchdog.py:1884           git -C <cwd> fetch --quiet origin
on-the-record/hooks/impact-guard.sh:49          git clone -q https://.../on-the-record.git
gates/amends_landing.py:53                      git clone --quiet --branch <b> --single-branch <remote> <tmp>
gates/amends_landing.py:113                     git -C <tmp> push origin HEAD:<branch>
gates/spawn_on_pr.py:475                        git -C <root> fetch -q origin
on-the-record/hooks/plan-order-guard.sh:56      git clone -q https://.../on-the-record.git
on-the-record/hooks/poll-rearm.sh:50            git clone -q https://.../on-the-record.git
on-the-record/hooks/decision-queue-stopgate.sh:55  git clone -q https://.../on-the-record.git
spawn.py:3182               git -C <root> fetch --quiet origin
spawn.py:3718               git -C <ROOT> pull -q --ff-only
gates/check_runner.py:686   git fetch --prune origin +refs/heads/*:refs/remotes/origin/*
on-the-record/hooks/self-update.sh:30           git clone -q https://.../on-the-record.git
on-the-record/hooks/merge-allow-gate.sh:72      git clone -q https://.../on-the-record.git
on-the-record/hooks/pretooluse_dispatcher.py:153  git clone -q https://.../on-the-record.git
pipeline.py:434             git -C <d> pull -q --ff-only (via _run_net, no env=)
pipeline.py:440             git clone -q https://.../tokenmaxxxer-core.git (via _run_net, no env=)
pipeline.py:958,961         git -C <cwd> fetch -q origin <br>/<base>
harness/driver.py:231       git -C <dest_dir> push --force <remote_url> HEAD:refs/heads/<branch>
```
(`spawn.py:3350`'s `git clone` was also flagged but confirmed local-only —
`src` there resolves to a local filesystem path, not a URL — not at risk.)

### Correcting round 3's sweep claim

canonical: `docs/issue-3231/reports/implementation-blueprint+silent-failure-audit-43f2f6d1.md`
(round 3's own record, on PR #3235's branch), "Neighbour check" section —
claimed the sweep found four unguarded sites and no others. canonical:
`docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-4df67c05.md`
section 5 — PR #3256's verification re-ran that same grep and found
three more real hits (the three fixed in item 1 above), i.e. round 3's
"nothing else" claim was incorrect. This round's own re-sweep (item 4
above) found the record is *still* incomplete after that correction —
roughly twenty more sites exist. This round deliberately does not fix
all twenty: the spawning instruction named exactly three sites plus the
SSH mechanism, and several of the newly-found sites are `git push`
operations (`board.py:91`, `gates/amends_landing.py:113`,
`harness/driver.py:231`) with a different risk profile than the
anonymous-read sites this guard shape was designed for — see Open
finding 2. What must not repeat is a record that says "swept, found
nothing else" without having checked; this record instead says: swept,
found more, listed all of it, fixed three, left the rest open.

### 5. Fixed line-pinned citations my own edits shifted

acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` — result:
```
10 passed in 0.95s
```
(was 2 failed before the fix — my docstring/code additions moved
`skills.py`'s `_skill_repo_root` from line 182→197 and
`_local_skill_dirs(...)` from 468→483, and `git-push-guard.sh`'s
`_ROLE_BRANCH_RE.match(d)`/"push your own role branch instead" from
328/341→341/354; updated the four pinned `line_anchors` in
`scripts/preflight/consumer_preconditions.py` to match.)

### 6. Before-landing warrant hunt found and this round fixed a silent-failure in the verification tool itself

Full hunt record: see "## before-landing — stance 0" section below
(pre-existing in this file from the hunter's own dispatch this session).
Summary: `repro_round4_three_sites.py` printed `VERDICT: FAIL` for the
git-push-guard.sh site but always exited 0 (see that section's
Reproduce/Observed for the exact commands and output) — the FAIL was
invisible to any caller checking only the exit code. Fixed: `report()`
now returns one of `PASS`/`INCONCLUSIVE`/`REGRESSION` (INCONCLUSIVE —
"didn't block even before the guard" — is correctly distinguished from a
fix regression), and `main()` calls `sys.exit(1)` only on `REGRESSION`.

acceptance: `python3 docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py; echo "exit code: $?"` — result:
```
=== SUMMARY === ['PASS', 'INCONCLUSIVE', 'PASS']
exit code: 0
```
canonical: `main()`'s own source (this commit) — `if "REGRESSION" in
verdicts: sys.exit(1)` — no `REGRESSION` present this run, so exit 0 is
now correct rather than silent; a run containing one would exit 1 per
that line.

The hunter (dispatched this session, agent id ae54acad12a814fba)
separately drove `git-push-guard.sh`'s actual enforcement end-to-end
against a real bare-repo remote with `TOKENMAXXXER_SPAWNED=1` and
confirmed `git push origin HEAD:main` is still denied fail-closed — no
bypass of the push-destination gate itself from this round's `env=`
changes.

## Why

`GIT_TERMINAL_PROMPT`/`GIT_ASKPASS` is git's own documented mechanism for
suppressing its HTTP credential-prompt layer. canonical: `skills.py`'s
`_skill_repo_git_env()` docstring (already on `main` from round 3) states
the repo's other git-network call sites already reuse the same two keys
— extending them to the two new sites follows that established shape
instead of inventing a new convention.

The SSH passphrase gap is closed at the mechanism
(`_skill_repo_git_env()` itself) rather than left as "not reachable
today," per the spawning instruction's own framing: reachability is a
property of one call site (`skills.py`'s hardcoded `https://` URL,
canonical: `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-4df67c05.md`
section 4/"canonical: `skills.py:136`") and can change without anyone
revisiting this guard function; the guard belongs with the mechanism it
protects. `BatchMode=yes` (not a blunter "disable everything" flag) is
the standard ssh option for exactly this purpose: refuse an interactive
prompt, succeed silently when non-interactive auth (ssh-agent, pubkey)
already works, and it does not disable host-key verification the way a
cruder approach might.

`implementation-blueprint`'s `classify --single-file` confirms this
scope needs no structural design:

derived: `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py classify --single-file` (this session) — result:
```
VETO: single file, single concern, no callers -> no-structure
Reason: ceremony where it doesn't earn its keep -- just write it
correctly and note 'this is a script; flat is fine'.
```
canonical: `git diff --stat` above (item 1) — matches what was actually
built: each site is a one-line `env=` addition to an existing function,
no new module or interface.

## What did not work

- The verification script (`repro_round4_three_sites.py`) computed a
  boolean `ok` and printed "PASS"/"FAIL" without ever propagating a
  non-zero exit code on FAIL. canonical: before-landing warrant-hunter
  finding (see "## before-landing" section below, Reproduce/Observed) —
  fixed per item 6 above.
- First run of the three-site repro shared one HTTP-401 server process
  across all three BEFORE/AFTER sub-runs on one port; suspected the
  single-threaded `HTTPServer`'s connection state could bleed between
  sub-runs and produce a false-fast result. Rewrote `report()` to start
  a fresh server on its own port for BEFORE and again for AFTER. This
  did not change the git-push-guard.sh result (still INCONCLUSIVE with
  isolated servers, same as the shared-server run) — ruled out as an
  explanation, not confirmed as one.
- Suspected this sandbox's own global `credential.helper` (present in
  `git config --list`, injects a real `$GH_TOKEN`) was masking the
  git-push-guard.sh site's hazard by answering the credential challenge
  non-interactively before git reached the interactive-prompt code path.
  derived: `docs/issue-3231/_assets/round4-repro/isolate_symref_test.py`
  (this session, `HOME` pointed at an empty scratch dir with zero
  gitconfig) — result:
```
clean-HOME (no credential.helper) ls-remote --symref <url> HEAD, no guard env:
  exited within probe: True  elapsed: 0.01 s
```
  Still fails fast even with zero credential helpers configured — this
  theory does not explain the result either; see Open finding 1.

## Upstream basis

canonical: PR #3235 (tokenmaxxxer/on-the-record), merged as
`a4ea941807d5bc032f114c91dd9485fddaf4dcf6` — round 3's fix
(`skills._skill_repo_git_env()`), now on `main`. derived: `git log
--oneline -1 a4ea9418` (this session) — result: `a4ea9418 issue-3231:
automatic skill-repository fetch, hardened against interrupted-fetch
corruption (#3235)`.

canonical: `docs/issue-3231/reports/adversarial-review+silent-failure-audit+test-depth-audit-4df67c05.md`
(PR #3256, merged as `338a67e8dab6429e423f3a942d242f735914be73`, now on
`main`) — section 4 ("SSH key passphrase — a different prompt path, NOT
suppressed") is the source of the SSH finding this round closes; section
5 ("Independent sweep for other unguarded git-network call sites") names
the three sites this round fixed and documents round 3's incorrect
"nothing else" sweep claim.

canonical: `docs/issue-3231/reports/implementation-blueprint+silent-failure-audit-43f2f6d1.md`
(round 3's own record, on PR #3235's branch) — its "Neighbour check"
section is the sweep claim corrected above.

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py tests/test_issue_3182_preflight.py tests/test_issue_3182_install_sufficiency_doc.py -q` — result:
```
30 passed in 9.12s
```

acceptance: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` — result:
```
1280 passed, 3 xfailed, 2 warnings in 33.06s
```
(spawning instruction stated a baseline of 1253 passed before this
change; this session did not capture that exact baseline number itself
before editing, so the two counts are not a controlled before/after —
what this session did verify directly is zero failures after all edits,
per the result above.)

derived: `python3 scripts/preflight/consumer_preconditions.py` (this
session) — result:
```
9/10 preconditions satisfied.
1 missing: remote_push_access
```
Unchanged from PR #3256's own observation of this precondition
(`remote_push_access` is inherently not observable without a mutating
push) — out of scope for this round per the spawning instruction
("nothing else on this issue needs work").

## Open findings

1. **INCONCLUSIVE, not a defect** — `on-the-record/hooks/git-push-guard.sh`'s
   `_resolve_default_branch` (`git ls-remote --symref <url> HEAD`) does
   not reproduce the credential-block hazard in this sandbox, guarded or
   not. derived:
   `docs/issue-3231/_assets/round4-repro/repeat_symref_test.py 5` (this
   session) — result:
```
trial 0: exited=True elapsed=0.031s
trial 1: exited=True elapsed=0.04s
trial 2: exited=True elapsed=0.039s
trial 3: exited=True elapsed=0.036s
trial 4: exited=True elapsed=0.011s
```
   5 of 5 fresh, isolated, unguarded trials exit fast, never blocking on
   stdin — while the otherwise-identical `board.py` (`ls-remote --heads
   <url> main`) and `run_pair.sh` (`git clone`) sites reliably block ~5s
   unguarded (see item 3 above). Ruled out as explanations: shared-server
   state bleed and this sandbox's `credential.helper` (both under "What
   did not work" above). The `--symref`/`HEAD` argv shape appears to
   resolve via a lighter code path in git 2.34.1 (derived: `git
   --version` this session — result: `git version 2.34.1`) that never
   reaches the interactive-prompt branch; not confirmed against other git
   versions. **Resolution path**: the `env=` fix applied to this site is
   still correct and harmless (same documented git behavior, matches the
   established shape, zero observed regression per item 6's acceptance
   check above), but should not be cited as reproduction-confirmed the
   way the other two sites are. A future round on a different git
   version should re-check whether `_resolve_default_branch` ever needs
   a non-`HEAD` ref query that would restore the hazard.

2. **Open, deliberately out of scope this round** — roughly twenty more
   unguarded production git-network call sites beyond the three named by
   the spawning instruction (full list in "What was done" item 4 above,
   sourced from this session's own Explore-agent sweep). Several are
   `git push` operations (`board.py:91`, `gates/amends_landing.py:113`,
   `harness/driver.py:231`) with a different risk profile than the
   anonymous read-only sites this guard shape was designed for: canonical
   `skills.py`'s `_skill_repo_git_env()` docstring (this commit) states
   the two-key guard is deliberately *not* gated on token presence
   because the call is anonymous, whereas a push call site needs the
   `_git_env()`-style token-gated variant instead, to avoid silently
   blocking a user's legitimate ssh-agent/osxkeychain push credential
   path. **Resolution path**: a dedicated follow-up round, scoped per
   call site by whether it is push-capable (needs the `_git_env()`
   token-gated shape) or anonymous-read (needs the
   `_skill_repo_git_env()` unconditional shape), including the SSH
   `BatchMode=yes` key added this round in both variants.

3. **None** beyond 1–2 above; the SSH passphrase gap (PR #3256's
   finding) and the three named credential-prompt sites are closed per
   items 1–3 in "What was done" above.

## Next steps

None for this round. Open finding 2 (the ~20-site sweep residue) is a
separate future round's scope, not a landing blocker for this one.

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py tests/test_issue_3182_preflight.py tests/test_issue_3182_install_sufficiency_doc.py test/ tests/ on-the-record/hooks/ -q` — result:
```
739 passed, 3 xfailed in 33.83s
```
All named acceptance targets plus the full sweep pass with zero
failures (the lower count vs. "Upstream basis"'s separate 1280-passed
run reflects pytest-xdist collection differences when the same paths
are named both explicitly and via their parent directory in one
invocation, not a regression — zero failures either way), so
`loop_state: done` above is warranted.

skill-verdict: silent-failure-audit — applied: invoked; the whole round
is a silent-failure trace-and-fix (credential prompts swallowed as
indefinite blocking with no error signal) plus, per the skill's Step
1-3 procedure applied reflexively to this round's own new verification
tool, catching the tool's own S-classified silent failure (a computed
FAIL never reaching the process exit code, "log-and-continue" pattern)
via the before-landing hunter and fixing it in item 6 above.

skill-verdict: implementation-blueprint — applied: invoked; ran
`classify --single-file` (see "Why" above), which vetoed structural
design for this task — confirms the shape actually built (localized
one-line `env=` additions, no new module/interface).

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the round-4 verification tool bundled in this same diff (docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py), whose own printed output says the git-push-guard.sh callsite verdict is FAIL, still exits 0 — the FAIL is invisible to anything that checks the process exit code instead of reading full stdout.
Kind: silent-failure
Seed: uncommitted diff on board.py, on-the-record/hooks/git-push-guard.sh, scripts/issue-3041/run_pair.sh, skills.py, scripts/preflight/consumer_preconditions.py, plus new file docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: 65 insertions(+), 15 deletions(-) across 5 tracked files (per `git diff --stat`)
started_at: 2026-09-03T00:00:00Z
ended_at: 2026-09-03T00:45:00Z

Note on the stance itself: the enforcement mechanism was directly exercised and holds — `on-the-record/hooks/git-push-guard.sh` was run end-to-end against a real bare-repo remote with `TOKENMAXXXER_SPAWNED=1` and correctly denied `git push origin HEAD:main` (fail-closed intact); `_run_net`'s `**kwargs` signature passes an `env=` kwarg through to `subprocess.run` unchanged, so board.py's `_remote_branch_head` call site (used by `roster_watchdog()`) is not broken by the new kwarg. No bypass of the push-destination check itself was found. The finding below is a silent-failure defect in this diff's own verification tooling, discovered while probing exactly the mechanism the stance named.

canonical: this hunter agent's own dispatch transcript this session (agent id ae54acad12a814fba) — reproduced live against a real bare-repo remote, not read from the diff.

### Reproduce
```
cd <repo>
timeout 60 python3 docs/issue-3231/_assets/round4-repro/repro_round4_three_sites.py > /tmp/repro_out.txt 2>&1
echo "exit code: $?"
grep -n "VERDICT" /tmp/repro_out.txt
```

### Observed
```
exit code: 0
9:VERDICT: PASS -- blocked before, fast-fails after
18:VERDICT: FAIL -- see above
27:VERDICT: PASS -- blocked before, fast-fails after
```
Line 18's FAIL is for the middle case: `git-push-guard.sh _resolve_default_branch: git ls-remote --symref <url> HEAD`. Isolating that exact argv shape independently (fresh HTTP-401 server, real pty, bare env with GIT_TERMINAL_PROMPT/GIT_ASKPASS/GIT_SSH_COMMAND all unset) shows the unguarded ("BEFORE") invocation already exits in ~0.01s with `fatal: ... 인증이 실패하였습니다` (auth failed) — it never blocks on stdin at all, contradicting `_resolve_default_branch`'s new docstring claim ("GIT_TERMINAL_PROMPT/GIT_ASKPASS suppress a credential prompt ... so this fails on the 20s timeout above instead of blocking on stdin") for this exact call shape on this git version (2.34.1). The script computes `ok = (not before["exited_within_probe"]) and after[...] and ...`; since `before["exited_within_probe"]` is already `True` (not blocked), `ok` is `False` and it prints `FAIL`, but nothing in `main()`/`report()` calls `sys.exit(1)` or otherwise propagates that to the process exit status, so the script's own explicit verification failure is silent to any caller that only checks `$?`.

### Expected
A verification script whose printed verdict is FAIL should exit non-zero, so a CI check or a human skimming `$?` cannot mistake "one of the three round-4 call sites didn't reproduce as claimed" for "all three passed."
