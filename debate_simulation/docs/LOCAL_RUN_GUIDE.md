# Guia de execução local — debate, moderação e juiz

Guia prático para rodar o experimento com **modelos locais** (Ollama), do
primeiro comando até a leitura dos resultados. Cobre apenas a execução; para
as fases de preparação do dataset e geração de personas, ver
[`../../docs/EXECUTION_GUIDE.md`](../../docs/EXECUTION_GUIDE.md). Para a
justificativa da escolha por modelos locais, ver
[`local_models_decision.md`](local_models_decision.md).

**Todos os comandos assumem diretório de trabalho `debate_simulation/`.**

```bash
cd "/Users/gpcmoura/Documents/Code/MSC/PESC/Disciplinas/CSCW/unproductive-debates-personas /debate_simulation"
```

> O nome da pasta raiz termina com um **espaço**. Sem aspas, o `cd` falha.

---

## Fase 0 — Preparar o ambiente (uma vez só)

### 0.1 Dependências Python

```bash
uv sync
```

### 0.2 Ollama instalado e servidor no ar

```bash
ollama --version          # esperado: 0.33.0 ou superior
curl -s http://localhost:11434/api/version
```

Se o `curl` não responder, suba o servidor **em outro terminal** e deixe-o
aberto:

```bash
ollama serve
```

