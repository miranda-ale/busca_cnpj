# busca_cnpj

See `AGENTS.md` for the language and naming rules and the lint workflow.

## Dependencies

- `required_apps = ["frappe/frappe@version-15", "frappe/erpnext@version-15"]`. It is consumed by
  `integracoes_customizadas` (Legal module and Bionexo import), which declares it in `required_apps`; changes to
  `busca_cnpj.cnpj` and `busca_cnpj.api` affect that app. Strong and weak dependencies are listed in
  [docs/dependencies.md](docs/dependencies.md).
- The Portuguese function names (`buscar_cnpj`, `confirmar_dados_cnpj`, `formatar_cnpj`, `normalizar_cnpj`,
  `validar_cnpj`, `validar_cpf`, `validar_tax_id`) remain as deprecated aliases for external consumers. Do not remove
  them before `integracoes_customizadas` migrates to the English names.
- There are no patches. Tests live in `busca_cnpj/tests/` (`test_cnpj.py`).

## Version, tags and documentation

- `__version__` in `busca_cnpj/__init__.py` must match the tag (currently `2.0.0`). Check it before creating the tag.
- **A `feature/*` branch uses the `main` major + 1** (in force since 2026-11-01). Minor and patch run normally inside
  it: with `main` at `vX.Y.Z`, the feature starts at `v(X+1).0.0` and continues `v(X+1).0.1`, `v(X+1).1.0`... while on
  the branch. If `main` bumps its major, the feature bumps with it. Check the `main` version
  (`git show main:busca_cnpj/__init__.py`) and `git tag` before tagging, and never reuse an existing number.
- Tags outside the HEAD history (`git tag --no-merged HEAD`) are not part of the app; ignore `rc/*` tags in the
  CHANGELOG.
- `README.md` and `CHANGELOG.md` are maintained by hand, only with what is committed; update both together with
  behavior changes.
- Overview of the dependencies between apps: `../../CLAUDE.md`.

## Language and naming

Source of truth: [`clm/docs/naming-conventions.md`](https://github.com/still-pulse/clm/blob/main/docs/naming-conventions.md).

- Identifiers, documentation, comments, docstrings and commit messages in **English**; user-facing labels in pt-BR
  (`label`, `translations/`).
- DocTypes carry the app prefix; Reports, Print Formats and Workspaces use ASCII-only names.
- Custom Fields on `Employee`/`Designation` (and other core DocTypes) are `custom_<app>_<meaning>`.
- New patches are `sNN_<action_in_snake_case>`, registered in `patches.txt`.
- Roles created by the app are prefixed with the app name.
