#!/usr/bin/env python3
"""Deterministic documentation checks for the engineering showcase.

Usage:
  python3 scripts/check_docs.py check [--today YYYY-MM-DD]
  python3 scripts/check_docs.py extract-mermaid OUTPUT_DIR

`check` exits 1 on any failure and prints GitHub annotations. It verifies the
required structure, the `Last verified` convention, internal links and heading
anchors, JSON syntax, mechanical style rules, and generic disclosure patterns. Standard
library only, so a local run and a CI run reach the same verdict.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "LICENSE-CODE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "docs/operating-model.md",
    "docs/architecture/isolated-agent.md",
    "docs/architecture/github-authorization.md",
    "docs/architecture/independent-reviewer.md",
    "docs/workflows/delivery-lifecycle.md",
    "docs/decisions/README.md",
    "docs/lessons/README.md",
    "docs/evidence/README.md",
    "docs/security.md",
    "docs/roadmap.md",
    "examples/README.md",
]

# Pages that state claims and therefore carry a `Last verified` line.
DATED_GLOBS = ["README.md", "SECURITY.md", "CONTRIBUTING.md", "docs/**/*.md", "examples/README.md"]
STALE_AFTER_DAYS = 120
LAST_VERIFIED = re.compile(r"^Last verified: (\d{4}-\d{2}-\d{2})$")

# Files whose text is checked for style and disclosure. Licenses are verbatim
# legal text and this script necessarily contains the patterns it looks for.
TEXT_SUFFIXES = {".md", ".json", ".yml", ".yaml", ".py", ".txt", ".jsonc"}
EXCLUDED = {"LICENSE", "LICENSE-CODE", "scripts/check_docs.py", "scripts/test_check_docs.py"}

STYLE_RULES = [
    ("em dash", re.compile("—")),
    ("curly quote", re.compile("[‘’“”]")),
    ("unresolved marker", re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b")),
]

DISCLOSURE_RULES = [
    ("absolute home path", re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("cloud key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("chat token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]+")),
    ("loopback endpoint", re.compile(r"\b(?:127\.0\.0\.1|localhost):\d+")),
    ("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")),
]

FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`[^`]*`")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: str, line: int, message: str) -> None:
        self.errors.append(f"::error file={path},line={line}::{message}")

    def warn(self, path: str, line: int, message: str) -> None:
        self.warnings.append(f"::warning file={path},line={line}::{message}")


def rel(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def prose_lines(text: str) -> Iterable[tuple[int, str, bool]]:
    """Yield (line number, line, inside a fenced block)."""
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker[0] * len(marker)
                yield number, line, True
                continue
            if marker[0] == fence[0] and len(marker) >= len(fence) and not match.group(2).strip():
                fence = None
                yield number, line, True
                continue
        yield number, line, fence is not None


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: strip markup, lowercase, keep word characters, hyphens and spaces."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(text: str) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for _, line, fenced in prose_lines(text):
        if fenced:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        slug = github_slug(match.group(2))
        if slug in counts:
            counts[slug] += 1
            found.add(f"{slug}-{counts[slug]}")
        else:
            counts[slug] = 0
            found.add(slug)
    return found


def check_links(path: pathlib.Path, root: pathlib.Path, text: str, report: Report) -> None:
    cache: dict[pathlib.Path, set[str]] = {}
    for number, line, fenced in prose_lines(text):
        if fenced:
            continue
        for target in LINK.findall(INLINE_CODE.sub("", line)):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue  # external (https:, mailto:) links are not checked here
            file_part, _, fragment = target.partition("#")
            destination = (path.parent / file_part).resolve() if file_part else path
            try:
                destination.relative_to(root.resolve())
            except ValueError:
                report.error(rel(path, root), number, f"link leaves the repository: {target}")
                continue
            if not destination.exists():
                report.error(rel(path, root), number, f"broken link: {target}")
                continue
            if fragment:
                if destination.is_dir() or destination.suffix != ".md":
                    report.error(rel(path, root), number, f"anchor on a non-Markdown target: {target}")
                    continue
                if destination not in cache:
                    cache[destination] = anchors(destination.read_text(encoding="utf-8"))
                if fragment not in cache[destination]:
                    report.error(rel(path, root), number, f"missing anchor: {target}")


def check_last_verified(path: pathlib.Path, root: pathlib.Path, text: str, today: dt.date, report: Report) -> None:
    for number, line in enumerate(text.splitlines()[:6], start=1):
        match = LAST_VERIFIED.match(line.strip())
        if not match:
            continue
        try:
            verified = dt.date.fromisoformat(match.group(1))
        except ValueError:
            report.error(rel(path, root), number, "Last verified date is not a valid date")
            return
        if verified > today:
            report.error(rel(path, root), number, "Last verified date is in the future")
        elif (today - verified).days > STALE_AFTER_DAYS:
            report.warn(
                rel(path, root),
                number,
                f"Last verified {verified} is more than {STALE_AFTER_DAYS} days old; re-verify or mark as historical",
            )
        return
    report.error(rel(path, root), 1, "missing 'Last verified: YYYY-MM-DD' in the first lines")


def check_patterns(path: pathlib.Path, root: pathlib.Path, text: str, report: Report) -> None:
    for number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in STYLE_RULES + DISCLOSURE_RULES:
            if pattern.search(line):
                report.error(rel(path, root), number, f"{name} found")


def check_json(path: pathlib.Path, root: pathlib.Path, text: str, report: Report) -> None:
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        report.error(rel(path, root), exc.lineno, f"invalid JSON: {exc.msg}")


def text_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        name = rel(path, root)
        if name in EXCLUDED or "node_modules" in path.parts:
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


def dated_pages(root: pathlib.Path) -> list[pathlib.Path]:
    pages: set[pathlib.Path] = set()
    for pattern in DATED_GLOBS:
        pages.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(pages)


def run_checks(root: pathlib.Path, today: dt.date) -> Report:
    report = Report()
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            report.error(name, 1, "required file is missing")
    for path in dated_pages(root):
        check_last_verified(path, root, path.read_text(encoding="utf-8"), today, report)
    for path in text_files(root):
        text = path.read_text(encoding="utf-8")
        check_patterns(path, root, text, report)
        if path.suffix == ".md":
            check_links(path, root, text, report)
        elif path.suffix == ".json":
            check_json(path, root, text, report)
    return report


def extract_mermaid(root: pathlib.Path, output: pathlib.Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.relative_to(root).parts or "node_modules" in path.parts:
            continue
        block: list[str] | None = None
        start = 0
        for number, line, _ in prose_lines(path.read_text(encoding="utf-8")):
            stripped = line.strip()
            if block is None and stripped.startswith("```mermaid"):
                block, start = [], number
            elif block is not None and stripped.startswith("```"):
                count += 1
                stem = rel(path, root).replace("/", "__").removesuffix(".md")
                (output / f"{stem}__L{start}.mmd").write_text("\n".join(block) + "\n", encoding="utf-8")
                block = None
            elif block is not None:
                block.append(line)
    return count


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    extract = sub.add_parser("extract-mermaid")
    extract.add_argument("output", type=pathlib.Path)
    args = parser.parse_args(argv)

    if args.command == "extract-mermaid":
        count = extract_mermaid(ROOT, args.output)
        print(f"extracted {count} Mermaid diagram(s)")
        return 0 if count else 1

    report = run_checks(ROOT, args.today)
    for line in report.warnings + report.errors:
        print(line)
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
