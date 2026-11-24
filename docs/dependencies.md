# Dependencies

## Strong dependencies (declared)

| Dependency | Where declared | Why |
| --- | --- | --- |
| `frappe/frappe@version-15` | `required_apps` in `hooks.py`; `[tool.bench.frappe-dependencies]` in `pyproject.toml` | Framework (`frappe.whitelist`, Custom Fields, Property Setters, `requests` is shipped with it). |
| `frappe/erpnext@version-15` | `required_apps` in `hooks.py`; `[tool.bench.frappe-dependencies]` in `pyproject.toml` | Fills the ERPNext `Supplier`, `Address` and `Employee` DocTypes (`Employee` is part of ERPNext in v15; HRMS is not required). |

## Weak dependencies (optional, guarded)

None. `busca_cnpj` imports nothing from other custom apps.

## Consumers

`integracoes_customizadas` declares `busca_cnpj` in `required_apps` and uses it. The inverse direction (this app
depending on its consumers) must never exist.

| Consumer use | Consumer location | What it calls |
| --- | --- | --- |
| Supplier creation in the Bionexo import | `integracoes_customizadas/bionexo/importacao.py` | `busca_cnpj.api.buscar_cnpj` and `confirmar_dados_cnpj` (guarded by `frappe.get_installed_apps()`) |
| CPF/CNPJ validation in the legal case DocType | `juridico/doctype/processo_judicial/processo_judicial.py` | `busca_cnpj.cnpj.formatar_cnpj`, `normalizar_cnpj`, `validar_tax_id` |
| CPF validation of the case parties | `juridico/parte.py` | `busca_cnpj.cnpj.validar_cpf` |
| CPF/CNPJ input mask in the form | `processo_judicial.js` | `busca_cnpj.taxid.bind_input` (guarded by `window.busca_cnpj?.taxid`) |

### Deprecated Portuguese aliases

Phase 1 of the naming standardization renamed the public functions to English. The old names remain as aliases so
that the consumers above keep working until they migrate:

| Deprecated alias | English name |
| --- | --- |
| `busca_cnpj.api.buscar_cnpj` (whitelisted) | `busca_cnpj.api.lookup_cnpj` |
| `busca_cnpj.api.confirmar_dados_cnpj` (whitelisted) | `busca_cnpj.api.confirm_cnpj_data` |
| `busca_cnpj.cnpj.normalizar_cnpj` | `normalize_cnpj` |
| `busca_cnpj.cnpj.validar_cnpj` | `validate_cnpj` |
| `busca_cnpj.cnpj.formatar_cnpj` | `format_cnpj` |
| `busca_cnpj.cnpj.validar_cpf` | `validate_cpf` |
| `busca_cnpj.cnpj.validar_tax_id` | `validate_tax_id` |

`integracoes_customizadas` has already migrated to the English names on its own branch; remove the aliases in a later
release, after that branch is merged and verified with a grep (see ADR-004). Remove the aliases only after `integracoes_customizadas` imports the English names. The keys of the dictionaries
returned by `lookup_cnpj` (`razao_social`, `cnpj_formatado`, `socios`, `endereco`, ...) are a payload contract shared
with that app and are unchanged.
