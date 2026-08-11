# Survey — issue #854 (pr-preflight.sh phase-1 closing-keyword refusal never fired)

canonical: `on-the-record/hooks/pr-preflight.sh` (this branch's working
copy at survey time).

## Current hook shape

`on-the-record/hooks/pr-preflight.sh` is a `PreToolUse` hook matched on the
`Bash` tool. It only ever runs when Claude Code's own hook dispatcher hands
it a matching Bash-tool call — i.e. only inside a hooked Claude Code
session. It:

1. Reads stdin as `CG_PAYLOAD` (the PreToolUse JSON event).
2. Triggers on `\bgh\s+pr\s+(create|edit)\b` in `tool_input.command`.
3. Extracts the `--body`/`--body-file` value from the raw command string via
   regex (no real shell parser).
4. Determines `issue`/`role` from the current branch (`issue-<n>/<role>`),
   and `phase` from whether an exact `APPROVE issue-<n>/<role>` comment
   from a `docs/specs/approvers.md` account exists on the issue.
5. Runs `check_body()`, then, for `phase == "phase1"` only, a second check
   that exits 2 if the body carries a `Closes`/`Fixes`/`Resolves #<issue>`
   keyword — the issue #741 round-2 refusal this issue investigates.

## Finding 1 — both real incidents happened entirely outside the hook's reach

canonical: `gh api graphql` query, `pullRequest(number: 844) { body
userContentEdits(first: 10) { nodes { editedAt editor { login } } }
mergedAt mergedBy { login } }`, run this session.

The GraphQL `userContentEdits` field on PR #844 returns exactly two edits.

Both edits' `editor.login` is `jjongkwann` — the human account, not any
bot/agent login a role session posts under.

canonical: same GraphQL query result, this session.

Edit 1 (`2026-08-11T11:29:43Z`) is the creation; its body has no closing
keyword. Edit 2 (`2026-08-11T11:31:18Z`)'s `diff` field already ends in
`Closes #839`, appended after the original text.

canonical: same GraphQL query result (`mergedAt`, `mergedBy.login`
fields), this session.

`mergedAt` is `2026-08-11T11:31:22Z`; `mergedBy.login` is `jjongkwann` —
4 seconds after edit 2 above.

canonical: `on-the-record-issue-839-implementation.session.20260811T201002.61524.log`,
line 529 (`tool_input.command` field), read this session.

That line is the session's one and only `gh pr create` tool-call event for
PR #844. Its body text reads `Addresses #839 — phase 1 ...` — no closing
keyword anywhere.

canonical: driven-hook reproduction, this session (`bash
/tmp/pr-preflight-original.sh`, a pre-fix copy of this branch's hook at
`HEAD`, stub `gh` returning `issue_comments: []`, payload = line 529's
`tool_input.command`).

```
$ PATH="/tmp/fakebin:$PATH" GH_FIXTURES=/tmp/fixtures_phase1.json \
    bash /tmp/pr-preflight-original.sh < payload_real_create_no_closes.json
(no stderr) exit 0
```

The hook correctly allows this real command — it never had a closing
keyword to refuse.

canonical: `gh api repos/tokenmaxxxer/on-the-record/commits/febdf0b06f7a12e47490a629b74898675a21632b -q '.commit.message'`,
run this session.

PR #844's merge commit message itself carries no closing keyword
(`References issue 839, phase-1 only — not closing it yet.`).

canonical: same commit-message read, immediately above.

GitHub therefore closed #839 from the PR body's content at merge time,
not from the merge commit message text.

canonical: `grep -rn "gh pr edit\|gh pr create" /Users/jk/.tokenmaxxxer/work/*.log`,
run this session over every session log file present in that directory.

No `gh pr edit 844` call, and no `gh pr create`/`gh pr edit` call carrying
`Closes #839`, appears in either issue-839 session log or any other
session log under `/Users/jk/.tokenmaxxxer/work/`.

canonical: same grep output, immediately above.

The grep's only `gh pr edit` hit in the entire directory is `gh pr edit
240` in an issue-221 session log — unrelated to #839/#844.

canonical: `gh api graphql` (same query shape as PR #844's, above),
`pullRequest(number: 864)`, run this session.

PR #864 (issue #846's phase-1 PR, the issue's "세 번째 사례") shows the
identical shape: `author.login` and `mergedBy.login` are both
`jjongkwann`; two `userContentEdits`, both by `jjongkwann`
(`2026-08-11T12:54:22Z`, `2026-08-11T12:55:14Z`); the second edit's `diff`
already ends `...#846\n\n\nCloses #846`; `mergedAt` is
`2026-08-11T12:55:21Z` — 7 seconds after that edit.

canonical: `grep -rn "gh pr edit 864\|gh pr create.*864" /Users/jk/.tokenmaxxxer/work/on-the-record-issue-846-implementation.session.*.log`,
run this session over all three issue-846 session logs.

No `gh pr create`/`gh pr edit` call carrying `Closes #846` for PR #864
appears in any of the three issue-846 session logs.

canonical: Finding 1's own evidence, all paragraphs above (the two
GraphQL reads, the two session-log greps).

