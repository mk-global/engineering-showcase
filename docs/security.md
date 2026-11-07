# Security philosophy and disclosure boundaries

Last verified: 2026-11-07

## Security philosophy

A handful of principles show up on almost every page of this showcase, so here they are in one place.

**Authority is narrow, short-lived and held by the right identity.**
The coding agent, the reviewer, the credential broker, the CI runners and the founder are separate identities, each with a written list of what it may never do, enforced by the operating system, GitHub or the broker rather than by convention.

**Failure is refusal.**
When a credential, a check or a dependency is unavailable, the system stops.
It never falls back to a broader credential, never treats "could not verify" as "verified", and never publishes a pass it could not justify.

**A model proposes; deterministic code decides.**
Model output is untrusted data, whether it is a code review or text inside a pull request.
Every decision that gates a merge or grants access is made by code whose behavior can be read and tested.

**Evidence is anchored to exact commits.**
A review, a test result or a deployment is about one immutable commit, and the platform checks that the thing merging or deploying is still that commit.

**A habit is not a control.**
If something matters, GitHub, the operating system or a test enforces it.
Several of the [decisions](decisions/README.md) started as an audit that found a protection which existed only because someone always did the right thing.

**Limits are stated.**
Every component page ends with what the component does not protect against.
A security claim without its boundary is not a claim I'm willing to make.

## What this repository publishes

The goal is real technical depth without making the private environment easier to attack.

Published:

- the architecture, the trust boundaries, and which identity holds which authority;
- interfaces and contracts, such as the ticket contract, the reviewer's output schema and the broker's protocol shape;
- design decisions, rejected approaches and their reasons;
- how each control is verified, and aggregate measurements with their method and date;
- the known limitations and residual risks.

## What this repository deliberately leaves out

| Category | Why it is withheld |
| --- | --- |
| Credential and key locations, file names and permissions on the live machine | They tell an attacker with local access exactly where to look |
| Local account names, user and group IDs, service labels, socket paths and local endpoints | They map the live installation without adding to anyone's understanding of the design |
| GitHub App, installation, ruleset and team identifiers | They identify live configuration that the explanation does not need |
| Exact limits that guard an access path, such as the broker's rate limits | Knowing the precise threshold helps someone stay just under it |
| Names of private repositories and products, and private ticket and pull-request numbers | Private projects are not mine alone to disclose, and the numbers cannot be followed by a visitor anyway |
| The platform's source code, logs, screenshots and raw evidence | Source carries operational detail throughout; raw evidence can carry identifiers and data |
| Hardware specifics and the identity of the local model | Not needed to understand the design, and the reviewer deliberately records no model identity |

Some of the reviewer's design bounds, such as running one review at a time and capping re-reviews, are published, because they explain the design and guard no access path.

Where a concrete example helps, the repository uses a synthetic one written for this purpose and labeled as illustrative.
Nothing under [`examples/`](../examples/README.md) is copied from the private platform.

CreatorBrio is the one product named, because its repository is public and its governance is already visible on GitHub.

Before publication, every page went through deterministic scans: secret patterns, absolute paths, and a private list of names and identifiers that must not appear, kept outside this repository because the list itself would disclose them.
Every page was also read line by line against the categories above, and then reviewed in a fresh context that had not seen the drafting decisions.
That second review found an overstated independence claim, settings described as enabled before they could be, and a misattributed audit figure, all corrected before publication.
Both reads were AI-assisted, so they were treated as evidence, not as proof that a disclosure is safe.

## How this repository is protected

This is a public, documentation-first repository, and it is governed under the platform's [public-repository model](decisions/05-public-and-private-ci-security-models.md):

- the default branch has a ruleset with no bypass actors that refuses deletion and force-pushes, requires a pull request, and requires two checks with strict freshness: this repository's CI, pinned to GitHub Actions, and the independent reviewer's context, pinned to the reviewer App;
- every pull request must close an open ticket in this repository whose body passes the ticket contract, which the reviewer enforces;
- CI runs only on GitHub-hosted runners, with a read-only token, no secrets, every action pinned to a full commit SHA, and only GitHub-owned actions allowed;
- workflows cannot approve pull requests, and workflow runs from outside contributors need approval;
- pull-request creation is restricted to collaborators, and interactions are limited to collaborators, so strangers cannot fill the shared review queue;
- secret scanning and push protection are enabled;
- the engineering App is not installed here. Changes are made from the founder's session and reviewed by the independent reviewer like any other.

## Reporting a vulnerability

See [`SECURITY.md`](../SECURITY.md).
