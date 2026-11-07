# Delivery lifecycle and governance

Last verified: 2026-11-07

This page follows a change from ticket to production and describes the shared governance that several independently developed products sit on.
Each section carries its own status, because this is the part of the platform where implemented and planned work sit closest together.

## The lifecycle

```mermaid
flowchart LR
    subgraph dev["Development: engineering agent account"]
        t["Admitted ticket"] --> code["Implement and<br/>verify locally"]
    end

    subgraph prz["Pull request: untrusted until proven"]
        pr["Pull request<br/>closes the ticket"]
        ci["CI<br/>(runner chosen by repository trust)"]
        rv["Independent reviewer<br/>(exact head and base)"]
        pol["PR and ticket policy"]
    end

    subgraph merge["Protected merge: enforced by GitHub"]
        rs{"Ruleset: required contexts,<br/>pinned identities, strict"}
        am["Native auto-merge<br/>(merge commit)"]
    end

    subgraph stg["Staging: staging-only credential"]
        sd["Deploy the exact<br/>merged commit"]
        si["Prove the served build<br/>and its backend"]
    end

    subgraph prd["Production: planned"]
        rc["Qualified immutable<br/>release candidate"]
        fa["Founder approval bound to<br/>product, environment, candidate"]
        pp["Promote without rebuild"]
        rb["Rehearsed rollback"]
    end

    code --> pr
    pr --> ci & rv & pol
    ci & rv & pol --> rs --> am --> sd --> si
    si -.-> rc -.-> fa -.-> pp -.-> rb

    classDef planned stroke-dasharray: 5 5,color:#666;
    class rc,fa,pp,rb planned;
```

| Stage | Status |
| --- | --- |
| Ticket admission, pull-request policy, required checks, independent review, exact-head protected merge | Implemented |
| Automated merging when every required check passes | Implemented on the platform repository and enabled per repository by decision |
| Staging deployment of the exact commit with a served-identity check | Partially implemented |
| Release candidates, founder-bound production approval, promotion without rebuild, rehearsed rollback | Planned |

## Ticket-driven work

Every engineering ticket must contain eight sections: Problem, Desired Outcome, Scope, Out of Scope, Acceptance Criteria (with at least one list item), Verification, Dependencies and Blockers, and Risks and Constraints.
A small, dependency-free validator checks this, and its parser is shared with the reviewer through a common set of test vectors, so both read a ticket the same way.

The important design choice is that **admission is recomputed, not recorded**.
A workflow labels tickets `ticket:ready` or `ticket:invalid` for people to see, but nothing that decides whether work may proceed reads that label, because anyone with issue write access can apply it.
Every verifier, including the pull-request policy and the reviewer, re-runs the validator on the ticket's current body at the moment it decides.
An admission receipt published by a trusted App was considered and rejected: its issuer would make the same deterministic decision every verifier can recompute, so it would add a write path, a permission and mutable state without adding a security property.

Admission is also separate from authorization.
A well-formed ticket is admitted; whether anyone decided the work should happen is a separate, human question.

Where the reviewer enforces ticket scope, a pull request must close at least one open, admitted ticket in the same repository, and the reviewer judges the diff against that ticket's Scope, Out of Scope and Acceptance Criteria.
Scope findings follow consequence rather than file count: unauthorized expansion across a security or data boundary is P1, unrelated behavioral work is P2.
Editing the ticket after a pass revokes the pass on the unchanged head.

## Required checks, exact commits

On a governed repository the default branch has a ruleset with no bypass actors that refuses deletion and force-pushes, requires a pull request, and requires a small set of status checks with strict freshness.
Each required check is pinned to the integration that is allowed to produce it, so the reviewer's context can only be satisfied by the reviewer App and CI contexts only by GitHub Actions.

Strict freshness means a pull request can merge only while its head is up to date with the protected branch.
Together with head-anchored statuses, this gives exact-commit verification: what merges is the commit that was reviewed and tested, against the base it was reviewed against.
An illustrative ruleset is in [`examples/github/ruleset-protected-main.json`](../../examples/github/ruleset-protected-main.json).

## Automated merging

Pull requests merge through GitHub's native auto-merge once every required check is green at the exact head.
There is no merge bot, merge service, approval service or scheduler.
The engineering App can arm auto-merge, but it can never publish the reviewer's context, so it cannot merge anything the reviewer has not passed.

Getting here took an audit and a reversal, described in [decision 4](../decisions/04-auto-merge-without-human-approval.md).
The short version is that founder-only paths were once protected only by the founder's habit of merging by hand, a GitHub-native required-reviewer rule was built to make that real, and then the founder deliberately removed human approval for every path in the platform repository, keeping the pinned reviewer and CI as the gate.

## Shared governance components

Several products are developed independently, at different speeds, and none of them should break because another changed something central.
The platform therefore releases its governance as versioned components:

| Component | What it enforces |
| --- | --- |
| Ticket and pull-request policy | The eight-section ticket contract, the pull-request contract, and that a pull request closes an open, admitted ticket |
| Runner policy | Every CI job runs on exactly one approved runner class, chosen by an exact selector, with governance jobs bounded to ten minutes |
| Product repository standard | A product repository declares and provides the documents and governance roles the standard requires |

Each release is an immutable tag; a correction is a new version, never a re-tag.
Consumers pin a full 40-character commit SHA, with the tag in a comment for humans.
A branch reference is never used, because a branch means a central edit reaches every repository the moment it merges, with nobody choosing it.

