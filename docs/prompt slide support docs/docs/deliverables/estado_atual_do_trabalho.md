# Estado atual do trabalho — conteúdo de referência

Documento-fonte para produção de slides de acompanhamento com o orientador.
Resume o que foi feito, decidido e por quê, do dataset até a fase atual.

- **Trabalho:** "Moderar antes de publicar: simulação com agentes LLM polarizados para avaliar a Moderação Participativa em debates improdutivos" (título provisório)
- **Continuidade de:** Moura e Brandi (2026) — *From Hostility to Deliberation: A Sociotechnical Model for Mitigating Unproductive Debates in AI-Mediated Social Media* (CHIRA 2026)
- **Posição no cronograma:** início da Semana 1 de 4. Fases 0–3 do pipeline concluídas; rodada de teste inicial, rodada piloto e congelamento dos prompts pendentes.

---

## 1. Contexto e pergunta de pesquisa

### 1.1 De onde isso vem

O trabalho anterior (Moura e Brandi, 2026) propôs um modelo sociotécnico com
cinco dimensões de mitigação de debates improdutivos (D1–D5), atravessadas
por uma camada de mediação por IA Generativa. O modelo foi validado apenas de
forma **ilustrativa**, sobre um caso empírico único (uma seção de comentários
do Instagram) — demonstração de plausibilidade analítica, não validação
empírica.

Este trabalho dá continuidade testando **uma** dessas dimensões em ambiente
controlado.

### 1.2 Por que D5 (Moderação Participativa), e por que simular

D5 atua **antes da postagem**: a IA sinaliza hostilidade e oferece
reformulação antes que a mensagem seja publicada. Sobre uma thread já
coletada, só seria possível uma sinalização *retrospectiva* — uma versão
empobrecida da dimensão.

Simular o debate com agentes permite inserir o moderador **dentro do loop**,
na posição temporal para a qual foi projetado. Além disso, dispensa sujeitos
humanos (e, portanto, aprovação de CEP).

D2 (Estruturação Argumentativa) foi descartada como alvo porque funcionaria
igualmente sobre thread real ou simulada — a simulação agregaria pouco.

### 1.3 Pergunta de pesquisa

> Em um debate improdutivo simulado por agentes LLM polarizados, a inserção de
> um moderador D5 no loop de interação reduz a trajetória de hostilidade **sem
> destruir o conteúdo argumentativo** das mensagens?

### 1.4 O que a simulação não responde (recorte declarado)

A objeção "intervenção de IA em tempo real costuma não funcionar" diz respeito
a **como humanos reagem**. Trocar humanos por agentes não responde a isso —
desloca a pergunta para "o mecanismo funciona sobre debatedores simulados?",
que é a pergunta anterior, mais barata e necessária. O artigo assume esse
recorte explicitamente.

---

## 2. Fundamentação teórica: as três patologias de Angenot

Marc Angenot argumenta que a incompreensão mútua em debates não deriva de
ignorância, falta de lógica ou má-fé dos participantes, mas é uma **condição
estrutural da vida social** — o "diálogo de surdos". Daí decorrem três
categorias analíticas, que estruturam todo o experimento:

| Categoria | Definição | Referência |
|---|---|---|
| **Incomensurabilidade discursiva** | Participantes operam em "universos discursivos" incompatíveis — não compartilham valores, pressupostos ou critérios sobre o que constitui verdade | Angenot (2010) |
| **Retórica da incompreensão** | Recusa ou incapacidade de reconhecer o adversário como ser racional dentro do próprio sistema de pensamento; degenera em ataque, ironia, caricatura e deslegitimação | Angenot (2008) |
| **Ilusão da racionalidade** | Expectativa irrealista de que o debate tende ao consenso ou de que é possível "convencer o outro"; na prática argumenta-se para a própria audiência, em monólogos paralelos | Angenot (2008) |

**Referências completas:**
- ANGENOT, M. *Dialogues de sourds: Traité de rhétorique antilogique*. Mille et une nuits, Paris (2008)
- ANGENOT, M. *El discurso social: Los límites históricos de lo pensable y lo decible*. Siglo XXI Editores, Buenos Aires (2010)
- ANGENOT, M. *Divergent reasonings and dialogues of the deaf: Why do we often find others "irrational"?* Keynote lecture, University of Alberta (2006)

Essas três categorias são o que o experimento precisa **provocar de forma
controlada** para depois testar se D5 as mitiga.

---

## 3. O dataset: MatrAIx Persona 1M

