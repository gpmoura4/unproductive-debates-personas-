# Revisão da regra de classificação de polos (esquerda/direita)

Este documento audita a regra atualmente usada para classificar personas nos
grupos `polo_esquerda_political_lean` / `polo_direita_political_lean` (arquivo
`outputs/phase2_decoded_personas.json`, gerado por
`scripts/03_decode_attributes.py`) e que alimenta diretamente a geração de
prompts de debate em `../debate_simulation/scripts/00_generate_persona_prompts.py`.

**Status: a regra atual é insuficiente para o experimento.** Ela classifica
por um único campo, sem checar coerência entre atributos. Este documento
descreve a regra atual, mostra um caso real problemático já presente no
dataset gerado, e propõe uma regra de coerência para substituí-la.

---

## 1. Regra atualmente implementada

Localização: `scripts/03_decode_attributes.py`, linhas 286–300.

```python
pol_lean_id = "political_lean" if "political_lean" in id_to_index else None
left_profiles = []
right_profiles = []
if pol_lean_id:
    for r in decoded_records:
        lean = r["political_attributes"].get(pol_lean_id)
        if lean in ("Left", "Center-left"):
            left_profiles.append(r)
        elif lean in ("Right", "Center-right"):
            right_profiles.append(r)
```

Depois, na montagem do JSON de saída (linhas 303–310):

```python
"polo_esquerda_political_lean": left_profiles[:10],
"polo_direita_political_lean": right_profiles[:10],
```

**Em palavras:** dentro da amostra de 2.000 personas decodificadas, uma
persona entra no polo esquerda/direita se, e somente se, o campo
`political_lean` (um entre dez campos decodificados) tiver o valor
`Left`/`Center-left` ou `Right`/`Center-right`. Os outros nove campos
(`religiosity`, `trust_level`, `values_priority`,
`att_free_markets`, `att_government_regulation`, `att_labor_unions`,
`att_immigration`, `att_gun_ownership`, `att_capital_punishment`) **não são
consultados na decisão** — podem estar `null`, `Neutral`, ou até apontar em
direção contrária ao lean, e a persona é aceita do mesmo jeito. Os "10 de
cada polo" salvos no JSON são simplesmente os 10 primeiros que aparecem na
ordem de iteração da amostra — não há ordenação por força/consistência do
sinal ideológico, nem exigência de um mínimo de atributos preenchidos.

## 2. Por que isso é um problema para o experimento

O objetivo do `debate_simulation` é simular debates entre personas de polos
ideológicos opostos e medir algo sobre a dinâmica desse debate (ver
`00_generate_persona_prompts.py`, que transforma cada persona em um prompt
de sistema e instrui o modelo a "manter consistência de posicionamento").
Para isso ser um experimento válido, os dois grupos (esquerda/direita)
precisam representar posições **internamente coerentes e mutuamente
distintas** — caso contrário:

- **Efeito diluído**: se metade das personas "de esquerda" têm sinal
  ideológico fraco (só `political_lean`, resto nulo/neutro), qualquer
  diferença observada entre os polos no debate fica borrada por ruído,
  reduzindo o poder estatístico do experimento.
- **Contaminação por incoerência**: uma persona com `political_lean=Right`
  mas `att_labor_unions=Enthusiast` e `att_government_regulation=Enthusiast`
  (posições tipicamente associadas à esquerda econômica) gera um prompt
  internamente contraditório. O LLM debatedor recebe instruções conflitantes
  e o comportamento resultante não é atribuível de forma limpa a "uma
  persona de direita".
- **Não reprodutibilidade do costurado (grounding)**: para um artigo
  científico, a alegação "personas foram construídas a partir de atributos
  ideológicos reais do dataset" (texto literal do prompt gerado, linha 72-73
  de `00_generate_persona_prompts.py`) fica mais fraca se a única evidência
  de que a persona é "real" e "de esquerda"/"de direita" é um único campo
  categórico sem verificação cruzada.

### 2.1 Caso real já presente no dataset gerado

Arquivo `../debate_simulation/prompts/polo_esquerda/persona_06.txt`
(`source_record_id = Q55759875`):

```
- orientação política: Center-left
- religiosidade: Devout
- nível de confiança institucional: Skeptical
- valor central: Achievement
- posição sobre livre mercado: Neutral
- posição sobre regulação governamental: Neutral
- posição sobre sindicatos: Neutral
- posição sobre posse de armas: Neutral
- posição sobre pena de morte: Neutral
```

Isso não é uma contradição lógica automática (não há impedimento de uma
pessoa de centro-esquerda ser devota), mas é um **sinal isolado**: dos 9
campos além de `political_lean`, apenas 2 estão preenchidos
(`religiosity`, `trust_level`) e nenhum dos 6 campos de atitude
(`att_*`, que são os que mais diretamente indicam posição econômica/social)
tem qualquer valor não-neutro/não-nulo reforçando "esquerda". A persona é
classificada e usada no experimento com base em 1 campo, sem reforço.

## 3. Regra proposta (coerência multi-atributo)

Ideia central: exigir **acordo entre múltiplos sinais**, não só o
`political_lean`, e permitir excluir (ou sinalizar) personas cujos
atributos preenchidos apontam em direções opostas.

### 3.1 Passo 1 — Mapear a direção esperada de cada atributo

Para os campos de atitude (`att_*`), definir qual valor é "alinhado à
esquerda" e qual é "alinhado à direita", com base na literatura de
ciência política padrão (eixo econômico/social clássico):

