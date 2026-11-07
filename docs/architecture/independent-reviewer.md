# Independent local AI reviewer

Last verified: 2026-11-07

Status: **Implemented.**
First built on 2026-08-13 and now the required review gate on the protected branches of the platform repository, several private product repositories and the public CreatorBrio repository.
Since 2026-10-29 it runs as a dedicated system service.

The reviewer is a long-running daemon that reviews pull requests with a local model, publishes a commit status that branch rules require before merging, and is built so that the identity that wrote a change cannot publish or satisfy that status itself.
It reads and reasons about code; it never builds, installs, tests or executes anything from a pull request.

## Why an agent reviewing its own change is not review

The engineering agent can, and does, check its own work.
That is useful, and it is not independent.
The same context, prompt history and assumptions that produced a mistake are the ones looking for it, and the agent controls what it shows itself.
An agent that can also publish the "review passed" signal can simply publish it.

Independence here means four concrete things:

- **A different process with a different context.** The reviewer starts from the pull request on GitHub, not from the implementing session.
- **A different identity.** It runs under its own GitHub App and its own macOS service account. The engineering identity cannot read its key, write its installation, or post a status the branch rules will accept.
- **Inputs the author cannot shape.** The verdict is computed from the exact head and base commits and, where tickets are required, the ticket's scope. Pull-request titles and descriptions are not inputs to the enforced result, because the author can edit them after a pass.
- **A decision the model does not make alone.** The model proposes findings; deterministic code decides the gate.

## Architecture

```text
GitHub App installations
  -> repository allowlist (the only authorization; visibility is not permission)
  -> open pull requests
  -> generation identity: repository + PR + head SHA + base SHA + ticket-scope digest
  -> already settled? skip
  -> bare mirror + disposable worktree, Git hardened
  -> controller-generated review artifacts
  -> Claude Code, headless, with every built-in tool removed
  -> read-only repository-access server inside an OS sandbox
  -> schema-validated result
  -> deterministic verdict policy
  -> secret scan -> staleness check -> duplicate-publication check
  -> review comment + commit statuses
  -> SQLite state, worktree removed
```

Inference runs on a local model server with an Anthropic-compatible API, on the same machine.
Claude Code is the agent runtime that drives the review session against that local endpoint.
No pull-request content leaves the machine for inference.

## From pull request to merge

```mermaid
sequenceDiagram
    autonumber
    actor Agent as Engineering agent
    participant GH as GitHub
    participant D as Reviewer daemon
    participant M as Model session<br/>(no built-in tools)
    participant R as Read-only repo server<br/>(OS sandbox)
    participant C as Deterministic controller

    Agent->>GH: Open PR closing an admitted ticket
    GH-->>GH: CI starts on hosted or self-hosted runners
    loop every poll cycle
        D->>GH: List open PRs in allowlisted repositories
    end
    D->>D: Generation = repo + PR + head + base + scope digest
    D->>GH: Re-validate the linked ticket's current body
    D->>GH: Fetch exact head from the base repository
    D->>D: Build worktree and controller artifacts
    D->>M: Review contract as system prompt
    M->>R: list_files, search_repo, read_file, read_file_range
    R-->>M: Bounded, path-checked responses
    Note over D,GH: About once a minute: has the head or base moved?<br/>If so, stop the session and record it stale.
    M-->>D: Schema-valid verdict, confidence, findings
    D->>C: Decide
    C-->>D: success / failure / error
    D->>D: Scan the outbound payload for secrets
    D->>GH: Re-check head, base and ticket scope
    D->>GH: Post COMMENT review and statuses at the head SHA
    D->>GH: Read back: newest status authored by the reviewer App matches
    GH-->>GH: Ruleset: reviewer context pinned to the reviewer App,<br/>CI green, branch up to date
    GH->>GH: Native auto-merge
```

## Discovering and scheduling work

**Authorization is an allowlist.**
The reviewer's GitHub App is publicly installable, so anyone on GitHub can make their repositories visible to it.
Visibility is therefore never permission.
Exactly one list of exact, case-sensitive `owner/repo` names authorizes review work, everything else is discarded before its pull requests are even listed, and an empty list refuses to start rather than meaning "everything".

