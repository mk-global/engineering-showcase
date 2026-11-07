# Contributing and maintenance

Last verified: 2026-11-07

This is a personal portfolio of a private system, so pull requests are limited to collaborators.
If you have a question or spot an error, the profile links in the [README](README.md#about-me) are the best way to reach me, and anything security-related belongs in a [private report](SECURITY.md).

The rest of this page is the process I follow to keep the showcase accurate, safe and current.

## How a change is made

Every change goes through the same governed path as the platform it describes:

1. **Ticket.** Open an issue using the architecture-update template. It must contain the eight sections of the ticket contract (Problem, Desired Outcome, Scope, Out of Scope, Acceptance Criteria, Verification, Dependencies / Blockers, Risks / Constraints), because the independent reviewer refuses a pull request whose linked ticket does not.
2. **Branch and pull request.** One coherent change per pull request, with `Closes #<n>` naming the ticket in the same repository.
3. **CI.** The `validate` check runs on a GitHub-hosted runner: Markdown lint, internal links and anchors, rendering of every Mermaid diagram, the required page structure and `Last verified` lines, the example tests, style rules, generic disclosure patterns and a secret scan of the branch's history.
4. **Independent review.** The local AI reviewer reviews the exact head against the ticket's scope. Its status is required, and only its own identity can satisfy it.
5. **Merge.** GitHub's native auto-merge merges once both required checks are green at the exact head and the branch is up to date. There is no manual approval step.

## Accuracy check

Before a change is opened, every claim it adds or changes is checked against the running system, not against documentation, memo or memory:

- a capability's status must match the [status labels](README.md#status-labels), and anything not built is labeled Planned;
- a number must come from a measurement with a date, sample and method, and is added beside older measurements rather than replacing them;
- the [evidence index](docs/evidence/README.md) changes in the same pull request as the page whose claim it supports;
- a page's `Last verified` date moves only when its claims were re-checked.

The [evidence freshness convention](docs/evidence/README.md#evidence-freshness-convention) says what happens when a page goes stale.

## Disclosure check

Public text must not make the private environment easier to attack.
Before opening a pull request:

- run the private denylist scan, which is kept outside this repository because the list itself names private systems;
- read the diff against the categories in [what this repository leaves out](docs/security.md#what-this-repository-deliberately-leaves-out);
- write any concrete example as a synthetic illustration, never as edited live configuration;
- remember that a pull request branch on a public repository is public the moment it is pushed, so the check covers every commit on the branch, not only the final diff.

CI's disclosure check catches generic patterns only, such as absolute home paths, private keys and token shapes.
It is a backstop, not the review.
AI review is not evidence that a disclosure is safe.

## Writing style

Sentence-case headings, one sentence per line in the Markdown source, plain words, no em dashes, no curly quotes.
The mechanical rules are checked by CI.
