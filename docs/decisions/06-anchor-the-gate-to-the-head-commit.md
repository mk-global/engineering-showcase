# Decision 6: anchor the review gate to the head commit

Last verified: 2026-11-07

## Problem

A review describes a diff, and a diff depends on two commits: the pull request's head and the base it is compared against.
A commit status attaches to one commit.
So which commit should the required review status live on, and how does it stop describing a stale diff when the base moves?

## Initial approach

The first design published one fixed context on the pull request's test merge commit, the synthetic commit GitHub computes to show what merging would produce.
The reasoning was neat: when the base advances, GitHub computes a new merge commit, which carries no status, so the gate invalidates itself automatically.

## What we learned

It could never work, and only a real merge attempt showed it.
GitHub regenerates the test merge commit as part of the merge operation itself, then evaluates the required check against the regenerated commit, which by construction carries no status.
The merge was rejected three times in a row, each attempt producing a new merge commit.
Re-anchoring the status onto each new commit and retrying regenerated it again: a livelock, not a race to win.
Throughout, GitHub's merge box reported the pull request as mergeable while the ruleset refused it.

The lasting lesson: **the merge box is not acceptance evidence. Only a real merge attempt is.**

Two more facts came out of the same testing.
GitHub resolves a required context from the test merge commit in preference to the head when both carry it, so the retired context name can never be reused: an old status on a merge commit could override a current one on the head.
And because a status carries no pull-request association, one shared context let a review of a five-file diff satisfy a different pull request with an unreviewed one-file diff, which then merged.

## Decision

On 2026-08-14 the gate moved to the head commit:

- one required context per protected branch, so a review against one base can never satisfy another;
- strict "branch must be up to date" freshness, which binds the head to the base it was reviewed against, verified by the reviewer through GitHub before every publication;
- the retired name permanently reserved and rejected by configuration validation;
- every review recorded with the gating strategy that produced it, so historical verdicts are never reinterpreted under the new rules.

## Trade-off

- A base advance blocks every open pull request until its branch is updated, and updating changes the head, so it needs a fresh review. That costs review time, and with one review slot it costs queue time.
- The gate's soundness depends on a repository setting, strict freshness, staying on. The reviewer reads it back before publishing and refuses to publish a pass if it drifts, which turns a silent weakening into a blocked merge.

## Result

The head-anchored, branch-scoped gate has been the only enforcement architecture since 2026-08-14, and it is the model this repository's own ruleset uses.
