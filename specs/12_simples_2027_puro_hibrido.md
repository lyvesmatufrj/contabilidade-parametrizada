# Spec 12 — Simples Nacional 2027: comparação puro vs híbrido com CBS em análise de sensibilidade

**Status:** pronta para implementação  
**Prioridade:** alta — demonstração didática/profissional  
**Depende de:** Specs 00–11 + corpus RTC vigente  
**Base de implementação:** `320895cdb31a621db920ca6a8057e94725a0d95f`  
**Data de fechamento do recorte jurídico:** 2026-09-02  
**Período demonstrativo:** janeiro de 2027  
**Decisão analisada:** Simples Nacional “puro” vs. Simples Nacional “híbrido” no 1º semestre de 2027

---

# 1. Objetivo

Implementar o primeiro contrafactual tributário substantivo do projeto sobre uma base econômico-operacional fixa.

A pergunta é:

```text
Para a mesma empresa e as mesmas operações,
o que muda quando IBS/CBS permanecem dentro do Simples Nacional
versus
quando IBS/CBS são apurados pelo regime regular?
```

Formalmente, manter:

```text
EVENTOS^(s) = EVENTOS
EVENTOS_FISCAIS^(s) = EVENTOS_FISCAIS
ENTIDADE^(s) = ENTIDADE
```

e variar somente:

```text
rho_t^(s)
Theta_t^(s)
```

nos dois cenários:

```text
SIMPLES_2027_PURO
SIMPLES_2027_HIBRIDO
```

A comparação deve decompor:

1. carga própria no Simples;
2. parcelas de CBS e IBS dentro do DAS;
3. DAS residual no cenário híbrido;
4. débitos regulares de CBS/IBS;
5. créditos potenciais da própria empresa no regime regular;
6. créditos modelados segundo hipótese explícita de realização;
7. crédito potencial disponibilizado a cliente B2B;
8. encargo tributário comparável;
9. alíquota de equilíbrio da CBS.

A Spec 12 **não escolhe automaticamente o “melhor” regime**.

---

# 2. Motivação didática e profissional

A demonstração deve representar uma decisão efetivamente disponível em 2026 para efeitos em 2027.

No Simples “puro”:

```text
CBS e IBS permanecem no regime unificado.
```

No Simples “híbrido”:

```text
a empresa continua optante pelo Simples Nacional para os demais tributos,
mas CBS e IBS são apurados e recolhidos segundo o regime regular.
```

Essa comparação é especialmente útil em operações B2B porque o regime escolhido altera a posição da empresa e de seus clientes na cadeia de créditos.

A saída deve servir como:

```text
suporte quantitativo, auditável e pedagógico à decisão
```

e não como:

```text
parecer jurídico
recomendação automática
promessa de economia
substituição do PGDAS-D
substituição da apuração assistida oficial
```

---

# 3. Source of truth

A precedência continua:

```text
Volumes I–III
    >
Specs
    >
código
```

Para a camada tributária:

```text
fontes normativas oficiais
    ->
FISCAL_PARAM
    ->
seleção de regra efetiva
    ->
cálculo
    ->
resultado
```

A Spec 12 preserva integralmente a governança da Spec 08:

```text
Prov(p)
=
(fonte, dispositivo, versão, vigência, data de consulta)
```

para todo parâmetro normativo efetivamente utilizado.

---

# 4. Corpus jurídico e técnico do recorte

## 4.1 Fontes normativas centrais

Usar prioritariamente:

```text
docs/tax_sources/rtc/normative/02_LC_214_2025_compilada.html
docs/tax_sources/rtc/normative/23_LC_123_2006_compilada.html
docs/tax_sources/rtc/normative/24_Resolucao_CGSN_186_2026.html
docs/tax_sources/rtc/normative/25_Resolucao_CGSN_190_2026.html
```

### Papel da LC 214/2025

Usar para:

- opção do optante do Simples pelo regime regular de IBS/CBS;
- regras gerais de não cumulatividade;
- créditos no regime regular;
- limitação de créditos do optante que mantém IBS/CBS no Simples;
- crédito do adquirente no regime regular quando compra de optante pelo Simples;
- alíquota do IBS em 2027;
- regra de transição da CBS em 2027;
- necessidade de resolução do Senado para a alíquota de referência da CBS.

### Papel da LC 123/2006

Usar para:

- RBT12;
- fórmula da alíquota efetiva;
- Anexo I;
- estrutura do Simples Nacional;
- percentuais efetivos por tributo.

### Papel da Resolução CGSN 186/2026

Usar para o recorte temporal excepcional de 2027:

```text
01/09/2026 a 30/09/2026
```

para a opção relativa ao primeiro semestre de 2027.

### Papel da Resolução CGSN 190/2026

Usar para:

- faculdade de recolher CBS/IBS no regime regular;
- exclusão das parcelas de CBS/IBS do regime unificado quando exercida a opção;
- opção semestral;
- base temporal por faturamento;
- Anexo I de 2027;
- repartição entre IRPJ, CSLL, CBS, CPP, ICMS e IBS.

## 4.2 Fonte 26

```text
docs/tax_sources/rtc/normative/26_Resolucao_CGSN_191_2026.html
```

permanece no corpus, mas **não é necessária ao recorte material de comércio de mercadorias desta spec**.

Seu conteúdo relativo à NFS-e é relevante para futuros recortes de serviços.

Não criar dependência artificial dessa fonte.

## 4.3 Fontes de orientação

Usar como apoio interpretativo e de UX, nunca acima das normas:

```text
docs/tax_sources/rtc/guidance/27_Roteiro_Opcao_Simples_2027.pdf
docs/tax_sources/rtc/guidance/28_Manual_Opcao_IBS_CBS_Regime_Regular_Simples_2027.pdf
docs/tax_sources/rtc/guidance/29_Orientacao_RFB_Simples_Puro_Hibrido_2027.html
docs/tax_sources/rtc/guidance/30_TCU_Metodologia_Aliquota_CBS_2027.pdf
```

A fonte 29 fundamenta a utilidade didática da comparação B2B.

A fonte 30 documenta metodologia e processo de fixação da alíquota da CBS, mas **não fornece uma alíquota legal definitiva de 2027**.

---

# 5. Decisão jurídica central

O optante pelo Simples pode permanecer:

```text
Simples puro
```

ou exercer a opção:

```text
Simples híbrido
=
Simples para os demais tributos
+
regime regular para IBS/CBS
```

No híbrido:

```text
as parcelas de IBS e CBS não são cobradas no regime unificado.
```

Essa é a variação de `rho_t` da Spec 12.

Não alterar a entidade nem os fatos para construir o cenário alternativo.

---

# 6. Regra arquitetural central — fato não é resultado fiscal

