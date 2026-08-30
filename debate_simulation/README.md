# debate_simulation

Simulação de debates políticos improdutivos usando personas de debate geradas a partir do MatrAIx Persona 1M. Cobre a geração de prompts de persona, o fluxo de debate com moderação, e um juiz que avalia se a hostilidade/moderação foi respeitada.

Este subprojeto consome os outputs de [`../dataset_analysis/`](../dataset_analysis/) (especificamente `phase2_decoded_personas.json`) e é independente em dependências — não compartilha `.venv` nem `pyproject.toml` com a análise do dataset.

## Estado atual

- ✅ Geração de prompts de persona (Layer 1 — identidade ideológica, em inglês) a partir dos atributos decodificados (polo esquerda/direita), com rastreamento de origem separado em `persona_metadata.json`.
- ✅ Layer 2 (comportamento de debate improdutivo) definida estaticamente em [`prompts/debate behavior/debate behavior.txt`](prompts/debate%20behavior/debate%20behavior.txt) — não gerada por script.
- ✅ Configuração de modelos por perfil ([`config/models.yaml`](config/models.yaml)) para os três papéis (debatedor, moderador D5, juiz), com 4 perfis selecionáveis e verificação de credenciais só para os provedores que o perfil usa.
- ✅ Cliente LLM único ([`src/llm/client.py`](src/llm/client.py)) para OpenRouter e Ollama (ambos expõem endpoints compatíveis com a API da OpenAI), com retry exponencial em falhas transitórias e captura de latência/uso de tokens.
- ✅ Smoke test ([`scripts/smoke_test.py`](scripts/smoke_test.py)) — valida que os três papéis alcançam seus modelos, sem depender do loop de debate.
- ✅ Simulação do debate entre personas ([`src/debater/`](src/debater/)) — composição Layer 1 + Layer 2 num prompt de sistema e geração de turnos.
- ✅ Loop de debate ([`src/debate/loop.py`](src/debate/loop.py)) — alterna as personas nas duas condições (controle e tratamento), grava `transcript.json` e retoma de um histórico existente.
- ✅ Fluxo de moderação D5 ([`src/moderator/`](src/moderator/)) — schemas, montagem de prompt, orquestração (`D5Moderator.moderate()`) e parsing tolerante da resposta JSON. Decisões de design em [`docs/moderator_design_decisions.md`](docs/moderator_design_decisions.md).
- ✅ Log das moderações ([`src/moderator/logger.py`](src/moderator/logger.py)) — manifest por execução + um JSON por turno em `experiments/{experiment_id}/`, gravados incrementalmente e nunca sobrescritos.
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

## Testes

```bash
uv run pytest tests/ -v
```

137 testes, **totalmente offline** — o cliente LLM é substituído por um duplo
que devolve respostas roteirizadas, então a suíte roda sem chave de API, sem
rede e sem custo. Rode antes de qualquer execução com modelos reais.

| Arquivo | Cobre |
|---|---|
| [`tests/test_config.py`](tests/test_config.py) | Resolução de perfis, precedência (flag → env → YAML), verificação seletiva de credenciais |
| [`tests/test_prompt.py`](tests/test_prompt.py) | Montagem da mensagem do moderador, ordenação do histórico, e o **blinding** (nenhum rótulo de polo/orientação política na mensagem) |
| [`tests/test_moderator.py`](tests/test_moderator.py) | Cascata de parsing, retentativa única, validação do contrato, resolução do texto publicado, aviso de consistência |
| [`tests/test_logger.py`](tests/test_logger.py) | Manifest, registros por turno, não-sobrescrita, registros de falha, leitura de estado para retomada |
| [`tests/test_debater.py`](tests/test_debater.py) | Composição Layer 1 + Layer 2, rótulos YOU/OPPONENT, limpeza da mensagem, blinding da Layer 1 |
| [`tests/test_debate_loop.py`](tests/test_debate_loop.py) | Alternância de turnos, as duas condições, propagação da reformulação, falha de moderação, retomada, transcript |

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

## Rodada de debate (piloto)

```bash
# As duas condições, 4 turnos cada, no mesmo tema e par
uv run python debate_simulation/scripts/run_debate.py --turns 4

# Só uma condição
uv run python debate_simulation/scripts/run_debate.py --condition treatment

# Outro tema / par / persona
uv run python debate_simulation/scripts/run_debate.py --topic "Abortion" --pair pair-01 --persona-index 1
```

Produz **dado experimental real** — cada execução grava `manifest.json`,
`transcript.json` e (no tratamento) um registro por turno em `moderation/`.
Comece pequeno: o padrão são 4 turnos, que é o piloto "1 par, 3–4 turnos" do
desenho, não a execução completa de 12.

O ciclo por turno:

```
debatedor gera candidata
  → tratamento: moderador D5 pontua e, acima do limiar, reformula
  → controle:   a candidata é publicada sem alteração
  → o texto publicado entra no transcript
  → o oponente responde ao que foi publicado
```

Esse último passo é o que propaga o efeito do D5: o oponente responde à
mensagem que **passou**, não à que foi tentada.

