# matraix-debate-personas

Pesquisa de mestrado (PESC/COPPE/UFRJ) que avalia se o dataset MatrAIx Persona 1M pode fundamentar personas de debate político polarizado (conservador vs. progressista), e usa essas personas para simular debates políticos improdutivos.

O repositório é dividido em dois subprojetos Python independentes, cada um com seu próprio `pyproject.toml`/`uv.lock`/`.venv`:

## [`dataset_analysis/`](dataset_analysis/)

Inspeção e exploração do dataset MatrAIx Persona 1M: schema, distribuições, decodificação do vetor binário de atributos, identificação de dimensões politicamente relevantes. Produz `outputs/phase2_decoded_personas.json`, a lista de personas decodificadas por polo ideológico que alimenta o subprojeto de simulação.

**Estado:** completo (Fases 0-2).

## [`debate_simulation/`](debate_simulation/)

Geração de prompts de persona a partir das personas decodificadas, simulação do debate entre polos opostos, fluxo de moderação, e um juiz que avalia hostilidade/aderência à moderação.

**Estado:** geração de prompts pronta; debate, moderação e juiz ainda em aberto (dependem da escolha do motor de LLM).

## Ordem de execução

```bash
# 1. Análise do dataset (gera as personas decodificadas por polo)
cd dataset_analysis
uv sync
uv run python scripts/00_download_schema.py
uv run python scripts/01_inspect_schema.py
uv run python scripts/02_explore_parquet.py
uv run python scripts/03_decode_attributes.py

# 2. Geração de prompts de persona (Layer 1) a partir do resultado acima
cd ../debate_simulation
uv sync
uv run python scripts/00_generate_persona_prompts.py
```

Guia detalhado, passo a passo, com o que cada script lê/gera e por quê:
[`docs/EXECUTION_GUIDE.md`](docs/EXECUTION_GUIDE.md).

Cada subprojeto também tem seu próprio README com detalhes de setup, scripts e outputs.

## Notas gerais

- Cada subprojeto usa `uv` exclusivamente para gerenciamento de dependências — nenhum `requirements.txt`, nenhum `pip install` direto.
- Dados baixados e ambientes virtuais não são versionados no git (ver `.gitignore` na raiz).
- `debate_simulation/` depende dos outputs de `dataset_analysis/` mas os dois nunca compartilham `.venv`.