A Spec 09 permanece congelada.

Ela foi construída como uma fotografia documental CBS 2026 e validava, entre outros:

```text
PCBS_PERCENT
VCBS_CENTS
```

contra a regra vigente.

Esse contrato **não deve ser reaproveitado como entrada do novo contrafactual 2027**.

Na Spec 12:

```text
alíquota
débito
crédito
CBS calculada
IBS calculado
```

são derivados do cenário.

Logo:

```text
EVENTOS_FISCAIS
```

não deve conter para o novo demo:

```text
PCBS_PERCENT
VCBS_CENTS
PIBS_PERCENT
VIBS_CENTS
CREDITO_CENTS
DEBITO_CENTS
```

como fonte de verdade factual.

Preservar a direção:

```text
fato econômico/documental
    ->
regra do cenário
    ->
resultado tributário
```

Não modificar a Spec 09 para atingir esse objetivo.

---

# 7. Separação obrigatória: parâmetro normativo vs. parâmetro analítico

Esta é uma decisão bloqueadora da Spec 12.

## 7.1 Parâmetros normativos

Definir:

```text
Theta_t^norm
```

como os parâmetros jurídicos persistidos em:

```text
FISCAL_PARAM
```

Esses parâmetros:

- exigem fonte oficial;
- exigem dispositivo;
- exigem vigência;
- exigem versão normativa;
- exigem data de consulta;
- exigem versão computacional;
- pertencem ao `TaxContext`.

Exemplos:

```text
alíquota nominal do Anexo I
parcela a deduzir
percentual de repartição da CBS
percentual de repartição do IBS
alíquota regular do IBS em 2027
```

## 7.2 Parâmetros analíticos

Definir separadamente:

```text
theta^analysis
```

Esses parâmetros são hipóteses de simulação.

Eles **não são legislação**.

Criar schema canônico:

```python
TAX_ANALYSIS_PARAMETER_COLUMNS = (
    "ID_ANALISE",
    "CHAVE_PARAM",
    "VALOR",
    "TIPO_VALOR",
    "DESCRICAO",
)
```

Materialização Excel:

```text
ANALISE_PARAM
```

Representação Python:

```text
analysis_parameters: DataFrame
```

Eles não pertencem a `TaxContext`.

Não adicionar:

```text
FONTE_URL
DISPOSITIVO
VIG_INI
VIG_FIM
VERSAO_NORMA
```

a `ANALISE_PARAM`, pois isso poderia sugerir natureza normativa.

## 7.3 Proibição de mistura

Nunca:

```text
ANALISE_PARAM -> FISCAL_PARAM
```

automaticamente.

Nunca:

```text
hipótese analítica -> Prov(p)
```

Nunca permitir a mesma `CHAVE_PARAM` simultaneamente como:

```text
normativa
e
analítica
```

com semântica ambígua.

## 7.4 Regra de precedência para a CBS 2027

O parâmetro normativo futuro será:

```text
CBS_2027_REGULAR_RATE_FRACTION
```

Enquanto não houver linha normativa válida e vigente para essa chave:

```text
CBS oficial 2027 = pendente
```

Para a demonstração, usar exclusivamente:

```text
CBS_2027_ANALYSIS_RATE_FRACTION
```

de `ANALISE_PARAM`.

Quando, no futuro, `FISCAL_PARAM` passar a conter:

```text
CBS_2027_REGULAR_RATE_FRACTION
```

com proveniência válida:

```text
taxa normativa tem precedência
```

e a taxa analítica é ignorada no cálculo principal.

O relatório deve registrar:

```text
CBS_RATE_SOURCE = "normative"
```

ou:

```text
CBS_RATE_SOURCE = "analysis"
```

Nunca inferir que uma taxa de análise é a taxa legal esperada.

---

# 8. Parâmetros analíticos da primeira demonstração

Criar em:

```text
data/examples/simples_2027/analysis_parameters.csv
```

as linhas:

```text
ID_ANALISE = DEMO_SIMPLES_2027
CHAVE_PARAM = CBS_2027_ANALYSIS_RATE_FRACTION
VALOR = 0.09
TIPO_VALOR = decimal
DESCRICAO = Hipótese analítica para demonstração; não representa alíquota oficial da CBS 2027.
```

e:

```text
ID_ANALISE = DEMO_SIMPLES_2027
CHAVE_PARAM = REGULAR_CREDIT_REALIZATION_FRACTION
VALOR = 1.0
TIPO_VALOR = decimal
DESCRICAO = Hipótese analítica de realização integral dos créditos elegíveis no período.
```

A escolha de `0.09` tem finalidade pedagógica: colocar o caso próximo da alíquota de equilíbrio.

Não descrever `0.09` como:

```text
estimativa oficial
previsão do governo
alíquota provável
alíquota de referência
```

---

# 9. Escopo material da primeira versão

Implementar somente:

- pessoa jurídica;
- empresa comercial;
- optante pelo Simples Nacional;
- Anexo I;
- RBT12 positivo;
- RBT12 até R$ 3.600.000,00;
- faixas 1 a 5 do Anexo I;
- um estabelecimento;
- janeiro de 2027;
- operações domésticas;
- mercadorias comuns;
- compras para revenda;
- fornecedor das compras sujeito ao regime regular de IBS/CBS;
- vendas B2B para cliente sujeito ao regime regular;
- vendas B2C para consumidor final;
- sem tratamento diferenciado/específico;
- sem devolução/cancelamento;
- sem exportação;
- sem importação;
- sem substituição tributária;
- sem monofasia;
- sem ZFM/ALC;
- sem ativo imobilizado;
- sem frete autônomo;
- sem descontos condicionais/incondicionais;
- sem benefícios fiscais;
- sem créditos presumidos;
- sem saldos anteriores;
- sem compensações interperíodos;
- sem split payment operacional;
- sem recolhimento pelo adquirente;
- sem reconstrução integral da NF-e;
- sem reconciliação contábil do tributo.

A limitação:

```text
RBT12 <= 3.600.000,00
```

é uma fronteira de engenharia da primeira versão para evitar o tratamento do sublimite/faixa 6.

Não afirmar que R$ 3,6 milhões é o limite geral de opção do Simples.

---

# 10. Fora de escopo

Não implementar nesta spec:

- faixa 6 do Anexo I;
- Anexos II a V;
- MEI;
- início de atividade;
- segregações complexas de receita;
- serviços;
- NFS-e;
- ICMS fora do Simples por sublimite;
- receitas monofásicas;
- ICMS-ST;
- PIS/Cofins históricos;
- comparação Lucro Real vs. Presumido;
- DRE fiscal;
- contabilização de IBS/CBS;
- pagamento real;
- fluxo de caixa real;
- data efetiva de extinção de débito para cada documento;
- créditos de compras feitas de fornecedor do Simples;
- ranking de regimes;
- recomendação automática;
- otimização;
- parecer jurídico.