In both real-world recurrences, the `Closes #<issue>` text and the merge
itself came from the human account directly — never through a `gh pr
create`/`edit` Bash-tool call inside a hooked Claude Code session.
`pr-preflight.sh` only ever runs on a Bash-tool event Claude Code's own
dispatcher hands it; a PR-body edit made on github.com's web UI, or a
`gh`/API call run from a plain terminal with no `hooks.json` wired to it,
produces no such event. This rules out all three "남은 후보" in the issue
body (phase misjudged as phase2; `gh issue view` fail-open; a `hooks.json`
matcher miss) as the cause of these two incidents — none of that
hook-internal logic ever executed for either one.

canonical: `gh issue view 854 --comments`, read at the start of this
session (the issue's own posted control-group evidence, PRs #875/#879).

Control-group cross-check: PR #875 (issue-866 phase-1, plain `#866` only)
did not close #866 on merge; PR #879 (issue-866 phase-2, `Closes #866`)
did. GitHub's own auto-close mechanism behaves correctly on both — the gap
is specific to a body change made outside the hook's own reach.

## Finding 2 — an independent, reproducible bug in `--body` extraction

canonical: driven-hook reproduction, this session — `/tmp/pr-preflight-original.sh`
(pre-fix), stub `gh` (`issue_comments: []`), payload built from PR #844's
real body (Finding 1's line-529 command) turned into a `gh pr edit 844
--body ...` call with `Closes #839` appended after the body's existing
text.

Building this reproduction surfaced a second, independent defect,
unrelated to how PR #844's `Closes #839` actually got there.

canonical: `on-the-record/hooks/pr-preflight.sh` at `HEAD` (pre-fix line
53), read this session.

The pre-fix `--body` regex, `r"--body(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)"`,
is a naive quote-balance match: for a double-quoted argument it stops at
the first unescaped `"` character — it does not parse shell syntax.

canonical: the same line-529 command text, inspected directly this
session.

The dominant real-world shape for every `gh pr create`/`gh pr edit` call
sampled (issue-839's, issue-846's, and others) is `--body "$(cat <<'EOF'
...body... EOF)"`. Bash parses this correctly via the heredoc's own
delimiter lines, but the regex above has no concept of `$(...)` or
heredocs.

canonical: same command text, immediately above.

PR #844's real body contains an unescaped `"` mid-way through: `... not
"무리" (impractical) ...`.

```
$ PATH="/tmp/fakebin:$PATH" GH_FIXTURES=/tmp/fixtures_phase1.json \
    bash /tmp/pr-preflight-original.sh < payload_real_edit_with_closes.json
(no stderr) exit 0
```

canonical: direct regex trace against the same command text
(`re.search(...).group(1)`, length/content inspected), run this session.

The pre-fix hook allows the command above — it should deny it (phase1,
body genuinely contains `Closes #839`, 154 characters after the `"무리"`
quote). The captured `--body` value is 1207 characters, ending right
before `"무리"` — 1044 characters short of the real 2251-character
command, never reaching `Closes #839`.

canonical: the issue #854 body's own "이미 배제된 원인 2" section, read at
the start of this session.

This is why that check did not catch the defect: it ran the regex against
a short reconstructed body (`Addresses #839 — phase 1.\n\nCloses #839`)
with no embedded quote character, which the regex handles fine — it was
never run against a body containing one.

canonical: Finding 1 above (no `gh pr edit`/`create` call for either
incident ever carried a closing keyword through the Bash tool).

This bug is independent of Finding 1 — it did not cause either real
incident — but it is a live gap in the exact code path this issue
investigates: a future in-session `gh pr create`/`edit` call carrying a
heredoc body with an embedded quote before `Closes #<issue>` would
silently defeat the phase-1 refusal too.

## Finding 3 — fail-open was not the cause

canonical: Finding 1's session-log greps (no `gh` invocation failure
appears around either incident) and Finding 1's driven-hook reproduction
(the one in-session `gh pr create` call for issue-839 completed with a
correct `exit 0`, meaning its own internal `gh issue view` lookup
succeeded).

`sys.exit(0)` on `gh issue view ... --json comments` returning `None` is
reachable only when a `gh` invocation the hook itself makes fails. Neither
incident involved the hook running at all, so this fail-open branch is not
implicated in either real recurrence. The proposal's `## Rationale`
records the keep/change decision on this policy anyway, since the issue
explicitly asks for one.

## Sources consulted

- `gh issue view 854 --json body,comments`
- `gh pr view 844 --json title,body,url,mergedAt,mergedBy,author,mergeCommit`
- `gh api graphql` (PR #844 and PR #864 `userContentEdits`)
- `gh api repos/tokenmaxxxer/on-the-record/commits/<merge-sha>`
- `git log --all --grep=839 --oneline`
- Session logs: `on-the-record-issue-839-implementation.session.20260811T{201002,203353}.*.log`;
  `on-the-record-issue-846-implementation.session.20260811T{211647,215554,221346}.*.log`
- `on-the-record/hooks/pr-preflight.sh`, `on-the-record/hooks/approval-gate.sh`
  (current working-copy read, this branch)
- `docs/issue-876/reports/implementation/resolution.md` (precedent for a
  phase-1 session landing a hook-script fix directly in the same PR)

## Skip condition

This is a pure bugfix (Finding 2: the `--body` extraction regex is not
shell-aware for the dominant real-world heredoc idiom) discovered through
reproduction, not a new feature or product surface — the scout-directive's
sweep/deepening protocol is skipped per its own "pure bugfix" exemption.
No exemplar research applies to a regex parsing defect in an internal
`PreToolUse` hook.
