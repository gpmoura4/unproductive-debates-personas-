# debate_simulation

Simulação de debates políticos improdutivos usando personas de debate geradas a partir do MatrAIx Persona 1M. Cobre a geração de prompts de persona, o fluxo de debate com moderação, e um juiz que avalia se a hostilidade/moderação foi respeitada.

Este subprojeto consome os outputs de [`../dataset_analysis/`](../dataset_analysis/) (especificamente `phase2_decoded_personas.json`) e é independente em dependências — não compartilha `.venv` nem `pyproject.toml` com a análise do dataset.

## Estado atual

- ✅ Geração de prompts de persona (Layer 1 — identidade ideológica, em inglês) a partir dos atributos decodificados (polo esquerda/direita), com rastreamento de origem separado em `persona_metadata.json`.
- ✅ Layer 2 (comportamento de debate improdutivo) definida estaticamente em [`prompts/debate behavior/debate behavior.txt`](prompts/debate%20behavior/debate%20behavior.txt) — não gerada por script.
- ✅ Configuração de modelos por perfil ([`config/models.yaml`](config/models.yaml)) para os três papéis (debatedor, moderador D5, juiz), com 4 perfis selecionáveis e verificação de credenciais só para os provedores que o perfil usa.
- ✅ Cliente LLM único ([`src/llm/client.py`](src/llm/client.py)) para OpenRouter e Ollama (ambos expõem endpoints compatíveis com a API da OpenAI), com retry exponencial em falhas transitórias e captura de latência/uso de tokens.
- ✅ Smoke test ([`scripts/smoke_test.py`](scripts/smoke_test.py)) — valida que os três papéis alcançam seus modelos, sem depender do loop de debate.
- ⏳ Simulação do debate entre personas (combinação de Layer 1 + Layer 2, execução via LLM) — **em aberto**.
- ✅ Fluxo de moderação D5 ([`src/moderator/`](src/moderator/)) — schemas, montagem de prompt, orquestração (`D5Moderator.moderate()`) e parsing tolerante da resposta JSON. Decisões de design em [`docs/moderator_design_decisions.md`](docs/moderator_design_decisions.md).
- ⏳ Log das moderações ([`src/moderator/logger.py`](src/moderator/logger.py)) — **em aberto**. Deve expor `write(record)` e `write_failure(dict)`.
- ⏳ Juiz (avaliação de hostilidade/moderação) — **em aberto**.

## Pré-requisitos

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `../dataset_analysis/outputs/phase2_decoded_personas.json` já gerado (rodar o subprojeto `dataset_analysis/` primeiro)

## Setup

```bash
# Instalar dependências
uv sync

# Chave da OpenRouter (necessária para os perfis smoke_test, hybrid e api_only)
export OPENROUTER_API_KEY=sk-or-...

# Alternativa ao export: um arquivo .env na raiz do repositório ou em
# debate_simulation/, com uma linha KEY=valor. É lido automaticamente e já
# está no .gitignore. Uma variável exportada no shell tem precedência sobre
# o arquivo.
echo 'OPENROUTER_API_KEY=sk-or-...' > ../.env

# Opcional: instalar o Ollama e baixar os modelos locais
# (necessário para os perfis local e hybrid)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull gemma2:9b-instruct-q4_K_M
```

## Smoke test — validar o pipeline antes de escolher um perfil

```bash
# Usa modelos gratuitos da OpenRouter — sem custo.
uv run python debate_simulation/scripts/smoke_test.py
```

Se as três chamadas passarem, o encanamento está correto e você pode
prosseguir. Rode isto antes do experimento completo em qualquer máquina nova.

O script é deliberadamente independente do loop de debate, do juiz e da
seleção de personas: ele envia payloads mínimos fixos, então uma falha aqui é
falha de encanamento (config, credencial, rede), não de lógica do experimento.

Funciona da raiz do repositório ou de dentro de `debate_simulation/`. Se o
interpretador em uso não tiver as dependências do subprojeto — por exemplo,
quando há um virtualenv de **outro** projeto ativado no shell (`VIRTUAL_ENV`
apontando para outro lugar) — o script se reexecuta automaticamente em
`debate_simulation/.venv`, em vez de falhar com `ModuleNotFoundError`.

```bash
# Testar outro perfil (ex.: verificar se o Ollama está no ar)
uv run python debate_simulation/scripts/smoke_test.py --profile local
```

## Escolha do perfil para o experimento completo

Os quatro perfis vivem em [`config/models.yaml`](config/models.yaml). A troca
é de uma linha só — por ordem de precedência: flag de CLI, variável de
ambiente `DEBATE_PROFILE`, ou `default_profile` no YAML.