Compras de fornecedor do Simples ficam para uma extensão posterior, porque sua correta modelagem exige atributos adicionais do fornecedor e do crédito correspondente.

---

# 11. Cenários

O fixture canônico da Spec 12 deve conter exatamente dois cenários ativos.

## 11.1 Baseline

```text
ID_CENARIO = SIMPLES_2027_PURO
E_BASELINE = true
REGIME_ENTIDADE = simples_nacional
REGIME_CONSUMO = simples_ibs_cbs_das
DT_REFERENCIA_NORMATIVA = 2027-01-31
ID_VERSAO_NORMATIVA = SIMPLES_2027_H1_V1
ATIVO = true
```

## 11.2 Alternativo

```text
ID_CENARIO = SIMPLES_2027_HIBRIDO
E_BASELINE = false
REGIME_ENTIDADE = simples_nacional
REGIME_CONSUMO = ibs_cbs_regime_regular
DT_REFERENCIA_NORMATIVA = 2027-01-31
ID_VERSAO_NORMATIVA = SIMPLES_2027_H1_V1
ATIVO = true
```

Os dois cenários referenciam a mesma entidade e o mesmo bundle normativo.

A diferença jurídica está em:

```text
REGIME_CONSUMO
```

---

# 12. Entidade do demo

Criar:

```text
data/examples/simples_2027/entity_profile.csv
```

com pelo menos:

```text
TIPO_PESSOA = pj
ATIVIDADE = comercio_revenda_mercadorias
OPTANTE_SIMPLES = true
ANEXO_SIMPLES = I
RBT12_CENTS = 120000000
```

onde:

```text
R$ 1.200.000,00 = 120.000.000 centavos
```

Não incluir resultado tributário em `ENTIDADE`.

---

# 13. Base econômica do demo

Criar uma empresa sintética com quatro eventos principais.

## Evento 1 — aporte

```text
aporte de capital
R$ 200.000,00
```

Não é fato gerador do recorte tributário.

## Evento 2 — compra para revenda

```text
compra de mercadoria
R$ 85.000,00
fornecedor no regime regular IBS/CBS
destinação = revenda
```

## Evento 3 — venda B2B

```text
venda
R$ 70.000,00
cliente no regime regular IBS/CBS
tipo_cliente = b2b
```

Custo da mercadoria:

```text
R$ 59.500,00
```

## Evento 4 — venda B2C

```text
venda
R$ 30.000,00
consumidor final
tipo_cliente = b2c
```

Custo da mercadoria:

```text
R$ 25.500,00
```

Assim:

```text
receita do mês = R$ 100.000,00
compras elegíveis = R$ 85.000,00
CMV = R$ 85.000,00
resultado bruto/contábil simplificado = R$ 15.000,00
```

Os quatro eventos são fatos comuns a ambos os cenários.

---

# 14. Atributos fiscais factuais mínimos

Usar `EVENTOS_FISCAIS` em formato longo.

Para compra:

```text
AMBITO_OPERACAO = domestica
REGIME_FORNECEDOR = ibs_cbs_regime_regular
DESTINACAO_AQUISICAO = revenda
```

Para venda B2B:

```text
AMBITO_OPERACAO = domestica
TIPO_CLIENTE = b2b
REGIME_ADQUIRENTE = ibs_cbs_regime_regular
```

Para venda B2C:

```text
AMBITO_OPERACAO = domestica
TIPO_CLIENTE = b2c
REGIME_ADQUIRENTE = consumidor_final
```

Não exigir:

```text
PCBS_PERCENT
VCBS_CENTS
```

ou equivalentes como entradas.

---

# 15. Convenção de base econômica

Para esta primeira demonstração, adotar explicitamente a convenção de engenharia:

```text
VL_EVENTO_CENTS das compras/vendas suportadas
=
valor econômico fixo usado como base do cálculo comparativo
```

dentro do recorte sem ajustes de base.

Isso permite preservar:

```text
EVENTOS^(puro) = EVENTOS^(hibrido)
```

A Spec 12 **não reconstrói o valor total da NF-e nem altera contas a receber/pagar em função do IBS/CBS do cenário**.

Portanto:

```text
resultado tributário da Spec 12
```

não deve ser automaticamente lançado no núcleo contábil.

Essa limitação deve aparecer no README/COMPARACAO do demo.

---

# 16. Parâmetros normativos exigidos

Adicionar a:

```text
data/examples/simples_2027/tax_parameters.csv
```

um bundle:

```text
ID_VERSAO_NORMATIVA = SIMPLES_2027_H1_V1
```

com os seguintes parâmetros obrigatórios.

## 16.1 Faixas 1 a 5 do Anexo I

Para `n = 1..5`:

```text
SIMPLES_ANNEX_I_F{n}_RBT12_MAX_CENTS
SIMPLES_ANNEX_I_F{n}_NOMINAL_RATE_FRACTION
SIMPLES_ANNEX_I_F{n}_DEDUCTION_CENTS
```

Valores:

```text
F1: 18000000  | 0.04  | 0
F2: 36000000  | 0.073 | 594000
F3: 72000000  | 0.095 | 1386000
F4: 180000000 | 0.107 | 2250000
F5: 360000000 | 0.143 | 8730000
```

Todos os valores monetários estão em centavos.

## 16.2 Repartição

```text
SIMPLES_ANNEX_I_CBS_SHARE_FRACTION = 0.1533
SIMPLES_ANNEX_I_IBS_SHARE_FRACTION = 0.0017
```

Esses valores são usados somente no escopo das faixas 1 a 5.

## 16.3 Base temporal

```text
SIMPLES_2027_REVENUE_RECOGNITION = faturamento
```

## 16.4 IBS regular

```text
IBS_2027_REGULAR_RATE_FRACTION = 0.001
```

correspondente ao total:

```text
0,05% estadual + 0,05% municipal = 0,10%
```

## 16.5 CBS regular

Nesta versão inicial:

```text
NÃO adicionar
CBS_2027_REGULAR_RATE_FRACTION
```

a `FISCAL_PARAM`.

A ausência é intencional e representa:

```text
alíquota normativa ainda pendente de fixação
```

A implementação deve aceitar essa chave como **opcional**, nunca obrigatória enquanto o ato do Senado não for incorporado.

---

# 17. Valores normativos não podem ser hard-coded no motor

O código pode hard-code:

- nomes de chaves;
- nomes dos regimes suportados;
- fronteiras de escopo;
- nomes de status.

O código não pode hard-code como valor normativo:

```text
0.04
0.073
0.095
0.107
0.143
5940
13860
22500
87300
0.1533
0.0017
0.001
```

