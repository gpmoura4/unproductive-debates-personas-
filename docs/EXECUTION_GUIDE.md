# Guia de execução — pipeline completo

Este guia orienta a execução, do zero, de todas as fases do pipeline: da
inspeção do dataset MatrAIx Persona 1M até a geração dos prompts de debate
(Layer 1) usados como persona. Cobre os dois subprojetos independentes
(`dataset_analysis/` e `debate_simulation/`), na ordem correta.

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
```

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

## Outputs finais relevantes para o experimento

| Arquivo | Descrição |
|---|---|
| `dataset_analysis/outputs/phase2_decoded_personas.json` | As 20 personas selecionadas (10 esquerda + 10 direita), com atributos decodificados e métricas de coerência |
| `dataset_analysis/outputs/phase2_decode_report.md` | Cobertura por dimensão, distribuições, tabela de exclusões por polo |
| `debate_simulation/outputs/prompts/personas/persona_metadata.json` | Metadados de rastreamento das 20 personas (polo, fonte, ID, versão do prompt e `political_lean` ocultado do texto do prompt) |
| `debate_simulation/outputs/prompts/personas/polo_esquerda/persona_NN.txt` | 10 prompts de sistema (Layer 1), polo esquerda, em inglês |
| `debate_simulation/outputs/prompts/personas/polo_direita/persona_NN.txt` | 10 prompts de sistema (Layer 1), polo direita, em inglês |
| `debate_simulation/prompts/debate behavior/debate behavior.txt` | Layer 2 — regras de comportamento de debate improdutivo (estático, não gerado) |

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
- Nenhum script requer chave de API da Anthropic — todo o pipeline até aqui
  é inspeção/decodificação offline de dados e geração de texto por template,
  sem chamadas a LLM.