> **Não feche esse terminal nem use Ctrl+C enquanto estiver rodando o
> experimento** — isso mata o servidor e as chamadas passam a falhar.
> Alternativa: instalar o app do macOS (https://ollama.com/download), que
> mantém o servidor rodando em segundo plano.

### 0.3 Modelos baixados

```bash
ollama list
```

Esperado (~15,4 GB no total):

| Modelo | Papel | Tamanho |
|---|---|---|
| `llama3.1:8b-instruct-q4_K_M` | Debatedor (A) | 4,9 GB |
| `qwen2.5:7b-instruct-q4_K_M` | Moderador D5 (B) | 4,7 GB |
| `gemma2:9b-instruct-q4_K_M` | Juiz (C) | 5,8 GB |

Se faltar algum:

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull gemma2:9b-instruct-q4_K_M
```

### 0.4 Selecionar o perfil local

Há três formas; escolha uma.

```bash
# (a) Variável de ambiente — vale para todos os comandos do terminal atual
export DEBATE_PROFILE=local

# (b) Flag por comando — mais explícito, não depende do estado do shell
uv run python scripts/run_debate.py --profile local ...

# (c) Permanente: editar `default_profile: local` em config/models.yaml
```

Este guia usa a forma **(b)**, a flag `--profile local` em cada comando, para
que cada linha possa ser copiada isoladamente.

### 0.5 Validar

```bash
# Testes offline — não usa modelo nenhum
uv run pytest tests/ -q
#   esperado: 167 passed

# Encanamento — 1 chamada por papel
uv run python scripts/smoke_test.py --profile local
#   esperado: SMOKE TEST PASSED — 3/3 roles reachable
```

> A **primeira chamada a cada modelo** carrega os pesos em memória e demora
> bem mais que as seguintes (dezenas de segundos). Não é travamento.

---

## Fase 1 — Debate sem moderação (condição de controle)

A condição de controle usa **apenas o debatedor**. É a execução mais barata e
a primeira que vale rodar: se as personas não escalarem hostilidade aqui, o
moderador não terá o que moderar.

```bash
uv run python scripts/run_debate.py --profile local \
  --condition control \
  --turns 3
```

**Gera:**

```
experiments/{experiment_id}/
├── manifest.json      ← condições da execução
└── transcript.json    ← o debate
```

**Modelos em memória:** 1 (~5,5 GB).

---

## Fase 2 — Debate com moderação D5 (condição de tratamento)

Acrescenta o moderador: cada mensagem candidata é avaliada antes de ser
publicada e, acima do limiar de hostilidade, reformulada.

```bash
uv run python scripts/run_debate.py --profile local \
  --condition treatment \
  --turns 3
```

**Gera, além do anterior:**

```
└── moderation/
    ├── turn_001_persona_1.json
    ├── turn_002_persona_2.json
    └── turn_003_persona_1.json
```

**Modelos em memória:** 2, alternando por turno (~10,5 GB).

---

## Fase 3 — As duas condições em sequência

```bash
uv run python scripts/run_debate.py --profile local --turns 3
```

Sem `--condition`, o padrão é `both`: roda o controle e depois o tratamento,
sobre o mesmo tema e par, criando **dois** `experiment_id` distintos. É o que
permite comparar.

---

## Fase 4 — Avaliação pelo juiz

O juiz pontua as mensagens **publicadas** na escala 0–4, três vezes cada
(consistência intra-juiz).

```bash
uv run python scripts/run_debate.py --profile local --turns 3 --judge
```

**Gera, adicionalmente:**

```
└── judgements/
    ├── turn_001_persona_1.json
    └── ...
```

Para economizar tempo numa depuração (uma execução por mensagem em vez de
três):

```bash
uv run python scripts/run_debate.py --profile local --turns 3 --judge --judge-runs 1
```

> `--judge-runs 1` **elimina a medida de consistência intra-juiz**, que é
> métrica obrigatória do desenho. Use para depurar, não para produzir dado de
> análise.

**Modelos em memória:** o juiz roda depois do debate (~6,5 GB), mas o modelo
do debatedor pode ainda estar residente. Se houver pressão de memória, rode o
julgamento separado — ver [Fase 6](#fase-6--controle-de-memória).

---

## Fase 5 — Ler os resultados

Tudo aqui lê apenas do disco: **não chama modelo, não custa nada**, pode
rodar quantas vezes quiser.

```bash
# Listar todas as execuções gravadas
uv run python scripts/show_results.py

# A execução mais recente, turno a turno
uv run python scripts/show_results.py --last

# Idem, incluindo as justificativas do moderador e do juiz
uv run python scripts/show_results.py --last --full

# Controle × tratamento lado a lado — o efeito principal
uv run python scripts/show_results.py --compare

# Uma execução específica, pelo id
uv run python scripts/show_results.py 20260901-151435_gun-ownership_pair-00_treatment

# Todas as execuções, em sequência
uv run python scripts/show_results.py --all
```

### Como ler a saída

```
TURN 3  [persona_1]   moderator: hostility=3 ['rhetoric_of_incomprehension']

  CANDIDATE (what the debater wrote):
    Your "concerns" about gun culture are cute, but let's get real...

  PUBLISHED (after reformulation):
    Your concerns about gun culture are valid, but let's focus on...

  JUDGE: median=2  runs=[2, 2, 3]  <- judge disagreed with itself
```

| Elemento | Significado |
|---|---|
| `moderator: hostility=N` | Nota do **moderador** para a candidata (0–4) |
| `CANDIDATE` / `PUBLISHED` | Só aparecem separados quando houve reformulação |
| `JUDGE: median=N` | Mediana das 3 execuções do **juiz**, sobre o texto publicado |
| `runs=[...]` | As três notas individuais |
| `judge disagreed with itself` | As 3 execuções divergiram — sinal de instabilidade |
| `MODERATION FAILED` | O moderador não produziu veredito; a candidata foi publicada sem moderação |
| `! Intervened at hostility_level 1...` | Aviso de inconsistência: o modelo interveio fora da própria regra |

> **A nota do moderador e a do juiz não são comparáveis diretamente.** O
> moderador pontua a *candidata*, antes da publicação; o juiz pontua o que foi
> *publicado*. Quando houve reformulação, são textos diferentes.

### Ler o JSON diretamente

```bash
# Trajetória de hostilidade de uma execução
cat experiments/{experiment_id}/transcript.json | python3 -m json.tool

# Só as notas do juiz, por turno
for f in experiments/{experiment_id}/judgements/turn_*.json; do
  python3 -c "import json,sys; d=json.load(open('$f')); print(d['turn'], d['summary']['scores'])"
done
```

---

## Fase 6 — Controle de memória

Os três modelos somam ~15,4 GB em disco, mas **não precisam estar residentes
ao mesmo tempo**.

```bash
# O que está carregado agora, e até quando
ollama ps

# Descarregar tudo imediatamente
ollama stop llama3.1:8b-instruct-q4_K_M
ollama stop qwen2.5:7b-instruct-q4_K_M
ollama stop gemma2:9b-instruct-q4_K_M

# Pressão de memória do sistema (o número que importa é a porcentagem livre)
memory_pressure | tail -2
```

Por padrão o Ollama mantém um modelo carregado por 5 minutos após o último
uso. Para ajustar:

```bash
export OLLAMA_KEEP_ALIVE=1m     # libera memória mais rápido
export OLLAMA_KEEP_ALIVE=30m    # evita recarregar entre fases
```

**Se a máquina ficar lenta**, rode debate e julgamento separadamente:

```bash
# 1. Debate + moderação, sem juiz (2 modelos)
uv run python scripts/run_debate.py --profile local --turns 3

# 2. Liberar memória
ollama stop llama3.1:8b-instruct-q4_K_M
ollama stop qwen2.5:7b-instruct-q4_K_M

# 3. Julgar depois (1 modelo)
#    NOTA: hoje o julgamento só roda junto com --judge no run_debate.py.
#    Um script separado para julgar transcripts existentes ainda não existe.
```

---

## Parâmetros do experimento

| Flag | Padrão | O que muda |
|---|---|---|
| `--profile` | `smoke_test` | **Use sempre `local`** neste fluxo |
| `--turns N` | 4 | Número de turnos do debate |
| `--condition` | `both` | `control`, `treatment` ou `both` |
| `--judge` | desligado | Ativa a avaliação do juiz |
| `--judge-runs N` | 3 | Execuções do juiz por mensagem |
| `--topic "..."` | `Gun Ownership` | Tema do debate |
| `--pair` | `pair-00` | Identificador do par (só rotula a execução) |
| `--persona-index N` | 0 | **Qual persona usar de cada polo** (0 a 9) |
| `--seed N` | 42 | Registrado no manifest |

### Trocar o tema

Os três temas-âncora da Layer 2:

```bash
uv run python scripts/run_debate.py --profile local --topic "Gun Ownership" --turns 3
uv run python scripts/run_debate.py --profile local --topic "Abortion" --turns 3
uv run python scripts/run_debate.py --profile local --topic "Drug Legalization" --turns 3
```

O tema é texto livre — outros valores funcionam, mas fogem do desenho
declarado no plano.

### Trocar as personas

`--persona-index` seleciona **qual** das 10 personas de cada polo entra no
debate. O índice 0 são as ideologicamente mais coerentes de cada polo; o 9,
as menos.

```bash
# Par 0: persona_00 da esquerda × persona_00 da direita
uv run python scripts/run_debate.py --profile local --persona-index 0 --pair pair-00 --turns 3

# Par 3: persona_03 de cada polo
uv run python scripts/run_debate.py --profile local --persona-index 3 --pair pair-03 --turns 3
```

Use `--pair` coerente com `--persona-index` — ele não seleciona nada, só
rotula a execução no `experiment_id` e no manifest.

### Trocar os modelos

Edite o bloco `local:` em [`../config/models.yaml`](../config/models.yaml).
Para testar se um comportamento é específico de um modelo:

```yaml
  local:
    moderator:
      model: llama3.1:8b-instruct-q4_K_M    # em vez de qwen2.5
```

Baixe o modelo antes (`ollama pull`). Mantenha **três famílias distintas**
entre os papéis — é requisito metodológico de anti-afinidade.

---

## Onde ficam os resultados

```
experiments/{YYYYMMDD-HHMMSS}_{tema}_{par}_{condição}/
├── manifest.json          ← modelos, personas, SHA-256 dos prompts, seed
├── transcript.json        ← candidata e texto publicado por turno
├── moderation/            ← só no tratamento
│   └── turn_NNN_persona_N.json
└── judgements/            ← só com --judge
    └── turn_NNN_persona_N.json
```

Cada execução cria um diretório novo — **nada é sobrescrito**. Turnos
repetidos recebem sufixo numérico; falhas viram `*_FAILED.json`, nunca são
omitidas.

| Arquivo | Quando consultar |
|---|---|
| `manifest.json` | Sob quais condições o dado foi produzido |
| `transcript.json` | Visão geral do debate |
| `moderation/turn_*.json` | Auditar uma reformulação: justificativa, `argument_preserved`, histórico visto pelo moderador |
| `judgements/turn_*.json` | As 3 notas do juiz e o resumo derivado |
| `*_FAILED.json` | Diagnosticar uma falha |

---

## Receitas comuns

```bash
# Piloto completo, as duas condições, com juiz
uv run python scripts/run_debate.py --profile local --turns 3 --judge
uv run python scripts/show_results.py --compare

# Só verificar se as personas escalam hostilidade (mais barato)
uv run python scripts/run_debate.py --profile local --condition control --turns 6
uv run python scripts/show_results.py --last

# Debate longo, sem juiz, para inspecionar a moderação
uv run python scripts/run_debate.py --profile local --condition treatment --turns 8
uv run python scripts/show_results.py --last --full

# Testar outro tema e outro par
uv run python scripts/run_debate.py --profile local \
  --topic "Abortion" --pair pair-02 --persona-index 2 --turns 3 --judge
```

---

## Problemas conhecidos

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Connection refused` / `APIConnectionError` | Servidor Ollama parado | `ollama serve` em outro terminal |
| Primeira chamada muito lenta | Carregamento dos pesos | Normal; as seguintes são rápidas |
| Máquina lenta, ventilador alto | Dois modelos residentes | `ollama ps`, depois `ollama stop <modelo>` |
| `model not found` | Modelo não baixado | `ollama pull <modelo>` |
| `usage: null` nos registros | Ollama nem sempre reporta tokens | Esperado; a latência continua sendo medida |
| `Intervened at hostility_level 1, below the threshold of 2` | O moderador contrariou a própria regra | **Não é bug** — é dado sobre o modelo, registrado de propósito |
| Reformulação inverte a posição da persona | Modelo pequeno higienizando demais | Achado do piloto; ver [`moderator_design_decisions.md`](moderator_design_decisions.md) |
| Juiz dá a mesma nota a tudo | Saturação da escala | Inspecionar com `--full`; pode exigir calibração do prompt |

---

## O que verificar no piloto

Antes de rodar o experimento completo, quatro perguntas que esta rodada
responde:

1. **As personas escalam hostilidade no controle?** Se não, os guardrails dos
   modelos 7–9B estão suprimindo o fenômeno e o experimento não se sustenta
   com esses modelos.
2. **O moderador respeita o próprio limiar?** Conte os
   `consistency_warning` — intervenções abaixo de 2 indicam moderador zeloso
   demais.
3. **A reformulação preserva o argumento?** Compare `CANDIDATE` e `PUBLISHED`
   com `--full`. Se a posição da persona muda, o D5 está apagando o dissenso
   em vez de moderar a hostilidade.
4. **O juiz é consistente e discrimina?** Procure `judge disagreed with
   itself` e verifique se notas diferentes aparecem para turnos de
   hostilidade visivelmente diferente.