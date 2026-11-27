# ADR-001: Leitura mínima garantida em DocTypes vinculados por Link

## Contexto
O `CLM` identificou e corrigiu um problema recorrente em apps Frappe: quando um DocType de um app referencia,
por campo Link, um DocType de outro módulo/app (ex.: ERPNext, HR), o papel de uso básico/diário costuma não ter
nenhuma permissão própria sobre esse DocType referenciado — depende implicitamente de um papel de outro módulo
já conceder leitura, o que nem sempre acontece. O usuário fica bloqueado no meio do fluxo (Link vazio, erro de
permissão ao abrir ou selecionar o registro referenciado), sem indício de que a causa é de outro módulo, não do
app que o usuário estava usando. Ver o precedente completo em
[`clm/docs/adr-006-leitura-minima-em-doctypes-vinculados.md`](https://github.com/still-pulse/clm) (ADR-006 do
`CLM`, que corrigiu o caso concreto com fixtures de `Custom DocPerm` para `CLM Administrator`, `CLM Manager` e
`CLM User`).

O `busca_cnpj` tem uma particularidade em relação ao caso do CLM: **este app não define papéis próprios** (não
há `fixtures/role.json`). Ele preenche três DocTypes padrão de outros módulos — `Supplier` (Fornecedor),
`Address` (Endereço) e `Employee` (Colaborador) — a partir de consultas públicas de CNPJ e CEP, mas quem decide
qual papel de usuário tem acesso a esses botões/APIs é sempre o app consumidor. Hoje o único consumidor
declarado (`required_apps`) é o `integracoes_customizadas`, que usa `busca_cnpj.api.buscar_cnpj`,
`confirmar_dados_cnpj` e as funções de `busca_cnpj.cnpj`/`busca_cnpj.taxid` (ver
[Uso por outros apps](../README.md#uso-por-outros-apps) no README). Se o papel que o `integracoes_customizadas`
expõe a essas funções não tiver leitura garantida em `Supplier`, `Address` e `Employee`, o mesmo tipo de bloqueio
do CLM se repete aqui: o usuário aciona a busca de CNPJ/CEP, mas falha ao abrir ou vincular o próprio registro
que acabou de ser preenchido.

## Decisão
O princípio geral do CLM se aplica ao `busca_cnpj`, mas de forma indireta, por não haver papel próprio aqui para
receber a fixture:

- **O `busca_cnpj` em si não define nem precisa definir papéis ou fixtures de `Custom DocPerm`** — ele só
  preenche campos em DocTypes que já existem, com permissões que já são de outro módulo (ERPNext, HR).
- Qualquer app que exponha uma API, botão ou fluxo do `busca_cnpj` (`buscar_cnpj`, `buscar_cep`,
  `confirmar_dados_cnpj`, `busca_cnpj.cnpj`, `busca_cnpj.taxid`) a um papel de usuário é responsável por garantir
  que esse papel tenha, no mínimo, permissão de leitura (`read`/`select`) em `Supplier`, `Address` e `Employee`
  — os três DocTypes que o `busca_cnpj` preenche. Sem isso, o usuário fica bloqueado no meio do fluxo exatamente
  como no caso do CLM, só que a causa está um nível abaixo (no `busca_cnpj`, preenchendo um registro que o papel
  do app consumidor não pode ler de volta).
- Essa responsabilidade já está sendo tratada à parte, na documentação do próprio `integracoes_customizadas`
  (outro agente cuida disso em paralelo, no repositório daquele app). Este ADR documenta o princípio do lado do
  `busca_cnpj`, para que qualquer novo consumidor que venha a depender deste app saiba, desde o início, que
  precisa garantir essa leitura mínima para o papel que usa.
- Se o `busca_cnpj` um dia vier a preencher um novo DocType vinculado (além de Supplier/Address/Employee), esta
  seção deve ser atualizada no mesmo commit que introduzir esse preenchimento.

## Consequências
- O `busca_cnpj` continua sem fixtures de permissão e sem papéis próprios: nada muda no código ou no
  comportamento do app a partir deste documento.
- A checagem de leitura mínima recai sobre o app consumidor (hoje, `integracoes_customizadas`), não sobre este
  repositório. Revisão de PR aqui deve apenas sinalizar, ao adicionar um novo DocType preenchido pelo
  `busca_cnpj`, que os apps consumidores precisarão revisar as permissões do papel que usam.
- Este documento não cria, remove nem altera nenhuma permissão, fixture ou DocType — é só registro do
  princípio, seguindo o precedente do CLM.
