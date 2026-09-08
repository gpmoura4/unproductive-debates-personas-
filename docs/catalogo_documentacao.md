# Catálogo da documentação — base para o artigo final

Inventário recursivo do repositório, gerado em 08/09/2026. Classifica cada
arquivo por eixo temático e indica se deve ser copiado para
`docs/artigo_base/`.

**Totais do repositório** (excluindo `.git/`, `.venv/`, `__pycache__/`):

| Categoria | Arquivos |
|---|---|
| Total | 947 |
| Dados gerados por execução (`experiments/`, `analysis/`) | 768 |
| Documentação (`.md`, `.txt`, `.docx`, `.pdf`) | 70 |
| Código (`.py`) | 50 |
| Dados brutos (Parquet) | 2 (2,0 GB) |
| Figuras (`.png`) | 55 |

---

## EIXO 1 — PLANO E DESENHO EXPERIMENTAL

### Plano_Monografia_CSCW_v6.docx
- **Caminho original:** `docs/support materials/papers/Plano_Monografia_CSCW_v6.docx`
- **Formato:** .docx
- **Status:** VIGENTE
- **Descrição:** Plano de monografia com desenho experimental, cronograma e
  metodologia. Versão corrente, atualizada com as decisões da Seção 9.1 de
  `estado_atual_do_trabalho.md`.
- **Copiar:** SIM
- **Nota:** há edições pendentes registradas em `docs/pending_docx_edits.md`
  (7 edições) que ainda não foram aplicadas ao arquivo.

### Plano_Monografia_CSCW_v5.docx
- **Caminho original:** `docs/support materials/papers/Plano_Monografia_CSCW_v5.docx`
- **Formato:** .docx
- **Status:** SUPERADO por `Plano_Monografia_CSCW_v6.docx`
- **Descrição:** Versão anterior do plano, preservada como histórico.
- **Copiar:** NÃO — versão superada; mantida no original para rastreabilidade.

### estado_atual_do_trabalho.md
- **Caminho original:** `docs/deliverables/estado_atual_do_trabalho.md`
- **Formato:** .md
- **Última modificação:** 2026-09-08
- **Status:** VIGENTE — **com ressalva**
- **Descrição:** Documento-base do trabalho: contexto, pergunta de pesquisa,
  fundamentação, dataset, pipeline, decisões centrais, limitações e trabalhos
  futuros. É o documento mais completo do repositório.
- **Copiar:** SIM
- **Ressalva:** as Seções 7 ("o que já está produzido") e 8 ("próximos passos")
  descrevem como pendente o experimento que já foi executado. Atualizar antes
  de usar como fonte para o método.

### EXECUTION_GUIDE.md
- **Caminho original:** `docs/EXECUTION_GUIDE.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Guia de execução das Fases 4–6 do pipeline.
- **Copiar:** SIM

### LOCAL_RUN_GUIDE.md
- **Caminho original:** `debate_simulation/docs/LOCAL_RUN_GUIDE.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Guia por fases da execução local com Ollama.
- **Copiar:** SIM

### README.md (raiz)
- **Caminho original:** `README.md`
- **Formato:** .md
- **Última modificação:** 2026-08-26
- **Status:** AVALIAR — pode estar desatualizado (anterior à execução)
- **Descrição:** Visão geral do repositório e dos dois subprojetos.
- **Copiar:** SIM

### README.md (dataset_analysis)
- **Caminho original:** `dataset_analysis/README.md`
- **Formato:** .md
- **Última modificação:** 2026-08-26
- **Status:** AVALIAR — anterior à execução
- **Descrição:** Documentação do subprojeto de análise do dataset (Fases 0–2).
- **Copiar:** SIM