| dimensão | valor alinhado à ESQUERDA | valor alinhado à DIREITA | neutro/não decisivo |
|---|---|---|---|
| `att_free_markets` | Skeptical | Positive / Enthusiast | Neutral |
| `att_government_regulation` | Positive / Enthusiast | Skeptical | Neutral |
| `att_labor_unions` | Positive / Enthusiast | Skeptical | Neutral |
| `att_immigration` | Positive | Skeptical | Neutral |
| `att_gun_ownership` | Skeptical | Positive / Enthusiast | Neutral |
| `att_capital_punishment` | Skeptical | Positive / Enthusiast | Neutral |

`religiosity`, `trust_level` e `values_priority` **não** devem ser tratados
como determinantes de polo (não são posições político-ideológicas por si,
são covariáveis demográficas/psicográficas) — mas devem ser mantidos como
metadados descritivos do prompt, já que ajudam a compor uma persona rica,
desde que não conflitem logicamente com o restante (ver 3.3).

> Nota: os valores exatos de cada dimensão categórica (`values` em
> `data/schema/persona_codes.schema.json`) devem ser conferidos antes de
> codificar essa tabela em script — o texto acima assume os rótulos já
> observados nos exemplos de `phase2_decoded_personas.json`
> (`Positive`, `Neutral`, `Skeptical`, `Enthusiast`).

### 3.2 Passo 2 — Calcular um "score de alinhamento"

Para cada persona, considerar apenas os `att_*` **não-nulos**:

```
score = (nº de att_* alinhados ao lean) − (nº de att_* alinhados ao lean oposto)
n_att_preenchidos = nº de att_* não-nulos
```

### 3.3 Passo 3 — Critério de inclusão no polo

Uma persona só entra em `polo_esquerda` / `polo_direita` se **todas** as
condições abaixo forem satisfeitas:

1. **Sinal primário**: `political_lean` ∈ {Left, Center-left} (ou
   {Right, Center-right}, respectivamente). *(igual à regra atual)*
2. **Cobertura mínima**: `n_att_preenchidos >= K` (ex.: K=2) — evita aceitar
   personas com quase tudo nulo, como o caso Q55759875 acima.
3. **Sem contradição direta**: nenhum `att_*` preenchido aponta para o lado
   oposto ao `political_lean` (score não pode ter nenhum voto contrário —
   ou, numa versão menos estrita, `score >= 0`).
4. **(Opcional, mais rígido) Maioria concordante**: `score / n_att_preenchidos
   >= 0.5`, isto é, ao menos metade dos atributos preenchidos reforça o lean.

Personas que passam no critério 1 mas falham em 2–4 devem ser **descartadas
da lista de polos** (não usadas no debate), não incluídas mesmo que com
ressalva — para manter os grupos experimentais limpos.

### 3.4 Passo 4 — Seleção determinística dos N por polo

Depois de filtrar, ordenar os candidatos por `score` decrescente (e, em
empate, por `n_att_preenchidos` decrescente) antes de cortar os top-N. Isso
troca "os 10 primeiros que apareceram na amostra" — hoje arbitrário, dependente
só da ordem de iteração — por "os 10 com maior evidência de coerência
ideológica", que é o que o experimento realmente precisa.

### 3.5 Consequência esperada

Como a maioria das personas na amostra de 2000 tem quase todos os `att_*`
nulos (ver cobertura por dimensão em `phase2_decode_report.md` — a maior
parte dos campos de atitude tem cobertura baixa), aplicar este filtro
provavelmente **reduz bastante** o número de candidatos elegíveis por polo
dentro da amostra atual de 2.000. Se após o filtro sobrarem poucos
candidatos (menos que o N desejado, ex. 10), a ação correta é **aumentar
`SAMPLE_SIZE`** (ex.: amostrar direto do total de 200.000, ou de todos os
shards) até ter candidatos suficientes que passem no critério de coerência
— não afrouxar a regra para preencher a cota.

## 4. Resumo executivo

| | Regra atual | Regra proposta |
|---|---|---|
| Campo(s) usado(s) | só `political_lean` | `political_lean` + os 6 `att_*` |
| Checagem de contradição | nenhuma | exige ausência de `att_*` no lado oposto |
| Cobertura mínima exigida | nenhuma (aceita quase tudo nulo) | mínimo de N atributos de atitude preenchidos |
| Critério de corte para top-10 | ordem de aparição na amostra | maior score de coerência ideológica |
| Risco atual | personas fracas/ambíguas contaminam os grupos experimentais | grupos mais garantidamente distintos e internamente consistentes |

## 5. Próximos passos sugeridos

1. Confirmar contra `data/schema/persona_codes.schema.json` os valores
   categóricos exatos de cada `att_*` (a tabela da seção 3.1 assume os
   rótulos vistos na amostra atual, pode haver outros).
2. Implementar a função de coerência (`compute_alignment_score`) em
   `scripts/03_decode_attributes.py`, substituindo o filtro de
   `left_profiles`/`right_profiles` atual.
3. Reexecutar a Fase 2 com uma amostra maior se o filtro deixar poucos
   candidatos elegíveis por polo.
4. Documentar no `phase2_decode_report.md` quantas personas foram
   descartadas por incoerência/baixa cobertura, para que o artigo possa
   citar esse critério de curadoria como parte da metodologia.
