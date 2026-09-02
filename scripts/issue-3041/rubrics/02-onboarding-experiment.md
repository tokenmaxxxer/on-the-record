A strong answer:
- Names a single primary metric with a concrete numeric threshold, fixed before data collection (not "we'll see how it looks").
- States the decision rule mechanically: what result counts as ship, what counts as don't-ship, decided in advance rather than left to post-hoc judgment.
- States a sample size and/or run duration needed to reach a trustworthy read.
- Names at least one guardrail metric with a bounded acceptable-degradation limit, not just a bare metric name with no bound.
- Treats a primary-metric win alongside a breached guardrail as a breach/no-ship rather than an unqualified win.
