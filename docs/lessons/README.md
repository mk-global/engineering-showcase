# Lessons

Last verified: 2026-11-07

These are failures and surprises the platform ran into, roughly in the order they happened, and what changed because of each.
Most were found by the platform's own checks or measurements.
A few were found because something broke in front of me.

The [decisions](../decisions/README.md) describe the bigger choices; these are the smaller, sharper lessons that fed them.

## The merge box is not acceptance evidence

*2026-08-14.*
The first review gate lived on GitHub's synthetic test merge commit.
GitHub's merge box said the pull request was mergeable while the ruleset kept refusing the merge, because GitHub regenerates that commit during the merge itself.
Only a real merge attempt exposed it.
Since then, every gate change has been accepted on the evidence of a real merge or a real refused merge, never on what the merge box says.
Full story in [decision 6](../decisions/06-anchor-the-gate-to-the-head-commit.md).

## A commit status does not know which pull request it is for

*2026-08-14.*
Two pull requests can share a head commit against different base branches.
With a single shared status context, a pass on one diff satisfied the other, and a pull request whose actual diff had never been reviewed merged.
Required review contexts became one per protected branch, and publication now refuses when another open pull request shares the head against a different protected base.

## Two reviews raced on one mirror

*2026-09-07.*
Running two reviews at once looked like an easy throughput win.
Measured, the second review failed within five seconds because both were fetching into the same per-repository Git mirror.
The surviving review reproduced its earlier verdict exactly, so the model server was not the problem.
Concurrency stayed at one, with the reason written next to the setting so nobody raises it without fixing the mirror first.

## The model was reading previews

*2026-09-17.*
A coherent 15-file change ran out of turns three times without reaching a verdict.
The investigation found that the agent CLI silently replaces any tool result above 50,000 characters with a 2 KB preview and a file path, and the reviewer had no tool to open that path.
616 of 656 recorded reviewer sessions contained at least one elided result.
The model had been spending its turns re-reading the same file in pieces.
Responses are now bounded below the threshold inside the repository server, large diffs are split into parts sized to arrive whole, and a preview arriving anyway ends the run as an error instead of degrading silently.

## Long jobs starved twenty-second checks

*2026-09-30.*
Three long application CI jobs held the only self-hosted runner for 102 minutes while short policy checks queued, one for 68 minutes.
Adding an identical runner would not have helped, because GitHub can hand two long jobs to two runners that both carry every requested label.
Runners were split into two classes with disjoint labels, and the runner policy now requires governance jobs to declare a timeout of ten minutes or less.

## A proof the model never opened

*September 2026.*
The reviewer had learned to prove, from Git history alone, that a pull request was an exact rollback of earlier commits.
On one real rollback the proof verified and was exact, and the review still reported the restored code as three newly introduced regressions, because the model never read the proof.
Writing evidence is not delivering it.
The controller now checks its own record of what the model read, and discards a result formed without reading a verified proof.

## sudo carried the founder's environment into the agent account

*2026-10-27.*
The obvious way to start a shell as the agent account from the founder's terminal failed the isolation check in 11 places.
macOS's default sudo policy keeps the caller's `PATH` and SSH agent socket, and sudo adds the caller's home directory as a variable.
The fix keeps the identity change and starts the agent's shell from an empty environment, so only the minimum crosses the boundary.
Details on the [isolated agent page](../architecture/isolated-agent.md#a-clean-shell-headless).

## A public repository answered anonymously

*2026-10-27.*
The isolation check proved "no credential" by expecting a remote read to fail.
When the agent gained its first public repository, the read succeeded, because GitHub serves public repositories anonymously, and the check reported a credential that did not exist.
The check now judges each probe by Git's own HTTP trace, looking for an `Authorization` header, and adds a dry-run push that GitHub always authenticates.
A negative test has to be negative for the right reason.

## Health checks stayed green through an outage

*2026-10-31.*
The local model server stayed in an "unload pending" state for 28 minutes and answered every generation request with HTTP 409.
Its health and model-list endpoints stayed healthy the whole time.
One pull request spent all three of its review attempts on the outage without the model ever running.
Failures that happen before the model produces anything are now refunded and retried with backoff, and the reviewer probes recovery with a real one-token request rather than a health endpoint.
The deferral is bounded at eight in a row, so a probe that misreports cannot hold reviews forever.

## Advisory work held the only slot

*2026-10-29 to 2026-11-01.*
Reviews of a branch where the review was not even required held 36% of the reviewer's slot over three days, and authoritative reviews waited behind them for half of all measured waiting time.
The scheduler now selects every required review before any advisory one.
The fix was a selection rule, deliberately not preemption, so a running review always finishes.

## False positives invite placating code

*Measured 2026-11-01.*
When the reviewer blocked a correct change, authors sometimes changed the code until the model was satisfied.
In the audited month four changes were purely placating, made only to get past a finding that was wrong.
The working rule now is to rebut a wrong finding with an executed check on the pull request and order a bounded re-review, never to rewrite correct code for the model.

## A slow prefill looked like a dead connection

*Early November 2026.*
On a pull request with a very large diff, the model read every diff part in a single turn, and processing that much input before producing any output took about ten minutes.
The agent CLI ends a stream that shows no content for roughly that long, so every try was cut off close to finishing, with the model server still working, and the pull request deadlocked.
The repository server now bounds how much it serves per model turn, sized from measurement to leave a wide margin under the CLI's cutoff.
The obvious fix, raising the CLI's idle timeout, was measured and rejected: it replaces the content cutoff rather than extending it, so a genuinely stalled model would run to the per-try deadline instead.

## A publishing failure re-ran a 14-minute review

*2026-11-05.*
Three 5xx responses to one review POST turned a passed review into an error, and the next cycle started the same 14-minute review again on identical inputs.
A decided verdict is now stored, with the exact scanned review body, before publication starts, and a failed publication is retried from that record without the model.
The POST is sent once per attempt, never retried blindly, because creating a review is not idempotent and a 5xx does not prove GitHub created nothing; before this fix one failed publication could send up to twelve.

## Building inside-out

*Recorded 2026-08-18.*
The first prototype of a separate overnight repository auditor was built orchestration-first, before its core invariants were fixed.
Live runs then exposed basic gaps one at a time: malformed model output that crashed the run, evidence read from a dirty working tree rather than the pinned commit, a mandatory second model that exhausted memory, and a model allowed to grade its own evidence.
The postmortem's conclusion was that local models were not the problem; the controller and its tests were insufficiently disciplined, and the user had been acting as the integration test harness.
The rewrite started from the invariants: evidence anchored to Git objects at an exact commit, controller-owned evidence grading, and one certified model on the critical path.
That auditor is [experimental](../evidence/README.md#evidence-index); the lesson carried into everything else.
