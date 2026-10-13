# Busca CNPJ (`busca_cnpj`)

Consulta de CNPJ e CEP brasileiros integrada aos cadastros do ERPNext. Preenche o **Fornecedor** (`Supplier`) a
partir da Receita Federal e agiliza endereços em **Endereço** (`Address`) e **Colaborador** (`Employee`).

Aceita o CNPJ numérico tradicional e o **CNPJ alfanumérico** da Receita Federal (a partir de julho/2026).

## Funcionalidades

### Fornecedor (`Supplier`)

- **Botão de busca de CNPJ**: consulta o CNPJ informado em `tax_id` e apresenta razão social, nome fantasia,
  situação cadastral, natureza jurídica, CNAEs, endereço, telefones, e-mail e quadro societário. Após a
  confirmação do usuário (`confirmar_dados_cnpj`), atualiza o fornecedor, cria o **Endereço** e o **Contato**
  (sócios, telefone e e-mail) vinculados e preenche a tabela de CNAEs.
- **Fontes com contingência**: consulta [CNPJ.ws](https://publica.cnpj.ws); se falhar, usa
  [BrasilAPI](https://brasilapi.com.br) e, por fim, [Minha Receita](https://minhareceita.org).
- **CNAEs do fornecedor**: tabela filha `CNAE Fornecedor` (código, descrição e indicador de CNAE principal) em
  seção recolhível logo abaixo do CNPJ/CPF.
- **Máscara e validação**: formata o CNPJ durante a digitação e valida os dígitos verificadores (numérico e
  alfanumérico) ou o CPF, tanto no formulário quanto no servidor (`doc_events` → `Supplier.validate`).
- **Higienização da razão social**: converte para maiúsculas, remove acentos e descarta caracteres especiais
  (mantém letras, números, espaço e `& - . /`) ao nomear o fornecedor.

### Endereço (`Address`) e Colaborador (`Employee`)

- **Busca de CEP** (ViaCEP): botão e consulta ao digitar o CEP preenchem logradouro, bairro, cidade e UF.
- `Address` ganha o campo **Bairro** e tem o layout ajustado (CEP logo abaixo do tipo de endereço).
- `Employee` ganha o campo **CEP (Endereço Atual)**, que preenche o *Endereço Atual* após confirmação.

### Instalação e migração

- Cria os Custom Fields necessários (`cnaes`, `custom_current_cep`, `custom_bairro`) e ajusta o layout de Address.
- Desativa Client/Server Scripts legados do site que ainda validam CNPJ apenas com dígitos.

## Requisitos

- Frappe v15 e ERPNext (`required_apps = ["erpnext"]`)
- Acesso de saída à internet para as APIs de CNPJ e CEP

## Instalação

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench --site <site> install-app busca_cnpj
bench --site <site> migrate
```

## Uso

1. Abra ou crie um **Fornecedor** e informe o CNPJ em *Tax ID*.
2. Clique no botão de busca de CNPJ, revise os dados retornados e confirme.
3. Em **Endereço** ou **Colaborador**, informe o CEP e use o botão de busca para completar o endereço.

## Desenvolvimento

```text
busca_cnpj/
├── api.py                # métodos públicos: buscar_cnpj, buscar_cep, confirmar_dados_cnpj
├── cnpj.py               # normalização e dígito verificador (numérico e alfanumérico), CPF
├── supplier_validate.py  # validação server-side do Fornecedor
├── setup.py              # Custom Fields e ajustes de instalação/migração
├── public/js/            # supplier.js · address.js · employee.js · cep.js
└── busca_cnpj/doctype/cnae_fornecedor/
```

Testes (a partir da raiz do bench):

```bash
bench --site <site> run-tests --app busca_cnpj --module busca_cnpj.tests.test_cnpj
```

O app usa `pre-commit` (ruff, eslint, prettier, pyupgrade):

```bash
cd apps/busca_cnpj
pre-commit install
```

## Licença

MIT
