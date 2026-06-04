# Security Policy

## Supported Versions
The `master` branch and the latest release on PyPI are the actively supported lines.

## Reporting a Vulnerability
Please do not open public issues for security vulnerabilities.

Report privately by email to security@ahu.services and include:
- affected component or function
- impact and attack scenario
- reproduction steps
- suggested mitigation if available

You will receive an acknowledgement as soon as possible, and we will coordinate remediation and disclosure timing.

## Hardening Notes
- Treat API keys and secrets as sensitive; never commit them or paste them into issues.
- Keep `ssl_verify=True` in production.
- Keep dependencies (`requests`, `urllib3`) up to date.
