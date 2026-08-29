# Decisões de design — prompts de persona (Layer 1)

Este documento registra decisões tomadas sobre o conteúdo dos prompts de
persona gerados por
[`scripts/00_generate_persona_prompts.py`](../scripts/00_generate_persona_prompts.py)
(a camada de identidade ideológica — Layer 1 — do prompt de debate, específica
de cada persona) e a motivação metodológica por trás de cada uma. O objetivo é
documentar essas escolhas para fundamentação na seção de metodologia do artigo.

Para o desenho da Layer 2 (comportamento durante o debate, comum aos dois
polos), ver
[`debate_behavior_design_decisions.md`](debate_behavior_design_decisions.md).
Para as regras de classificação de polos que originam as personas, ver
[`../../dataset_analysis/docs/left right categories/regras_categorizacao_esquerda_direita.md`](../../dataset_analysis/docs/left%20right%20categories/regras_categorizacao_esquerda_direita.md).

---

## 1. Omissão do alinhamento político no texto do prompt (*political-lean blinding*)

### O que existia antes (`prompt_version` v2.0)

O prompt declarava o alinhamento político da persona de duas formas
redundantes — no rótulo do polo, na primeira linha, e como primeiro item da
lista de atributos:

```
You are a debate persona (left pole), built from ideological attributes
drawn from the MatrAIx Persona 1M dataset.

Your positioning is defined by the following attributes:
- political orientation: Left
- religiosity: Secular
...
```

### O que passou a existir (`prompt_version` v2.1)

Nem o rótulo do polo nem o atributo `political_lean` aparecem no texto do
prompt. A persona é descrita **apenas** por suas posições substantivas sobre
temas concretos:

```
You are a debate persona.

Your positioning is defined by the following attributes:
- religiosity: Secular
- institutional trust level: Verifying
- core value: Community
- stance on free market: Neutral
- stance on government regulation: Positive
...
```

O valor de `political_lean` **continua registrado** em
[`outputs/prompts/personas/persona_metadata.json`](../outputs/prompts/personas/persona_metadata.json),
no campo `blinded_attributes`, junto com `pole` e `pole_label`:

```json
{
  "pole": "left",
  "pole_label": "left pole",
  "persona_index": 0,
  "matraix_source": "wiki",
  "matraix_id": "Q56224097",
  "prompt_version": "v2.1",
  "blinded_attributes": {
    "political_lean": "Left"
  }
}
```

O ocultamento é **do agente, não nosso**: quem conduz o experimento mantém
acesso integral ao rótulo para pareamento, análise e auditoria.

### Motivação

**Problema identificado:** ao receber o rótulo `Left` ou `Right`
explicitamente, o modelo tende a debater *o rótulo* em vez de debater *as
posições da persona*. Rótulos político-partidários são uma das categorias
sociais mais densamente representadas nos dados de pré-treinamento, e
acompanham um repertório cultural inteiro — vocabulário, bordões, temas de
saliência, estilo retórico, e uma caricatura implícita de "como fala alguém
de esquerda/direita". A instrução passa a competir com esse repertório
aprendido, e o risco é que o comportamento observado no debate reflita o
estereótipo do modelo sobre cada campo político em vez do perfil ideológico
efetivamente amostrado do dataset.

**Riscos específicos do rótulo explícito:**

1. **Viés e estereotipia induzidos pelo rótulo.** O rótulo funciona como
   chave de acesso a um script cultural pronto. Uma persona rotulada `Right`
   pode passar a exibir posições que o modelo associa à direita em geral, mas
   que não estão entre seus atributos — o oposto do que o desenho pretende.
   O prompt já instrui "Do not invent attributes", mas o rótulo trabalha
   contra essa instrução ao fornecer, implicitamente, um conjunto inteiro de
   atributos não declarados.
2. **Achatamento da variação interna a cada polo.** As personas foram
   selecionadas justamente por coerência multi-indicador, e não são
   homogêneas dentro do polo (variam em religiosidade, valor central,
   confiança institucional, e na intensidade das posições econômicas). O
   rótulo tende a puxar todas as personas de um mesmo polo em direção a um
   protótipo comum, reduzindo essa variação — que é parte do que o desenho
   pretende preservar ao usar personas derivadas de dados reais.
3. **Redundância com os atributos substantivos.** O alinhamento político não
   acrescenta informação posicional: ele é, na regra de classificação
   adotada, uma *consequência* das posições substantivas, não um dado
   independente delas. A classificação de polos exige âncora em
   `political_lean` **e** ausência de contradição nos indicadores nucleares
   do eixo econômico (`att_free_markets`, `att_government_regulation`,
   `att_labor_unions`), justamente para garantir essa coerência. As posições
   substantivas que permanecem no prompt já determinam o polo; o rótulo só
   acrescenta a carga conotativa.
4. **Validade da alegação de "personas reais".** O argumento metodológico do
   artigo é que o conteúdo do debate decorre de perfis ideológicos amostrados
   de um dataset. Quanto mais o comportamento puder ser atribuído ao rótulo
   em vez do perfil, mais frágil fica essa alegação. Esta decisão é
   consistente com a remoção do roteiro de frames por tema/polo na Layer 2
   (seção 1 de
   [`debate_behavior_design_decisions.md`](debate_behavior_design_decisions.md)):
   ambas movem o desenho na mesma direção — fazer o argumento emergir dos
   atributos da persona, em vez de ser pré-escrito pelo polo.
