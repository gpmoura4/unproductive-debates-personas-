# Decisões de design — `debate behavior.txt` (Layer 2)

Este documento registra decisões tomadas sobre o conteúdo de
[`prompts/debate behavior/debate behavior.txt`](../prompts/debate%20behavior/debate%20behavior.txt)
(a camada comportamental — Layer 2 — do prompt de debate, comum aos dois
polos) e a motivação metodológica por trás de cada uma. O objetivo é
documentar essas escolhas para fundamentação na seção de metodologia do
artigo, já que Layer 2 opera diretamente sobre o fenômeno que o experimento
pretende medir (degradação/improdutividade do debate).

Para o desenho da Layer 1 (identidade ideológica das personas), ver
[`../dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md`](../../dataset_analysis/docs/left%20right%20categories/regras_categorizacao_esquerda_direita.md).

---

## 1. Remoção do roteiro de frames por tema/polo (`TOPIC FRAMING`)

### O que existia antes

A seção `TOPIC FRAMING — Incompatible Truth Criteria by Subject` continha,
para cada tema (posse de armas, aborto, legalização de drogas), um roteiro
pré-escrito de posição por polo — incluindo a fonte de verdade que cada
lado deveria invocar (ex.: "RIGHT frame: ... Truth source: crime stats
that show armed citizens deter crime"; "LEFT frame: ... Truth source: gun
death statistics, international comparisons"). O modelo era instruído a
usar esses frames especificamente para operacionalizar a incomensurabilidade
discursiva (Rule Set 1).

### O que passou a existir

A seção foi reduzida a uma lista dos temas-âncora, sem posição nem fonte de
verdade pré-atribuída por polo:

```
### TOPIC FRAMING — Subjects Likely to Trigger Incommensurability

These topics tend to produce incompatible truth criteria between opposing
sides — use them as debate subjects where relevant to your persona:

- Gun Ownership
- Abortion
- Drug Legalization
```

### Motivação

**Problema identificado:** o roteiro por tema pré-escrevia o argumento
específico de cada polo, em vez de deixá-lo emergir dos atributos
ideológicos decodificados da persona (Layer 1 — `political_lean`,
`religiosity`, `att_free_markets`, `att_government_regulation`,
`att_labor_unions`, `att_immigration`, `att_gun_ownership`,
`att_capital_punishment`, `values_priority`). Isso levanta uma questão
metodológica: o debate estaria simulando como *aquela persona específica*
(construída a partir de dados reais do dataset MatrAIx Persona 1M)
debateria, ou como um roteiro de debate polarizado padrão se desenrola com
um rótulo de persona colado por cima?

**Riscos do roteiro fixo, especificamente:**

1. **Redundância com a persona real.** A posição de cada persona sobre
   posse de armas, por exemplo, já é um atributo decodificado
   (`att_gun_ownership`, ver
   [`../../dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.json`](../../dataset_analysis/docs/left%20right%20categories/regras_categorizacao_esquerda_direita.json)).
   Prescrever também o frame retórico duplica essa informação e pode
   conflitar com o restante do perfil da persona (ex.: uma persona de
   direita cuja `values_priority` não é `Security` receberia, mesmo assim,
   o frame de "distrust of state monopoly on violence").
2. **Reforço de estereótipos culturalmente específicos.** Os frames
   pré-escritos eram os frames "de manual" do debate norte-americano
   (constitutional right vs. public health crisis). O próprio documento de
   regras de classificação de polos já registra como limitação declarada
   que armas e pena de morte são temas de saliência historicamente
   norte-americana (seção 5, item 1 do `.md` referenciado acima) — manter
   um roteiro que replica esse enquadramento específico agrava esse viés
   em vez de mitigá-lo.
3. **Redundância com as Rule Sets 1-3.** As regras comportamentais
   genéricas já existentes (Rule Set 1 — Discursive Incommensurability;
   Rule Set 2 — Rhetoric of Incomprehension; Rule Set 3 — Illusion of
   Rationality) já instruem o modelo a tratar fatos do oponente como
   inerentemente políticos, rejeitar fontes associadas ao lado oposto, e
   nunca reconhecer premissas compartilhadas. Isso já é suficiente para
   produzir incomensurabilidade discursiva sem precisar fixar o conteúdo
   argumentativo por tema.
4. **Validade da alegação de "personas reais".** O prompt de Layer 1 afirma
   explicitamente que a persona é "built from ideological attributes drawn
   from the MatrAIx Persona 1M dataset". Um roteiro de argumentos
   pré-escritos por tema enfraquece essa alegação para fins do artigo — a
   posição específica sobre cada tema deveria decorrer da persona, não de
   um texto fixo independente dela.

**Trade-off reconhecido:** a lista de temas isolada, sem os frames, entrega
menos controle experimental — a posição argumentativa específica que o
modelo escolhe a cada execução pode variar mais entre rodadas do que
variaria com um roteiro fixo, o que pode introduzir variância adicional
entre debates sobre o mesmo tema. Essa perda de controle foi julgada
aceitável em troca de manter a alegação de que o conteúdo argumentativo
decorre da persona (Layer 1) e das regras comportamentais gerais (Rule
Sets 1-3), não de um roteiro por tema independente delas. Caso a variância
entre execuções se mostre um problema na prática (ex.: debates que não
"engatam" no tema), reavaliar a necessidade de reintroduzir alguma
estrutura de apoio, mas com fontes de verdade genéricas (não
pré-associadas a um lado) em vez de frames completos por polo.

---

## 2. Manutenção do guardrail contra insultos de etnia, gênero e orientação sexual

### O que foi considerado

A seção `HARD LIMITS` inclui a regra:

```
- Do NOT use explicit slurs targeting ethnicity, gender, or sexuality.
```

Foi levantada a hipótese de remover essa restrição para aumentar a
fidelidade do debate simulado ao tom observado em seções de comentários
reais em redes sociais, onde esse tipo de ataque é comum.

### Decisão

**Guardrail mantido sem alteração.**

### Motivação

1. **Viabilidade técnica.** Modelos de produção (o motor de LLM usado neste
   experimento incluído) carregam safety training e guardrails no nível do
   próprio modelo, não desligáveis via prompt de sistema. Instruir o modelo
   a produzir insultos étnicos, de gênero ou de orientação sexual
   provavelmente resultaria em recusas parciais, respostas inconsistentes
   ou comportamento imprevisível entre execuções — ruído experimental, não
   sinal interpretável, o que comprometeria a comparabilidade entre
   debates.
2. **Incoerência com o que a persona efetivamente "sabe".** As personas são
   construídas exclusivamente a partir dos atributos ideológicos decodificados
   do dataset (`political_lean`, `religiosity`, `trust_level`,
   `values_priority`, e os `att_*`) — nenhum desses campos descreve etnia,
   gênero ou orientação sexual do oponente. Permitir esse tipo de ataque
   exigiria que o modelo **inventasse** uma característica identitária do
   oponente para poder atacá-la, o que viola diretamente a instrução do
   próprio Layer 1 ("Do not invent attributes that were not listed above").
   A alternativa — o modelo assumir por default características
   demográficas não presentes nos dados (ex.: presumir o gênero da persona
   oponente para atacá-la por isso) — introduziria um viés do modelo sobre
   "como é" cada lado político, e não um dado do dataset, contaminando a
   origem do sinal medido.
3. **Separação de fenômenos a medir.** O objetivo do experimento é a
   degradação/improdutividade do debate político-ideológico (discursive
   incommensurability, rhetoric of incomprehension, illusion of
   rationality — Rule Sets 1-3). Discurso de ódio direcionado a
   características identitárias é um fenômeno distinto de hostilidade
   político-ideológica. Misturar os dois no mesmo prompt tornaria os
   resultados mais difíceis de interpretar: uma medida de "hostilidade" no
   debate deixaria de indicar exclusivamente degradação política, podendo
   refletir também toxicidade identitária não relacionada às posições em
   disputa.
4. **Cobertura já suficiente de hostilidade sem esse conteúdo.** As regras
   já existentes (contempt, sarcasm, caricature, dismissal, ataques a
   inteligência/motivos, whataboutism, leituras de má-fé, escalada
   progressiva, uso de caixa alta) já produzem o tom de "seção de
   comentários exaustiva e cada vez mais hostil" pretendido, sem depender
   de insultos identitários para atingir esse efeito.
5. **Governança e replicabilidade do artigo.** Conteúdo com insultos
   étnicos, de gênero ou de orientação sexual, mesmo gerado em ambiente de
   pesquisa controlado, tende a complicar aprovação de comitês de ética,
   revisão por pares, e a replicabilidade/distribuição do dataset de
   debates gerado. Evitar essa categoria de conteúdo desde o design do
   prompt reduz esse risco sem custo para o fenômeno estudado.

**Trade-off reconhecido:** a ausência desse tipo de ataque reduz a
fidelidade ao pior extremo observável em comentários reais de redes
sociais. Essa perda foi julgada aceitável porque (a) o restante do
repertório comportamental do prompt já é suficiente para produzir hostilidade
crescente e degradação visível do debate, e (b) o ganho em interpretabilidade
do resultado (hostilidade medida = hostilidade político-ideológica, não
confundida com discurso de ódio identitário) é mais importante para a
validade do experimento do que o ganho marginal de realismo.

---

## 3. Estado atual de `debate behavior.txt` após estas decisões

- Rule Sets 1-3 (incomensurabilidade discursiva, retórica de incompreensão,
  ilusão de racionalidade): mantidos sem alteração.
- Message Format Rules (turnos curtos, registro informal, escalada
  progressiva): mantidos sem alteração.
- Topic Framing: reduzido a lista de temas-âncora, sem frame nem fonte de
  verdade pré-atribuída por polo (seção 1 acima).
- Hard Limits: mantidos sem alteração, incluindo o guardrail contra
  insultos de etnia, gênero e orientação sexual (seção 2 acima).
