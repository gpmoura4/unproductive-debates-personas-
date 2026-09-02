# Decisão de design — execução com modelos locais

Este documento registra a decisão de executar o experimento com modelos
rodando localmente (via [Ollama](https://ollama.com)) em vez da API gratuita
da OpenRouter, a evidência empírica que motivou a mudança, e as implicações
metodológicas. Destina-se à seção de método e à declaração de limitações do
artigo.

Para as decisões sobre o conteúdo dos prompts, ver
[`persona_prompt_design_decisions.md`](persona_prompt_design_decisions.md),
[`debate_behavior_design_decisions.md`](debate_behavior_design_decisions.md) e
[`moderator_design_decisions.md`](moderator_design_decisions.md).

---

## 1. O que motivou a mudança: instabilidade do free tier

### Evidência observada

O pipeline foi implementado e validado com o perfil `smoke_test` (modelos
`:free` da OpenRouter). Três classes de falha apareceram na tentativa de
produzir a primeira rodada piloto real (agosto–setembro de 2026):

**(a) Rotatividade de slugs.** O trio originalmente especificado
(`llama-3.3-70b:free`, `deepseek-chat-v3.1:free`,
`gemini-2.0-flash-exp:free`) passou a retornar 404 durante o desenvolvimento:
os dois primeiros migraram para acesso pago, o terceiro foi descontinuado.
Foi necessário reescolher os três modelos e reverificar o catálogo.

**(b) Cota diária não documentada na especificação inicial.** O free tier
impõe **50 requisições por dia** por conta, além do limite por minuto. Uma
célula completa do experimento (1 tema × 1 par × 12 turnos × 2 condições, com
juiz) custa **108 chamadas** — mais que o dobro da cota diária. O experimento
completo (3 temas × 10 pares) custa ~3.240 chamadas, o que no free tier levaria
cerca de 65 dias.

**(c) Indisponibilidade do pool compartilhado — a falha determinante.** Os
modelos `:free` são servidos por um pool compartilhado entre todos os usuários
da plataforma. Em execuções sucessivas do piloto, a condição de **tratamento
falhou repetidamente**, sempre no papel do moderador, com duas famílias de
modelo diferentes:

| Modelo do moderador | Erro retornado |
|---|---|
| `nvidia/nemotron-3-super-120b-a12b:free` | HTTP 502 — `Upstream error from Nvidia: Service temporarily overloaded` |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | HTTP 502 — `ResourceExhausted: Worker local total request limit reached (16/16)` |
| `google/gemma-4-26b-a4b-it:free` | HTTP 429 — `temporarily rate-limited upstream`, `limit_source: upstream_provider_shared_pool` |

O padrão foi sistemático: a condição de **controle** (que usa apenas o
debatedor) completou com sucesso; a de **tratamento** (que adiciona o
moderador) abortou no primeiro turno. Trocar o modelo do moderador não
resolveu — apenas mudou o provedor que falhava.

**(d) Comportamento não determinístico de roteamento.** O smoke test, ao
perguntar a identidade do modelo, recebeu respostas inconsistentes entre
execuções do mesmo slug (`"I am the moderator model, Nemotron"` numa
execução, `"I am not a moderator model; I am ChatGPT"` em outra). Modelos são
sabidamente pouco confiáveis ao se autoidentificar, mas a inconsistência é
compatível com fallback de roteamento da plataforma sob saturação — o que
significa que **não há garantia de qual modelo produziu cada resposta**.

### Por que (c) e (d) são fatais para o experimento, não apenas inconvenientes

O ponto (b) é um problema de tempo: contornável com crédito pago. Os pontos
(c) e (d) atingem a validade:

1. **Viés de disponibilidade.** Se a condição de tratamento falha mais que a
   de controle — porque exige um modelo a mais, e portanto tem mais chances de
   esbarrar em indisponibilidade —, os dados sobreviventes não são uma amostra
   aleatória das execuções tentadas. Debates de tratamento que "deram certo"
   podem diferir sistematicamente dos que falharam (por exemplo, os que
   rodaram em horários de menor carga).
2. **Impossibilidade de atribuir a resposta a um modelo.** O desenho exige
   **anti-afinidade**: debatedor, moderador e juiz devem ser de famílias
   distintas, para que o juiz não avalie texto produzido pelo próprio modelo
   (Seção 8.2 do plano). Se a plataforma pode redirecionar silenciosamente uma
   chamada para outro modelo sob saturação, essa garantia não se sustenta.
3. **Irreprodutibilidade.** Um slug `:free` pode virar pago, ser
   descontinuado, ou ter seu modelo subjacente atualizado sem aviso. Um
   terceiro que tentasse replicar o experimento meses depois não teria como
   executar a mesma configuração — o que é um problema para um artigo.

---

## 2. Decisão

**O experimento passa a ser executado com modelos locais (perfil `local`),
via Ollama.** O perfil `smoke_test` permanece no repositório, mas com escopo
redefinido: validação de encanamento (o código alcança os modelos, o formato
de resposta é o esperado), **não** produção de dado experimental.

### Configuração adotada

| Papel | Modelo | Quantização | Disco | RAM aprox. |
|---|---|---|---|---|
| Debatedor (A) | `llama3.1:8b-instruct-q4_K_M` | Q4_K_M | 4,9 GB | ~5,5 GB |
| Moderador D5 (B) | `qwen2.5:7b-instruct-q4_K_M` | Q4_K_M | 4,7 GB | ~5,0 GB |
| Juiz (C) | `gemma2:9b-instruct-q4_K_M` | Q4_K_M | 5,8 GB | ~6,5 GB |

Três famílias distintas (Meta · Alibaba · Google), preservando o requisito de
anti-afinidade.

### Justificativa das escolhas

- **Llama 3.1 8B como debatedor.** Entre os modelos abertos desse porte, é o
  que impõe menos recusa a conteúdo conflituoso — relevante porque a Layer 2
  exige justamente que a persona produza hostilidade crescente. Um debatedor
  que recusa esvazia o fenômeno a ser medido.
- **Qwen 2.5 7B como moderador.** Bom desempenho em seguimento de formato
  estruturado (a saída do D5 é um contrato JSON com seis campos), que é a
  exigência dominante desse papel.
- **Gemma 2 9B como juiz.** Ver seção 3.
- **Quantização Q4_K_M** em todos: o ponto de equilíbrio usual entre
  degradação de qualidade e consumo de memória. Q8_0 dobraria a RAM sem ganho
  proporcional para tarefas de classificação com rubrica explícita.

### Gestão de memória (restrição de hardware)

O ambiente de execução declarado é um **MacBook Air M2 com 24 GB de memória
unificada**. Os três modelos somam ~15,4 GB em disco, mas **não precisam estar
residentes simultaneamente**:

- **Fase de debate + moderação:** dois modelos ativos, alternando por turno
  (~10,5 GB).
- **Fase de julgamento:** um modelo ativo (~6,5 GB), executada como passo
  separado, depois que o debate terminou.

Isso mantém o pico de uso bem abaixo da capacidade da máquina. O Ollama
mantém um modelo carregado por 5 minutos após o último uso
(`OLLAMA_KEEP_ALIVE`) e o descarrega sob pressão de memória.

---

## 3. Todos os papéis usam SLMs — e por que isso é mais defensável no juiz

### Esclarecimento

Uma formulação anterior deste documento sugeria "SLM como juiz" em contraste
com os demais papéis. Isso é impreciso: na configuração adotada, **os três
papéis rodam modelos de 7–9B**, faixa que a literatura trata como *small
language models*. Não há contraste entre um juiz pequeno e debatedor/moderador
grandes.

A razão é a restrição de hardware declarada (24 GB de memória unificada): um
modelo de 30B+ quantizado em Q4 exigiria ~20 GB residentes, inviabilizando a
execução junto com o sistema operacional e um segundo modelo.

Consequência para o artigo: a limitação "modelos de porte reduzido" vale para
**toda a cadeia**, não apenas para a avaliação, e deve ser declarada nesses
termos.

### Por que o uso de SLM é mais defensável no juiz que nos demais papéis

Ainda que a escolha seja imposta pelo hardware, ela é metodologicamente mais
justificável no papel de juiz:

1. **A tarefa é classificação com rubrica, não geração aberta.** O prompt do
   juiz fornece a escala 0–4 com descrição explícita de cada nível e as três
   categorias de patologia. O trabalho conceitual está na rubrica; o que se
   pede ao modelo é aplicá-la de forma consistente. É o tipo de tarefa em que
   a distância entre modelos pequenos e grandes é menor.
2. **É o papel de maior volume.** O juiz executa **3 vezes por mensagem
   publicada** — 72 das 108 chamadas de uma célula completa (67%). É onde o
   custo de inferência mais pesa, e portanto onde um modelo menor mais rende.
3. **Consistência intra-juiz é a métrica obrigatória** (Seção 8.4 do plano).
   Com `temperature: 0.0`, um modelo menor tende a produzir saída mais estável
   entre execuções repetidas do mesmo input — que é exatamente o que essa
   métrica mede.
4. **Evidência contrária ao "modelo maior é melhor".** Nas execuções com API,
   o juiz grande (`cohere/north-mini-code:free`) atribuiu nota **3 a todas as
   mensagens de um debate**, unanimemente nas 9 execuções — sem discriminar
   entre turnos de hostilidade visivelmente diferente. Em outra execução,
   discordou de si mesmo em 2 de 3 turnos (`[4,3,4]`, `[3,4,4]`) apesar de
   `temperature: 0.0`. Nem consistência nem poder discriminativo foram
   garantidos pelo tamanho: o que os determina é a calibração da rubrica.

**Trade-off reconhecido:** um modelo menor pode ter menor capacidade de
detectar hostilidade sutil ou dependente de contexto (ironia que exige
conhecimento cultural, por exemplo). Essa limitação é mitigada — não
eliminada — pela auditoria humana de 30 pares prevista na Seção 8.4, e deve
ser declarada nas limitações do artigo.

**A validar no piloto:** se o juiz local saturar (atribuir a mesma nota a
mensagens de hostilidade claramente distinta) ou apresentar amplitude alta
entre as 3 execuções, o prompt do juiz precisa de calibração **antes** da
execução completa — não o modelo precisa ser trocado por um maior.

---

## 4. Riscos da execução local, e o que verificar

| Risco | Como se manifesta | Como verificar no piloto |
|---|---|---|
| **Guardrails suprimem a hostilidade** | O debatedor recusa ou amacia; o debate não escala e o D5 não tem o que moderar | Rodar a condição de **controle primeiro** e inspecionar a trajetória de hostilidade. Se não escalar, o experimento não se sustenta com esses modelos |
| **Aderência fraca ao formato JSON** | Moderador/juiz produzem texto não parseável; sobe a taxa de `parse_recovery_used` | O campo `parse_strategy` é gravado em cada registro. Uma taxa alta de `retry_call` indica modelo inadequado ao papel |
| **Juiz satura a escala** | Todas as mensagens recebem a mesma nota | Comparar as notas do juiz entre turnos e entre condições |
| **Tempo de execução** | ~4 h estimadas para o experimento completo, contra ~30 min na API paga | Medir `latency_ms` no piloto e extrapolar |

O primeiro risco é o mais sério e o mais barato de testar: a condição de
controle exige apenas o debatedor.

---

## 5. Ganhos metodológicos (por que isto não é apenas um contorno)

A migração para modelos locais foi motivada por falhas operacionais, mas
melhora a qualidade metodológica do trabalho em três frentes — e deve ser
apresentada no artigo como decisão de método, não como plano de contingência:

1. **Reprodutibilidade.** Os modelos são identificados por tag e quantização
   (`llama3.1:8b-instruct-q4_K_M`), com pesos imutáveis. Um terceiro pode
   baixar exatamente os mesmos artefatos e reexecutar o experimento — o que
   não é possível com slugs de API que mudam ou desaparecem.
2. **Atribuição garantida.** Não há camada de roteamento entre a chamada e o
   modelo: a garantia de anti-afinidade entre debatedor, moderador e juiz
   passa a ser verificável, não confiada a um intermediário.
3. **Ausência de viés de disponibilidade.** Toda célula planejada pode ser
   executada; nenhuma condição experimental falha com mais frequência que
   outra por razões alheias ao desenho.

Some-se a isso custo zero e independência de cota, que tornam viável rodar o
experimento completo — e repeti-lo, se os prompts forem recalibrados após o
piloto.

**Limitação a declarar no artigo:** os modelos locais de 7–9B quantizados são
menos capazes que os modelos de fronteira usados em trabalhos comparáveis. Os
resultados devem ser lidos como obtidos nessa classe de modelos, e não
extrapolados sem verificação para sistemas de produção baseados em modelos
maiores.