# Security Policy

## Trust model

- `model.py` files are **executed as ordinary Python** with your user's permissions. They are not sandboxed. Only build models you wrote or trust.
- The one-line installers download and run `install.py` from this repository. If you prefer to review it first, use the manual install described in the [README](README.md#manual-install).
- The installer writes only to the skill directory and to the agent configuration files listed in the README; `--uninstall` removes those entries.

## Supported versions

Only the latest version on the `main` branch receives fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Include steps to reproduce and the affected files or commands. You can expect a first response within a week.
