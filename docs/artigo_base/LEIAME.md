# Base documental para produção do artigo

Pasta criada em **08/09/2026** por inventário automatizado do repositório.
Contém **CÓPIAS** organizadas por eixo temático. Todos os originais permanecem
intactos nos caminhos listados em [`CATALOGO.md`](CATALOGO.md).

**130 arquivos, 6,4 MB.** O catálogo anotado descreve cada um, com status
(vigente / superado / avaliar) e justificativa das exclusões.

---

## Índice rápido

| Eixo | Pasta | Qtd. | Descrição |
|---|---|---:|---|
| 1 | `01_plano_e_desenho/` | 7 | Plano v6, documento-base do trabalho, guias de execução, READMEs |
| 2 | `02_fundamentacao_teorica/` | 3 | Escala de hostilidade, regra de classificação política, paper CHIRA 2026 |
| 3 | `03_personas_e_dataset/` | 31 | Relatórios das Fases 0–2, personas decodificadas, 20 prompts de persona |
| 4 | `04_prompts_instrumentos/` | 4 | Prompts do D5, do juiz, de comportamento, e o de geração de slides |
| 5 | `05_regras_e_decisoes/` | 7 | Decisões de projeto, pendências de revisão, configuração de modelos |
| 6 | `06_limitacoes_e_trabalhos_futuros/` | 1 | Métricas pendentes com custo estimado |
| 7 | `07_referencias/` | 1 | 22 referências em ABNT, agrupadas e consolidadas |
| 8 | `08_implementacao/` | 23 | Scripts da pipeline e módulos que implementam D5, juiz, debatedor e análise |
| 9 | `09_resultados_e_dados/` | 51 | Relatórios, tabelas, figuras e exemplo trabalhado, nos dois corpora |
| 10 | `10_producao_paralela/` | 1 | Ponteiro — o paper CHIRA está no Eixo 2 |

---

## Por onde começar

**Para o método:** `01_plano_e_desenho/estado_atual_do_trabalho.md` é o
documento mais completo do repositório — mas suas Seções 7 e 8 estão
desatualizadas (descrevem como pendente o experimento já executado).

**Para os resultados:** `09_resultados_e_dados/balanced/report.md` traz o
resultado principal e as quatro ressalvas metodológicas. O corpus balanceado
(10 células, 20 debates) é a análise principal; `full/` é a verificação de
robustez (21 réplicas, 42 debates). As duas concordam.

**Para a fundamentação:** `02_fundamentacao_teorica/` tem os dois documentos
que ancoram as decisões teóricas — a escala de hostilidade e a regra de
classificação política —, cada um com sua própria seção de referências.

**Para as figuras:** `09_resultados_e_dados/balanced/figures/` (4 PNG a 300 dpi
com legendas em `.txt`) e `balanced/examples/` (10 páginas 16:9 do exemplo
trabalhado).

---

## O que NÃO está aqui

| Item | Onde está | Por quê |
|---|---|---|
| `experiments/` (768 arquivos) | `debate_simulation/experiments/` | Volume incompatível com pasta de trabalho; versionado no git; a agregação está no Eixo 9 |
| Shards Parquet (2,0 GB) | `dataset_analysis/data/persona-1m/` | Dado bruto grande |
| Plano v5 | `docs/support materials/papers/` | Superado pela v6 |
| Testes (12 arquivos) | `debate_simulation/tests/` | Relevantes para reprodutibilidade, não para o texto |
| Código de infraestrutura | `debate_simulation/src/llm/`, `src/config/` | Cliente HTTP, parsing, carregamento de perfis |
| `prompt slide support docs/` | `docs/` | Já é uma coleção de cópias |

---

## Lacunas a resolver antes de escrever

Extraídas do catálogo, em ordem de urgência:

1. **Seções 7 e 8 de `estado_atual_do_trabalho.md` estão defasadas** —
   descrevem como pendente o experimento já executado. É o documento-base do
   trabalho descrevendo mal o próprio estado.
2. **Não existe arquivo `.bib`** — as referências só existem em Markdown. Para
   submissão em LaTeX, será necessário converter.
3. **Não existe rascunho do artigo** — nenhum `.tex`, `.docx` ou `.md` em
   produção. Esta pasta é a base para começar.
4. **Limitações dispersas em três arquivos** — Seções 10 e 11 de
   `estado_atual_do_trabalho.md`, Seção 6 de
   `fundamentacao_escala_hostilidade.md`, e `metrics_pending.md`. Convém
   consolidar.
5. **7 edições pendentes no plano v6** — ver
   `05_regras_e_decisoes/pending_docx_edits.md`. O `.docx` está defasado em
   relação aos documentos Markdown.
6. **3 métricas não calculadas** — preservação verificada, reformulação
   efetiva e consistência inter-juiz. Custos em
   `06_limitacoes_e_trabalhos_futuros/metrics_pending.md`.
7. **Auditoria humana não preenchida** —
   `09_resultados_e_dados/balanced/amostra_auditoria.csv` tem os 30 pares
   sorteados, mas as colunas de anotação seguem vazias.
8. **Codebook de anotação não produzido** — previsto no protocolo de validação
   da escala.

---

## Como regenerar esta pasta

As cópias refletem o repositório em 08/09/2026. Se os originais mudarem, a
pasta fica defasada — ela não se atualiza sozinha. O catálogo
([`CATALOGO.md`](CATALOGO.md)) registra o caminho original de cada arquivo,
o que permite refazer a cópia seletivamente.

Os resultados do Eixo 9 são derivados e regeneráveis a partir de
`debate_simulation/`:

```
uv run python scripts/compute_metrics.py            # corpus balanceado
uv run python scripts/compute_metrics.py --full     # corpus completo
uv run python scripts/build_showcase.py             # exemplo trabalhado
```
