# busca_cnpj

The rest of the repository instructions is in `CLAUDE.md`. Versioning rule:

- **A `feature/*` branch uses the `main` major + 1** (in force since 2026-11-01). Minor and patch run normally inside
  it: with `main` at `vX.Y.Z`, the feature starts at `v(X+1).0.0` and continues `v(X+1).0.1`, `v(X+1).1.0`... while on
  the branch. If `main` bumps its major, the feature bumps with it. Check the `main` version
  (`git show main:busca_cnpj/__init__.py`) and `git tag` before tagging, and never reuse an existing number.

## Language and naming

Source of truth: [`clm/docs/naming-conventions.md`](https://github.com/still-pulse/clm/blob/main/docs/naming-conventions.md)
and [`clm/docs/fixtures-and-migrations.md`](https://github.com/still-pulse/clm/blob/main/docs/fixtures-and-migrations.md).

- Identifiers (functions, modules, variables, files), documentation, comments, docstrings and commit messages are in
  **English**. User-facing labels and messages stay in pt-BR (`label`, `translations/`).
- New DocTypes use the app prefix; Reports, Print Formats and Workspaces have ASCII-only names (accents only in
  `label`).
- Custom Fields on core DocTypes (for example `Employee`, `Designation`) are named `custom_<app>_<meaning>`.
- New patches are `sNN_<action_in_snake_case>` in `busca_cnpj/patches/`, registered in `patches.txt`; released
  patches are never renamed or edited.
- Roles created by the app are prefixed with the app name.
- Do not rename DocTypes, fieldnames, roles or persisted strings in a refactor: that is a dedicated migration.

## Lint and pre-commit

- Run `pre-commit install` once after cloning the repository.
- CI (`.github/workflows/linter.yml`) runs pre-commit, semgrep and pip-audit.
- Lint and CI decisions: [docs/adr-003-padronizacao-de-lint-e-ci.md](docs/adr-003-padronizacao-de-lint-e-ci.md).