**Every review has an identity.**
A review is keyed by repository, pull request, head SHA, base SHA and a digest of the ticket scope, enforced by a unique constraint in its database.
The base is part of the identity because a review describes a diff, and the diff changes when the base moves even if the head does not.
The scope digest is part of it because a ticket edited after a pass changes what work was authorized.
Polling the same pull request every minute creates no duplicate work.

**One review runs at a time.**
That is a measured limit: two concurrent reviews on 2026-09-07 raced on the shared per-repository Git mirror, and concurrency stays at one until that is fixed.
With one slot, queue order decides how long a pull request stays unmergeable, so selection is deterministic and logged:

1. Reviews into a protected branch run before advisory reviews of other branches.
2. Higher declared project priority first.
3. Human or agent pull requests before bot pull requests, within a priority tier.
4. A pull request that has already been reviewed once and had a fix pushed runs before one nobody has looked at yet.
5. Oldest first, by the first time any version of the pull request was queued.

Two bounded starvation guards stop a busy high-priority project, or a stream of follow-up fixes, from starving everything else.
Retries after an infrastructure failure deliberately do not earn priority, or the queue would reward failure.
Every selection writes one log line saying why that pull request was chosen.

## Reviewing the exact commits

The head is fetched from the base repository's `refs/pull/<n>/head`, so a fork is never contacted, and the fetched commit must equal the SHA the API reported.
Git runs with user and system configuration disabled, hooks disabled, LFS and filters cleared, submodules never recursed and symlinks materialized as plain files, so nothing in a pull request runs during checkout.
Credentials reach Git only through an ephemeral askpass helper, never in arguments or in `.git/config`.

The diff comes from GitHub when GitHub will render it.
GitHub refuses to render diffs above 20,000 lines, so for exactly that refusal the reviewer computes the comparison locally.
It takes the merge base from GitHub's compare endpoint rather than from its own shallow mirror, because a shallow repository does not refuse ancestry questions: it answers them wrongly, and the wrong answers look exactly like real ones.
It then checks the local result against GitHub's own file, addition and deletion counts and fails the run on any mismatch, because an incomplete diff is indistinguishable from a smaller, cleaner change.
A diff is never truncated to fit; it is split into parts the model reads in order, and a diff too large even for that fails the review.

## Containment

The reviewer reads attacker-controlled content and publishes to pull requests, so containment is the central design concern.

**No built-in tools.**
Claude Code is launched with every built-in tool removed: no shell, no file read or write, no web access, no sub-agents.
Repository access comes only from a controller-owned server exposing four read-only tools: list files, literal search, read a file, read a line range.
Before trusting the session, the controller reads the session's initialization event and aborts unless the registered tool set is exactly those four and the server is connected.
That check exists because the CLI silently ignores settings that fail validation in non-interactive mode, which would otherwise fail open.

**Layers, each verified at startup:**

1. **Capability boundary.** Every path is canonicalized, symlinks resolved, kept inside its root, and must appear in an inventory built from `git ls-files`. Binary files, oversized reads, unbounded searches and long line ranges are refused.
2. **Literal search.** No regular expression is ever compiled from model input.
3. **OS sandbox.** The repository server runs under macOS `sandbox-exec` with no network and no read access to user homes or system secrets, apart from the worktree, the review artifacts and its own code. Each start verifies the denial against the reviewer's real private key.
4. **Secret separation.** Child processes get an environment built from an explicit allowlist. The App key and tokens never reach the model or the repository server.
5. **Publication guard.** The exact outbound payload is scanned for credential shapes and for the live token and key by value and fingerprint, before it is stored and before it is sent. A hit publishes nothing.
6. **Output neutralization.** Mentions and leading slash commands in model text are defused, so a prompt-injected review cannot notify people or command other bots.

If any layer cannot be verified, the daemon refuses to run.

**Three trust roots.**
The model sees files under `run/` (controller provenance: identifiers, validated SHAs and booleans only), `pr/` (the diff, title, description and file list, all untrusted) and `repo/` (the worktree, untrusted).
Artifacts live outside the worktree, so a pull request cannot ship its own provenance file.
The review contract arrives only as the system prompt and is not readable through any tool, so repository content cannot replace it.

