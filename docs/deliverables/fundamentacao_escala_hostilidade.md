# Fundamentação Teórica da Escala de Hostilidade 0–4

Documento de fundamentação da escala ordinal usada pelo moderador D5 e pelo
Juiz C no experimento de simulação de debate improdutivo.

**Instrumentos que implementam a escala:**

- `debate_simulation/prompts/debate moderator D5/debate moderator D5.txt` —
  moderador D5, que pontua a mensagem *candidata* antes da publicação e decide
  pela reformulação.
- `debate_simulation/prompts/debate judge/debate judge.txt` — Juiz C, que
  pontua a mensagem *publicada* em avaliação cega, três vezes por mensagem.

Os dois prompts são carregados verbatim pelo pipeline e não são alterados por
este documento. O desenho experimental em que a escala opera está no plano
vigente (`Plano_Monografia_CSCW_v6.docx`).

---

## 1. Introdução e posicionamento

A escala de hostilidade 0–4 é uma **operacionalização ordinal original**,
desenvolvida para este estudo. Ela **não** é adoção direta de nenhum
instrumento existente na literatura de incivilidade política online.

O que ela faz é sintetizar distinções conceituais já consolidadas em três
tradições de pesquisa:

1. a distinção **impoliteness vs. incivility** de Papacharissi (2004);
2. a **taxonomia de tipos de incivilidade** de Coe, Kenski e Rains (2014);
3. a separação **incivility vs. intolerance** de Rossini (2022) e o modelo
   tridimensional de Bentivegna e Rega (2022).

Declarar essa condição importa: apresentar a escala como reprodução de
instrumento validado seria falso, e apresentá-la como construção livre
esconderia a ancoragem que a torna auditável. Ela é uma contribuição original
**com** ancoragem teórica explícita — e é assim que deve ser lida.

### 1.1 Por que uma escala ordinal discreta

A escolha por níveis discretos, em vez de uma classificação binária ou de um
score contínuo, decorre de três requisitos do desenho experimental:

| Requisito | Implicação |
|---|---|
| **Uso por LLM como classificador instrucional** | O modelo recebe a escala por instrução em linguagem natural. Isso exige categorias discretas com descritor verbal — um modelo instruído não calibra de forma confiável um score contínuo sem âncoras textuais |
| **Comparabilidade entre instrumentos** | O moderador D5 e o Juiz C operam sobre a mesma escala, em momentos distintos do fluxo (candidata vs. publicada). Uma escala comum é condição para que as duas medições sejam confrontáveis |
| **Interpretabilidade para análise qualitativa** | Os logs de debate são lidos manualmente na auditoria. Níveis nomeados permitem localizar e discutir casos; um score 0,73 não |

Kennedy et al. (2020) argumentam que a classificação binária de discurso hostil
descarta informação relevante sobre **severidade**, tratando como equivalentes
mensagens que o público percebe de forma muito distinta. A escala ordinal
preserva essa informação dentro das restrições impostas pelo uso instrucional
por LLM.

---

## 2. Revisão das abordagens existentes

Cada abordagem abaixo resolve parte do problema. Nenhuma, isoladamente, produz
uma escala ordinal discreta aplicável por instrução a um agente LLM — e é essa
lacuna que justifica a operacionalização proposta.

### 2.1 Taxonomias categóricas

**Coe, Kenski e Rains (2014); Rains et al. (2017); Kenski, Coe e Rains (2020)**

Definem cinco tipos binários de incivilidade: *name-calling*, *aspersion*,
*lying*, *vulgarity* e *pejorative for speech*. É a taxonomia mais adotada na
área, e sua força está na confiabilidade de codificação: cada tipo é
identificável de forma relativamente objetiva.

A limitação para o presente uso é a **ausência de hierarquia de severidade** —
os cinco tipos são categorias paralelas, não graus. Kenski et al. (2020),
porém, demonstram empiricamente que o público percebe severidades distintas
entre eles: *name-calling* e *vulgarity* são percebidos como mais incivis que
*aspersion* ou *lying*. Esse achado sugere uma **dimensão ordinal latente** que
a taxonomia categórica não expressa, e que a escala aqui proposta torna
explícita.

### 2.2 Distinção impoliteness vs. incivility

**Papacharissi (2004)**

Separa dois fenômenos frequentemente confundidos:

- **Impoliteness** — violação de normas interpessoais de etiqueta: tom rude,
  linguagem vulgar, impaciência.
