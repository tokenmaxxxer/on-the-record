# Shared exact-string allowlist of vendor-published canonical documentation
# example credentials (issue #1033). Both credential-record-guard.sh and
# credential-network-guard.sh import this so a legitimate security-teaching
# example (e.g. this repo's own docs explaining what these guards catch)
# does not trip the same guard as a real leaked secret.
#
# Exact-string match ONLY — never fold these into the shape regexes and
# never match by prefix/substring. A string that merely resembles one of
# these by one character still blocks.
#
# Sources (docs/issue-1033/reports/implementation/survey.md):
# - AWS IAM example access key ID, from AWS's own documentation
#   (docs.aws.amazon.com IAM examples use this exact placeholder key).
AWS_EXAMPLE_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"

# - GitHub's documented example classic PAT, from GitHub's own docs
#   (docs.github.com authentication docs use this exact placeholder token).
GITHUB_EXAMPLE_CLASSIC_PAT = "ghp_16C7e42F292c6912E7710c838347Ae178B4a"

EXAMPLE_ALLOWLIST = frozenset({
    AWS_EXAMPLE_ACCESS_KEY_ID,
    GITHUB_EXAMPLE_CLASSIC_PAT,
})