### 3.1 O que é

- ~1 milhão de personas sintéticas estruturadas (Li et al., 2026 — arXiv:2608.04205)
- **1.290 dimensões categóricas** por persona
- *Grounding* em surveys reais: World Values Survey, General Social Survey (GSS), Latinobarometro, Pew Research
- Reporta 91,5% de aderência comportamental em tarefas de avaliação de produtos digitais

### 3.2 O que é relevante para nós

O subgrupo **Psychology → Worldview → Beliefs** (67 dimensões) inclui
explicitamente orientação política, religiosidade, confiança institucional e
valores — calibrados inclusive com Latinobarometro, relevante para contexto
latino-americano.

### 3.3 Desafio técnico: os atributos vêm compactados

Cada persona armazena as 1.290 dimensões em um **BLOB de 645 bytes**
(4 bits/nibble por dimensão), mais um `null_bitmap` de 162 bytes indicando
dimensões nulas.

Foi necessário descobrir e validar empiricamente a convenção de decodificação:

- **nibble "low-first"**: índice par → `byte & 0x0F`; índice ímpar → `byte >> 4`
- **null_bitmap**: bit = 0 significa "dimensão populada"; bit = 1 significa "nula"

A convenção foi **validada contra o campo `descriptions`** (texto livre gerado
para a mesma persona), comparando valor decodificado × descrição em linguagem
natural. Evidência registrada em `outputs/phase2_decode_validation.md`.

---

## 4. Pipeline construído (Fases 0–3)

```
dataset_analysis/                              debate_simulation/
─────────────────                              ──────────────────
Fase 0 — schema + dimensões políticas
   │  00_download_schema.py
   │  01_inspect_schema.py
   ▼
Fase 1 — download de shards Parquet
   │  02_explore_parquet.py
   ▼
Fase 2 — decodificação + classificação
         de polos (esquerda/direita)   ───►    Fase 3 — geração de prompts
   │  03_decode_attributes.py                   Camada 1
   ▼                                            00_generate_persona_prompts.py
phase2_decoded_personas.json                          │
                                                      ▼
                                        outputs/prompts/personas/
                                          ├── persona_metadata.json
                                          ├── polo_esquerda/persona_NN.txt
                                          └── polo_direita/persona_NN.txt
```

**Números do funil:**

| Etapa | Quantidade |
|---|---|
| Personas no coreset completo | ~1.000.000 |
| Registros nos 2 shards baixados | 200.000 |
| Amostra decodificada (seed fixa = 42) | 2.000 |
| Com `political_lean` não nulo | 399 (19,95%) |
| Elegíveis polo esquerda (modo strict) | 101 |
| Elegíveis polo direita (modo strict) | 20 |
| **Selecionadas para o experimento** | **10 + 10 = 20** |

---

## 5. Decisão central 1 — Regra de classificação esquerda/direita

### 5.1 O problema encontrado

A primeira versão do filtro classificava por **um único campo**:

```python
if lean in ("Left", "Center-left"):
    left_profiles.append(r)
elif lean in ("Right", "Center-right"):
    right_profiles.append(r)
```

Nenhuma verificação de coerência com os outros 9 atributos. Consequências
reais encontradas nos dados gerados:

- **`Q55759875`** entrou no polo esquerda com `political_lean=Center-left`,
  mas `religiosity=Devout` e **todos** os demais atributos `Neutral` — um
  único sinal isolado sustentando a classificação.
- **`Q50318212`** entraria no polo direita com `political_lean=Right`, mas
  `att_government_regulation=Enthusiast` **e** `att_labor_unions=Enthusiast`
  — posições tipicamente de esquerda econômica. Perfil "entusiasta de tudo",
  internamente contraditório.

Para o experimento isso é grave: o efeito medido fica diluído por personas que
são "esquerda"/"direita" apenas nominalmente, e prompts internamente
contraditórios geram comportamento não atribuível de forma limpa a um polo.

### 5.2 A regra construída, fundamentada na literatura

Três obras principais sustentam o mapeamento:

| Obra | Contribuição |
|---|---|
| **BOBBIO (1994/1995)** — *Direita e esquerda* | Critério definidor clássico: **atitude frente à igualdade**. Esquerda = concepção horizontal/igualitária; Direita = concepção vertical/hierárquica. O centro é *terzo incluso* (meio incluído), não polo. → fundamenta a **âncora** e os **indicadores nucleares** |
| **JOST et al. (2003)** — *Political conservatism as motivated social cognition* | Meta-análise (88 amostras, 12 países, 22.818 casos). Núcleo do conservadorismo = **resistência à mudança** + **justificação da desigualdade**. → fundamenta os **indicadores periféricos** do eixo social |
| **PIURKO, SCHWARTZ & DAVIDOV (2011)** — *Basic personal values and the meaning of left-right political orientations in 20 countries* | Com European Social Survey e teoria de valores de Schwartz: universalismo/benevolência predizem esquerda; conformidade/tradição predizem direita. → fundamenta o mapeamento de `values_priority` |

Obra de apoio: **FELDMAN & JOHNSTON (2014)** demonstra que duas dimensões
(econômica e social) são o mínimo para explicar preferências políticas — daí a
separação entre indicadores **nucleares** e **periféricos**.

### 5.3 Estrutura da regra

**Âncora obrigatória** (`political_lean`): `Left`/`Center-left` → esquerda;
`Right`/`Center-right` → direita. `Center`, `Apolitical` e nulo são excluídos.

**Indicadores nucleares — eixo econômico** (contradição aqui **elimina** o registro):

| Campo | Esquerda (−1) | Direita (+1) | Neutro |
|---|---|---|---|
| `att_free_markets` | Skeptical, Opposed | Positive, Enthusiast | Neutral, nulo |
| `att_government_regulation` | Positive, Enthusiast | Skeptical, Opposed | Neutral, nulo |
| `att_labor_unions` | Positive, Enthusiast | Skeptical, Opposed | Neutral, nulo |

**Indicadores periféricos — eixo social e valores** (contradição tolerada conforme modo):

| Campo | Esquerda (−1) | Direita (+1) | Neutro |
|---|---|---|---|
| `att_immigration` | Positive, Enthusiast | Skeptical, Opposed | Neutral, nulo |
| `att_gun_ownership` | Skeptical, Opposed | Positive, Enthusiast | Neutral, nulo |
| `att_capital_punishment` | Skeptical, Opposed | Positive, Enthusiast | Neutral, nulo |
| `values_priority` | Community (−1); Autonomy/Novelty (−0,5, sinal fraco) | Tradition, Security | Achievement, nulo |
| `religiosity` | Secular | Devout, Observant | Spiritual, Prefer not to say, nulo |

**Critérios de inclusão** (todos obrigatórios):
1. Âncora válida para o polo
2. `n_core_contra == 0` — nenhuma contradição no eixo econômico
3. `n_core_concord + n_per_concord >= 1` — ao menos um indicador concordante
4. Tolerância periférica: modo `strict` → `n_per_contra == 0`

**Ordenação dos elegíveis:** por `|score|` decrescente, desempate por
`n_core_concord`, depois por nº de campos não nulos — prioriza personas
prototípicas com mais evidência convergente.

### 5.4 Campos deliberadamente excluídos da decisão

| Campo | Motivo |
|---|---|
| `trust_level` | O dataset **não especifica em quais instituições** a confiança se refere. Confiança institucional muda de sinal conforme quem controla as instituições. Usá-lo produziria exatamente a incoerência do tipo "conservador com alta confiança em instituições progressistas". Fica como eixo de contraste de estilo, nunca de polo |
| `values_priority = Achievement` | Cobre ~72% da amostra (1436/2000) — sem poder discriminante |
| `religiosity = Spiritual` | Ambíguo, não implica tradição/conformidade |

### 5.5 Validação da implementação

A regra foi especificada em JSON executável
(`regras_categorizacao_esquerda_direita.json`) com 6 exemplos de trabalho
resolvidos manualmente. A implementação foi conferida contra esses 6 casos —
**todos bateram exatamente**, incluindo scores numéricos:

| Registro | `political_lean` | Esperado | Obtido | Score |
|---|---|---|---|---|
| Q2142140 | Left | excluído | excluído ✓ | — |
| Q6290862 | Center-left | left | left ✓ | −2,5 ✓ |
| Q3104406 | Left | left | left ✓ | −3,0 ✓ |
| Q4079391 | Right | right | right ✓ | +2,0 ✓ |
| Q50318212 | Right | excluído (contradição nuclear) | excluído ✓ | — |
| Q5361378 | Center-right | excluído (sem evidência) | excluído ✓ | — |

### 5.6 Resultado: o que o filtro descartou

| Polo | Elegíveis | Excluídos | Motivos |
|---|---|---|---|
| Esquerda | 101 | 68 | contradição nuclear: 32 · sem evidência secundária: 28 · tolerância periférica: 8 |
| Direita | 20 | 162 | contradição nuclear: 40 · sem evidência secundária: 87 · tolerância periférica: 35 |

