# Operating model

Last verified: 2026-11-07

This page is the big picture: how a piece of engineering work moves from a decision to a merged and deployed change, and which identity holds authority at each step.
The pages under [`architecture/`](architecture/) and [`workflows/`](workflows/) go deep on each part.

## The problem it solves

An AI coding agent can write and change code quickly.
The harder question is what authority it holds while it does.

When an agent runs as the developer's own operating-system user, it can read every credential that user can read: SSH keys, the GitHub CLI's login, organization-admin tokens, other services' keys.
No permission setting on GitHub can stop a process from using a credential its own user can read.
An agent that reviews its own change is also not an independent review, however careful it is, because the same context that produced a mistake is the context checking for it.
And a control that exists only as a habit, such as "I always look before I merge", stops existing the first time merging is automated.

So the design question became how to let the agent do as much engineering as possible while every piece of authority it needs is narrow, short-lived, enforced by something other than its own good behavior, and checked by something it cannot influence.

## Design philosophy

**Automate the repeatable work.**
Implementation, opening pull requests, running checks, reviewing, merging and deploying staging are mechanical once their inputs are decided, so they run without a human in the loop.

**Keep authority boundaries explicit.**
Each identity has a written list of what it may do and what it may never do, and the list is enforced by the operating system, GitHub, or a credential broker.
When something is unavailable, the system refuses; it never falls back to a broader credential.

**Make human intervention meaningful.**
The founder decides what work exists, which repositories and permissions an identity may have, when a privileged component is installed, and (once built) which exact build reaches production.
The founder no longer approves individual pull requests.
That was a deliberate decision with real costs, explained in [decision 4](decisions/04-auto-merge-without-human-approval.md).

## End-to-end flow

```mermaid
flowchart TB
    subgraph founderZone["Founder: decides, does not execute routine work"]
        decide["Product and governance decisions<br/>recorded on tickets"]
    end

    subgraph engZone["Engineering agent account: no GitHub identity of its own"]
        impl["Implement against the ticket's<br/>scope and acceptance criteria"]
        local["Local verification"]
    end

    subgraph brokerZone["Key broker: holds the only App key"]
        mint["Mint a token for one repository,<br/>one permission profile"]
    end

    subgraph githubZone["GitHub: enforces"]
        ticket["Ticket<br/>(eight required sections)"]
        pr["Pull request closing the ticket"]
        ci["CI on runners matched to trust"]
        rules{"Ruleset: required checks<br/>at the exact head, strict"}
        merge["Native auto-merge"]
    end

    subgraph reviewZone["Reviewer service: separate identity and machine account"]
        review["Read-only review of the exact<br/>head and base on a local model"]
        controller["Deterministic verdict policy"]
    end

    subgraph deployZone["Deployment"]
        staging["Staging: deploy the exact merged commit,<br/>prove what is served"]
        prod["Production: founder approval bound<br/>to one immutable candidate"]
    end

    decide --> ticket --> impl --> local
    local -->|"asks"| mint
    mint -->|"token lives for one command"| pr
    pr --> ci --> rules
    pr --> review --> controller -->|"status only the reviewer<br/>identity can satisfy"| rules
    rules -->|"all green"| merge --> staging
    staging -.-> prod
    decide -.->|"exact-candidate approval"| prod

    classDef planned stroke-dasharray: 5 5,color:#666;
    classDef partial stroke-width:3px;
    class prod planned;
    class staging partial;
```

Solid lines and boxes are operating.
Staging, with the thick border, is partially implemented, and dashed elements are planned.

## Who holds authority at each step

| Step | Acts as | May | May never | Status |
| --- | --- | --- | --- | --- |
| Decide the work | Founder | Write tickets, record decisions, change governance | Be bypassed by an agent's own judgment about scope | Implemented |
| Admit the ticket | Deterministic validator, recomputed by every verifier | Accept a ticket whose current body has the eight required sections | Trust a label, which anyone with issue write access can apply | Implemented |
| Implement | Engineering agent account | Edit code, run local tools, ask the broker for a token | Read founder credentials, reach a container engine, hold a GitHub login | Implemented |
| Talk to GitHub | Engineering GitHub App, through the broker | Contents, pull requests and issues for one repository per token | Workflows, Actions, administration, deployments, secrets, organization settings | Implemented |
| Validate | CI on runners chosen by repository trust | Run checks on the pull request | Run public pull-request code on a private self-hosted runner | Implemented |
| Review | Reviewer service under its own App and macOS account | Read the exact change, publish a status and a comment | Execute pull-request code, approve, merge, or be produced by the engineering identity | Implemented |
| Merge | GitHub, through the repository ruleset | Merge when every required context is green at the exact head and the branch is current | Accept a status from any identity other than the one pinned for that context | Implemented |
| Deploy staging | Staging-only deployment credential in a branch-restricted environment | Deploy one product's staging project | Reach production, which the provider refuses for that credential | Partially implemented |
| Promote to production | Product and environment specific deployment identity | Promote one approved, immutable candidate | Be reached from the agent account or an untrusted build | Planned |

## Where a human still intervenes

These are the places the founder acts, and each one is a decision rather than a rubber stamp:

- deciding what is worth building, and writing that down as a ticket an agent can be held to;
- authorizing a new repository, permission or identity, which takes effect only after a privileged installation the founder approves at the console;
- ordering a fresh review when a reviewer defect or an outage made an earlier verdict wrong, which is bounded and recorded;
- approving one exact production candidate, once production promotion exists.

What the founder no longer does is look at every pull request before it merges.
The reviewer, the required checks and the ticket scope are the gate, and the [evidence page](evidence/README.md) shows how good that gate is and where it falls short.

## What is deliberately not automated

- Changes to the controls themselves (rulesets, App permissions, the broker's policy, the reviewer's installation) are proposed by pull request like any other change, but they only take effect through a privileged installation step that the founder runs.
- No identity the agent can reach holds production credentials, and nothing deploys to production on merge.
- The reviewer never executes pull-request code. It reads and reasons, which is a real limitation as well as a security property, discussed on the [reviewer page](architecture/independent-reviewer.md#limitations).

## Where to go next

- [Isolated engineering agent](architecture/isolated-agent.md)
- [GitHub authorization and the key broker](architecture/github-authorization.md)
- [Independent local AI reviewer](architecture/independent-reviewer.md)
- [Delivery lifecycle and governance](workflows/delivery-lifecycle.md)
