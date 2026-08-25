# debate_simulation

Simulação de debates políticos improdutivos usando personas de debate geradas a partir do MatrAIx Persona 1M. Cobre a geração de prompts de persona, o fluxo de debate com moderação, e um juiz que avalia se a hostilidade/moderação foi respeitada.

Este subprojeto consome os outputs de [`../dataset_analysis/`](../dataset_analysis/) (especificamente `phase2_decoded_personas.json`) e é independente em dependências — não compartilha `.venv` nem `pyproject.toml` com a análise do dataset.

## Estado atual

- ✅ Geração de prompts de persona a partir dos atributos decodificados (polo esquerda/direita).
- ⏳ Simulação do debate entre personas — **em aberto**, depende da escolha do motor de LLM.
- ⏳ Fluxo de moderação — **em aberto**.
- ⏳ Juiz (avaliação de hostilidade/moderação) — **em aberto**.

## Pré-requisitos

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `../dataset_analysis/outputs/phase2_decoded_personas.json` já gerado (rodar o subprojeto `dataset_analysis/` primeiro)

## Setup

```bash
cd debate_simulation
uv sync
```

## Execução dos scripts

```bash
# Fase 3 — Gerar prompts de persona a partir das personas decodificadas
uv run python scripts/00_generate_persona_prompts.py
# → lê:   ../dataset_analysis/outputs/phase2_decoded_personas.json
# → gera: outputs/phase3_persona_prompts.json
# → gera: prompts/polo_esquerda/persona_NN.txt
# → gera: prompts/polo_direita/persona_NN.txt
```

## Outputs esperados

| Arquivo | Gerado por | Conteúdo |
|---|---|---|
| `outputs/phase3_persona_prompts.json` | `00_generate_persona_prompts.py` | Prompts estruturados de todas as personas, por polo |
| `prompts/polo_esquerda/persona_NN.txt` | `00_generate_persona_prompts.py` | Prompt de sistema individual, pronto para uso como persona |
| `prompts/polo_direita/persona_NN.txt` | `00_generate_persona_prompts.py` | Idem, polo direita |

## Notas

- As personas atuais vêm de uma amostra pequena (10 por polo) do coreset MatrAIx — ver limitações registradas em `../dataset_analysis/outputs/phase2_decode_report.md`.
- Os prompts são gerados apenas a partir dos atributos categóricos decodificados (`political_attributes`) — o dataset não fornece biografia/nome para essas personas, então os prompts são deliberadamente enxutos.
- Nenhuma dependência de SDK de LLM foi adicionada ainda — a escolha do motor (Anthropic API ou outro) ainda está em aberto e deve ser feita antes dos próximos scripts (debate, moderação, juiz).
- Os dados baixados/gerados (`outputs/`, `prompts/`) seguem a mesma política do repositório: outputs não são versionados por padrão (ver `.gitignore` na raiz).
