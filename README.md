# Contabilidade parametrizada

MVP simples do sistema contábil parametrizado.

O contrato de implementação desta fase está em [`specs/README_specs_plan.md`](specs/README_specs_plan.md), com o Marco A implementado até as specs 00-05:

- scaffold do projeto;
- convenções canônicas de nomes e tipos;
- plano de contas (`P_t` / `\mathcal P_t`) como `DataFrame` validado;
- template de plano de contas para empresa comercial simples;
- eventos econômicos (`u_t`) determinísticos e validados;
- operador de escrituração para `Lambda_t`;
- Livro Diário, Livro Razão (`Raz_t`) e balancete (`b_t`) derivados.

Ficam fora desta fase workbook Excel, BP, DRE, DFC, DVA, geração aleatória, banco de dados, API, ORM e qualquer implementação tributária.
