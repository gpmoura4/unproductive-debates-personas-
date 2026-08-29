# debate_simulation

Simulação de debates políticos improdutivos usando personas de debate geradas a partir do MatrAIx Persona 1M. Cobre a geração de prompts de persona, o fluxo de debate com moderação, e um juiz que avalia se a hostilidade/moderação foi respeitada.

Este subprojeto consome os outputs de [`../dataset_analysis/`](../dataset_analysis/) (especificamente `phase2_decoded_personas.json`) e é independente em dependências — não compartilha `.venv` nem `pyproject.toml` com a análise do dataset.

## Estado atual

- ✅ Geração de prompts de persona (Layer 1 — identidade ideológica, em inglês) a partir dos atributos decodificados (polo esquerda/direita), com rastreamento de origem separado em `persona_metadata.json`.
- ✅ Layer 2 (comportamento de debate improdutivo) definida estaticamente em [`prompts/debate behavior/debate behavior.txt`](prompts/debate%20behavior/debate%20behavior.txt) — não gerada por script.
- ⏳ Simulação do debate entre personas (combinação de Layer 1 + Layer 2, execução via LLM) — **em aberto**, depende da escolha do motor de LLM.
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
# Fase 3 — Gerar prompts de persona (Layer 1) a partir das personas decodificadas
uv run python scripts/00_generate_persona_prompts.py
# → lê:   ../dataset_analysis/outputs/phase2_decoded_personas.json
# → gera: outputs/prompts/personas/persona_metadata.json
# → gera: outputs/prompts/personas/polo_esquerda/persona_NN.txt
# → gera: outputs/prompts/personas/polo_direita/persona_NN.txt
```

## Outputs esperados

| Arquivo | Gerado por | Conteúdo |
|---|---|---|
| `outputs/prompts/personas/persona_metadata.json` | `00_generate_persona_prompts.py` | Lista de 20 objetos `{pole, pole_label, persona_index, matraix_source, matraix_id, prompt_version, blinded_attributes}` — rastreamento de origem e alinhamento político, ambos fora do texto do prompt |
| `outputs/prompts/personas/polo_esquerda/persona_NN.txt` | `00_generate_persona_prompts.py` | Prompt de sistema (Layer 1), em inglês, pronto para uso como persona |
| `outputs/prompts/personas/polo_direita/persona_NN.txt` | `00_generate_persona_prompts.py` | Idem, polo direita |
| [`prompts/debate behavior/debate behavior.txt`](prompts/debate%20behavior/debate%20behavior.txt) | (estático, não gerado) | Layer 2 — regras de comportamento de debate improdutivo, comum aos dois polos |

## Notas

- As personas atuais vêm de uma amostra do coreset MatrAIx (10 por polo, selecionadas por uma regra de coerência ideológica multi-indicador) — ver a regra em `../dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md` e os números de cobertura/exclusão em `../dataset_analysis/outputs/phase2_decode_report.md`.
- Os prompts (Layer 1) são gerados apenas a partir dos atributos categóricos decodificados (`political_attributes`) — o dataset não fornece biografia/nome para essas personas, então os prompts são deliberadamente enxutos. Todos os textos são gerados em inglês e não contêm nenhuma referência à fonte/ID do dataset original; essa informação de proveniência vive só em `persona_metadata.json`.
- **O alinhamento político é omitido do texto do prompt** (*political-lean blinding*): nem `political_lean` nem o rótulo do polo aparecem no `.txt`. A persona é descrita só por suas posições substantivas, para evitar que o modelo encene o estereótipo associado ao rótulo em vez de derivar a postura dos atributos amostrados. O valor continua em `persona_metadata.json` (`blinded_attributes`) e na estrutura de diretórios — o ocultamento vale para o agente, não para nós. Justificativa em [`docs/persona_prompt_design_decisions.md`](docs/persona_prompt_design_decisions.md).
- Layer 2 (`prompts/debate behavior/debate behavior.txt`) é independente do polo/persona — define como qualquer persona deve se comportar durante o debate (regras de discurso improdutivo, escalada, etc.) e é combinada com o Layer 1 no momento de montar o prompt final do agente.
- Nenhuma dependência de SDK de LLM foi adicionada ainda — a escolha do motor (Anthropic API ou outro) ainda está em aberto e deve ser feita antes dos próximos scripts (debate, moderação, juiz).
- Os dados gerados (`outputs/`) seguem a mesma política do repositório: outputs não são versionados por padrão (ver `.gitignore` na raiz) — exceto quando comitados deliberadamente para fixar o conjunto de personas usado no experimento.