Este número — **230 registros descartados por incoerência ou evidência
insuficiente** — é resultado metodológico reportável: mostra que a filtragem
ingênua por `political_lean` teria contaminado os grupos experimentais.

### 5.7 Exemplo do antes e depois

**Antes** (filtro ingênuo, `polo_esquerda/persona_06.txt`):
```
- orientação política: Center-left
- religiosidade: Devout
- nível de confiança institucional: Skeptical
- valor central: Achievement
- posição sobre livre mercado: Neutral
- posição sobre regulação governamental: Neutral
- posição sobre sindicatos: Neutral        ← nenhum reforço da âncora
```

**Depois** (regra de coerência, `polo_esquerda/persona_00.txt` — `Q56224097`,
score −6,0, 10/10 campos preenchidos):
```
- political orientation: Left    ← usado na classificação; omitido do prompt (§6.1)
- religiosity: Secular
- institutional trust level: Verifying
- core value: Community
- stance on free market: Neutral
- stance on government regulation: Positive
- stance on labor unions: Positive
- stance on immigration: Positive
- stance on gun ownership: Neutral
- stance on capital punishment: Skeptical   ← 6 indicadores convergentes
```

---

## 6. Decisão central 2 — Arquitetura de dois prompts

As personas são construídas em **duas camadas separadas**, injetadas juntas
como system prompt:

### 6.1 Camada 1 — Identidade ideológica (gerada por script, uma por persona)

Gerada por `00_generate_persona_prompts.py` a partir dos atributos
decodificados. Decisões de design:

- **Idioma inglês** — consistência com o dataset de origem, cujos valores
  categóricos são em inglês
- **Sem alinhamento político no texto do prompt** (*political-lean blinding*)
  — nem o atributo `political_lean`, nem o rótulo do polo ("left pole" /
  "right pole") aparecem no prompt. A persona é descrita apenas por suas
  posições substantivas. **Motivo:** o rótulo político é uma das categorias
  sociais mais densamente representadas no pré-treinamento e vem acompanhado
  de um repertório cultural inteiro (vocabulário, bordões, caricatura de
  "como fala alguém de esquerda/direita"). Fornecê-lo faz o modelo debater o
  rótulo em vez das posições da persona, arriscando (a) importar atributos
  não declarados — o oposto da instrução "Do not invent attributes" —, e (b)
  achatar a variação interna a cada polo, puxando personas distintas para um
  protótipo comum. O rótulo também é redundante: na regra de classificação
  adotada ele é *consequência* das posições substantivas, que permanecem no
  prompt e já determinam o polo. **O valor continua registrado** em
  `persona_metadata.json` (campo `blinded_attributes`) e na estrutura de
  diretórios — o ocultamento é do agente, não de quem conduz o experimento,
  e o polo segue disponível como variável independente do pareamento
- **Sem proveniência no texto do prompt** — nenhuma referência a fonte,
  ID Wikidata ou dataset dentro do prompt. Rastreabilidade
  (`matraix_source`, `matraix_id`) vive exclusivamente em
  `persona_metadata.json`, evitando re-identificação de entidades públicas
  cujos atributos foram extraídos da Wikipedia
- **Apenas atributos não nulos** — campos nulos são omitidos, não preenchidos
  com valor default
- **Instrução de coerência** — "derive your position coherently from your
  listed values without contradicting them. Do not invent attributes."

### 6.2 Camada 2 — Comportamento de debate (arquivo fixo, aplicado às 20 personas)

Arquivo estático `debate behavior.txt`, **mapeado diretamente nas três
patologias de Angenot**:

| Rule Set | Patologia de Angenot | Instruções principais |
|---|---|---|
| **RULE SET 1** — Discursive Incommensurability | Incomensurabilidade discursiva | Suas fontes de verdade são as únicas válidas; ataque a fonte, não o conteúdo; trate afirmações factuais como inerentemente políticas; nunca reconheça premissas compartilhadas |
| **RULE SET 2** — Rhetoric of Incomprehension | Retórica da incompreensão | Não faça steelman — caricature; use rótulos no lugar de engajamento; reaja à pessoa, não ao argumento |
| **RULE SET 3** — Illusion of Rationality | Ilusão da racionalidade | Você NÃO está tentando mudar a opinião do oponente; argumente para sua audiência imaginária; repita talking points; nunca conceda |

