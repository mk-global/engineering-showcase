# Decision 2: brokered, short-lived credentials

Last verified: 2026-11-08

## Problem

An audit of how automation authenticated to GitHub, in early October 2026, found agent work using a machine-user personal access token, and agent sessions running where the founder's own SSH keys and admin-scoped GitHub CLI login were readable.
Long-lived, broadly scoped bearer credentials in reach of an AI agent are the opposite of least privilege.

## Initial approach

The replacement was a GitHub App with a fixed, small permission set, and a client wrapper that mints an installation token for one repository and one permission profile per command and revokes it afterwards.
For the first pilot repository, the App's private key was placed in the agent's own account, in an owner-only file.
That was a recorded, temporary decision with an explicit trigger: re-evaluate custody before the App is installed on a second repository.

## What we learned

Scoping the token is not the same as scoping the key.
Whoever holds an App's private key can sign their own App JWT and mint a token for every repository the App is installed on, with every permission the App has, whatever the wrapper would have asked for.
With one repository that is a contained risk.
When the App gained a second repository, the agent account could mint tokens the wrapper would never have allowed, and the re-evaluation trigger fired as designed.

## Decision

Move the key to a separate service account, a key broker, on 2026-10-13:

- a **new** key was generated directly into the broker's custody, and the key the agent had held was deleted from the App's settings, so no copy of the App key the agent ever held remains valid;
- the agent asks the broker over a Unix socket, and the broker identifies the caller from the kernel's peer credentials, never from the request;
- the broker mints only exactly one allowlisted repository with one allowlisted profile, verifies the result, and the client verifies it again;
- if the broker is unavailable, the agent has no GitHub access. There is no fallback to a local key, a personal token or the founder's credentials.

## Trade-off

- The broker is a single point of failure for the agent's GitHub access. That is deliberate: failing closed is the property being bought.
- Adding a repository is now a coordinated window in which the installation, the broker's policy and the client's allowlist must change together, with the founder present.
- **The broker does not isolate sessions from each other.** It authorizes by operating-system user, and every engineering session runs as the same one, so any session can request a token for any repository the agent is authorized for. Fixing that needs a per-session identity the broker can verify, which is not built and is stated as a residual risk rather than glossed over.

## Result

Every GitHub operation the agent performs uses a token that is scoped to one repository and carries exactly the permissions of one allowlisted profile.
Tokens are normally revoked when the command ends; GitHub's one-hour expiry is the hard bound, and repository scope, not lifetime, is the enforced boundary.
The agent cannot read the key or sign a JWT, and the broker mints only what its installed policy grants.
The design and its tests are on the [authorization page](../architecture/github-authorization.md).
