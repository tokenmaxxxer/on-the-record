# Deviation log — issue-2219 (implementation role)

- 2026-08-25T00:00:00Z | inline | warrant-protocol calls for a background warrant-hunter after-proposal and before-landing; this session used the CORE_BUILD_NOW=1 bypass (no proposal round) and pushed + opened PR #2246 before dispatching the before-landing hunt, running it after landing instead — dispatched retroactively against commit ff1de0b7 as a post-hoc safety check rather than a true before-landing gate.
