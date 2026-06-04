# Contributing

Thanks for contributing to btcde.py.

## Requirements
- Python 3.x
- `pip`

## Development Setup
```bash
pip install -e .
pip install -r tests/requirements.txt
pre-commit install --install-hooks
pytest
```

## Branch and Commit Guidelines
- Create a feature branch from `master`.
- Use Conventional Commits, e.g.:
  - `feat: add withdrawal endpoint`
  - `fix: handle empty orderbook response`
  - `docs: clarify API credit costs`

## Pull Request Checklist
- Keep changes focused and minimal.
- Add or update tests for behavior changes.
- Update docs (method list, credit costs) when behavior changes.
- Run `pre-commit run --all-files` before opening a PR.
- Ensure CI is green.

## Security and Secrets
- Never commit real API keys or secrets.
- For vulnerabilities, follow `SECURITY.md`.

## Review Policy
- All PRs require human review before merge.
- AI-assisted changes are welcome, but maintainers are responsible for final correctness.
