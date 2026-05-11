# Public artifact hygiene

Public artifacts include pull request text, review comments, commit messages, release notes, and repository docs. Keep those artifacts safe to publish.

## Run locally

Install and run the hook from the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pre-commit
pre-commit install --install-hooks
pre-commit run public-artifact-hygiene --all-files
```

For text that is not stored in the repo yet, pipe it through the same guard before publishing:

```bash
cat pr-body.md | python3 tools/check_public_artifacts.py --stdin --label pr-body.md
```

CI runs the same pre-commit hook on pull requests.

## What the guard blocks

The check fails on public-facing files when it finds:

- Local workstation or agent runtime paths.
- Prompt text, private model notes, scratch notes, or private routing metadata.
- Authorization headers, credential assignments, tokens, or private key blocks.
- Trading, payment, or banking write-operation wording that implies use of real accounts or funds.
- Escaped newline markers in prose where real line breaks should be used.

## Fix and rerun

1. Replace private details with neutral placeholders such as `<PROJECT_REPO>`, `<LOCAL_PATH_REDACTED>`, or `<REDACTED_SECRET>`.
2. Rewrite unsafe prose so it describes mocked or fixture-based behavior, not real account or funds movement.
3. Convert escaped newline markers in commit or PR text into real line breaks.
4. Rerun `pre-commit run public-artifact-hygiene --all-files` and, for PR text, rerun the standard input command above.
