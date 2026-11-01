# busca_cnpj

## Dependências

- `required_apps = ["erpnext"]`. É consumido por `integracoes_customizadas` (Jurídico e importação Bionexo), que o declara em
  `required_apps`; mudanças em `busca_cnpj.cnpj` e `busca_cnpj.api` afetam esse app.
- Não há patches. Os testes ficam em `busca_cnpj/tests/` (`test_cnpj.py`).

## Versão, tags e documentação

- `__version__` em `busca_cnpj/__init__.py` deve bater com a tag (hoje ambos em 1.3.6; commits posteriores ficam em "Não lançado" no CHANGELOG). Confira antes de criar a tag.
- Tags fora do histórico do HEAD (`git tag --no-merged HEAD`) não fazem parte do app; ignore tags `rc/*` no CHANGELOG.
- `README.md` e `CHANGELOG.md` são mantidos à mão, só com o que está commitado; atualize os dois junto com mudanças de comportamento.
- Visão geral das dependências entre apps: `../../CLAUDE.md`.
