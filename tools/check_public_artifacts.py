#!/usr/bin/env python3
"""Check public-facing repository artifacts for unsafe disclosure patterns."""
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Pattern, Tuple


PUBLIC_SUFFIXES = {
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
    "__pycache__",
    "build",
    "dist",
}


@dataclass(frozen=True)
class Rule:
    code: str
    description: str
    pattern: Pattern


def _rx(value: str, flags: int = re.IGNORECASE) -> Pattern:
    return re.compile(value, flags)


RULES = [
    Rule(
        "literal-escaped-newline",
        "literal escaped newline sequence; use real line breaks in public prose",
        _rx(r"\\n", 0),
    ),
    Rule(
        "openclaw-path",
        "internal agent/runtime path or metadata",
        _rx(r"(?:/root|/home/[A-Za-z0-9_.-]+)/[.]openclaw\b|[.]openclaw\b|workspace-[A-Za-z0-9_.-]+|agents/[^\s]+/sessions"),
    ),
    Rule(
        "local-user-path",
        "local workstation path",
        _rx(r"(?:/Users/[A-Za-z0-9_.-]+\b|/mnt/data\b|C:\\\\Users\\\\[A-Za-z0-9_.-]+)"),
    ),
    Rule(
        "prompt-leakage",
        "prompt, hidden reasoning, or scratchpad leakage",
        _rx(r"\b(?:system|developer) prompt\b|chain[- ]of[- ]thought|hidden reasoning|scratchpad|subagent context"),
    ),
    Rule(
        "board-routing-leakage",
        "private board, owner, or routing metadata",
        _rx(r"\bplanka[_-][A-Za-z0-9_-]+\b|\bOwner:\s|\binternal board routing\b|\bboard id\b|\bcard id\b"),
    ),
    Rule(
        "auth-header",
        "authorization header or bearer token material",
        _rx(r"\bAuthorization\s*:\s*(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    ),
    Rule(
        "secret-assignment",
        "secret or credential assignment with a non-placeholder value",
        _rx(r"\b(?:API[_-]?KEY|API[_-]?SECRET|X[-_]?API[-_]?KEY|X[-_]?API[-_]?SIGNATURE|HMAC[_-]?SIGNATURE|WEBHOOK[_-]?SECRET|REPO[_-]?(?:USER|PASS)|SVC[_-]?PASS|PRIVATE[_-]?KEY|AWS[_-]?SECRET[_-]?ACCESS[_-]?KEY|AWS[_-]?SESSION[_-]?TOKEN|BUNQ[_-]?API[_-]?KEY)\b\s*[:=]\s*(?![<{$][A-Z0-9_{}$.-]+[>}]?\b)[\"']?[A-Za-z0-9_./+=:-]{8,}"),
    ),
    Rule(
        "private-key-block",
        "private key block",
        _rx(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    Rule(
        "live-write-token",
        "live trading, payment, or banking write-operation wording",
        _rx(r"\b(?:live|real|production)\s+(?:trade|trading|order|payment|withdrawal|deposit|bank transfer)\b|\b(?:execute|place|submit|cancel|withdraw|deposit|pay|transfer)\s+(?:a\s+)?(?:live|real|production)?\s*(?:trade|order|payment|withdrawal|deposit|bank transfer)\b"),
    ),
]


def is_probably_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def public_artifact_paths(root: Path) -> List[Path]:
    paths = []  # type: List[Path]
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in PUBLIC_SUFFIXES or path.name in {"MANIFEST", "LICENSE"}:
            paths.append(path)
    return paths


def should_scan(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in PUBLIC_SUFFIXES or path.name in {"MANIFEST", "LICENSE"}


def line_col(text: str, offset: int) -> Tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return line, offset - line_start + 1


def check_text(label: str, text: str) -> List[str]:
    failures = []  # type: List[str]
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            line, col = line_col(text, match.start())
            failures.append(f"{label}:{line}:{col}: {rule.code}: {rule.description}")
    return failures


def decode_path(path: Path) -> Optional[str]:
    if is_probably_binary(path):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check public-facing artifacts for local paths, prompts, secrets, and malformed escaped newlines."
    )
    parser.add_argument("paths", nargs="*", help="Files to check. If omitted, scan public artifact files in the repository.")
    parser.add_argument("--stdin", action="store_true", help="Check text from standard input as a public artifact.")
    parser.add_argument("--label", default="<stdin>", help="Label to use with --stdin diagnostics.")
    args = parser.parse_args(argv)

    failures = []  # type: List[str]
    if args.stdin:
        failures.extend(check_text(args.label, sys.stdin.read()))
    else:
        if args.paths:
            candidates = [Path(path) for path in args.paths]
        else:
            candidates = public_artifact_paths(Path.cwd())
        for path in candidates:
            if not should_scan(path):
                continue
            text = decode_path(path)
            if text is None:
                continue
            failures.extend(check_text(str(path), text))

    if failures:
        print("Public artifact hygiene check failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print("\nReplace sensitive details with neutral placeholders, convert escaped newline sequences to real line breaks, then rerun the check.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