The validators parse what they judge rather than pattern-matching text.
The runner policy parses every workflow with a YAML parser and judges each job from the parsed tree, and an expression anywhere in a runner selector is refused, because an expression could resolve to a different runner at run time.
The product standard uses a deliberately restricted manifest parser with no YAML dependency, so local and CI verdicts are identical.

### Verification across repositories

An onboarding operation reads the organization's intended state from one declarative inventory: runner classes and their members, the released version of each component, the governance workflows and the contexts they produce, repository classes with their rulesets, and each repository's class.
It can onboard one repository, verify one, or audit the whole organization against live GitHub in both directions, reporting anything present but not declared and anything declared but not present.
It is idempotent: a conforming repository produces zero changes, and two runs against the same live state compute the same plan.
It fails closed, reporting a blocked step with the permission it needed rather than skipping it, and it only ever narrows the runner group, never widens it.

## CI runners and workload separation

Private repositories run CI on self-hosted runners on the same machine, split into two classes that differ by one label:

| | Compute class | Governance class |
| --- | --- | --- |
| For | Application builds, databases, integration tests | Short policy checks |
| Container engine | One isolated VM per runner, with only that runner's ports forwarded | None at all |
| Job length | The repository's own timeouts | 1 to 10 minutes, required by the runner policy |

The split came from a measured incident.
On 2026-09-30 three long application jobs held the only runner for 102 minutes while 20-second policy checks waited, one of them for 68 minutes.
A second identical runner would not have fixed it, because GitHub hands a job to any runner carrying every requested label, so two long jobs could still occupy both.
Making the classes disjoint turns the separation into a property of GitHub's scheduler.

The persistent self-hosted runners are not a clean security boundary for code a repository supplies, which is acceptable only because they serve private repositories under the same owner.
Disposable, one-job execution for untrusted code is [planned](../roadmap.md).

## Public and private repositories

A public repository is a different trust problem: anyone can fork it and open a pull request.
Public repositories therefore form a separate, audited category:

- CI runs only on GitHub-hosted runners, which are ephemeral and isolated per job;
- the private runner group refuses public repositories, and the onboarding operation refuses to widen it;
- the organization audit checks that each public repository is actually public, is not admitted to the runner group, has no workflow job that names a self-hosted selector or chooses its runner in a way that cannot be resolved statically, and requires the reviewer's context pinned to the reviewer App with strict freshness;
- the default workflow token is read-only and workflows cannot approve pull requests;
- the self-hosted governance workflows cannot run there, so the reviewer enforces ticket scope instead.

The reasoning is in [decision 5](../decisions/05-public-and-private-ci-security-models.md).
This repository is the second member of that category, after CreatorBrio.

## Staging

Status: **Partially implemented.**

The target behavior: on every push to a product's staging branch, deploy exactly that commit to the product's staging project, wait a bounded time for the hosting provider to serve it, prove that the served build is that commit, and prove it talks to the staging backend and not to a legacy or production one.

What exists:

- **A shared staging adapter, implemented and tested.** It refuses anything but a full 40-character commit, creates the deployment exactly once and never retries the create request (a failed create is reported as "outcome unknown" because it may have created a deployment), treats the deployment as served only when it is ready and its aliases have moved, and scans the served HTML and scripts for expected and forbidden backend identities, failing closed at every size and time bound.
- **A staging-only credential model.** The hosting provider's project-scoped token is refused for every other project, including production, and lives only in a GitHub environment restricted to the staging branch, never in a repository secret or an agent environment.
- **A served-identity check in the first product's own CI,** recorded on 2026-10-15, which runs on every push to staging and checks that the served page's identity matches the pushed commit.

What does not exist yet: the reusable workflow that lets products call the shared adapter has not been released, so the adapter is not yet the path any product deploys through.
Several provider behaviors the adapter depends on are recorded as unverified until its first live run.

## Production promotion and rollback

Status: **Planned.** None of this section is implemented.

The design, adopted as a target on 2026-10-11:

- **A qualified, immutable release candidate.** The thing promoted to production is the thing that was qualified. A staging build may differ when build-time configuration differs, but the production candidate itself is never rebuilt between qualification and promotion.
- **Founder approval bound to one candidate.** Approval names the product, environment, commit, deployment and migration set, is received by a control plane the engineering identity cannot forge, and unlocks a production credential only after it is given.
- **Separate deployment identities** per product and environment, unreachable from the agent account or an untrusted build.
- **No deployment on merge.** Mapping existing products onto this design showed why this must be a precondition rather than a default: a hosting provider's Git integration can deploy production whenever the default branch moves, and the only safe interim control was to stop production builds entirely until the standard exists.
- **Code rollback first, data recovery separately.** Rolling back to a previous release is the first response to bad code. Restoring data is a different, higher-risk operation with its own approval, and every product needs a rehearsed restore with measured recovery point and recovery time before its first production deployment under this model.

The production security standard that makes these enforceable is an open piece of work.

## What the automation removed

Before this platform, moving a change to merge meant a person checking that the work had a well-formed ticket, that the branch was current, that CI was green, that someone had looked at the diff, and then clicking merge, for every pull request in every repository.
Each of those is now a check that GitHub enforces at the exact head, though a ticket check confirms structure, not whether the work is wise, so the founder's time goes to the decisions on the [operating model](../operating-model.md#where-a-human-still-intervenes) page instead.

I have not measured how much time this saves, and this page does not estimate it.
