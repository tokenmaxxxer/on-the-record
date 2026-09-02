A strong answer:
- Checks whether assignment was actually randomized and whether the two groups came out balanced (a sample-ratio-mismatch-style check), not just accepting the reported split.
- Checks whether the test/measurement platform itself has been validated (e.g. an A/A-style sanity check), not only the one result in question.
- Checks whether the design (metric, threshold, stopping rule) was fixed before the result came in, or whether the test was stopped/interpreted after seeing a surprising number (peeking).
- Treats an unusually large, surprising win with extra skepticism rather than at face value, and asks what could produce this number besides a real effect (novelty, bug, seasonality, external event).
- Gives a concrete recommendation (e.g. hold the rollout pending specific checks) rather than a vague "seems fine" or "seems risky."
