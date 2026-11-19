# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-19

### Added

- Agent skill with a clarify → research → model → build & verify → report workflow.
- `build.py`: STEP / STL / DXF export, solid and mesh validity, print-bed fit, support-free printing (bridges vs. overhangs), collision and clearance checks, user requirement checks, isolated preview rendering, Markdown/JSON reports and change manifest.
- PASS / FAIL / NOT_VERIFIED result model; overall PASS is never emitted automatically.
- Optional FreeCAD `.FCStd` export with safe replacement of existing documents.
- Installers for macOS, Linux and Windows; global and per-project installation for Claude Code, Cursor, Zed, Codex, GitHub Copilot, Antigravity (CLI and App) and `AGENTS.md`-based agents.
- Pinned, tested dependency set (`requirements.lock`).
- Examples: bracket, Iskele desk organizer, and two models that fail on purpose (collisions, bridges).
- Self-tests and regression tests.

[Unreleased]: https://github.com/acikyol/agent-cad-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/acikyol/agent-cad-skill/releases/tag/v1.0.0
