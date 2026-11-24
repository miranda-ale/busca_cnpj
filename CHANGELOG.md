# Changelog

History reconstructed from the app's `git tag` and `git log` (read-only) and checked against the files. The date is
that of the commit marked by the tag. The "Unreleased" entries come from commits after `v1.3.6` / `v2.0.0`.

## Git history limits

- **Start of history:** the HEAD has **a single root**, `77634c3` ("docs: reescreve README", 2026-10-13), marked by
  tag `v1.3.2`. It already brings the whole app (API, JS, DocType, tests, CI); the HEAD's git does not show how the
  functions came about. The `CNAE Fornecedor` DocType has a `creation` of 2026-02-23 in its JSON, earlier than the
  history: there was prior work outside it.
- **Tags outside the history:** `v1.3.1` (commit `6462d12`, 2026-10-08, "chore(pyproject): declara
  frappe-dependencies e documenta dependencias") is not an ancestor of HEAD (`git tag --no-merged HEAD`) and is a
  second root. It appears below only by subject, as a range entry, and is not part of the app.
- **Tag types:** `v1.3.2` and `v1.3.3` are annotated; `v1.3.1`, `v1.3.4`, `v1.3.5` and `v1.3.6` are lightweight.
  There are no `rc/*` tags.
- **Tag dates:** `v1.3.3` to `v1.3.6` fall on the same day (2026-10-28), in a sequence of CI and version commits.
- **No tag:** commit `b67b505` (2026-10-31) is after `v1.3.6` and did not change `__version__` (it stayed `1.3.6`).
- **`__version__` vs `app_version`:** `busca_cnpj/__init__.py` was `1.2.2` in tags `v1.3.1` and `v1.3.2` (`v1.3.2`
  went out with an outdated `__version__`, which `v1.3.3` fixed) and follows the tag from `v1.3.3` on (`1.3.6` at
  that HEAD, even after `b67b505`). `hooks.py` does not define `app_version`.
- **Patches:** there are none (`patches.txt` has only the headers). Nothing to note about numbering.
- Commit messages are short; the content of each entry was checked in the files of each commit (`git show --stat`).

## Unreleased

- Naming and language standardization (phase 1): identifiers in Python, JavaScript and tests renamed from Portuguese
  to English (`lookup_cnpj`, `lookup_cep`, `confirm_cnpj_data`, `normalize_cnpj`, `validate_cnpj`, `format_cnpj`,
  `validate_cpf`, `validate_tax_id`, ...); comments, docstrings and documentation translated to English. The old
  Portuguese names of the functions used by `integracoes_customizadas` remain as deprecated aliases (including `buscar_cep`, `formatar_cep`, `formatar_telefone`, `sanitizar_razao_social`, `valor_caractere` and the `setup.py` helpers). DocType,
  fieldnames, payload keys and user-facing messages are unchanged.
- Metadata: publisher StillPulse Tecnologia LTDA, proprietary license, `required_apps` as
  `frappe/frappe@version-15` and `frappe/erpnext@version-15`; new [docs/dependencies.md](docs/dependencies.md) and
  [ADR-004](docs/adr-004-language-and-naming-standardization.md).

## Unreleased · 2026-10-31

- Commit `b67b505` ("feat: máscara progressiva de CPF/CNPJ global"): new `public/js/taxid.js` (`busca_cnpj.taxid`:
  `strip`, `mask`, `bind_input`) loaded across the whole Desk; `app_include_js` in `hooks.py` becomes the list
  `cep.js` + `taxid.js`. Used by `integracoes_customizadas` (Processo Judicial); `__version__` did not change.

## v2.0.0 — Pinned dependencies · 2026-11-02

- `required_apps` becomes `frappe/erpnext@version-15`.
- README: `bench get-app` used `--branch develop` (nonexistent); it is now `main`, with ERPNext on `version-15`.

## v1.3.6 — Closes the CI cycle on main · 2026-10-28

- Commit `60a352d` ("chore: fecha o ciclo do CI na main"): only bumps `__version__` to `1.3.6`. Closes the cycle of
  versions `v1.3.4` and `v1.3.5`, integrated by merge (`13d3dfe`).

## v1.3.5 — Frappe checking tools · 2026-10-28

- Commit `dc589ab` ("ci: ferramentas de checagem do Frappe (commitlint, linter, CI)"), integrated by PR #1
  (`c1edd25`).
- Adds `commitlint.config.js` and the `commitlint` hook in `.pre-commit-config.yaml`; extends
  `.github/workflows/linter.yml` (semantic-commits job on PRs). `__version__` becomes `1.3.5`.

## v1.3.4 — CI also on main · 2026-10-28

- Commit `8af3c26`: the `ci.yml` workflow now also runs on push to the `main` branch (previously only `develop`) and
  the concurrency group is renamed to `ci-busca_cnpj-…`. `__version__` becomes `1.3.4`.

## v1.3.3 — Aligns `__version__` with tag v1.3.2 · 2026-10-28

- Commit `b74d0db`: `__version__` goes from `1.2.2` to `1.3.3` (the message says "alinha com a v1.3.2"; the recorded
  value is `1.3.3`, that of the tag itself).

## v1.3.2 — README rewrite (recorded initial state) · 2026-10-13

Root of the history (`77634c3`, "docs: reescreve README"). State of the code at this tag, checked in the files, and
not changes made in it:

- **Supplier:** CNPJ *Buscar* button with a confirmation dialog (`buscar_cnpj`, `confirmar_dados_cnpj`) that updates
  the supplier and creates Address, Contact (partner, phone, e-mail) and CNAEs; mask and validation of numeric and
  alphanumeric CNPJ and of CPF, in the form and on the server (`doc_events` → `Supplier.validate`); legal-name
  sanitization; child table `CNAE Fornecedor`.
- **Sources:** CNPJ.ws, with fallback to BrasilAPI and Minha Receita (15 s timeout); CNPJ.ws response converted to
  the BrasilAPI format.
- **CEP:** ViaCEP lookup on Address and Employee (`cep.js`, `address.js`, `employee.js`); Custom Fields `cnaes`,
  `custom_current_cep` and `custom_bairro`; Address layout adjustment.
- **Installation/migration:** `after_install`/`after_migrate` create the Custom Fields and disable legacy Supplier
  Client/Server Scripts that validate CNPJ with digits only.
- **Tests:** `tests/test_cnpj.py` with 9 CNPJ tests (no API tests).
- **Infrastructure:** `.pre-commit-config.yaml`, `.eslintrc`, `.editorconfig`, workflows `ci.yml` and `linter.yml`.

## v1.3.1 (outside the HEAD history) — pyproject · 2026-10-08

Range entry, described only by the subject of commit `6462d12`: "declara frappe-dependencies e documenta
dependencias". It is a **separate root** (no parent) that already contains the whole app, outside the HEAD history.
By the difference between the tags (`git diff v1.3.1 v1.3.2`), `v1.3.2` changes only `README.md` relative to it;
hence `v1.3.1` already had the same code and `pyproject.toml` (inference from the diff).
