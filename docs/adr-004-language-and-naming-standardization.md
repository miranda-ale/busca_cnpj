# ADR-004: Language and naming standardization (phase 1)

## Status

Accepted (2026-11-24).

## Context

The 10 Frappe apps of the ecosystem (`bhcl_site`, `rh_brasil`, `busca_cnpj`, `integracoes_customizadas`,
`assinatura_eletronica`, `clm`, `pdf_ocr`, `pulse_gestor`, `pulse_finance`, `pulse_process`) are being prepared to be
unified and migrated from Frappe v15 to v16. They mixed Portuguese and English in documentation, comments,
identifiers and filenames, which makes cross-app review and code moving harder. The target standard is the one
already used by `clm`: `clm/docs/naming-conventions.md` and `clm/docs/fixtures-and-migrations.md`.

This ADR records the phase 1 decisions and what changed in `busca_cnpj`. Phase 1 is limited to naming and language:
it changes no DocType name, fieldname, role, persisted string or user-facing text (that is phase 2).

## Decision

1. **English** for documentation, comments, docstrings, identifiers (functions, modules, variables, files) and
   commit messages. User-facing labels and messages stay in **pt-BR** (`label`, `__()`/`_()` source strings,
   `translations/`).
2. App metadata: `app_publisher = "StillPulse Tecnologia LTDA"`, `app_license = "Proprietary"` (`license.txt`),
   copyright header "StillPulse Tecnologia LTDA and contributors".
3. `required_apps` as a uniform list of `"org/repo@branch"` strings; here
   `["frappe/frappe@version-15", "frappe/erpnext@version-15"]`.
4. The rule for new code is recorded in `AGENTS.md` and `CLAUDE.md` ("Language and naming").
5. Public names consumed by other apps are renamed but keep deprecated Portuguese aliases until the consumers migrate.

## What changed in this repository

### Public functions

| Old name | New name |
| --- | --- |
| `busca_cnpj.api.buscar_cnpj` (whitelisted) | `busca_cnpj.api.lookup_cnpj` |
| `busca_cnpj.api.buscar_cep` (whitelisted) | `busca_cnpj.api.lookup_cep` |
| `busca_cnpj.api.confirmar_dados_cnpj` (whitelisted) | `busca_cnpj.api.confirm_cnpj_data` |
| `busca_cnpj.api.formatar_cep` | `format_cep` |
| `busca_cnpj.api.formatar_telefone` | `format_phone` |
| `busca_cnpj.api.sanitizar_razao_social` | `sanitize_company_name` |
| `busca_cnpj.cnpj.normalizar_cnpj` | `normalize_cnpj` |
| `busca_cnpj.cnpj.validar_cnpj` | `validate_cnpj` |
| `busca_cnpj.cnpj.formatar_cnpj` | `format_cnpj` |
| `busca_cnpj.cnpj.validar_cpf` | `validate_cpf` |
| `busca_cnpj.cnpj.validar_tax_id` | `validate_tax_id` |
| `busca_cnpj.cnpj.valor_caractere` | `character_value` |

Private helpers (`_consultar_api`, `_normalizar_cnpjws`, `_criar_endereco`, `_criar_contato`, ...) and the helpers in
`setup.py` and the JavaScript files were renamed too; they have no external consumers.

### Parameter and payload changes

- `confirm_cnpj_data(supplier_name, data)`: the second parameter was `dados`. Callers passing it positionally (as
  `integracoes_customizadas` does) are unaffected; keyword callers must use `data`. The JS of this app was updated.
- The keys of the dictionary returned by `lookup_cnpj` (`razao_social`, `nome_fantasia`, `cnpj_formatado`,
  `situacao_cadastral`, `situacao_ativa`, `socios`, `endereco`, `telefone_1`, `cnaes`, ...) are a **payload
  contract** shared with the JS and with `integracoes_customizadas` and were **kept unchanged**.

### Deprecated Portuguese aliases

Kept so that unmigrated consumers keep working:

- `busca_cnpj.api.buscar_cnpj`, `busca_cnpj.api.buscar_cep` and `busca_cnpj.api.confirmar_dados_cnpj` (all still
  `@frappe.whitelist()`, delegating to the English functions);
- `busca_cnpj.api.formatar_cep`, `formatar_telefone`, `sanitizar_razao_social`;
- `busca_cnpj.cnpj.normalizar_cnpj`, `validar_cnpj`, `formatar_cnpj`, `validar_cpf`, `validar_tax_id`,
  `valor_caractere`;
- `busca_cnpj.setup.ajustar_layout_address`, `desativar_scripts_cnpj_legado`.

Every public name that existed on `main` before the rename keeps an alias; `tests/test_cnpj.py` fails if any of them
goes missing.

`integracoes_customizadas` (the only known consumer) already migrated to the English names on its own branch, so the
aliases can be **removed in a later release, after that branch is merged**. Before removing them, verify with a grep
in every consumer repository, for example:

```bash
grep -rnE "buscar_cnpj|confirmar_dados_cnpj|buscar_cep|formatar_cnpj|normalizar_cnpj|validar_cnpj|validar_cpf|validar_tax_id" \
  --include=*.py --include=*.js --include=*.json --include=*.md ../*/ --exclude-dir=busca_cnpj --exclude-dir=.git
```

An empty result (apart from this app) means the aliases are safe to delete. Also check Client Scripts, Server Scripts
and custom code stored on the sites, which a repository grep cannot see.

### Metadata and documentation

Publisher, license, copyright headers, `required_apps` and `pyproject.toml` author/license were updated; README,
CHANGELOG, ADR-001..003, `AGENTS.md` and `CLAUDE.md` were translated to English; `docs/dependencies.md` was added.
The ADR filenames were kept in Portuguese because other repositories link to them.

## Phase 2 (out of scope, found during this work)

- DocType `CNAE Fornecedor` is named in Portuguese and has no app prefix; it is referenced by the `cnaes` Custom
  Field (`options`) and by `confirm_cnpj_data`. Renaming it needs a patch and a coordinated change.
- Custom Fields outside the `custom_busca_cnpj_<meaning>` pattern: `cnae_section`, `cnaes` (Supplier),
  `custom_current_cep` (Employee) and `custom_bairro` (Address). Renaming persisted fieldnames needs data-migrating
  patches and updates to the JS and to consumers.
- `app_email` in `hooks.py` is still an old personal e-mail address. Replacing it is a maintainer decision and was
  not changed.
- Persisted Error Log titles and user-facing messages remain in Portuguese.

## Repository remote change

The repository was served from `miranda-ale/busca_cnpj` and the standard now names `still-pulse/busca_cnpj@main` in
`required_apps`/installation docs (the README `bench get-app` line already points to `still-pulse/busca_cnpj`). Until
the repository is transferred, `origin` remains `miranda-ale/busca_cnpj`, and consumers that still list
`miranda-ale/busca_cnpj@main` in their `required_apps` (for example `integracoes_customizadas` before its migration)
must be updated at the time of the transfer, or bench will resolve the wrong source.

## Consequences

- Cross-app review is easier; new code follows one language and naming rule.
- Temporary duplication: the aliases add a few lines to be removed later.
- Risk: the Bench test suite and a live site were **not** run; validation was ruff, `compileall`, `node --check` and
  the pure unit tests (`python -m unittest busca_cnpj.tests.test_cnpj`). The lookup flow against the real APIs and
  the Supplier form should be smoke-tested on a bench before release.
- Rollback: revert the PR; the aliases mean consumers were never forced to change at the same time.