### README.md (debate_simulation)
- **Caminho original:** `debate_simulation/README.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Documentação do subprojeto de simulação (Fases 3–6).
- **Copiar:** SIM

---

## EIXO 2 — FUNDAMENTAÇÃO TEÓRICA

### fundamentacao_escala_hostilidade.md
- **Caminho original:** `docs/deliverables/fundamentacao_escala_hostilidade.md`
- **Formato:** .md
- **Última modificação:** 2026-09-08
- **Status:** VIGENTE
- **Descrição:** Fundamentação da escala ordinal de hostilidade 0–4: revisão de
  sete abordagens da literatura, ancoragem nível a nível, justificativa do
  limiar ≥ 2, as três patologias de Angenot e seis limitações.
- **Copiar:** SIM

### regras_categorizacao_esquerda_direita.md
- **Caminho original:** `dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Regra de classificação política e sua fundamentação teórica
  (Bobbio, Jost et al., Piurko et al., Feldman & Johnston). Inclui âncora,
  indicadores nucleares/periféricos e critérios de inclusão.
- **Copiar:** SIM — classificado aqui pela carga de fundamentação; o produto
  operacional (`.json`) vai para o Eixo 3.

### regras_categorizacao_esquerda_direita (1).md
- **Caminho original:** `dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita (1).md`
- **Formato:** .md
- **Status:** DUPLICATA EXATA de `regras_categorizacao_esquerda_direita.md`
- **Descrição:** Cópia byte a byte (15.406 bytes, `diff` sem diferenças),
  provavelmente resultado de download duplicado.
- **Copiar:** NÃO — duplicata verificada.

### Unproductive_Debates___CHIRA_2026.pdf
- **Caminho original:** `docs/support materials/papers/Unproductive_Debates___CHIRA_2026.pdf`
- **Formato:** .pdf (859 KB)
- **Status:** VIGENTE
- **Descrição:** Paper anterior (Moura e Brandi, 2026) que originou o modelo
  sociotécnico e a dimensão D5. É a base conceitual do trabalho atual.
- **Copiar:** SIM — ver também Eixo 10.

---

## EIXO 3 — PERSONAS E DATASET

### phase0_schema_report.md
- **Caminho original:** `dataset_analysis/outputs/phase0_schema_report.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Relatório da Fase 0 — inspeção do schema do MatrAIx Persona 1M
  e identificação das dimensões políticas.
- **Copiar:** SIM

### phase0_political_dimensions.json
- **Caminho original:** `dataset_analysis/outputs/phase0_political_dimensions.json` (96 KB)
- **Formato:** .json
- **Status:** VIGENTE
- **Descrição:** Dimensões políticas extraídas do schema, com índices e
  vocabulários por dimensão.
- **Copiar:** SIM

### phase1_parquet_report.md
- **Caminho original:** `dataset_analysis/outputs/phase1_parquet_report.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Relatório da Fase 1 — exploração dos shards Parquet e
  identificação das personas candidatas.
- **Copiar:** SIM

### phase1_parquet_schema_raw.txt
- **Caminho original:** `dataset_analysis/outputs/phase1_parquet_schema_raw.txt`
- **Formato:** .txt
- **Status:** VIGENTE
- **Descrição:** Dump bruto do schema Parquet, evidência de apoio à Fase 1.
- **Copiar:** SIM

### phase1_candidate_personas.json
- **Caminho original:** `dataset_analysis/outputs/phase1_candidate_personas.json` (4 KB)
- **Formato:** .json
- **Status:** VIGENTE
- **Descrição:** Personas candidatas após o filtro inicial.
- **Copiar:** SIM

### phase2_decode_report.md
- **Caminho original:** `dataset_analysis/outputs/phase2_decode_report.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Relatório da Fase 2 — decodificação do BLOB de 645 bytes
  (convenção nibble low-first e null_bitmap).
- **Copiar:** SIM

### phase2_decode_validation.md
- **Caminho original:** `dataset_analysis/outputs/phase2_decode_validation.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Validação empírica da convenção de decodificação contra o campo
  `descriptions`. Evidência central para a defensabilidade da pipeline.
- **Copiar:** SIM

### phase2_polarization_rule_review.md
- **Caminho original:** `dataset_analysis/outputs/phase2_polarization_rule_review.md`
- **Formato:** .md
- **Status:** VIGENTE
- **Descrição:** Validação da regra de classificação política em exemplos de
  trabalho conferidos manualmente.
- **Copiar:** SIM

### phase2_decoded_personas.json
- **Caminho original:** `dataset_analysis/outputs/phase2_decoded_personas.json` (44 KB)
- **Formato:** .json
- **Status:** VIGENTE
- **Descrição:** Personas decodificadas com atributos legíveis — insumo direto
  da geração de prompts.