- **Incivility** — ameaça a valores democráticos: deslegitimação do
  interlocutor, estereotipação, exclusão do outro do espaço deliberativo.

A distinção é fundacional porque estabelece que **ser rude não é o mesmo que
ser danoso à deliberação**. Uma discussão pode ser áspera e ainda assim
democraticamente produtiva. É essa separação que a escala transforma em
fronteira operacional (Seção 4).

### 2.3 Incivility vs. intolerance

**Rossini (2022)**

Avanço empírico sobre Papacharissi. Rossini mostra que incivilidade e
intolerância ocorrem em **contextos discursivos diferentes**: a incivilidade
aparece em discussões com engajamento produtivo — opinião justificada,
confronto com discordância —, enquanto a intolerância aparece em discussões
homogêneas, com menos deliberação.

A implicação é forte e contraintuitiva: a incivilidade interpessoal **não é
incompatível** com discussão política democrática. O que ameaça a deliberação é
a intolerância — a deslegitimação e a estereotipação do outro.

### 2.4 Modelo tridimensional

**Bentivegna e Rega (2022)**

Decompõem a incivilidade política em três dimensões: *impoliteness*,
*delegitimação individual* e *delegitimação institucional*. O modelo é validado
empiricamente por survey (n = 797).

A **delegitimação individual** — enquadrar o oponente como irracional,
desonesto ou moralmente deficiente — é o conceito que corresponde diretamente
ao nível 3 da escala, e o que fundamenta tratá-lo como categoria própria em vez
de gradação de rispidez.

### 2.5 Scores contínuos probabilísticos

**Perspective API / Jigsaw**

Produzem um score 0–1 que representa a **probabilidade de que um leitor perceba
o texto como tóxico** — não a severidade da hostilidade. São duas grandezas
distintas, e a primeira não é o que o experimento precisa medir.

Além disso, o score é opaco quanto ao critério e não é reutilizável por
instrução: não há descritores textuais que um agente LLM possa aplicar.

### 2.6 Variáveis intervalares via IRT

**Kennedy et al. (2020)**

Decompõem o constructo de discurso hostil em componentes ordinais avaliados por
crowdworkers e os transformam, via Rasch IRT, numa variável contínua com
propriedades intervalares. É metodologicamente a abordagem mais rigorosa
revisada aqui.

Duas razões a inviabilizam neste desenho: exige **milhares de anotadores
humanos** para calibração, e o produto final é uma variável contínua calibrada
para aquele corpus — não uma escala discreta reutilizável por instrução.

### 2.7 Efeitos da incivilidade

**Mutz e Reeves (2005)**

Demonstram experimentalmente que a incivilidade viola normas de interação
respeitosa e produz **reações negativas viscerais** que se generalizam para
além da interação imediata, reduzindo a confiança política.

É a base para a premissa que sustenta todo o experimento: hostilidade
interpessoal degrada a qualidade do debate, e mitigá-la é um objetivo
legítimo de desenho sociotécnico.

---

## 3. Ancoragem nível a nível

Cada nível da escala e sua ancoragem na literatura revisada. O texto da coluna
"Definição operacional" reproduz a formulação usada nos prompts.

