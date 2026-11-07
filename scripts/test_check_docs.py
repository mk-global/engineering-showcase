"""Tests for check_docs.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'"""

import datetime as dt
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_docs  # noqa: E402

TODAY = dt.date(2026, 11, 7)


class SlugTests(unittest.TestCase):
    def test_matches_github_anchors(self):
        cases = {
            "Reviewer audit, 2026-11-01": "reviewer-audit-2026-11-01",
            "A clean shell, headless": "a-clean-shell-headless",
            "Decision 1: separate the implementer": "decision-1-separate-the-implementer",
            "The `validate` check": "the-validate-check",
            "Dependencies / Blockers": "dependencies--blockers",
        }
        for heading, slug in cases.items():
            with self.subTest(heading=heading):
                self.assertEqual(check_docs.github_slug(heading), slug)

    def test_duplicate_headings_are_numbered(self):
        self.assertEqual(check_docs.anchors("## Result\n\n## Result\n"), {"result", "result-1"})

    def test_headings_inside_fences_are_ignored(self):
        self.assertEqual(check_docs.anchors("```\n## Not a heading\n```\n## Real\n"), {"real"})


class RepositoryCheckTests(unittest.TestCase):
    def make(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root

    def errors(self, files):
        root = self.make(files)
        report = check_docs.Report()
        for path in check_docs.dated_pages(root):
            check_docs.check_last_verified(path, root, path.read_text(), TODAY, report)
        for path in check_docs.text_files(root):
            text = path.read_text()
            check_docs.check_patterns(path, root, text, report)
            if path.suffix == ".md":
                check_docs.check_links(path, root, text, report)
            elif path.suffix == ".json":
                check_docs.check_json(path, root, text, report)
        return report

    def test_clean_page_passes(self):
        report = self.errors({
            "README.md": "# T\n\nLast verified: 2026-11-01\n\nSee [a](docs/a.md#part-two).\n",
            "docs/a.md": "# A\n\nLast verified: 2026-11-01\n\n## Part two\n",
        })
        self.assertEqual(report.errors, [])

    def test_broken_link_and_anchor_fail(self):
        report = self.errors({
            "README.md": "# T\n\nLast verified: 2026-11-01\n\n[x](nope.md) [y](docs/a.md#missing)\n",
            "docs/a.md": "# A\n\nLast verified: 2026-11-01\n",
        })
        joined = "\n".join(report.errors)
        self.assertIn("broken link: nope.md", joined)
        self.assertIn("missing anchor: docs/a.md#missing", joined)

    def test_links_inside_code_are_not_checked(self):
        report = self.errors({"README.md": "# T\n\nLast verified: 2026-11-01\n\n```\n[x](nope.md)\n```\n`[y](nope.md)`\n"})
        self.assertEqual(report.errors, [])

    def test_missing_future_and_stale_dates(self):
        missing = self.errors({"README.md": "# T\n"})
        self.assertTrue(any("missing 'Last verified" in e for e in missing.errors))
        future = self.errors({"README.md": "# T\n\nLast verified: 2027-01-01\n"})
        self.assertTrue(any("in the future" in e for e in future.errors))
        stale = self.errors({"README.md": "# T\n\nLast verified: 2026-01-01\n"})
        self.assertEqual(stale.errors, [])
        self.assertTrue(any("more than 120 days" in w for w in stale.warnings))

    def test_invalid_json_fails(self):
        report = self.errors({"examples/a.json": '{"a": 1,}\n'})
        self.assertTrue(any("invalid JSON" in e for e in report.errors))

    def test_style_and_disclosure_patterns_fail(self):
        bad = [
            "an em — dash",
            "“curly”",
            "TODO later",
            "/Users/someone/secret",
            "-----BEGIN RSA PRIVATE KEY-----",
            "ghp_" + "a" * 36,
            "http://127.0.0.1:4321",
            "someone@example.com",
        ]
        for line in bad:
            with self.subTest(line=line):
                report = self.errors({"README.md": f"# T\n\nLast verified: 2026-11-01\n\n{line}\n"})
                self.assertTrue(report.errors, line)


if __name__ == "__main__":
    unittest.main()
