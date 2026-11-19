# Contributing

Thanks for your interest in improving agent-cad-skill! Bug reports, reference notes, example models and fixes are all welcome.

## Ways to contribute

- **Report a bug** — open an issue with the model (or a minimal version of it), the command you ran, and `output/report.json`.
- **Suggest a feature** — open an issue describing the CAD task the agent struggles with.
- **Improve the skill** — clearer instructions in `SKILL.md` or `references/` often help agents more than new code.
- **Add an example** — a small, focused `model.py` that demonstrates one check or technique.

## Development setup

```bash
git clone https://github.com/acikyol/agent-cad-skill.git
cd agent-cad-skill
python3 .agents/skills/agent-cad-skill/scripts/setup_env.py .venv
```

## Running the tests

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python tests/run_tests.py
.venv/bin/python examples/iskele/test_model.py
```

All three must pass before you open a pull request. `tests/run_tests.py` builds every example and compares the result with the expected outcome — `collisions` and `bridges` are **supposed** to fail.

## Guidelines

- **Keep the skill lean.** `SKILL.md` is loaded into the agent's context; every line costs tokens. Put details in `references/`.
- **All files are in English.**
- **Never weaken verification.** A check must not report PASS when it could not actually run — use `NOT_VERIFIED`. See [docs/verification.md](docs/verification.md).
- **Source every off-the-shelf dimension** in examples (official drawing or STEP file, with date).
- **No new dependencies** without a clear reason; if you add one, update `requirements.lock`.
- **One topic per pull request**, with a short description of what changed and how you tested it.
- **Update [CHANGELOG.md](CHANGELOG.md)** under *Unreleased* for user-visible changes.

## Code of Conduct

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
