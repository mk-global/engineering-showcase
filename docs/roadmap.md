# Roadmap and current limitations

Last verified: 2026-11-08

Everything on this page is **Planned** unless it says otherwise.
None of it is a capability today.

## Limitations that matter most

- **Production delivery is not automated, and should not be yet.**
  There is no release-candidate record, no founder approval bound to an exact candidate, and no rehearsed rollback.
  Products under the platform standard do not deploy to production on merge; one older product deploys from its default branch under a recorded founder exception.
- **The reviewer never runs the code it reviews.**
  Its false positives and its blind spots both come from that.
- **The broker does not separate one agent session from another.**
  Any engineering session can request a token for any repository the agent may work on.
- **Self-hosted CI runners persist between jobs.**
  They are not a boundary against hostile repository code, which is why public repositories never use them.
- **One machine runs the agent, the reviewer, the model and the private runners.**
  It is a single point of failure for review throughput, and the review stops when the machine sleeps.

## Planned work, in rough order

1. **A production deployment standard.**
   Approval bound to the exact product, environment, commit, deployment and migration set, received by a control plane the engineering identity cannot forge, unlocking a production credential only afterwards, with cross-product denial tests.
   This is the precondition for any product's production promotion under this model.
2. **Release the shared staging workflow,** so products deploy staging through the tested adapter rather than their own steps, and record the provider behaviors that are currently unverified.
3. **Per-product recovery.**
   Defined recovery point and recovery time objectives, backup and point-in-time recovery evidence, and a rehearsed restore, before each product's first production deployment under the standard.
4. **An isolated execution worker** that owns container work, reached by the agent through a job-level interface that accepts declared operations against a repository revision.
   Never a Docker socket, daemon API or remote shell for the agent.
5. **Disposable CI execution** for code a repository supplies: a clean one-job environment that is destroyed after use, on the existing hardware, before treating self-hosted CI as hardened.
6. **Per-session repository isolation** for the broker, which needs a session identity the broker can verify independently of the caller.
7. **Retire the remaining long-lived credentials** left from older automation paths.
8. **Reviewer, after its feature freeze is reassessed on 2026-12-01.**
   If false positives stay near two a week, the next investment is reducing them.
   Consuming CI results as review evidence and scaling to very large diffs come after that.
9. **Read-only production diagnostics** through provider-scoped profiles, each separately authorized and verified before use.

## Deliberately not planned

- No Kubernetes or custom workflow orchestrator. GitHub Actions and the existing runners are enough at this scale.
- No per-product macOS accounts for now. The broker's residual risk is the cost of that choice, and it is written down.
- No fully autonomous production changes. A human decides which exact build reaches production.
- No custom signing infrastructure, unless provenance needs cannot be met by existing tooling.
- No mandatory multi-reviewer prose loops for routine tickets.
