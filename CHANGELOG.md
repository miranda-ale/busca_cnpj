# Changelog

Histórico reconstruído de `git tag` e `git log` do app (somente leitura) e conferido com os arquivos. A data é a do
commit marcado pela tag. Descreve só o que está commitado (`HEAD` = `v1.3.6`); alterações locais sem commit
(`hooks.py`, `public/js/taxid.js`) ficam de fora.

## Limites do histórico git

- **Início do histórico:** o HEAD tem **uma única raiz**, `77634c3` ("docs: reescreve README", 2026-10-13), marcada pela
  tag `v1.3.2`. Ela já traz o app inteiro (API, JS, DocType, testes, CI); o git do HEAD não mostra como as funções
  surgiram. O DocType `CNAE Fornecedor` tem `creation` de 2026-02-23 no JSON, anterior ao histórico: houve trabalho
  prévio fora dele.
- **Tags fora do histórico:** `v1.3.1` (commit `6462d12`, 2026-10-08, "chore(pyproject): declara frappe-dependencies e
  documenta dependencias") não é ancestral do HEAD (`git tag --no-merged HEAD`) e é uma segunda raiz. Entra abaixo só
  pelo assunto, como entrada de faixa, e não é parte do app.
- **Tipos de tag:** `v1.3.2` e `v1.3.3` são anotadas; `v1.3.1`, `v1.3.4`, `v1.3.5` e `v1.3.6` são leves. Não há tags
  `rc/*`.
- **Datas de tag:** `v1.3.3` a `v1.3.6` caem no mesmo dia (2026-10-28), em sequência de commits de CI e versão.
- **`__version__` x `app_version`:** `busca_cnpj/__init__.py` foi `1.2.2` nas tags `v1.3.1` e `v1.3.2` (a `v1.3.2` saiu
  com `__version__` desatualizado, o que a `v1.3.3` corrigiu) e acompanha a tag de `v1.3.3` em diante (`1.3.6` no
  HEAD). O `hooks.py` não define `app_version`.
- **Patches:** não há (`patches.txt` só com os cabeçalhos). Nada a observar sobre numeração.
- As mensagens de commit são curtas; o conteúdo de cada entrada foi conferido nos arquivos de cada commit
  (`git show --stat`).

## v1.3.6 — Fecha o ciclo do CI na main · 2026-10-28

- Commit `60a352d` ("chore: fecha o ciclo do CI na main"): só incrementa `__version__` para `1.3.6`. Fecha o ciclo das
  versões `v1.3.4` e `v1.3.5`, integradas por merge (`13d3dfe`).

## v1.3.5 — Ferramentas de checagem do Frappe · 2026-10-28

- Commit `dc589ab` ("ci: ferramentas de checagem do Frappe (commitlint, linter, CI)"), integrado pelo PR #1
  (`c1edd25`).
- Adiciona `commitlint.config.js` e o hook `commitlint` no `.pre-commit-config.yaml`; amplia
  `.github/workflows/linter.yml` (job de commits semânticos em PR). `__version__` passa a `1.3.5`.

## v1.3.4 — CI também na main · 2026-10-28

- Commit `8af3c26`: o workflow `ci.yml` passa a rodar em push também na branch `main` (antes só `develop`) e o grupo de
  concorrência é renomeado para `ci-busca_cnpj-…`. `__version__` passa a `1.3.4`.

## v1.3.3 — Alinha `__version__` com a tag v1.3.2 · 2026-10-28

- Commit `b74d0db`: `__version__` sai de `1.2.2` para `1.3.3` (a mensagem diz "alinha com a v1.3.2"; o valor gravado é
  `1.3.3`, o da própria tag).

## v1.3.2 — Reescrita do README (estado inicial registrado) · 2026-10-13

Raiz do histórico (`77634c3`, "docs: reescreve README"). Estado do código nesta tag, conferido nos arquivos, e não
mudanças feitas nela:

- **Fornecedor:** botão *Buscar* de CNPJ com janela de confirmação (`buscar_cnpj`, `confirmar_dados_cnpj`) que atualiza
  o fornecedor e cria Endereço, Contato (sócio, telefone, e-mail) e CNAEs; máscara e validação de CNPJ numérico e
  alfanumérico e de CPF, no formulário e no servidor (`doc_events` → `Supplier.validate`); higienização da razão
  social; tabela filha `CNAE Fornecedor`.
- **Fontes:** CNPJ.ws, com contingência para BrasilAPI e Minha Receita (timeout de 15 s); resposta do CNPJ.ws convertida
  ao formato da BrasilAPI.
- **CEP:** busca por ViaCEP em Endereço e Colaborador (`cep.js`, `address.js`, `employee.js`); Custom Fields `cnaes`,
  `custom_current_cep` e `custom_bairro`; ajuste de layout do Endereço.
- **Instalação/migração:** `after_install`/`after_migrate` criam os Custom Fields e desativam Client/Server Scripts de
  Fornecedor legados que validam CNPJ só com dígitos.
- **Testes:** `tests/test_cnpj.py` com 9 testes de CNPJ (sem testes de API).
- **Infraestrutura:** `.pre-commit-config.yaml`, `.eslintrc`, `.editorconfig`, workflows `ci.yml` e `linter.yml`.

## v1.3.1 (fora do histórico do HEAD) — pyproject · 2026-10-08

Entrada de faixa, descrita só pelo assunto do commit `6462d12`: "declara frappe-dependencies e documenta dependencias".
É uma **raiz separada** (sem pai) que já contém o app inteiro, fora do histórico do HEAD. Pela diferença entre as tags
(`git diff v1.3.1 v1.3.2`), `v1.3.2` muda só o `README.md` em relação a ela; logo a `v1.3.1` já tinha o mesmo código e
`pyproject.toml` (inferência a partir do diff).