- **Copiar:** SIM

### regras_categorizacao_esquerda_direita.json
- **Caminho original:** `dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.json` (8 KB)
- **Formato:** .json
- **Status:** VIGENTE
- **Descrição:** Versão operacional (legível por máquina) da regra de
  classificação política.
- **Copiar:** SIM

### persona_metadata.json
- **Caminho original:** `debate_simulation/outputs/prompts/personas/persona_metadata.json` (8 KB)
- **Formato:** .json
- **Status:** VIGENTE
- **Descrição:** Metadados das 20 personas selecionadas (10 por polo): id
  MatrAIx, polo, atributos cegados, versão do prompt.
- **Copiar:** SIM

### persona_00.txt … persona_09.txt (polo_esquerda e polo_direita)
- **Caminho original:** `debate_simulation/outputs/prompts/personas/polo_{esquerda,direita}/`
- **Formato:** .txt (20 arquivos)
- **Status:** VIGENTE
- **Descrição:** Prompts de persona prontos (Camada 1 — identidade), 10 por
  polo. Produto final da pipeline de seleção.
- **Copiar:** SIM — todos os 20, preservando a separação por polo.

### persona-1m-0000.parquet / persona-1m-0001.parquet
- **Caminho original:** `dataset_analysis/data/persona-1m/` (2,0 GB no total)
- **Formato:** .parquet
- **Status:** VIGENTE — dado bruto
- **Descrição:** Dois shards do MatrAIx Persona 1M. Fonte primária de todas as
  personas.
- **Copiar:** NÃO — dado bruto grande (regra 7). Registrado aqui pelo caminho.

---

## EIXO 4 — PROMPTS (INSTRUMENTOS)

### debate behavior.txt
- **Caminho original:** `debate_simulation/prompts/debate behavior/debate behavior.txt`
- **Formato:** .txt
- **Status:** VIGENTE
- **Descrição:** Camada 2 — prompt de comportamento de debate, com as regras de
  escalada e o mapeamento para as patologias de Angenot.
- **Copiar:** SIM

### debate moderator D5.txt
- **Caminho original:** `debate_simulation/prompts/debate moderator D5/debate moderator D5.txt`
- **Formato:** .txt
- **Status:** VIGENTE
- **Descrição:** Prompt do moderador D5: escala de hostilidade 0–4, tabela de
  decisão mecânica, limiar ≥ 2, regras de reformulação e exemplos.
- **Copiar:** SIM

### debate judge.txt
- **Caminho original:** `debate_simulation/prompts/debate judge/debate judge.txt`
- **Formato:** .txt
- **Status:** VIGENTE
- **Descrição:** Prompt do Juiz C: pontuação cega das mensagens publicadas na
  mesma escala 0–4, três execuções por mensagem.
- **Copiar:** SIM
- **Nota:** alguns documentos e prompts anteriores referem-se a este arquivo
  como `judge_c.txt` — o nome real é `debate judge.txt`.

### prompt_geracao_slides.md
- **Caminho original:** `docs/deliverables/prompt_geracao_slides.md`
- **Formato:** .md
- **Última modificação:** 2026-09-03
- **Status:** VIGENTE
- **Descrição:** Prompt para geração da apresentação de resultados
  preliminares, com a lista de arquivos-fonte necessários.
- **Copiar:** SIM — instrumento de produção, não do experimento.

---

## EIXO 5 — REGRAS E DECISÕES METODOLÓGICAS

### moderator_design_decisions.md
- **Caminho original:** `debate_simulation/docs/moderator_design_decisions.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Decisões de projeto do moderador D5, incluindo as falhas
  encontradas no piloto (limiar, inversão de posição, aspas não escapadas,
  reformulação que não modera) e as correções aplicadas.
- **Copiar:** SIM

### debate_behavior_design_decisions.md
- **Caminho original:** `debate_simulation/docs/debate_behavior_design_decisions.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Decisões sobre o comportamento dos debatedores, incluindo a
  calibragem da escalada até o nível 4 e o guardrail identitário.
- **Copiar:** SIM

