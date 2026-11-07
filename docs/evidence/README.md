# Evidence and status

Last verified: 2026-11-07

This page links each main claim in the showcase to how it was verified.
The platform's source and its tickets are private, so visitors cannot follow the evidence to its origin.
What they can check is the method: what was run or read, when, and what it would and would not reveal.

## How to read this page

- **Status** uses the labels defined in the [README](../../README.md#status-labels).
- **Verified by** names the kind of evidence: an automated test suite, a live read of GitHub configuration, a live run recorded on the change's ticket, or a measurement with its method.
- **Last verified** is the date the evidence was last checked against the running system, not the date the feature was built.

### Evidence freshness convention

A showcase like this decays quietly: a page written in November reads as current in March unless something says otherwise.
So:

1. Every page starts with a `Last verified: YYYY-MM-DD` line, and CI refuses a page without one.
2. A page's date moves only when its claims were re-checked against the running system, never when only wording changed.
3. CI warns when a page is more than 120 days old. A stale page must be re-verified, or its claims must be rewritten in the past tense as a historical snapshot.
4. Measured figures always carry their measurement date and sample, and are never updated in place. A new measurement is added beside the old one.
5. When a capability changes status, its row here changes in the same pull request as the page that describes it.

## Evidence index

All rows were last verified on 2026-11-07.

| Capability | Status | Verified by | Test or CI evidence | Decision | Observed outcome | Known limitations |
| --- | --- | --- | --- | --- | --- | --- |
| Ticket admission recomputed from the current body | Implemented | Test suite; released immutable version | 35 ticket and pull-request policy tests pass; shared parser vectors with the reviewer | [Lifecycle](../workflows/delivery-lifecycle.md#ticket-driven-work) | Labels admit nothing; an edited ticket is re-judged at the next check | Admission checks structure, not whether the work is wise |
| Isolated, headless engineering agent account | Implemented | Test suite plus live isolation proof recorded on each change's ticket | 74 isolation-check tests and 14 shell-launcher tests pass | [Decision 2](../decisions/02-brokered-short-lived-credentials.md) | Latest live proof from inside the account: 82 probes passed, none failed or unverified (2026-11-05) | A user account is not a VM; covers known credential locations only |
| One-repository, per-command GitHub tokens | Implemented | Test suite against a fake GitHub that verifies JWTs independently | 67 client tests pass | [Decision 2](../decisions/02-brokered-short-lived-credentials.md) | No command can print a token; tokens revoked after each command | A token is a bearer credential for its short life |
| Key broker holding the only App key | Implemented since 2026-10-13 | Test suite on a real Unix socket; activation verified on its ticket | 78 broker tests pass | [Decision 2](../decisions/02-brokered-short-lived-credentials.md) | Agent cannot read the key; refusal when the broker is down | No per-session repository isolation |
| Independent reviewer: containment, exact-commit identity, deterministic verdict | Implemented | Test suite; startup self-checks; live ruleset reads | 1,128 reviewer tests pass | [Decisions 1, 3, 6](../decisions/README.md) | See the audit below | Never executes code; model judgment fallible; not OS network-confined |
| Reviewer as a dedicated system service from sealed releases | Implemented since 2026-10-29 | Live service configuration read on 2026-11-07: the active release was built from the main commit | Release install runs the full suite in place | [Decision 1](../decisions/01-separate-implementer-and-reviewer.md) | Founder sessions cannot rewrite the running gate | Trusts an unauthenticated local model endpoint (open risk) |
| Pinned, strict required checks with no bypass | Implemented | Live read of effective branch rules on governed repositories | Not applicable | [Decision 6](../decisions/06-anchor-the-gate-to-the-head-commit.md) | A foreign `success` under the reviewer's context does not satisfy the rule (verified live) | Relies on repository settings staying correct; the reviewer re-reads them before publishing |
| Auto-merge with no human approval on the platform repository | Implemented since 2026-11-01 | Live rule-suite evaluation of the first merge after the change | Not applicable | [Decision 4](../decisions/04-auto-merge-without-human-approval.md) | Merged with no approval event and only the main ruleset evaluated | Reviewer becomes the only independent semantic check |
| Runner classes with disjoint selectors | Implemented | Runner-policy test suite; organization audit | 71 runner-policy tests pass | [Lifecycle](../workflows/delivery-lifecycle.md#ci-runners-and-workload-separation) | By construction, a policy check cannot be handed to an application runner | Persistent runners are not a boundary against hostile repository code |
| Versioned, SHA-pinned governance components | Implemented | Release tags; consumers' pins checked by the product standard | 62 product-standard tests pass | [Lifecycle](../workflows/delivery-lifecycle.md#shared-governance-components) | Central changes reach a repository only when it moves its pin | Pins must be moved deliberately, so fixes propagate slowly |
| Organization onboarding and audit | Implemented | Test suite against a fake GitHub; operator-run live audit | 52 onboarding tests pass | [Decision 5](../decisions/05-public-and-private-ci-security-models.md) | Audit compares declared and live state in both directions | Needs organization-admin credentials, so it runs from an operator session, not CI |
| Public-repository category | Implemented | Organization audit; live settings reads | Covered by the onboarding tests | [Decision 5](../decisions/05-public-and-private-ci-security-models.md) | Public repositories cannot reach private runners | Some public-repository protections are time-limited and must be renewed |
| Staging adapter: exact-commit deploy and backend identity check | Partially implemented | Test suite against a fake hosting API and a fake served site | 39 adapter tests pass | [Lifecycle](../workflows/delivery-lifecycle.md#staging) | Not yet the path any product deploys through | Reusable workflow not released; provider behaviors unverified until a live run |
| Overnight repository auditor | Experimental | Built with its own tests; not re-run for this page | Not summarized here | Not applicable | Not evaluated here | No measurement of its findings' quality |
| Founder-bound production promotion, release candidates, rollback drills | Planned | Not applicable | None | [Lifecycle](../workflows/delivery-lifecycle.md#production-promotion-and-rollback) | Not built | |
| Isolated execution worker for container jobs | Planned | Not applicable | None | [Roadmap](../roadmap.md) | Not built | |
| Merge-commit-anchored review gate | Superseded 2026-08-14 | Real merge attempts | Not applicable | [Decision 6](../decisions/06-anchor-the-gate-to-the-head-commit.md) | Livelocked against GitHub's merge behavior | |
| App key in the agent's own account | Superseded 2026-10-13 | Not applicable | Not applicable | [Decision 2](../decisions/02-brokered-short-lived-credentials.md) | Replaced by the broker, with key rotation | |
| Founder-only approval for reserved paths | Superseded 2026-11-01 | Ruleset definition recorded before deletion | Not applicable | [Decision 4](../decisions/04-auto-merge-without-human-approval.md) | Removed by founder decision | |

Test counts are from runs of each suite at the platform's main commit on 2026-11-07, before this repository's own onboarding change.
Every suite listed passed; none was skipped.

## Reviewer audit, 2026-11-01

This is the only effectiveness measurement of the reviewer, and it is a point-in-time audit, not a running metric.

**Method.**
The population for effectiveness was every blocking or inconclusive verdict from 2026-10-01 to 2026-11-01 in the repositories that could be read: 16 `CHANGES_REQUIRED` verdicts carrying 18 P1 or P2 findings, plus 3 inconclusive verdicts, out of about 270 pull requests with a settled verdict.
For each verdict, one auditor read the code at the reviewed head, the later commits, the discussion and CI.
An independent skeptic then tried to refute each classification and agreed with all 18 findings and all 3 inconclusive assessments.
A later change or a later pass was not accepted as proof of validity.
Performance was measured on the 30 most recently merged pull requests into branches where the reviewer is required, spanning 2026-10-30 to 2026-11-01.

**Effectiveness.**

| Measure | Result |
| --- | --- |
| P1 and P2 findings valid | 7 of 18 |
| Partially valid | 2 of 18 |
| False positive | 9 of 18 |
| Real findings also caught by tests or CI | 0 of 9 |
| Material real findings | 2 of about 270 reviewed pull requests, both application code; one at a database-permission boundary the tests had mocked |
| Low-impact real findings | 7, in documentation, runbooks and scripts |
| False positives that still forced a code change to pass | 4 purely placating, 1 mixed |
| Inconclusive verdicts | 3: two ran out of reading budget on 64- and 141-file changes, one passed at 0.75 confidence, below the 0.80 floor |

Every false positive was a confident misreading of code the reviewer could not run, such as Python's conditional-expression precedence, an index into a path's parents, or a field name mistaken for a built-in property.

**Performance (n = 30, final head of each pull request).**

| Measure | Median | p95 |
| --- | --- | --- |
| Push to reviewer success | 18.5 min | about 97 min |
| Of which queueing | 4.5 min | 89.5 min |
| Of which the review run | 7.7 min | 37.5 min |

Over three days, 36% of the reviewer's busy time went to advisory reviews of a branch where it was not required, and that was the largest single cause of waiting.
The scheduler has since been changed to select required reviews first.

**Reliability after the service cutover (2026-10-29 to 2026-11-01, 122 runs).**
23 runs ended in error.
Ten were advisory.
Of the rest, nine came from one containment-verification outage, three from a model-server memory-pressure incident, and one was a timeout.

**Limits of this evidence.**

- The performance sample covers about two and a half days after the service cutover; a 95th percentile at n = 30 rests on the two largest values.
- Effectiveness rests on 18 findings and 16 verdicts and should be read as directional.
- False negatives were counted only as defects that surfaced after merge within days. Escapes not yet found are not counted.
- Push times were approximated by the earliest check on each head.

## What has not been measured

I have not measured, and the showcase does not claim:

- deployment frequency, lead time, or change failure rate;
- engineering time saved, or any percentage reduction in effort;
- the reviewer's recall, meaning how many real defects it misses;
- how the reviewer compares with human review on the same changes.
