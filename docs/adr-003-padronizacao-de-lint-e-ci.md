# ADR-003: Lint and CI standardization

## Status

Accepted (2026-11-21).

## Context

The 10 Frappe apps of the ecosystem are being prepared for unification and for the v15 -> v16/v17 migration. The
apps diverged in lint and CI (Python version, ruff version and rules, ignores, pre-commit excludes, JS hooks), which
makes it harder to review and move code between them. This ADR records the common configuration adopted and the
decisions made when applying it to `busca_cnpj`.

## Decision

1. Python version: the current minimum **3.11 is kept** (`target-version = "py311"`, `requires-python = ">=3.11"`,
   `linter.yml` on 3.11) because of a production constraint. Production and staging were confirmed on **Python 3.12**,
   and `ci.yml` now runs the tests on 3.12 to mirror production; the 3.14 used before is incompatible with Frappe v15
   (freezegun breaks at collection: `AttributeError: module 'uuid' has no attribute '_load_system_functions'`). The
   migration target for Frappe v16 is `>=3.13` (`target-version = "py313"`, `requires-python = ">=3.13"`,
   `linter.yml` and `ci.yml` consistent), to be done in the migration itself.
2. ruff pinned to v0.16.10 through `ruff-pre-commit`, rules `F,E,W,I,UP,B,RUF` and an `ignore` list identical to
   CLM's.
3. pyupgrade covered by ruff's `UP` rule, with no separate hook.
4. F401 is **not** ignored: dead imports are removed; re-exports/side-effect imports are kept with
   `# noqa: F401  # <reason>`. User-visible strings with an ambiguous unicode character get `# noqa: RUF001` instead
   of changing the text.
5. prettier 2.7.1 and eslint 8.44.0 kept (upgrade postponed, to avoid mixing it with the standardization; review when
   preparing for v16/v17).
6. The pre-commit `exclude` entries are always paths of the repository itself; dead entries were removed, without
   widening the ignored scope.
7. ESLint globals are declared in `.eslintrc` with minimal scope. In this repository: only `busca_cnpj`
   (`"writable"`), the app's own namespace created by `frappe.provide`. No `overrides` needed.
8. JS files with Jinja are excluded from prettier/eslint by exact path. In this repository: none.
9. JS formatted by prettier in a style-only commit. In this repository: 3 files (`cep.js`, `supplier.js`,
   `taxid.js`).
10. pip-audit runs only in CI and audits only the `pyproject` (the erpnext/hrms dependencies are commented out), so
    it covers little: pending.
11. commitlint kept and `pre-commit install` documented in `AGENTS.md`.
12. No tag and no `__version__` change in this standardization.

## Consequences

- Identical lint and formatting across the apps, easing unification and cross-review.
- Dead imports show up as errors (F401) and need removal or a justified `noqa`.
- prettier/eslint versions stay outdated until the preparation for v16/v17.
- ESLint now actually validates the JS; the `busca_cnpj` namespace is accepted as a global, but typos in it are no
  longer detected.

## State of this repository

| Item | State |
| --- | --- |
| F401 | 1 import removed (`import frappe` in `cnae_fornecedor.py`, commit `fix: corrigir erros do ruff check`); 0 kept with `noqa`; `F401` removed from the ignore list in `pyproject.toml` |
| Excludes changed | Dead prettier and eslint entries removed (`public/dist`, `templates/includes`, `public/js/lib`, `cypress`); `node_modules` and `boilerplate` kept |
| ESLint | `no-undef` for `busca_cnpj` (25 occurrences in 5 files) resolved with the global; no real bug found |
| Prettier | 3 JS files reformatted (style only) |
| pre-commit (`SKIP=commitlint pre-commit run --all-files`) | All hooks pass |

## Pending

- Migrate to `>=3.13` together with v16; also review the prettier/eslint versions when preparing for v16/v17.
- Extend pip-audit to cover the erpnext/hrms dependencies (currently commented out).
- Evaluate migrating `.eslintrc` to the flat configuration when eslint is upgraded.