| Nível | Definição operacional | Ancoragem conceitual | Referências-chave |
|---|---|---|---|
| **0 — Sem hostilidade** | Desacordo legítimo, tom neutro ou respeitoso. Aplica-se sempre que a mensagem ataca o argumento, não a pessoa | Zona de discordância aceitável: Papacharissi (2004) separa desacordo de incivilidade; Rossini (2022) mostra que desacordo sem incivilidade associa-se a engajamento deliberativo produtivo | Papacharissi (2004); Rossini (2022) |
| **1 — Tom ríspido** | Impaciência, rispidez, sarcasmo dirigido ao argumento e não à pessoa. Desdém sem deslegitimação | *Aspersion* de Coe et al. (2014): linguagem depreciativa dirigida a uma ideia, plano ou comportamento — distinta do *name-calling*, dirigido à pessoa. Corresponde à *impoliteness* de Papacharissi (2004), que não constitui ameaça democrática | Coe et al. (2014); Papacharissi (2004) |
| **2 — Ironia / caricatura** | A posição do oponente é reduzida e ridicularizada. Desprezo codificado. Começa a alvejar a pessoa indiretamente | Zona de transição entre *impoliteness* e *incivility/intolerance* (Rossini, 2022). A caricatura como forma retórica de debate improdutivo corresponde à *rhétorique de l'incompréhension* de Angenot (2008). *Pejorative for speech* de Coe et al. (2014): ataque ao modo como o outro se expressa | Rossini (2022); Angenot (2008); Coe et al. (2014) |
| **3 — Deslegitimação** | O oponente é explicitamente enquadrado como irracional, desonesto ou moralmente deficiente. Ataques ao caráter ou à inteligência. Rótulos substituem o engajamento | *Delegitimação individual* de Bentivegna e Rega (2022), validada por survey. *Name-calling* de Coe et al. (2014): linguagem depreciativa dirigida à pessoa ou grupo. Kenski et al. (2020): *name-calling* é a forma percebida como mais incivil pelo público | Bentivegna e Rega (2022); Coe et al. (2014); Kenski et al. (2020) |
| **4 — Ataque pessoal explícito** | Insulto direto, desprezo aberto, linguagem que alveja a identidade, a dignidade ou o valor da pessoa. Apelos a sanção social | *Intolerance* de Rossini (2022): estereotipação ofensiva e ameaças. Nível mais severo da progressão, onde a percepção de incivilidade é maior (Kenski et al., 2020) e os efeitos sobre a confiança política são documentados (Mutz e Reeves, 2005) | Rossini (2022); Kenski et al. (2020); Mutz e Reeves (2005) |

---

## 4. Justificativa do limiar de intervenção (≥ 2)

O moderador D5 intervém quando a mensagem candidata atinge nível 2 ou superior.
A regra é mecânica: 0 e 1 publicam sem alteração; 2, 3 e 4 exigem reformulação.

### 4.1 O limiar traduz a fronteira impoliteness / incivility

O corte em 2 operacionaliza a fronteira conceitual entre **impoliteness**
(níveis 0–1, aceitável) e **incivility/intolerance** (níveis 2–4, danosa à
deliberação), conforme a distinção de Papacharissi (2004) e a validação
empírica de Rossini (2022).

Papacharissi (2004) argumenta que a impoliteness não é necessariamente danosa e
pode coexistir com discussão política democrática produtiva. Rossini (2022)
fornece a evidência: a incivilidade interpessoal — *aspersion*, tom ríspido —
aparece em contextos de engajamento deliberativo real, enquanto a intolerância
— deslegitimação, estereotipação — aparece em contextos de baixa deliberação.

### 4.2 O que muda no nível 2

O nível 2 marca o ponto em que **o alvo da hostilidade migra do argumento para
a pessoa**, ainda que indiretamente, via caricatura ou desprezo codificado. É
exatamente a fronteira que a literatura usa para separar impoliteness de
incivility.

Abaixo desse ponto, intervir seria suprimir aspereza legítima — o que
comprometeria a validade do experimento, já que a dimensão D5 se propõe a
mitigar hostilidade improdutiva, não a homogeneizar o tom do debate.

### 4.3 Natureza da decisão

Esta é uma **decisão de design do experimento**. O limiar traduz uma distinção
conceitual da literatura numa regra mecânica aplicável por um agente moderador,
mas **não é derivado de um threshold empírico previamente validado para uso com
LLMs**. Essa limitação está declarada na Seção 6.

---

## 5. As três patologias de Angenot como sinais de hostilidade

A escala numérica é complementada, no prompt do moderador D5, por um componente
de detecção de patologias baseado em Angenot (2008).

### 5.1 As três categorias

Angenot identifica três categorias analíticas do debate improdutivo — o
*dialogue de sourds*:

| Patologia | Descrição |
|---|---|
| **Incomensurabilidade discursiva** | Os interlocutores operam a partir de premissas, valores e fontes de verdade incompatíveis, o que torna o encontro argumentativo impossível |
| **Retórica da incompreensão** | Ataques à pessoa em vez do argumento: caricatura, deslegitimação, desprezo — recusa de reconhecer o outro como racional dentro do próprio sistema |
| **Ilusão da racionalidade** | Performance retórica dirigida a uma audiência terceira, sem intenção real de persuadir o interlocutor direto |

### 5.2 Papel distinto da escala

As patologias **não são níveis** de uma escala e não devem ser lidas como tal.
A distinção é funcional:

- a **escala numérica (0–4)** mede *severidade* — quanto de hostilidade há;
- as **patologias** descrevem *mecanismo* — que tipo de dinâmica improdutiva
  está em curso.

