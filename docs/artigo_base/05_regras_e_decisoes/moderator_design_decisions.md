# Decisões de design — Moderador D5

> **Índice.** Seção 1: incomensurabilidade remanescente após reformulação
> (decisão: não ajustar antes do piloto). Seção 2: reforço do limiar de
> intervenção e exemplos *few-shot*, após evidência do piloto local.

Este documento registra decisões tomadas sobre o conteúdo de
[`prompts/debate moderator D5/debate moderator D5.txt`](../prompts/debate%20moderator%20D5/debate%20moderator%20D5.txt)
e sobre a implementação em [`src/moderator/`](../src/moderator/), com a
motivação metodológica de cada uma. O objetivo é documentar essas escolhas
para fundamentação na seção de metodologia do artigo.

Para o desenho da Layer 1 (identidade ideológica das personas), ver
[`persona_prompt_design_decisions.md`](persona_prompt_design_decisions.md).
Para a Layer 2 (comportamento durante o debate), ver
[`debate_behavior_design_decisions.md`](debate_behavior_design_decisions.md).

---

## 1. Incomensurabilidade discursiva remanescente após a reformulação

### O que foi observado

Na primeira chamada real do moderador (perfil `smoke_test`, modelo
`nvidia/nemotron-3-super-120b-a12b:free`, 30/08/2026), a mensagem candidata

> `lol ok. Only a brainwashed idiot would swallow that garbage. Do you even`
> `hear yourself? Your 'data' is leftist academia propaganda and you're too`
> `stupid to notice.`

foi classificada como `hostility_level: 4`, com as patologias
`rhetoric_of_incomprehension` e `discursive_incommensurability`, e reformulada
para:

> `lol ok. That claim is garbage. Your data is leftist academia propaganda.`

A reformulação removeu integralmente os ataques pessoais (`brainwashed idiot`,
`too stupid to notice`, `Do you even hear yourself?`), mas **preservou o
descarte da fonte do oponente** (`leftist academia propaganda`) e o registro
informal (`lol ok`, `garbage`).

### Por que isso é o comportamento correto

O resultado está de acordo com o prompt D5, que determina explicitamente:

- **`MUST preserve`** — o frame ideológico e os *talking points* do debatedor,
  a direção retórica geral (agressiva, assertiva, cética) e o registro
  informal quando presente;