5. **Preservação do rótulo para análise.** Nada se perde analiticamente. O
   polo continua sendo a variável independente do desenho experimental
   (pareamento esquerda × direita) e permanece disponível em
   `persona_metadata.json` e na estrutura de diretórios
   (`polo_esquerda/`, `polo_direita/`). O ocultamento atua exclusivamente
   sobre o que o agente lê.

**Trade-off reconhecido:** sem o rótulo, o "encaixe" de uma persona no polo
atribuído passa a depender inteiramente da coerência dos atributos
substantivos. Para personas com muitos campos nulos, ou cujo perfil seja
fracamente diferenciado, o comportamento no debate pode ficar menos
nitidamente polarizado do que ficaria com o rótulo explícito — o que pode
reduzir a intensidade do conflito simulado. Essa perda foi julgada aceitável
porque (a) o critério de seleção por score de coerência já favorece personas
com sinal ideológico consistente e vários indicadores concordantes,
mitigando o caso do perfil fraco; (b) a hostilidade e a escalada do debate
são produzidas pela Layer 2, que independe do polo; e (c) polarização obtida
via rótulo seria justamente o artefato que o desenho quer evitar. Caso o
piloto mostre debates que não se diferenciam entre polos, a alternativa
preferível é revisar o critério de seleção das personas (exigindo mais
indicadores concordantes) antes de reintroduzir o rótulo no prompt.

### Implementação

Em [`scripts/00_generate_persona_prompts.py`](../scripts/00_generate_persona_prompts.py),
o ocultamento é declarativo, via a constante `BLINDED_ATTRIBUTES`:

```python
# Attributes deliberately withheld from the prompt text. They stay in
# persona_metadata.json for analysis, pairing and auditing.
BLINDED_ATTRIBUTES = ("political_lean",)
```

Atributos listados aí são pulados na montagem do texto do prompt e gravados
em `blinded_attributes` no metadata. O rótulo do polo foi removido da primeira
linha do template no mesmo passo — mantê-lo ali anularia o ocultamento, já que
"left pole" comunica exatamente a mesma informação que `political orientation:
Left`.

**Verificação:** após a regeneração, nenhuma ocorrência de
`political orientation`, `political lean`, `left pole` ou `right pole` existe
nos 20 arquivos `.txt` gerados, e os 20 registros de `persona_metadata.json`
têm `political_lean` não nulo.

---

## 2. Enxugamento da linha de abertura

### O que existia antes

A primeira linha do template, mesmo após a remoção do rótulo do polo, ainda
declarava a origem dos dados:

```
You are a debate persona, built from ideological attributes drawn from the
MatrAIx Persona 1M dataset.
```

### O que passou a existir

```
You are a debate persona.
```

### Motivação

1. **Coerência com a regra de "sem proveniência no prompt".** A menção ao
   dataset de origem era a última referência de proveniência remanescente
   dentro do texto do prompt — inconsistente com a decisão, já vigente, de
   manter fonte e ID exclusivamente em `persona_metadata.json`. A remoção
   fecha essa lacuna: nenhum arquivo `.txt` menciona mais dataset, fonte ou
   identificador.
2. **Irrelevância para o comportamento pretendido.** Saber que os atributos
   vieram de um dataset não informa nenhuma posição de debate. A frase
   ocupava espaço no system prompt sem contribuir para a tarefa.
3. **Risco de enquadramento acadêmico.** Declarar ao agente que ele é um
   artefato construído a partir de um dataset de pesquisa convida um registro
   analítico/meta — o modelo pode se comportar como *sujeito de experimento*
   descrevendo uma posição, em vez de um participante de debate sustentando
   uma. Como o experimento mede degradação de debate, qualquer distanciamento
   meta induzido pelo prompt é ruído indesejado. Isso é uma extensão do mesmo
   raciocínio da seção 1: rótulos e enquadramentos de identidade no prompt
   acionam repertórios que competem com os atributos substantivos.

**Trade-off reconhecido:** nenhum relevante. A informação removida é
inteiramente redundante com o metadata e não tem função posicional. A
rastreabilidade ao registro de origem é preservada integralmente por
`persona_metadata.json`.

---

## 3. Estado atual dos prompts de Layer 1 após estas decisões

- Atributos presentes no prompt: `religiosity`, `trust_level`,
  `values_priority`, `att_free_markets`, `att_government_regulation`,
  `att_labor_unions`, `att_immigration`, `att_gun_ownership`,
  `att_capital_punishment`.
- Atributo ocultado do prompt e preservado no metadata: `political_lean`
  (seção 1 acima).
- Rótulo de polo: ausente do texto do prompt; preservado no metadata e na
  estrutura de diretórios.
- Proveniência (`matraix_source`, `matraix_id`) e menção ao dataset de
  origem: ausentes do texto do prompt; preservadas no metadata (seção 2
  acima).
- Linha de abertura: `You are a debate persona.`
- Idioma dos prompts: inglês.
- `prompt_version` corrente: `v2.1`.
