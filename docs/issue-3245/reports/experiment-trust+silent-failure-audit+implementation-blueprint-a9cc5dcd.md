---
issue: 3245
role: experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd
author: experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd
skills: experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: committing
upstream:
  - path: docs/issue-3245/reports/independent-verification-2.md
    sha: c2e23a4b5fe038be99a6dd3b67f2a0e6890f9461
  - path: docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md
    sha: 5bf676422d7680a81388d9924c8185b4fb707a23
---

# issue-3245 — experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd record

## What was done

This session's actual task, per its own consult-log, was to verify and
land uncommitted work already sitting in this workspace from an earlier
turn/session on this same branch -- not to author new code.

canonical: this session's own `docs/issue-3245/reports/consult-log/*.md`
(4 `skill_judge` entries, timestamps 03:09:05 through 03:11:08) -- all four
independently reject `adversarial-review` and every other mounted-skill
candidate for this exact task text ("workspace contains uncommitted work
from the previous session — verify briefly, then commit/push/PR; do not
redo"), each with `picked=[]`.

derived: `git status --porcelain=v1` (this session, before any edit)
```
 M scripts/consumer-path/prepare_arms.py
 M scripts/consumer-path/run_pair.py
 M tests/test_consumer_path_trust_root.py
?? docs/issue-3245/_assets/02-onboarding-experiment/
?? docs/issue-3245/reports/consult-log/
```

The uncommitted diff adds `prepare_arms.provision_credentials()`: it
copies only `<source>/.claude/.credentials.json` into each arm's isolated
`tempfile.mkdtemp()` `HOME` (no plugin registration, no marketplace
config, no `~/.claude.json`), and `run_pair.py` now passes this session's
own real `$HOME` as that source. This directly implements the fix
`independent-verification-2` (upstream, sha `c2e23a4b5fe038be99a6dd3b67f2a0e6890f9461`)
diagnosed: an isolated arm `HOME` with no credentials makes `claude -p`
fail on "Not logged in" before any hook or skills-manipulation logic
runs, which `spawn.py doctor()`'s coarse `PreToolUse`-fired check
misreports as "hooks don't fire headless."

acceptance: `python3 -m pytest tests/test_consumer_path_trust_root.py -q`
(this session, this turn, HEAD `def3b886` + the uncommitted diff) —
result:
```
22 passed in 0.83s
```

The new tests (`test_provision_credentials_copies_only_the_credentials_file`,
`test_provision_credentials_fails_closed_without_a_source`,
`test_build_manifest_provisions_credentials_identically_on_both_arms`,
`test_build_manifest_without_credentials_source_stays_unauthenticated`)
cover: narrow copy (only `.credentials.json`, nothing else lands under
`HOME`), fail-closed behavior when no credentials source exists, identical
provisioning on both arms without touching the on/off `skill_files`
manipulated variable, and unchanged default (no-credentials) behavior for
existing callers.

The untracked 02-onboarding-experiment assets directory (path
docs/issue-3245/_assets/02-onboarding-experiment, not yet in git history
as of this writing -- committed together with this record below;
manifest.json, manifest.json.sha256, transport.json, no result.json) is a
real `build_manifest()` run against a previously deferred pair. It was
recorded as deferred here:

derived: `grep -n "02-onboarding-experiment" "docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md"` — result (matching line):
```
| 02-onboarding-experiment | #21 | #22 | not attempted | -- | -- | -- | -- | -- | No -- not attempted this session |
```

Its manifest.json shows both arms with `credentials.provisioned: true` --
direct evidence the fix produces a valid, credentialed manifest on a real
pair, not just under the unit tests:

derived: `python3 -c "import json; m=json.load(open('docs/issue-3245/_assets/02-onboarding-experiment/manifest.json')); print([a['credentials']['provisioned'] for a in m['arms']])"` — result:
```
[True, True]
```

There is no result.json because this run only went through arm
preparation; it did not carry through to a full skills-on/skills-off
dispatch and scoring pass. Per the "do not redo" instruction this session
was given, no attempt was made to run that dispatch to completion.

Committed all of the above (code, tests, the manifest/transport
artifacts, and this record) on this branch. Push/PR status: see
`## Next steps`.

## Why

Re-authoring or re-running this work would have contradicted the
session's own instruction ("do not redo") and duplicated work whose
soundness could be checked directly against the upstream diagnosis and
the test run already cited under `## What was done`. Verifying (read
diff, cross-reference upstream diagnosis, run tests) and then landing was
the smallest correct action.

## Upstream basis

- docs/issue-3245/reports/independent-verification-2.md, sha
  `c2e23a4b5fe038be99a6dd3b67f2a0e6890f9461` -- diagnosed the
  unauthenticated-arm-`HOME` root cause this diff fixes.
- docs/issue-3245/reports/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-7b04b22b.md,
  sha `5bf676422d7680a81388d9924c8185b4fb707a23` -- recorded R007 and left
  `02-onboarding-experiment` as "not attempted this session."

derived: `git log --oneline -1 5bf676422d7680a81388d9924c8185b4fb707a23` — result:
```
5bf67642 issue-3245: record R007 consumer-path run (0/5 pairs scored, CLI/hook regression found)
```

## Open findings

- `gh auth status` fails for this account (`GH_TOKEN` and the cached
  `~/.config/gh/hosts.yml` token both invalid) -- resolution path: human
  runs `gh auth login` or `gh auth refresh -h github.com`. This blocks
  `gh pr create`/`gh pr view` from this session; it does not block `git
  commit`.
- The 02-onboarding-experiment pair's actual skills-on/skills-off dispatch
  and scoring (a result.json) is still not attempted -- resolution path:
  a future session runs `run_pair.py` for that pair to completion once
  `gh` auth and rate limit allow closing the loop with a PR.

## Next steps

derived: `git push -u origin issue-3245/experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd` — result:
```
def3b886..e20781e0  issue-3245/experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd -> issue-3245/experiment-trust+silent-failure-audit+implementation-blueprint-a9cc5dcd
```
Push succeeded (git's own HTTPS auth to this remote is independent of
`gh`'s token). `gh pr create` was then attempted and refused by this
repo's own `pr-base-guard` pre-tool-use hook, fail-closed, because it
could not run `gh repo view --json defaultBranchRef` under the same
broken `gh` auth/rate-limit state recorded under `## Open findings`.

An external relay or a future session with restored `gh` auth needs to
open the PR (title "issue-3245: provision arm credentials in
consumer-path launcher", body drafted at this session's own
`/tmp/pr-body-3245-a9cc5dcd.md`, trailer `Advances #3245` since this
session did not run the pair dispatch through to a scored result.json).
`loop_state` moves to `landed` once that PR opens; until then it stays
`committing`.

other mounted skills: not triggered
