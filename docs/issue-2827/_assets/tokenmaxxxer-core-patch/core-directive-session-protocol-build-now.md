[core] Interaction protocol for role '<role>' (role-handoff contract v3), build-now (single-phase) variant:

- Requirements enter as GitHub ISSUES, authored by the user only. You never
  file an issue. The issue number is the subject: subject = issue-<n>, and
  a task you cannot tie to an issue is not yours to start.
- YOUR issue is assigned in the prompt that invoked this session — you
  never pick one yourself. If the invocation names no issue, do not choose
  one, do not start work, and do not create anything: ask which issue you
  are being opened for, and stop until answered. All work in this session
  stays inside that one issue's branch and tree.
- ALL of your output — code, records, reports, documents — returns to the
  user as a PULL REQUEST against main. Never push to main. Work on the
  branch issue-<n>/<role> (one branch per issue x role; never share a
  branch with another role).
- This session is running build-now (contract v3 s19a): CORE_BUILD_NOW=1
  was set by the spawner, not by you, so the two-phase proposal/Approve
  boundary does not apply this run — skip the proposal round, build on
  issue-<n>/<role>, commit code and your record, and open ONE PR carrying
  the work. A session never grants itself this bypass by setting the
  variable on its own. (The two-phase default, the checkpoint variant, and
  the Approve-signal mechanics — string-equality test, two-account vs
  single-account mode, near-match reporting duty — do not apply while this
  variable is set; read core/directive/session-protocol.md if this session
  ever needs them, e.g. after a scope-exceeded stop hands off remaining
  work to a follow-up two-phase unit.)
- Human decisions are GitHub acts only: PR merge = acceptance of the
  delivered work, issue/PR closed unmerged = refusal. Never approve, merge,
  or relay an approval yourself.
- Output layout, enforced: code under src/, tests under test/, documents
  under docs/ (README.md excepted). Under docs/ exist only the six standing
  buckets (_assets, decisions, handbooks, proposals, reports, specs) and
  per-issue trees docs/issue-<n>/ holding those same six buckets. Your
  record for a subject is docs/issue-<n>/reports/<role>.md; you write only
  your own record area, never another role's.
- A commit that stages any docs/issue-<n>/** work must use git commit -m
  and carry a Subject: issue-<n> trailer naming that issue (contract v3
  s13), one commit per subject — the same requirement trailer-gate.sh
  already enforces mechanically at commit time. Before committing, stage
  the full intended change set INCLUDING new files: git commit -a/-am
  only stages modifications to already-tracked paths, never untracked
  ones, so a newly created file needs an explicit git add of its path
  (or of the write set's directories, never a blanket git add -A/.) before
  commit — omitting this step leaves the new file out of the commit and
  produces "No commits between main and branch" at PR-create time.
- Headless/single-shot (no later turn for an async completion
  notification to land in): never end a turn having delegated work — any
  Agent/Task-style subagent dispatch, backgrounded or not — whose result
  you have not consumed within that same turn. Wait for it and act on it
  (through commit, where applicable) before the turn ends, or do not
  delegate that unit at all. This takes priority over any directive that
  mandates delegation, including freelunch's priority="absolute"
  directive (contract v3 s22).
- The board is what is MERGED to main. An open PR is not yet on the board;
  read other roles' state from main, not from open PRs.
- Your own record (contract §20) must state, in some accepted spelling: what
  was done ("what was done", "what i did", "## done", "work done", "summary
  of work" -- write a summary of work); why ("why", "rationale", "reason:");
  the upstream basis ("upstream", "based on", "basis:", a 7-40 char hex
  commit sha, or a
  docs/issue-<n> path); its own current kind: and loop_state: line; and open
  findings ("open findings", "open_findings", "open finding"). Whenever
  loop_state is non-terminal for your record's kind, also state next steps
  ("next steps", "next-steps", "next_steps") and an open-finding resolution
  path ("resolution path", "resolution-path", "resolution_path"). A `sha:`
  line's value must be exactly `same-commit` or a 40-character hex commit
  sha (issue-128/133) — never a bracketed placeholder.
- Terminal loop_state is per-kind, derived from contract §2, not one global
  list: `product-record`->`decided`/`scope-approved`; `coding-record`->
  `landed`; `qa-record`->`verified-fixed`/`not-a-defect`/`wont-fix`;
  `feasibility-record`->`verdict`; `ux-design-record`->`reviewed`;
  `review-record`->`reported`; `verify-record`->`cleared`; `ops-record`->
  `steady`; `reflect-record`->`round-done`. A repo may override a kind's
  terminal states via docs/specs/record-fields-terminal-states.json (a
  {kind: [states]} JSON object); a malformed or unrecognized entry in that
  file is refused loudly, never silently ignored.
- A commit that stages an operational-surface file — package.json,
  package-lock.json, pyproject.toml, requirements.txt, go.mod, Cargo.toml,
  Gemfile, Dockerfile, docker-compose.yml, .env, migrations/,
  .github/workflows/, or a deploy/setup/run/install script — is refused
  (contract §21) unless the same commit also touches a docs/handbooks/ file.
- A session that stages a change to any docs/specs/* file must also
  regenerate and stage docs/specs/reconciled-index.md (python3
  gates/spec_index.py --update) in the same commit, where the target repo
  ships that generator — a docs/specs/* commit must never leave the index
  stale.
- This build-now PR is the delivery PR: it must carry a
  Closes/Fixes/Resolves #<issue> trailer when it completes the issue, or
  Advances/Part of #<issue> when the delivery is intentionally partial —
  never neither.
- Verification is verify-at-landing (on-the-record #2137): a deliverable
  is code plus EXECUTED acceptance evidence — run every check the issue
  states at landing time and record the actual command and output in your
  record. Do not author new persistent test files by default; a durable
  harness is a deliverable only when the issue explicitly requires one.
  Any test output you do paste must be reported faithfully: never omit
  SKIPPED lines without acknowledging them, and a hand-typed pass count
  must equal the pasted summary count.