**Falha de moderação não aborta o debate.** Se o moderador não produzir um
veredito utilizável nem após a retentativa, a candidata é publicada e o turno
fica marcado com `moderated: false` (e listado em `unmoderated_turns`). Uma
execução de tratamento pode, portanto, conter turnos não moderados — calcular
a hostilidade média sem excluí-los subestimaria o efeito da intervenção.

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
| `experiments/{experiment_id}/manifest.json` | `src/moderator/logger.py` | Condições da execução: personas (com proveniência MatrAIx), modelos, SHA-256 dos prompts, threshold, seed |
| `experiments/{experiment_id}/moderation/turn_NNN_persona_N.json` | `src/moderator/logger.py` | Um registro por mensagem avaliada: candidata, snapshot do histórico, veredito, texto publicado, metadados da chamada |
| `experiments/{experiment_id}/transcript.json` | `src/debate/loop.py` | O debate publicado: candidata e texto publicado por turno, hostilidade, se houve reformulação, turnos não moderados |

### Rastreabilidade das execuções

Cada execução vive em `experiments/{experiment_id}/`, com
`experiment_id` no formato `{YYYYMMDD-HHMMSS}_{tema}_{par}_{condição}` —
ex.: `20260830-144831_gun-ownership_pair-00_treatment`.

- **Gravação incremental.** Cada turno é escrito assim que termina; uma falha no turno 11 não custa os 10 anteriores (requisito §8.3 do desenho experimental).
- **Nunca sobrescreve.** Um turno repetido recebe sufixo numérico (`turn_003_persona_1_2.json`) — ambas as tentativas são dado.
- **Falhas são registradas**, não omitidas: `turn_NNN_persona_N_FAILED.json` guarda a resposta bruta, o tipo e a mensagem da exceção. Um arquivo ausente seria indistinguível de um turno que nunca rodou.
- **`history_snapshot`** guarda o histórico exato que o moderador viu naquele turno. Custa disco, mas torna cada registro auditável isoladamente — necessário para a auditoria humana dos 30 pares.
- **Proveniência MatrAIx** (`matraix_source`, `matraix_id`) vive **só no manifest**, nunca em prompt enviado a um modelo — é o elo interno de rastreabilidade, e o *political-lean blinding* depende dessa separação.
- **SHA-256 dos prompts** no manifest e em cada registro provam qual versão exata produziu a execução, o que importa porque os prompts congelam ao fim da Semana 1.
- **`parse_strategy`** registra como o JSON foi recuperado da resposta (`direct`, `fence_stripped`, `block_extracted`, `retry_call`). A taxa de recuperação é um achado sobre o modelo, não só um detalhe de implementação — modelos de *reasoning* como o Nemotron raciocinam antes de emitir o JSON.

### Retomada

O logger também lê o que já existe, para o runner continuar de onde parou:

| Método | Devolve |
|---|---|
| `exists()` | Se a execução já foi iniciada (manifest presente) |
| `completed_turns()` | Pares `(turn, persona_id)` concluídos com sucesso |
| `failed_turns()` | Pares cuja moderação falhou — **devem ser refeitos**, não pulados |
| `last_completed_turn()` | Maior número de turno registrado, ou 0 |
| `load_published_history()` | O transcript publicado, em ordem de turno, para retomar o debate |
| `find_runs(topic, pair_id, condition)` | Execuções existentes de uma célula do experimento |

`load_published_history()` devolve o texto **efetivamente publicado** — a
reformulação quando houve intervenção —, que é o que o oponente respondeu.
Retomar a partir da candidata original quebraria o loop do D5.

## Notas

- As personas atuais vêm de uma amostra do coreset MatrAIx (10 por polo, selecionadas por uma regra de coerência ideológica multi-indicador) — ver a regra em `../dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md` e os números de cobertura/exclusão em `../dataset_analysis/outputs/phase2_decode_report.md`.
- Os prompts (Layer 1) são gerados apenas a partir dos atributos categóricos decodificados (`political_attributes`) — o dataset não fornece biografia/nome para essas personas, então os prompts são deliberadamente enxutos. Todos os textos são gerados em inglês e não contêm nenhuma referência à fonte/ID do dataset original; essa informação de proveniência vive só em `persona_metadata.json`.
- **O alinhamento político é omitido do texto do prompt** (*political-lean blinding*): nem `political_lean` nem o rótulo do polo aparecem no `.txt`. A persona é descrita só por suas posições substantivas, para evitar que o modelo encene o estereótipo associado ao rótulo em vez de derivar a postura dos atributos amostrados. O valor continua em `persona_metadata.json` (`blinded_attributes`) e na estrutura de diretórios — o ocultamento vale para o agente, não para nós. Justificativa em [`docs/persona_prompt_design_decisions.md`](docs/persona_prompt_design_decisions.md).
- **A reformulação do D5 preserva incomensurabilidade discursiva** (ex.: descartar a fonte do oponente como "propaganda"), removendo apenas o ataque pessoal. Isso é o desenho operando como especificado — o prompt manda preservar o frame ideológico e mirar o nível 1, não o 0 —, não uma falha. A decisão de **não ajustar os prompts antes do piloto** e o que verificar nele estão em [`docs/moderator_design_decisions.md`](docs/moderator_design_decisions.md).
- Layer 2 (`prompts/debate behavior/debate behavior.txt`) é independente do polo/persona — define como qualquer persona deve se comportar durante o debate (regras de discurso improdutivo, escalada, etc.) e é combinada com o Layer 1 no momento de montar o prompt final do agente.
- Nenhuma dependência de SDK de LLM foi adicionada ainda — a escolha do motor (Anthropic API ou outro) ainda está em aberto e deve ser feita antes dos próximos scripts (debate, moderação, juiz).
- Os dados gerados (`outputs/`) seguem a mesma política do repositório: outputs não são versionados por padrão (ver `.gitignore` na raiz) — exceto quando comitados deliberadamente para fixar o conjunto de personas usado no experimento.
