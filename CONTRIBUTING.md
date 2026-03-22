# Contributing to ShareClaw

Thanks for wanting to contribute. ShareClaw is deliberately simple -- one core file, zero dependencies, works with any LLM. Let's keep it that way.

## How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Run tests: `pytest`
5. Push and open a PR

## Development setup

```bash
git clone https://github.com/<your-fork>/shareclaw.git
cd shareclaw
pip install -e .
pytest
```

That's it. No Docker, no build tools, no config files.

## Code style

- **Keep it simple.** The entire core is one file (`shareclaw/core.py`). If your change makes sense there, put it there.
- **No over-engineering.** No abstract base classes, no factory patterns, no dependency injection. Just functions and one class.
- **Standard library only** for the core. `json`, `os`, `time`, `pathlib` -- that's the dependency list. Keep it that way.
- **Type hints** are welcome but not required.
- **Docstrings** on public methods.

## PRs we want

- **Integrations** -- CrewAI, AutoGen, LangGraph, OpenClaw, Claude Code adapters. These go in `examples/` or a separate integration package, not in core.
- **New protocols** -- if you have a multi-agent coordination pattern that works in production, add it to `protocols/`.
- **Examples** -- real-world usage in `examples/`. Show your shared_brain.md, your execution.md, your results.
- **Bug fixes** -- always welcome.
- **Tests** -- always welcome.
- **Documentation** -- especially integration guides.

## PRs we don't want

- **Breaking the single-file simplicity.** If your PR splits `core.py` into multiple files, it will be declined.
- **Adding heavy dependencies.** No SQLAlchemy, no Redis, no Celery. The core must stay zero-dependency (standard library only).
- **Abstract layers.** No `BaseBrain`, no `BrainInterface`, no plugin systems. One class. One file.
- **Framework lock-in.** ShareClaw works with any LLM, any framework, any language. Don't make it require a specific one.
- **Config file proliferation.** No YAML configs, no TOML configs for runtime. The brain state is JSON. The protocols are markdown. That's the config.

## Testing

```bash
pytest                    # run all tests
pytest tests/test_core.py # run specific test file
pytest -v                 # verbose output
```

Write tests for any new functionality. Tests go in `tests/`.

## Questions?

Open an issue. Keep it short.