### persona_prompt_design_decisions.md
- **Caminho original:** `debate_simulation/docs/persona_prompt_design_decisions.md`
- **Formato:** .md
- **Última modificação:** 2026-08-29
- **Status:** VIGENTE
- **Descrição:** Decisões de construção dos prompts de persona: arquitetura de
  duas camadas, campos deliberadamente excluídos, blinding de `political_lean`.
- **Copiar:** SIM

### local_models_decision.md
- **Caminho original:** `debate_simulation/docs/local_models_decision.md`
- **Formato:** .md
- **Última modificação:** 2026-09-01
- **Status:** VIGENTE
- **Descrição:** Decisão de migrar para modelos locais. Documenta as três
  falhas do free tier da OpenRouter e o viés de disponibilidade que
  introduziam (controle passava, tratamento falhava).
- **Copiar:** SIM

### pending_docx_edits.md
- **Caminho original:** `docs/pending_docx_edits.md`
- **Formato:** .md
- **Última modificação:** 2026-09-08
- **Status:** VIGENTE — ação pendente
- **Descrição:** Sete edições especificadas para o plano v6 (`.docx` não
  editado diretamente): compliance total, limitações, trabalhos futuros e
  bibliografia.
- **Copiar:** SIM

### PENDENCIAS_REVISAO.md
- **Caminho original:** `docs/PENDENCIAS_REVISAO.md`
- **Formato:** .md
- **Última modificação:** 2026-09-08
- **Status:** VIGENTE — ação pendente
- **Descrição:** Metadados bibliográficos a conferir no PDF original antes da
  submissão, percentuais de Katsaros et al. a validar, e itens de consistência
  interna.
- **Copiar:** SIM

### models.yaml
- **Caminho original:** `debate_simulation/config/models.yaml` (8 KB)
- **Formato:** .yaml
- **Status:** VIGENTE
- **Descrição:** Perfis de modelo (local, api_only, smoke_test) com provedor,
  temperatura e limites por papel. Documenta a configuração exata do
  experimento.
- **Copiar:** SIM

---

## EIXO 6 — LIMITAÇÕES E TRABALHOS FUTUROS

### metrics_pending.md
- **Caminho original:** `debate_simulation/docs/metrics_pending.md`
- **Formato:** .md
- **Última modificação:** 2026-09-02
- **Status:** VIGENTE
- **Descrição:** Métricas não calculadas, com o motivo e o custo estimado de
  cada uma: preservação verificada, reformulação efetiva, inter-juiz, auditoria
  humana e separação entre efeito direto e desescalada indireta.
- **Copiar:** SIM

**Nota:** as limitações e os trabalhos futuros do trabalho estão nas Seções 10
e 11 de `estado_atual_do_trabalho.md` (Eixo 1) e na Seção 6 de
`fundamentacao_escala_hostilidade.md` (Eixo 2). Não existem como arquivos
próprios — ver LACUNAS.

---

## EIXO 7 — REFERÊNCIAS BIBLIOGRÁFICAS

### referencias.md
- **Caminho original:** `docs/deliverables/referencias.md`
- **Formato:** .md
- **Última modificação:** 2026-09-08
- **Status:** VIGENTE
- **Descrição:** 22 referências em ABNT, agrupadas em 7 eixos temáticos, com
  lista consolidada em ordem alfabética e tabela de metadados pendentes (⚠).
- **Copiar:** SIM

**Nota:** não existe arquivo `.bib` no repositório — ver LACUNAS.

---

## EIXO 8 — IMPLEMENTAÇÃO (CÓDIGO RELEVANTE)

Critério aplicado (regra 6): copiar apenas o que implementa lógica descrita no
artigo. Infraestrutura genérica é listada mas não copiada.

### 00_generate_persona_prompts.py
- **Caminho original:** `debate_simulation/scripts/00_generate_persona_prompts.py`
- **Status:** VIGENTE
- **Descrição:** Gera os prompts de persona (Camada 1) a partir das personas
  decodificadas, aplicando o blinding de atributos.
- **Copiar:** SIM

### 03_decode_attributes.py
- **Caminho original:** `dataset_analysis/scripts/03_decode_attributes.py`
- **Status:** VIGENTE
- **Descrição:** Decodifica o BLOB de atributos do MatrAIx e aplica a regra de
  classificação esquerda/direita. Lógica central da Fase 2.
