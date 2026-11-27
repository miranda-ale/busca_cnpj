# Busca CNPJ (`busca_cnpj`)

Brazilian CNPJ (company tax ID) and CEP (postal code) lookup integrated with ERPNext records. It fills the
**Supplier** (`Supplier`) from public Federal Revenue Service (Receita Federal) data sources and speeds up addresses
in **Address** (`Address`) and **Employee** (`Employee`). Current version: **2.0.0** (see
[CHANGELOG.md](CHANGELOG.md)).

It accepts the traditional numeric CNPJ and the Receita Federal **alphanumeric CNPJ** (from July 2026).

It is also used by another app on the bench: `integracoes_customizadas` depends on it (see
[Use by other apps](#use-by-other-apps) and [docs/dependencies.md](docs/dependencies.md)).

## Features

### Supplier (`Supplier`)

- **CNPJ lookup button** next to *Tax ID*: queries the given CNPJ and opens a confirmation dialog with legal name,
  trade name, registration status (with a warning if it is not ATIVA), legal nature, address, phone, e-mail, CNAEs
  (Brazilian economic activity codes) and partners (QSA). On confirmation (`confirm_cnpj_data`):
  - for a new Supplier, the form is saved first, with CNPJ, legal name and type *Company*;
  - it updates the CNPJ (`tax_id`), the supplier type and the CNAE table;
  - if the supplier name is set by *Supplier Name* (`supp_master_name`), it renames the document to the legal name;
    if a supplier with that name already exists, it keeps the original and logs to the Error Log;
  - it creates or updates the **Address** (type *Office*, primary) and the **Contact** (first QSA partner as name and
    qualification as designation, phone and e-mail), both linked to the supplier, and sets them as primary. A failure
    in one of them does not undo the rest: it goes to the Error Log and the user receives a warning.
- **Sources with fallback**: tries [CNPJ.ws](https://publica.cnpj.ws) first; if that source does not answer
  successfully, tries [BrasilAPI](https://brasilapi.com.br) and, last, [Minha Receita](https://minhareceita.org). The
  CNPJ.ws response is converted to the BrasilAPI format (`_normalize_cnpjws`), which is the format used by
  `lookup_cnpj`.
- **Supplier CNAEs**: child table `CNPJ Supplier CNAE` (code, description and primary-CNAE flag) in a collapsible
  section right below the CNPJ/CPF.
- **Mask and validation**: formats the CNPJ while typing and validates the check digits (numeric and alphanumeric)
  or the CPF, in the form (`supplier.js`) and on the server (`doc_events` → `Supplier.validate`). An empty `tax_id`
  is accepted.
- **Legal-name sanitization**: converts to uppercase, strips accents and drops special characters (keeps letters,
  digits, space and `& - . /`) when editing the supplier name and in the data returned by the lookup.

### Address (`Address`) and Employee (`Employee`)

- **CEP lookup** ([ViaCEP](https://viacep.com.br)): button and Enter key on the CEP field fill street, neighborhood,
  city and state. Generic CEPs (without a street) do not overwrite what was already typed.
- `Address` gains the **Bairro** (neighborhood) field (`custom_bairro`), the **CEP** label and an adjusted layout
  (CEP right below the address type).
- `Employee` gains the **CEP (Endereço Atual)** field (`custom_current_cep`); the lookup fills the *Current Address*
  (`current_address`) after confirmation, if another address is already present.

### Installation and migration

- `after_install` and `after_migrate` (same idempotent routine) create the Custom Fields (`cnae_section` and `cnaes`
  on Supplier, `custom_current_cep` on Employee, `custom_bairro` on Address) and adjust the Address layout (Property
  Setters).
- They disable, on the site, Supplier Client Scripts and Server Scripts that still validate CNPJ with digits only
  (identified by known text snippets). They only disable, never delete, and log to the `busca_cnpj` logger.

## Privacy and query limits

- Queries leave from the Frappe **server**, not from the user's browser. The 14-character CNPJ (unmasked) goes in the
  CNPJ.ws URL and, only if that fails, in BrasilAPI and Minha Receita. The CEP (8 digits) goes in the ViaCEP URL. No
  other ERPNext data is sent. CNPJs are public, but the history of which CNPJs/CEPs the company queries is visible
  to those providers.
- 15-second timeout per request. A 400/404 error on all sources becomes "CNPJ não encontrado"; a connection failure
  on all becomes "Não foi possível conectar"; any other HTTP code is reported in the message.
- **There is no cache, queue or rate control**: each click on *Buscar* triggers a call to the APIs, and the usage
  limits of the public providers (defined by them, subject to change) apply to the server's IP. The same holds for
  whoever calls `lookup_cnpj` in bulk (for example the Bionexo import).
- The methods `busca_cnpj.api.lookup_cnpj`, `lookup_cep` and `confirm_cnpj_data` (and the deprecated aliases
  `buscar_cnpj` and `confirmar_dados_cnpj`) are `@frappe.whitelist()` (they require a logged-in user).
  `confirm_cnpj_data` (and its alias) accepts POST only and writes with `ignore_permissions=True`: whoever can call it from the Desk does not go through
  the Supplier permission check.

## Use by other apps

`integracoes_customizadas` declares `busca_cnpj` in `required_apps` and uses it (checked in
`apps/integracoes_customizadas/`):

| Use | Where | What it calls |
| --- | --- | --- |
| Supplier registration in the Bionexo import | `integracoes_customizadas/bionexo/importacao.py` | `busca_cnpj.api.buscar_cnpj` and `confirmar_dados_cnpj` (only if `busca_cnpj` is installed; if the lookup fails, it registers with the name and CNPJ from the report) |
| CPF/CNPJ validation of the legal case (Processo Judicial) | `juridico/doctype/processo_judicial/processo_judicial.py` | `busca_cnpj.cnpj.formatar_cnpj`, `normalizar_cnpj`, `validar_tax_id` |
| CPF validation of the parties | `juridico/parte.py` | `busca_cnpj.cnpj.validar_cpf` |
| CPF/CNPJ mask in the form | `processo_judicial.js` | `busca_cnpj.taxid.bind_input` (guarded by `window.busca_cnpj?.taxid`) |

Those consumers still use the **deprecated Portuguese aliases** of the functions, which this app keeps until they
migrate to the English names (`lookup_cnpj`, `lookup_cep`, `confirm_cnpj_data`, `format_cnpj`, `normalize_cnpj`,
`validate_tax_id`, `validate_cpf`); see [docs/dependencies.md](docs/dependencies.md). Changes to the signatures and return values of
`busca_cnpj.cnpj` and `busca_cnpj.api` affect that app. The `busca_cnpj.taxid` helper is loaded globally by this app
(`taxid.js`), but today only `integracoes_customizadas` uses it; no form of `busca_cnpj` itself calls it.

`busca_cnpj` defines no roles of its own: whoever exposes these APIs to a user role is responsible for ensuring that
the role has minimum read access to `Supplier`, `Address` and `Employee`, so the user is not blocked in the middle of
the flow — see [docs/adr-001-leitura-minima-em-doctypes-vinculados.md](docs/adr-001-leitura-minima-em-doctypes-vinculados.md).

CNPJ and CEP lookups are integrations with an external service and must log failures with enough context to
diagnose without rereading the code — see
[docs/adr-002-qualidade-e-legibilidade-de-logs.md](docs/adr-002-qualidade-e-legibilidade-de-logs.md).

## Requirements

- Frappe v15 and ERPNext v15 (`required_apps` in `hooks.py` and `[tool.bench.frappe-dependencies]` in
  `pyproject.toml`); the `Employee` used in `employee.js` belongs to ERPNext and does not require HRMS.
- Python >= 3.11 (`requires-python`).
- Outbound internet access to CNPJ.ws, BrasilAPI, Minha Receita and ViaCEP.
- `requests` ships with Frappe: `pyproject.toml` does not declare it and the code imports no other external package.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app erpnext --branch version-15
bench get-app still-pulse/busca_cnpj --branch main
bench --site <site> install-app erpnext busca_cnpj
bench --site <site> migrate
```

## Configuration and usage

There is no configuration: install it and it works. The Supplier form gains the button and the mask.

1. Open or create a **Supplier** and enter the CNPJ in *Tax ID*.
2. Click *Buscar*, review the returned data and confirm.
3. On **Address** or **Employee**, enter the CEP and use *Buscar* (or Enter) to complete the address.

User-facing messages and labels are written in Portuguese in the code (the source strings of `__()`/`_()`); the app
**has no translation file** (no `.po`/`.csv`), so there is no unused translation.

## Development

```text
busca_cnpj/
├── api.py                # public methods (lookup_cnpj, lookup_cep, confirm_cnpj_data), API queries and normalization
├── cnpj.py               # normalization, check digits (numeric and alphanumeric), formatting, CPF and validate_tax_id
├── supplier_validate.py  # server-side Supplier validation (doc_events)
├── setup.py              # Custom Fields, Address layout and disabling of legacy scripts
├── hooks.py · modules.txt · patches.txt (no patches)
├── public/js/            # cep.js · taxid.js (global) · supplier.js · address.js · employee.js
├── tests/test_cnpj.py
└── busca_cnpj/doctype/cnpj_supplier_cnae/   # child table of CNAEs
```

There is no workspace, report, print format, fixture or patch; the only DocType is `CNPJ Supplier CNAE` (child table).

JavaScript loading (`hooks.py`): `cep.js` and `taxid.js` are included on every Desk page (`app_include_js`).
`cep.js` exposes `busca_cnpj.cep` (`strip`, `mask`, `bind_input`, `add_button`, `lookup`); `taxid.js` exposes
`busca_cnpj.taxid` (`strip`, `mask`, `bind_input`: progressive mask for CPF up to 11 digits and for CNPJ, including
alphanumeric, above that or with letters; limits the field to 18 characters); `supplier.js`, `address.js` and
`employee.js` are included through `doctype_js` on Supplier, Address and Employee. `supplier.js` has its own copies of
the CNPJ functions (`strip_cnpj`, `format_cnpj`, `validate_cnpj`), duplicating `cnpj.py`.

### Naming

Identifiers, comments and documentation are in English; user-facing labels and messages stay in pt-BR. See
[AGENTS.md](AGENTS.md) (Language and naming).

### Tests

There is **one** test file, [busca_cnpj/tests/test_cnpj.py](busca_cnpj/tests/test_cnpj.py), with **10 pure `unittest`
tests** (no database): normalization, ASCII-48 value, official alphanumeric CNPJ, numeric CNPJ, invalid check digit,
length, formatting, `validate_tax_id` and the deprecated aliases.

```bash
bench --site <site> run-tests --app busca_cnpj
bench --site <site> run-tests --module busca_cnpj.tests.test_cnpj
```

**Not covered**: `lookup_cnpj`, `_query_api` and the fallback between sources, `_normalize_cnpjws`, `lookup_cep`,
`confirm_cnpj_data` (rename, Address, Contact, CNAEs; only the POST restriction, the savepoint rollback and the absence of a manual commit are tested), `sanitize_company_name`, phone and CEP formatters,
`validate_cpf`, `supplier_validate`, `setup.py` (Custom Fields and disabling of legacy scripts) and all of the
JavaScript. There are no HTTP mocks.

### Lint

The app uses `pre-commit` (ruff, eslint, prettier; commitlint on PRs):

```bash
cd apps/busca_cnpj
pre-commit install
```

Lint decisions: [docs/adr-003-padronizacao-de-lint-e-ci.md](docs/adr-003-padronizacao-de-lint-e-ci.md).

## Documentation

- [CHANGELOG.md](CHANGELOG.md): history by version and git limits.
- [docs/dependencies.md](docs/dependencies.md): strong and weak dependencies, consumers and deprecated aliases.
- [docs/adr-001-leitura-minima-em-doctypes-vinculados.md](docs/adr-001-leitura-minima-em-doctypes-vinculados.md):
  principle of guaranteed minimum read access on Link-connected DocTypes, applied to the consuming apps of this app.
- [docs/adr-002-qualidade-e-legibilidade-de-logs.md](docs/adr-002-qualidade-e-legibilidade-de-logs.md): quality of
  external-integration logs.
- [docs/adr-003-padronizacao-de-lint-e-ci.md](docs/adr-003-padronizacao-de-lint-e-ci.md): lint and CI standardization.
- [docs/adr-004-language-and-naming-standardization.md](docs/adr-004-language-and-naming-standardization.md): language and naming standardization (phase 1), deprecated aliases and phase 2 items.

## License

Proprietary (`app_license = "Proprietary"` in `hooks.py`). See [license.txt](license.txt). Copyright (c) 2026
StillPulse Tecnologia LTDA.
