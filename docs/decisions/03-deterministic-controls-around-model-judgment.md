# Decision 3: deterministic controls around model judgment

Last verified: 2026-11-07

## Problem

A language model's review is nondeterministic, can be influenced by the text it reads, and can be confidently wrong.
If the model's own output decided whether a change may merge, every one of those properties would flow straight into the merge gate.

## Initial approach

The reviewer always separated the model's proposal from a controller's decision, and always forbade executing pull-request code.
What took longer to learn was how many other places a model-shaped failure could slip through as if it were a result.

## What we learned

Several failures were not the model being wrong about code.
They were the system around the model quietly believing something it had not checked:

- **Settings that fail validation are silently ignored** by the CLI in non-interactive mode. A tool restriction that failed to apply would have given the model tools it was never meant to have, with no error. The controller now reads the session's initialization event and refuses to continue unless the registered tool set is exactly what it expects.
- **The model was not seeing what we thought it saw.** The CLI replaces any tool result over 50,000 characters with a short preview and a file path the reviewer had no tool to open. When this was measured on 2026-09-17, 616 of 656 recorded reviewer sessions contained at least one elided result. Responses are now bounded below the threshold in the server itself, and a preview arriving anyway ends the run as an error.
- **A nondeterministic model asked often enough will eventually pass anything.** Attempts per change are capped, operator-ordered re-reviews are capped at two and recorded, and infrastructure failures that happen before the model runs are refunded rather than spent, so outages cannot burn the cap.
- **Delivering evidence is not the same as the model reading it.** In September 2026, after the controller had proved a pull request was an exact rollback, the review still reported the restored code as three new regressions because the model never opened the proof. The controller now checks its record of what the model actually read and discards a result formed without it.

## Decision

The model proposes; deterministic code decides, and anything the controller cannot verify is an error, never a pass:

- the result must validate against a schema;
- any P1 or P2 finding, any non-`PASS` verdict, or confidence below 0.80 fails the gate;
- timeouts, exhausted budgets, malformed output and elided evidence are errors;
- the published payload is scanned for secrets before it is stored or sent;
- whether the change is still the one reviewed is checked against GitHub immediately before publishing.

The controller can lower a model's blocking finding in exactly one case: when a deterministic proof shows the pull request is an exact rollback, the finding is in a restored file, and the model tagged it as restored baseline.
Even then, the finding is lowered and never removed.

## Trade-off

- The controller cannot tell a correct P1 from a wrong one. In the audited month half of the blocking findings were false positives, and the deterministic policy blocked on all of them. Authors are expected to rebut with an executed check and request a re-review, not to write code that placates the model.
- Strictness costs availability. After the service cutover, 19% of runs ended in error, mostly during two infrastructure incidents, and each error is time a pull request cannot merge.

## Result

No pull request has merged without a successful authoritative review in the audited period, and the reviewer's failures show up as errors or blocks rather than as silent passes.
Its accuracy is a separate, measured problem, with false-positive reduction named as the next investment if the rate does not fall.
