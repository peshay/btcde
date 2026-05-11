#!/usr/bin/env python3
"""Guard public artifacts for hygiene leaks before commit or CI publication."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

TEXT_SUFFIXES_WITH_LITERAL_NEWLINES = {
    "",
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "__pycache__",
}

PLACEHOLDER_VALUES = {
    "",
    "api_key",
    "apikey",
    "api_secret",
    "changeme",
    "dummy",
    "example",
    "example_key",
    "example_password",
    "example_secret",
    "example_token",
    "none",
    "null",
    "password",
    "placeholder",
    "secret",
    "sample",
    "test",
    "token",
    "your_api_key",
    "your_api_secret",
    "your_password",
    "your_secret",
    "your_token",
}

LOCAL_PATH_PATTERNS = [
    ("local home path", re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/[^\s`'\"<>]*", re.IGNORECASE)),
    ("windows local path", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s`'\"<>]+", re.IGNORECASE)),
]

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")),
    ("github fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("gitlab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("openai token", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "bearer token",
        re.compile(
            r"\bBearer\s+(?!<|\$\{|TOKEN\b|REDACTED\b)[A-Za-z0-9._~+/=-]{16,}\b",
            re.IGNORECASE,
        ),
    ),
]

SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(?P<key>api[_-]?key|api[_-]?secret|auth[_-]?token|access[_-]?token|secret|password|priv(?:ate)?[_-]?key)\b"
    r"\s*[:=]\s*"
    r"(?P<quote>[\"'])?(?P<value>[^\s,\"'`#}]+)",
    re.IGNORECASE,
)

HEX_VALUE_RE = re.compile(r"^[0-9a-fA-F]{32,}$")
HIGH_ENTROPY_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9_./+=-]{24,}$")


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".pdf"}:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def git_files() -> List[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    output = proc.stdout.decode("utf-8", errors="replace")
    return [line for line in output.split("\0") if line]


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if not path.is_file():
        return True
    return not is_probably_text(path)


def is_placeholder(value: str) -> bool:
    clean = value.strip().strip("'\"`<>{}[](),.;")
    normalized = clean.lower().replace("-", "_")
    if normalized in PLACEHOLDER_VALUES:
        return True
    return normalized.startswith(("example", "sample", "your", "dummy", "placeholder", "changeme"))


def suspicious_assignment_value(value: str) -> bool:
    clean = value.strip().strip("'\"`<>{}[](),.;")
    if is_placeholder(clean):
        return False
    if clean.startswith(("$", "${", "os.environ", "env.")):
        return False
    return bool(HEX_VALUE_RE.match(clean) or HIGH_ENTROPY_RE.match(clean))


def iter_findings(label: str, text: str, suffix: str) -> Iterable[Tuple[int, str, str]]:
    if suffix in TEXT_SUFFIXES_WITH_LITERAL_NEWLINES:
        for line_no, line in enumerate(text.splitlines(), start=1):
            if r"\n" in line:
                yield line_no, "literal escaped newline", "replace backslash-n text with a real line break"

    for name, pattern in LOCAL_PATH_PATTERNS + SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            yield line_no, name, "remove or redact this before publishing"

    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        value = match.group("value")
        if suspicious_assignment_value(value):
            line_no = text.count("\n", 0, match.start()) + 1
            yield line_no, "secret-looking assignment", "use a placeholder or environment variable"


def check_text(label: str, text: str, suffix: str = "") -> List[str]:
    findings = []
    for line_no, name, advice in iter_findings(label, text, suffix.lower()):
        findings.append("{}:{}: {}: {}".format(label, line_no, name, advice))
    return findings


def check_paths(paths: Sequence[str]) -> List[str]:
    findings = []
    for raw_path in paths:
        path = Path(raw_path)
        if should_skip(path):
            continue
        suffix = path.suffix.lower()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            findings.append("{}:0: read error: {}".format(raw_path, exc))
            continue
        findings.extend(check_text(raw_path, text, suffix))
    return findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Files to scan; defaults to git-tracked files with --all")
    parser.add_argument("--all", action="store_true", help="Scan all git-tracked files")
    parser.add_argument("--stdin", action="store_true", help="Scan text from standard input")
    parser.add_argument("--label", default="stdin", help="Label to display for --stdin findings")
    args = parser.parse_args(argv)

    if args.stdin:
        findings = check_text(args.label, sys.stdin.read(), Path(args.label).suffix)
    else:
        files = git_files() if args.all or not args.files else list(args.files)
        findings = check_paths(files)

    if findings:
        print("Public artifact hygiene guard found issues:", file=sys.stderr)
        for finding in findings:
            print("  {}".format(finding), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
