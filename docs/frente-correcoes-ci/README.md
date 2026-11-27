# Frente de correções de produto reveladas pelo CI: busca_cnpj

Registro de 2026-11-23. Branch: `claude/frappe-ci-product-fixes-ag289b`. PR #4. HEAD antes desta documentação: `8ebaabd`.
Este retrato pode ficar desatualizado: confira `git log`, o PR e os checks reais antes de agir.

## O que foi feito
- `1c2cbe5` CI no padrão institucional; `0854bf6` e `8ebaabd` trocam `db.commit()` por savepoint com rollback parcial em
  `confirmar_dados_cnpj`, que passa a aceitar só POST; `3979a8d` Semgrep `scan` completo. Semgrep de 2 para 0.

## Estado e riscos
- Dispatch verde (Server run 44991081010). **CI do próprio PR não foi visto.**
- Em erro no rename, o save anterior do Fornecedor agora também é revertido (registrado no CHANGELOG).

## Pendências
- Acompanhar o CI do PR #4 até o fim.

## Arquivos desta pasta
- `prompt-nova-sessao.md`: contexto completo da frente, com as regras permanentes, os padrões institucionais, as decisões
  do usuário e o estado de **todos** os apps. Cópia idêntica em cada repositório.
- `setup-ambiente-frappe.sh`: script único de ambiente (bench, MariaDB, Redis, `payments`, `erpnext`, `hrms` e os apps
  clonados). **Nunca foi executado de ponta a ponta**; só a sintaxe e a lógica do `frappe-env` foram validadas.

## Regras que valem aqui
CI verde sempre; nenhum `# nosemgrep`, skip ou job desativado sem aprovação explícita; todo bug corrigido ganha teste;
Semgrep em varredura completa; arredondamento monetário proibido (truncar na 2ª casa); PR só depois de revisor isolado.
