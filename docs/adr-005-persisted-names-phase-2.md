# ADR-005 — Phase 2: persisted names of `busca_cnpj`

Status: proposed (merge needs L5).

## Decision

| Type | Old | New |
|---|---|---|
| DocType (child table of `Supplier.cnaes`) | `CNAE Fornecedor` | `CNPJ Supplier CNAE` (folder and module path `cnpj_supplier_cnae`) |

Patch `busca_cnpj.patches.s01_rename_cnae_doctype` (`[pre_model_sync]`, idempotent) calls `frappe.rename_doc`, which renames
the table, the Custom Field options of `Supplier.cnaes` and the child rows' references.

## Not in this change

The Custom Fields `cnae_section`, `cnaes`, `custom_current_cep` and `custom_bairro` keep their fieldnames: they are
database columns shared with `rh_brasil` and `integracoes_customizadas` and belong to the Custom Field waves (b) and (f).
The deprecated Portuguese function aliases stay (decision: removal only in wave (h), after a consumer grep).

## Compatibility

No other repository of the set (nor `pulse_mobile`) references `CNAE Fornecedor` (grep). Server Scripts or Reports outside
the repositories that cite the old name must be fixed by hand.

## Verification (`dev.localhost`, all apps, synthetic seed)

- [x] L0 ruff check/format, compileall. [x] L2 `busca_cnpj` 19 tests OK.
- [x] L3 migrate from the seeded "before" state: old DocType and table gone, new ones present, 8 child rows preserved,
  `Supplier.cnaes` options updated, `parenttype` intact.
- [x] L4 second migrate no change (one `Patch Log` row); restore of the "before" backup returns the exact "before" state;
  migrate again gives the exact "after" state.
- [ ] L5 staging: **not executed**. Production runs `fa2845e`, so the Phase 1 patches are not part of this verification.