Esses valores devem vir de `FISCAL_PARAM`.

Também não hard-code:

```text
0.09
```

como CBS 2027.

A taxa 0.09 vem de `ANALISE_PARAM`.

---

# 18. Tipos numéricos

Usar:

```python
Decimal
```

para taxas e cálculos.

Nunca usar `float` binário como fonte de verdade.

Persistir valores de parâmetros como:

```text
texto + TIPO_VALOR
```

seguindo a arquitetura da Spec 08.

---

# 19. Seleção da faixa do Simples

Dado:

```text
RBT12
```

selecionar exatamente uma faixa entre F1 e F5.

Se:

```text
RBT12 <= 0
```

rejeitar.

Se:

```text
RBT12 > 360000000 cents
```

rejeitar como fora do recorte.

Não implementar a faixa 6 silenciosamente.

---

# 20. Alíquota efetiva do Simples

Calcular:

```text
a_eff
=
(RBT12 * a_nom - PD) / RBT12
```

onde:

```text
a_nom = alíquota nominal da faixa
PD = parcela a deduzir
```

Para o demo:

```text
RBT12 = R$ 1.200.000
a_nom = 10,70%
PD = R$ 22.500
```

esperar:

```text
a_eff = 0.08825
```

ou:

```text
8,825%
```

---

# 21. Receita mensal

A base mensal do Simples no demo é a soma das vendas suportadas no período:

```text
R = R$ 100.000,00
```

Usar faturamento.

Não usar recebimento financeiro da venda a prazo como critério.

---

# 22. Cenário Simples puro

Calcular:

```text
DAS_TOTAL = R * a_eff
```

Para o demo:

```text
DAS_TOTAL = R$ 8.825,00
```

Calcular:

```text
DAS_CBS = DAS_TOTAL * 0.1533
DAS_IBS = DAS_TOTAL * 0.0017
```

e:

```text
DAS_OUTROS
=
DAS_TOTAL - DAS_CBS - DAS_IBS
```

Após arredondamento canônico dos outputs:

```text
DAS_CBS = R$ 1.352,87
DAS_IBS = R$ 15,00
DAS_OUTROS = R$ 7.457,13
```

A própria empresa no Simples puro:

```text
CREDITO_EMPRESA_CBS_POTENCIAL = 0
CREDITO_EMPRESA_IBS_POTENCIAL = 0
```

porque não apropria créditos de IBS/CBS nessa opção.

---

# 23. Crédito potencial do cliente B2B no Simples puro

Para vendas B2B a adquirente no regime regular:

```text
R_B2B = R$ 70.000,00
```

definir:

```text
taxa_efetiva_CBS_Simples
=
a_eff * share_CBS
```

e:

```text
taxa_efetiva_IBS_Simples
=
a_eff * share_IBS
```

Calcular crédito potencial ao cliente:

```text
CLIENTE_B2B_CREDITO_CBS_POTENCIAL
=
R_B2B * taxa_efetiva_CBS_Simples
```

```text
CLIENTE_B2B_CREDITO_IBS_POTENCIAL
=
R_B2B * taxa_efetiva_IBS_Simples
```

No demo, após arredondamento:

```text
CBS = R$ 947,01
IBS = R$ 10,50
```

Usar sempre a expressão:

```text
crédito potencial ao cliente sujeito ao regime regular
```

Não afirmar:

```text
crédito financeiro efetivamente realizado
```

---

# 24. Cenário híbrido

No híbrido:

```text
DAS_OUTROS
```

permanece igual ao componente residual calculado a partir do Anexo I.

CBS e IBS deixam o DAS.

## 24.1 Taxa CBS usada

Resolver a taxa nesta ordem:

```text
1. CBS_2027_REGULAR_RATE_FRACTION em FISCAL_PARAM, se presente, válido e vigente
2. CBS_2027_ANALYSIS_RATE_FRACTION em ANALISE_PARAM
```

Registrar:

```text
CBS_RATE_SOURCE
```

como:

```text
normative
```

ou:

```text
analysis
```

## 24.2 Taxa IBS

Usar:

```text
IBS_2027_REGULAR_RATE_FRACTION
```

sempre de `FISCAL_PARAM`.

---

# 25. Débitos regulares

Para cada tributo `j` em:

```text
CBS
IBS
```

calcular:

```text
DEBITO_j = R * r_j
```

No demo com taxa analítica CBS de 9%:

```text
CBS_DEBITO = R$ 9.000,00
IBS_DEBITO = R$ 100,00
```

---

# 26. Créditos potenciais da empresa

Compras elegíveis:

```text
P = R$ 85.000,00
```

Calcular:

```text
CREDITO_POTENCIAL_j = P * r_j
```

No demo:

```text
CBS = R$ 7.650,00
IBS = R$ 85,00
```

Esses valores são apresentados como:

```text
créditos potenciais do regime regular
```

e continuam sujeitos aos requisitos jurídicos/operacionais de apropriação.

---

# 27. Crédito modelado para comparação

Aplicar:

```text
alpha
=
REGULAR_CREDIT_REALIZATION_FRACTION
```

de `ANALISE_PARAM`.

Definir:

```text
CREDITO_MODELADO_j
=
alpha * CREDITO_POTENCIAL_j
```

Para o demo:

```text
alpha = 1
```

Esse é um **parâmetro analítico**, não norma.

O relatório deve marcar métricas dependentes de `alpha` como:

```text
analitico
```

---

# 28. Saldo regular modelado

Calcular:

```text
S_j
=
DEBITO_j - CREDITO_MODELADO_j
```

Guardar separadamente:

```text
T_j = max(S_j, 0)
C_SALDO_j = max(-S_j, 0)
```

No demo:

```text
CBS T = R$ 1.350,00
IBS T = R$ 15,00
```

Não chamar `T_j` de pagamento efetivamente ocorrido.

Usar no produto:

```text
saldo líquido modelado
```

ou:

```text
valor líquido modelado
```

---

# 29. Encargo tributário comparável

Para fins exclusivamente analíticos, definir:

```text
E_puro
=
DAS_TOTAL
```

e:

```text
E_hibrido
=
DAS_OUTROS
+
T_CBS
+
T_IBS
```

Essa métrica é:

```text
comparável
```

mas não é:

```text
fluxo de caixa real
```

No demo:

```text
E_puro = R$ 8.825,00
E_hibrido = R$ 8.822,13
```

Após materialização em centavos:

```text
DELTA_E
=
E_hibrido - E_puro
=
-R$ 2,87
```

A subtração deve usar os valores monetários já materializados em centavos.

---

# 30. Crédito potencial do cliente B2B no híbrido

Calcular:

