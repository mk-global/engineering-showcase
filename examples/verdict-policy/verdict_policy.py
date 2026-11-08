"""Illustrative deterministic verdict policy for a model-assisted code review.

This is a standalone example written for the engineering showcase. It shows the
shape of the decision described in docs/architecture/independent-reviewer.md:
the model proposes a verdict and findings, and this code alone decides whether
the required status is success, failure or error. It is not the platform's
implementation.

Licensed under the MIT License (see LICENSE-CODE).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

SEVERITIES = ("P1", "P2", "P3", "INFO")
BLOCKING_SEVERITIES = frozenset({"P1", "P2"})
MODEL_VERDICTS = ("PASS", "CHANGES_REQUIRED", "NEEDS_DEEPER_REVIEW")
DEFAULT_MINIMUM_CONFIDENCE = 0.80


@dataclass(frozen=True)
class Decision:
    """The controller's decision. `state` is the commit status to publish."""

    state: str  # "success", "failure" or "error"
    description: str


class MalformedResult(ValueError):
    """The model's output did not match the review contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MalformedResult(message)


def _confidence(value: Any, where: str) -> float:
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{where}: confidence must be a number",
    )
    _require(0.0 <= float(value) <= 1.0, f"{where}: confidence must be between 0 and 1")
    return float(value)


def validate(result: Any) -> Mapping[str, Any]:
    """Check the parts of the review contract the decision depends on."""
    _require(isinstance(result, Mapping), "result must be an object")
    _require(result.get("verdict") in MODEL_VERDICTS, "verdict is not a known value")
    _confidence(result.get("confidence"), "result")
    findings = result.get("findings")
    _require(isinstance(findings, Sequence) and not isinstance(findings, (str, bytes)), "findings must be a list")
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        _require(isinstance(finding, Mapping), f"{where} must be an object")
        _require(finding.get("severity") in SEVERITIES, f"{where}: unknown severity")
        _confidence(finding.get("confidence"), where)
    return result


def decide(result: Any, minimum_confidence: float = DEFAULT_MINIMUM_CONFIDENCE) -> Decision:
    """Decide the required status from a model's review result.

    The order matters: a result that fails validate() is an error, never a
    pass, and any blocking finding fails the gate whatever the model's own
    verdict says. validate() checks only the fields this decision uses: it does
    not reject a result that lacks other contract fields or carries extra ones,
    so a real controller validates the whole result against its schema first.
    """
    try:
        result = validate(result)
    except MalformedResult as exc:
        return Decision("error", f"Review could not complete: {exc}")

    blocking = [f for f in result["findings"] if f["severity"] in BLOCKING_SEVERITIES]
    if blocking:
        return Decision("failure", f"Review found {len(blocking)} blocking issue(s)")
    if result["verdict"] == "CHANGES_REQUIRED":
        return Decision("failure", "Review requested changes")
    if result["verdict"] == "NEEDS_DEEPER_REVIEW":
        return Decision("failure", "Review was inconclusive")
    if float(result["confidence"]) < minimum_confidence:
        return Decision("failure", "Review was inconclusive (confidence below threshold)")
    return Decision("success", "Review passed")
