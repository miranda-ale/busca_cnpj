# ADR-003: Padronização de lint e CI

## Status

Aceita (2026-11-21).

## Contexto

Os 10 apps Frappe do ecossistema estão sendo preparados para unificação e para a migração v15 -> v16/v17. Os apps
divergiam em lint e CI (versão do Python, versão e regras do ruff, ignores, excludes do pre-commit, hooks de JS),
o que dificulta revisar e mover código entre eles. Esta ADR registra a configuração comum adotada e as decisões
tomadas ao aplicá-la no `busca_cnpj`.

## Decisão

1. Versão do Python: o mínimo atual **3.11 é mantido** (`target-version = "py311"`, `requires-python = ">=3.11"`,
   `linter.yml` em 3.11 até a decisão 13) por restrição de produção. Produção e homologação foram confirmadas em **Python 3.12**, e o
   `ci.yml` passou a rodar os testes em 3.12 para refletir a produção; o 3.14 usado antes é incompatível com o Frappe
   v15 (freezegun quebra na coleta: `AttributeError: module 'uuid' has no attribute '_load_system_functions'`). O alvo
   de migração ao Frappe v16 é `>=3.13` (`target-version = "py313"`, `requires-python = ">=3.13"`, `linter.yml` e
   `ci.yml` coerentes), a executar na própria migração.
2. ruff fixado em v0.16.10 via `ruff-pre-commit`, regras `F,E,W,I,UP,B,RUF` e lista de `ignore` idêntica à do CLM.
3. pyupgrade coberto pela regra `UP` do ruff, sem hook separado.
4. F401 **não** é ignorado: imports mortos são removidos; reexportações/efeito colateral são mantidos com
   `# noqa: F401  # <motivo>`. Strings visíveis ao usuário com caractere unicode ambíguo recebem
   `# noqa: RUF001` em vez de alterar o texto.
5. prettier 2.7.1 e eslint 8.44.0 mantidos (atualização adiada, para não misturar com a padronização; revisar na
   preparação para v16/v17).
6. Os `exclude` do pre-commit são sempre caminhos do próprio repositório; entradas mortas foram removidas, sem
   ampliar o escopo ignorado.
7. Globais de ESLint são declaradas no `.eslintrc` com escopo mínimo. Neste repositório: apenas `busca_cnpj`
   (`"writable"`), namespace do próprio app criado por `frappe.provide`. Nenhum `overrides` necessário.
8. Arquivos JS com Jinja são excluídos de prettier/eslint por caminho exato. Neste repositório: nenhum.
9. JS formatado pelo prettier em commit exclusivo de estilo. Neste repositório: 3 arquivos
   (`cep.js`, `supplier.js`, `taxid.js`).
10. O pip-audit roda só no CI e audita apenas o `pyproject` (as dependências erpnext/hrms ficam comentadas), então
    cobre pouco: pendência.
11. commitlint mantido e `pre-commit install` documentado no `AGENTS.md`.
12. Sem tag nem mudança de `__version__` nesta padronização.
13. Python no CI: `linter.yml` e `ci.yml` (quando existe) rodam em **3.12**, igual à produção/homologação; o piso 3.11 continua em `requires-python` e `target-version`. Nunca 3.14 (o Frappe v15 não o suporta).
14. Actions alinhadas em todos os workflows: `actions/checkout@v7`, `actions/setup-python@v7`, `actions/setup-node@v7`, `actions/cache@v6`. O `pre-commit/action` foi substituído por três passos (`pip install pre-commit`, `actions/cache@v6` de `~/.cache/pre-commit`, `pre-commit run --all-files`). Os workflows de CI/testes ganharam `workflow_dispatch` para validar sem PR, e o job `linter` roda também fora de PR.
15. pip-audit informativo: o job obrigatório `deps-vulnerable-check` permanece e audita este app. Foi adicionado o job separado `deps-vulnerable-check-stack` com `continue-on-error: true`, que clona o Frappe e o ERPNext `version-15` do GitHub e roda `pip-audit` sobre essas cópias (os requisitos declarados por elas). Não audita este app nem as versões efetivamente instaladas no ambiente; achados aparecem no log, mas não deixam o gate vermelho.
16. Dependências explícitas: imports reais auditados. `requests` vem do Frappe e `erpnext` está em `required_apps` (hooks) e em `[tool.bench.frappe-dependencies]`; o código não importa nenhum outro pacote externo. Nenhuma declaração faltava. Dependências fracas com guarda ficam documentadas, nunca em `required_apps`.
17. Semgrep em varredura completa: o passo roda `semgrep scan --error --metrics=off` com as regras do `frappe/semgrep-rules` e `r/python.lang.correctness` sobre todo o repositório (PR, push na `main` e `workflow_dispatch`), igual nos demais apps. Não usa `semgrep ci`, que em PR analisa só o diff; qualquer achado reprova o job.

## Consequências

- Lint e formatação idênticos entre os apps, facilitando a unificação e a revisão cruzada.
- Imports mortos aparecem como erro (F401) e precisam de remoção ou `noqa` justificado.
- Versões de prettier/eslint ficam defasadas até a preparação para o v16/v17.
- O ESLint passa a validar de fato o JS; o namespace `busca_cnpj` é aceito como global, mas erros de digitação
  nele deixam de ser detectados.

## Estado deste repositório

| Item | Estado |
| --- | --- |
| F401 | 1 import removido (`import frappe` em `cnae_fornecedor.py`, commit `fix: corrigir erros do ruff check`); 0 mantidos com `noqa`; `F401` removido do ignore no `pyproject.toml` |
| Excludes alterados | Removidas entradas mortas de prettier e eslint (`public/dist`, `templates/includes`, `public/js/lib`, `cypress`); mantidos `node_modules` e `boilerplate` |
| ESLint | `no-undef` de `busca_cnpj` (25 ocorrências em 5 arquivos) resolvido com a global; nenhum bug real encontrado |
| Prettier | 3 arquivos JS reformatados (apenas estilo) |
| pre-commit (`SKIP=commitlint pre-commit run --all-files`) | Todos os hooks passam |

## Pendências

- Migrar para `>=3.13` junto com o v16; revisar também as versões de prettier/eslint na preparação para o v16/v17.
- Ampliar o pip-audit para cobrir as dependências erpnext/hrms (hoje comentadas). Parcialmente atendida pelo job informativo `deps-vulnerable-check-stack`; falta tornar o gate obrigatório após triar os achados.
- Avaliar migrar o `.eslintrc` para a configuração flat quando o eslint for atualizado.
