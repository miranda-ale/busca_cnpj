# ADR-002: Qualidade e legibilidade de logs de integração externa

## Contexto

O `integracoes_customizadas` identificou e corrigiu um problema recorrente em integrações com serviço externo: a
integração com a API Pública do DataJud (CNJ) passou a falhar com HTTP 403 em todos os tribunais, mas o Error Log
só registrava `"Processo X, tribunal Y: DataJudError. Dados anteriores preservados."` — sem endpoint, método,
status HTTP, corpo da resposta ou traceback. Diagnosticar a causa raiz exigiu ler o código-fonte, não o log. Ao
mesmo tempo, cada processo falhando virava um registro próprio a cada execução — com 56 processos falhando, eram
56 entradas por rodada, inundando o Error Log. A correção (DocType `DataJud Sync Log`, com contexto estruturado,
agrupamento por execução/tipo de erro e chave de API mascarada) e o princípio geral estão documentados em
[`integracoes_customizadas/docs/adr-002-qualidade-e-legibilidade-de-logs.md`](https://github.com/still-pulse/integracoes_customizadas)
e em
[`integracoes_customizadas/docs/datajud-qualidade-de-logs.md`](https://github.com/still-pulse/integracoes_customizadas)
(a correção concreta aplicada ao DataJud).

O `busca_cnpj` é especialmente exposto a esse mesmo tipo de problema: **todo o app é integração com serviço
externo**. `busca_cnpj.api._consultar_api` consulta três bases públicas da Receita Federal em contingência
(CNPJ.ws, BrasilAPI, Minha Receita) e `busca_cnpj.api.buscar_cep` consulta o ViaCEP — ambos via `requests.get`
direto, sem fila, sem cache e sem DocType de log próprio (ver
[Privacidade e limites das consultas](../README.md#privacidade-e-limites-das-consultas) no README).

Hoje, ao inspecionar o código real (`busca_cnpj/api.py`):

- Em `_consultar_api`, uma falha de conexão (`requests.exceptions.RequestException`) em qualquer das três fontes é
  silenciosamente ignorada (`continue`) — **nenhuma chamada a `frappe.log_error` registra qual fonte falhou, com
  que URL, status HTTP ou exceção**. O usuário recebe só `frappe.throw` com uma mensagem genérica
  ("Não foi possível conectar", "Erro ao consultar CNPJ (código N)"); se as três fontes mudarem de contrato ou
  começarem a responder 403/429, não há nenhum registro no Error Log para diagnosticar à distância — exatamente o
  sintoma que motivou o ADR do DataJud, só que aqui ainda pior: nem o log pobre existe, porque não há log nenhum.
- Em `buscar_cep`, o mesmo padrão: falha de conexão ou status HTTP diferente de 200 vira só `frappe.throw`, sem
  `frappe.log_error`.
- Os únicos `frappe.log_error` do app ficam em `confirmar_dados_cnpj` (rename de Supplier duplicado, falha ao criar
  Endereço, falha ao criar Contato) e **já seguem parcialmente o padrão**: título descritivo, nome do Supplier e,
  nos dois últimos, `frappe.get_traceback()` completo. Faltam, porém, o contexto da chamada HTTP que originou a
  falha (quando aplicável) e qualquer classificação de erro.
- Não há segredo em jogo nestas três APIs (CNPJ.ws, BrasilAPI, Minha Receita e ViaCEP são públicas, sem chave), ao
  contrário do DataJud — mas o princípio de não gravar segredo em claro vale para qualquer integração futura deste
  app que passe a exigir autenticação.

## Decisão

O princípio geral do `integracoes_customizadas` (ADR-002 daquele app) se aplica ao `busca_cnpj`: toda integração
com um serviço externo (API de terceiro, webhook, fila) deste app deve logar contexto suficiente para
diagnosticar sem reler o código-fonte, e sem inundar o Error Log:

1. **Contexto estruturado, não só a mensagem da exceção ou o `frappe.throw` ao usuário**: endpoint/URL consultada,
   método HTTP, status HTTP, os primeiros ~1.000 caracteres do corpo da resposta, o tipo da exceção e o
   traceback. Um `frappe.throw` com mensagem amigável para o usuário não substitui o `frappe.log_error` com esse
   contexto técnico — são propósitos diferentes.
2. **Nunca gravar segredo em claro**: nenhuma das integrações atuais (CNPJ.ws, BrasilAPI, Minha Receita, ViaCEP)
   usa chave de API hoje, então esta regra ainda não tem efeito prático aqui — mas vale desde já para qualquer
   integração futura deste app que passe a exigir chave, token ou header de autenticação: nunca em claro no log,
   só um prefixo mascarado quando for útil confirmar qual credencial foi usada.
3. **Classificar o erro**, não só repetir a exceção crua: ao menos falha de conexão/timeout, status 4xx do
   cliente (CNPJ/CEP inválido ou não encontrado) e status 5xx/indisponibilidade do provedor são categorias
   distintas o bastante para decidir a ação (nada a fazer vs. provedor fora do ar vs. dado do usuário errado).
4. **Agrupar falhas repetidas da mesma execução por tipo de erro**, com contagem, em vez de um registro por item
   processado — relevante sobretudo para quem chama `buscar_cnpj` em lote (ex.: a importação Bionexo do
   `integracoes_customizadas`, citada em [Uso por outros apps](../README.md#uso-por-outros-apps)): uma falha
   sistêmica nas três fontes de CNPJ deve gerar poucos registros de log claros, não um por CNPJ da lista.

Isso não exige recriar o design do `DataJud Sync Log` aqui: o volume de chamadas deste app é por clique do usuário
(não por execução agendada com dezenas de itens), então o Error Log do Frappe, usado hoje, continua sendo
suficiente — desde que cada falha de `_consultar_api` e de `buscar_cep` passe a registrar o item 1 acima, o que
hoje **não acontece** (achado, não corrigido neste documento — fora do escopo desta mudança, que é só
documentação). Um DocType próprio de log só se justificaria se este app passasse a rodar em lote com volume de
falha relevante por execução (ver item 4).

## Consequências

- Este documento não altera nenhum código: `_consultar_api` e `buscar_cep` continuam sem `frappe.log_error` nas
  falhas de conexão/HTTP até que outra mudança, com escopo próprio, implemente o item 1 acima.
- Revisão de PR: uma integração externa nova ou alterada neste app que só grava `frappe.log_error(str(exc))` (ou
  nem isso, como hoje em `_consultar_api`/`buscar_cep`) sem status HTTP/corpo/classificação não está completa.
- Ao tocar em `_consultar_api`, `buscar_cep` ou qualquer integração externa nova deste app por outro motivo,
  aproveitar para alinhar o log dela a este padrão.
