# busca_cnpj

## Dependências

- `required_apps = ["erpnext"]`. É consumido por `integracoes_customizadas` (Jurídico e importação Bionexo), que o declara em
  `required_apps`; mudanças em `busca_cnpj.cnpj` e `busca_cnpj.api` afetam esse app.
- Não há patches. Os testes ficam em `busca_cnpj/tests/` (`test_cnpj.py`).

## Versão, tags e documentação

- `__version__` em `busca_cnpj/__init__.py` deve bater com a tag (hoje ambos em 1.3.6; commits posteriores ficam em "Não lançado" no CHANGELOG). Confira antes de criar a tag.
- **Branch `feature/*` usa o major da `main` + 1** (regra vigente desde 2026-11-01). Minor e patch correm normalmente
  dentro dele: com a `main` em `vX.Y.Z`, a feature nasce em `v(X+1).0.0` e segue `v(X+1).0.1`, `v(X+1).1.0`...
  enquanto estiver na branch. Se a `main` subir de major, a feature sobe junto. Confira a versão da `main`
  (`git show main:busca_cnpj/__init__.py`) e `git tag` antes de tagear, e não reutilize número existente.
- Tags fora do histórico do HEAD (`git tag --no-merged HEAD`) não fazem parte do app; ignore tags `rc/*` no CHANGELOG.
- `README.md` e `CHANGELOG.md` são mantidos à mão, só com o que está commitado; atualize os dois junto com mudanças de comportamento.
- Visão geral das dependências entre apps: `../../CLAUDE.md`.
