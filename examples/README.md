# Examples

Last verified: 2026-11-07

Every file here is a standalone illustration written for this showcase.
None is copied from the private platform, and none is configuration from the live environment.
The example code is licensed under the [MIT License](../LICENSE-CODE).

| Example | What it illustrates |
| --- | --- |
| [`verdict-policy/`](verdict-policy/) | The deterministic decision that turns a model's review into a required status, with tests. CI runs them. |
| [`review-result.schema.json`](review-result.schema.json) | The contract a model's review must satisfy before the controller will consider it. |
| [`review-result.example.json`](review-result.example.json) | A synthetic review result that the verdict policy fails because of a P1 finding. |
| [`github/ruleset-protected-main.json`](github/ruleset-protected-main.json) | A repository ruleset with no bypass actors, strict freshness, and each required check pinned to the identity allowed to produce it. |
| [`tickets/ticket-template.md`](tickets/ticket-template.md) | The eight-section ticket contract that admission checks. |

In the ruleset, `15368` is GitHub Actions' public integration ID, so the `validate` check can only be satisfied by a GitHub Actions run.
`1000001` is a placeholder for the reviewer App's integration ID; use your own App's ID.
Pinning is what stops another identity with status-write access from posting a `success` under the same context name.

To run the example tests:

```bash
python3 -m unittest discover -s examples/verdict-policy -p 'test_*.py'
```