```text
CLIENTE_B2B_CREDITO_CBS_POTENCIAL
=
R_B2B * r_CBS
```

```text
CLIENTE_B2B_CREDITO_IBS_POTENCIAL
=
R_B2B * r_IBS
```

No demo com CBS analítica de 9%:

```text
CBS = R$ 6.300,00
IBS = R$ 70,00
```

Esses valores devem ser apresentados lado a lado com o Simples puro.

---

# 31. Alíquota de equilíbrio da CBS

Para:

```text
R - alpha*P > 0
```

definir a taxa de CBS que iguala o encargo comparável:

```text
r_CBS*
=
(DAS_CBS + DAS_IBS) / (R - alpha*P)
-
r_IBS
```

No demo:

```text
r_CBS*
=
0.090191666666...
```

aproximadamente:

```text
9,0192%
```

Esse objeto é:

```text
DERIVADO ANALÍTICO
```

Não é:

```text
alíquota legal
alíquota prevista
recomendação
```

Se:

```text
R - alpha*P <= 0
```

retornar:

```text
None
```

e informar que não existe limiar finito dentro da forma analítica usada.

---

# 32. Interpretação do limiar

O workbook pode explicar:

```text
taxa CBS usada < r_CBS*
    ->
encargo comparável híbrido menor no modelo

taxa CBS usada > r_CBS*
    ->
encargo comparável híbrido maior no modelo
```

Isso não implica decisão ótima porque ainda existem:

- créditos na cadeia;
- preço;
- margem;
- prazo financeiro;
- perfil dos clientes;
- risco operacional;
- compliance;
- outros tributos e restrições.

Não produzir recomendação automática.

---

# 33. Arredondamento

Usar `Decimal`.

Definir uma convenção de engenharia determinística:

```text
ROUND_HALF_UP
```

para materialização de métricas monetárias em centavos.

A ordem é:

```text
1. calcular em Decimal com precisão suficiente
2. materializar cada métrica monetária reportada em centavos
3. calcular DELTA a partir dos valores reportados em centavos
```

Não afirmar que essa convenção reproduz todos os detalhes internos do PGDAS-D.

No demo:

```text
E_puro = 882500 cents
E_hibrido = 882213 cents
DELTA = -287 cents
```

---

# 34. Novo módulo

Criar:

```text
src/accounting_sim/tax_simples_2027.py
```

Não modificar:

```text
src/accounting_sim/tax_cbs_2026.py
```

salvo import puramente necessário, que deve ser evitado.

---

# 35. API pública mínima

Criar:

```python
SIMPLES_2027_RULE_SPEC_VERSION = "spec_12_simples_2027_puro_hibrido_v1"
```

Dataclasses:

```python
@dataclass(frozen=True)
class EffectiveSimples2027Rules:
    normative_version_id: str
    rule_version: str
    annex_i_bands: tuple[...]
    cbs_share_fraction: Decimal
    ibs_share_fraction: Decimal
    ibs_regular_rate_fraction: Decimal
    cbs_regular_rate_fraction: Decimal | None
    revenue_recognition: str
```

```python
@dataclass(frozen=True)
class Simples2027AnalysisAssumptions:
    analysis_id: str
    cbs_analysis_rate_fraction: Decimal
    regular_credit_realization_fraction: Decimal
```

```python
@dataclass(frozen=True)
class Simples2027CounterfactualReport:
    baseline_scenario_id: str
    alternative_scenario_id: str
    scenario_results: pd.DataFrame
    comparison_results: pd.DataFrame
    cbs_rate_used_fraction: Decimal
    cbs_rate_source: str
    cbs_break_even_rate_fraction: Decimal | None
```

Funções:

```python
def validate_tax_analysis_parameters(
    analysis_parameters: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def validate_simples_2027_admissibility(
    events: pd.DataFrame,
    tax_context: TaxContext,
    analysis_parameters: pd.DataFrame,
) -> ValidationReport:
    ...
```

```python
def select_effective_simples_2027_rules(
    tax_context: TaxContext,
    scenario_id: str,
) -> EffectiveSimples2027Rules:
    ...
```

```python
def select_simples_2027_analysis_assumptions(
    analysis_parameters: pd.DataFrame,
) -> Simples2027AnalysisAssumptions:
    ...
```

```python
def run_simples_2027_counterfactual_report(
    events: pd.DataFrame,
    tax_context: TaxContext,
    analysis_parameters: pd.DataFrame,
) -> Simples2027CounterfactualReport:
    ...
```

Pode decompor internamente em helpers.

Não criar framework genérico de engines.

---

# 36. Schema de resultados por cenário

Definir em `tax_simples_2027.py`:

```python
SIMPLES_2027_SCENARIO_RESULT_COLUMNS = (
    "ID_CENARIO",
    "REGIME_CONSUMO",
    "RECEITA_MES_CENTS",
    "RBT12_CENTS",
    "ALIQUOTA_EFETIVA_SIMPLES",
    "DAS_TOTAL_CENTS",
    "DAS_CBS_CENTS",
    "DAS_IBS_CENTS",
    "DAS_OUTROS_CENTS",
    "CBS_REGULAR_RATE_FRACTION",
    "CBS_RATE_SOURCE",
    "CBS_DEBITO_REGULAR_CENTS",
    "CBS_CREDITO_EMPRESA_POTENCIAL_CENTS",
    "CBS_CREDITO_EMPRESA_MODELADO_CENTS",
    "CBS_VALOR_LIQUIDO_MODELADO_CENTS",
    "CBS_SALDO_CREDOR_MODELADO_CENTS",
    "IBS_REGULAR_RATE_FRACTION",
    "IBS_DEBITO_REGULAR_CENTS",
    "IBS_CREDITO_EMPRESA_POTENCIAL_CENTS",
    "IBS_CREDITO_EMPRESA_MODELADO_CENTS",
    "IBS_VALOR_LIQUIDO_MODELADO_CENTS",
    "IBS_SALDO_CREDOR_MODELADO_CENTS",
    "ENCARGO_TRIBUTARIO_COMPARAVEL_CENTS",
    "CLIENTE_B2B_CREDITO_CBS_POTENCIAL_CENTS",
    "CLIENTE_B2B_CREDITO_IBS_POTENCIAL_CENTS",
    "STATUS_RESULTADO",
    "VERSAO_REGRA",
)
```

Semântica:

### Puro

Campos regulares não aplicáveis:

```text
CBS_REGULAR_RATE_FRACTION = None
CBS_DEBITO_REGULAR_CENTS = None
CBS_CREDITO_EMPRESA_MODELADO_CENTS = None
...
```

Mas:

```text
CBS_CREDITO_EMPRESA_POTENCIAL_CENTS = 0
IBS_CREDITO_EMPRESA_POTENCIAL_CENTS = 0
```

