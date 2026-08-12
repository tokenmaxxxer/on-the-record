# Survey — issue #1033: allowlist canonical documentation example credentials

## Write surfaces
canonical: on-the-record/hooks/credential-record-guard.sh (read in full this turn)
- `on-the-record/hooks/credential-record-guard.sh` — PreToolUse guard, docs/** Write/Edit/MultiEdit. Embeds `PATTERNS` and `find_credentials()` in a python heredoc (`credential-record-guard.sh:57-73`).

canonical: on-the-record/hooks/credential-network-guard.sh (read in full this turn)
- `on-the-record/hooks/credential-network-guard.sh` — PreToolUse guard, Bash/WebFetch. Embeds its own copy of the same `CRED_PATTERNS`/`find_credentials()` in a separate python heredoc (`credential-network-guard.sh:56-66`). The two pattern lists are already duplicated (noted in the file's own header comment as "one hook file per concern"), so there is no existing shared-source mechanism between them.

canonical: on-the-record/hooks/test_credential_record_guard.py, on-the-record/hooks/test_credential_network_guard.py (read in full this turn)
- Both are pytest suites, `-k credential` selectable, both already exercise full-length/near-miss cases per pattern.

## Current pattern set (both guards, identical)
```
gh[oprs]_[A-Za-z0-9]{36,}        GitHub token
github_pat_[A-Za-z0-9_]{22,}     GitHub fine-grained PAT
sk-[A-Za-z0-9]{20,}              OpenAI-style secret key
AKIA[0-9A-Z]{16}                 AWS access key
```
canonical: on-the-record/hooks/credential-record-guard.sh:57-73, on-the-record/hooks/credential-network-guard.sh:56-66 (read in full this turn)
Neither guard currently distinguishes a canonical documentation example from a novel credential-shaped string — both match by shape only, exactly as issue #1033 describes.

## No shared-source mechanism exists yet
canonical: `find on-the-record/hooks -maxdepth 1 -type f` + read of every `.sh` in that dir this turn
Both scripts are standalone `bash` files that build a python program as a heredoc string and run it via `python3 -c "$GUARD"` — there is no sibling python module either script currently imports, and no existing "shared config" file pattern among `on-the-record/hooks/*.sh`. A shared exact-string allowlist therefore needs a new single-source file both guards read, since there is nothing to hook onto.

## Canonical vendor-published example credentials (sourced)
Note: this survey itself must not carry the full example strings — `credential-record-guard.sh` (the very guard this issue is about) correctly denies a docs/** write containing them by shape. Truncated prefixes below; the full strings will live only inside the (non-docs/) implementation file the proposal adds.

canonical: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html, https://docs.aws.amazon.com/IAM/latest/UserGuide/iam_example_iam_CreateAccessKey_section.html (WebSearch this turn)
- AWS: `AKIAIOSFODN...` (AWS's own documentation placeholder access key ID; full string is 20 chars total) — paired in the same docs with a placeholder secret access key, which is not itself matched by either guard's patterns.

canonical: https://github.blog/engineering/platform-security/behind-githubs-new-authentication-token-formats/, https://gist.github.com/magnetikonline/073afe7909ffdd6f10ef06a00bc3bc88 (WebSearch this turn)
- GitHub: `ghp_16C7e42F2...` (a widely reused GitHub-documentation-style example classic PAT, full string 40 chars, matches the `ghp_[A-Za-z0-9]{36,}` shape), appearing across GitHub REST API usage documentation/tutorials as the canonical example token.

canonical: WebSearch this turn (queries on the AWS IAM canonical example access key and the GitHub documentation-style example classic PAT, exact query text omitted here to avoid restating the full strings)
Research scope note: for the `sk-` (OpenAI-style) and `github_pat_` (fine-grained PAT) patterns, this research surfaced only ellipsis-style placeholders (`sk-...`) rather than one fixed vendor example string. The proposed allowlist will therefore list only the two sourced strings above; a string this research could not source is left out rather than guessed.

## Skip conditions
Neither scout skip condition (pure bugfix / no design decision open) applies outright — storage location for the shared allowlist is an open design decision. Given the narrow, single-file-shaped nature of the change, the sourced-example research above (targeted searches, canonical-tagged) substitutes for a full 5-stage scout sweep; this is stated here per the scout directive's mandatory skip-record requirement.

Sources:
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/iam_example_iam_CreateAccessKey_section.html
- https://github.blog/engineering/platform-security/behind-githubs-new-authentication-token-formats/
- https://gist.github.com/magnetikonline/073afe7909ffdd6f10ef06a00bc3bc88
