# Engineering decisions

Last verified: 2026-11-07

These are six decisions that shaped the platform, written up because the reasoning matters more than the component list.
Two of them reverse an earlier choice, and every one of them has a cost that is still being paid.

Each follows the same shape: the problem, the first approach, what we learned, the decision, the trade-off, and the result.

| # | Decision | Date | Outcome |
| --- | --- | --- | --- |
| 1 | [Separate the implementer from the reviewer](01-separate-implementer-and-reviewer.md) | 2026-08-13 to 2026-10-29 | Implemented |
| 2 | [Brokered, short-lived credentials](02-brokered-short-lived-credentials.md) | 2026-10-06 to 2026-10-13 | Implemented, with a stated residual risk |
| 3 | [Deterministic controls around model judgment](03-deterministic-controls-around-model-judgment.md) | 2026-08-13 onward | Implemented |
| 4 | [Auto-merge without human approval](04-auto-merge-without-human-approval.md) | 2026-10-29 to 2026-11-01 | Implemented after reversing a control I had just built |
| 5 | [Different CI security models for public and private repositories](05-public-and-private-ci-security-models.md) | 2026-10-27 to 2026-10-28 | Implemented, one control is time-limited |
| 6 | [Anchor the review gate to the head commit](06-anchor-the-gate-to-the-head-commit.md) | 2026-08-14 | Implemented, after the first design failed against real merges |