porque a impossibilidade de apropriação é uma conclusão normativa, não ausência de informação.

### Híbrido

Preencher campos regulares.

`STATUS_RESULTADO`:

```text
normativo
```

para puro.

Para híbrido nesta primeira versão:

```text
analitico
```

porque `alpha` é uma hipótese analítica e, enquanto não houver taxa CBS normativa, a taxa CBS também será analítica.

---

# 37. Schema de comparação

Definir:

```python
SIMPLES_2027_COMPARISON_COLUMNS = (
    "ID_CENARIO_BASE",
    "ID_CENARIO",
    "METRICA",
    "BASELINE_CENTS",
    "ALTERNATIVO_CENTS",
    "DELTA_CENTS",
    "STATUS_BASELINE",
    "STATUS_ALTERNATIVO",
)
```

Gerar pelo menos:

```text
ENCARGO_TRIBUTARIO_COMPARAVEL
CREDITO_EMPRESA_CBS_POTENCIAL
CREDITO_EMPRESA_IBS_POTENCIAL
CLIENTE_B2B_CREDITO_CBS_POTENCIAL
CLIENTE_B2B_CREDITO_IBS_POTENCIAL
```

Delta sempre:

```text
alternativo - baseline
```

Não produzir ranking.

---

# 38. Validação estrutural de ANALISE_PARAM

Exigir:

- schema exato;
- uma única `ID_ANALISE`;
- `CHAVE_PARAM` única;
- `VALOR` persistido como texto;
- `TIPO_VALOR` válido;
- `float` binário rejeitado como entrada programática;
- `CBS_2027_ANALYSIS_RATE_FRACTION` em `(0,1)`;
- `REGULAR_CREDIT_REALIZATION_FRACTION` em `[0,1]`.

Não aceitar colunas de proveniência normativa.

Não aceitar a chave:

```text
CBS_2027_REGULAR_RATE_FRACTION
```

em `ANALISE_PARAM`.

Ela pertence exclusivamente a `FISCAL_PARAM`.

---

# 39. Validação dos cenários

Exigir:

- exatamente dois cenários ativos;
- exatamente um baseline;
- baseline com `REGIME_CONSUMO=simples_ibs_cbs_das`;
- alternativa com `REGIME_CONSUMO=ibs_cbs_regime_regular`;
- ambos `REGIME_ENTIDADE=simples_nacional`;
- mesma entidade;
- mesma `ID_VERSAO_NORMATIVA`;
- referência normativa dentro do primeiro semestre de 2027;
- nenhuma alteração em fatos.

Cenários inativos são ignorados.

---

# 40. Validação da entidade

Exigir:

```text
TIPO_PESSOA = pj
ATIVIDADE = comercio_revenda_mercadorias
OPTANTE_SIMPLES = true
ANEXO_SIMPLES = I
```

e:

```text
0 < RBT12_CENTS <= 360000000
```

---

# 41. Validação dos eventos

Somente tipos tributariamente suportados:

```text
compra_mercadoria_a_vista
compra_mercadoria_a_prazo
venda_a_vista
venda_a_prazo
```

Outros eventos contábeis, como aporte:

```text
são ignorados pela camada tributária
```

e continuam no núcleo contábil.

Exigir pelo menos:

- uma compra elegível;
- uma venda;
- uma venda B2B;
- uma venda B2C.

---

# 42. Não cumulatividade no híbrido

Nesta spec, crédito potencial só é calculado para compra que satisfaça:

```text
AMBITO_OPERACAO = domestica
REGIME_FORNECEDOR = ibs_cbs_regime_regular
DESTINACAO_AQUISICAO = revenda
```

Não modelar outras origens de crédito.

O crédito modelado é:

```text
potencial * alpha
```

e não uma afirmação de apropriação efetiva.

---

# 43. Não alterar schemas das Specs 09–11

Não alterar:

```text
TAX_OPERATION_RESULT_COLUMNS
TAX_ASSESSMENT_RESULT_COLUMNS
COUNTERFACTUAL_COMPARISON_COLUMNS
```

para encaixar artificialmente o Simples 2027.

A Spec 12 usa seus schemas próprios.

Isso evita distorcer o significado de:

```text
S_APUR
T_RECOLHER
```

para um problema que envolve DAS + regime regular + métricas de cadeia.

---

# 44. Integração com workbook

Adicionar ao contrato global:

```text
ANALISE_PARAM
SIMPLES_2027_RESULTADOS
SIMPLES_2027_COMPARACAO
```

Sugestão de ordem técnica:

```text
...
CENARIOS_TRIBUTARIOS
FISCAL_PARAM
ANALISE_PARAM
FISCAL_RESULTADOS_OPERACAO
FISCAL_APURACAO
COMPARATIVO_CENARIOS
SIMPLES_2027_RESULTADOS
SIMPLES_2027_COMPARACAO
VALIDACOES
PROVENIENCIA
```

`ANALISE_PARAM`:

```text
editável
```

Os dois resultados Simples:

```text
derivados e não editáveis
```

---

# 45. WorkbookInputs

Estender de forma compatível:

```python
@dataclass(frozen=True)
class WorkbookInputs:
    ...
    tax_context: TaxContext | None = None
    tax_analysis_parameters: pd.DataFrame | None = None
```

O default deve ser DataFrame vazio com:

```text
TAX_ANALYSIS_PARAMETER_COLUMNS
```

Não colocar `analysis_parameters` dentro de `TaxContext`.

---

# 46. Dispatch explícito e mínimo no workbook

O workbook atual conhece o relatório CBS 2026.

Adicionar apenas uma seleção explícita entre os dois recortes suportados.

Exemplo conceitual:

```text
se cenários ativos pertencem ao recorte CBS 2026:
    usar run_cbs_2026_counterfactual_report

se cenários ativos pertencem ao recorte Simples 2027:
    usar run_simples_2027_counterfactual_report

senão:
    rejeitar como experimento tributário não suportado
```

Não criar:

```text
plugin registry
TaxEngine abstrato
DSL tributária
reflection
entry points
```

Não generalizar antes da necessidade.

---

# 47. Compatibilidade CBS 2026

O artefato existente:

```text
artifacts/contabilidade_parametrizada.xlsx
```

continua sendo o caso canônico CBS 2026.

Ele deve continuar produzindo os mesmos resultados tributários anteriores.

As novas abas:

```text
ANALISE_PARAM
SIMPLES_2027_RESULTADOS
SIMPLES_2027_COMPARACAO
```

podem ficar vazias nesse artefato.

Não transformar o caso 2026 em Simples 2027.

---

# 48. Novo demo separado

Criar:

```text
scripts/build_simples_2027_demo.py
```

e:

