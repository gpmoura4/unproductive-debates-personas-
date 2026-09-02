# Guia de execução — pipeline completo

Este guia orienta a execução, do zero, de todas as fases do pipeline: da
inspeção do dataset MatrAIx Persona 1M até a execução do experimento
(debate → moderação → juiz) e a leitura dos resultados. Cobre os dois
subprojetos independentes (`dataset_analysis/` e `debate_simulation/`), na
ordem correta.

**Se você só quer rodar o experimento** (Fases 0-3 já executadas, prompts de
persona já em `debate_simulation/outputs/prompts/personas/`), vá direto para
[Rodada piloto — passo a passo completo](#rodada-piloto--passo-a-passo-completo).

Para detalhes específicos de cada subprojeto, ver também
[`dataset_analysis/README.md`](../dataset_analysis/README.md) e
[`debate_simulation/README.md`](../debate_simulation/README.md).

---

## Visão geral do pipeline

```
dataset_analysis/                              debate_simulation/
─────────────────                              ──────────────────
Fase 0 — schema + dimensões políticas
   │
   ▼
Fase 1 — download de shards Parquet
   │
   ▼
Fase 2 — decodificação + classificação
         de polos (esquerda/direita)   ───►    Fase 3 — geração de prompts
   │                                            de debate (Layer 1)
   ▼                                                  │
outputs/phase2_decoded_personas.json                  ▼
                                        outputs/prompts/personas/
                                          ├── persona_metadata.json
                                          ├── polo_esquerda/persona_NN.txt
                                          └── polo_direita/persona_NN.txt
                                                      │
                                                      ▼
                                        Fase 4 — debate (Layer 1 + Layer 2)
                                                      │  candidata
                                                      ▼
                                        Fase 5 — moderação D5
                                                      │  texto publicado
                                                      ▼
                                        Fase 6 — juiz de hostilidade
                                                      │
                                                      ▼
                                        experiments/{experiment_id}/
                                          ├── manifest.json
                                          ├── transcript.json
                                          ├── moderation/
                                          └── judgements/
```

**Fases 0-3** são offline: inspeção de dados e geração de texto por template,
sem custo. **Fases 4-6** chamam modelos de LLM e produzem dado experimental.

Cada subprojeto tem seu próprio `pyproject.toml`/`.venv`, gerenciado via
[`uv`](https://docs.astral.sh/uv/). Eles nunca compartilham ambiente virtual;
`debate_simulation/` apenas lê um arquivo JSON gerado por `dataset_analysis/`.

---

## Pré-requisitos

- Python 3.11+
- `uv` instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- (Somente se o dataset HuggingFace estiver gated) uma conta autenticada via
  `uv run huggingface-cli login`

---

## Parte 1 — `dataset_analysis/` (Fases 0-2)

Todos os comandos abaixo assumem que o diretório de trabalho é
`dataset_analysis/`.

```bash
cd dataset_analysis
uv sync
```

### Fase 0 — Schema e dimensões politicamente relevantes

```bash
# Passo 1: baixar os arquivos de schema do dataset (não baixa os Parquet)
uv run python scripts/00_download_schema.py
# → gera: data/schema/dimensions.json
# → gera: data/schema/persona_codes.schema.json

# Passo 2: identificar, por term-match, quais das 1290 dimensões têm
# semântica política/ideológica relevante
uv run python scripts/01_inspect_schema.py
# → lê:   data/schema/dimensions.json
# → gera: outputs/phase0_schema_report.md
# → gera: outputs/phase0_political_dimensions.json
```

### Fase 1 — Download de shards e exploração de distribuições

```bash
uv run python scripts/02_explore_parquet.py
# → baixa: data/persona-1m/ (2 shards Parquet, ~500 MB, 200.000 personas)
# → lê:    outputs/phase0_political_dimensions.json
# → gera:  outputs/phase1_parquet_schema_raw.txt
# → gera:  outputs/phase1_parquet_report.md
# → gera:  outputs/phase1_candidate_personas.json
```

### Fase 2 — Decodificação do vetor binário + classificação de polos

```bash
uv run python scripts/03_decode_attributes.py
# → lê:   data/schema/persona_codes.schema.json
# → lê:   outputs/phase0_political_dimensions.json
# → lê:   docs/left right categories/regras_categorizacao_esquerda_direita.json
# → lê:   data/persona-1m/*.parquet
# → gera: outputs/phase2_decode_validation.md
# → gera: outputs/phase2_decoded_personas.json   ← consumido pela Fase 3
# → gera: outputs/phase2_decode_report.md
```

O que este passo faz, em resumo:

1. Amostra 2.000 personas (seed fixa = 42) dos 200.000 registros baixados.
2. Decodifica, para cada uma, as 10 dimensões politicamente relevantes
   curadas manualmente (`political_lean`, `religiosity`, `trust_level`,
   `values_priority` e os seis `att_*`).
3. Classifica cada persona em **polo esquerda** ou **polo direita** aplicando
   a regra de coerência multi-indicador definida em
   [`docs/left right categories/regras_categorizacao_esquerda_direita.json`](../dataset_analysis/docs/left%20right%20categories/regras_categorizacao_esquerda_direita.json)
   (fundamentação teórica completa no `.md` irmão): âncora obrigatória em
   `political_lean`, exigência de ausência de contradição nos indicadores
   nucleares (eixo econômico) e tolerância periférica no eixo social/valores.
   Isso descarta perfis internamente contraditórios (ex.: "conservador" com
   `att_labor_unions=Enthusiast`) e perfis com evidência insuficiente
   (ex.: âncora sozinha, sem nenhum atributo secundário preenchido).
4. Ordena os elegíveis por força de coerência e salva os 10 melhores de cada
   polo em `outputs/phase2_decoded_personas.json`, junto com os contadores
   de coerência (`coherence`) e um log de exclusões
   (`pole_classification_rule.stats`).

**Verificação rápida:** o console imprime, ao final, quantas personas foram
aceitas e excluídas por polo, e o motivo de cada exclusão:

```
Perfis elegíveis polo esquerda: 101 (modo=strict); polo direita: 20 (modo=strict)
Exclusões polo esquerda: {'excluded': 68, 'reasons': {...}}
Exclusões polo direita: {'excluded': 162, 'reasons': {...}}
```

---

## Parte 2 — `debate_simulation/` (Fase 3)

Requer que `dataset_analysis/outputs/phase2_decoded_personas.json` já exista
(Parte 1 concluída). Comandos abaixo assumem diretório de trabalho
`debate_simulation/`.

```bash
cd ../debate_simulation
uv sync
```

### Fase 3 — Geração dos prompts de debate (Layer 1)

```bash
uv run python scripts/00_generate_persona_prompts.py
# → lê:   ../dataset_analysis/outputs/phase2_decoded_personas.json
# → gera: outputs/prompts/personas/persona_metadata.json
# → gera: outputs/prompts/personas/polo_esquerda/persona_NN.txt (10 arquivos)
# → gera: outputs/prompts/personas/polo_direita/persona_NN.txt  (10 arquivos)
```

O que este passo faz:

- Para cada uma das 20 personas (10 por polo) em `phase2_decoded_personas.json`,
  gera um prompt de sistema em **inglês** (Layer 1 — identidade ideológica),
  seguindo um template fixo: religiosidade, confiança institucional, valor
  central e as posições `att_*` não-nulas.
- O texto do prompt **não contém** o alinhamento político da persona
  (*political-lean blinding*): nem o atributo `political_lean`, nem o rótulo
  do polo. A persona é descrita apenas por suas posições substantivas, para
  que o modelo derive a postura desses atributos em vez de encenar o
  estereótipo associado ao rótulo "esquerda"/"direita". O valor continua
  registrado em `persona_metadata.json` (campo `blinded_attributes`) — o
  ocultamento é do agente, não de quem conduz o experimento. Justificativa
  completa em
  [`debate_simulation/docs/persona_prompt_design_decisions.md`](../debate_simulation/docs/persona_prompt_design_decisions.md).
- O texto do prompt também **não contém** nenhuma referência à origem do dado
  (fonte do dataset, ID da entidade Wikidata etc.) — essa informação de
  rastreamento fica exclusivamente em `persona_metadata.json`, uma lista de
  20 objetos `{pole, pole_label, persona_index, matraix_source, matraix_id,
  prompt_version, blinded_attributes}` que permite religar cada arquivo `.txt`
  à persona original quando necessário (auditoria, reprodutibilidade, citação
  no artigo).
- Este script gera apenas Layer 1 (identidade ideológica). O comportamento de
  debate (Layer 2 — regras de discurso improdutivo, escalada, etc.) é um
  arquivo separado e estático, não gerado por script:
  [`prompts/debate behavior/debate behavior.txt`](../debate_simulation/prompts/debate%20behavior/debate%20behavior.txt).
  Layer 1 e Layer 2 são combinados no momento de montar o prompt final do
  agente debatedor (fora do escopo desta fase de geração).

---

## Parte 3 — Execução do experimento (Fases 4-6)

A partir daqui o pipeline **chama modelos de LLM** e produz dado
experimental. As três fases rodam pelo mesmo script; são separadas aqui
porque produzem artefatos distintos e podem ser inspecionadas uma a uma.

Todos os comandos assumem diretório de trabalho `debate_simulation/`.

### Pré-requisito: modelos locais (Ollama)

O experimento roda com modelos locais. Justificativa da escolha (e por que os
modelos gratuitos da OpenRouter foram descartados) em
[`debate_simulation/docs/local_models_decision.md`](../debate_simulation/docs/local_models_decision.md).

```bash
# 1. Instalar o Ollama
brew install ollama                              # macOS
# ou: curl -fsSL https://ollama.com/install.sh | sh

# 2. Subir o servidor (deixe rodando, ou use o app do macOS)
ollama serve

# 3. Baixar os três modelos — ~15,4 GB, uma única vez
ollama pull llama3.1:8b-instruct-q4_K_M   # debatedor · 4,9 GB
ollama pull qwen2.5:7b-instruct-q4_K_M    # moderador · 4,7 GB
ollama pull gemma2:9b-instruct-q4_K_M     # juiz      · 5,8 GB

# 4. Conferir
ollama list
curl http://localhost:11434/api/version
```

Selecione o perfil e valide o encanamento:

```bash
export DEBATE_PROFILE=local

uv run python scripts/smoke_test.py --profile local
# → 3 chamadas (uma por papel). Se falhar aqui, é config/servidor,
#   não lógica do experimento.
```

**Memória.** Os três modelos somam ~15,4 GB em disco, mas não ficam residentes
ao mesmo tempo: debate + moderação usam dois (~10,5 GB de RAM); o julgamento
roda depois, com um só (~6,5 GB). Em uma máquina com 16 GB funciona; com 24 GB
há folga. O Ollama descarrega modelos ociosos após 5 minutos
(`OLLAMA_KEEP_ALIVE`) e sob pressão de memória.

> **Alternativa por API (não recomendada para produzir dado).** Se preferir a
> OpenRouter, defina `OPENROUTER_API_KEY` (via `export` ou um `.env` na raiz
> do repositório) e use `--profile smoke_test`. Note a cota de 50
> requisições/dia e a instabilidade do pool de modelos gratuitos — em testes,
> a condição de tratamento falhou repetidamente por indisponibilidade do
> moderador.

### Orçamento de chamadas

> **Com o perfil `local` não há cota nem custo por chamada** — o limite é
> tempo de inferência, não requisições. As tabelas abaixo importam apenas se
> você usar um perfil de API. Para dimensionar o tempo local, meça
> `latency_ms` no piloto e multiplique pelo número de chamadas.

O free tier da OpenRouter tem **cota de 50 requisições por dia**. Cada etapa
consome:

| Etapa | Chamadas |
|---|---|
| Debate | 1 por turno, por condição |
| Moderação | 1 por turno (só no tratamento) |
| Juiz | 3 por mensagem publicada, por condição |

Um debate é sempre entre **duas personas** (uma de cada polo) — isso não é
parâmetro. O que dimensiona o custo são **turnos**, **condições** e
**execuções do juiz por mensagem**.

Fórmula: `debate = turnos × condições` · `moderação = turnos` (só no
tratamento) · `juiz = turnos × condições × execuções`.

| Configuração do piloto | Comando | Exp. | +smoke |
|---|---|---:|---:|
| **2 turnos, 2 condições, juiz 3×** | `--turns 2 --judge` | 18 | 21 |
| **3 turnos, 2 condições, juiz 3×** | `--turns 3 --judge` | 27 | 30 |
| **4 turnos, 2 condições, juiz 3×** | `--turns 4 --judge` | 36 | 39 |
| 3 turnos, 2 condições, juiz 1× | `--turns 3 --judge --judge-runs 1` | 15 | 18 |
| 6 turnos, só tratamento, juiz 3× | `--turns 6 --condition treatment --judge` | 30 | 33 |
| 6 turnos, 2 condições, juiz 1× | `--turns 6 --judge --judge-runs 1` | 30 | 33 |

**Todas as linhas acima cabem nas 50 requisições diárias.** Recomendado para
a primeira rodada: **3 turnos, 2 condições, juiz 3×** (30 com o smoke) — deixa
20 requisições de folga para uma segunda tentativa no mesmo dia se algo falhar.

> `--judge-runs 1` economiza bastante, mas **elimina a medida de consistência
> intra-juiz** (§8.4 do desenho): com uma execução só não há como saber se o
> juiz concorda consigo mesmo. Use para esticar o orçamento numa depuração,
> não para produzir dado que vá para a análise.

Escopos que **não** cabem:

| Escopo | Chamadas | No free tier |
|---|---|---|
| 1 célula completa (12 turnos, 2 condições, juiz 3×) | 108 | ~3 dias |
| Experimento completo (3 temas × 10 pares) | 3.240 | ~65 dias |

Adicionar ~US$ 10 de crédito eleva a cota para 1000/dia, colocando o
experimento completo em ~3 dias — dentro do teto de R$ 100 do projeto.

A cota é **diária e por conta**, contando toda requisição a modelo `:free`,
inclusive as que falham por erro de parsing e são repetidas. Reserve folga.

---

### Fase 4 — Debate (Layer 1 + Layer 2 → mensagens candidatas)

Não roda isolada: o debate acontece dentro de `run_debate.py`, junto com a
moderação. Para ver **só** o debate, use a condição de controle, onde nenhum
moderador atua:

```bash
uv run python scripts/run_debate.py --condition control --turns 3
# → gera: experiments/{experiment_id}/manifest.json
# → gera: experiments/{experiment_id}/transcript.json
# custo: 3 chamadas (1 por turno)
```

O que acontece a cada turno:

1. O debatedor da vez recebe um prompt de sistema montado na hora:
   **Layer 1** (sua persona) + **Layer 2** (regras de debate improdutivo) +
   o tema.
2. Recebe, como mensagem de usuário, o histórico **publicado** até ali,
   rotulado `YOU` / `OPPONENT` — nunca por polo.
3. Devolve uma mensagem em texto livre (a *candidata*).
4. No controle, a candidata é publicada sem alteração.
5. As personas alternam: `persona_1` (esquerda) abre, `persona_2` (direita)
   responde.

### Fase 5 — Moderação D5 (candidata → texto publicado)

```bash
uv run python scripts/run_debate.py --condition treatment --turns 3
# → gera: experiments/{experiment_id}/manifest.json
# → gera: experiments/{experiment_id}/transcript.json
# → gera: experiments/{experiment_id}/moderation/turn_NNN_persona_N.json
# custo: 6 chamadas (3 de debate + 3 de moderação)
```

O que muda em relação ao controle: antes de publicar, cada candidata passa
pelo moderador D5, que devolve um JSON com `hostility_level` (0-4),
patologias detectadas, justificativa e — se `hostility_level >= 2` — uma
`reformulation`.

**A reformulação substitui a candidata automaticamente**, e é ela que o
oponente vê no turno seguinte. É isso que propaga o efeito da intervenção
pelo debate. (Substituição sem etapa de aceite é decisão metodológica
deliberada — estima o efeito sob *compliance* total, um limite superior. Ver
Seção 8.2 de `estado_atual_do_trabalho.md`.)

Se a moderação falhar de forma irrecuperável, o debate **não** aborta: a
candidata é publicada, o turno é marcado `moderated: false` e listado em
`unmoderated_turns`. Média de hostilidade no tratamento deve excluir esses
turnos.

### Fase 6 — Juiz de hostilidade (texto publicado → notas)

```bash
uv run python scripts/run_debate.py --turns 3 --judge
# roda as DUAS condições e pontua ambas
# → gera, em cada experiment_id:
#     judgements/turn_NNN_persona_N.json
# custo: 27 chamadas (6 debate + 3 moderação + 18 juiz)
```

Cada mensagem **publicada** é pontuada 3 vezes na mesma escala 0-4
(consistência intra-juiz). O juiz:

- é um modelo de **família diferente** dos outros dois (anti-afinidade: não
  avalia texto que ele mesmo escreveu);
- **não sabe a condição** nem se uma mensagem foi reformulada — ele pontua
  texto, não intervenções;
- tem suas 3 execuções guardadas individualmente; mediana, amplitude e
  unanimidade são **derivadas** delas.

> **`hostility_level` do moderador ≠ nota do juiz.** O moderador pontua a
> *candidata*, antes da publicação. O juiz pontua o que foi *publicado*. No
> tratamento com reformulação são textos diferentes — compará-los
> diretamente compara uma mensagem com sua própria substituta.

---

## Rodada piloto — passo a passo completo

Sequência mínima que exercita as três fases e cabe no free tier — **30
chamadas no total**, deixando 20 de folga na cota diária.

```bash
cd debate_simulation
uv sync
export DEBATE_PROFILE=local          # modelos locais; ver pré-requisito acima

# 1. Testes offline — sem modelo nenhum, sem custo
uv run pytest tests/ -q
#    esperado: 167 passed

# 2. Encanamento — 3 chamadas
uv run python scripts/smoke_test.py --profile local
#    esperado: SMOKE TEST PASSED — 3/3 roles reachable

# 3. O piloto: debate + moderação + juiz, nas duas condições — 27 chamadas
uv run python scripts/run_debate.py --turns 3 --judge

# 4. Ler os resultados (só disco, sem custo)
uv run python scripts/show_results.py              # lista as execuções
uv run python scripts/show_results.py --compare    # controle × tratamento
uv run python scripts/show_results.py --last --full
```

> A primeira chamada a cada modelo inclui o carregamento em memória e é
> visivelmente mais lenta que as seguintes. Não confunda com travamento.

Ajustes de escala, se precisar de mais folga ou de mais debate:

```bash
# Mais barato ainda — 18 chamadas
uv run python scripts/run_debate.py --turns 2 --judge

# Escalada mais longa, mas só o tratamento — 30 chamadas
uv run python scripts/run_debate.py --turns 6 --condition treatment --judge
```

> Com **2-3 turnos a escalada é curta** — cada persona fala 1 ou 2 vezes, e a
> Layer 2 manda a hostilidade crescer progressivamente ("by turn 6 you should
> be openly hostile"). Espere um contraste modesto entre as condições. O
> objetivo desta rodada é verificar que **o fluxo produz dado interpretável**,
> não medir o efeito: para isso são os 12 turnos.

### O que observar em cada etapa

Durante o passo 3, a saída mostra o debate acontecendo ao vivo:

```
TREATMENT — Gun Ownership · pair-00
  Turn 1 [persona_1]  hostility=0
    Look, I'm not anti-gun, but the whole "I need an AR-15..." crowd...
  Turn 3 [persona_1]  hostility=2  REFORMULATED
    candidate : "The CDC estimate that you love to throw around? You realize...
    published : The CDC estimate you cite comes from a Kleck survey that has...
```

- `hostility=N` — a nota do **moderador** para a candidata.
- `REFORMULATED` — a candidata cruzou o limiar; compare as duas linhas para
  ver o que foi removido e o que foi preservado.
- `--- judging N messages ---` — a fase do juiz, com `median` e as 3 notas.

No passo 4, `--compare` dá o resultado principal:

```
  control     mean=2.50  per-turn=[1, 4]  interventions=0
  treatment   mean=1.00  per-turn=[1, 1]  interventions=1
```

### Perguntas que o piloto responde

1. **As personas escalam hostilidade no controle?** Se não escalarem
   (guardrail do modelo, Layer 2 fraca demais), o D5 não tem o que moderar e
   o experimento não se sustenta. Olhe a trajetória do controle primeiro.
2. **O D5 dispara na frequência esperada?** `interventions` sobre o total de
   turnos.
3. **A reformulação preserva o argumento?** Compare `candidate` × `published`
   com `--full`, que mostra também o campo `argument_preserved`.
4. **O juiz é consistente consigo mesmo?** Procure por
   `judge disagreed with itself`. Muita discordância indica que o prompt do
   juiz precisa de calibração antes da execução completa.

---

## Estrutura de saída do experimento

```
debate_simulation/experiments/
└── 20260830-164116_gun-ownership_pair-00_treatment/
    ├── manifest.json          ← condições da execução
    ├── transcript.json        ← o debate publicado
    ├── moderation/            ← só no tratamento
    │   ├── turn_001_persona_1.json
    │   └── turn_002_persona_2.json
    └── judgements/            ← só com --judge
        ├── turn_001_persona_1.json
        └── turn_002_persona_2.json
```

O `experiment_id` é `{YYYYMMDD-HHMMSS}_{tema}_{par}_{condição}`. Cada
execução cria um diretório novo — nada é sobrescrito.

| Arquivo | O que contém | Quando ler |
|---|---|---|
| `manifest.json` | Personas (com proveniência MatrAIx), modelos, SHA-256 dos prompts, seed, threshold | Para saber sob quais condições o dado foi produzido |
| `transcript.json` | Por turno: candidata, texto publicado, se foi reformulado, nota do moderador, se foi moderado | Visão geral do debate |
| `moderation/turn_*.json` | Veredito completo: justificativa, patologias, `argument_preserved`, snapshot do histórico que o moderador viu, metadados da chamada | Auditar uma reformulação específica |
| `judgements/turn_*.json` | As 3 execuções do juiz + resumo (mediana, amplitude, unanimidade) | Analisar hostilidade e consistência |
| `*_FAILED.json` | Falhas irrecuperáveis: resposta bruta, tipo e mensagem da exceção | Diagnosticar o que deu errado |

Falhas são **gravadas**, não omitidas — um arquivo ausente seria
indistinguível de um turno que nunca rodou.

---

## Experimento completo

> **Não rode antes de o piloto validar os modelos escolhidos.** A regra de
> congelamento (Seção 8.1 do plano) prevê que prompts e desenho fiquem
> fixos ao fim da Semana 1; rodar 3.240 chamadas com um prompt que ainda vai
> mudar é desperdício.

Parâmetros do desenho: **3 temas × 10 pares × 12 turnos × 2 condições**.

```bash
# 1. Perfil de produção (ver debate_simulation/README.md)
export DEBATE_PROFILE=local

# 2. Rodar cada célula: tema × par
for topic in "Gun Ownership" "Abortion" "Drug Legalization"; do
  for i in 0 1 2 3 4 5 6 7 8 9; do
    uv run python scripts/run_debate.py \
      --topic "$topic" \
      --pair "pair-0$i" \
      --persona-index "$i" \
      --turns 12 \
      --judge
  done
done
```

Cada célula é independente: uma falha não invalida as anteriores, e o laço
pode ser retomado a partir da célula que faltou. Dentro de um debate, a
retomada é por turno — `transcript.json` e os registros já gravados
permitem continuar sem regerar o que existe.

---

## Outputs finais relevantes para o experimento

| Arquivo | Descrição |
|---|---|
| `dataset_analysis/outputs/phase2_decoded_personas.json` | As 20 personas selecionadas (10 esquerda + 10 direita), com atributos decodificados e métricas de coerência |
| `dataset_analysis/outputs/phase2_decode_report.md` | Cobertura por dimensão, distribuições, tabela de exclusões por polo |
| `debate_simulation/outputs/prompts/personas/persona_metadata.json` | Metadados de rastreamento das 20 personas (polo, fonte, ID, versão do prompt e `political_lean` ocultado do texto do prompt) |
| `debate_simulation/outputs/prompts/personas/polo_esquerda/persona_NN.txt` | 10 prompts de sistema (Layer 1), polo esquerda, em inglês |
| `debate_simulation/outputs/prompts/personas/polo_direita/persona_NN.txt` | 10 prompts de sistema (Layer 1), polo direita, em inglês |
| `debate_simulation/prompts/debate behavior/debate behavior.txt` | Layer 2 — regras de comportamento de debate improdutivo (estático, não gerado) |
| `debate_simulation/prompts/debate moderator D5/debate moderator D5.txt` | Prompt do moderador D5 (estático, não gerado) |
| `debate_simulation/prompts/debate judge/debate judge.txt` | Prompt do juiz de hostilidade (estático, não gerado) |
| `debate_simulation/experiments/{experiment_id}/` | Uma execução do experimento: manifest, transcript, registros de moderação e do juiz |

---

## Rodando tudo do zero (sequência única)

```bash
# A partir da raiz do repositório
cd dataset_analysis
uv sync
uv run python scripts/00_download_schema.py
uv run python scripts/01_inspect_schema.py
uv run python scripts/02_explore_parquet.py
uv run python scripts/03_decode_attributes.py

cd ../debate_simulation
uv sync
uv run python scripts/00_generate_persona_prompts.py

# --- daqui em diante o pipeline chama LLMs ---
# Pré-requisito: Ollama instalado e os 3 modelos baixados (ver Parte 3)
export DEBATE_PROFILE=local
uv run pytest tests/ -q                                    # offline, sem modelo
uv run python scripts/smoke_test.py --profile local        # 3 chamadas
uv run python scripts/run_debate.py --turns 3 --judge      # 27 chamadas
uv run python scripts/show_results.py --compare            # offline
```

## Notas

- Todos os scripts são idempotentes quanto a downloads (não rebaixam
  arquivos já presentes), mas **regeneram** seus outputs a cada execução —
  rodar a Fase 2 de novo sobrescreve `phase2_decoded_personas.json`, o que
  por sua vez muda quais personas a Fase 3 vai usar.
- A amostragem da Fase 2 usa seed fixa (`SAMPLE_SEED = 42`), então o
  conjunto de 2.000 personas amostradas é o mesmo entre execuções — mas a
  regra de classificação de polos (JSON de regras) pode mudar se você editar
  `docs/left right categories/regras_categorizacao_esquerda_direita.json`,
  o que muda quais das 2.000 entram nos polos.
- **Fases 0-3 não requerem chave de API** — são inspeção/decodificação
  offline de dados e geração de texto por template, sem chamadas a LLM. A
  suíte de testes (`uv run pytest tests/ -q`) também é inteiramente offline:
  o cliente LLM é substituído por um duplo com respostas roteirizadas.
- **Fases 4-6 requerem os modelos rodando** (Ollama no perfil `local`, ou
  `OPENROUTER_API_KEY` num perfil de API). Só elas geram `experiments/`.
- Ao contrário das fases anteriores, **a execução do experimento nunca
  sobrescreve** seus outputs: cada rodada cria um `experiment_id` novo
  (carimbado com data/hora), e dentro dele um turno repetido recebe sufixo
  numérico em vez de substituir o anterior.
- Os modelos gratuitos do perfil `smoke_test` são de *reasoning* e gastam
  tokens de raciocínio antes de emitir JSON — por isso seus `max_tokens` são
  bem maiores que os dos perfis pagos. Se aparecer
  `finish_reason='length'` com conteúdo nulo, é isso: aumente `max_tokens`
  daquele papel em `config/models.yaml`.
- No perfil `local`, a **primeira chamada a cada modelo** carrega os pesos em
  memória e é bem mais lenta que as seguintes. O Ollama mantém o modelo
  carregado por 5 minutos após o último uso; ajuste com
  `export OLLAMA_KEEP_ALIVE=10m` se quiser evitar recargas entre fases.
- Os modelos locais **não reportam contagem de tokens** de forma consistente.
  Quando o provedor não informa, `usage` é gravado como `null` nos registros —
  nunca fabricado. Latência (`latency_ms`) continua sendo medida normalmente.