# Decisões de design — Moderador D5

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
