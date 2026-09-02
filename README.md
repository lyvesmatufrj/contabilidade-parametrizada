# Contabilidade parametrizada

MVP simples do sistema contábil parametrizado com interface tributária contrafactual estrutural.

O contrato de implementação desta fase está em
[`specs/README_specs_plan.md`](specs/README_specs_plan.md),
com o Marco A implementado nas specs 00–05, o Marco B implementado nas specs 06–07 e a interface estrutural da Spec 08:

- scaffold do projeto;
- convenções canônicas de nomes e tipos;
- plano de contas (`P_t` / `\mathcal P_t`) como `DataFrame` validado;
- template de plano de contas para empresa comercial simples;
- eventos econômicos (`u_t`) determinísticos e validados;
- operador de escrituração para `Lambda_t`;
- Livro Diário, Livro Razão (`Raz_t`) e balancete (`b_t`) derivados.
- workbook Excel (`Wb_t`) como interface física auditável, regenerado pelo Python a partir de `CONFIG`, `PLANO_CONTAS`, `MAPEAMENTO_CONTAS`, `EVENTOS` e `MAPEAMENTO_DF`;
- `MAPEAMENTO_DF` como `COD_CTA -> DEMONSTRACAO -> COD_LINHA`, separado de `MAPEAMENTO_CONTAS`;
- BP e DRE mínimos derivados do balancete e dos movimentos do período, sem lançamentos de encerramento.
- `TaxContext` validado a partir de `ENTIDADE`, `EVENTOS_FISCAIS`, `CENARIOS_TRIBUTARIOS` e `FISCAL_PARAM`, sem cálculo tributário.

Ficam fora desta fase DFC, DVA, geração aleatória, banco de dados, API, ORM, motor tributário concreto, admissibilidade jurídica, bases, alíquotas, créditos, débitos, apuração e comparação monetária de regimes.
