# Decision 4: auto-merge without human approval

Last verified: 2026-11-08

## Problem

Every agent-authored pull request in the platform repository was merged by the founder, by hand.
That made the founder the throughput limit of the whole system, and it hid a worse problem.

## Initial approach

Before enabling GitHub's native auto-merge, an audit on 2026-10-29 checked what merging by hand had actually been protecting.
It found two gaps:

- changes to the controls themselves (agent instructions, workflows, the reviewer, the credential tooling, the agent's isolation check, the App allowlist) were reserved for the founder only by habit. The ruleset required no approval, and the Engineering App could already merge anything the reviewer passed;
- the pull-request policy check ran on every pull request but was not required, so auto-merge would have ignored a red result.

The first fix made the habit real.
A GitHub-native required-reviewer rule demanded a founder-team approval for those paths, invalidated by any later push, with a deliberate route for the founder's own pull requests.
It was built and verified against real rule evaluations on 2026-10-29.

## What we learned

A human approval on every control-plane change keeps the founder on the critical path for exactly the changes an autonomous platform needs most often, the ones that fix the platform.
And it was being treated as a safety net while the actual check, reading the diff, was the reviewer's job anyway.

## Decision

On 2026-11-01 the founder revoked founder-only approvals for every path, including the reviewer's own code and the CI definitions.
A pull request into the platform repository's main branch now merges once the pinned reviewer context and every other required check are green at its exact head, with no human approval event.

What was kept, explicitly:

- the ruleset itself, with no bypass actors;
- the reviewer's context pinned to the reviewer App, and CI contexts pinned to GitHub Actions, all strict;
- pull-request-only merging, with deletion and force-push refused;
- the separation between the identity that writes code and the identity that reviews it;
- the pull-request policy check as a required context, so auto-merge cannot ignore it. The repository's full verification suite joined it as a required context later the same day.

What was not added: no code-owners file, no other required human reviewer, no admin bypass, no bespoke gate.
The deleted ruleset's full definition was recorded on its ticket so it can be restored exactly.

## Trade-off

- The reviewer is now the only independent semantic check before a merge into the platform repository. Its false-positive rate and its queueing became merge latency for everything.
- A change to the reviewer merges on the say-so of the previous reviewer. The mitigation is that merging deploys nothing: a reviewer change only takes effect through a separate, privileged activation.
- The founder sees changes after they merge rather than before.

## Result

The first formerly reserved pull request after the change merged with no approval event, by a direct merge from the engineering App, with GitHub's rule evaluation showing only the main ruleset applied.
Native auto-merge was enabled on the repository later the same day, and the first auto-merge followed.
The same day, the reviewer audit measured what the platform now depended on, and its findings drove a month-long reviewer feature freeze and a scheduling fix that runs required reviews before advisory ones.
That sequence, removing a human gate and immediately measuring the automated one that replaced it, is the part of this decision I'd repeat.