```text
artifacts/demo_simples_2027_puro_vs_hibrido.xlsx
```

Não sobrescrever:

```text
artifacts/contabilidade_parametrizada.xlsx
```

---

# 49. UX da aba RESUMO no demo 2027

Quando o workbook detectar o recorte Simples 2027, `RESUMO` deve mostrar:

```text
Empresa: empresa comercial sintética
Período: janeiro/2027
RBT12: R$ 1.200.000,00
Anexo: I
Baseline: Simples puro
Alternativo: Simples híbrido
```

Operações do período:

```text
aporte
compra
venda B2B
venda B2C
```

Resultado contábil simplificado:

```text
Receita: R$ 100.000,00
CMV: R$ 85.000,00
Resultado: R$ 15.000,00
```

---

# 50. UX da aba COMPARACAO no demo 2027

A comparação humana deve ter dois blocos.

## 50.1 Carga própria

Mostrar:

| Indicador | Simples puro | Simples híbrido | Delta |
|---|---:|---:|---:|
| DAS total | valor | n/a | n/a |
| CBS dentro do DAS | valor | n/a | n/a |
| IBS dentro do DAS | valor | n/a | n/a |
| DAS residual | valor | valor | 0 |
| CBS regular líquida modelada | n/a | valor | n/a |
| IBS regular líquido modelado | n/a | valor | n/a |
| Encargo tributário comparável | valor | valor | delta |

Não representar `n/a` como zero.

## 50.2 Cadeia de créditos

Mostrar:

| Indicador | Puro | Híbrido | Delta |
|---|---:|---:|---:|
| Crédito potencial CBS da empresa | 0 | valor | delta |
| Crédito potencial IBS da empresa | 0 | valor | delta |
| Crédito potencial CBS ao cliente B2B | valor | valor | delta |
| Crédito potencial IBS ao cliente B2B | valor | valor | delta |

---

# 51. Banner obrigatório sobre a CBS

Enquanto `CBS_RATE_SOURCE=analysis`, mostrar de forma destacada:

```text
CBS 2027 — taxa usada nesta simulação: 9,0000%
STATUS: HIPÓTESE ANALÍTICA
A alíquota normativa de 2027 ainda não está cadastrada em FISCAL_PARAM.
```

Mostrar também:

```text
Alíquota de equilíbrio da CBS: aproximadamente 9,0192%
```

com rótulo:

```text
DERIVADO ANALÍTICO
```

---

# 52. Nota metodológica obrigatória

Na aba `COMPARACAO`:

```text
O encargo tributário comparável do cenário híbrido depende de hipóteses
analíticas sobre a taxa da CBS e a realização de créditos. Ele não representa
pagamento financeiro efetivamente ocorrido nem substitui a apuração oficial.
```

E:

```text
A análise não define automaticamente o melhor regime.
```

---

# 53. ENTRADAS

Adicionar `ANALISE_PARAM` à aba guia `ENTRADAS`.

Classificar separadamente:

```text
HIPÓTESES ANALÍTICAS — NÃO NORMATIVAS
```

Nunca agrupá-la com:

```text
FISCAL_PARAM
```

que deve continuar classificada como:

```text
PARÂMETROS NORMATIVOS — ALTA SENSIBILIDADE
```

---

# 54. README

Explicar claramente:

```text
FISCAL_PARAM
=
fonte normativa parametrizada

ANALISE_PARAM
=
hipóteses declaradas para análise de sensibilidade
```

Explicar que:

```text
uma hipótese em ANALISE_PARAM nunca é apresentada como legislação.
```

---

# 55. Proveniência

Adicionar ao workbook:

```text
simples_2027_rule_spec_version
analysis_id
analysis_parameters_present
cbs_rate_source
```

Não copiar parâmetros analíticos para:

```text
tax_normative_versions
```

---

# 56. Output esperado do fixture

Com:

```text
RBT12 = 1.200.000
receita = 100.000
compras elegíveis = 85.000
vendas B2B = 70.000
CBS análise = 9%
IBS regular = 0,1%
alpha = 1
```

esperar:

```text
aliquota efetiva Simples = 8,825%
DAS total = R$ 8.825,00
DAS CBS = R$ 1.352,87
DAS IBS = R$ 15,00
DAS outros = R$ 7.457,13
```

Híbrido:

```text
CBS débito = R$ 9.000,00
CBS crédito potencial = R$ 7.650,00
CBS crédito modelado = R$ 7.650,00
CBS líquido modelado = R$ 1.350,00

IBS débito = R$ 100,00
IBS crédito potencial = R$ 85,00
IBS crédito modelado = R$ 85,00
IBS líquido modelado = R$ 15,00

encargo comparável = R$ 8.822,13
```

Comparação:

```text
encargo puro = R$ 8.825,00
encargo híbrido = R$ 8.822,13
delta = -R$ 2,87
```

Crédito B2B:

```text
Puro:
CBS = R$ 947,01
IBS = R$ 10,50

Híbrido:
CBS = R$ 6.300,00
IBS = R$ 70,00
```

Alíquota de equilíbrio:

```text
0.090191666666...
≈ 9,0192%
```

---

# 57. Interpretação pedagógica esperada

A demonstração deve tornar visualmente claro que, com a hipótese CBS de 9%:

```text
a diferença de encargo próprio modelado é muito pequena
```

mas:

```text
a diferença no crédito potencial entregue à cadeia B2B é grande.
```

Esse contraste é uma conclusão do caso sintético, não uma conclusão universal.

---

# 58. Testes — análise vs norma

Cobrir obrigatoriamente:

1. `ANALISE_PARAM` tem schema exato.
2. `ANALISE_PARAM` não pertence a `TaxContext`.
3. parâmetros analíticos não exigem proveniência normativa.
4. `FISCAL_PARAM` continua exigindo proveniência.
5. `CBS_2027_ANALYSIS_RATE_FRACTION` não é aceita como chave normativa usada pela engine.
6. `CBS_2027_REGULAR_RATE_FRACTION` não é aceita em `ANALISE_PARAM`.
7. taxa analítica é usada somente quando taxa normativa está ausente.
8. taxa normativa válida tem precedência quando presente.
9. source é marcado `analysis`/`normative`.
10. nenhum `0.09` é hard-coded como taxa normativa no source.

---

# 59. Testes — Simples

Cobrir:

1. seleção das faixas 1–5;
2. RBT12 zero rejeitado;
3. RBT12 > 3,6 milhões rejeitado;
4. fórmula de `a_eff`;
5. repartição CBS/IBS;
6. receita pelo faturamento;
7. baseline puro;
8. híbrido;
9. compra de fornecedor não regular rejeitada nesta versão;
10. falta de B2B rejeitada no fixture demonstrativo;
11. falta de B2C rejeitada no fixture demonstrativo;
12. fatos não mutados;
13. nenhum `ID_CENARIO` adicionado aos fatos;
14. determinismo;
15. ordem baseline primeiro;
16. exatamente dois cenários ativos;
17. regime baseline/alternativo correto.

