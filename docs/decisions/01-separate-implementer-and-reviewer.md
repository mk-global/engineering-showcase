# Decision 1: separate the implementer from the reviewer

Last verified: 2026-11-08

## Problem

An AI agent that writes a change can also check it, and it should.
But a check run by the author, in the author's context, is not independent, and if the author can also publish the "review passed" signal, the gate is only as strong as the author's restraint.

## Initial approach

The first reviewer, built in August 2026, already used its own GitHub App, which was the right instinct.
It ran as a login agent under the founder's macOS user, from files the founder owned.
At the same time, AI coding sessions also ran as the founder.
So any agent session could, in principle, read the reviewer App's private key and rewrite the reviewer's code, configuration and prompt, all without an administrator prompt.
The reviewer was independent in its GitHub identity and not in anything underneath it.

## What we learned

Independence has to hold at every layer an author could touch, including the ones underneath the identity GitHub displays.
It needs a separate process and context, a separate GitHub identity, a separate operating-system identity that holds the key, an installation the author cannot modify, and a branch rule that accepts the status only from that identity.
Remove any one of those and the author has a way to produce a passing result without a real review.

## Decision

- The reviewer has its own GitHub App, and every required review context is pinned to that App's integration ID in a repository ruleset.
- The coding agent runs as its own non-admin account that cannot read the reviewer's key or state ([isolated agent](../architecture/isolated-agent.md)).
- Since 2026-10-29 the reviewer runs as a dedicated, hidden, non-admin system account, from root-owned, sealed releases built only from merged commits, with its own pinned copies of its runtime.
- The engineering App can open and merge pull requests but has no way to write the reviewer's context in a form the ruleset accepts.

## Trade-off

- Installing or changing the reviewer now takes a privileged step at the console, which slows down fixing it.
- The reviewer still depends on a model server outside its own account. That dependency was accepted by explicit decision.
- The reviewer trusts its local model endpoint without authenticating it, so a process on the same machine able to answer in its place could influence a verdict. This is a recorded, accepted residual risk.
- A change to the reviewer is reviewed by the previous release of the reviewer, which by construction does not contain the change. Its new behavior is proven by tests, not by the live gate.

## Result

The engineering identity cannot publish a status the branch rules accept as the review, and cannot change the program that produces it.
It is not a complete separation: the trusted model endpoint above is a residual path to influencing a verdict, recorded and accepted rather than closed.
The reviewer's effectiveness is a separate question, answered with measurements on the [evidence page](../evidence/README.md#reviewer-audit-2026-11-01).