## Structured findings, and who decides

The model must return a result that validates against a schema: a verdict of `PASS`, `CHANGES_REQUIRED` or `NEEDS_DEEPER_REVIEW`, an overall confidence, a summary, the files it inspected, and findings with severity (`P1` to `P3`, or `INFO`), file, line, evidence, impact, recommendation and confidence.
An illustrative schema is in [`examples/review-result.schema.json`](../../examples/review-result.schema.json).

The controller then decides, deterministically:

| Condition | Gate |
| --- | --- |
| Any P1 or P2 finding | failure |
| Model verdict `CHANGES_REQUIRED` | failure |
| Model verdict `NEEDS_DEEPER_REVIEW` | failure, described as inconclusive |
| Confidence below 0.80 | failure, described as inconclusive |
| `PASS`, no P1 or P2, confidence at or above 0.80 | success |
| Malformed output, budget exhausted, timeout, unreadable evidence, model unavailable | error |

P3 and INFO findings never block on their own.
A standalone version of this policy, with tests, is in [`examples/verdict-policy/`](../../examples/verdict-policy/).

The model also has a bounded budget of turns and wall-clock time, divided into exploration, verification and synthesis phases that the repository server enforces in-band.
A run that ends without a valid result is an error, never a pass, and the controller never invents a verdict on the model's behalf.

## Publishing and merge gating

Two statuses go to the head commit:

| Context | Purpose |
| --- | --- |
| `local-ai/pr-review/<branch>` | Enforcement. One per protected branch, required by the branch's ruleset. |
| `local-ai/pr-review/pr-<number>` | Visibility for people. Never required. |

The review itself is posted as a `COMMENT`.
The reviewer never approves and never merges.

Three GitHub facts shape this, and each was learned by testing against real merges:

- **A commit status is not access-controlled per context.** Anyone with status-write permission can post `success` under any context name. Classic branch protection matches on name alone. The required check must therefore be configured in a repository ruleset that pins the context to the reviewer App's integration ID. That was verified live: a `success` posted by another authenticated user under the exact context left the pull request blocked.
- **A status has no pull-request association.** Two pull requests can share a head commit against different bases, and a single shared context would let a review of one diff satisfy the other. This was demonstrated: a pass on a five-file diff satisfied a different pull request whose one-file diff had never been reviewed, and it merged. Hence one context per protected branch, and a refusal to publish when another open pull request shares the head against a different protected base.
- **The status says nothing about the base it was reviewed against.** Strict "branch must be up to date" freshness is what binds the two, so it is part of the security model. Before every authoritative publication the reviewer reads the ruleset back from GitHub and publishes no pass unless the context is required, pinned to it, and strict.

After publishing, the reviewer reads the commit's statuses back and checks that the newest one authored by its own App matches what it wrote.
It deliberately ignores other identities' writes rather than reacting to them, because reacting would hand any collaborator a way to deny every merge.

## When things go wrong

| Situation | Behavior |
| --- | --- |
| The head or base moves during a review | Checked about once a minute while the model runs. The session is stopped, the run is recorded stale with no verdict, and the new version is queued. Re-checked again immediately before publishing. |
| The ticket is edited after a pass | Any published success for the old scope is driven back to `pending` on the same head before a replacement review starts. |
| The ticket validator cannot run, or GitHub cannot be read for the ticket | Treated as not admitted: any published success is withdrawn and nothing new is published. |
| The model server refuses work before the model produces anything | The attempt is refunded and deferred with backoff, at most eight times in a row. Probes use a real one-token request, because health endpoints stayed green during an actual outage. |
| Timeout, malformed output, transport interruption after the model began | Charged as a failed attempt. Repeated attempts are capped, because a nondeterministic model asked often enough will eventually pass anything. |
| Publication to GitHub fails after a verdict is decided | The exact scanned review body is stored with the decision and republished without rerunning the model, at most once per attempt and with backoff, because creating a review is not idempotent. |
| A reviewer defect or outage made a verdict wrong | An operator can order at most two fresh reviews of the unchanged generation, with a recorded reason. The command can only requeue; the daemon reviews and publishes. |
| The daemon is stopped mid-review | The model session is killed, the run is requeued by the next daemon, and nothing is published for it. |