---

# 60. Testes — créditos

Cobrir:

1. puro não apropria créditos próprios: zero;
2. cliente B2B no puro recebe crédito potencial calculado pela parcela efetiva;
3. B2C não entra no crédito de cadeia;
4. híbrido calcula crédito potencial de compra regular;
5. `alpha=1` reproduz todo crédito potencial no modelo;
6. `alpha=0.5` reduz somente crédito modelado, não o crédito potencial;
7. créditos CBS e IBS ficam segregados.

---

# 61. Testes — alíquota de equilíbrio

Cobrir:

```text
r* ≈ 0.090191666666...
```

para o fixture canônico.

Cobrir também:

```text
R - alpha*P <= 0
```

retornando `None`.

---

# 62. Testes — números do demo

Verificar exatamente em centavos:

```text
DAS_TOTAL = 882500
DAS_CBS = 135287
DAS_IBS = 1500
DAS_OUTROS = 745713

CBS_DEBITO_HIBRIDO = 900000
CBS_CREDITO_HIBRIDO = 765000
CBS_LIQUIDO_HIBRIDO = 135000

IBS_DEBITO_HIBRIDO = 10000
IBS_CREDITO_HIBRIDO = 8500
IBS_LIQUIDO_HIBRIDO = 1500

ENCARGO_PURO = 882500
ENCARGO_HIBRIDO = 882213
DELTA = -287

CLIENTE_PURO_CBS = 94701
CLIENTE_PURO_IBS = 1050
CLIENTE_HIBRIDO_CBS = 630000
CLIENTE_HIBRIDO_IBS = 7000
```

---

# 63. Testes — regressão

Todos os testes CBS 2026 devem continuar passando.

Em particular:

```text
tax_cbs_2026.py
tax_counterfactual.py
tax_comparison.py
```

não devem mudar semanticamente.

O workbook CBS 2026 deve continuar gerando:

```text
CBS_2026_BASE
CBS_2026_CONTROLE
```

com os resultados anteriores.

---

# 64. Artefato de demonstração

Gerar:

```text
artifacts/demo_simples_2027_puro_vs_hibrido.xlsx
```

Não substituir o artefato canônico CBS 2026.

O demo deve abrir em:

```text
RESUMO
```

e permitir compreender a decisão sem consultar código.

---

# 65. Script

Criar:

```text
scripts/build_simples_2027_demo.py
```

Ele deve:

1. carregar fixtures Simples 2027;
2. criar plano de contas/mapeamentos já existentes;
3. construir `TaxContext`;
4. carregar `ANALISE_PARAM`;
5. construir `WorkbookInputs`;
6. chamar `build_workbook`;
7. validar o artefato;
8. imprimir resumo.

Não duplicar fórmulas tributárias no script.

---

# 66. Fixtures

Criar:

```text
data/examples/simples_2027/events.csv
data/examples/simples_2027/entity_profile.csv
data/examples/simples_2027/fiscal_event_attributes.csv
data/examples/simples_2027/tax_scenarios.csv
data/examples/simples_2027/tax_parameters.csv
data/examples/simples_2027/analysis_parameters.csv
```

---

# 67. Atualização do roadmap

Atualizar:

```text
specs/README_specs_plan.md
```

incluindo:

| Spec | Questão | Produto |
|---|---|---|
| 12 | Como comparar Simples 2027 puro vs híbrido sem confundir norma com hipótese de sensibilidade? | demonstração profissional com carga própria, créditos de cadeia e limiar CBS |

Não redefinir o Marco D de geração sintética.

A Spec 12 é uma:

```text
extensão tributária substantiva do caminho aberto pelo Marco C
```

e não uma nova camada de infraestrutura genérica.

---

# 68. Arquivos que não devem ser alterados

Não alterar, salvo correção estritamente necessária e justificada:

```text
specs/09_cbs_2026_regular_nfe55.md
specs/10_counterfactual_tax_experiment.md
specs/11_counterfactual_tax_comparison_report.md
src/accounting_sim/tax_cbs_2026.py
src/accounting_sim/tax_counterfactual.py
src/accounting_sim/tax_comparison.py
docs/tax_sources/**
```

Não alterar os documentos 23–30.

---

# 69. Definition of done

A Spec 12 está concluída quando:

1. existem os dois cenários reais puro/híbrido;
2. fatos são idênticos entre eles;
3. DAS puro é calculado pelo Anexo I;
4. CBS/IBS são retirados do DAS no híbrido;
5. IBS regular usa parâmetro normativo;
6. CBS usa taxa analítica explicitamente identificada enquanto a normativa está ausente;
7. FISCAL_PARAM e ANALISE_PARAM são estruturalmente separados;
8. créditos potenciais da empresa e do cliente B2B são exibidos;
9. alíquota de equilíbrio é calculada;
10. nenhum ranking é produzido;
11. workbook 2027 é gerado separadamente;
12. workbook 2026 continua funcionando;
13. todos os testes focados passam;
14. suíte completa passa uma vez ao final;
15. a interface deixa explícito o status normativo/analítico de cada resultado relevante.

---

# 70. Nota de atualização futura

Quando o Senado Federal publicar a alíquota de referência da CBS de 2027:

1. adicionar a nova fonte oficial ao corpus;
2. adicionar em `FISCAL_PARAM`:
   ```text
   CBS_2027_REGULAR_RATE_FRACTION
   ```
   com proveniência completa;
3. não apagar a capacidade analítica;
4. a engine passa automaticamente a preferir a taxa normativa;
5. `CBS_RATE_SOURCE` muda para:
   ```text
   normative
   ```
6. recalcular o demo.

Essa atualização não deve exigir reescrever as fórmulas da Spec 12.

---

# 71. Síntese formal

A Spec 12 implementa:

```text
bar_zeta
+
rho_puro
+
Theta_norm
    ->
Y_puro
```

e:

```text
bar_zeta
+
rho_hibrido
+
Theta_norm
+
theta_analysis
    ->
Y_hibrido_modelado
```

com:

```text
Theta_norm != theta_analysis
```

por construção.

A comparação é:

```text
Delta Y
=
Y_hibrido - Y_puro
```

mas a interpretação permanece vetorial:

```text
carga própria
crédito da empresa
crédito da cadeia
```

sem função de utilidade implícita.

Essa separação é condição necessária para que o workbook seja, ao mesmo tempo:

```text
didático
profissional
auditável
juridicamente honesto sobre suas hipóteses
```