- **Copiar:** SIM

### 02_explore_parquet.py
- **Caminho original:** `dataset_analysis/scripts/02_explore_parquet.py`
- **Status:** VIGENTE
- **Descrição:** Exploração dos shards e seleção das personas candidatas.
- **Copiar:** SIM

### 01_inspect_schema.py / 00_download_schema.py
- **Caminho original:** `dataset_analysis/scripts/`
- **Status:** VIGENTE
- **Descrição:** Download e inspeção do schema do dataset (Fase 0).
- **Copiar:** SIM — descrevem a etapa de descoberta do schema, citada no método.

### run_debate.py
- **Caminho original:** `debate_simulation/scripts/run_debate.py`
- **Status:** VIGENTE
- **Descrição:** Runner CLI do experimento: monta o loop de debate, aplica a
  condição (controle/tratamento) e dispara o juiz.
- **Copiar:** SIM

### compute_metrics.py
- **Caminho original:** `debate_simulation/scripts/compute_metrics.py`
- **Status:** VIGENTE
- **Descrição:** Calcula todas as métricas, tabelas e figuras a partir do
  corpus selecionado.
- **Copiar:** SIM

### src/debate/loop.py
- **Caminho original:** `debate_simulation/src/debate/loop.py`
- **Status:** VIGENTE
- **Descrição:** Loop de debate: alterna personas, aplica a moderação no
  tratamento, grava o transcript. Implementa a distinção candidato ×
  publicado.
- **Copiar:** SIM

### src/moderator/ (moderator.py, schema.py, prompt.py, logger.py)
- **Caminho original:** `debate_simulation/src/moderator/`
- **Status:** VIGENTE
- **Descrição:** Implementação do D5: avaliação do candidato, decisão de
  intervenção, reformulação e registro. `moderator.py` contém a lógica de
  `consistency_warning` (decisões fora do limiar).
- **Copiar:** SIM (4 arquivos)

### src/judge/ (judge.py, schema.py, prompt.py, logger.py)
- **Caminho original:** `debate_simulation/src/judge/`
- **Status:** VIGENTE
- **Descrição:** Implementação do Juiz C: pontuação 3× por mensagem, mediana e
  registro de consistência intra-juiz.
- **Copiar:** SIM (4 arquivos)

### src/debater/ (debater.py, prompt.py)
- **Caminho original:** `debate_simulation/src/debater/`
- **Status:** VIGENTE
- **Descrição:** Composição das Camadas 1 e 2 e geração da mensagem candidata,
  incluindo a nota de escalada por turno.
- **Copiar:** SIM (2 arquivos)

### src/analysis/ (selection.py, metrics.py, report.py, layout.py, showcase.py)
- **Caminho original:** `debate_simulation/src/analysis/`
- **Status:** VIGENTE
- **Descrição:** Camada de análise: critérios de seleção do corpus,
  balanceamento, cálculo das métricas, geração de tabelas/figuras e do exemplo
  trabalhado.
- **Copiar:** SIM (5 arquivos) — `selection.py` documenta os critérios de
  exclusão, que precisam ser descritos no método.

### Código NÃO copiado (infraestrutura)
- `src/llm/client.py`, `src/llm/parsing.py` — cliente HTTP e cascata de
  parsing JSON. Infraestrutura.
- `src/config/loader.py` — carregamento de perfis. Infraestrutura.
- `scripts/show_results.py`, `show_selection.py`, `build_analysis.py`,
  `build_showcase.py`, `smoke_test.py` — ferramentas de inspeção e execução.
- `scripts/run_batch.sh` — orquestração de lote.
- `tests/` (12 arquivos) — 248 testes offline. Relevantes para reprodutibilidade,
  não para o texto do artigo.
- `pyproject.toml`, `uv.lock`, `.gitignore` — configuração de ambiente.
- Todos os `__init__.py`.

---

## EIXO 9 — RESULTADOS E DADOS

