# Decision 5: different CI security models for public and private repositories

Last verified: 2026-11-07

## Problem

The governance model was written for private repositories: CI on the organization's own self-hosted runners, policy workflows on a dedicated governance runner, and an onboarding operation that refuses GitHub-hosted runners.
On 2026-10-27 the first public repository, CreatorBrio, came under governance, and none of that could be applied to it as written.

## Initial approach

The repository arrived with what a public project typically has: CI on GitHub-hosted runners and a ruleset requiring one CI check.
Measured against the platform's standard, that check was not pinned to any integration and did not require the branch to be up to date, so anyone with status-write access could satisfy it.
The governance workflows could not run there at all, because the private runner group does not admit public repositories.
And the independent reviewer is a shared, fail-closed resource with limited throughput, so on a public repository, pull requests from strangers would compete with every private product's reviews.

## What we learned

Two threats that are absent for a private repository dominate for a public one.

- **Code execution.** A persistent self-hosted runner that runs a fork's pull request runs a stranger's code on the machine that also hosts the platform. GitHub-hosted runners are ephemeral and isolated per job, so for public code they are the stronger boundary, even though the private policy forbids them.
- **Queue exhaustion.** The reviewer executes nothing and needs no runner, so it can safely cover a public repository, but its capacity is shared, so a public repository needs admission control in front of it.

## Decision

Recorded as founder decisions on 2026-10-28:

- public repositories run CI only on GitHub-hosted runners, as a narrowly scoped, audited exception;
- they form their own inventory category, and the organization audit checks each one is public, is not admitted to the private runner group, has no workflow job that could reach a self-hosted runner, and requires the reviewer's context pinned and strict;
- the reviewer enforces ticket scope there, because the self-hosted ticket and pull-request workflows cannot run;
- the default workflow token is read-only, workflows cannot approve pull requests, and actions are pinned by SHA;
- as an interim queue protection, repository interactions are limited to collaborators.

## Trade-off

- The interaction limit is a GitHub feature with a maximum duration, so it must be renewed or replaced.
- Public repositories get a narrower governance surface than private ones, because the shared policy workflows cannot run there.
- Two security models means two things to keep correct, which is why the audit checks the public category explicitly rather than trusting it.

## Result

CreatorBrio merged its first pull request under this model on 2026-10-28.
This showcase is the second public repository.
It adds GitHub's repository-level restriction of pull-request creation to collaborators, a permanent control rather than an expiring one, alongside the time-limited interaction limit, and enables secret scanning with push protection.
Its configuration is described in [security](../security.md#how-this-repository-is-protected).
