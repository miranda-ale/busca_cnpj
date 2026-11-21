# ADR-001: Guaranteed minimum read access on Link-connected DocTypes

## Context

`CLM` identified and fixed a recurring problem in Frappe apps: when a DocType in one app references, through a Link
field, a DocType from another module/app (e.g. ERPNext, HR), the basic/daily-use role usually has no permission of
its own on the referenced DocType. It implicitly depends on a role from another module already granting read access,
which does not always happen. The user gets blocked in the middle of the flow (empty Link, permission error when
opening or selecting the referenced record), with no hint that the cause lives in another module rather than in the
app the user was working with. See the full precedent in
[`clm/docs/adr-006-leitura-minima-em-doctypes-vinculados.md`](https://github.com/still-pulse/clm) (`CLM` ADR-006,
which fixed the concrete case with `Custom DocPerm` fixtures for `CLM Administrator`, `CLM Manager` and `CLM User`).

`busca_cnpj` differs from the CLM case in one respect: **this app defines no roles of its own** (there is no
`fixtures/role.json`). It fills three standard DocTypes from other modules — `Supplier`, `Address` and `Employee` —
from public CNPJ and CEP lookups, but the consuming app always decides which user role has access to these
buttons/APIs. Today the only declared consumer (`required_apps`) is `integracoes_customizadas`, which uses
`busca_cnpj.api.lookup_cnpj`, `confirm_cnpj_data` (the deprecated aliases `buscar_cnpj` and `confirmar_dados_cnpj`
are still exposed) and the functions in `busca_cnpj.cnpj`/`busca_cnpj.taxid` (see
[Use by other apps](../README.md#use-by-other-apps) in the README and [dependencies.md](dependencies.md)). If the
role that `integracoes_customizadas` exposes to these functions has no guaranteed read access on `Supplier`,
`Address` and `Employee`, the same kind of blocking as in CLM happens here: the user triggers the CNPJ/CEP lookup but
fails to open or link the very record that was just filled.

## Decision

The general CLM principle applies to `busca_cnpj`, but indirectly, because there is no role of its own here to
receive the fixture:

- **`busca_cnpj` itself neither defines nor needs roles or `Custom DocPerm` fixtures.** It only fills fields on
  DocTypes that already exist, with permissions that belong to another module (ERPNext, HR).
- Any app that exposes an API, button or flow of `busca_cnpj` (`lookup_cnpj`, `lookup_cep`, `confirm_cnpj_data`,
  `busca_cnpj.cnpj`, `busca_cnpj.taxid`) to a user role is responsible for ensuring that this role has at least read
  permission (`read`/`select`) on `Supplier`, `Address` and `Employee` — the three DocTypes that `busca_cnpj` fills.
  Without it, the user is blocked in the middle of the flow exactly as in the CLM case, only with the cause one level
  below (in `busca_cnpj`, filling a record that the consuming app's role cannot read back).
- This responsibility is already being handled separately, in the documentation of `integracoes_customizadas`
  itself (another agent handles it in parallel, in that app's repository). This ADR documents the principle on the
  `busca_cnpj` side, so that any new consumer that comes to depend on this app knows from the start that it must
  guarantee this minimum read access for the role it uses.
- If `busca_cnpj` ever starts filling a new linked DocType (besides Supplier/Address/Employee), this section must be
  updated in the same commit that introduces that behavior.

## Consequences

- `busca_cnpj` remains without permission fixtures and without roles of its own: nothing changes in the app's code or
  behavior because of this document.
- The minimum-read check falls on the consuming app (today, `integracoes_customizadas`), not on this repository. PR
  review here should only flag, when a new DocType filled by `busca_cnpj` is added, that the consuming apps will need
  to review the permissions of the role they use.
- This document does not create, remove or change any permission, fixture or DocType — it only records the
  principle, following the CLM precedent.