### report.md (metrics_balanced)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_balanced/report.md`
- **Status:** VIGENTE — **análise principal**
- **Descrição:** Relatório do corpus balanceado (10 células, 20 debates):
  resultado principal (Δ = −1,19), quatro tabelas com legenda e quatro
  ressalvas metodológicas.
- **Copiar:** SIM

### metrics.json (metrics_balanced)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_balanced/metrics.json`
- **Status:** VIGENTE
- **Descrição:** Todos os números da análise principal em formato estruturado.
- **Copiar:** SIM

### report.md (metrics_full)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_full/report.md`
- **Status:** VIGENTE — verificação de robustez
- **Descrição:** Mesmos cálculos sobre o corpus completo (21 réplicas, 42
  debates). Δ = −1,12, com 21/21 células na mesma direção.
- **Copiar:** SIM

### tables/*.md e *.csv (ambos os corpora)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_{balanced,full}/tables/`
- **Status:** VIGENTE
- **Descrição:** Quatro tabelas com legenda pronta (efeito principal,
  acionamento do D5, consistência do juiz, efeito por célula) mais o export
  `per_turn.csv` em formato longo.
- **Copiar:** SIM — ambos os conjuntos.

### figures/*.png e *.txt (ambos os corpora)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_{balanced,full}/figures/`
- **Status:** VIGENTE
- **Descrição:** Quatro figuras a 300 dpi com legendas em arquivo separado:
  efeito principal, trajetória por turno, distribuição das notas e Δ por
  célula.
- **Copiar:** SIM — ambos os conjuntos.

### examples/ (exemplo.md + 10 PNG)
- **Caminho original:** `debate_simulation/analysis/runs/metrics_balanced/examples/`
- **Status:** VIGENTE
- **Descrição:** Exemplo trabalhado de um debate (Drug Legalization, pair-03):
  10 páginas 16:9 e a versão em tabela. Inclui o par candidato × reformulação.
- **Copiar:** SIM

### amostra_auditoria.csv
- **Caminho original:** `debate_simulation/analysis/runs/metrics_balanced/amostra_auditoria.csv`
- **Status:** VIGENTE — insumo pendente de anotação
- **Descrição:** 30 pares candidato/reformulação sorteados com semente fixa,
  com colunas para anotação humana.
- **Copiar:** SIM

### selection.json
- **Caminho original:** `debate_simulation/analysis/runs/current/selection.json`
- **Status:** VIGENTE
- **Descrição:** Registro auditável do corpus **completo** (11 células, 21
  réplicas, 42 debates): cohort de prompts, cada réplica incluída com os dois
  `experiment_id`, e cada uma das 18 exclusões com o motivo.
- **Copiar:** SIM
- **Nota:** existe apenas em `runs/current/`, gerado por `build_analysis.py`.
  Os diretórios `metrics_balanced/` e `metrics_full/` são produzidos por
  `compute_metrics.py`, que não escreve esse arquivo — o recorte balanceado
  não tem `selection.json` próprio. Para gerá-lo:
  `build_analysis.py --balanced --name <nome>`.

### experiments/ (60 diretórios, ~768 arquivos)
- **Caminho original:** `debate_simulation/experiments/`
- **Status:** VIGENTE — dado bruto de execução
- **Descrição:** Log append-only de toda execução: `manifest.json`,
  `transcript.json`, `moderation/` e `judgements/` por debate. É a evidência
  primária dos resultados.
- **Copiar:** NÃO — volume incompatível com a pasta de trabalho (768 arquivos).
  Está versionado no git e permanece acessível pelo caminho original. A
  agregação relevante já está em `analysis/runs/`.

### batch_*.log
- **Caminho original:** `debate_simulation/experiments/batch_*.log` (4 arquivos)
- **Status:** VIGENTE
- **Descrição:** Logs de console das execuções em lote, incluindo os tempos por
  célula e o timeout do moderador que truncou uma célula.
- **Copiar:** NÃO — diagnóstico de execução, não conteúdo do artigo.

---

## EIXO 10 — PRODUÇÃO ACADÊMICA PARALELA

### Unproductive_Debates___CHIRA_2026.pdf
- **Caminho original:** `docs/support materials/papers/Unproductive_Debates___CHIRA_2026.pdf`
- **Formato:** .pdf (859 KB)
- **Status:** VIGENTE
- **Descrição:** Paper anterior (Moura e Brandi, 2026) — o modelo sociotécnico
  de onde vem a dimensão D5.