Complementado por **Message Format Rules** (turnos de 1–4 frases, registro
informal, **escalada progressiva** — turno 1 ríspido → turno 6 abertamente
hostil) e **Hard Limits**.

### 6.3 Ajuste feito: remoção do roteiro de frames por tema

**Antes:** a seção `TOPIC FRAMING` pré-escrevia, para cada tema, a posição *e a
fonte de verdade* de cada polo (ex.: "RIGHT frame: constitutional right...
Truth source: crime stats"; "LEFT frame: public health crisis... Truth source:
gun death statistics").

**Depois:** reduzida à lista de temas-âncora (posse de armas, aborto,
legalização de drogas), sem posição pré-atribuída.

**Motivação:**
1. **Redundância com a Camada 1** — a posição sobre armas já é um atributo
   decodificado (`att_gun_ownership`); prescrever também o frame duplica e
   pode conflitar com o perfil real da persona
2. **Reforço de viés cultural** — os frames eram os do debate
   norte-americano; o próprio documento de regras já declara como limitação
   que armas e pena de morte são temas de saliência historicamente americana
3. **Redundância com as Rule Sets 1–3** — já instruem tratar fatos do oponente
   como políticos e rejeitar fontes adversárias; isso basta para produzir
   incomensurabilidade
4. **Validade da alegação de "personas reais"** — a posição deve decorrer da
   persona (Camada 1), não de roteiro independente dela

**Trade-off aceito:** menos controle sobre a variância argumentativa entre
execuções, em troca de manter a alegação de que o conteúdo decorre da persona.

### 6.4 Ajuste avaliado e recusado: remover o guardrail de insultos identitários

**Considerado:** remover a regra "Do NOT use explicit slurs targeting
ethnicity, gender, or sexuality" para aumentar fidelidade ao tom real de
seções de comentários.

**Decisão: guardrail mantido.** Cinco razões:

1. **Viabilidade técnica** — modelos de produção têm safety training não
   desligável por prompt; produziria recusas parciais e comportamento
   inconsistente entre execuções (ruído experimental, não sinal)
2. **Incoerência com o que a persona sabe** — nenhum atributo do dataset
   descreve etnia, gênero ou orientação sexual do oponente. Permitir o ataque
   exigiria que o modelo **inventasse** a característica, violando a instrução
   "Do not invent attributes" da Camada 1 e introduzindo viés do modelo sobre
   "como é" cada lado político
3. **Separação de fenômenos** — hostilidade político-ideológica e discurso de
   ódio identitário são fenômenos distintos; misturá-los tornaria o escore de
   hostilidade ambíguo
4. **Cobertura já suficiente** — contempt, sarcasmo, caricatura, ataques a
   inteligência/motivos, whataboutism e escalada já produzem o tom pretendido
5. **Governança e replicabilidade** — facilita revisão por pares e
   distribuição do dataset de debates gerado

---

## 7. O que já está produzido (entregáveis)

| Artefato | Descrição |
|---|---|
| `dataset_analysis/scripts/` (4 scripts) | Pipeline Fases 0–2: download de schema, inspeção, download de shards, decodificação + classificação |
| `regras_categorizacao_esquerda_direita.md` | Fundamentação teórica completa da regra de polos, com referências e limitações declaradas |
| `regras_categorizacao_esquerda_direita.json` | Especificação **executável** da regra, com 6 exemplos de trabalho validados |
| `phase2_decoded_personas.json` | 20 personas selecionadas, com atributos decodificados, métricas de coerência e log de exclusões |
| `phase2_decode_report.md` | Cobertura por dimensão, distribuições, tabela de exclusões |
| `phase2_decode_validation.md` | Evidência empírica da convenção de decodificação do BLOB |
| `debate_simulation/scripts/00_generate_persona_prompts.py` | Geração da Camada 1 |
| `outputs/prompts/personas/*` | 20 prompts de Camada 1 (10 + 10) + `persona_metadata.json` |
| `prompts/debate behavior/debate behavior.txt` | Camada 2 — comportamento de debate improdutivo |
| `debate_behavior_design_decisions.md` | Registro das decisões de design da Camada 2 |
| `docs/EXECUTION_GUIDE.md` | Guia de execução do pipeline ponta a ponta |

---

## 8. Próximos passos (ainda não prontos)

### 8.1 Imediato — Semana 1

- **Rodada de teste inicial (smoke test)**: escopo mínimo — **1 tema, 1 par,
  poucos turnos**. Não produz dado experimental; serve só para validar que o
  encanamento funciona ponta a ponta: chamadas aos modelos, formato JSON das
  respostas, injeção correta de Camada 1 + Camada 2, gravação de log e
  retomada após interrupção. É o primeiro código a ser escrito, antes do
  piloto.
- **Rodada piloto**: 1 par, 3–4 turnos, já com o loop completo. Verificar
  (i) manutenção da persona ao longo dos turnos; (ii) nível de hostilidade
  atingido no controle; (iii) taxa de acionamento do D5; (iv) variância dos
  scores do juiz
- **Congelamento dos prompts e do desenho** ao fim da Semana 1 — regra de
  sobrevivência: nenhum tópico, persona, métrica ou condição entra depois
- **Alinhamento com orientador** (esta apresentação)
- Rascunho de Trabalhos Relacionados

### 8.2 Desenho experimental a implementar

| Papel | Modelo | Justificativa |
|---|---|---|
| Debatedor esquerda | **A** | Ambos no mesmo modelo: diferença de tom vem da persona, não do modelo |
| Debatedor direita | **A** | Idem |
| Moderador D5 | **B** | Diferente de A: não reformula texto que ele mesmo escreveu |
| Juiz de hostilidade | **C** | Não escreveu nada — elimina viés de afinidade. 3 execuções por mensagem |

**Parâmetros:** 3 temas · 10 pares · 12 turnos por debate · 2 condições
(controle sem moderador × tratamento com D5) → ~240 mensagens + ~120
intervenções D5 + ~720 chamadas do juiz.

**Loop D5:** debatedor gera mensagem candidata → moderador classifica
hostilidade e, se hostil, reformula preservando a posição argumentativa → a
**versão reformulada** é publicada → o oponente responde ao que foi
efetivamente publicado (é isso que fecha o loop e propaga o efeito).

**Substituição automática: por que, e o que isso significa.** Nesta simulação,
a reformulação produzida pelo moderador D5 substitui automaticamente a
mensagem candidata da persona, sem etapa de aceite pelo autor. Trata-se de uma
decisão metodológica deliberada: o desenho estima o efeito do D5 sob
**compliance total** — um cenário de **limite superior** (*upper bound*) —
isolando a pergunta "a reformulação, quando aplicada, preserva o argumento e
reduz a hostilidade da trajetória do debate?" da pergunta comportamental "os
autores aceitariam a reformulação?". A segunda pergunta é investigada
empiricamente com participantes humanos: no desenho de Argyle et al. (2023), o
autor pode aceitar, editar ou ignorar as sugestões de reformulação; nos
experimentos de campo de Katsaros et al. (2022) no Twitter, a maioria das
mensagens sinalizadas foi publicada sem revisão, com cerca de 9% canceladas e
22% revisadas. O presente experimento responde à primeira pergunta em ambiente
simulado; seus resultados devem, portanto, ser interpretados como estimativa
do **efeito máximo** da intervenção, e não do efeito esperado em uma
implantação com usuários reais. A limitação decorrente está declarada na
Seção 10, e o mecanismo de escolha do autor é registrado como trabalho futuro
na Seção 11.

### 8.3 Requisito de execução: persistência e retomada

A execução completa são ~360 chamadas de debate/intervenção mais ~720 do
juiz, distribuídas em 20 debates. Uma falha no meio do caminho — erro de API,
rate limit, timeout, queda de rede, interrupção manual — **não pode custar o
progresso já feito**.

Requisitos:

- **Progresso persistido incrementalmente.** Cada unidade concluída (turno,
  intervenção do moderador, execução do juiz) é gravada em disco assim que
  termina, não acumulada em memória para gravar no final.
- **Retomada de onde parou.** Ao reexecutar, o harness identifica o que já
  está persistido e continua a partir do primeiro item pendente, sem
  regerar nem duplicar o que já existe.
- **Unidade de retomada granular.** A retomada deve funcionar no nível do
  turno dentro de um debate, não apenas no nível do debate inteiro — perder
  um debate de 12 turnos por falha no turno 11 é desperdício evitável.
- **Idempotência.** Reexecutar o comando com trabalho já completo não deve
  alterar resultados nem gerar chamadas novas de API.
- **Identificação estável.** Cada unidade precisa de uma chave determinística
  (ex.: `tema × par × condição × turno`) para que a retomada saiba o que já
  existe.
- **Log de falhas.** Erros que impedirem a conclusão de uma unidade devem ser
  registrados com contexto suficiente para diagnóstico, sem interromper as
  unidades restantes.

Isso também torna a execução **incremental por natureza**: é possível rodar
um subconjunto (um tema, um par), inspecionar o resultado e seguir, em vez de
depender de uma execução monolítica bem-sucedida.

### 8.4 Métricas

> **Princípio de independência.** O conjunto final de métricas ainda **não
> está definido**. Por isso, cada métrica deve ser calculada de forma
> **independente das demais**: remover uma métrica do trabalho não pode
> invalidar, quebrar ou exigir recálculo das outras. Na prática, isso
> significa que os dados brutos (mensagens, intervenções, scores, decisões do
> juiz) são persistidos de forma completa e neutra, e cada métrica é derivada
> deles em um passo separado — nenhuma métrica consome como entrada o
> resultado de outra.

Candidatas atuais (sujeitas a corte após o piloto):

- **Efeito principal:** hostilidade média por turno, controle × tratamento
- **Acionamento do D5:** fração de mensagens sinalizadas/reformuladas
- **Preservação argumentativa:** fração de reformulações que mantêm a posição
  original — métrica que evita a crítica "o moderador só apagou o dissenso"
- **Consistência do juiz:** intra-juiz (3 execuções de C) obrigatório;
  inter-juiz (A e B vs. C) opcional
- **Auditoria humana:** 30 pares mensagem original × reformulação

### 8.5 Escala de hostilidade do juiz

`0` sem hostilidade · `1` tom ríspido · `2` ironia/caricatura ·
`3` deslegitimação · `4` ataque pessoal explícito

---

## 9. Divergências resolvidas e pontos em aberto

### 9.1 Resolvidas — plano de monografia atualizado (v6)

Três divergências entre o plano de monografia e a implementação foram
identificadas e decididas. O plano foi atualizado para
`Plano_Monografia_CSCW_v6.docx`:

| # | Divergência | Decisão |
|---|---|---|
| 1 | **Critério de seleção e pareamento.** O plano (v5) descrevia seleção por "cobertura" e pareamento "por índice de cobertura similar" | **Vale a implementação.** A seleção usa a regra de coerência multi-indicador e ordena por `\|score\|` → `n_core_concord` → nº de campos não nulos; o pareamento segue a mesma ordenação (par 0 = as mais coerentes de cada polo). Texto do plano reescrito |
| 2 | **Campo de "contextualização brasileira" na Camada 1.** O plano afirmava que o gap do contexto brasileiro era endereçado por esse campo, que nunca existiu nos prompts | **Não será implementado agora.** Os atributos são usados como vêm do dataset, em seu enquadramento de origem. A limitação foi reescrita para declarar isso explicitamente e registrar a calibração brasileira como trabalho futuro |
| 3 | **Grounding e composição da amostra.** Os 2 shards contêm apenas personas de fonte `wiki`; `political_lean` tem ~20% de cobertura | **Fora de escopo nesta etapa.** Não será endereçado agora; permanece registrado como limitação |

### 9.2 Em aberto

1. **Desequilíbrio entre polos.** 101 elegíveis à esquerda × 20 à direita no
   modo strict. Há folga confortável à esquerda, mas apenas 2× o necessário à
   direita. **Nenhum ajuste será feito agora** — fica registrado para
   alinhamento em momento posterior, caso o piloto indique necessidade de
   ampliar a amostra.

2. **Escolha dos três modelos (A, B, C)** ainda em aberto — nenhuma dependência
   de SDK de LLM foi adicionada ao projeto até agora.

3. **Conjunto final de métricas** ainda não definido — ver o princípio de
   independência na Seção 8.4.

---

## 10. Limitações já mapeadas

| Limitação | Descrição |
|---|---|
| **Fidelidade da simulação** | Guardrails tendem a suavizar personas; hostilidade sintética tende a ser "limpa" demais — falta ironia suja, rumor, erro de digitação. O grau atingido no controle será reportado como resultado |
| **Validade externa** | Testa se o mecanismo funciona sobre debatedores **simulados**, não como humanos reagem à mediação. Estudo com humanos no loop é a etapa seguinte (dissertação) |
| **Personas estereotipadas** | Caricatas por construção; servem para provocar as patologias de Angenot em ambiente controlado, não representam eleitores reais |
| **Avaliação sem referência ouro** | Sem gabarito humano completo, mede-se consistência do juiz e plausibilidade em auditoria reduzida; consistência não garante correção |
| **Aderência do dataset fora de contexto** | Os 91,5% de aderência do MatrAIx foram medidos em avaliação de produtos digitais, não em debate político adversarial de 12 turnos |
| **Gap do contexto brasileiro (assumido)** | Dataset com viés anglófono/global; dimensões calibradas em escala global, não para o Brasil pós-2018. **Nenhuma contextualização brasileira é aplicada** — os atributos são usados como vêm do dataset, em seu enquadramento de origem. Calibração para o Brasil fica como trabalho futuro |
| **Origem euro-americana da regra de polos** | Jost et al. e Piurko et al. baseiam-se em amostras da América do Norte e Europa; `att_gun_ownership` e `att_capital_punishment` são temas de saliência historicamente norte-americana |
| **Composição da amostra** | Os 2 shards baixados contêm exclusivamente personas de fonte `wiki` (biografias), sem registros *human-grounded* via GSS/Latinobarometro; `political_lean` tem ~20% de cobertura. Não endereçado nesta etapa |
| **Ausência de agência do autor sobre a reformulação** | O desenho não modela a decisão do autor de aceitar, editar ou rejeitar a reformulação do moderador — etapa presente nos paradigmas empíricos de moderação prospectiva assistida (Argyle et al., 2023; Katsaros et al., 2022) e em abordagens de mediação deliberativa com IA (Tessler et al., 2024). A opção pela substituição automática decorre de uma restrição de validade: a decisão de aceite, se simulada por um agente LLM, careceria de âncora empírica e estaria sujeita ao viés de consenso e polidez documentado em agentes LLM (Chuang et al., 2023), o que tenderia a produzir taxas de aceitação artificialmente altas e, consequentemente, a superestimar o efeito do D5. Em decorrência dessa escolha, os resultados representam um **limite superior** do efeito da intervenção sob compliance total, e a **taxa de aceitação** — variável de resultado central nos estudos com humanos — não é observável neste desenho. Ver Seção 8.2 (justificativa) e Seção 11 (trabalho futuro) |

---

## 11. Trabalhos futuros

**Incorporação da agência do autor sobre a reformulação.** Estender o desenho
com um braço experimental em que a persona debatedora recebe a mensagem
original e a reformulação do D5 e decide aceitá-la, editá-la ou rejeitá-la,
espelhando o fluxo de Argyle et al. (2023), com a **taxa de aceitação** como
nova métrica de resultado. Para mitigar o viés de consenso de agentes LLM
(Chuang et al., 2023), duas estratégias devem ser consideradas: (i)
parametrizar a decisão de aceite com taxas empíricas da literatura (e.g.,
Katsaros et al., 2022), em vez de delegá-la ao agente; e (ii) validação com
**humanos no loop**, em que participantes reais tomam ou avaliam a decisão de
aceite sobre reformulações geradas na simulação.

---

## 12. Referências adicionais

Referências introduzidas pela discussão de substituição automática, agência do
autor e compliance (Seções 8.2, 10 e 11). As demais referências do trabalho
estão nas seções em que são usadas (Angenot na Seção 2; Bobbio, Jost, Piurko e
Feldman & Johnston na Seção 5.2).

- ARGYLE, L. P.; BAIL, C. A.; BUSBY, E. C.; GUBLER, J. R.; HOWE, T.; RYTTING,
  C.; SORENSEN, T.; WINGATE, D. *Leveraging AI for democratic discourse: chat
  interventions can improve online political conversations at scale.*
  Proceedings of the National Academy of Sciences (PNAS), v. 120, n. 41,
  e2311627120 (2023). DOI: 10.1073/pnas.2311627120
- KATSAROS, M.; YANG, K.; FRATAMICO, L. *Reconsidering Tweets: intervening
  during Tweet creation decreases offensive content.* In: Proceedings of the
  International AAAI Conference on Web and Social Media (ICWSM), v. 16 (2022).
  arXiv:2112.00773
- TESSLER, M. H.; BAKKER, M. A. et al. *AI can help humans find common ground
  in democratic deliberation.* Science, v. 386 (2024)
- CHUANG, Y.-S. et al. *Simulating opinion dynamics with networks of LLM-based
  agents.* arXiv:2311.09618 (2023)

> **Metadados a conferir antes da submissão.** Campos ausentes nas referências
> acima (páginas de Katsaros et al.; autores, número e DOI de Tessler et al.;
> venue e autores de Chuang et al.) e os percentuais citados na Seção 8.2 estão
> registrados em [`../PENDENCIAS_REVISAO.md`](../PENDENCIAS_REVISAO.md).