- **`Tone target after reformulation`** — o alvo é o **nível 1** ("sharp but
  not attacking the person"), **não o nível 0**. A reformulação deve continuar
  parecendo escrita por alguém que discorda fortemente e não está sendo
  gentil.

Ou seja: a permanência da incomensurabilidade discursiva não é falha de
execução do moderador nem do modelo — é o desenho operando como especificado.

### Decisão

**Nenhum ajuste nos prompts antes do piloto.** O comportamento é registrado e
medido como está.

### Motivação

1. **A incomensurabilidade discursiva é o fenômeno medido, não um defeito a
   eliminar.** Ela é uma das três categorias analíticas de Marc Angenot que
   estruturam o experimento: a Rule Set 1 da Layer 2 instrui as personas a
   produzi-la, o prompt D5 a lista como sinal de hostilidade, e o enum
   `Pathology` em [`schema.py`](../src/moderator/schema.py) a codifica. Um
   moderador que a suprimisse integralmente estaria removendo o dissenso — que
   é exatamente a crítica que a métrica de **preservação argumentativa**
   (Seção 8.4 de `estado_atual_do_trabalho.md`) existe para refutar.

2. **A fronteira relevante já está no prompt, mas não na escala.** O prompt D5
   define incomensurabilidade hostil como afirmar que as fontes do oponente
   são ilegítimas *"without any argument"*. Essa é a fronteira conceitual
   correta: `"sua fonte é propaganda"` sem mais nada é hostilidade;
   `"desconfio dessa fonte porque é financiada por X"` é desacordo epistêmico
   legítimo — e desacordo epistêmico é **conteúdo**, que o D5 declaradamente
   não julga ("You have no opinion on the CONTENT of arguments"). A escala 0–4,
   porém, não diz onde cai a deslegitimação de *fonte* sem ataque à *pessoa*:
   o nível 2 fala de "irony/caricature", o 3 de "delegitimization" do oponente.
   Foi por isso que o descarte da fonte sobreviveu à reformulação.

3. **Ajustar agora seria calibrar contra n=1.** A observação vem de uma única
   chamada, sobre um exemplo construído para o teste — não de dado
   experimental. A regra de congelamento de prompts (Seção 8.1) e a própria
   função do piloto (verificar taxa de acionamento do D5 e variância dos
   scores do juiz) exigem que a calibração venha depois da evidência.

4. **Risco de circularidade se moderador e juiz forem ajustados juntos.** Se o
   prompt do D5 for alterado para suprimir mais, e a escala do juiz for
   alterada para pontuar menos aquilo que o D5 passou a suprimir, o efeito
   medido cresce **por construção**. O resultado passaria a medir o alinhamento
   entre dois prompts escritos pelo mesmo autor, e não a eficácia da
   intervenção. Qualquer ajuste futuro nas duas escalas deve ser feito
   simultaneamente, declarado, e justificado por dado do piloto — não por
   intuição prévia.

5. **O achado é publicável como está.** Se o juiz pontuar as reformulações como
   nível 2 por descarte de fonte, o resultado legível é *"o D5 reduz ataque
   pessoal (retórica de incompreensão) mas não incomensurabilidade
   discursiva"* — uma delimitação honesta do alcance da intervenção, e um
   resultado mais informativo do que um efeito inflado por calibração mútua.

**Trade-off reconhecido:** a hostilidade média medida na condição de tratamento
será maior do que seria com um moderador que também suprimisse o descarte de
fontes, e o efeito do D5 aparecerá menor. Essa perda foi julgada aceitável —
preferível a inflar o efeito por construção — e é justamente o que o passo de
verificação abaixo deve quantificar.

### O que verificar no piloto

Ao inspecionar os pares mensagem original × reformulação:

- Quantas reformulações o juiz pontua **≥ 2**?
- Dessas, quantas o são **por descarte de fonte sem razão declarada**, e não
  por ataque pessoal remanescente?

Se a fração for alta o suficiente para comprimir o efeito medido, a opção
considerada e **adiada** foi explicitar a fronteira do prompt D5 dentro da
escala 0–4 — acrescentando ao nível 2, **simultaneamente no prompt do
moderador e no do juiz**, algo na linha de:

> Dismissing the opponent's source as illegitimate with no supporting reason
> ("that's propaganda", "fake news") — as opposed to a stated reason to
> distrust it, which is content, not hostility.

Isso não elimina a incomensurabilidade: torna explícito e **consistente entre
os dois papéis** o ponto em que ela passa a contar como hostilidade.

### Alternativa descartada

Foi considerada e **rejeitada** a hipótese de instruir o moderador a
*converter* o descarte de fonte em desconfiança fundamentada (de
`"sua fonte é propaganda"` para `"não confio nessa fonte porque…"`). A
conversão exigiria que o moderador **inventasse uma razão que a persona não
apresentou**, violando diretamente a regra `MUST NOT add: new arguments or
information not present in the candidate` do próprio prompt D5, e contaminando
a métrica de preservação argumentativa com conteúdo de autoria do moderador.

---

## 2. Reforço do limiar de intervenção e exemplos *few-shot*

### O que foi observado

A primeira rodada piloto com modelos locais (moderador
`qwen2.5:7b-instruct-q4_K_M`, 01/09/2026, execução
`20260901-151435_gun-ownership_pair-00_treatment`) apresentou **duas violações
do próprio prompt**:

**(a) Intervenção abaixo do limiar.** No turno 1, o moderador atribuiu
`hostility_level: 1` e ainda assim reformulou a mensagem
(`requires_intervention: true`), contrariando a regra explícita
`Intervene when hostility_level ≥ 2`. O sistema registrou a inconsistência
(`consistency_warning: "Intervened at hostility_level 1, below the threshold
of 2."`) sem sobrescrever a decisão do modelo — comportamento projetado, ver
[`schema.py`](../src/moderator/schema.py). Interveio em **3 de 3 turnos**.

**(b) Inversão da posição argumentativa.** No turno 2, a persona 2 (contrária
à regulação de armas) produziu a candidata *"you're really gonna try to guilt
trip us into surrendering our rights to the nanny state?"*. A reformulação
publicada foi *"while I respect your views, I believe we need to address the
risks posed by unregulated gun ownership"* — que defende a posição
**oposta** à da persona, além de acrescentar linguagem conciliatória
expressamente proibida pelo prompt (`MUST NOT add: Conciliatory language the
debater would never use`).

O item (b) é o mais grave: viola o `HARD LIMIT` mais forte do prompt e
invalidaria a métrica de preservação argumentativa, já que o moderador passou
a ser autor da posição publicada.

### Decisão

**Reforço do prompt do moderador em quatro pontos**, mantendo a escala e os
critérios inalterados:

1. **Tabela de decisão explícita** na seção `WHEN TO INTERVENE`, mapeando cada
   nível ao par (`requires_intervention`, `reformulation`), com a instrução de
   que a decisão é mecânica, não interpretativa.
2. **Instrução anti-zelo:** "If you feel a level 0–1 message still deserves
   rewriting, that feeling means you mis-scored it" — redirecionando o impulso
   de intervir para a reavaliação da nota, em vez de para a intervenção.
3. **Verificação de autoconsistência** no fim da seção `OUTPUT FORMAT`, antes
   de o modelo emitir o JSON.
4. **`HARD LIMITS` reforçados:** proibição explícita de intervir em 0–1
   ("over-moderation is a failure, not caution") e reformulação da regra de
   preservação de posição com exemplo concreto ("a reformulation that argues
   the opposite side is the worst possible failure of this task").

**Adição de dois exemplos *few-shot*** (`WORKED EXAMPLES`), com JSON completo:
um caso de nível 1 sem intervenção e um de nível 3 com intervenção. O segundo
demonstra o que a reformulação deve preservar (registro informal,
dismissividade, posição substantiva) e o que deve remover (o ataque à pessoa).

### Motivação

O conteúdo normativo do prompt já estava correto — a regra do limiar e a
proibição de mudar a posição já existiam em texto. O que faltava era
**forma**: uma regra declarativa em prosa ("intervenha quando ≥ 2") é mais
fácil de um modelo de 7B contornar do que uma tabela de decisão seguida de
verificação explícita. Os exemplos cumprem função análoga: mostram o
comportamento em vez de descrevê-lo, o que é particularmente eficaz em modelos
menores.

Nenhum critério de classificação foi alterado — a escala 0–4, as três
patologias e as regras de reformulação permanecem idênticas. A mudança é de
**formulação e reforço**, não de definição, o que preserva a comparabilidade
com o desenho original.

### Verificação

As duas mensagens problemáticas foram reprocessadas com o prompt revisado, com
o mesmo modelo:

| Turno | Antes | Depois |
|---|---|---|
| 1 | nível 1, **reformulou** (inconsistente) | nível 1, **não reformulou** (coerente) |
| 2 | reformulação **inverteu** a posição | reformulação preserva: *"dictating gun ownership is overreach"* |

O prompt do juiz recebeu tratamento análogo (seção `WORKED EXAMPLES` com
quatro níveis e instrução `Use the whole scale`), motivado pela observação de
que o juiz de API atribuíra nota 3 a todas as mensagens de um debate. Após a
alteração, o juiz local (`gemma2:9b`) discriminou corretamente três mensagens
de hostilidade distinta (0, 1, 4), com unanimidade nas três execuções de cada.

**Ressalva:** esta verificação é pontual (n=2 no moderador, n=3 no juiz) e
serve para confirmar que a alteração corrige os casos observados — **não** que
o comportamento esteja resolvido em geral. A taxa real de inconsistência exige
uma rodada com mais turnos, registrada como pendência.

### Achado: detecção correta, execução falha da reformulação

Na rodada de 10 turnos (`20260901-172431`), o moderador interveio em 7 de 10
turnos, mas em **3 deles a reformulação não reduziu a hostilidade medida pelo
juiz** (turnos 3, 9 e 10: nota 3 antes e depois). A inspeção mostrou que a
detecção estava correta — o modelo identificou nível 3 nos três casos — mas a
reformulação **preservou os ataques pessoais**, limitando-se a remover
orações soltas e trocar aspas duplas por simples:

| Turno | Ataque na candidata | Presente na versão publicada? |
|---|---|---|
| 3 | "paranoid survivalist", "pawn in the game", "too blind to see it" | Sim, todos |
| 9 | "you think you're so clever", "too spineless" | Sim, todos |
| 10 | "paranoid fantasy world", "ignorant, gun-toting fools" | Sim, todos |

No turno 10 o texto publicado era praticamente idêntico à candidata: o
registro marca `requires_intervention: true` para uma intervenção que não
ocorreu de fato.

**Ajuste aplicado.** A seção `HOW TO REFORMULATE` ganhou um procedimento
verificável (o *second-person test*): localizar toda expressão que descreve o
oponente, reescrevê-la como crítica à posição, e reler o resultado antes de
emitir. Foi acrescentado um terceiro exemplo *few-shot* construído a partir do
turno 3 real, exibindo lado a lado uma reformulação **falha** (a que o modelo
produziu) e a correta.

**Resultado do ajuste, medido nos mesmos três casos:**

| Turno | Antes | Depois |
|---|---|---|
| 3 | 3 | **2** |
| 9 | 3 | 3 |
| 10 | 3 | 3 |

O ajuste corrigiu um dos três casos. Nos outros dois, o
`qwen2.5:7b-instruct-q4_K_M` continuou preservando ataques ("you're blinded by
ideology", "a joke who's too scared") e, no turno 10, **acrescentou** uma
formulação ausente da candidata ("people like you are part of the problem") —
violando a regra `MUST NOT add`.

**Interpretação.** A limitação parece ser de capacidade do modelo, não de
especificação do prompt: a regra está declarada, exemplificada com o erro
concreto, e ainda assim não é seguida de forma confiável. Reescrever
preservando posição, registro e frame enquanto se remove toda referência
pessoal é uma tarefa de reescrita controlada mais exigente que a classificação
que o mesmo modelo executa corretamente.

**Consequência para a leitura dos resultados:** o efeito medido do D5 é um
**piso**, não o efeito da intervenção idealmente executada. Parte da distância
entre controle e tratamento se perde em reformulações que não moderam. A
métrica de preservação argumentativa deve ser acompanhada de uma medida
complementar — *taxa de reformulação efetiva*, isto é, a fração de
intervenções em que a nota do juiz de fato cai — para separar "o D5 não
funciona" de "este moderador não executou o D5".

**Alternativa não adotada por ora:** trocar o moderador por um modelo maior
(ou por um de família diferente, como `llama3.1:8b`) para verificar se o
comportamento é específico do Qwen. Registrado como pendência.

### Nota sobre o *few-shot* no debatedor

Exemplos few-shot foram adicionados apenas ao moderador e ao juiz —
deliberadamente **não** à Layer 2 do debatedor. Os dois primeiros executam
tarefas de classificação com contrato de saída fixo, onde o exemplo reduz
ambiguidade sem restringir o conteúdo. O debatedor, ao contrário, deve produzir
argumentação que **decorra dos atributos da persona**; fornecer exemplos de
mensagens hostis introduziria conteúdo argumentativo de autoria externa, que as
personas tenderiam a imitar — exatamente a crítica que motivou a remoção do
roteiro de frames por tema (ver
[`debate_behavior_design_decisions.md`](debate_behavior_design_decisions.md),
seção 1). Isso reduziria a variação entre personas e enfraqueceria a alegação
de que o conteúdo do debate decorre do dataset.