Uma mensagem de nível 2 e outra de nível 4 podem exibir a mesma patologia; uma
mesma mensagem pode exibir mais de uma. Por isso são registradas como campo
separado no log de moderação, e não combinadas num índice único.

### 5.3 Originalidade da operacionalização

A aplicação das categorias de Angenot como **instrumento de detecção
computacional** é contribuição original do modelo Moura-Brandi. A obra de
Angenot é reconhecida na tradição de retórica e análise do discurso, mas sua
operacionalização para uso por agentes LLM em moderação automatizada não possui
precedente direto na literatura — o que significa, também, que não há benchmark
externo contra o qual validá-la (Seção 6).

---

## 6. Limitações

1. **Ausência de validação humana da escala de hostilidade.** A escala ordinal
   0–4, embora ancorada em distinções conceituais consolidadas na literatura
   (Papacharissi, 2004; Coe et al., 2014; Rossini, 2022; Bentivegna e Rega,
   2022), não foi submetida a processo formal de validação com anotadores
   humanos neste estudo. Isso implica que: (i) a concordância inter-anotador
   (*Krippendorff's α* ordinal) não foi mensurada, de modo que não há evidência
   empírica de que os descritores dos cinco níveis produzem classificações
   consistentes entre avaliadores independentes; e (ii) a dependência cultural
   da percepção de hostilidade — reconhecida na literatura como fator
   significativo (Papacharissi, 2004; Rossini, 2022) — não foi controlada, e a
   escala pode não generalizar para contextos discursivos distintos do debate
   político brasileiro simulado neste trabalho. Os resultados de hostilidade
   reportados devem, portanto, ser interpretados como classificações
   instrumentais do agente LLM, e não como medidas validadas de hostilidade
   percebida por humanos.

2. **Ausência de calibração do Juiz C contra ground truth humano.** O Juiz C
   (agente LLM que classifica hostilidade de forma cega à condição
   experimental) não foi comparado com classificações humanas de referência.
   Sem essa calibração, não é possível determinar: (i) se o Juiz C apresenta
   vieses sistemáticos (e.g., sub-classificar ironia contextual brasileira por
   ter sido treinado predominantemente em inglês, ou comprimir a escala em
   torno dos níveis intermediários); (ii) se a concordância entre o Juiz C e
   avaliadores humanos atinge patamares aceitáveis (*Krippendorff's α* ordinal
   ≥ 0,667); nem (iii) se a variância intra-juiz (entre as 3 execuções por
   mensagem) é comparável à variância inter-anotador humana. A ausência dessa
   calibração é uma limitação direta dos achados quantitativos do estudo: os
   scores de hostilidade reportados refletem a classificação do LLM, cuja
   fidedignidade em relação ao julgamento humano não foi estabelecida neste
   trabalho.

3. **Descritores projetados para LLM, não para codificação humana.** Os
   descritores de cada nível foram redigidos para uso instrucional por modelos
   de linguagem, não para codificação humana convencional. A interpretação dos
   descritores por um LLM pode diferir da interpretação por anotadores humanos
   treinados.

4. **Limiar não derivado empiricamente.** O corte em ≥ 2 traduz uma distinção
   conceitual da literatura, mas não foi derivado de um threshold empírico
   específico. A sensibilidade dos resultados ao limiar — por exemplo, testar
   ≥ 3 como condição alternativa — é análise adicional possível.

5. **Unidimensionalidade pressuposta.** A progressão ordinal pressupõe que os
   cinco níveis formam uma dimensão única de severidade crescente. A literatura
   sugere que diferentes tipos de incivilidade são percebidos com severidades
   distintas (Kenski et al., 2020), mas a relação ordinal estrita entre os
   níveis específicos desta escala não foi validada empiricamente.

6. **Patologias sem benchmark externo.** A operacionalização das três
   patologias de Angenot para detecção por LLM é original e não possui
   benchmark externo de validação.

Os protocolos que endereçam as limitações 1 e 2 — validação da escala com
anotadores humanos e calibração do Juiz C contra ground truth — estão
detalhados na Seção 11 de
[`estado_atual_do_trabalho.md`](estado_atual_do_trabalho.md).

---

## Referências

As referências completas estão em
[`referencias.md`](referencias.md), seção "Incivilidade e moderação em discurso
político online" (e seção "Fundamentação teórica" para Angenot).

Metadados pendentes de conferência estão registrados em
[`../PENDENCIAS_REVISAO.md`](../PENDENCIAS_REVISAO.md).
