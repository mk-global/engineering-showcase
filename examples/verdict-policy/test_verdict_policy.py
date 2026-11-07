"""Tests for the illustrative verdict policy. Run: python3 -m unittest discover -s examples/verdict-policy -p 'test_*.py'"""

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from verdict_policy import decide  # noqa: E402

EXAMPLE = pathlib.Path(__file__).resolve().parents[1] / "review-result.example.json"


def result(verdict="PASS", confidence=0.9, findings=()):
    return {"verdict": verdict, "confidence": confidence, "findings": list(findings)}


def finding(severity, confidence=0.9):
    return {"severity": severity, "confidence": confidence}


class DecideTests(unittest.TestCase):
    def test_clean_pass_succeeds(self):
        self.assertEqual(decide(result()).state, "success")

    def test_any_blocking_finding_fails_even_when_the_model_says_pass(self):
        for severity in ("P1", "P2"):
            with self.subTest(severity=severity):
                self.assertEqual(decide(result(findings=[finding(severity)])).state, "failure")

    def test_non_blocking_findings_do_not_block(self):
        self.assertEqual(decide(result(findings=[finding("P3"), finding("INFO")])).state, "success")

    def test_changes_required_fails_without_findings(self):
        self.assertEqual(decide(result(verdict="CHANGES_REQUIRED")).state, "failure")

    def test_needs_deeper_review_is_a_failure_not_an_error(self):
        decision = decide(result(verdict="NEEDS_DEEPER_REVIEW"))
        self.assertEqual(decision.state, "failure")
        self.assertIn("inconclusive", decision.description)

    def test_low_confidence_pass_fails(self):
        self.assertEqual(decide(result(confidence=0.79)).state, "failure")
        self.assertEqual(decide(result(confidence=0.80)).state, "success")

    def test_malformed_output_is_an_error_never_a_pass(self):
        cases = [
            None,
            "PASS",
            {},
            result(verdict="APPROVE"),
            result(confidence="high"),
            result(confidence=True),
            result(confidence=1.5),
            {"verdict": "PASS", "confidence": 0.9, "findings": "none"},
            result(findings=[finding("CRITICAL")]),
            result(findings=[{"severity": "P3"}]),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(decide(case).state, "error")

    def test_bundled_example_result_is_decided(self):
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(decide(example).state, "failure")


if __name__ == "__main__":
    unittest.main()