- **Copiar:** SIM — cópia única no Eixo 2 (fundamentação); referenciado aqui.

### prompt slide support docs/ (37 arquivos)
- **Caminho original:** `docs/prompt slide support docs/`
- **Status:** VIGENTE — pasta derivada
- **Descrição:** Pasta montada para a geração dos slides: cópias de 18
  documentos + 14 figuras + o prompt.
- **Copiar:** NÃO — é ela própria uma coleção de cópias; duplicá-la criaria uma
  terceira camada. Permanece disponível no caminho original.

---

## DOCUMENTOS NÃO RELEVANTES

| Arquivo | Justificativa |
|---|---|
| `.DS_Store` (5 arquivos) | Metadado do Finder |
| `.env` | Credenciais — **não copiar em nenhuma hipótese** |
| `.gitignore` (4 arquivos) | Configuração de versionamento |
| `.gitkeep` (6 arquivos) | Marcadores de diretório vazio |
| `debate_simulation/.pytest_cache/` | Cache de testes, regenerável |
| `uv.lock` (5 arquivos) | Lockfile de dependências |
| `*.metadata`, `*.TAG` (6 arquivos) | Metadados de download do dataset |
| `regras_categorizacao_esquerda_direita (1).md` | Duplicata exata verificada |
| `Plano_Monografia_CSCW_v5.docx` | Superado pela v6 |

---

## LACUNAS IDENTIFICADAS

Documentos que deveriam existir, dado o que os arquivos existentes referenciam
ou o estágio do trabalho:

1. **Arquivo `.bib`** — não existe. As referências estão apenas em Markdown
   (`referencias.md`). Para submissão em LaTeX será necessário converter.

2. **Rascunho do artigo final** — não existe nenhum arquivo `.tex`, `.docx` ou
   `.md` que seja o texto do artigo em produção. Esta pasta é a base para
   iniciá-lo.

3. **Documento consolidado de limitações e trabalhos futuros** — existem
   apenas como seções dentro de outros documentos (Seções 10 e 11 de
   `estado_atual_do_trabalho.md`; Seção 6 de
   `fundamentacao_escala_hostilidade.md`; `metrics_pending.md`). Para o artigo,
   convém consolidá-las.

4. **Atualização das Seções 7 e 8 de `estado_atual_do_trabalho.md`** — descrevem
   como pendente o experimento já executado. É a lacuna mais urgente: o
   documento-base do trabalho está desatualizado quanto ao seu próprio estado.

5. **Codebook de anotação humana** — previsto no protocolo de validação da
   escala (trabalho futuro), ainda não produzido.

6. **Resultado da auditoria humana** — `amostra_auditoria.csv` está gerado mas
   as colunas de anotação seguem vazias.

7. **Edições pendentes no plano v6** — as 7 edições de `pending_docx_edits.md`
   não foram aplicadas ao `.docx`. O plano vigente está defasado em relação aos
   documentos Markdown.

8. **Métricas pendentes** — preservação argumentativa verificada, reformulação
   efetiva e consistência inter-juiz não foram calculadas (ver
   `metrics_pending.md` para o custo de cada uma).

---

## PROBLEMAS ENCONTRADOS

| Problema | Detalhe |
|---|---|
| Duplicata exata | `regras_categorizacao_esquerda_direita (1).md` é cópia byte a byte do original |
| Nome de arquivo divergente | Documentos referem-se ao prompt do juiz como `judge_c.txt`; o arquivo real é `debate judge/debate judge.txt` |
| Documento-base defasado | Seções 7 e 8 de `estado_atual_do_trabalho.md` descrevem o experimento como pendente |
| Espaço no caminho raiz | O diretório do projeto termina em espaço, o que quebra comandos de shell sem aspas |
| Credencial na raiz | `.env` presente, mas corretamente coberto pelo `.gitignore` (linha 38) e nunca commitado — verificado, sem ação necessária |

Nenhum problema de encoding foi encontrado: todos os arquivos `.md` e `.txt`
estão em UTF-8 com acentuação íntegra.