A run moves through these states:

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> running: selected by the scheduler
    running --> queued: failed before the model ran (deferred, attempt refunded)
    running --> stale: head, base or scope moved
    running --> publishing: controller decided
    running --> error: attempts exhausted
    publishing --> passed: published, gate success
    publishing --> failed: published, gate failure
    publishing --> needs_deeper_review: published, gate failure (inconclusive)
    publishing --> stale: moved before publication
    passed --> queued: operator-ordered re-review (bounded)
    failed --> queued: operator-ordered re-review (bounded)
    stale --> [*]
    passed --> [*]
    failed --> [*]
    needs_deeper_review --> [*]
    error --> [*]
```

## Running it as a service

The reviewer gates merges in several repositories, so an accidental or malicious change to the running reviewer is a change to every gate at once.

- **Sealed releases.** The service never runs from a development checkout. A release is one merged commit, extracted from Git objects, built and tested in place, recorded with a hash of every file, and sealed read-only. Its self-check refuses to run if any installed file differs.
- **A dedicated service account.** Since 2026-10-29 the reviewer runs as a hidden, non-admin system account from root-owned copies of the release, and since 2026-10-30 with pinned, signature-checked copies of Node.js and the Claude CLI. The founder's own processes, including AI agent sessions, can no longer rewrite the running gate without an administrator prompt.
- **Exactly one publisher.** A starting daemon refuses while any other reviewer process runs on the host, and the two installation forms refuse each other.
- **Changing the reviewer is reviewed by the deployed reviewer.** A pull request that changes the reviewer is reviewed by the release built from `main`, which does not contain the change. Merging deploys nothing; a separate, privileged activation does.

## How well it works

A point-in-time audit on 2026-11-01 measured the reviewer against real pull requests, with each blocking finding classified from the code and then independently challenged.
The headline numbers:

| Measure | Result |
| --- | --- |
| P1 and P2 findings that were valid / partially valid / false positives | 7 / 2 / 9, of 18 |
| Real findings that tests or CI also caught | 0 of 9 |
| Material real findings | 2, both in application code; one at a database-permission boundary the tests had mocked |
| Final-head review run time, median (n = 30) | 7.7 minutes |
| Final-head queue time, median (n = 30) | 4.5 minutes, p95 about 90 minutes |
| Runs ending in error after the service cutover | 23 of 122 (19%), mostly two infrastructure incidents |

The full table, method and caveats are on the [evidence page](../evidence/README.md#reviewer-audit-2026-11-01).
The conclusion drawn from it was to keep the reviewer as the required gate, fix how it spends its single slot rather than add features, and freeze feature work for a month.

## Limitations

- **Pull-request code is never executed,** so no build, test or runtime evidence informs the review. Every false positive in the audit was a confident misreading of code the reviewer could not run, such as operator precedence or an index into a path list. CI and the reviewer catch different defect classes; neither replaces the other.
- **Model judgment is fallible in both directions.** Half the blocking findings in the audited month were wrong, and defects the reviewer passed were found after merge.
- **The Claude process is not network-confined by the operating system.** macOS refuses nested sandboxes, and the repository server, which is the process that can read files, needs the sandbox more. The compensating controls are that the session has no network-capable tool and its endpoint is pinned to the local model server.
- **The reviewer trusts its local model endpoint.** The endpoint is not authenticated, so a process on the same machine that could answer in the model server's place could influence a verdict. The engineering identity cannot publish the status itself, but this residual path means the gate's independence rests partly on the host. It is recorded as an open risk, accepted for a single-owner workstation, and not yet solved.
- **macOS only,** because containment depends on `sandbox-exec`.
- **One machine, one slot.** Throughput is bounded by local inference, and the review stops when the machine sleeps.

## Related

- [Decision 1: separate the implementer from the reviewer](../decisions/01-separate-implementer-and-reviewer.md)
- [Decision 3: deterministic controls around model judgment](../decisions/03-deterministic-controls-around-model-judgment.md)
- [Decision 6: anchor the gate to the head commit](../decisions/06-anchor-the-gate-to-the-head-commit.md)
- [Lessons from operating it](../lessons/README.md)
