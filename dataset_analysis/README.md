# dataset_analysis

Inspeção exploratória do dataset MatrAIx Persona 1M para identificar dimensões ideológicas relevantes à polarização política brasileira. Objetivo: avaliar se o dataset pode fundamentar a construção de personas de debate contrastantes (conservador vs. progressista) para o experimento em [`../debate_simulation/`](../debate_simulation/).

Este é o subprojeto de **análise do dataset** (Fases 0-2). A simulação do debate em si (geração de prompts, moderação, julgamento) vive em [`../debate_simulation/`](../debate_simulation/), como um subprojeto Python independente.

## Pré-requisitos

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Setup

```bash
# 1. A partir da raiz do repositório, entrar neste subprojeto
cd dataset_analysis

# 2. Criar ambiente virtual e instalar dependências
uv sync

# 3. (Somente se o dataset HuggingFace for gated) Autenticar
uv run huggingface-cli login
```

## Execução dos scripts

```bash
# Fase 0 — Download dos arquivos de schema
uv run python scripts/00_download_schema.py

# Fase 0 — Inspeção do schema: identifica dimensões politicamente relevantes
uv run python scripts/01_inspect_schema.py

# Fase 1 — Download de 2 shards Parquet + exploração de distribuições
uv run python scripts/02_explore_parquet.py

# Fase 2 — Decodificação do vetor binário de atributos políticos
uv run python scripts/03_decode_attributes.py
```

## Ordem de execução detalhada

```bash
# Setup único (cria .venv e instala dependências do pyproject.toml)
uv sync

# (Somente se o dataset HuggingFace for gated)
uv run huggingface-cli login

# Fase 0 — passo 1: baixar os arquivos de schema
uv run python scripts/00_download_schema.py
# → gera: data/schema/dimensions.json
# → gera: data/schema/persona_codes.schema.json

# Fase 0 — passo 2: inspecionar schema e identificar dimensões políticas
uv run python scripts/01_inspect_schema.py
# → lê:   data/schema/dimensions.json
# → gera: outputs/phase0_schema_report.md
# → gera: outputs/phase0_political_dimensions.json

# Fase 1: baixar 2 shards Parquet e explorar distribuições
uv run python scripts/02_explore_parquet.py
# → baixa: data/persona-1m/ (2 shards, ~500MB)
# → lê:   outputs/phase0_political_dimensions.json
# → gera: outputs/phase1_parquet_schema_raw.txt
# → gera: outputs/phase1_parquet_report.md
# → gera: outputs/phase1_candidate_personas.json

# Fase 2: decodificar o vetor binário `attributes` para as dimensões políticas
uv run python scripts/03_decode_attributes.py
# → lê:   data/schema/persona_codes.schema.json
# → lê:   outputs/phase0_political_dimensions.json
# → lê:   data/persona-1m/*.parquet
# → gera: outputs/phase2_decode_validation.md
# → gera: outputs/phase2_decoded_personas.json
# → gera: outputs/phase2_decode_report.md
```

## Outputs esperados

| Arquivo | Gerado por | Conteúdo |
|---|---|---|
| `outputs/phase0_schema_report.md` | `01_inspect_schema.py` | Relatório de dimensões por grupo, tabelas de candidatos políticos |
| `outputs/phase0_political_dimensions.json` | `01_inspect_schema.py` | Lista estruturada de dimensões candidatas com valores |
| `outputs/phase1_parquet_schema_raw.txt` | `02_explore_parquet.py` | Schema real das colunas Parquet |
| `outputs/phase1_parquet_report.md` | `02_explore_parquet.py` | Distribuições, perfis contrastantes, cobertura |
| `outputs/phase1_candidate_personas.json` | `02_explore_parquet.py` | Personas candidatas dos dois polos ideológicos |
| `outputs/phase2_decode_validation.md` | `03_decode_attributes.py` | Evidência empírica da convenção de decodificação do vetor binário |
| `outputs/phase2_decoded_personas.json` | `03_decode_attributes.py` | Amostra de personas com atributos políticos decodificados |
| `outputs/phase2_decode_report.md` | `03_decode_attributes.py` | Cobertura, distribuições e perfis contrastantes decodificados |

## Notas

- Todos os scripts são idempotentes: rodar duas vezes não duplica downloads nem quebra outputs já gerados.
- Nenhum script requer chave de API da Anthropic — esta fase é de inspeção offline de dados.
- Os dados baixados (`data/persona-1m/`, `data/schema/*.json`) não são versionados no git.
