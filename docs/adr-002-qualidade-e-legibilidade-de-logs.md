# ADR-002: Quality and readability of external-integration logs

## Context

`integracoes_customizadas` identified and fixed a recurring problem in integrations with external services: the
integration with the DataJud public API (CNJ, the Brazilian National Council of Justice) started failing with
HTTP 403 on every court, but the Error Log only recorded `"Processo X, tribunal Y: DataJudError. Dados anteriores
preservados."` — with no endpoint, method, HTTP status, response body or traceback. Diagnosing the root cause
required reading the source code, not the log. At the same time, each failing case became its own record on every
run — with 56 failing cases, that meant 56 entries per round, flooding the Error Log. The fix (the `DataJud Sync Log`
DocType, with structured context, grouping by run/error type and a masked API key) and the general principle are
documented in
[`integracoes_customizadas/docs/adr-002-qualidade-e-legibilidade-de-logs.md`](https://github.com/still-pulse/integracoes_customizadas)
and in
[`integracoes_customizadas/docs/datajud-qualidade-de-logs.md`](https://github.com/still-pulse/integracoes_customizadas)
(the concrete fix applied to DataJud).

`busca_cnpj` is especially exposed to this same kind of problem: **the whole app is an integration with external
services**. `busca_cnpj.api._query_api` queries three public Federal Revenue Service (Receita Federal) data sources
with fallback (CNPJ.ws, BrasilAPI, Minha Receita) and `busca_cnpj.api.lookup_cep` queries ViaCEP — both through a
direct `requests.get`, with no queue, no cache and no log DocType of their own (see
[Privacy and query limits](../README.md#privacy-and-query-limits) in the README).

Today, inspecting the actual code (`busca_cnpj/api.py`):

- In `_query_api`, a connection failure (`requests.exceptions.RequestException`) on any of the three sources is
  silently ignored (`continue`) — **no call to `frappe.log_error` records which source failed, with which URL, HTTP
  status or exception**. The user only gets a `frappe.throw` with a generic message ("Não foi possível conectar",
  "Erro ao consultar CNPJ (código N)"); if all three sources change contract or start answering 403/429, there is no
  Error Log record to diagnose remotely — exactly the symptom that motivated the DataJud ADR, only worse here: not
  even the poor log exists, because there is no log at all.
- In `lookup_cep`, the same pattern: a connection failure or an HTTP status other than 200 becomes only a
  `frappe.throw`, with no `frappe.log_error`.
- The only `frappe.log_error` calls in the app are in `confirm_cnpj_data` (duplicate Supplier rename, failure to
  create Address, failure to create Contact) and **already partially follow the pattern**: descriptive title,
  Supplier name and, in the last two, the full `frappe.get_traceback()`. They still lack, however, the context of the
  HTTP call that originated the failure (when applicable) and any error classification.
- No secret is involved in these four APIs (CNPJ.ws, BrasilAPI, Minha Receita and ViaCEP are public, with no key),
  unlike DataJud — but the principle of never writing a secret in clear text applies to any future integration of
  this app that starts requiring authentication.

## Decision

The general principle of `integracoes_customizadas` (ADR-002 of that app) applies to `busca_cnpj`: every integration
with an external service (third-party API, webhook, queue) in this app must log enough context to diagnose without
rereading the source code, and without flooding the Error Log:

1. **Structured context, not only the exception message or the `frappe.throw` shown to the user**: the endpoint/URL
   queried, HTTP method, HTTP status, the first ~1,000 characters of the response body, the exception type and the
   traceback. A `frappe.throw` with a friendly user message does not replace a `frappe.log_error` with this technical
   context — they serve different purposes.
2. **Never write a secret in clear text**: none of the current integrations (CNPJ.ws, BrasilAPI, Minha Receita,
   ViaCEP) uses an API key today, so this rule has no practical effect here yet — but it applies from now on to any
   future integration of this app that starts requiring a key, token or authentication header: never in clear text in
   the log, only a masked prefix when it is useful to confirm which credential was used.
3. **Classify the error**, not just repeat the raw exception: at least connection failure/timeout, client 4xx status
   (invalid or not-found CNPJ/CEP) and provider 5xx status/unavailability are categories distinct enough to decide
   the action (nothing to do vs. provider down vs. wrong user data).
4. **Group repeated failures of the same run by error type**, with a count, instead of one record per processed
   item — relevant above all for whoever calls `lookup_cnpj` in bulk (e.g. the Bionexo import of
   `integracoes_customizadas`, cited in [Use by other apps](../README.md#use-by-other-apps)): a systemic failure on
   the three CNPJ sources should generate a few clear log records, not one per CNPJ in the list.

This does not require recreating the `DataJud Sync Log` design here: the call volume of this app is per user click
(not per scheduled run with dozens of items), so the Frappe Error Log, used today, remains sufficient — as long as
each failure in `_query_api` and `lookup_cep` starts recording item 1 above, which today **does not happen** (a
finding, not fixed in this document — out of scope for this change, which is documentation only). A dedicated log
DocType would only be justified if this app started running in bulk with a relevant failure volume per run (see
item 4).

## Consequences

- This document does not change any code: `_query_api` and `lookup_cep` remain without `frappe.log_error` on
  connection/HTTP failures until another change, with its own scope, implements item 1 above.
- PR review: a new or changed external integration in this app that only writes `frappe.log_error(str(exc))` (or not
  even that, as today in `_query_api`/`lookup_cep`) without HTTP status/body/classification is not complete.
- When touching `_query_api`, `lookup_cep` or any new external integration of this app for another reason, take the
  opportunity to align its log with this pattern.
