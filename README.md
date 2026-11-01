# Busca CNPJ (`busca_cnpj`)

Consulta de CNPJ e CEP brasileiros integrada aos cadastros do ERPNext. Preenche o **Fornecedor** (`Supplier`) a
partir de bases públicas da Receita Federal e agiliza endereços em **Endereço** (`Address`) e **Colaborador**
(`Employee`). Versão atual: **1.3.6** (ver [CHANGELOG.md](CHANGELOG.md)).

Aceita o CNPJ numérico tradicional e o **CNPJ alfanumérico** da Receita Federal (a partir de julho/2026).

Também é usado por outro app do bench: o `integracoes_customizadas` depende dele (ver
[Uso por outros apps](#uso-por-outros-apps)).

## Funcionalidades

### Fornecedor (`Supplier`)

- **Botão de busca de CNPJ** ao lado de *Tax ID*: consulta o CNPJ informado e abre uma janela de confirmação com razão
  social, nome fantasia, situação cadastral (com alerta se não for ATIVA), natureza jurídica, endereço, telefone,
  e-mail, CNAEs e quadro societário (QSA). Ao confirmar (`confirmar_dados_cnpj`):
  - em Fornecedor novo, o formulário é salvo primeiro, com CNPJ, razão social e tipo *Company*;
  - atualiza o CNPJ (`tax_id`), o tipo de fornecedor e a tabela de CNAEs;
  - se o nome do fornecedor é definido pelo *Supplier Name* (`supp_master_name`), renomeia o documento para a razão
    social; se já existir fornecedor com esse nome, mantém o original e registra no Error Log;
  - cria ou atualiza o **Endereço** (tipo *Office*, primário) e o **Contato** (primeiro sócio do QSA como nome e
    qualificação como cargo, telefone e e-mail), ambos vinculados ao fornecedor, e os define como principais. Falha
    em um deles não desfaz o restante: vai para o Error Log e o usuário recebe aviso.
- **Fontes com contingência**: tenta [CNPJ.ws](https://publica.cnpj.ws) primeiro; se a fonte não responder com
  sucesso, tenta [BrasilAPI](https://brasilapi.com.br) e, por fim, [Minha Receita](https://minhareceita.org). A
  resposta do CNPJ.ws é convertida para o formato da BrasilAPI (`_normalizar_cnpjws`), que é o formato usado em
  `buscar_cnpj`.
- **CNAEs do fornecedor**: tabela filha `CNAE Fornecedor` (código, descrição e indicador de CNAE principal) em seção
  recolhível logo abaixo do CNPJ/CPF.
- **Máscara e validação**: formata o CNPJ durante a digitação e valida os dígitos verificadores (numérico e
  alfanumérico) ou o CPF, no formulário (`supplier.js`) e no servidor (`doc_events` → `Supplier.validate`). O
  campo `tax_id` vazio é aceito.
- **Higienização da razão social**: converte para maiúsculas, remove acentos e descarta caracteres especiais (mantém
  letras, números, espaço e `& - . /`) ao editar o nome do fornecedor e nos dados devolvidos pela consulta.

### Endereço (`Address`) e Colaborador (`Employee`)

- **Busca de CEP** ([ViaCEP](https://viacep.com.br)): botão e tecla Enter no campo CEP preenchem logradouro, bairro,
  cidade e UF. CEPs genéricos (sem logradouro) não apagam o que já foi digitado.
- `Address` ganha o campo **Bairro** (`custom_bairro`), o rótulo **CEP** e o layout ajustado (CEP logo abaixo do tipo
  de endereço).
- `Employee` ganha o campo **CEP (Endereço Atual)** (`custom_current_cep`); a busca preenche o *Endereço Atual*
  (`current_address`) depois de confirmação, se já houver outro endereço.

### Instalação e migração

- `after_install` e `after_migrate` (mesma rotina, idempotente) criam os Custom Fields (`cnae_section` e `cnaes` em
  Supplier, `custom_current_cep` em Employee, `custom_bairro` em Address) e ajustam o layout de Address
  (Property Setters).
- Desativam, no site, Client Scripts e Server Scripts de Fornecedor que ainda validam CNPJ apenas com dígitos
  (identificados por trechos de texto conhecidos). Só desativam, não apagam, e registram no log `busca_cnpj`.

## Privacidade e limites das consultas

- As consultas saem do **servidor** do Frappe, não do navegador do usuário. O CNPJ de 14 caracteres (sem máscara)
  vai na URL de CNPJ.ws e, só se a anterior falhar, de BrasilAPI e Minha Receita. O CEP (8 dígitos) vai na URL do
  ViaCEP. Nenhum outro dado do ERPNext é enviado. Os CNPJs são públicos, mas o histórico de quais CNPJs/CEPs a empresa
  consulta fica visível para esses provedores.
- Timeout de 15 segundos por requisição. Erro 400/404 em todas as fontes vira "CNPJ não encontrado"; falha de conexão em
  todas vira "Não foi possível conectar"; outro código HTTP é informado na mensagem.
- **Não há cache, fila nem controle de taxa**: cada clique em *Buscar* gera uma chamada às APIs, e os limites de uso
  dos provedores públicos (definidos por eles, sujeitos a mudança) valem para o IP do servidor. O mesmo vale para
  quem chama `buscar_cnpj` em lote (por exemplo a importação Bionexo).
- Os métodos `busca_cnpj.api.buscar_cnpj`, `buscar_cep` e `confirmar_dados_cnpj` são `@frappe.whitelist()` (exigem
  usuário logado). `confirmar_dados_cnpj` grava com `ignore_permissions=True`: quem pode chamá-lo pelo Desk não
  passa pela checagem de permissão de Fornecedor.

## Uso por outros apps

`integracoes_customizadas` declara `busca_cnpj` em `required_apps` e usa (conferido em
`apps/integracoes_customizadas/`):

| Uso | Onde | O que chama |
| --- | --- | --- |
| Cadastro de fornecedores da importação Bionexo | `integracoes_customizadas/bionexo/importacao.py` | `busca_cnpj.api.buscar_cnpj` e `confirmar_dados_cnpj` (só se `busca_cnpj` estiver instalado; se a consulta falhar, cadastra com nome e CNPJ do relatório) |
| Validação de CPF/CNPJ do Processo Judicial | `juridico/doctype/processo_judicial/processo_judicial.py` | `busca_cnpj.cnpj.formatar_cnpj`, `normalizar_cnpj`, `validar_tax_id` |
| Validação de CPF das partes | `juridico/parte.py` | `busca_cnpj.cnpj.validar_cpf` |
| Máscara de CPF/CNPJ no formulário | `processo_judicial.js` | `busca_cnpj.taxid.bind_input` (com guarda `window.busca_cnpj?.taxid`) |

Mudanças nas assinaturas e no retorno de `busca_cnpj.cnpj` e `busca_cnpj.api` afetam esse app. O helper
`busca_cnpj.taxid` ainda não está no commit atual do `busca_cnpj` (ver [Estado do disco](#estado-do-disco-fora-do-commit)).

## Requisitos

- Frappe v15 e ERPNext v15 (`required_apps = ["erpnext"]` e `[tool.bench.frappe-dependencies]` no `pyproject.toml`);
  o `Employee` usado em `employee.js` é do ERPNext, não exige HRMS.
- Python >= 3.11 (`requires-python`).
- Acesso de saída à internet para CNPJ.ws, BrasilAPI, Minha Receita e ViaCEP.
- `requests` vem com o Frappe: o `pyproject.toml` não o declara e o código não importa nenhum outro pacote externo.

## Instalação

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench --site <site> install-app busca_cnpj
bench --site <site> migrate
```

## Configuração e uso

Não há configuração: instalou, funciona. A tela de Fornecedor passa a ter o botão e a máscara.

1. Abra ou crie um **Fornecedor** e informe o CNPJ em *Tax ID*.
2. Clique em *Buscar*, revise os dados retornados e confirme.
3. Em **Endereço** ou **Colaborador**, informe o CEP e use *Buscar* (ou Enter) para completar o endereço.

Mensagens e rótulos estão em português no código; o app **não tem arquivo de tradução** (nenhum `.po`/`.csv`), então
não há tradução sem uso.

## Desenvolvimento

```text
busca_cnpj/
├── api.py                # métodos públicos (buscar_cnpj, buscar_cep, confirmar_dados_cnpj), consulta às APIs e normalização
├── cnpj.py               # normalização, DV (numérico e alfanumérico), formatação, CPF e validar_tax_id
├── supplier_validate.py  # validação server-side do Fornecedor (doc_events)
├── setup.py              # Custom Fields, layout de Address e desativação de scripts legados
├── hooks.py · modules.txt · patches.txt (sem patches)
├── public/js/            # cep.js (global) · supplier.js · address.js · employee.js
├── tests/test_cnpj.py
└── busca_cnpj/doctype/cnae_fornecedor/   # tabela filha de CNAEs
```

Não há workspace, relatórios, formatos de impressão, fixtures nem patches; o único DocType é `CNAE Fornecedor`
(tabela filha).

Carregamento do JavaScript (`hooks.py` no commit): `cep.js` entra em todas as páginas do Desk (`app_include_js`) e
expõe `busca_cnpj.cep` (`strip`, `mask`, `bind_input`, `add_button`, `lookup`); `supplier.js`, `address.js` e
`employee.js` entram por `doctype_js` em Supplier, Address e Employee. `supplier.js` tem as próprias cópias das
funções de CNPJ (`strip_cnpj`, `format_cnpj`, `validate_cnpj`), duplicando `cnpj.py`.

### Testes

Existe **um** arquivo de testes, [busca_cnpj/tests/test_cnpj.py](busca_cnpj/tests/test_cnpj.py), com **9 testes** de
`unittest` puros (sem banco): normalização, valor ASCII-48, CNPJ alfanumérico oficial, CNPJ numérico, DV inválido,
tamanho, formatação e `validar_tax_id`.

```bash
bench --site <site> run-tests --app busca_cnpj
bench --site <site> run-tests --module busca_cnpj.tests.test_cnpj
```

**Não são cobertos**: `buscar_cnpj`, `_consultar_api` e contingência entre fontes, `_normalizar_cnpjws`, `buscar_cep`,
`confirmar_dados_cnpj` (renomeação, Endereço, Contato, CNAEs), `sanitizar_razao_social`, formatadores de telefone e
CEP, `validar_cpf`, `supplier_validate`, `setup.py` (Custom Fields e desativação de scripts legados) e todo o
JavaScript. Não há mocks de HTTP.

### Lint

O app usa `pre-commit` (ruff, eslint, prettier; commitlint em PRs):

```bash
cd apps/busca_cnpj
pre-commit install
```

Conferido em 2026-10-31 com `env/bin/ruff` 0.17.3, sem alterar arquivos: `ruff check` aponta 2 erros (I001, imports
fora de ordem em `api.py` e `setup.py`) e `ruff format --check` indicaria reformatar 5 dos 17 arquivos Python
(a base mistura tabs e espaços).

## Estado do disco (fora do commit)

Este README descreve o que está commitado (`HEAD`, tag `v1.3.6`). Na cópia local há alterações sem commit, **não
documentadas aqui**: `hooks.py` modificado (`app_include_js` passa a incluir também `taxid.js`) e
`busca_cnpj/public/js/taxid.js` não rastreado (`busca_cnpj.taxid`: máscara progressiva de CPF/CNPJ).

## Documentação

- [CHANGELOG.md](CHANGELOG.md): histórico por versão e limites do git.
- Não há pasta `docs/`.

## Licença

MIT (`app_license = "mit"` no `hooks.py`). O arquivo [license.txt](license.txt) é o texto da MIT, mas ainda com os
marcadores `[year] [fullname]` sem preencher.
