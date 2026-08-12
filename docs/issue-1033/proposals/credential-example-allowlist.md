---
status: proposed
files:
  - on-the-record/hooks/credential-example-allowlist.py
  - on-the-record/hooks/credential-record-guard.sh
  - on-the-record/hooks/credential-network-guard.sh
  - on-the-record/hooks/test_credential_record_guard.py
  - on-the-record/hooks/test_credential_network_guard.py
---

## Request
Issue #1033: `credential-record-guard.sh` and `credential-network-guard.sh` block by shape only, so a vendor-published canonical documentation *example* credential (e.g. AWS's AKIA-prefixed IAM example key, GitHub's documentation-style example classic PAT) trips the same guard as a real leaked secret, forcing awkward `[REDACTED]`-rewrites of legitimate security-teaching material. Add an exact-string allowlist of such canonical examples, shared by both guards from one source, with no loosening of the shape patterns themselves — a novel credential-shaped string must still block. Requirement linkage: R001 (the guard is the standing security invariant and must not be weakened).

## Constraints
- Exact-string match only — the allowlist entries are compared as literal strings against the regex match span, never folded into the regex patterns themselves or matched by prefix/substring.
- Single source shared by both guards — no independent copy of the allowlist per guard (mirrors the existing duplicated-pattern-list problem this issue implicitly flags: the two guards already re-embed identical `PATTERNS`/`CRED_PATTERNS` lists, and this proposal does not make that worse by adding a third divergence point).
- No pattern-level loosening: the four shape regexes (`gh[oprs]_...`, `github_pat_...`, `sk-...`, `AKIA...`) are untouched. A string that merely resembles an example (e.g. differs by one character) still blocks.
- Only credentials actually sourced to a vendor's own published documentation are added (survey: AWS's `AKIAIOSFODN...` example access key ID, GitHub's `ghp_16C7e42F2...` example classic PAT — both confirmed via web search this session, `docs/issue-1033/reports/implementation/survey.md`). No guessed or synthesized "example-looking" strings are added for `sk-` or `github_pat_`, since no canonical vendor example was found for either.

## Rationale
Two storage shapes were considered for the shared allowlist:
1. **A new shared Python module** (`credential-example-allowlist.py`) that both guards' python heredocs import by inserting its directory onto `sys.path` (the guard's own script directory, resolved via an env var the wrapping bash passes in) — **chosen**. Keeps the allowlist as executable Python (a `frozenset` of strings), which is exactly the shape `find_credentials()` in both guards already needs to check membership against, and needs no new parsing logic in either heredoc.
2. **A plain-text/JSON sidecar file** read via `open()` — **rejected**. It would work equally well functionally, but every other piece of shared state in `on-the-record/hooks/` that guards read at runtime (patterns, thresholds) is Python literal data embedded in code, not an external data file with its own parse step; introducing a new file format for one guard pair adds a second convention with no offsetting benefit, since the allowlist is committed alongside the guards anyway and gets no runtime-editability benefit from being data instead of code.

## What will be done
- Add `on-the-record/hooks/credential-example-allowlist.py`: a module exposing `EXAMPLE_ALLOWLIST` (a `frozenset[str]`) containing the two sourced canonical example strings (AWS IAM example access key ID, GitHub example classic PAT), with a comment citing where each was sourced from.
- In both `credential-record-guard.sh`'s and `credential-network-guard.sh`'s python heredocs: before running, the wrapping bash sets an env var (`CRG_HOOKS_DIR` / `CNG_HOOKS_DIR`) to the guard's own script directory (`$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)`); the heredoc inserts that directory onto `sys.path` and does `from credential_example_allowlist import EXAMPLE_ALLOWLIST` (module file named with underscores for import validity; the on-disk guard-facing name can stay hyphenated only if Python import requires underscores — using `credential_example_allowlist.py` as the actual file name to import cleanly, referenced as such in `files:` above).
- In each guard's `find_credentials()`, skip a match whose exact matched text (`m.group(0)`) is a member of `EXAMPLE_ALLOWLIST`, before appending it to `hits`.
- Add one acceptance test per guard: the canonical example string passes (`returncode == 0`), and a novel AKIA-shaped string (already covered by an existing test) continues to block — confirming no shape-level loosening.
- Run `python3 -m pytest on-the-record/hooks/ -k credential` and confirm a clean pass before calling the work done.

## Out of scope
- Adding allowlist entries for `sk-` or `github_pat_` shapes (no sourced canonical vendor example found this session).
- Any allowlist entry sourced from anywhere other than the vendor's own published documentation (e.g. no StackOverflow-popular example strings).
- Changing the `[REDACTED]`/short-truncated-prefix escape hatches already in `credential-record-guard.sh` — those are untouched.
- Any change to `credential-network-guard.sh`'s command/network-detection logic beyond the same allowlist skip.

## How you'll know it worked
`python3 -m pytest on-the-record/hooks/ -k credential` passes, including two new cases: the canonical AWS example key content passes both guards' Write/Bash-shaped inputs, and a novel AKIA-shaped string (16 different suffix chars) still returns exit code 2 from both.