| Perfil | Debatedor · Moderador · Juiz | Custo | Tempo | Quando escolher |
|---|---|---|---|---|
| `smoke_test` | OpenRouter grátis (MiniMax M3 · Nemotron 3 Super · Cohere North Mini) | **US$ 0** | ~30 chamadas | **Sempre primeiro.** Valida o pipeline ponta a ponta. Rate limit de ~20 req/min |
| `local` | Tudo no Ollama (Llama 3.1 8B · Qwen 2.5 7B · Gemma 2 9B) | **US$ 0** | ~4 h | Custo zero é requisito, ou não há chave de API. **Risco:** guardrails em modelos 7-9B podem suprimir a escalada de hostilidade — validar no piloto |
| `hybrid` | OpenRouter pago (GPT-4o-mini · Claude Haiku 4.5) + juiz no Ollama | ~US$ 3 | ~1 h | **Perfil de produção recomendado.** Qualidade onde importa (debate e moderação), custo zero no juiz, que é o papel de maior volume (3 execuções por mensagem) |
| `api_only` | Tudo na OpenRouter paga (GPT-4o-mini · Claude Haiku 4.5 · Gemini 2.0 Flash) | ~US$ 4 | ~30 min | Tempo de execução é a prioridade, ou o Ollama não está disponível na máquina |

Os três papéis usam modelos de **famílias diferentes** em todos os perfis —
requisito metodológico contra viés de afinidade (o juiz não deve avaliar texto
produzido pelo próprio modelo). O teto de orçamento do projeto é R$ 100
(~US$ 18), com folga confortável sobre os ~US$ 4 do perfil mais caro.

> **Decida o perfil de produção DEPOIS que o smoke test passar e DEPOIS que o
> debate piloto (1 par, 3–4 turnos) validar que os modelos escolhidos produzem
> escalada de hostilidade na condição de controle e moderação coerente na
> condição de tratamento.**

Troca de perfil:

- `export DEBATE_PROFILE=hybrid`
- ou a flag `--profile hybrid` no runner do experimento (adicionada quando o
  runner for implementado)
- ou editar `default_profile` em [`config/models.yaml`](config/models.yaml)

**Temperaturas** (iguais em todos os perfis): debatedor `0.7` (saída variada e
expressiva), moderador `0.2` (julgamento consistente, tolera variação menor),
juiz `0.0` (reprodutibilidade máxima entre as 3 execuções por mensagem).

> **Os slugs gratuitos da OpenRouter mudam com frequência.** O trio original
> da especificação (`llama-3.3-70b:free`, `deepseek-chat-v3.1:free`,
> `gemini-2.0-flash-exp:free`) passou a retornar 404 — os dois primeiros
> viraram pagos, o terceiro foi descontinuado. Os atuais foram verificados em
> 29/08/2026. Se um papel começar a falhar com 404, liste o catálogo com
> `curl https://openrouter.ai/api/v1/models | jq '.data[].id | select(endswith(":free"))'`
> e escolha outro, mantendo **três famílias distintas** (anti-afinidade).
> Isso afeta só o `smoke_test`; os perfis pagos usam slugs estáveis.

**Nota sobre `max_tokens` no `smoke_test`:** moderador e juiz usam orçamentos
maiores (2000 e 600) que nos perfis de produção (800 e 300). O Nemotron é um
modelo de *reasoning* — os tokens de raciocínio são contados antes do JSON de
saída, e com 800 a resposta era truncada no meio do objeto. Perfis pagos
mantêm 800/300.

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
- **A reformulação do D5 preserva incomensurabilidade discursiva** (ex.: descartar a fonte do oponente como "propaganda"), removendo apenas o ataque pessoal. Isso é o desenho operando como especificado — o prompt manda preservar o frame ideológico e mirar o nível 1, não o 0 —, não uma falha. A decisão de **não ajustar os prompts antes do piloto** e o que verificar nele estão em [`docs/moderator_design_decisions.md`](docs/moderator_design_decisions.md).
- Layer 2 (`prompts/debate behavior/debate behavior.txt`) é independente do polo/persona — define como qualquer persona deve se comportar durante o debate (regras de discurso improdutivo, escalada, etc.) e é combinada com o Layer 1 no momento de montar o prompt final do agente.
- Nenhuma dependência de SDK de LLM foi adicionada ainda — a escolha do motor (Anthropic API ou outro) ainda está em aberto e deve ser feita antes dos próximos scripts (debate, moderação, juiz).
- Os dados gerados (`outputs/`) seguem a mesma política do repositório: outputs não são versionados por padrão (ver `.gitignore` na raiz) — exceto quando comitados deliberadamente para fixar o conjunto de personas usado no experimento.
